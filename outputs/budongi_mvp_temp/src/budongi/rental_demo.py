"""Explicit fictional snapshot for exercising the rental CLI without API keys."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .rental_storage import connect_rental, import_rental_snapshot, observation_id_for

DEMO_SNAPSHOT_ID = "synthetic_rental_demo_v1"


def create_rental_demo(directory: Path) -> dict:
    directory = Path(directory)
    database = directory / "serving.sqlite3"
    if database.exists():
        raise ValueError("데모 DB가 이미 있습니다. 다른 데모 폴더를 지정해 주세요.")
    directory.mkdir(parents=True, exist_ok=True)
    source = "synthetic_rental_demo"
    payload = [{"complex_id": f"synthetic-{index}", "name": f"합성 단지 {index}",
                "sgg_cd": "11110", "latitude": 37.57 + index * 0.002, "longitude": 126.98,
                "deposit_krw": 100_000_000 + index * 10_000_000, "monthly_rent_krw": 600_000 + index * 50_000,
                "contract_date": "2026-09-15", "rental_type": "wolse", "area_sqm": 59.9}
               for index in range(1, 4)]
    raw = json.dumps({"fictional": True, "complexes": payload}, ensure_ascii=False, sort_keys=True).encode("utf-8")
    file_ref = "synthetic-input.json"
    (directory / file_ref).write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    manifest = {"fictional": True, "datasets": [{"source": source, "source_date": "2026-10-01",
                "retrieved_at_utc": "2026-10-06T00:00:00Z", "files": [{"path": file_ref, "sha256": digest, "rows": 3}]}]}
    observations, complexes, matches = [], [], []
    for index, item in enumerate(payload, 1):
        provenance = {"source": source, "source_file_ref": file_ref, "source_content_sha256": digest, "source_row_number": index}
        observation_id = observation_id_for(**provenance)
        observations.append(provenance | {"observation_id": observation_id, "apartment_name": item["name"],
                            "sgg_cd": item["sgg_cd"], "contract_date": item["contract_date"], "rental_type": item["rental_type"],
                            "deposit_krw": item["deposit_krw"], "monthly_rent_krw": item["monthly_rent_krw"],
                            "area_sqm": item["area_sqm"], "raw_payload": item | {"fictional": True}})
        complexes.append(provenance | {"complex_id": item["complex_id"], "name": item["name"],
                         "sgg_cd": item["sgg_cd"], "latitude": item["latitude"], "longitude": item["longitude"],
                         "identity_evidence": "fictional fixture identity", "raw_payload": {"fictional": True}})
        matches.append({"observation_id": observation_id, "complex_id": item["complex_id"], "review_status": "confirmed",
                        "match_basis": "fictional fixture", "evidence": "synthetic identity only", "reviewed_by": "synthetic fixture",
                        "reviewed_at_utc": "2026-10-06T00:00:00Z"})
    connection = connect_rental(database)
    try:
        import_rental_snapshot(connection, snapshot_id=DEMO_SNAPSHOT_ID, snapshot_date="2026-10-06",
                               source_manifest=manifest, observations=observations, complexes=complexes, matches=matches)
    finally:
        connection.close()
    request = {"rental_type": "wolse", "max_deposit_krw": 130_000_000, "max_monthly_rent_krw": 750_000,
               "districts": ["종로구"], "workplace": {"latitude": 37.57, "longitude": 126.98, "verified": True,
               "source": source, "source_ref": "fictional workplace"},
               "conditions": [{"kind": "workplace", "max_distance_m": 500, "required": True},
                              {"kind": "station", "max_distance_m": 500, "required": False}]}
    request_file = directory / "request.json"
    request_file.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"fictional": True, "snapshot_id": DEMO_SNAPSHOT_ID, "rental_db": str(database), "request_file": str(request_file)}
