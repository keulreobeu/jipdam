"""Build an isolated fictional snapshot for local Tool Calling smoke tests."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from budongi.storage import connect, import_snapshot


SNAPSHOT_ID = "synthetic_toolcall_smoke_v1"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(".local_runtime/synthetic_smoke"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    apartments = args.output_dir / "apartments.csv"
    transactions = args.output_dir / "transactions.csv"
    database = args.output_dir / "serving.sqlite3"
    if database.exists():
        raise FileExistsError(f"Fixture database already exists: {database}")
    write_csv(apartments,
              ["apartment_id", "name", "address", "built_year", "source", "source_id", "valid_date"],
              [
                  {"apartment_id": "APT_A", "name": "가상마곡A", "address": "서울특별시 강서구 마곡동 1",
                   "built_year": "2010", "source": "synthetic_smoke", "source_id": "A", "valid_date": "2023-12-31"},
                  {"apartment_id": "APT_B", "name": "가상마곡B", "address": "서울특별시 강서구 마곡동 2",
                   "built_year": "2015", "source": "synthetic_smoke", "source_id": "B", "valid_date": "2023-12-31"},
              ])
    write_csv(transactions,
              ["transaction_id", "apartment_id", "contract_date", "price_krw", "area_sqm",
               "status", "source", "source_id", "valid_date"],
              [
                  {"transaction_id": "T_A1", "apartment_id": "APT_A", "contract_date": "2023-01-10",
                   "price_krw": "800000000", "area_sqm": "84", "status": "valid",
                   "source": "synthetic_smoke", "source_id": "A1", "valid_date": "2023-01-15"},
                  {"transaction_id": "T_A2", "apartment_id": "APT_A", "contract_date": "2023-11-01",
                   "price_krw": "900000000", "area_sqm": "84", "status": "valid",
                   "source": "synthetic_smoke", "source_id": "A2", "valid_date": "2023-11-10"},
                  {"transaction_id": "T_B1", "apartment_id": "APT_B", "contract_date": "2023-10-01",
                   "price_krw": "700000000", "area_sqm": "84", "status": "valid",
                   "source": "synthetic_smoke", "source_id": "B1", "valid_date": "2023-10-10"},
              ])
    connection = connect(database)
    try:
        imported = import_snapshot(connection, snapshot_id=SNAPSHOT_ID,
                                   snapshot_date="2023-12-31", apartments_csv=apartments,
                                   transactions_csv=transactions)
    finally:
        connection.close()
    (args.output_dir / "README.txt").write_text(
        "All apartments, transactions, prices and names here are fictional. "
        "This fixture measures code and model behavior only.\n", encoding="utf-8"
    )
    print(json.dumps({"snapshot_id": SNAPSHOT_ID, "database": str(database),
                      "fictional": True, **imported}))


if __name__ == "__main__":
    main()
