from __future__ import annotations

import unittest

from budongi.team_collection import contract as C

from budongi.team_collection.core.mapping import apply_mapping, compile_mapping, header_coverage


def _doc(fields, **extra):
    doc = {"mapping_version": "v1", "record_type": "facility", "fields": fields}
    doc.update(extra)
    return doc


class MappingVisibleTests(unittest.TestCase):
    def test_compile_fills_defaults(self) -> None:
        m = compile_mapping(_doc([{"target": "name", "source": "명칭", "type": "text",
                                   "required": True}]))
        self.assertEqual(m["header_row"], 1)
        self.assertEqual(m["unmapped"], [])
        self.assertEqual(m["mapping_version"], "v1")
        self.assertEqual(m["record_type"], "facility")
        self.assertEqual(m["fields"], [{"target": "name", "source": "명칭", "type": "text",
                                        "required": True}])

    def test_compile_date_and_bool_defaults(self) -> None:
        m = compile_mapping(_doc([{"target": "d", "source": "D", "type": "date"},
                                  {"target": "b", "source": "B", "type": "bool"}]))
        self.assertEqual(m["fields"][0]["formats"], ["%Y-%m-%d", "%Y%m%d", "%Y.%m.%d", "%Y/%m/%d"])
        self.assertIs(m["fields"][0]["required"], False)
        self.assertEqual(m["fields"][1]["true_values"], ["y", "yes", "true", "1"])
        self.assertEqual(m["fields"][1]["false_values"], ["n", "no", "false", "0"])

    def test_compile_rejects_unknown_type(self) -> None:
        with self.assertRaises(C.ContractError) as ctx:
            compile_mapping(_doc([{"target": "a", "source": "A", "type": "float"}]))
        self.assertEqual(str(ctx.exception), "invalid_mapping:type")

    def test_apply_converts_typical_values(self) -> None:
        m = compile_mapping(_doc([
            {"target": "name", "source": "명칭", "type": "text"},
            {"target": "code", "source": "코드", "type": "code"},
            {"target": "n", "source": "수", "type": "int"},
            {"target": "v", "source": "값", "type": "decimal"},
            {"target": "d", "source": "일자", "type": "date"},
            {"target": "b", "source": "여부", "type": "bool"},
        ]))
        header = ("명칭", "코드", "수", "값", "일자", "여부")
        record, errors = apply_mapping(m, header, ("서울역", "00123", "1,234", "1,234.50",
                                                   "20240105", "Y"))
        self.assertEqual(errors, [])
        self.assertEqual(record, {"name": "서울역", "code": "00123", "n": 1234, "v": "1234.50",
                                  "d": "2024-01-05", "b": True})

    def test_apply_reports_invalid_number(self) -> None:
        m = compile_mapping(_doc([{"target": "n", "source": "N", "type": "int"}]))
        record, errors = apply_mapping(m, ("N",), ("abc",))
        self.assertEqual(errors, ["invalid_number:n"])
        self.assertIsNone(record["n"])
        self.assertEqual(record["n_raw"], "abc")

    def test_apply_missing_required(self) -> None:
        m = compile_mapping(_doc([{"target": "name", "source": "N", "type": "text",
                                   "required": True}]))
        record, errors = apply_mapping(m, ("N",), ("  ",))
        self.assertIsNone(record["name"])
        self.assertEqual(errors, ["missing_required:name"])

    def test_header_coverage_typical(self) -> None:
        m = compile_mapping(_doc([{"target": "name", "source": "명칭", "type": "text"},
                                  {"target": "x", "source": "X", "type": "decimal"}],
                                 unmapped=["비고"]))
        cov = header_coverage(m, ("명칭", "비고", "기타"))
        self.assertEqual(cov, {"mapped": ["명칭"], "unmapped_declared": ["비고"],
                               "unknown": ["기타"], "missing": ["X"], "complete": False})
        cov2 = header_coverage(m, ("X", "명칭", "비고"))
        self.assertEqual(cov2["mapped"], ["X", "명칭"])
        self.assertTrue(cov2["complete"])


if __name__ == "__main__":
    unittest.main()
