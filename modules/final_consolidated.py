from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

PERIODS_FINAL = [2, 5, 10, 25, 50, 100, 200]
FLOW_STAGES_FINAL = [
    "Proyecto",
    "Delimitación de cuenca",
    "Corrección y validación de cuenca",
    "Cuenca topográfica de soporte",
    "Subcuenca hidrológica de cálculo",
    "Eje del cauce / eje hidráulico",
    "Curvas de nivel y topografía de respaldo",
    "Secciones transversales",
    "Perfil longitudinal",
    "Perfil 3D con espejo de agua",
    "Hidrología automática con bases internas",
    "Distribuciones estadísticas y bondad de ajuste",
    "Caudales por período de retorno",
    "Hidráulica",
    "Caudales agregados por km",
    "Socavación",
    "Lámina cartográfica",
    "Exportación KMZ, Excel, PDF e imágenes",
    "Auditoría final",
]

GEOMETRY_USAGE_ROWS = [
    ("Cuenca topográfica de soporte", "DEM, curvas, entorno del cauce, secciones, lámina cartográfica", "basin_topographic_kml"),
    ("Subcuenca hidrológica de cálculo", "caudales, morfometría, Tc, períodos de retorno", "basin_hydrologic_kml"),
    ("Eje hidráulico", "perfil longitudinal, secciones, hidráulica, socavación, espejo de agua 3D", "axis_line"),
    ("Curvas simples", "visualización general y respaldo preliminar", "contours_kml"),
    ("Curvas interpoladas en corredor", "mejora localizada de secciones en el eje", "axis_contours_kml"),
    ("Curvas externas KMZ", "respaldo topográfico externo, casos 2-3-4", "topo_support_df"),
]


def sanitize_project_name(name: str | None) -> str:
    """Return a filesystem-safe project name without losing readability."""
    raw = (name or "").strip() or "Proyecto_HidroSed"
    raw = re.sub(r"\s+", "_", raw)
    raw = re.sub(r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ_-]+", "", raw)
    raw = raw.strip("_-.")
    return raw or "Proyecto_HidroSed"


def project_file_name(project_name: str | None, suffix: str, ext: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ_-]+", "_", str(suffix or "Salida")).strip("_")
    ext = str(ext or "").lstrip(".")
    return f"{sanitize_project_name(project_name)}_{suffix}.{ext}"


def official_flow_dataframe(active_stage: str | None = None) -> pd.DataFrame:
    rows = []
    active_stage = active_stage or ""
    for i, stage in enumerate(FLOW_STAGES_FINAL, start=1):
        rows.append({
            "N°": i,
            "Etapa oficial": stage,
            "Estado visual": "actual" if stage == active_stage else "pendiente / disponible",
        })
    return pd.DataFrame(rows)


def geometry_usage_trace(session_state: Mapping) -> pd.DataFrame:
    rows = []
    for geom, use, key in GEOMETRY_USAGE_ROWS:
        exists = bool(session_state.get(key) is not None)
        # basin compatibility fallbacks
        if key == "basin_topographic_kml":
            exists = bool(session_state.get("basin_topographic_kml") or session_state.get("basin_active_kml") or session_state.get("basin_kml"))
        if key == "basin_hydrologic_kml":
            exists = bool(session_state.get("basin_hydrologic_kml") or session_state.get("basin_active_kml") or session_state.get("basin_kml"))
        if key == "axis_line":
            exists = bool(session_state.get("axis_line") or session_state.get("axis_auto_coords"))
        rows.append({
            "Geometría / insumo": geom,
            "Uso técnico": use,
            "Existe": "Sí" if exists else "No",
            "Clave interna": key,
        })
    return pd.DataFrame(rows)


