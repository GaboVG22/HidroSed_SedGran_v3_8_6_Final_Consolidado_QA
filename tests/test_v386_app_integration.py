from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_v386_app_contains_project_name_and_navigation_buttons():
    src = APP.read_text(encoding="utf-8")
    assert "Nombre del proyecto actual" in src
    assert "Guardar y avanzar a" in src
    assert "official_flow_dataframe" in src
    assert "HidroSed Final Consolidado · v3.8.6" in src


def test_v386_app_contains_geometry_separation_and_frequency_analysis():
    src = APP.read_text(encoding="utf-8")
    assert "Cuenca topográfica de soporte" in src
    assert "Subcuenca hidrológica" in src
    assert "Análisis estadístico automático" in src
    assert "fit_frequency_distributions" in src
    assert "Ranking de distribuciones" in src


def test_v386_app_contains_lateral_inflows_and_project_download_names():
    src = APP.read_text(encoding="utf-8")
    assert "Caudal agregado por km" in src
    assert "apply_lateral_inflows" in src
    assert "_project_file(\"Eje_Cauce_Cuenca\", \"kmz\")" in src
    assert "_project_file(\"Cuenca_Eje_Curvas_Unificado\", \"kmz\")" in src
