from __future__ import annotations
import importlib.util
from pathlib import Path as _P
_S = importlib.util.spec_from_file_location("merge_plan", _P(__file__).resolve().parents[1] / "tooling" / "role2_harness" / "merge_plan.py")
merge_plan = importlib.util.module_from_spec(_S)
_S.loader.exec_module(merge_plan)
main = merge_plan.main
merge = merge_plan.merge

import contextlib
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest




class TestMergePlan(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.plan_dir = Path(self.tmp_dir_obj.name)

    def tearDown(self) -> None:
        self.tmp_dir_obj.cleanup()

    def _create_plan(
        self,
        base_data: dict[str, Any] | None = None,
        units: list[dict[str, Any]] | None = None,
        create_test_files: bool = True,
    ) -> None:
        if base_data is None:
            base_data = {"name": "sample_plan", "version": "1.0.0"}
        base_file = self.plan_dir / "plan.base.json"
        base_file.write_text(json.dumps(base_data, indent=2), encoding="utf-8")

        if units is not None:
            units_dir = self.plan_dir / "units"
            units_dir.mkdir(parents=True, exist_ok=True)
            for idx, unit in enumerate(units):
                unit_id = unit.get("id", f"unit_{idx}")
                unit_file = units_dir / f"{idx:02d}_{unit_id}.json"
                unit_file.write_text(json.dumps(unit, indent=2), encoding="utf-8")

                if create_test_files:
                    for t in unit.get("tests", []) or []:
                        t_path = self.plan_dir / t
                        t_path.parent.mkdir(parents=True, exist_ok=True)
                        t_path.write_text("# test file", encoding="utf-8")
                    for t in unit.get("hidden_tests", []) or []:
                        t_path = self.plan_dir / t
                        t_path.parent.mkdir(parents=True, exist_ok=True)
                        t_path.write_text("# hidden test file", encoding="utf-8")

    def test_topological_sort_with_order_and_id_tie_break(self) -> None:
        units = [
            {"id": "u_b", "order": 2, "depends_on": ["u_a"]},
            {"id": "u_a", "order": 0, "depends_on": []},
            {"id": "u_d", "order": 0, "depends_on": []},
            {"id": "u_c", "order": 0, "depends_on": []},
        ]
        self._create_plan(units=units)

        res = merge(self.plan_dir)
        self.assertEqual(res["units"], 4)
        self.assertTrue(res["written"])
        self.assertEqual(res["order"], ["u_a", "u_c", "u_d", "u_b"])

        plan_file = self.plan_dir / "plan.json"
        self.assertTrue(plan_file.is_file())
        saved = json.loads(plan_file.read_text(encoding="utf-8"))
        self.assertEqual(saved["name"], "sample_plan")
        self.assertEqual(saved["version"], "1.0.0")
        self.assertEqual([u["id"] for u in saved["units"]], ["u_a", "u_c", "u_d", "u_b"])

    def test_idempotent_second_run(self) -> None:
        units = [
            {"id": "u1", "order": 1, "depends_on": []},
            {"id": "u2", "order": 0, "depends_on": []},
        ]
        self._create_plan(units=units)

        first_run = merge(self.plan_dir)
        self.assertTrue(first_run["written"])
        self.assertEqual(first_run["order"], ["u2", "u1"])

        second_run = merge(self.plan_dir)
        self.assertFalse(second_run["written"])
        self.assertEqual(second_run["order"], ["u2", "u1"])

    def test_base_has_units(self) -> None:
        self._create_plan(base_data={"name": "invalid", "units": []}, units=[{"id": "u1"}])
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "base_has_units")

    def test_no_units_directory_missing(self) -> None:
        self._create_plan(units=None)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "no_units")

    def test_no_units_empty_directory(self) -> None:
        self._create_plan(units=[])
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "no_units")

    def test_duplicate_unit_id(self) -> None:
        units = [
            {"id": "duplicate_id", "order": 0},
            {"id": "duplicate_id", "order": 1},
        ]
        self._create_plan(units=units)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "duplicate_unit_id")

    def test_duplicate_deliverable_across_units(self) -> None:
        units = [
            {"id": "u1", "deliverables": ["build/app.bin"]},
            {"id": "u2", "deliverables": ["build/app.bin"]},
        ]
        self._create_plan(units=units)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "duplicate_deliverable")

    def test_duplicate_deliverable_within_unit(self) -> None:
        units = [
            {"id": "u1", "deliverables": ["build/app.bin", "build/app.bin"]},
        ]
        self._create_plan(units=units)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "duplicate_deliverable")

    def test_missing_test_file_in_tests(self) -> None:
        units = [
            {"id": "u1", "tests": ["tests/test_missing.py"]},
        ]
        self._create_plan(units=units, create_test_files=False)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "missing_test_file:tests/test_missing.py")

    def test_missing_test_file_in_hidden_tests(self) -> None:
        units = [
            {"id": "u1", "hidden_tests": ["tests/hidden/test_secret.py"]},
        ]
        self._create_plan(units=units, create_test_files=False)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "missing_test_file:tests/hidden/test_secret.py")

    def test_unknown_dependency(self) -> None:
        units = [
            {"id": "u1", "depends_on": ["missing_unit"]},
        ]
        self._create_plan(units=units)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "unknown_dependency:missing_unit")

    def test_dependency_cycle_direct(self) -> None:
        units = [
            {"id": "u1", "depends_on": ["u2"]},
            {"id": "u2", "depends_on": ["u1"]},
        ]
        self._create_plan(units=units)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "dependency_cycle")

    def test_dependency_cycle_self(self) -> None:
        units = [
            {"id": "u1", "depends_on": ["u1"]},
        ]
        self._create_plan(units=units)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "dependency_cycle")

    def test_hidden_listed_as_visible_in_tests(self) -> None:
        units = [
            {"id": "u1", "tests": ["tests/suite.py"], "hidden_tests": ["tests/suite.py"]},
        ]
        self._create_plan(units=units, create_test_files=True)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "hidden_listed_as_visible:tests/suite.py")

    def test_hidden_listed_as_visible_in_context_files(self) -> None:
        units = [
            {"id": "u1", "context_files": ["src/util.py"]},
            {"id": "u2", "hidden_tests": ["src/util.py"]},
        ]
        self._create_plan(units=units, create_test_files=True)
        with self.assertRaises(ValueError) as ctx:
            merge(self.plan_dir)
        self.assertEqual(str(ctx.exception), "hidden_listed_as_visible:src/util.py")

    def test_cli_main_success(self) -> None:
        units = [
            {"id": "u1", "order": 0},
        ]
        self._create_plan(units=units)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([str(self.plan_dir)])

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["units"], 1)
        self.assertTrue(output["written"])
        self.assertEqual(output["order"], ["u1"])

    def test_cli_main_value_error(self) -> None:
        self._create_plan(base_data={"name": "bad", "units": []}, units=[{"id": "u1"}])

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([str(self.plan_dir)])

        self.assertEqual(code, 2)
        output = json.loads(buf.getvalue())
        self.assertEqual(output, {"error": "base_has_units"})

    def test_cli_main_invalid_args(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([])

        self.assertEqual(code, 2)
        output = json.loads(buf.getvalue())
        self.assertEqual(output, {"error": "invalid_arguments"})


if __name__ == "__main__":
    unittest.main()
