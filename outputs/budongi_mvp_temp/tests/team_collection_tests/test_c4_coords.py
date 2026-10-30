import unittest
from budongi.team_collection import contract as C
from budongi.team_collection.core.coords import (
    crs_candidates,
    epsg_from_prj,
    in_bounds,
    standardize,
)

GEO = 'GEOGCS["GCS_{g}",DATUM["D_{g}",SPHEROID["{s}",{a},{f}]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'
WGS = ("WGS_1984", "WGS_1984", "6378137.0", "298.257223563")
GRS = ("Korea_2000", "GRS_1980", "6378137.0", "298.257222101")
BES = ("Korean_Datum_1985", "Bessel_1841", "6377397.155", "299.1528128")


def geo(e):
    return GEO.format(g=e[0], s=e[1], a=e[2], f=e[3])


def tm(name, e, fe, fn, cm, k):
    return ('PROJCS["%s",%s,PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",%s],'
            'PARAMETER["False_Northing",%s],PARAMETER["Central_Meridian",%s],PARAMETER["Scale_Factor",%s],'
            'PARAMETER["Latitude_Of_Origin",38.0],UNIT["Meter",1.0]]' % (name, geo(e), fe, fn, cm, k))


WKT = {
    "EPSG:4326": geo(WGS),
    "EPSG:5179": tm("Korea_2000_Korea_Unified_Coordinate_System", GRS, "1000000.0", "2000000.0", "127.5", "0.9996"),
    "EPSG:5181": tm("Korea_2000_Korea_Central_Belt", GRS, "200000.0", "500000.0", "127.0", "1.0"),
    "EPSG:5186": tm("Korea_2000_Korea_Central_Belt_2010", GRS, "200000.0", "600000.0", "127.0", "1.0"),
    "EPSG:5174": tm("Korean_1985_Modified_Central_Belt", BES, "200000.0", "500000.0", "127.0028902777778", "1.0"),
    "EPSG:2097": tm("Korean_1985_Korea_Central_Belt", BES, "200000.0", "500000.0", "127.0", "1.0"),
    "EPSG:3857": ('PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",%s,PROJECTION["Mercator_Auxiliary_Sphere"],'
                  'PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],'
                  'PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]]' % geo(WGS)),
}


class TestC4EpsgFromPrj(unittest.TestCase):
    def test_each_known_crs(self):
        for code, wkt in WKT.items():
            self.assertEqual(epsg_from_prj(wkt), code, code)
        self.assertIsNone(epsg_from_prj(""))

    def test_non_str_raises(self):
        with self.assertRaises(C.ContractError) as cm:
            epsg_from_prj(None)
        self.assertEqual(str(cm.exception), "invalid_wkt")


class TestC4Candidates(unittest.TestCase):
    def test_ranges(self):
        self.assertEqual(crs_candidates(127.0, 37.5), ("EPSG:4326",))
        self.assertEqual(crs_candidates(953000, 1952000), ("EPSG:5179",))
        self.assertEqual(crs_candidates(198000, 750000), ("EPSG:5186",))
        self.assertEqual(crs_candidates(198000, 450000),
                         ("EPSG:5181", "EPSG:5186", "EPSG:5174", "EPSG:2097"))
        self.assertEqual(crs_candidates(14135000, 4518000), ("EPSG:3857",))
        self.assertEqual(crs_candidates("abc", 1), ())


class TestC4Standardize(unittest.TestCase):
    KEYS = {"latitude", "longitude", "source_x", "source_y", "source_crs", "source_axis_order",
            "coordinate_method", "coordinate_review_status", "coordinate_null_reason"}

    def test_wgs84_lon_lat(self):
        out = standardize("126.978", "37.5665", source_crs=C.WGS84, axis_order="x=lon,y=lat")
        self.assertEqual(set(out), self.KEYS)
        self.assertAlmostEqual(out["latitude"], 37.5665)
        self.assertAlmostEqual(out["longitude"], 126.978)
        self.assertIsNone(out["coordinate_null_reason"])
        self.assertEqual(out["coordinate_method"], "source_provided")
        self.assertEqual(out["coordinate_review_status"], "pending")

    def test_projected_kept_without_latlon(self):
        out = standardize(198000, 451000, source_crs="EPSG:5181", axis_order="x=lon,y=lat")
        self.assertIsNone(out["latitude"])
        self.assertIsNone(out["longitude"])
        self.assertEqual(out["coordinate_null_reason"], "crs_not_wgs84")
        self.assertEqual(out["source_crs"], "EPSG:5181")
        self.assertEqual(out["source_y"], 451000)


class TestC4InBounds(unittest.TestCase):
    def test_areas(self):
        self.assertIs(in_bounds(35.1, 129.0), True)
        self.assertIs(in_bounds(37.5, 127.0, area="seoul"), True)
        self.assertIs(in_bounds(35.1, 129.0, area="seoul"), False)
        with self.assertRaises(C.ContractError) as cm:
            in_bounds(37.5, 127.0, area="mars")
        self.assertEqual(str(cm.exception), "invalid_area")


if __name__ == "__main__":
    unittest.main()
