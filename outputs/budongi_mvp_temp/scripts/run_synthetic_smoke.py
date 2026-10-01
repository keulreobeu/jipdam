"""Exercise FACT, NO_MATCH, and COMPARE with a fictional local snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from budongi.agent import ask
from budongi.storage import connect
from scripts.make_synthetic_smoke import SNAPSHOT_ID


CASES = {
    "filter": "가상 데이터에서 서울 강서구에 있는 전용 84㎡ 아파트 중 최근 실거래가가 10억 원 이하인 단지를 찾아줘.",
    "fact": "가상 데이터에서 단지 ID APT_A의 최신 실거래 가격과 계약일을 알려줘.",
    "no_match": "가상 데이터에서 서울 강서구 전용 84㎡이며 최근 실거래가가 5억 원 이하인 단지를 찾아줘.",
    "compare": "가상 데이터에서 단지 ID APT_A와 APT_B의 최신 실거래 가격을 비교해줘.",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3.5:4b-q4_K_M")
    parser.add_argument("--root", type=Path, default=Path(".local_runtime/synthetic_smoke"))
    parser.add_argument("--run-prefix", default="smoke_v2")
    parser.add_argument("--cases", nargs="+", choices=list(CASES), default=list(CASES))
    args = parser.parse_args()
    connection = connect(args.root / "serving.sqlite3")
    summary = []
    try:
        for case in args.cases:
            question = CASES[case]
            run_id = f"{args.run_prefix}_{case}"
            if (args.root / "runs" / f"{run_id}.jsonl").exists():
                raise FileExistsError(f"Smoke run already exists: {run_id}")
            result = ask(connection, snapshot_id=SNAPSHOT_ID, question=question,
                         model=args.model, endpoint="http://127.0.0.1:11434/v1/chat/completions",
                         run_id=run_id, output_dir=args.root, timeout=120, question_id=case)
            summary.append({key: result[key] for key in ("question_id", "question", "answer",
                                                       "status", "tool_calls", "latency_ms")})
            print(json.dumps({"case": case, "status": result["status"],
                              "tools": [call["tool"] for call in result["tool_calls"]],
                              "latency_ms": result["latency_ms"]}, ensure_ascii=False), flush=True)
    finally:
        connection.close()
    (args.root / f"{args.run_prefix}_{'-'.join(args.cases)}_summary.json").write_text(
        json.dumps({"test_data": "fictional", "is_real_evaluation": False,
                    "cases": summary}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
