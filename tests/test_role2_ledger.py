from __future__ import annotations
import importlib.util
from pathlib import Path as _P
_S = importlib.util.spec_from_file_location("ledger", _P(__file__).resolve().parents[1] / "tooling" / "role2_harness" / "ledger.py")
ledger = importlib.util.module_from_spec(_S)
_S.loader.exec_module(ledger)
REQUIRED = ledger.REQUIRED
VERDICTS = ledger.VERDICTS
append = ledger.append
canonical = ledger.canonical
main = ledger.main
summary = ledger.summary
verify = ledger.verify

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path




def _sample_entry(**overrides) -> dict:
    entry = {
        "ts_utc": "2026-10-29T14:30:00Z",
        "artifact": {
            "type": "source_code",
            "id": "ledger.py",
            "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        },
        "producer": {
            "vendor": "google",
            "family": "gemini",
            "model": "gemini-1.5-pro",
            "tool": "antigravity",
            "effort": "high",
        },
        "verdict": "pass",
        "evidence": "All automated checks and unit tests passed.",
        "decided_by": "producer",
        "gates": ["syntax", "unit_test"],
    }
    entry.update(overrides)
    return entry


class TestLedger(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.temp_dir.name) / "ledger.jsonl"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_chaining(self) -> None:
        entry1 = _sample_entry(verdict="pass")
        rec1 = append(self.ledger_path, entry1)
        self.assertEqual(rec1["prev_sha256"], "0" * 64)
        self.assertIn("sha256", rec1)

        entry2 = _sample_entry(verdict="needs_fix")
        rec2 = append(self.ledger_path, entry2)
        self.assertEqual(rec2["prev_sha256"], rec1["sha256"])

        entry3 = _sample_entry(verdict="fail")
        rec3 = append(self.ledger_path, entry3)
        self.assertEqual(rec3["prev_sha256"], rec2["sha256"])

        res = verify(self.ledger_path)
        self.assertEqual(res, {"entries": 3, "ok": True, "first_bad_line": None})

    def test_tamper_detection_middle_line_content(self) -> None:
        append(self.ledger_path, _sample_entry(verdict="pass"))
        append(self.ledger_path, _sample_entry(verdict="pass"))
        append(self.ledger_path, _sample_entry(verdict="pass"))

        lines = self.ledger_path.read_bytes().splitlines()
        rec2 = json.loads(lines[1].decode("utf-8"))
        rec2["verdict"] = "fail"
        lines[1] = json.dumps(rec2, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.ledger_path.write_bytes(b"\n".join(lines) + b"\n")

        res = verify(self.ledger_path)
        self.assertFalse(res["ok"])
        self.assertEqual(res["first_bad_line"], 2)

    def test_tamper_detection_middle_line_rehash(self) -> None:
        append(self.ledger_path, _sample_entry(verdict="pass"))
        append(self.ledger_path, _sample_entry(verdict="pass"))
        append(self.ledger_path, _sample_entry(verdict="pass"))

        lines = self.ledger_path.read_bytes().splitlines()
        rec2 = json.loads(lines[1].decode("utf-8"))
        rec2["verdict"] = "fail"
        rec2_without_sha = {k: v for k, v in rec2.items() if k != "sha256"}
        import hashlib
        rec2["sha256"] = hashlib.sha256(canonical(rec2_without_sha)).hexdigest()
        lines[1] = canonical(rec2)
        self.ledger_path.write_bytes(b"\n".join(lines) + b"\n")

        res = verify(self.ledger_path)
        self.assertFalse(res["ok"])
        self.assertEqual(res["first_bad_line"], 3)

    def test_tamper_detection_first_line_prev(self) -> None:
        append(self.ledger_path, _sample_entry(verdict="pass"))
        append(self.ledger_path, _sample_entry(verdict="pass"))

        lines = self.ledger_path.read_bytes().splitlines()
        rec1 = json.loads(lines[0].decode("utf-8"))
        rec1["prev_sha256"] = "1" * 64
        lines[0] = canonical(rec1)
        self.ledger_path.write_bytes(b"\n".join(lines) + b"\n")

        res = verify(self.ledger_path)
        self.assertFalse(res["ok"])
        self.assertEqual(res["first_bad_line"], 1)

    def test_reserved_fields(self) -> None:
        entry_with_prev = _sample_entry(prev_sha256="0" * 64)
        with self.assertRaises(ValueError) as ctx:
            append(self.ledger_path, entry_with_prev)
        self.assertEqual(str(ctx.exception), "reserved_field")

        entry_with_sha = _sample_entry(sha256="a" * 64)
        with self.assertRaises(ValueError) as ctx:
            append(self.ledger_path, entry_with_sha)
        self.assertEqual(str(ctx.exception), "reserved_field")

    def test_invalid_entries_missing_required(self) -> None:
        for field in REQUIRED:
            entry = _sample_entry()
            del entry[field]
            with self.assertRaises(ValueError) as ctx:
                append(self.ledger_path, entry)
            self.assertEqual(str(ctx.exception), f"invalid_entry:{field}")

    def test_invalid_entries_artifact(self) -> None:
        invalid_artifacts = [
            "not-a-dict",
            {"type": "source", "id": "1"},  # missing sha256
            {"type": "source", "sha256": "0" * 64},  # missing id
            {"id": "1", "sha256": "0" * 64},  # missing type
            {"type": "source", "id": "1", "sha256": "A" * 64},  # uppercase hex
            {"type": "source", "id": "1", "sha256": "0" * 63},  # short hex
            {"type": "source", "id": "1", "sha256": "g" * 64},  # non hex
        ]
        for art in invalid_artifacts:
            with self.assertRaises(ValueError) as ctx:
                append(self.ledger_path, _sample_entry(artifact=art))
            self.assertEqual(str(ctx.exception), "invalid_entry:artifact")

    def test_invalid_entries_producer(self) -> None:
        invalid_producers = [
            "not-a-dict",
            {"vendor": "v", "family": "f", "model": "m", "tool": "t"},  # missing effort
            {"vendor": "v", "family": "f", "model": "m", "effort": "low"},  # missing tool
            {"vendor": "v", "family": "f", "tool": "t", "effort": "low"},  # missing model
            {"vendor": "v", "model": "m", "tool": "t", "effort": "low"},  # missing family
            {"family": "f", "model": "m", "tool": "t", "effort": "low"},  # missing vendor
            {"vendor": "v", "family": "f", "model": "m", "tool": "t", "effort": 123},  # non-str effort
        ]
        for prod in invalid_producers:
            with self.assertRaises(ValueError) as ctx:
                append(self.ledger_path, _sample_entry(producer=prod))
            self.assertEqual(str(ctx.exception), "invalid_entry:producer")

    def test_invalid_entries_reviewer_and_referee(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            append(self.ledger_path, _sample_entry(reviewer={"vendor": "v"}))
        self.assertEqual(str(ctx.exception), "invalid_entry:reviewer")

        with self.assertRaises(ValueError) as ctx:
            append(self.ledger_path, _sample_entry(referee={"vendor": "v"}))
        self.assertEqual(str(ctx.exception), "invalid_entry:referee")

        # None or absent reviewer/referee allowed
        entry_none = _sample_entry(reviewer=None, referee=None)
        rec = append(self.ledger_path, entry_none)
        self.assertIsNone(rec["reviewer"])
        self.assertIsNone(rec["referee"])

    def test_invalid_entries_verdict(self) -> None:
        for bad_verdict in ("approved", "PASS", "failed", "", 123):
            with self.assertRaises(ValueError) as ctx:
                append(self.ledger_path, _sample_entry(verdict=bad_verdict))
            self.assertEqual(str(ctx.exception), "invalid_entry:verdict")

        for good_verdict in VERDICTS:
            rec = append(self.ledger_path, _sample_entry(verdict=good_verdict))
            self.assertEqual(rec["verdict"], good_verdict)

    def test_invalid_entries_gates(self) -> None:
        for bad_gates in ("gate1", ["g1", 123], {"gate": True}, None):
            with self.assertRaises(ValueError) as ctx:
                append(self.ledger_path, _sample_entry(gates=bad_gates))
            self.assertEqual(str(ctx.exception), "invalid_entry:gates")

    def test_invalid_entries_ts_utc(self) -> None:
        for bad_ts in (
            "2026-10-29 14:30:00Z",
            "2026-10-29T14:30:00",
            "2026/10/29T14:30:00Z",
            "invalid-date",
            123456789,
        ):
            with self.assertRaises(ValueError) as ctx:
                append(self.ledger_path, _sample_entry(ts_utc=bad_ts))
            self.assertEqual(str(ctx.exception), "invalid_entry:ts_utc")

    def test_empty_file_verify(self) -> None:
        non_existent = Path(self.temp_dir.name) / "missing.jsonl"
        res_missing = verify(non_existent)
        self.assertEqual(res_missing, {"entries": 0, "ok": True, "first_bad_line": None})

        empty_file = Path(self.temp_dir.name) / "empty.jsonl"
        empty_file.touch()
        res_empty = verify(empty_file)
        self.assertEqual(res_empty, {"entries": 0, "ok": True, "first_bad_line": None})

    def test_summary_counts(self) -> None:
        res_empty = summary(self.ledger_path)
        self.assertEqual(
            res_empty,
            {"entries": 0, "by_artifact_type": {}, "by_verdict": {}, "pairs": {}},
        )

        reviewer_actor = {
            "vendor": "anthropic",
            "family": "claude-3-5",
            "model": "claude-3-5-sonnet",
            "tool": "agy",
            "effort": None,
        }

        # Entry 1: gemini > claude-3-5
        append(
            self.ledger_path,
            _sample_entry(
                artifact={"type": "code", "id": "1", "sha256": "0" * 64},
                verdict="pass",
                producer={"vendor": "google", "family": "gemini", "model": "1.5", "tool": "t", "effort": "low"},
                reviewer=reviewer_actor,
                evidence="CONFIDENTIAL_EVIDENCE_1",
            ),
        )

        # Entry 2: gemini > none
        append(
            self.ledger_path,
            _sample_entry(
                artifact={"type": "code", "id": "2", "sha256": "0" * 64},
                verdict="fail",
                producer={"vendor": "google", "family": "gemini", "model": "1.5", "tool": "t", "effort": "low"},
                reviewer=None,
                evidence="CONFIDENTIAL_EVIDENCE_2",
            ),
        )

        # Entry 3: openai > claude-3-5
        append(
            self.ledger_path,
            _sample_entry(
                artifact={"type": "spec", "id": "3", "sha256": "0" * 64},
                verdict="needs_fix",
                producer={"vendor": "openai", "family": "gpt-4", "model": "4o", "tool": "t", "effort": None},
                reviewer=reviewer_actor,
                evidence="CONFIDENTIAL_EVIDENCE_3",
            ),
        )

        res = summary(self.ledger_path)
        self.assertEqual(res["entries"], 3)
        self.assertEqual(res["by_artifact_type"], {"code": 2, "spec": 1})
        self.assertEqual(res["by_verdict"], {"pass": 1, "fail": 1, "needs_fix": 1})
        self.assertEqual(
            res["pairs"],
            {
                "gemini>claude-3-5": 1,
                "gemini>none": 1,
                "gpt-4>claude-3-5": 1,
            },
        )

        # Verify evidence text is never included in summary
        summary_json = json.dumps(res)
        self.assertNotIn("CONFIDENTIAL_EVIDENCE", summary_json)
        self.assertNotIn("evidence", res)

    def test_main_cli(self) -> None:
        append(self.ledger_path, _sample_entry(verdict="pass"))

        # Verify command
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            ret = main(["verify", str(self.ledger_path)])
        self.assertEqual(ret, 0)
        verify_out = json.loads(stdout_buf.getvalue())
        self.assertTrue(verify_out["ok"])
        self.assertEqual(verify_out["entries"], 1)

        # Summary command
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            ret = main(["summary", str(self.ledger_path)])
        self.assertEqual(ret, 0)
        summary_out = json.loads(stdout_buf.getvalue())
        self.assertEqual(summary_out["entries"], 1)

        # Unknown command -> ValueError -> return 2 with {"error": ...}
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            ret = main(["bad_command", str(self.ledger_path)])
        self.assertEqual(ret, 2)
        err_out = json.loads(stdout_buf.getvalue())
        self.assertEqual(err_out, {"error": "unknown_command:bad_command"})

        # Insufficient args -> return 2 with {"error": ...}
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            ret = main([])
        self.assertEqual(ret, 2)
        err_out = json.loads(stdout_buf.getvalue())
        self.assertEqual(err_out, {"error": "invalid_arguments"})


if __name__ == "__main__":
    unittest.main()
