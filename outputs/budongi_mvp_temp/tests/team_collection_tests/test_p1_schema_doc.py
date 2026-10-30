import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.package.schema_doc import build_schema, missing_keys

KEYS = ["delivery_schema_version", "source_id", "record_type", "mapping_version", "format", "columns",
        "source_file", "source_field_map", "unit_conversion", "missing_markers", "identifier",
        "status_rules", "region_code_definition", "coordinates", "unmapped_fields"]


def _args(**over):
    base = dict(source_id="seoul_bus", record_type="transit_route", mapping_version="m1",
                columns=[{"name": "name", "type": "text", "nullable": False, "unit": None,
                          "description": "route name", "required_when": "always"}],
                source_file="raw/routes.csv", field_map={"name": "ROUTE_NM"}, unmapped=["ETC"])
    base.update(over)
    return base


class TestP1BuildSchema(unittest.TestCase):
    def test_key_order(self):
        self.assertEqual(list(build_schema(**_args())), KEYS)

    def test_identity_values(self):
        doc = build_schema(**_args())
        self.assertEqual(doc["delivery_schema_version"], C.DELIVERY_SCHEMA_VERSION)
        self.assertEqual(doc["source_id"], "seoul_bus")
        self.assertEqual(doc["record_type"], "transit_route")
        self.assertEqual(doc["mapping_version"], "m1")
        self.assertEqual(doc["source_file"], "raw/routes.csv")

    def test_columns_full(self):
        doc = build_schema(**_args())
        self.assertEqual(doc["columns"], [{"name": "name", "type": "text", "nullable": False,
                                           "unit": None, "description": "route name",
                                           "required_when": "always"}])

    def test_column_defaults(self):
        doc = build_schema(**_args(columns=[{"name": "name", "type": "text"}]))
        self.assertEqual(doc["columns"], [{"name": "name", "type": "text", "nullable": True,
                                           "unit": None, "description": None,
                                           "required_when": None}])

    def test_field_map_and_unmapped(self):
        doc = build_schema(**_args())
        self.assertEqual(doc["source_field_map"], {"name": "ROUTE_NM"})
        self.assertEqual(doc["unmapped_fields"], ["ETC"])

    def test_descriptive_default_none(self):
        doc = build_schema(**_args())
        for key in ("format", "unit_conversion", "missing_markers", "identifier", "status_rules",
                    "region_code_definition", "coordinates"):
            self.assertIsNone(doc[key], key)

    def test_extra_supplies_descriptive(self):
        doc = build_schema(**_args(extra={"format": "jsonl", "missing_markers": ["-", "미상"],
                                          "coordinates": {"source_crs": "EPSG:4326"}}))
        self.assertEqual(doc["format"], "jsonl")
        self.assertEqual(doc["missing_markers"], ["-", "미상"])
        self.assertEqual(doc["coordinates"], {"source_crs": "EPSG:4326"})
        self.assertIsNone(doc["identifier"])

    def test_invalid_source_id(self):
        with self.assertRaises(C.ContractError) as cm:
            build_schema(**_args(source_id="Seoul"))
        self.assertEqual(str(cm.exception), "invalid_schema:source_id")

    def test_invalid_record_type(self):
        with self.assertRaises(C.ContractError) as cm:
            build_schema(**_args(record_type="bus"))
        self.assertEqual(str(cm.exception), "invalid_schema:record_type")


class TestP1MissingKeys(unittest.TestCase):
    def test_empty_dict_all_missing(self):
        self.assertEqual(missing_keys({}), KEYS)

    def test_fresh_schema_lists_descriptive(self):
        doc = build_schema(**_args())
        self.assertEqual(missing_keys(doc), ["format", "unit_conversion", "missing_markers",
                                             "identifier", "status_rules",
                                             "region_code_definition", "coordinates"])

    def test_complete_schema(self):
        extra = {k: "x" for k in ("format", "unit_conversion", "missing_markers", "identifier",
                                  "status_rules", "region_code_definition", "coordinates")}
        self.assertEqual(missing_keys(build_schema(**_args(extra=extra))), [])


if __name__ == "__main__":
    unittest.main()