def active_basin_parameters(metrics: Mapping | None, *, method: str = "HidroSed DEM / cuenca activa") -> pd.DataFrame:
    m = dict(metrics or {})
    def f(*keys, default=np.nan):
        for k in keys:
            v = m.get(k)
            if v is not None:
                return v
        return default

    area = f("area_km2", "area", default=np.nan)
    perimeter = f("perimetro_km", "perimeter_km", default=np.nan)
    length = f("longitud_cauce_km", "longitud_cauce_principal_km", "bbox_largo_km", default=np.nan)
    zmax = f("cota_max_m", "zmax_m", "elev_max_m", default=np.nan)
    zmin = f("cota_min_m", "zmin_m", "elev_min_m", default=np.nan)
    dz = f("desnivel_m", default=np.nan)
    if not np.isfinite(_safe(dz)) and np.isfinite(_safe(zmax)) and np.isfinite(_safe(zmin)):
        dz = _safe(zmax) - _safe(zmin)
    slope = f("pendiente_media", "slope_mean", default=np.nan)
    channel_slope = f("pendiente_cauce", "slope_cauce", default=np.nan)
    tc = f("tc_h", "tiempo_concentracion_h", default=np.nan)
    if not np.isfinite(_safe(tc)) and np.isfinite(_safe(length)) and np.isfinite(_safe(channel_slope)):
        S = max(_safe(channel_slope), 1e-6)
        Lm = max(_safe(length), 0) * 1000
        tc = 0.01947 * (Lm ** 0.77) * (S ** -0.385) / 60.0 if Lm > 0 else np.nan

    rows = [
        ("Área", area, "km²"),
        ("Perímetro", perimeter, "km"),
        ("Longitud cauce principal", length, "km"),
        ("Cota máxima", zmax, "m"),
        ("Cota mínima", zmin, "m"),
        ("Desnivel", dz, "m"),
        ("Pendiente media", slope, "m/m"),
        ("Pendiente del cauce", channel_slope, "m/m"),
        ("Centroide lon", f("centroide_lon", default=np.nan), "°"),
        ("Centroide lat", f("centroide_lat", default=np.nan), "°"),
        ("Punto control lon", f("punto_control_lon", "control_lon", default=np.nan), "°"),
        ("Punto control lat", f("punto_control_lat", "control_lat", default=np.nan), "°"),
        ("Tiempo concentración", tc, "h"),
        ("Método aplicado", method, ""),
        ("Consistencia DEM", f("dem_validation", "consistencia_dem", default="Por verificar"), ""),
        ("Consistencia curvas", f("contour_validation", "consistencia_curvas", default="Por verificar"), ""),
        ("Advertencias geométricas", f("warnings", "advertencias", default="Sin advertencias registradas"), ""),
    ]
    out = pd.DataFrame(rows, columns=["Parámetro", "Valor", "Unidad"])
    return out


def _safe(v, default=np.nan):
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def technical_alerts(session_state: Mapping) -> pd.DataFrame:
    alerts: list[dict] = []
    case_key = str(session_state.get("application_case_key", ""))
    if any(x in case_key for x in ["case_2", "case_3", "case_4", "external", "marginal"]):
        if not (session_state.get("topo_support_df") is not None or session_state.get("axis_contours_kml") or session_state.get("section_points_df")):
            alerts.append({"Severidad": "Alta", "Módulo": "Topografía", "Alerta": "Eje fuera/parcial/alejado requiere respaldo topográfico del corredor."})
    if not (session_state.get("axis_line") or session_state.get("axis_auto_coords")):
        alerts.append({"Severidad": "Media", "Módulo": "Eje hidráulico", "Alerta": "No existe eje manual o automático confirmado."})
    if not (session_state.get("basin_active_kml") or session_state.get("basin_kml")):
        alerts.append({"Severidad": "Media", "Módulo": "Cuenca", "Alerta": "No existe cuenca activa validada/corregida."})
    if session_state.get("profile_3d_html") and not session_state.get("hydraulic_profile_df") is not None:
        alerts.append({"Severidad": "Baja", "Módulo": "3D", "Alerta": "Perfil 3D disponible sin resultados hidráulicos conectados."})
    if not alerts:
        alerts.append({"Severidad": "OK", "Módulo": "Proyecto", "Alerta": "Sin alertas críticas registradas en los insumos principales."})
    return pd.DataFrame(alerts)


