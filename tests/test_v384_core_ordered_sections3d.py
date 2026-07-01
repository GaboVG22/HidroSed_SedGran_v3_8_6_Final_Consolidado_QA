from io import BytesIO
import pandas as pd
from pathlib import Path

from modules.sections_v13_core import (
    read_kml_or_kmz, extract_lines_from_kml, make_transformers, get_lines_dataframe,
    project_geom, generate_chainages, build_sections, sections_to_dataframe,
    sample_profiles, evaluate_section_quality, evaluate_modelable_sections,
    filter_sections_for_modelacion, filter_selected_profile_points,
)
from modules.visual_3d_hydraulic import create_section_selection_3d_figure, figure_to_html_bytes
from modules.hydraulic_hecras_like import hecras_like_steady_profile, sediment_from_hecras_profile


def _sample_kml():
    # Eje N-S; las secciones son aproximadamente E-W. Usamos curvas casi N-S
    # para asegurar intersecciones en cada perfil transversal.
    curves = []
    for i, lon in enumerate([-71.0006, -71.0003, -71.0000, -70.9997, -70.9994]):
        z = 100 + i * 2
        curves.append(f"""
<Placemark><name>Curva {z} m</name><LineString><coordinates>
{lon},-30.0012,0 {lon},-29.9988,0
</coordinates></LineString></Placemark>""")
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<kml xmlns='http://www.opengis.net/kml/2.2'><Document>
<Placemark><name>EJE_CAUCE_HIDROSED</name><LineString><coordinates>
-71.0000,-30.0010,0 -71.0000,-29.9990,0
</coordinates></LineString></Placemark>
{''.join(curves)}
</Document></kml>""".encode("utf-8")


def test_v384_motor_v13_sections_and_preview_3d_smoke():
    kml = read_kml_or_kmz(BytesIO(_sample_kml()), "interno.kml")
    lines = extract_lines_from_kml(kml)
    assert len(lines) >= 6
    fwd, inv = make_transformers("EPSG:32719")
    lines_df = get_lines_dataframe(lines, fwd)
    axis = next(f for f in lines if "EJE_CAUCE_HIDROSED" in f.name)
    axis_metric = project_geom(axis.geometry_wgs84, fwd)
    contours = []
    for f in lines:
        if f.fid == axis.fid:
            continue
        assert f.z_candidate is not None
        contours.append((f.fid, float(f.z_candidate), project_geom(f.geometry_wgs84, fwd)))
    chainages = generate_chainages(axis_metric.length, 0, axis_metric.length / 1000.0, 50.0, None, None, 0, include_ends=True)
    sections = build_sections(axis_metric, chainages, 120.0)
    section_table = sections_to_dataframe(sections, inv)
    points, summary = sample_profiles(sections, contours, inv)
    quality = evaluate_section_quality(sections, points, summary)
    modelable = evaluate_modelable_sections(sections, points, summary, section_quality=quality, min_points_each_bank=1, min_total_points=3, require_axis_elevation=False)
    selected_sections = filter_sections_for_modelacion(sections, modelable)
    selected_points = filter_selected_profile_points(points, modelable)
    assert not section_table.empty
    assert not points.empty
    assert len(selected_sections) >= 1
    fig = create_section_selection_3d_figure(section_table, points, modelable_df=modelable, vertical_exaggeration=1.5)
    html = figure_to_html_bytes(fig)
    assert b"plotly" in html.lower()


def test_v384_hidrologia_hidraulica_preserved_with_synthetic_sections():
    sec = pd.DataFrame({
        "section_id": [1, 2, 3],
        "pk_m": [0.0, 100.0, 200.0],
        "cota_fondo_m": [100.0, 99.0, 98.0],
        "cota_borde_izq_m": [104.0, 103.0, 102.0],
        "cota_borde_der_m": [104.0, 103.0, 102.0],
    })
    pts = []
    for sid, pk, z in zip(sec.section_id, sec.pk_m, sec.cota_fondo_m):
        for x, zz in [(-10, z + 4), (-4, z + 1), (0, z), (4, z + 1), (10, z + 4)]:
            pts.append({"section_id": sid, "pk_m": pk, "offset_m": x, "z_m": zz})
    pts = pd.DataFrame(pts)
    qdf = pd.DataFrame({"T_anios": [100], "Q_m3s": [20.0]})
    profile = hecras_like_steady_profile(sec, pts, qdf, n_manning=0.035)
    sed = sediment_from_hecras_profile(profile, d50_m=0.0286)
    assert not profile.empty
    assert {"tirante_max_m", "velocidad_m_s", "Froude", "energia_m", "radio_hidraulico_m"}.issubset(profile.columns)
    assert not sed.empty
