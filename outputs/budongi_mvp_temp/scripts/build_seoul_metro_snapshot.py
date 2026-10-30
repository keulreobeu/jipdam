"""Create an offline, unverified station snapshot from a user-approved CSV."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil

HEADERS = ["연번", "호선", "고유역번호(외부역코드)", "역명", "위도", "경도", "작성일자", "작성기준일"]
BATCH = "seoul-metro-station-coordinates-20250814-20261028-v1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(source: Path, download: Path, out: Path) -> None:
    if out.exists():
        raise SystemExit("Refusing to overwrite an existing output directory")
    raw = source.read_bytes()
    metadata = json.loads(download.read_text(encoding="utf-8"))
    if metadata["sha256"] != digest(raw) or metadata["bytes"] != len(raw):
        raise ValueError("Source bytes differ from download record")
    text = raw.decode("cp949")
    rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    if not rows or rows[0] != HEADERS or len(text.splitlines()) != len(rows) or any(len(row) != len(HEADERS) for row in rows[1:]):
        raise ValueError("Unexpected source columns or row width")
    out.mkdir(parents=True)
    (out / "raw").mkdir()
    (out / "normalized").mkdir()
    shutil.copyfile(source, out / "raw" / "seoul-metro-1-8-stations.csv")
    shutil.copyfile(Path(__file__), out / "build_seoul_metro_snapshot.py")
    records = []
    for index, values in enumerate(rows[1:], start=2):
        records.append({"source_id": "seoul_metro_station_coordinates_15099316", "batch_id": BATCH,
                        "source_sha256": metadata["sha256"], "source_row_number": index,
                        "source_values": dict(zip(HEADERS, values)), "quality_status": "source_unverified",
                        "coordinate_review_status": "pending", "latitude": None, "longitude": None,
                        "complex_id": None, "station_link_status": "not_linked"})
    with (out / "normalized" / "stations.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    write_json(out / "schema.json", {"record_type": "station_source_row", "encoding": "CP949",
               "source_columns": HEADERS, "source_row_number": "CSV physical line, header is line 1",
               "coordinate_policy": "Original strings preserved; verified coordinates remain null",
               "source_crs": "unknown", "identity_policy": "Source station code only; no internal links"})
    write_json(out / "validation.json", {"rows": len(records), "source_rows": len(rows) - 1,
               "source_width": len(HEADERS), "parse_errors": 0, "quality_status": "source_unverified",
               "coordinate_review_status": "pending", "source_crs": "unknown", "coverage": "unknown",
               "license": "Portal displays unrestricted use; dataset-specific review pending",
               "limitations": ["No station or complex matching", "No field survey or coordinate verification",
                               "No claim of complete rail network or station entrances"]})
    files = []
    for path in sorted(out.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            files.append({"path": path.relative_to(out).as_posix(), "bytes": len(data), "sha256": digest(data)})
    write_json(out / "manifest.json", {"batch_id": BATCH, "source": metadata, "files": files})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--download", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.source, args.download, args.output)


if __name__ == "__main__":
    main()
