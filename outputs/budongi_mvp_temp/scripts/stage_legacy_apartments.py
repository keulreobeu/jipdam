"""Stage an unverified legacy apartment CSV for development-only inspection.

This intentionally does not create a historical snapshot or transactions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from budongi.legacy import parse_address, read_legacy_csv


CATALOG_FIELDS = (
    "provisional_apartment_id", "name", "address", "province", "district",
    "neighborhood", "lat", "lon", "station_name", "station_distance_m",
    "planned_move_in_year", "source_row_count",
)
GROUP_FIELDS = ("위도", "경도", "지하철역", "지하철역_거리", "입주예정연도")


def stage(source: Path, output_dir: Path) -> dict[str, object]:
    rows, encoding = read_legacy_csv(source)
    if not rows:
        raise ValueError("The source CSV is empty")
    required = ("아파트명", "법정동주소") + GROUP_FIELDS
    missing_columns = [field for field in required if field not in rows[0]]
    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for number, row in enumerate(rows, start=2):
        name, address = row["아파트명"].strip(), row["법정동주소"].strip()
        if not name or not address:
            raise ValueError(f"Row {number} lacks apartment name or address")
        groups[(name, address)].append(row)

    catalog: list[dict[str, object]] = []
    for (name, address), members in sorted(groups.items()):
        for field in GROUP_FIELDS:
            if len({member[field].strip() for member in members}) != 1:
                raise ValueError(f"Conflicting {field} for {name} at {address}")
        first = members[0]
        location = parse_address(address)
        source_distance = first["지하철역_거리"].strip()
        distance_m = round(float(source_distance) * 1000, 1) if source_distance else ""
        key = hashlib.sha256(f"{name}\0{address}".encode("utf-8")).hexdigest()[:16]
        catalog.append({
            "provisional_apartment_id": f"PROV_{key}",
            "name": name, "address": address, **location,
            "lat": first["위도"].strip(), "lon": first["경도"].strip(),
            "station_name": first["지하철역"].strip(),
            "station_distance_m": distance_m,
            "planned_move_in_year": first["입주예정연도"].strip(),
            "source_row_count": len(members),
        })

    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    report: dict[str, object] = {
        "status": "provisional_unverified",
        "input_filename": source.name,
        "input_sha256": digest,
        "detected_encoding": encoding,
        "source_columns": len(rows[0]),
        "source_rows": len(rows),
        "exact_duplicate_rows": len(rows) - len({tuple(row.items()) for row in rows}),
        "provisional_apartments": len(catalog),
        "planned_move_in_year_counts": dict(sorted(Counter(row["입주예정연도"] for row in rows).items())),
        "missing_values_by_column": {
            field: sum(not row[field].strip() for row in rows) for field in rows[0]
        },
        "source_date_verified": False,
        "transaction_rows": 0,
        "limitations": [
            "The filename date is not a verified observation or valid date.",
            "Supply price is not a transaction price.",
            "Planned move-in year is not a built year.",
            "Provisional IDs are derived from name and address, not source IDs.",
            "This catalog must not be used as a real evaluation snapshot.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_copy = output_dir / "source.csv"
    if raw_copy.exists() and hashlib.sha256(raw_copy.read_bytes()).hexdigest() != digest:
        raise ValueError(f"A different source already exists at {raw_copy}")
    shutil.copyfile(source, raw_copy)
    with (output_dir / "apartment_catalog.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CATALOG_FIELDS)
        writer.writeheader()
        writer.writerows(catalog)
    (output_dir / "profile.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data/provisional/apartment_20230905"))
    args = parser.parse_args()
    print(json.dumps(stage(args.source, args.output_dir), ensure_ascii=False, indent=2))
