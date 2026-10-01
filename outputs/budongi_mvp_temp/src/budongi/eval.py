"""First-pass deterministic evaluation of tool selection, arguments and entities."""

from __future__ import annotations

import csv
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from datetime import date


NUMBER_CLAIM = re.compile(r"(?<![\d,])(?P<number>-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(?![\d,])")
DATE_CLAIM = re.compile(
    r"(?<!\d)(?P<year>20\d{2})(?:[-./]\s*(?P<month>\d{1,2})[-./]\s*(?P<day>\d{1,2})"
    r"|년\s*(?P<month_ko>\d{1,2})\s*월\s*(?P<day_ko>\d{1,2})\s*일?)(?!\d)"
)
DATE_SHAPE = re.compile(r"20\d{2}(?:[-./]\s*\d{1,2}[-./]\s*\d{1,2}|년\s*\d{1,2}\s*월\s*\d{1,2}\s*일?)")
UNIT_ALIASES = {
    "m": ("m", "미터"),
    "㎡": ("㎡", "m²", "제곱미터"),
    "원": ("원",),
    "만원": ("만원", "만 원"),
    "년": ("년", "년식"),
}
MONEY_UNIT_PATTERNS = {
    "원": ((r"억\s*원?(?!\s*\d)", Decimal("100000000")),
           (r"만\s*원(?!\w)", Decimal("10000")),
           (r"원(?!\w)", Decimal("1"))),
    "만원": ((r"억\s*원?(?!\s*\d)", Decimal("10000")),
             (r"만\s*원(?!\w)", Decimal("1")),
             (r"원(?!\w)", Decimal("0.0001"))),
}
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?。！？])\s+|[\r\n]+")


def _entity_alias_present(text: str, alias: str) -> bool:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", alias):
        return re.search(rf"(?<![A-Za-z0-9_-]){re.escape(alias)}(?![A-Za-z0-9_-])", text, re.IGNORECASE) is not None
    normalized_text = " ".join(text.casefold().split())
    normalized_alias = " ".join(alias.casefold().split())
    return bool(normalized_alias) and normalized_alias in normalized_text


def _date_values(text: str) -> set[str]:
    values = set()
    for match in DATE_CLAIM.finditer(text):
        month = match["month"] or match["month_ko"]
        day = match["day"] or match["day_ko"]
        try:
            values.add(date(int(match["year"]), int(month), int(day)).isoformat())
        except ValueError:
            continue
    return values