def lateral_inflows_dataframe(rows: Sequence[Mapping] | None) -> pd.DataFrame:
    cols = ["km", "Q_m3s", "nombre", "tipo", "permanencia", "variable_tiempo", "observacion"]
    df = pd.DataFrame(list(rows or []))
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan if c in ["km", "Q_m3s"] else ""
    df["km"] = pd.to_numeric(df["km"], errors="coerce")
    df["Q_m3s"] = pd.to_numeric(df["Q_m3s"], errors="coerce")
    return df[cols].dropna(subset=["km", "Q_m3s"]).sort_values("km").reset_index(drop=True)


def apply_lateral_inflows(q_design: pd.DataFrame, inflows: pd.DataFrame, section_km: Iterable[float] | None = None) -> pd.DataFrame:
    if q_design is None or q_design.empty:
        return pd.DataFrame()
    q = q_design.copy()
    if "T_anios" not in q.columns or "Q_m3s" not in q.columns:
        raise ValueError("q_design debe contener T_anios y Q_m3s.")
    inflows = lateral_inflows_dataframe([] if inflows is None else inflows.to_dict("records"))
    kms = sorted({float(k) for k in (section_km or []) if pd.notna(k)} | {0.0} | set(inflows["km"].dropna().astype(float).tolist()))
    rows = []
    for _, qr in q.iterrows():
        base = _safe(qr["Q_m3s"], 0)
        T = float(qr["T_anios"])
        for km in kms:
            add = float(inflows.loc[inflows["km"] <= km, "Q_m3s"].sum()) if not inflows.empty else 0.0
            rows.append({"T_anios": T, "km": km, "Q_base_m3s": base, "Q_agregado_m3s": add, "Q_total_m3s": base + add})
    return pd.DataFrame(rows)


