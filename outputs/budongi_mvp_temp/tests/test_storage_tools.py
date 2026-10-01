from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from budongi.agent import _unsupported_price_claims, ask
from budongi.cli import main as cli_main
from budongi.eval import evaluate
from budongi.storage import connect, import_snapshot, inspect_legacy
from budongi.tools import execute_tool


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class DataToolContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = connect(self.root / "serving.sqlite3")
        self.addCleanup(self.db.close)
        self.apartments = self.root / "apartments.csv"
        self.transactions = self.root / "transactions.csv"
        write_csv(self.apartments,
                  ["apartment_id", "name", "address", "built_year", "source", "source_id",
                   "valid_date", "station_name", "station_distance_m"],
                  [{"apartment_id": "APT_A", "name": "테스트A", "address": "서울특별시 강서구 마곡동 1",
                    "built_year": "2010", "source": "synthetic_test", "source_id": "A",
                    "valid_date": "2023-12-31", "station_name": "가상역", "station_distance_m": "350"},
                   {"apartment_id": "APT_B", "name": "테스트B", "address": "서울특별시 강서구 마곡동 2",
                    "built_year": "2015", "source": "synthetic_test", "source_id": "B",
                    "valid_date": "2023-12-31"}])
        write_csv(self.transactions,
                  ["transaction_id", "apartment_id", "contract_date", "price_krw", "area_sqm",
                   "status", "source", "source_id", "valid_date", "changed_date"],
                  [{"transaction_id": "T1", "apartment_id": "APT_A", "contract_date": "2023-01-10",
                    "price_krw": "800000000", "area_sqm": "84", "status": "valid",
                    "source": "synthetic_test", "source_id": "EVENT_X", "valid_date": "2023-01-15"},
                   {"transaction_id": "T2", "apartment_id": "APT_A", "contract_date": "2023-01-10",
                    "price_krw": "800000000", "area_sqm": "84", "status": "canceled",
                    "source": "synthetic_test", "source_id": "EVENT_X", "valid_date": "2023-02-01",
                    "changed_date": "2023-02-01"},
                   {"transaction_id": "T3", "apartment_id": "APT_A", "contract_date": "2023-11-01",
                    "price_krw": "900000000", "area_sqm": "84", "status": "corrected",
                    "source": "synthetic_test", "source_id": "EVENT_Y", "valid_date": "2023-11-10"}])
        import_snapshot(self.db, snapshot_id="fixture_2023_v1", snapshot_date="2023-12-31",
                        apartments_csv=self.apartments, transactions_csv=self.transactions)

    def test_canceled_revision_is_excluded(self) -> None:
        result = execute_tool(self.db, "fixture_2023_v1", "search_transactions", {"apartment_id": "APT_A"})
        self.assertEqual([row["transaction_id"] for row in result["rows"]], ["T3"])

    def test_latest_valid_price_filters_apartments(self) -> None:
        result = execute_tool(self.db, "fixture_2023_v1", "search_apartments",
                              {"district": "강서구", "max_price_krw": 1_000_000_000, "area_sqm": 84})
        self.assertEqual([row["apartment_id"] for row in result["rows"]], ["APT_A"])
        self.assertEqual(result["rows"][0]["price_krw"], 900_000_000)

    def test_detail_preserves_source_and_location(self) -> None:
        result = execute_tool(self.db, "fixture_2023_v1", "get_apartment_detail", {"apartment_id": "APT_A"})
        self.assertEqual(result["rows"][0]["source_id"], "A")
        self.assertEqual(result["rows"][0]["transaction_source_id"], "EVENT_Y")
        self.assertEqual(result["rows"][0]["station_distance_m"], 350)

    def test_arguments_are_validated_and_sql_is_bound(self) -> None:
        with self.assertRaises(ValueError):
            execute_tool(self.db, "fixture_2023_v1", "search_apartments", {"limit": 21})
        with self.assertRaises(ValueError):
            execute_tool(self.db, "fixture_2023_v1", "search_apartments", {"unapproved": 1})
        result = execute_tool(self.db, "fixture_2023_v1", "search_apartments",
                              {"district": "강서구' OR 1=1 --"})
        self.assertEqual(result["row_count"], 0)

    def test_snapshot_is_immutable_and_cutoff_enforced(self) -> None:
        with self.assertRaises(Exception):
            import_snapshot(self.db, snapshot_id="fixture_2023_v1", snapshot_date="2023-12-31",
                            apartments_csv=self.apartments, transactions_csv=self.transactions)
        with self.assertRaises(ValueError):
            import_snapshot(self.db, snapshot_id="future", snapshot_date="2024-01-01",
                            apartments_csv=self.apartments, transactions_csv=self.transactions)

    def test_legacy_supply_price_is_only_reported(self) -> None:
        legacy = self.root / "legacy.csv"
        write_csv(legacy, ["문서ID", "아파트명", "공급액(만원)"],
                  [{"문서ID": "A", "아파트명": "테스트A", "공급액(만원)": "80000"}])
        report = inspect_legacy(legacy)
        self.assertEqual(report["rows"], 1)
        self.assertIn("공급액(만원)", report["available_fields"])

    def test_deterministic_evaluation_marks_generation_pending(self) -> None:
        gold = self.root / "gold.jsonl"
        run = self.root / "run.jsonl"
        gold.write_text(json.dumps({"id": "q1", "task_type": "FILTER",
                                    "expected_tool_calls": [{"tool": "search_apartments", "arguments": {"district": "강서구"}}],
                                    "expected_entities": ["APT_A"],
                                    "required_facts": [
                                        {"entity": "APT_A", "field": "station_distance", "value": 350, "unit": "m", "tolerance": 0,
                                         "entity_aliases": ["APT_A"]},
                                        {"entity": "APT_A", "field": "contract_date", "value": "2023-01-10",
                                         "entity_aliases": ["APT_A"]},
                                        {"entity": "APT_A", "field": "price_krw", "value": 900000000, "unit": "원",
                                         "entity_aliases": ["APT_A"]}
                                    ]}, ensure_ascii=False) + "\n", encoding="utf-8")
        run.write_text(json.dumps({"question_id": "q1", "tool_calls": [{"tool": "search_apartments",
                            "arguments": {"district": "강서구"}, "returned_ids": ["APT_A"]}],
                            "answer": "APT_A 단지는 가상역까지 350m이며 계약일은 2023년 1월 10일, 거래가는 9억원입니다.",
                            "grounding_check": {"status": "passed", "failures": []}}, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        result = evaluate(gold, run, self.root / "report.csv")
        self.assertEqual(result["tool_selection_accuracy"], 1.0)
        self.assertEqual(result["answer_grounding"]["pass_rate"], 1.0)
        self.assertEqual(result["required_fact_coverage"]["matched_facts"], 3)
        self.assertEqual(result["required_fact_coverage"]["coverage_rate"], 1.0)
        self.assertEqual(result["generation"], "required_fact_coverage_measured_full_claim_precision_pending")

    def test_evaluation_keeps_unmeasured_and_not_run_separate_from_pass(self) -> None:
        gold = self.root / "gold_states.jsonl"
        run = self.root / "run_states.jsonl"
        gold_items = [
            {"id": "q1", "task_type": "FACT", "required_facts": [
                {"entity": "APT_A", "entity_aliases": ["APT_A"], "field": "distance", "value": 350, "unit": "m", "tolerance": 10}]},
            {"id": "q2", "task_type": "FACT", "required_facts": [
                {"entity": "APT_A", "entity_aliases": ["APT_A"], "field": "contract_date", "value": "2023-11-01"}]},
            {"id": "q3", "task_type": "FACT", "required_facts": [
                {"entity": "APT_A", "entity_aliases": ["APT_A"], "field": "distance", "value": 0.35, "unit": "km"},
                {"entity": "APT_A", "entity_aliases": ["APT_A"], "field": "distance", "value": 350},
                {"entity": "APT_A", "entity_aliases": ["APT_A"], "field": "distance", "value": 350, "unit": "m", "tolerance": -1}]},
            {"id": "q4", "task_type": "FACT", "required_facts": [
                {"entity": "APT_A", "entity_aliases": ["APT_A"], "field": "count", "value": 2}]},
            {"id": "q5", "task_type": "FACT", "required_facts": [
                {"entity": "APT_A", "entity_aliases": ["APT_A"], "field": "distance", "value": 350, "unit": "m", "tolerance": 0}]},
            {"id": "q6", "task_type": "FACT", "required_facts": [
                {"entity": "APT_A", "entity_aliases": ["APT_A"], "field": "distance", "value": 350, "unit": "m", "tolerance": 0}]},
        ]
        gold.write_text("".join(json.dumps(item) + "\n" for item in gold_items), encoding="utf-8")
        run.write_text("".join(json.dumps(record) + "\n" for record in [
            {"question_id": "q1", "answer": "APT_A 단지는 역까지 약 355미터입니다.",
             "grounding_check": {"status": "passed", "failures": []}},
            {"question_id": "q2", "answer": "APT_A 계약일은 2024-01-01입니다.",
             "grounding_check": {"status": "failed", "failures": [{"type": "unsupported_date", "claim": "2024-01-01"}]}},
            {"question_id": "q3", "answer": "APT_A 역까지 350m입니다.",
             "grounding_check": {"status": "not_run", "failures": []}},
            {"question_id": "q5", "answer": "APT_A 역까지 350.1m입니다.",
             "grounding_check": {"status": "passed", "failures": []}},
            {"question_id": "q6", "answer": "APT_B 역까지 350m입니다.",
             "grounding_check": {"status": "passed", "failures": []}},
        ]), encoding="utf-8")
        result = evaluate(gold, run, self.root / "report_states.csv")
        self.assertEqual(result["answer_grounding"]["passed"], 3)
        self.assertEqual(result["answer_grounding"]["failed"], 1)
        self.assertEqual(result["answer_grounding"]["not_run"], 1)
        self.assertEqual(result["answer_grounding"]["not_measured"], 1)
        self.assertEqual(result["answer_grounding"]["pass_rate"], 0.75)
        self.assertEqual(result["required_fact_coverage"]["matched_facts"], 1)
        self.assertEqual(result["required_fact_coverage"]["missing_facts"], 3)
        self.assertEqual(result["required_fact_coverage"]["not_measured_facts"], 4)
        self.assertEqual(result["required_fact_coverage"]["measured_facts"], 4)
        self.assertEqual(result["required_fact_coverage"]["coverage_rate"], 0.25)
        self.assertEqual(result["generation"], "required_fact_coverage_measured_full_claim_precision_pending")

    def test_agent_executes_only_validated_tool_and_logs_it(self) -> None:
        responses = [
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_1", "type": "function", "function": {
                    "name": "get_apartment_detail", "arguments": '{"apartment_id":"APT_A"}'}}]},
            {"role": "assistant", "content": "테스트A의 계약일은 2023-11-01입니다.", "tool_calls": []},
        ]
        with patch("budongi.agent._local_chat", side_effect=responses):
            record = ask(self.db, snapshot_id="fixture_2023_v1", question="테스트A 거래?",
                         model="stub-4b", endpoint="http://127.0.0.1:11434/v1/chat/completions",
                         run_id="test", output_dir=self.root, question_id="q1")
        self.assertEqual(record["status"], "ok")
        self.assertEqual(record["tool_calls"][0]["returned_ids"], ["APT_A"])
        self.assertTrue((self.root / "tool_runs" / "test.jsonl").exists())

    def test_agent_accepts_dates_ids_and_source_pair_present_in_tool_result(self) -> None:
        responses = [
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_1", "type": "function", "function": {
                    "name": "get_apartment_detail", "arguments": '{"apartment_id":"APT_A"}'}}]},
            {"role": "assistant", "content": "기준일: 2023-12-31. 단지 ID: APT_A, 거래 ID: T3, 계약일 2023-11-01, 거래가 9억 원, 출처: synthetic_test/EVENT_Y.", "tool_calls": []},
        ]
        with patch("budongi.agent._local_chat", side_effect=responses):
            record = ask(self.db, snapshot_id="fixture_2023_v1", question="테스트A 거래를 알려줘",
                         model="stub-4b", endpoint="http://127.0.0.1:11434/v1/chat/completions",
                         run_id="test_grounding_pass", output_dir=self.root)
        self.assertEqual(record["grounding_check"]["status"], "passed")
        self.assertEqual(record["grounding_check"]["failures"], [])
        self.assertIn("APT_A", record["answer"])
        self.assertIn("9억 원", record["answer"])

    def test_agent_replaces_unsupported_date_ids_and_source_with_safe_summary(self) -> None:
        responses = [
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_1", "type": "function", "function": {
                    "name": "get_apartment_detail", "arguments": '{"apartment_id":"APT_A"}'}}]},
            {"role": "assistant", "content": "기준일: 2024-01-01. 단지 ID: APT_FAKE, 거래 ID: T99, 출처: synthetic_test/FAKE.", "tool_calls": []},
        ]
        with patch("budongi.agent._local_chat", side_effect=responses):
            record = ask(self.db, snapshot_id="fixture_2023_v1", question="테스트A 거래를 알려줘",
                         model="stub-4b", endpoint="http://127.0.0.1:11434/v1/chat/completions",
                         run_id="test_grounding_fail", output_dir=self.root)
        self.assertEqual(record["status"], "unsupported_grounding_claim")
        self.assertEqual(record["grounding_check"]["status"], "failed")
        self.assertEqual({failure["type"] for failure in record["grounding_check"]["failures"]},
                         {"unsupported_date", "unsupported_apartment_id", "unsupported_transaction_id", "unsupported_source"})
        self.assertNotIn("APT_FAKE", record["answer"])
        self.assertNotIn("2024-01-01", record["answer"])
        saved_record = json.loads((self.root / "runs" / "test_grounding_fail.jsonl").read_text(encoding="utf-8").strip())
        self.assertNotIn("APT_FAKE", saved_record["answer"])
        self.assertIn("unsupported_apartment_id", {failure["type"] for failure in saved_record["grounding_check"]["failures"]})

    def test_agent_does_not_accept_unverified_direct_answer(self) -> None:
        with patch("budongi.agent._local_chat", return_value={"role": "assistant", "content": "임의 사실", "tool_calls": []}):
            record = ask(self.db, snapshot_id="fixture_2023_v1", question="테스트A 거래?",
                         model="stub-4b", endpoint="http://127.0.0.1:11434/v1/chat/completions",
                         run_id="test_no_tool", output_dir=self.root)
        self.assertEqual(record["status"], "no_tool_called")
        self.assertNotIn("임의 사실", record["answer"])

    def test_agent_keeps_answer_after_correcting_invalid_tool_arguments(self) -> None:
        responses = [
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "bad", "type": "function", "function": {
                    "name": "search_apartments", "arguments": '{"district":"강서구","limit":100}'}}]},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "good", "type": "function", "function": {
                    "name": "search_apartments", "arguments": '{"district":"강서구","limit":20}'}}]},
            {"role": "assistant", "content": "가상 단지 2곳을 찾았습니다.", "tool_calls": []},
        ]
        with patch("budongi.agent._local_chat", side_effect=responses):
            record = ask(self.db, snapshot_id="fixture_2023_v1", question="강서구 단지는?",
                         model="stub-4b", endpoint="http://127.0.0.1:11434/v1/chat/completions",
                         run_id="test_recovery", output_dir=self.root)
        self.assertEqual(record["status"], "recovered_tool_error")
        self.assertEqual(record["answer"], "가상 단지 2곳을 찾았습니다.")
        self.assertEqual(record["tool_calls"][0]["proposed_arguments"]["limit"], 100)
        self.assertEqual(record["tool_calls"][1]["status"], "ok")

    def test_unsupported_comparison_amount_is_replaced_with_tool_facts(self) -> None:
        self.assertEqual(_unsupported_price_claims("9억 원과 900,000,000원", {900_000_000}), [])
        self.assertIn("2.86억", _unsupported_price_claims("차액 약 2.86억 원", {900_000_000}))
        responses = [
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "a", "type": "function", "function": {
                    "name": "get_apartment_detail", "arguments": '{"apartment_id":"APT_A"}'}}]},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "b", "type": "function", "function": {
                    "name": "get_apartment_detail", "arguments": '{"apartment_id":"APT_B"}'}}]},
            {"role": "assistant", "content": "APT_A는 9억 원, APT_B는 7억 원. 차액은 2.86억 원입니다.",
             "tool_calls": []},
        ]
        with patch("budongi.agent._local_chat", side_effect=responses):
            record = ask(self.db, snapshot_id="fixture_2023_v1", question="비교해줘",
                         model="stub-4b", endpoint="http://127.0.0.1:11434/v1/chat/completions",
                         run_id="test_unsupported_amount", output_dir=self.root)
        self.assertEqual(record["status"], "unsupported_numeric_claim")
        self.assertIn("900,000,000원", record["answer"])
        self.assertNotIn("2.86억", record["answer"])

    def test_doctor_does_not_mark_synthetic_fixture_ready_for_real_eval(self) -> None:
        output = io.StringIO()
        with patch("sys.argv", ["budongi", "--db", str(self.root / "serving.sqlite3"), "doctor"]), \
                redirect_stdout(output):
            cli_main()
        report = json.loads(output.getvalue())
        self.assertTrue(report["synthetic_only"])
        self.assertFalse(report["ready_for_real_eval"])


if __name__ == "__main__":
    unittest.main()
