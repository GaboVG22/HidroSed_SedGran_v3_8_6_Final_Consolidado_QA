
from __future__ import annotations

import io
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely.ops import transform as shapely_transform


def _read_dem(path_or_bytes):
    import rasterio
    from rasterio.io import MemoryFile

    if isinstance(path_or_bytes, (str, Path)):
        src_ctx = rasterio.open(path_or_bytes)
    else:
        mem = MemoryFile(path_or_bytes)
        src_ctx = mem.open()

    with src_ctx as src:
        data = src.read(1, masked=True).astype("float64").filled(np.nan)
        if src.nodata is not None:
            data = np.where(np.isclose(data, src.nodata), np.nan, data)
        transform = src.transform
        crs = src.crs
        bounds = src.bounds
    return data, transform, crs, bounds


def hillshade(elevation, azimuth=315, altitude=45):
    elev = np.array(elevation, dtype=float)
    finite = np.isfinite(elev)
    if not finite.any():
        return np.zeros_like(elev)
    fill = np.nanmedian(elev[finite])
    elev = np.where(finite, elev, fill)
    dy, dx = np.gradient(elev)
    slope = np.pi / 2.0 - np.arctan(np.sqrt(dx * dx + dy * dy))
    aspect = np.arctan2(-dx, dy)
    az = np.deg2rad(azimuth)
    alt = np.deg2rad(altitude)
    shaded = np.sin(alt) * np.sin(slope) + np.cos(alt) * np.cos(slope) * np.cos(az - aspect)
    shaded = (shaded - shaded.min()) / max(shaded.max() - shaded.min(), 1e-9)
    return shaded


def _plot_polygon(ax, polygon_geom, color="#0057d8", linewidth=2.2, face_alpha=0.10):
    if polygon_geom is None or polygon_geom.is_empty:
        return
    geoms = polygon_geom.geoms if hasattr(polygon_geom, "geoms") else [polygon_geom]
    for geom in geoms:
        if geom.is_empty:
            continue
        xs, ys = geom.exterior.xy
        ax.fill(xs, ys, facecolor=color, alpha=face_alpha, edgecolor=color, linewidth=linewidth, zorder=5)
        for ring in geom.interiors:
            hx, hy = ring.xy
            ax.fill(hx, hy, facecolor="white", alpha=0.85, edgecolor=color, linewidth=0.8, zorder=6)


def _kml_polygon_geoms_lonlat(kml_bytes):
    if not kml_bytes:
        return None
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(kml_bytes)
        polygons = []
        for poly_el in root.findall(".//{*}Polygon"):
            coords_el = poly_el.find(".//{*}outerBoundaryIs/{*}LinearRing/{*}coordinates")
            if coords_el is None or not coords_el.text:
                continue
            coords = []
            for tok in coords_el.text.strip().split():
                parts = tok.split(",")
                if len(parts) >= 2:
                    coords.append((float(parts[0]), float(parts[1])))
            if len(coords) >= 3:
                try:
                    poly = Polygon(coords)
                    if poly.is_valid and not poly.is_empty:
                        polygons.append(poly)
                    else:
                        fixed = poly.buffer(0)
                        if fixed.is_valid and not fixed.is_empty:
                            polygons.append(fixed)
                except Exception:
                    continue
        if not polygons:
            return None
        if len(polygons) == 1:
            return polygons[0]
        merged = MultiPolygon(polygons)
        return merged.buffer(0) if not merged.is_valid else merged
    except Exception:
        return None


def _transform_geom_to_crs(geom, src_crs="EPSG:4326", dst_crs=None):
    if geom is None or dst_crs is None:
        return geom
    try:
        from pyproj import CRS, Transformer
        dst = CRS.from_user_input(dst_crs)
        src = CRS.from_user_input(src_crs)
        if dst == src:
            return geom
        transformer = Transformer.from_crs(src, dst, always_xy=True)
        return shapely_transform(transformer.transform, geom)
    except Exception:
        return geom


