import numpy as np
import pandas as pd

from modules.final_consolidated import (
    sanitize_project_name, project_file_name, official_flow_dataframe,
    geometry_usage_trace, active_basin_parameters, lateral_inflows_dataframe,
    apply_lateral_inflows, fit_frequency_distributions, PERIODS_FINAL,
)


def test_project_names_are_safe_and_used_in_file_names():
    assert sanitize_project_name("Quebrada Las Vertientes") == "Quebrada_Las_Vertientes"
    assert project_file_name("Quebrada Las Vertientes", "Cuenca", "kmz") == "Quebrada_Las_Vertientes_Cuenca.kmz"


def test_official_flow_has_19_stages():
    df = official_flow_dataframe("Eje del cauce / eje hidráulico")
    assert len(df) == 19
    assert "Eje del cauce / eje hidráulico" in df["Etapa oficial"].tolist()
    assert (df["Estado visual"] == "actual").sum() == 1


def test_geometry_usage_trace_separates_basin_axis_and_contours():
    df = geometry_usage_trace({"basin_active_kml": b"x", "axis_line": [(0, 0), (1, 1)], "contours_kml": b"c"})
    assert "Subcuenca hidrológica de cálculo" in df["Geometría / insumo"].tolist()
    assert "Eje hidráulico" in df["Geometría / insumo"].tolist()
    assert df.loc[df["Geometría / insumo"] == "Eje hidráulico", "Existe"].iloc[0] == "Sí"


def test_active_basin_parameters_recomputes_tc_from_corrected_metrics():
    df = active_basin_parameters({"area_km2": 12.0, "bbox_largo_km": 5.0, "pendiente_cauce": 0.04, "cota_max_m": 200, "cota_min_m": 100})
    assert "Tiempo concentración" in df["Parámetro"].tolist()
    tc = df.loc[df["Parámetro"] == "Tiempo concentración", "Valor"].iloc[0]
    assert float(tc) > 0


def test_lateral_inflows_accumulate_by_km_and_period():
    q = pd.DataFrame({"T_anios": [10, 100], "Q_m3s": [5.0, 15.0]})
    inflows = lateral_inflows_dataframe([
        {"km": 1.0, "Q_m3s": 2.0, "nombre": "Q lateral 1"},
        {"km": 3.0, "Q_m3s": 1.5, "nombre": "Q lateral 2"},
    ])
    out = apply_lateral_inflows(q, inflows, section_km=[0, 2, 4])
    assert not out.empty
    assert out[(out.T_anios == 10) & (out.km == 4.0)].iloc[0].Q_total_m3s == 8.5


def test_frequency_distributions_rank_and_quantiles():
    series = np.array([25, 31, 28, 45, 39, 52, 47, 60, 35, 42, 55, 65, 72, 58, 49, 33, 41, 53, 62, 70], dtype=float)
    res = fit_frequency_distributions(series, PERIODS_FINAL)
    assert not res["summary"].empty
    assert not res["ranking"].empty
    assert not res["quantiles"].empty
    assert set(PERIODS_FINAL).issubset(set(res["quantiles"]["T_anios"].astype(int)))
