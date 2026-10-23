"""Build an isolated, provenance-preserving SQLite DB from approved team ZIPs.

This intentionally does not publish rows to the transactional rental canonical
database: the imported source facts are still marked source_unverified.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import os
import sqlite3
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


PACKAGES = {
    "hug.zip": ("hug_jeonse_guarantee_accident_regional", "hug-accident-regional-202608-20261014-v1", "regional_statistic", 828, 828,
                "9ebf178baba3612e492128a732c38e54fcb6e2d2fb07202ef4e16fbfa3c0dcda", 9),
    "academy.zip": ("neis_academy_info", "neis-academy-national-20261014-v1", "facility", 138524, 138523,
                    "8da8dd9a1445138ed3929d1b5abedbfe1de6143b8583663f73d348ab4e4f2eda", 13),
    "library.zip": ("std_library_national", "std-library-national-20261014-v1", "facility", 3597, 3597,
                    "1e15a13cbcc153a6332cbc3288ff18ebcfdaf4262951551afedd9f8f66a46dbb", 14),
    "child_zone.zip": ("std_child_protection_zone_national", "std-child-protection-zone-national-20261014-v1", "facility", 14654, 14654,
                       "38651cf6384358b3ea4ebf1b4e2b94fd18defa084efb879de5b4ad7094985a63", 15),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_package(root: Path, zip_name: str, spec: tuple) -> tuple[dict, Path]:
    source_id, batch_id, record_type, expected_rows, accepted_rows, expected_zip_sha, issue = spec
    archive = root / zip_name
    if sha256(archive) != expected_zip_sha:
        raise ValueError(f"zip_hash_mismatch:{zip_name}")
    with zipfile.ZipFile(archive) as zf:
        if zf.testzip() is not None:
            raise ValueError(f"zip_crc_error:{zip_name}")
    manifests = list((root / Path(zip_name).stem).rglob("manifest.json"))
    if len(manifests) != 1:
        raise ValueError(f"manifest_count_mismatch:{zip_name}")
    manifest_path = manifests[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("source_id"), manifest.get("batch_id"), manifest.get("record_type")) != (source_id, batch_id, record_type):
        raise ValueError(f"manifest_identity_mismatch:{zip_name}")
    if manifest.get("quality_status") != "source_unverified":
        raise ValueError(f"unexpected_quality_status:{zip_name}")
    package_root = manifest_path.parent
    for entry in manifest.get("files", []):
        rel = PurePosixPath(entry["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"unsafe_manifest_path:{zip_name}")
        path = package_root.joinpath(*rel.parts)
        if not path.is_file() or path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            raise ValueError(f"manifest_file_integrity_mismatch:{zip_name}:{entry['path']}")
    normalized = [entry for entry in manifest["files"] if entry.get("path", "").startswith("normalized/") and entry.get("format") == "jsonl"]
    if len(normalized) != 1 or normalized[0].get("rows") != expected_rows:
        raise ValueError(f"normalized_row_count_mismatch:{zip_name}")
    if manifest.get("counts", {}).get("accepted") != accepted_rows:
        raise ValueError(f"accepted_row_count_mismatch:{zip_name}")
    return manifest, package_root / Path(*PurePosixPath(normalized[0]["path"]).parts)


def build(root: Path, database: Path) -> dict:
    if database.exists():
        raise FileExistsError(f"refusing_to_replace_existing_database:{database}")
    database.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=database.name + ".", suffix=".tmp", dir=database.parent)
    os.close(fd)
    temp = Path(temp_name)
    counts = {}
    try:
        with closing(sqlite3.connect(temp)) as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.executescript("""
                PRAGMA application_id=1248093265;
                PRAGMA user_version=1;
                CREATE TABLE imports(
                    source_id TEXT NOT NULL, batch_id TEXT NOT NULL, record_type TEXT NOT NULL,
                    dataset_id TEXT NOT NULL, issue_number INTEGER NOT NULL, drive_file_name TEXT NOT NULL,
                    drive_zip_sha256 TEXT NOT NULL, quality_status TEXT NOT NULL,
                    manifest_json TEXT NOT NULL, PRIMARY KEY(source_id,batch_id));
                CREATE TABLE records(
                    source_id TEXT NOT NULL, batch_id TEXT NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal>0),
                    record_type TEXT NOT NULL, validation_status TEXT NOT NULL CHECK(validation_status IN ('accepted','rejected')),
                    source_quality TEXT NOT NULL, payload_json TEXT NOT NULL,
                    PRIMARY KEY(source_id,batch_id,ordinal),
                    FOREIGN KEY(source_id,batch_id) REFERENCES imports(source_id,batch_id));
                CREATE INDEX records_by_type ON records(record_type,source_id,batch_id);
            """)
            for zip_name, spec in PACKAGES.items():
                manifest, data_path = verify_package(root, zip_name, spec)
                source_id, batch_id, record_type, expected_rows, accepted_rows, expected_zip_sha, issue = spec
                db.execute("INSERT INTO imports VALUES (?,?,?,?,?,?,?,?,?)", (
                    source_id, batch_id, record_type, str(manifest["dataset_id"]), issue, zip_name,
                    expected_zip_sha, manifest["quality_status"], json.dumps(manifest, ensure_ascii=False, sort_keys=True)))
                count = accepted = rejected = 0
                with data_path.open("r", encoding="utf-8") as stream:
                    for ordinal, line in enumerate(stream, 1):
                        payload = json.loads(line)
                        if payload.get("source_id") != source_id or payload.get("batch_id") != batch_id:
                            raise ValueError(f"record_lineage_mismatch:{zip_name}:{ordinal}")
                        status = payload.get("validation_status", "accepted")
                        if status not in {"accepted", "rejected"}:
                            raise ValueError(f"unknown_validation_status:{zip_name}:{ordinal}")
                        db.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?)", (
                            source_id, batch_id, ordinal, record_type, status, manifest["quality_status"],
                            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))))
                        count += 1
                        accepted += status == "accepted"
                        rejected += status == "rejected"
                if count != expected_rows or accepted != accepted_rows:
                    raise ValueError(f"actual_normalized_rows_mismatch:{zip_name}:{count}")
                if rejected != manifest.get("counts", {}).get("rejected", 0):
                    raise ValueError(f"rejected_row_count_mismatch:{zip_name}:{rejected}")
                counts[source_id] = {"accepted": accepted, "rejected": rejected}
            db.commit()
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("sqlite_integrity_check_failed")
            if db.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("sqlite_foreign_key_check_failed")
        os.replace(temp, database)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    return {"database": str(database), "counts": counts,
            "total_accepted": sum(row["accepted"] for row in counts.values()),
            "total_rejected": sum(row["rejected"] for row in counts.values()), "integrity": "ok"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(args.package_root, args.database)
    except (OSError, ValueError, KeyError, sqlite3.Error, zipfile.BadZipFile) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