def _transform_xy_to_crs(x, y, src_crs="EPSG:4326", dst_crs=None):
    if dst_crs is None:
        return float(x), float(y)
    try:
        from pyproj import CRS, Transformer
        dst = CRS.from_user_input(dst_crs)
        src = CRS.from_user_input(src_crs)
        if dst == src:
            return float(x), float(y)
        transformer = Transformer.from_crs(src, dst, always_xy=True)
        xx, yy = transformer.transform(float(x), float(y))
        return float(xx), float(yy)
    except Exception:
        return float(x), float(y)


def _line_coords_from_session(axis_line, dst_crs=None):
    if axis_line is None:
        return None
    try:
        return [_transform_xy_to_crs(float(x), float(y), dst_crs=dst_crs) for x, y in axis_line]
    except Exception:
        return None


def make_cartographic_sheet(
    dem_path,
    basin_kml_bytes=None,
    axis_line=None,
    control_point=None,
    metrics=None,
    title="HidroSed · Delimitación de cuenca y curvas de nivel",
    contour_interval=10.0,
):
    """Create professional preview PNG/PDF-like map as PNG bytes.

    This is a cartographic output renderer. It does not replace technical GIS review,
    but creates a high-quality visual sheet for reports.
    """
    data, transform, crs, bounds = _read_dem(dem_path)
    finite = data[np.isfinite(data)]
    if finite.size < 25:
        raise ValueError("DEM insuficiente para generar lámina cartográfica.")

    # Extensión en CRS del DEM. OpenTopography normalmente entrega EPSG:4326,
    # pero DEM locales pueden venir en UTM. La cuenca KML se transforma al CRS del DEM.
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    basin_lonlat = _kml_polygon_geoms_lonlat(basin_kml_bytes)
    basin_geom = _transform_geom_to_crs(basin_lonlat, dst_crs=crs) if basin_lonlat is not None else None

    data_for_map = data.copy()
    if basin_geom is not None and not basin_geom.is_empty:
        try:
            from rasterio.features import geometry_mask
            basin_mask = geometry_mask([mapping(basin_geom)], transform=transform, invert=True, out_shape=data.shape)
            data_for_map = np.where(basin_mask, data, np.nan)
        except Exception:
            data_for_map = data.copy()

    shade = hillshade(data_for_map if np.isfinite(data_for_map).any() else data)

    finite_map = data_for_map[np.isfinite(data_for_map)]
    if finite_map.size < 25:
        finite_map = finite
        data_for_map = data
    zmin = float(np.nanmin(finite_map))
    zmax = float(np.nanmax(finite_map))
    ci = max(float(contour_interval), 1.0)
    start = np.ceil(zmin / ci) * ci
    end = np.floor(zmax / ci) * ci
    levels = np.arange(start, end + ci, ci)
    if len(levels) > 160:
        # prevent unreadable sheet; technical export can still be 1 m in KMZ.
        step = int(np.ceil(len(levels) / 160))
        levels = levels[::step]

    fig = plt.figure(figsize=(16, 9), dpi=150)
    ax = fig.add_axes([0.05, 0.08, 0.68, 0.82])
    side = fig.add_axes([0.76, 0.08, 0.21, 0.82])
    side.axis("off")

    ax.imshow(shade, cmap="gray", extent=extent, origin="upper", alpha=0.85)
    ax.imshow(data_for_map, cmap="terrain", extent=extent, origin="upper", alpha=0.35)

    try:
        # For geographic DEM, imshow extent maps rows/cols to lon/lat.
        x = np.linspace(bounds.left, bounds.right, data.shape[1])
        y = np.linspace(bounds.top, bounds.bottom, data.shape[0])
        X, Y = np.meshgrid(x, y)
        cs = ax.contour(X, Y, data_for_map, levels=levels, linewidths=0.35, colors="black", alpha=0.68)
        if len(levels) <= 80:
            ax.clabel(cs, inline=True, fontsize=6, fmt=lambda v: f"{v:.0f}")
    except Exception:
        pass

    _plot_polygon(ax, basin_geom)

    if basin_geom is not None and not basin_geom.is_empty:
        minx, miny, maxx, maxy = basin_geom.bounds
        pad_x = max((maxx - minx) * 0.08, 1e-6)
        pad_y = max((maxy - miny) * 0.08, 1e-6)
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)

    axis_coords = _line_coords_from_session(axis_line, dst_crs=crs)
    if axis_coords:
        xs, ys = zip(*axis_coords)
        ax.plot(xs, ys, color="#0057d8", linewidth=2.8, zorder=8, label="Eje de cauce")

    if control_point:
        lon, lat = _transform_xy_to_crs(float(control_point.get("lon")), float(control_point.get("lat")), dst_crs=crs)
        ax.scatter([lon], [lat], s=70, c="red", edgecolors="white", linewidths=1.2, zorder=9)
        ax.text(lon, lat, "  Punto de control", fontsize=8, weight="bold", color="red", zorder=10)

    ax.set_title(title, fontsize=14, weight="bold")
    ax.set_xlabel("Longitud / X")
    ax.set_ylabel("Latitud / Y")
    ax.grid(True, alpha=0.25, linewidth=0.4)

    # North arrow
    ax.annotate("N", xy=(0.06, 0.88), xytext=(0.06, 0.74), xycoords="axes fraction",
                arrowprops=dict(facecolor="black", width=4, headwidth=12),
                ha="center", va="center", fontsize=12, weight="bold")

    side.text(0.0, 0.98, "RESUMEN MORFOMÉTRICO", fontsize=12, weight="bold", color="#003b73")
    side.plot([0, 1], [0.955, 0.955], color="#003b73", linewidth=2)

    if metrics:
        rows = [
            ("Área", "area_km2", "km²"),
            ("Perímetro", "perimetro_km", "km"),
            ("Kc compacidad", "coef_compacidad_kc", ""),
            ("Factor forma", "factor_forma", ""),
            ("Rel. elongación", "relacion_elongacion", ""),
            ("Ancho medio", "ancho_medio_km", "km"),
            ("Largo caract.", "bbox_largo_km", "km"),
            ("Ajuste salida", "distancia_ajuste_m", "m"),
        ]
        y = 0.90
        for label, key, unit in rows:
            val = metrics.get(key)
            if val is None:
                continue
            try:
                txt = f"{float(val):,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except Exception:
                txt = str(val)
            side.text(0.0, y, label, fontsize=9)
            side.text(0.66, y, f"{txt} {unit}".strip(), fontsize=9, weight="bold", color="#0057d8")
            y -= 0.055

    side.text(0.0, 0.42, "ALCANCE CARTOGRÁFICO", fontsize=11, weight="bold", color="#003b73")
    side.text(0.0, 0.385, "Cuenca activa usada: " + ("sí" if basin_geom is not None else "no"), fontsize=8, color="dimgray")
    side.text(0.0, 0.355, "Curvas recortadas al polígono: " + ("sí" if basin_geom is not None else "no"), fontsize=8, color="dimgray")

    side.text(0.0, 0.31, "LEYENDA", fontsize=12, weight="bold", color="#003b73")
    side.plot([0, 1], [0.292, 0.292], color="#003b73", linewidth=2)
    legend_items = [
        ("Curvas de nivel", "black"),
        ("Límite de cuenca", "#0057d8"),
        ("Eje de cauce", "#0057d8"),
        ("Punto de control", "red"),
    ]
    y = 0.25
    for label, color in legend_items:
        side.plot([0.02, 0.16], [y, y], color=color, linewidth=2)
        side.text(0.20, y - 0.01, label, fontsize=9)
        y -= 0.055

    side.text(0.0, 0.04, "Salida cartográfica preliminar.\nRequiere revisión técnica para diseño final.", fontsize=8, color="dimgray")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
