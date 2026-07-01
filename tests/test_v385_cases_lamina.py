from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from modules.application_cases import case_labels, application_cases
from modules.cartographic_output import make_cartographic_sheet


def test_four_application_cases_are_available():
    labels = case_labels()
    cases = application_cases()
    assert len(labels) == 4
    assert len(cases) == 4
    assert any("Caso 1" in x and "interno" in x.lower() for x in labels)
    assert any("Caso 2" in x and "dentro y fuera" in x.lower() for x in labels)
    assert any("Caso 3" in x and "marginal" in x.lower() for x in labels)
    assert any("Caso 4" in x and "externo" in x.lower() for x in labels)


def test_cartographic_sheet_uses_active_basin_polygon(tmp_path: Path):
    dem = tmp_path / "dem.tif"
    arr = np.arange(80 * 80, dtype="float32").reshape(80, 80)
    transform = from_origin(-71.0, -29.0, 0.001, 0.001)
    with rasterio.open(
        dem,
        "w",
        driver="GTiff",
        height=arr.shape[0],
        width=arr.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(arr, 1)

    kml = b"""<?xml version='1.0' encoding='UTF-8'?>
    <kml xmlns='http://www.opengis.net/kml/2.2'><Document><Placemark><name>cuenca_activa</name>
    <Polygon><outerBoundaryIs><LinearRing><coordinates>
    -70.98,-29.02,0 -70.94,-29.02,0 -70.94,-29.06,0 -70.98,-29.06,0 -70.98,-29.02,0
    </coordinates></LinearRing></outerBoundaryIs></Polygon>
    </Placemark></Document></kml>"""

    png = make_cartographic_sheet(
        dem,
        basin_kml_bytes=kml,
        control_point={"lon": -70.965, "lat": -29.055},
        metrics={"area_km2": 12.3},
        contour_interval=50.0,
    )
    assert png.startswith(b"\x89PNG")
    assert len(png) > 5000
