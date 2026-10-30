import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.adapters.wms import parse_capabilities, tile_grid, wms_params

CAPS_111 = ('<WMT_MS_Capabilities version="1.1.1"><Capability><Layer><Title>root</Title>'
            '<SRS>EPSG:4326</SRS>'
            '<Layer><Name>A2SM_FLUDMARKS</Name><Title>침수흔적도</Title>'
            '<SRS>EPSG:4326</SRS><SRS>EPSG:5179</SRS><SRS>EPSG:4326</SRS>'
            '<LatLonBoundingBox minx="124.0" miny="33.0" maxx="132.0" maxy="39.0"/></Layer>'
            '<Layer><Name>A2SM_FLOODFOVRRISK1</Name></Layer>'
            '</Layer></Capability></WMT_MS_Capabilities>').encode("utf-8")
CAPS_130 = ('<WMS_Capabilities xmlns="http://www.opengis.net/wms" version="1.3.0"><Capability>'
            '<Layer><Name>L1</Name><CRS>EPSG:4326</CRS>'
            '<EX_GeographicBoundingBox><westBoundLongitude>126.0</westBoundLongitude>'
            '<eastBoundLongitude>128.0</eastBoundLongitude>'
            '<southBoundLatitude>37.0</southBoundLatitude>'
            '<northBoundLatitude>38.0</northBoundLatitude></EX_GeographicBoundingBox>'
            '</Layer></Capability></WMS_Capabilities>').encode("utf-8")


class TestE12Capabilities(unittest.TestCase):
    def test_nested_named_layers_and_srs_dedupe(self):
        layers = parse_capabilities(CAPS_111)
        self.assertEqual([l["name"] for l in layers], ["A2SM_FLUDMARKS", "A2SM_FLOODFOVRRISK1"])
        first = layers[0]
        self.assertEqual(first["title"], "침수흔적도")
        self.assertEqual(first["srs"], ("EPSG:4326", "EPSG:5179"))
        self.assertEqual(first["bbox"], (124.0, 33.0, 132.0, 39.0))
        self.assertEqual(layers[1], {"name": "A2SM_FLOODFOVRRISK1", "title": None,
                                     "srs": (), "bbox": None})

    def test_namespaced_130_document(self):
        layers = parse_capabilities(CAPS_130)
        self.assertEqual(layers, ({"name": "L1", "title": None, "srs": ("EPSG:4326",),
                                   "bbox": (126.0, 37.0, 128.0, 38.0)},))

    def test_invalid_payloads(self):
        for raw in (b"no xml", "str", b'<Layer><Name>N</Name><LatLonBoundingBox minx="a" miny="1" '
                    b'maxx="2" maxy="3"/></Layer>'):
            with self.assertRaises(C.ContractError, msg=raw) as cm:
                parse_capabilities(raw)
            self.assertEqual(str(cm.exception), "invalid_payload")


class TestE12TileGrid(unittest.TestCase):
    def test_row_major_from_south_west(self):
        tiles = tile_grid((126.0, 37.0, 128.0, 38.0), cols=2, rows=2)
        self.assertEqual(tiles, ((126.0, 37.0, 127.0, 37.5), (127.0, 37.0, 128.0, 37.5),
                                 (126.0, 37.5, 127.0, 38.0), (127.0, 37.5, 128.0, 38.0)))

    def test_single_tile_is_the_bbox(self):
        self.assertEqual(tile_grid((126, 37, 128, 38), cols=1, rows=1),
                         ((126.0, 37.0, 128.0, 38.0),))

    def test_budget_and_argument_checks(self):
        with self.assertRaises(C.ContractError) as cm:
            tile_grid((0, 0, 1, 1), cols=21, rows=20)
        self.assertEqual(str(cm.exception), "tile_budget_exceeded")
        self.assertEqual(len(tile_grid((0, 0, 1, 1), cols=20, rows=20)), 400)
        for bad in ((0, 0, 0, 1), (0, 0, 1), ("a", 0, 1, 1), (0.0, 0.0, float("inf"), 1.0)):
            with self.assertRaises(C.ContractError, msg=bad) as cm:
                tile_grid(bad, cols=1, rows=1)
            self.assertEqual(str(cm.exception), "invalid_bbox")
        with self.assertRaises(C.ContractError) as cm:
            tile_grid((0, 0, 1, 1), cols=0, rows=1)
        self.assertEqual(str(cm.exception), "invalid_grid")

    def test_edges_exact_at_ends(self):
        tiles = tile_grid((126.1, 37.3, 127.9, 37.9), cols=3, rows=1)
        self.assertEqual(tiles[0][0], 126.1)
        self.assertEqual(tiles[-1][2], 127.9)
        self.assertEqual(tiles[0][2], tiles[1][0])


class TestE12Params(unittest.TestCase):
    def test_exact_order_111(self):
        params = wms_params(layer="A2SM_FLUDMARKS", bbox=(126.75, 37.4, 127.2, 37.7),
                            srs="EPSG:4326")
        self.assertEqual(params,
                         (("SERVICE", "WMS"), ("REQUEST", "GetMap"), ("VERSION", "1.1.1"),
                          ("LAYERS", "A2SM_FLUDMARKS"), ("STYLES", ""), ("SRS", "EPSG:4326"),
                          ("BBOX", "126.75,37.4,127.2,37.7"), ("WIDTH", "256"), ("HEIGHT", "256"),
                          ("FORMAT", "image/png"), ("TRANSPARENT", "TRUE")))

    def test_130_uses_crs_and_transparent_false(self):
        params = wms_params(layer="L", bbox=(0, 0, 1, 1), srs="EPSG:4326", version="1.3.0",
                            transparent=False)
        self.assertIn(("CRS", "EPSG:4326"), params)
        self.assertNotIn(("SRS", "EPSG:4326"), params)
        self.assertEqual(params[-1], ("TRANSPARENT", "FALSE"))
        self.assertIn(("BBOX", "0.0,0.0,1.0,1.0"), params)

    def test_argument_checks(self):
        with self.assertRaises(C.ContractError) as cm:
            wms_params(layer="", bbox=(0, 0, 1, 1), srs="EPSG:4326")
        self.assertEqual(str(cm.exception), "invalid_wms_param")
        with self.assertRaises(C.ContractError) as cm:
            wms_params(layer="L", bbox=(0, 0, 1, 1), srs="EPSG:4326", version="2.0.0")
        self.assertEqual(str(cm.exception), "invalid_wms_param")
        with self.assertRaises(C.ContractError) as cm:
            wms_params(layer="L", bbox=(1, 0, 0, 1), srs="EPSG:4326")
        self.assertEqual(str(cm.exception), "invalid_bbox")
        with self.assertRaises(C.ContractError) as cm:
            wms_params(layer="L", bbox=(0, 0, 1, 1), srs="EPSG:4326", width=4096)
        self.assertEqual(str(cm.exception), "invalid_wms_param")


if __name__ == "__main__":
    unittest.main()
