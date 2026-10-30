"""WMS GetCapabilities parsing, tile grid splitting, and GetMap parameter building."""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET

from budongi.team_collection import contract as C


def _local_name(elem: ET.Element) -> str:
    """Return local name of an XML element without namespace prefix."""
    tag = elem.tag
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _validate_bbox(bbox: object) -> tuple[float, float, float, float]:
    """Validate bounding box and return coordinates as floats."""
    if not isinstance(bbox, (tuple, list)) or len(bbox) != 4:
        raise C.ContractError("invalid_bbox")
    for coord in bbox:
        if not isinstance(coord, (int, float)) or isinstance(coord, bool) or not math.isfinite(coord):
            raise C.ContractError("invalid_bbox")
    if not (bbox[0] < bbox[2] and bbox[1] < bbox[3]):
        raise C.ContractError("invalid_bbox")
    return (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))


def _parse_bbox(elem: ET.Element) -> tuple[float, float, float, float] | None:
    """Extract and validate bounding box from direct children of a Layer element."""
    lat_lon_box = None
    ex_geo_box = None
    for child in elem:
        if not isinstance(child.tag, str):
            continue
        clname = _local_name(child)
        if clname == "LatLonBoundingBox" and lat_lon_box is None:
            lat_lon_box = child
        elif clname == "EX_GeographicBoundingBox" and ex_geo_box is None:
            ex_geo_box = child

    if lat_lon_box is not None:
        attrs = lat_lon_box.attrib
        for key in ("minx", "miny", "maxx", "maxy"):
            if key not in attrs:
                raise C.ContractError("invalid_payload")
        try:
            minx = float(attrs["minx"])
            miny = float(attrs["miny"])
            maxx = float(attrs["maxx"])
            maxy = float(attrs["maxy"])
        except Exception:
            raise C.ContractError("invalid_payload")
        if not (math.isfinite(minx) and math.isfinite(miny) and math.isfinite(maxx) and math.isfinite(maxy)):
            raise C.ContractError("invalid_payload")
        return (minx, miny, maxx, maxy)

    if ex_geo_box is not None:
        geo_vals: dict[str, float] = {}
        for child in ex_geo_box:
            if not isinstance(child.tag, str):
                continue
            clname = _local_name(child)
            if clname in ("westBoundLongitude", "southBoundLatitude", "eastBoundLongitude", "northBoundLatitude"):
                if child.text is None:
                    raise C.ContractError("invalid_payload")
                raw_text = child.text.strip()
                if not raw_text:
                    raise C.ContractError("invalid_payload")
                try:
                    val = float(raw_text)
                except Exception:
                    raise C.ContractError("invalid_payload")
                if not math.isfinite(val):
                    raise C.ContractError("invalid_payload")
                if clname not in geo_vals:
                    geo_vals[clname] = val
        for key in ("westBoundLongitude", "southBoundLatitude", "eastBoundLongitude", "northBoundLatitude"):
            if key not in geo_vals:
                raise C.ContractError("invalid_payload")
        return (
            geo_vals["westBoundLongitude"],
            geo_vals["southBoundLatitude"],
            geo_vals["eastBoundLongitude"],
            geo_vals["northBoundLatitude"],
        )

    return None


def parse_capabilities(payload: bytes) -> tuple[dict, ...]:
    """Parse named layers from a WMS GetCapabilities XML document."""
    if not isinstance(payload, bytes):
        raise C.ContractError("invalid_payload")
    try:
        root = ET.fromstring(payload)
    except Exception:
        raise C.ContractError("invalid_payload")

    layers: list[dict] = []
    for elem in root.iter():
        if _local_name(elem) != "Layer":
            continue

        name = None
        title = None
        srs_list: list[str] = []

        for child in elem:
            clname = _local_name(child)
            if clname == "Name" and name is None:
                stripped_name = (child.text or "").strip()
                if stripped_name:
                    name = stripped_name
            elif clname == "Title" and title is None:
                stripped_title = (child.text or "").strip()
                if stripped_title:
                    title = stripped_title
            elif clname in ("SRS", "CRS"):
                stripped_srs = (child.text or "").strip()
                if stripped_srs and stripped_srs not in srs_list:
                    srs_list.append(stripped_srs)

        if name is None:
            continue

        bbox = _parse_bbox(elem)

        layers.append({
            "name": name,
            "title": title,
            "srs": tuple(srs_list),
            "bbox": bbox,
        })

    return tuple(layers)


def tile_grid(bbox: tuple, *, cols: int, rows: int) -> tuple[tuple[float, float, float, float], ...]:
    """Split bounding box into a grid of tiles west-to-east then south-to-north."""
    minx, miny, maxx, maxy = _validate_bbox(bbox)

    if not isinstance(cols, int) or isinstance(cols, bool) or cols < 1:
        raise C.ContractError("invalid_grid")
    if not isinstance(rows, int) or isinstance(rows, bool) or rows < 1:
        raise C.ContractError("invalid_grid")

    if cols * rows > 400:
        raise C.ContractError("tile_budget_exceeded")

    ex = [minx + (maxx - minx) * i / cols for i in range(cols + 1)]
    ex[0] = minx
    ex[cols] = maxx

    ey = [miny + (maxy - miny) * j / rows for j in range(rows + 1)]
    ey[0] = miny
    ey[rows] = maxy

    tiles: list[tuple[float, float, float, float]] = []
    for j in range(rows):
        for i in range(cols):
            tiles.append((float(ex[i]), float(ey[j]), float(ex[i + 1]), float(ey[j + 1])))

    return tuple(tiles)


def wms_params(
    *,
    layer: str,
    bbox: tuple,
    srs: str,
    width: int = 256,
    height: int = 256,
    image_format: str = "image/png",
    transparent: bool = True,
    version: str = "1.1.1",
) -> tuple[tuple[str, str], ...]:
    """Build ordered GetMap query parameter pairs."""
    if not isinstance(layer, str) or not layer.strip():
        raise C.ContractError("invalid_wms_param")

    valid_bbox = _validate_bbox(bbox)

    if not isinstance(srs, str) or not srs.strip():
        raise C.ContractError("invalid_wms_param")

    if not isinstance(width, int) or isinstance(width, bool) or not (1 <= width <= 2048):
        raise C.ContractError("invalid_wms_param")
    if not isinstance(height, int) or isinstance(height, bool) or not (1 <= height <= 2048):
        raise C.ContractError("invalid_wms_param")

    if not isinstance(image_format, str) or not image_format.strip():
        raise C.ContractError("invalid_wms_param")

    if version not in ("1.1.1", "1.3.0"):
        raise C.ContractError("invalid_wms_param")

    srs_key = "SRS" if version == "1.1.1" else "CRS"
    bbox_str = ",".join(repr(float(v)) for v in valid_bbox)

    return (
        ("SERVICE", "WMS"),
        ("REQUEST", "GetMap"),
        ("VERSION", version),
        ("LAYERS", layer),
        ("STYLES", ""),
        (srs_key, srs),
        ("BBOX", bbox_str),
        ("WIDTH", str(width)),
        ("HEIGHT", str(height)),
        ("FORMAT", image_format),
        ("TRANSPARENT", "TRUE" if transparent else "FALSE"),
    )
