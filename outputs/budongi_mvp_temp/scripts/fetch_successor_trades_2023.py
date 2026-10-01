"""Fetch 2023 trade months under successor district codes found by probes."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from budongi.district_codes import SUCCESSOR_QUERY_CODES
from budongi.public_data import PublicDataError, fetch_molit
from scripts.fetch_catalog_trades_2023 import verify_copy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/provisional/api/molit_2023_successors"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    # Suwon's four constituent districts are already in the catalog collection.
    originals = {code: successors for code, successors in SUCCESSOR_QUERY_CODES.items()
                 if code != "41110"}
    codes = sorted({code for successors in originals.values() for code in successors})
    print(json.dumps({"source_codes": originals, "query_codes": codes,
                      "queries": len(codes) * 12}, ensure_ascii=False), flush=True)
    if not args.execute:
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = args.output_dir / "plan.json"
    scope = {"source_codes": originals, "query_codes": codes, "year": 2023,
             "status": "retrieval_time_copy_unverified",
             "reason": "Current API returns zero rows for historical districts after boundary changes."}
    if plan_path.exists():
        if json.loads(plan_path.read_text(encoding="utf-8")) != scope:
            raise ValueError("Existing successor plan differs")
    else:
        plan_path.write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count = 0
    rows = 0
    for code in codes:
        for number in range(1, 13):
            month = f"2023{number:02d}"
            folder = args.output_dir / code / month
            if not folder.exists():
                for attempt in range(3):
                    try:
                        fetch_molit(lawd_cd=code, deal_ymd=month, output_dir=folder)
                        break
                    except PublicDataError:
                        if folder.exists() or attempt == 2:
                            raise
                        time.sleep(2 ** attempt)
                time.sleep(0.15)
            rows += verify_copy(folder, code, month)
            count += 1
        print(json.dumps({"district": code, "verified_queries": count,
                          "verified_rows": rows}), flush=True)
    print(json.dumps({"complete": True, "verified_queries": count,
                      "verified_rows": rows}), flush=True)


if __name__ == "__main__":
    main()
