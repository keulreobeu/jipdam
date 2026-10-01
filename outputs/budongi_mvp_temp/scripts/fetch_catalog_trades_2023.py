"""Fetch 2023 apartment trades for every district in the provisional catalog.

The copies are retrieval-time evidence, not a certified 2023-as-of snapshot.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

from budongi.district_codes import district_for_address, official_districts
from budongi.public_data import PublicDataError, _molit_rows, fetch_molit


def plan(catalog_path: Path, code_archive: Path) -> dict[str, object]:
    districts, code_hash = official_districts(code_archive)
    catalog_bytes = catalog_path.read_bytes()
    catalog = list(csv.DictReader(catalog_bytes.decode("utf-8-sig").splitlines()))
    by_code: dict[str, dict[str, object]] = defaultdict(lambda: {"names": set(), "apartment_ids": []})
    unresolved = []
    for apartment in catalog:
        code, name = district_for_address(apartment["address"], districts)
        if code is None:
            unresolved.append(apartment["provisional_apartment_id"])
            continue
        by_code[code]["names"].add(name)
        by_code[code]["apartment_ids"].append(apartment["provisional_apartment_id"])
    if unresolved:
        raise ValueError(f"Unmapped apartment IDs: {unresolved}")
    return {
        "status": "retrieval_time_copy_unverified",
        "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(),
        "official_code_archive_sha256": code_hash,
        "official_code_source": "https://www.code.go.kr/stdcode/regCodeL.do",
        "year": 2023,
        "apartment_count": len(catalog),
        "district_count": len(by_code),
        "districts": {
            code: {"official_names": sorted(value["names"]),
                   "apartment_ids": sorted(value["apartment_ids"])}
            for code, value in sorted(by_code.items())
        },
        "limitations": [
            "Official code archive is a current download with active/abolished flags but no effective dates.",
            "Each response is checked against its queried district and contract month.",
            "Historical district boundaries and individual apartment identity still need review.",
        ],
    }


def verify_copy(folder: Path, code: str, month: str) -> int:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest["filters"] != {"LAWD_CD": code, "DEAL_YMD": month}:
        raise ValueError(f"Unexpected query in {folder}")
    parsed_rows = []
    for page in manifest["pages"]:
        raw = (folder / page["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != page["sha256"]:
            raise ValueError(f"Raw response hash changed: {folder}")
        page_rows, total = _molit_rows(raw)
        if len(page_rows) != page["rows"] or total != manifest["row_count"]:
            raise ValueError(f"Raw response count changed: {folder}")
        parsed_rows.extend(page_rows)
    rows = [json.loads(line) for line in (folder / "rows.jsonl").read_text(encoding="utf-8").splitlines()]
    if len(rows) != manifest["row_count"] or rows != parsed_rows:
        raise ValueError(f"Row count changed: {folder}")
    for row in rows:
        if row.get("sggCd") != code or f"{int(row['dealYear']):04d}{int(row['dealMonth']):02d}" != month:
            raise ValueError(f"Response district/month mismatch: {folder}")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/provisional/apartment_20230905/apartment_catalog.csv"))
    parser.add_argument("--code-archive", type=Path, default=Path("data/provisional/legal_district_codes/code_go_kr_full_download.bin"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/provisional/api/molit_2023_catalog"))
    parser.add_argument("--execute", action="store_true", help="Call the API; otherwise only print the plan")
    parser.add_argument("--limit", type=int, help="At most this many new district/month queries")
    args = parser.parse_args()
    scope = plan(args.catalog, args.code_archive)
    print(json.dumps({"apartments": scope["apartment_count"], "districts": scope["district_count"],
                      "queries": scope["district_count"] * 12}, ensure_ascii=False), flush=True)
    if not args.execute:
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = args.output_dir / "plan.json"
    if plan_path.exists():
        if json.loads(plan_path.read_text(encoding="utf-8")) != scope:
            raise ValueError("Existing collection plan differs from current inputs")
    else:
        plan_path.write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    new_queries = 0
    total_rows = 0
    completed = 0
    for code in scope["districts"]:
        for number in range(1, 13):
            month = f"2023{number:02d}"
            folder = args.output_dir / code / month
            if not folder.exists():
                if args.limit is not None and new_queries >= args.limit:
                    print(json.dumps({"new_queries": new_queries, "verified_queries": completed,
                                      "verified_rows": total_rows}), flush=True)
                    return
                for attempt in range(3):
                    try:
                        fetch_molit(lawd_cd=code, deal_ymd=month, output_dir=folder)
                        break
                    except PublicDataError:
                        if folder.exists() or attempt == 2:
                            raise
                        time.sleep(2 ** attempt)
                new_queries += 1
                time.sleep(0.15)
            total_rows += verify_copy(folder, code, month)
            completed += 1
        print(json.dumps({"district": code, "verified_queries": completed,
                          "verified_rows": total_rows}), flush=True)
    print(json.dumps({"complete": True, "verified_queries": completed,
                      "verified_rows": total_rows}), flush=True)


if __name__ == "__main__":
    main()
