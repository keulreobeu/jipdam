"""Coordinate CRS detection, magnitude candidates, bounds checking, and standardization."""
from __future__ import annotations

import math
import re

from budongi.team_collection import contract as C

_TM_DEFS = (
    ("EPSG:5179", 1000000.0, 2000000.0, 127.5, 0.9996, "GRS80"),
    ("EPSG:5181", 200000.0, 500000.0, 127.0, 1.0, "GRS80"),
    ("EPSG:5186", 200000.0, 600000.0, 127.0, 1.0, "GRS80"),
    ("EPSG:5174", 200000.0, 500000.0, 127.0028902777778, 1.0, "Bessel"),
    ("EPSG:2097", 200000.0, 500000.0, 127.0, 1.0, "Bessel"),
)

_MERCATOR_PROJECTIONS = frozenset({
    "mercator_auxiliary_sphere",
    "mercator_1sp",
    "popular_visualisation_pseudo_mercator",
})


def _parse_float(s: str) -> float | None:
    text = s.strip()
    if not re.match(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$", text):
        return None
    try:
        val = float(text)
        if math.isfinite(val):
            return val
    except (ValueError, TypeError):
        return None
    return None


def _match_ellipsoid(a: float, invf: float) -> str | None:
    if abs(a - 6378137.0) <= 0.001:
        if abs(invf - 298.257223563) <= 1e-7:
            return "WGS84"
        if abs(invf - 298.257222101) <= 1e-7:
            return "GRS80"
    if abs(a - 6377397.155) <= 0.001:
        if abs(invf - 299.1528128) <= 1e-7:
            return "Bessel"
    return None


def epsg_from_prj(wkt: str) -> str | None:
    """Return EPSG code matching WKT1 projection string, or None if unrecognized."""
    if not isinstance(wkt, str):
        raise C.ContractError("invalid_wkt")

    if wkt.startswith("\ufeff"):
        wkt = wkt[1:]

    if not wkt.strip():
        return None

    try:
        has_projcs = bool(re.search(r"\bPROJCS\s*\[", wkt, re.IGNORECASE))
        has_geogcs = bool(re.search(r"\bGEOGCS\s*\[", wkt, re.IGNORECASE))

        if not has_projcs and not has_geogcs:
            return None

        sph_m = re.search(
            r'\bSPHEROID\s*\[\s*["\']((?:[^"\'\\]|\\.)*)["\']\s*,\s*([^,\]]+)\s*,\s*([^,\]]+)',
            wkt,
            re.IGNORECASE,
        )
        if not sph_m:
            return None

        a = _parse_float(sph_m.group(2))
        invf = _parse_float(sph_m.group(3))
        if a is None or invf is None:
            return None

        ellipsoid = _match_ellipsoid(a, invf)

        if not has_projcs:
            if ellipsoid == "WGS84":
                return C.WGS84
            return None

        proj_m = re.search(r'\bPROJECTION\s*\[\s*["\']((?:[^"\'\\]|\\.)*)["\']\s*\]', wkt, re.IGNORECASE)
        if not proj_m:
            return None

        proj_name = proj_m.group(1).strip().lower().replace(" ", "_")

        params: dict[str, float] = {}
        for m in re.finditer(r'\bPARAMETER\s*\[\s*["\']((?:[^"\'\\]|\\.)*)["\']\s*,\s*([^,\]]+)', wkt, re.IGNORECASE):
            norm_name = m.group(1).strip().lower().replace(" ", "_")
            if norm_name in params:
                return None
            val = _parse_float(m.group(2))
            if val is None:
                return None
            params[norm_name] = val

        if proj_name == "transverse_mercator":
            required = (
                "false_easting",
                "false_northing",
                "central_meridian",
                "scale_factor",
                "latitude_of_origin",
            )
            if not all(r in params for r in required):
                return None

            fe = params["false_easting"]
            fn = params["false_northing"]
            cm = params["central_meridian"]
            k = params["scale_factor"]
            lat_0 = params["latitude_of_origin"]

            if abs(lat_0 - 38.0) > 1e-6:
                return None

            for code, t_fe, t_fn, t_cm, t_k, t_ell in _TM_DEFS:
                if (
                    abs(fe - t_fe) <= 0.001
                    and abs(fn - t_fn) <= 0.001
                    and abs(cm - t_cm) <= 1e-6
                    and abs(k - t_k) <= 1e-9
                    and ellipsoid == t_ell
                ):
                    return code
            return None

        if proj_name in _MERCATOR_PROJECTIONS:
            if abs(a - 6378137.0) > 0.001:
                return None
            fe = params.get("false_easting", 0.0)
            fn = params.get("false_northing", 0.0)
            cm = params.get("central_meridian", 0.0)
            if abs(fe) <= 1e-6 and abs(fn) <= 1e-6 and abs(cm) <= 1e-6:
                return "EPSG:3857"
            return None

        return None
    except C.ContractError:
        raise
    except Exception:
        return None


def crs_candidates(x: object, y: object) -> tuple[str, ...]:
    """Return matching EPSG codes based on coordinate magnitude ranges."""
    try:
        fx = float(x)  # type: ignore[arg-type]
        fy = float(y)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return ()

    if not (math.isfinite(fx) and math.isfinite(fy)):
        return ()

    results: list[str] = []

    if (
        (C.KOREA_LON[0] <= fx <= C.KOREA_LON[1] and C.KOREA_LAT[0] <= fy <= C.KOREA_LAT[1])
        or (C.KOREA_LAT[0] <= fx <= C.KOREA_LAT[1] and C.KOREA_LON[0] <= fy <= C.KOREA_LON[1])
    ):
        results.append(C.WGS84)

    if 600000.0 <= fx <= 1400000.0 and 1300000.0 <= fy <= 2200000.0:
        results.append("EPSG:5179")

    if 10000.0 <= fx <= 700000.0 and -100000.0 <= fy <= 700000.0:
        results.append("EPSG:5181")

    if 10000.0 <= fx <= 700000.0 and 0.0 <= fy <= 800000.0:
        results.append("EPSG:5186")

    if 10000.0 <= fx <= 700000.0 and -100000.0 <= fy <= 700000.0:
        results.append("EPSG:5174")

    if 10000.0 <= fx <= 700000.0 and -100000.0 <= fy <= 700000.0:
        results.append("EPSG:2097")

    if 13800000.0 <= fx <= 14700000.0 and 3850000.0 <= fy <= 4750000.0:
        results.append("EPSG:3857")

    return tuple(results)


def standardize(
    sx: object,
    sy: object,
    *,
    source_crs: str | None,
    axis_order: str | None,
) -> dict:
    """Standardize coordinates to WGS84 lat/lon if verified inside Korea."""
    null_reason: str | None = None
    lat: float | None = None
    lon: float | None = None

    if (
        sx is None
        or sy is None
        or (isinstance(sx, str) and not sx.strip())
        or (isinstance(sy, str) and not sy.strip())
    ):
        null_reason = C.COORDINATE_NULL_REASONS[0]
    elif source_crs is None or source_crs == "":
        null_reason = C.COORDINATE_NULL_REASONS[1]
    elif source_crs != C.WGS84:
        null_reason = C.COORDINATE_NULL_REASONS[2]
    elif axis_order not in ("x=lon,y=lat", "x=lat,y=lon"):
        null_reason = C.COORDINATE_NULL_REASONS[3]
    else:
        try:
            fx = float(sx)  # type: ignore[arg-type]
            fy = float(sy)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            null_reason = C.COORDINATE_NULL_REASONS[4]
        else:
            if not (math.isfinite(fx) and math.isfinite(fy)):
                null_reason = C.COORDINATE_NULL_REASONS[4]
            else:
                if axis_order == "x=lon,y=lat":
                    candidate_lon = fx
                    candidate_lat = fy
                else:
                    candidate_lat = fx
                    candidate_lon = fy

                if not (
                    C.KOREA_LAT[0] <= candidate_lat <= C.KOREA_LAT[1]
                    and C.KOREA_LON[0] <= candidate_lon <= C.KOREA_LON[1]
                ):
                    null_reason = C.COORDINATE_NULL_REASONS[5]
                else:
                    lat = candidate_lat
                    lon = candidate_lon

    return {
        "latitude": lat,
        "longitude": lon,
        "source_x": sx,
        "source_y": sy,
        "source_crs": source_crs,
        "source_axis_order": axis_order,
        "coordinate_method": "source_provided",
        "coordinate_review_status": "pending",
        "coordinate_null_reason": null_reason,
    }


def in_bounds(lat: object, lon: object, *, area: str = "korea") -> bool:
    """Return True if (lat, lon) lies inside the inclusive area bounds."""
    if area == "korea":
        lat_box = C.KOREA_LAT
        lon_box = C.KOREA_LON
    elif area == "seoul":
        lat_box = C.SEOUL_LAT
        lon_box = C.SEOUL_LON
    else:
        raise C.ContractError("invalid_area")

    try:
        flat = float(lat)  # type: ignore[arg-type]
        flon = float(lon)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False

    if not (math.isfinite(flat) and math.isfinite(flon)):
        return False

    return (
        lat_box[0] <= flat <= lat_box[1]
        and lon_box[0] <= flon <= lon_box[1]
    )
