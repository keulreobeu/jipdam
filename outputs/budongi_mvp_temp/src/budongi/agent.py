"""Small-model orchestrator using a local OpenAI-compatible chat endpoint."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .tools import TOOL_SCHEMA_VERSION, TOOL_SPECS, execute_tool

MAX_TOOL_CALLS = 5
SYSTEM_PROMPT_VERSION = "tool_prompt_v4"
ANSWER_GUARD_VERSION = "answer_grounding_v2"
SYSTEM_PROMPT = """당신은 검증된 2023년 부동산 스냅샷만 이용하는 도우미입니다.
FACT, FILTER, COMPARE 질문에는 제공된 세 가지 도구를 사용하세요.
도구 결과의 ID, 금액(원), 면적(㎡), 계약일, 출처를 그대로 유지하세요.
거래 가격의 출처는 transaction_source와 transaction_source_id를 사용하고,
단지 기본정보의 출처와 구분하세요. 백엔드 도구가 제공하지 않은 차액·비율은 계산해 쓰지 마세요.
가격은 실거래 기록이 있을 때만 실거래가라고 부르세요.
도구 인자의 금액은 원 단위 정수로 쓰세요(예: 10억 원은 1000000000). 면적은 숫자로 쓰고,
limit은 생략하거나 1부터 20 사이의 정수로 쓰세요. 도구 오류가 나면 인자를 고쳐 다시 호출하세요.
데이터에 없는 학군 평가, 미래 가격, 투자수익을 주장하지 마세요.
결과가 없으면 없다고 말하고, 질문이 모호하면 필요한 조건을 물으세요.
답변에는 기준일과 출처를 포함하세요. ID를 언급할 때는 `단지 ID: 값` 또는 `거래 ID: 값`, 출처는 `출처: source/source_id` 형식으로 명시하세요. SQL을 작성하지 마세요."""

PRICE_CLAIM = re.compile(r"(?<![\d,])(?P<number>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>만원|만\s*원|억|원)")
PERCENT_CLAIM = re.compile(r"\d+(?:\.\d+)?\s*(?:%|퍼센트)")
DATE_CLAIM = re.compile(r"(?<!\d)20\d{2}-\d{2}-\d{2}(?!\d)")
YEAR_CLAIM = re.compile(r"(?<![\w])(?P<year>20\d{2})년")
ID_CLAIM = re.compile(
    r"(?P<kind>단지\s*ID|아파트\s*ID|거래\s*ID)\s*[:：]?\s*"
    r"(?P<value>[^\s,，。;；/]+)", re.IGNORECASE
)
SOURCE_CLAIM = re.compile(
    r"(?:출처|source)\s*[:：]?\s*(?P<source>[\w.-]+)\s*/\s*(?P<source_id>[\w.-]+)",
    re.IGNORECASE,
)


def _unsupported_price_claims(answer: str, allowed: set[int]) -> list[str]:
    unsupported = []
    for match in PRICE_CLAIM.finditer(answer):
        factor = 100_000_000 if match["unit"] == "억" else 10_000 if match["unit"].startswith("만") else 1
        amount = int(Decimal(match["number"].replace(",", "")) * factor)
        if amount not in allowed:
            unsupported.append(match.group())
    unsupported.extend(match.group() for match in PERCENT_CLAIM.finditer(answer))
    return sorted(set(unsupported))


def _answer_grounding_failures(
    answer: str, results: list[dict[str, Any]], allowed_prices: set[int]
) -> list[dict[str, str]]:
    rows = [row for result in results for row in result.get("rows", [])]
    allowed_dates = {result["snapshot"].get("snapshot_date") for result in results}
    allowed_dates.update(
        value for row in rows for key, value in row.items()
        if "date" in key and isinstance(value, str) and re.fullmatch(r"20\d{2}-\d{2}-\d{2}", value)
    )
    allowed_dates.discard(None)
    allowed_years = {value[:4] for value in allowed_dates}
    allowed_apartment_ids = {str(row["apartment_id"]) for row in rows if row.get("apartment_id") is not None}
    allowed_transaction_ids = {str(row["transaction_id"]) for row in rows if row.get("transaction_id") is not None}
    allowed_sources = set()
    for row in rows:
        for source_key, source_id_key in (("source", "source_id"), ("transaction_source", "transaction_source_id")):
            source, source_id = row.get(source_key), row.get(source_id_key)
            if source is not None and source_id is not None:
                allowed_sources.add((str(source), str(source_id)))

    failures: list[dict[str, str]] = []

    def add(kind: str, claim: str) -> None:
        failure = {"type": kind, "claim": claim}
        if failure not in failures:
            failures.append(failure)

    for claim in _unsupported_price_claims(answer, allowed_prices):
        kind = "unsupported_percentage" if PERCENT_CLAIM.fullmatch(claim) else "unsupported_price"
        add(kind, claim)
    for match in DATE_CLAIM.finditer(answer):
        if match.group() not in allowed_dates:
            add("unsupported_date", match.group())
    for match in YEAR_CLAIM.finditer(answer):
        if match["year"] not in allowed_years:
            add("unsupported_date", match.group())
    for match in ID_CLAIM.finditer(answer):
        kind = "apartment_id" if "거래" not in match["kind"] else "transaction_id"
        allowed = allowed_apartment_ids if kind == "apartment_id" else allowed_transaction_ids
        claim = match["value"].rstrip(".,;:!?")
        if claim not in allowed:
            add(f"unsupported_{kind}", claim)
    for match in SOURCE_CLAIM.finditer(answer):
        pair = (match["source"], match["source_id"].rstrip(".,;:!?"))
        if pair not in allowed_sources:
            add("unsupported_source", f"{pair[0]}/{pair[1]}")
    return failures


def _safe_tool_summary(results: list[dict[str, Any]]) -> str:
    if not results:
        return "검증된 조회 결과가 없어 답변을 확인할 수 없습니다."
    snapshot_date = results[0]["snapshot"]["snapshot_date"]
    rows = [row for result in results for row in result["rows"]]
    if not rows:
        return f"조건에 맞는 조회 결과가 없습니다. 기준일: {snapshot_date}."
    lines = []
    seen = set()
    for row in rows:
        key = (row.get("apartment_id"), row.get("transaction_id"), row.get("contract_date"))
        if key in seen:
            continue
        seen.add(key)
        identity = row.get("name") or row.get("apartment_id") or row.get("transaction_id")
        fields = [str(identity)]
        if row.get("price_krw") is not None:
            fields.append(f"거래가 {row['price_krw']:,}원")
        if row.get("contract_date"):
            fields.append(f"계약일 {row['contract_date']}")
        source = row.get("transaction_source") or row.get("source")
        source_id = row.get("transaction_source_id") or row.get("source_id")
        if source and source_id:
            fields.append(f"출처 {source}/{source_id}")
        lines.append("- " + ", ".join(fields))
        if len(lines) == 20:
            break
    return "검증된 조회 결과:\n" + "\n".join(lines) + f"\n기준일: {snapshot_date}."


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _local_chat(endpoint: str, model: str, messages: list[dict[str, Any]], timeout: int) -> dict[str, Any]:
    parsed = urlparse(endpoint)
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if os.environ.get("BUDONGI_ALLOW_DOCKER_OLLAMA") == "1":
        local_hosts.add("ollama")
    if parsed.scheme != "http" or parsed.hostname not in local_hosts:
        raise ValueError("Only a local HTTP model endpoint is accepted")
    if not model.strip():
        raise ValueError("model must be provided")
    payload = {"model": model, "messages": messages, "tools": TOOL_SPECS,
               "tool_choice": "auto", "temperature": 0, "stream": False}
    request = Request(endpoint, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read(2_000_000))
    return data["choices"][0]["message"]


def ask(
    connection: sqlite3.Connection, *, snapshot_id: str, question: str,
    model: str, endpoint: str, run_id: str, output_dir: Path, timeout: int = 30,
    question_id: str | None = None,
) -> dict[str, Any]:
    if not question.strip():
        raise ValueError("question must not be empty")
    request_id = uuid.uuid4().hex
    started = time.perf_counter()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    calls: list[dict[str, Any]] = []
    answer = ""
    status = "ok"
    had_tool_error = False
    successful_results: list[dict[str, Any]] = []
    allowed_prices: set[int] = set()
    for _ in range(MAX_TOOL_CALLS + 1):
        response = _local_chat(endpoint, model, messages, timeout)
        proposed = response.get("tool_calls") or []
        if not proposed:
            answer = response.get("content") or ""
            if not calls:
                status = "no_tool_called"
                answer = "검증된 조회 결과가 없어 현재 제공된 데이터만으로는 답변을 확인할 수 없습니다."
            break
        messages.append(response)
        for call in proposed:
            name = call.get("function", {}).get("name", "")
            started_call = time.perf_counter()
            event: dict[str, Any] = {"request_id": request_id, "run_id": run_id, "tool": name,
                                     "snapshot_id": snapshot_id, "started_at": datetime.now(timezone.utc).isoformat()}
            if len(calls) >= MAX_TOOL_CALLS:
                result: dict[str, Any] = {"error": "tool_call_limit"}
                event["status"] = "limit"
                status = "tool_call_limit"
            else:
                try:
                    arguments = json.loads(call.get("function", {}).get("arguments") or "{}")
                    event["proposed_arguments"] = arguments
                    result = execute_tool(connection, snapshot_id, name, arguments)
                    successful_results.append(result)
                    allowed_prices.update(row["price_krw"] for row in result["rows"]
                                          if row.get("price_krw") is not None)
                    if "max_price_krw" in result["arguments"]:
                        allowed_prices.add(result["arguments"]["max_price_krw"])
                    event.update({"status": "ok", "arguments": result["arguments"],
                                  "row_count": result["row_count"],
                                  "returned_ids": [row.get("transaction_id") if name == "search_transactions"
                                                   else row.get("apartment_id") for row in result["rows"]]})
                    if had_tool_error:
                        status = "recovered_tool_error"
                except (ValueError, TypeError, json.JSONDecodeError, sqlite3.Error) as exc:
                    result = {"error": type(exc).__name__, "message": str(exc)}
                    event.update({"status": "error", "error": result["message"], "row_count": 0})
                    had_tool_error = True
                    status = "tool_error"
            event["duration_ms"] = round((time.perf_counter() - started_call) * 1000, 2)
            calls.append(event)
            _append_jsonl(output_dir / "tool_runs" / f"{run_id}.jsonl", event)
            messages.append({"role": "tool", "tool_call_id": call.get("id", ""),
                             "name": name, "content": json.dumps(result, ensure_ascii=False)})
        if len(calls) >= MAX_TOOL_CALLS:
            status = "tool_call_limit"
            break
    if status in {"tool_error", "tool_call_limit"}:
        answer = "조회 과정이 완료되지 않아 현재 제공된 데이터만으로는 답변을 확인할 수 없습니다."
    elif not answer:
        answer = "현재 제공된 데이터만으로는 답변을 확인할 수 없습니다."
    grounding_failures: list[dict[str, str]] = []
    grounding_status = "not_run"
    if successful_results and status not in {"tool_error", "tool_call_limit"}:
        grounding_failures = _answer_grounding_failures(answer, successful_results, allowed_prices)
        grounding_status = "failed" if grounding_failures else "passed"
        if grounding_failures:
            answer = _safe_tool_summary(successful_results)
            failure_types = {failure["type"] for failure in grounding_failures}
            status = ("unsupported_numeric_claim" if failure_types <= {"unsupported_price", "unsupported_percentage"}
                      else "unsupported_grounding_claim")
    record = {"request_id": request_id, "run_id": run_id, "question_id": question_id,
              "question": question,
              "answer": answer, "status": status, "snapshot_id": snapshot_id,
              "model_version": model, "tool_schema_version": TOOL_SCHEMA_VERSION,
              "prompt_version": SYSTEM_PROMPT_VERSION,
              "answer_guard_version": ANSWER_GUARD_VERSION,
              "unsupported_claims": [failure["claim"] for failure in grounding_failures],
              "grounding_check": {"status": grounding_status, "failures": grounding_failures},
              "tool_calls": calls,
              "latency_ms": round((time.perf_counter() - started) * 1000, 2)}
    _append_jsonl(output_dir / "runs" / f"{run_id}.jsonl", record)
    return record