def _empirical_positions(data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    xs = np.sort(np.asarray(data, dtype=float))
    n = len(xs)
    p = (np.arange(1, n + 1) - 0.44) / (n + 0.12)
    return xs, p


def fit_frequency_distributions(series: Sequence[float], periods: Sequence[int] | None = None) -> dict:
    """Fit common hydrologic frequency distributions with transparent ranking.

    This is intentionally defensive: failed distributions are returned with status="error"
    rather than breaking the application.
    """
    from scipy import stats

    periods = list(periods or PERIODS_FINAL)
    x = np.asarray([_safe(v) for v in series], dtype=float)
    x = x[np.isfinite(x)]
    x = x[x >= 0]
    if len(x) < 5:
        return {
            "summary": pd.DataFrame([{"n_validos": len(x), "advertencia": "Serie insuficiente para análisis estadístico robusto."}]),
            "ranking": pd.DataFrame(),
            "quantiles": pd.DataFrame(),
            "parameters": pd.DataFrame(),
            "observed": pd.DataFrame({"valor": x}),
        }

    dist_specs = [
        ("Normal", stats.norm, x),
        ("Log-Normal", stats.lognorm, x[x > 0]),
        ("Gumbel", stats.gumbel_r, x),
        ("Pearson III", stats.pearson3, x),
        ("Log-Pearson III", stats.pearson3, np.log(x[x > 0])),
        ("Gamma", stats.gamma, x[x > 0]),
        ("Weibull", stats.weibull_min, x[x > 0]),
        ("GEV", stats.genextreme, x),
    ]
    obs_x, ppos = _empirical_positions(x)
    rows_rank = []
    rows_params = []
    q_rows = []
    for name, dist, sample in dist_specs:
        sample = np.asarray(sample, dtype=float)
        if len(sample) < 5:
            rows_rank.append({"Distribución": name, "Estado": "error", "Advertencia": "muestra insuficiente"})
            continue
        try:
            params = dist.fit(sample)
            logpdf = dist.logpdf(sample, *params)
            ll = float(np.nansum(logpdf[np.isfinite(logpdf)]))
            k = len(params)
            n = len(sample)
            aic = 2 * k - 2 * ll
            bic = math.log(n) * k - 2 * ll
            if name == "Log-Pearson III":
                # compare empirical observed xs in original scale to fitted log-quantiles
                theor = np.exp(dist.ppf(ppos, *params))
            else:
                theor = dist.ppf(ppos, *params)
            rmse = float(np.sqrt(np.nanmean((obs_x[:len(theor)] - theor[:len(obs_x)]) ** 2))) if len(theor) else np.nan
            mae = float(np.nanmean(np.abs(obs_x[:len(theor)] - theor[:len(obs_x)]))) if len(theor) else np.nan
            ks_stat, ks_p = stats.kstest(sample, dist.cdf, args=params)
            try:
                ad_stat = float(stats.anderson(sample, dist="norm").statistic) if name == "Normal" else np.nan
            except Exception:
                ad_stat = np.nan
            rows_rank.append({
                "Distribución": name,
                "Estado": "ok",
                "n": n,
                "KS": float(ks_stat),
                "KS_pvalue": float(ks_p),
                "Anderson_Darling": ad_stat,
                "RMSE": rmse,
                "MAE": mae,
                "AIC": float(aic),
                "BIC": float(bic),
                "Advertencia": "" if n >= 20 else "serie corta; verificar T altos",
            })
            rows_params.append({"Distribución": name, "Parámetros": ", ".join(f"{p:.6g}" for p in params), "Método_estimación": "Máxima verosimilitud scipy"})
            for T in periods:
                prob = 1.0 - 1.0 / float(T)
                val = dist.ppf(prob, *params)
                if name == "Log-Pearson III":
                    val = math.exp(float(val))
                q_rows.append({"Distribución": name, "T_anios": int(T), "Valor_estimado": float(val) if np.isfinite(val) else np.nan})
        except Exception as exc:
            rows_rank.append({"Distribución": name, "Estado": "error", "Advertencia": str(exc)[:160]})
    ranking = pd.DataFrame(rows_rank)
    if not ranking.empty and "Estado" in ranking:
        ok = ranking[ranking["Estado"] == "ok"].copy()
        if not ok.empty:
            # Robust transparent rank: AIC + RMSE + KS. Lower is better.
            for col in ["AIC", "RMSE", "KS", "BIC"]:
                ok[f"rank_{col}"] = pd.to_numeric(ok[col], errors="coerce").rank(method="min")
            ok["Puntaje_ranking"] = ok[["rank_AIC", "rank_RMSE", "rank_KS", "rank_BIC"]].mean(axis=1)
            ok = ok.sort_values(["Puntaje_ranking", "AIC", "RMSE"]).reset_index(drop=True)
            ok["Recomendación"] = ["Adoptada sugerida" if i == 0 else "Alternativa" for i in range(len(ok))]
            ranking = pd.concat([ok, ranking[ranking["Estado"] != "ok"]], ignore_index=True, sort=False)
    summary = pd.DataFrame([{
        "n_validos": int(len(x)),
        "min": float(np.min(x)),
        "media": float(np.mean(x)),
        "mediana": float(np.median(x)),
        "max": float(np.max(x)),
        "desv_est": float(np.std(x, ddof=1)),
        "coef_variacion": float(np.std(x, ddof=1) / np.mean(x)) if np.mean(x) != 0 else np.nan,
        "advertencia": "Serie corta para períodos de retorno altos." if len(x) < 20 else "Serie con longitud aceptable para análisis preliminar.",
    }])
    return {
        "summary": summary,
        "ranking": ranking,
        "quantiles": pd.DataFrame(q_rows),
        "parameters": pd.DataFrame(rows_params),
        "observed": pd.DataFrame({"valor": np.sort(x)}),
    }


def hydrology_methodology_text() -> str:
    return (
        "El módulo hidrológico diferencia la subcuenca hidrológica de cálculo de la cuenca topográfica de soporte. "
        "Cuando existen series internas o cargadas, evalúa distribuciones Normal, Log-Normal, Gumbel, Pearson III, "
        "Log-Pearson III, Gamma, Weibull y GEV. La selección no es de caja negra: se muestra ranking por AIC, BIC, "
        "KS, RMSE y MAE, además de advertencias por longitud de serie y confiabilidad para períodos de retorno altos. "
        "La carga manual opera como complemento o reemplazo de la base interna, no como obligación."
    )
