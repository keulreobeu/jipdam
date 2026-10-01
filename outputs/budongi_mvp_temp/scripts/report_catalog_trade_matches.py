"""Create review candidates between provisional apartments and 2023 trade copies."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from budongi.district_codes import (
    SUCCESSOR_QUERY_CODES, district_for_address, official_districts,
    query_codes_for_catalog_code,
)
from scripts.fetch_catalog_trades_2023 import plan, verify_copy


def _normalized(value: str | None) -> str:
    return "".join(character.casefold() for character in (value or "") if character.isalnum())


def _address_parts(address: str, official_name: str) -> tuple[str | None, str | None]:
    parts = address.split()
    district_tokens = len(official_name.split())
    # The catalog has a few explicit shortened province/district names.
    offset = district_tokens - (1 if len(parts) > 1 and parts[1] in {
        "고양덕양구", "성남수정구", "용인처인구"
    } else 0)
    remainder = parts[offset:]
    if not remainder:
        return None, None
    first = re.fullmatch(r"(.+?(?:동|읍|면))(산?\d+(?:-\d+)?)?", remainder[0])
    if not first:
        return None, None
    neighborhood = first.group(1)
    lot = first.group(2)
    if neighborhood.endswith(("읍", "면")) and len(remainder) > 1:
        ri = re.fullmatch(r"(.+?리)(산?\d+(?:-\d+)?)?", remainder[1])
        if ri:
            neighborhood += " " + ri.group(1)
            lot = lot or ri.group(2)
            remainder = remainder[1:]
    for token in remainder[1:3]:
        found = re.fullmatch(r"(산?\d+(?:-\d+)?)(?:번지)?", token)
        if found:
            lot = found.group(1)
            break
    return neighborhood, lot


def report(catalog_path: Path, code_archive: Path, copies_dir: Path,
           successor_dir: Path) -> dict[str, object]:
    scope = plan(catalog_path, code_archive)
    expected_scope = json.loads((copies_dir / "plan.json").read_text(encoding="utf-8"))
    if scope != expected_scope:
        raise ValueError("Collection plan differs from catalog/code inputs")
    districts, _ = official_districts(code_archive)
    trades: dict[str, list[dict[str, str | None]]] = defaultdict(list)
    source_rows = 0
    for code in scope["districts"]:
        for number in range(1, 13):
            month = f"2023{number:02d}"
            folder = copies_dir / code / month
            source_rows += verify_copy(folder, code, month)
            with (folder / "rows.jsonl").open(encoding="utf-8") as stream:
                trades[code].extend(json.loads(line) for line in stream)
    supplementary_codes = sorted({successor for code, successors in SUCCESSOR_QUERY_CODES.items()
                                  if code != "41110" for successor in successors})
    supplement_scope = json.loads((successor_dir / "plan.json").read_text(encoding="utf-8"))
    if supplement_scope["query_codes"] != supplementary_codes:
        raise ValueError("Unexpected successor collection scope")
    for code in supplementary_codes:
        for number in range(1, 13):
            month = f"2023{number:02d}"
            folder = successor_dir / code / month
            source_rows += verify_copy(folder, code, month)
            with (folder / "rows.jsonl").open(encoding="utf-8") as stream:
                trades[code].extend(json.loads(line) for line in stream)
    output = []
    catalog = csv.DictReader(catalog_path.open(encoding="utf-8-sig", newline=""))
    for apartment in catalog:
        code, official_name = district_for_address(apartment["address"], districts)
        neighborhood, lot = _address_parts(apartment["address"], official_name)
        candidates = []
        for query_code in query_codes_for_catalog_code(code):
            for trade in trades[query_code]:
                name_match = _normalized(apartment["name"]) == _normalized(trade.get("aptNm"))
                neighborhood_match = neighborhood and _normalized(neighborhood) == _normalized(trade.get("umdNm"))
                lot_match = lot and neighborhood_match and lot == (trade.get("jibun") or "").strip()
                if name_match and neighborhood_match and lot_match:
                    evidence = "name_neighborhood_lot"
                elif name_match and neighborhood_match:
                    evidence = "name_neighborhood"
                elif name_match:
                    evidence = "name_only"
                elif lot_match:
                    evidence = "neighborhood_lot_only"
                else:
                    continue
                candidates.append((evidence, trade))
        priority = ("name_neighborhood_lot", "name_neighborhood", "neighborhood_lot_only", "name_only")
        best = next((level for level in priority if any(e == level for e, _ in candidates)), None)
        selected = [trade for evidence, trade in candidates if evidence == best]
        apt_sequences = sorted({str(row.get("aptSeq") or "") for row in selected if row.get("aptSeq")})
        output.append({
            "provisional_apartment_id": apartment["provisional_apartment_id"],
            "name": apartment["name"], "address": apartment["address"],
            "catalog_lawd_cd": code, "query_lawd_cds": query_codes_for_catalog_code(code),
            "evidence": best or "none",
            "candidate_apt_seq": apt_sequences,
            "candidate_trade_names": sorted({str(row.get("aptNm") or "") for row in selected}),
            "candidate_trade_neighborhoods": sorted({str(row.get("umdNm") or "") for row in selected}),
            "candidate_trade_lots": sorted({str(row.get("jibun") or "") for row in selected}),
            "candidate_trade_rows": len(selected),
            "requires_manual_review": bool(selected),
        })
    counts = Counter(item["evidence"] for item in output)
    return {
        "status": "candidate_matches_not_identity_verified",
        "catalog_apartments": len(output), "trade_rows": source_rows,
        "candidate_counts": dict(sorted(counts.items())), "rows": output,
        "limitations": [
            "Matching uses names, legal neighborhoods, and parcel text when available.",
            "Same parcel can contain a predecessor apartment and is not proof of identity.",
            "Trade responses were retrieved later than 2023 and can contain later corrections.",
            "No candidate has been loaded into the historical serving database.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/provisional/apartment_20230905/apartment_catalog.csv"))
    parser.add_argument("--code-archive", type=Path, default=Path("data/provisional/legal_district_codes/code_go_kr_full_download.bin"))
    parser.add_argument("--copies-dir", type=Path, default=Path("data/provisional/api/molit_2023_catalog"))
    parser.add_argument("--successor-dir", type=Path, default=Path("data/provisional/api/molit_2023_successors"))
    parser.add_argument("--output", type=Path, default=Path("data/provisional/matching_2023/report.json"))
    args = parser.parse_args()
    result = report(args.catalog, args.code_archive, args.copies_dir, args.successor_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review_path = args.output.with_name("candidates.csv")
    with review_path.open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["provisional_apartment_id", "name", "address", "evidence", "catalog_lawd_cd",
                  "query_lawd_cds", "candidate_apt_seq", "candidate_trade_names",
                  "candidate_trade_neighborhoods", "candidate_trade_lots", "candidate_trade_rows",
                  "manual_decision", "review_notes"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        priority = {"name_neighborhood_lot": 0, "name_neighborhood": 1,
                    "neighborhood_lot_only": 2, "name_only": 3}
        for item in sorted((row for row in result["rows"] if row["requires_manual_review"]),
                           key=lambda row: (priority[row["evidence"]], row["name"])):
            writer.writerow({key: " | ".join(item[key]) if isinstance(item.get(key), (list, tuple))
                             else item.get(key, "") for key in fields})
    print(json.dumps({key: result[key] for key in ("catalog_apartments", "trade_rows", "candidate_counts")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