def _required_fact_result(answer: str, fact: Any) -> dict[str, Any]:
    if (not isinstance(fact, dict) or "value" not in fact
            or not isinstance(fact.get("entity"), str) or not fact["entity"].strip()
            or not isinstance(fact.get("field"), str) or not fact["field"].strip()):
        return {"status": "not_measured", "reason": "malformed_fact"}
    value = fact.get("value")
    unit = fact.get("unit")
    tolerance = fact.get("tolerance", 0)
    result = {key: fact.get(key) for key in ("entity", "entity_aliases", "field", "value", "unit", "tolerance") if key in fact}
    if "tolerance" in fact:
        try:
            tolerance_value = Decimal(str(tolerance))
        except InvalidOperation:
            return {**result, "status": "not_measured", "reason": "invalid_numeric_range"}
        if not tolerance_value.is_finite() or tolerance_value < 0:
            return {**result, "status": "not_measured", "reason": "invalid_numeric_range"}
    if value is None or isinstance(value, bool):
        return {**result, "status": "not_measured", "reason": "unsupported_value_type"}
    if unit is not None and (not isinstance(unit, str) or unit not in UNIT_ALIASES):
        return {**result, "status": "not_measured", "reason": "unsupported_unit"}

    aliases = fact.get("entity_aliases", [fact["entity"]])
    if (not isinstance(aliases, list) or not aliases
            or any(not isinstance(alias, str) or not alias.strip() for alias in aliases)):
        return {**result, "status": "not_measured", "reason": "malformed_entity_aliases"}
    sentences = SENTENCE_BOUNDARY.split(answer)
    relevant_sentences = [sentence for sentence in sentences
                          if any(_entity_alias_present(sentence, alias) for alias in aliases)]
    if not relevant_sentences:
        return {**result, "status": "missing", "reason": "entity_not_mentioned"}
    relevant_answer = "\n".join(relevant_sentences)

    if isinstance(value, str):
        expected_dates = _date_values(value)
        if DATE_SHAPE.search(value) and not expected_dates:
            return {**result, "status": "not_measured", "reason": "invalid_date"}
        remainder = DATE_CLAIM.sub("", value).strip(" \t.,;:()[]")
        if expected_dates and not remainder:
            matched = bool(expected_dates & _date_values(relevant_answer))
        else:
            normalized_answer = " ".join(relevant_answer.casefold().split())
            normalized_value = " ".join(value.casefold().split())
            matched = bool(normalized_value) and normalized_value in normalized_answer
        return {**result, "status": "matched" if matched else "missing"}

    if not isinstance(value, (int, float)) or not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool):
        return {**result, "status": "not_measured", "reason": "unsupported_numeric_type"}
    if unit is None:
        return {**result, "status": "not_measured", "reason": "numeric_unit_required"}
    try:
        expected = Decimal(str(value))
        allowed_difference = Decimal(str(tolerance))
    except InvalidOperation:
        return {**result, "status": "not_measured", "reason": "invalid_numeric_range"}
    if not expected.is_finite() or not allowed_difference.is_finite() or allowed_difference < 0:
        return {**result, "status": "not_measured", "reason": "invalid_numeric_range"}

    unit_aliases = UNIT_ALIASES.get(unit, ())
    for match in NUMBER_CLAIM.finditer(relevant_answer):
        candidate = match["number"].replace(",", "")
        suffix = relevant_answer[match.end():]
        if unit in MONEY_UNIT_PATTERNS:
            for pattern, multiplier in MONEY_UNIT_PATTERNS[unit]:
                if re.match(rf"\s*{pattern}", suffix):
                    try:
                        if abs(Decimal(candidate) * multiplier - expected) <= allowed_difference:
                            return {**result, "status": "matched"}
                    except InvalidOperation:
                        break
            continue
        if unit_aliases and not any(re.match(rf"\s*{re.escape(unit_alias)}(?![A-Za-z0-9²])", suffix, re.IGNORECASE)
                                    for unit_alias in unit_aliases):
            continue
        try:
            if abs(Decimal(candidate) - expected) <= allowed_difference:
                return {**result, "status": "matched"}
        except InvalidOperation:
            continue
    return {**result, "status": "missing"}


def _required_facts_result(answer: str, required_facts: Any) -> dict[str, Any]:
    if not isinstance(required_facts, list) or not required_facts:
        return {"status": "not_measured", "facts": [], "matched": 0, "missing": 0, "not_measured": 0}
    facts = [_required_fact_result(answer, fact) for fact in required_facts]
    matched = sum(fact["status"] == "matched" for fact in facts)
    missing = sum(fact["status"] == "missing" for fact in facts)
    not_measured = sum(fact["status"] == "not_measured" for fact in facts)
    status = "failed" if missing else "not_measured" if not_measured else "passed"
    return {"status": status, "facts": facts, "matched": matched, "missing": missing,
            "not_measured": not_measured}


def _jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def evaluate(golden_path: Path, run_path: Path, report_path: Path) -> dict[str, Any]:
    golden = _jsonl(golden_path)
    predictions = {row["question_id"]: row for row in _jsonl(run_path)}
    if len(predictions) != len(_jsonl(run_path)):
        raise ValueError("Duplicate question_id in prediction run")
    details = []
    grounding_counts = {"passed": 0, "failed": 0, "not_run": 0, "not_measured": 0}
    required_fact_status_counts = {"passed": 0, "failed": 0, "not_measured": 0}
    required_fact_counts = {"matched": 0, "missing": 0, "not_measured": 0}
    for item in golden:
        prediction = predictions.get(item["id"], {})
        prediction_present = item["id"] in predictions
        expected = item.get("expected_tool_calls", [])
        actual = prediction.get("tool_calls", [])
        expected_names = [call["tool"] for call in expected]
        actual_names = [call["tool"] for call in actual]
        tool_match = expected_names == actual_names
        args_match = tool_match and all(
            a.get("arguments") == e.get("arguments") for a, e in zip(actual, expected)
        )
        returned = {entity for call in actual for entity in call.get("returned_ids", []) if entity}
        expected_entities = set(item.get("expected_entities", []))
        entity_precision = len(returned & expected_entities) / len(returned) if returned else float(not expected_entities)
        entity_recall = len(returned & expected_entities) / len(expected_entities) if expected_entities else float(not returned)
        grounding_check = prediction.get("grounding_check")
        grounding_status = grounding_check.get("status") if isinstance(grounding_check, dict) else None
        if grounding_status not in {"passed", "failed", "not_run"}:
            grounding_status = "not_measured"
        grounding_counts[grounding_status] += 1
        failures = grounding_check.get("failures", []) if isinstance(grounding_check, dict) else []
        required_facts = item.get("required_facts", [])
        if prediction_present:
            facts_result = _required_facts_result(str(prediction.get("answer") or ""), required_facts)
        else:
            unmeasured_facts = required_facts if isinstance(required_facts, list) else []
            count_unmeasured = len(unmeasured_facts)
            facts_result = {"status": "not_measured", "facts": [
                {**({key: fact.get(key) for key in ("entity", "entity_aliases", "field", "value", "unit", "tolerance")
                     if key in fact} if isinstance(fact, dict) else {}),
                 "status": "not_measured", "reason": "missing_prediction"}
                for fact in unmeasured_facts
            ], "matched": 0, "missing": 0, "not_measured": count_unmeasured}
        required_fact_status_counts[facts_result["status"]] += 1
        for fact_status in required_fact_counts:
            required_fact_counts[fact_status] += facts_result[fact_status]
        details.append({"question_id": item["id"], "task_type": item.get("task_type", ""),
                        "tool_selection_match": int(tool_match), "argument_exact_match": int(args_match),
                        "entity_precision": round(entity_precision, 4), "entity_recall": round(entity_recall, 4),
                        "answer_grounding_status": grounding_status,
                        "answer_grounding_failure_count": len(failures),
                        "required_fact_status": facts_result["status"],
                        "required_facts_matched": facts_result["matched"],
                        "required_facts_missing": facts_result["missing"],
                        "required_facts_not_measured": facts_result["not_measured"],
                        "required_fact_details": json.dumps(facts_result["facts"], ensure_ascii=False, sort_keys=True),
                        "generation_check": "full_claim_precision_pending"})
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(details[0]) if details else ["question_id"])
        writer.writeheader()
        writer.writerows(details)
    count = len(details)
    checked = grounding_counts["passed"] + grounding_counts["failed"]
    required_checked = required_fact_counts["matched"] + required_fact_counts["missing"]
    return {"samples": count,
            "tool_selection_accuracy": sum(row["tool_selection_match"] for row in details) / count if count else None,
            "argument_exact_accuracy": sum(row["argument_exact_match"] for row in details) / count if count else None,
            "entity_precision_mean": sum(row["entity_precision"] for row in details) / count if count else None,
            "entity_recall_mean": sum(row["entity_recall"] for row in details) / count if count else None,
            "answer_grounding": {"passed": grounding_counts["passed"], "failed": grounding_counts["failed"],
                                 "not_run": grounding_counts["not_run"],
                                 "not_measured": grounding_counts["not_measured"],
                                 "checked_samples": checked,
                                 "pass_rate": grounding_counts["passed"] / checked if checked else None},
            "required_fact_coverage": {
                "passed_questions": required_fact_status_counts["passed"],
                "failed_questions": required_fact_status_counts["failed"],
                "not_measured_questions": required_fact_status_counts["not_measured"],
                "matched_facts": required_fact_counts["matched"],
                "missing_facts": required_fact_counts["missing"],
                "not_measured_facts": required_fact_counts["not_measured"],
                "measured_facts": required_checked,
                "coverage_rate": round(required_fact_counts["matched"] / required_checked, 4) if required_checked else None},
            "generation": "required_fact_coverage_measured_full_claim_precision_pending"}
