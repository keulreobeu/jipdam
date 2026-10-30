"""Builds and checks the manifest.json document of a team_collection_v1 package."""
from __future__ import annotations

import copy
import re

from budongi.team_collection import contract as C

MANIFEST_KEYS = (
    "delivery_schema_version", "kind", "record_type", "source_id", "dataset_id", "provider",
    "source", "documentation_url", "dataset", "batch_id", "mapping_version", "owner",
    "record_url", "approval_ref", "collection_method", "scope", "request",
    "source_retrieved_at_utc", "provided_at_utc", "staged_at_utc", "snapshot_date",
    "quality_status", "requests", "collection_status", "counts", "files", "license_raw",
    "license_ref", "license_review_status", "normalized_withheld", "metadata_dataset_id",
)
COUNT_KEYS = ("expected_rows", "raw_rows", "accepted", "excluded", "rejected")

_PLAN_KEYS = ("source_id", "dataset_id", "record_type", "batch_id", "record_url",
              "approval_ref", "t_id")
_DATASET_KEYS = ("name", "provider", "source", "mapping_version", "collection_method",
                 "scope", "request")
_SECRET_RE = re.compile(r"servicekey=|:8088/[^/\s]{20,}/(?:json|xml)", re.IGNORECASE)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _utc_ok(value: object) -> bool:
    return isinstance(value, str) and C.UTC_Z_RE.match(value) is not None


def build_manifest(plan: dict, *, requests: list, files: list, counts: dict, owner: str,
                   dataset: dict, license: dict, staged_at_utc: str,
                   container: dict | None = None, normalized_withheld: bool = False) -> dict:
    """Build the manifest dict of a package or raise ContractError."""
    for key in _PLAN_KEYS:
        if key not in plan:
            raise C.ContractError("plan_missing:" + key)
    if not isinstance(plan["source_id"], str) or not C.SOURCE_ID_RE.match(plan["source_id"]):
        raise C.ContractError("invalid_source_id")
    batch_id = plan["batch_id"]
    if (not isinstance(batch_id, str) or not C.BATCH_ID_RE.match(batch_id)
            or len(batch_id) > C.BATCH_ID_MAX):
        raise C.ContractError("invalid_batch_id")
    record_type = plan["record_type"]
    if not isinstance(record_type, str) or (
            record_type not in C.RECORD_TYPES and record_type != C.RAW_ONLY):
        raise C.ContractError("invalid_record_type")

    for key in _DATASET_KEYS:
        if key not in dataset:
            raise C.ContractError("dataset_missing:" + key)
    for field in ("source_retrieved_at_utc", "provided_at_utc"):
        val = dataset.get(field)
        if val is not None and not _utc_ok(val):
            raise C.ContractError("invalid_utc:" + field)
    if not _utc_ok(staged_at_utc):
        raise C.ContractError("invalid_staged_at_utc")

    license_raw = license.get("raw")
    license_ref = license.get("ref")
    if license_raw in (None, "") and license_ref in (None, ""):
        raise C.ContractError("license_missing")

    if not isinstance(owner, str) or not owner.strip():
        raise C.ContractError("invalid_owner")
    if not isinstance(normalized_withheld, bool):
        raise C.ContractError("invalid_normalized_withheld")

    if not requests:
        raise C.ContractError("no_requests")
    statuses = []
    for item in requests:
        if not isinstance(item, dict):
            raise C.ContractError("invalid_request")
        status = item.get("collection_status")
        if not isinstance(status, str) or status not in C.REQUEST_STATUSES:
            raise C.ContractError("invalid_request_status")
        statuses.append(status)
    if all(s in C.BATCH_COMPLETE for s in statuses):
        collection_status = "complete"
    elif "inconsistent" in statuses:
        collection_status = "inconsistent"
    else:
        collection_status = "partial"

    seen = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise C.ContractError("invalid_file_entry")
        path = entry.get("path")
        size = entry.get("bytes")
        digest = entry.get("sha256")
        if (not isinstance(path, str) or not path or not _is_int(size) or size < 0
                or not isinstance(digest, str) or not C.SHA256_RE.match(digest)):
            raise C.ContractError("invalid_file_entry")
        if path in seen:
            raise C.ContractError("duplicate_file_path")
        seen.add(path)

    new_counts = {}
    for key in COUNT_KEYS:
        if key not in counts:
            raise C.ContractError("missing_count:" + key)
    for key in COUNT_KEYS:
        val = counts[key]
        if key == "expected_rows" and val is None:
            pass
        elif not _is_int(val) or val < 0:
            raise C.ContractError("invalid_count:" + key)
        new_counts[key] = val

    if container is not None and not isinstance(container, dict):
        raise C.ContractError("invalid_container")

    kind = dataset.get("kind")
    manifest = {
        "delivery_schema_version": C.DELIVERY_SCHEMA_VERSION,
        "kind": kind if kind is not None else record_type,
        "record_type": record_type,
        "source_id": plan["source_id"],
        "dataset_id": plan["dataset_id"],
        "provider": dataset["provider"],
        "source": dataset["source"],
        "documentation_url": dataset.get("documentation_url"),
        "dataset": dataset["name"],
        "batch_id": batch_id,
        "mapping_version": dataset["mapping_version"],
        "owner": owner,
        "record_url": plan["record_url"],
        "approval_ref": plan["approval_ref"],
        "collection_method": dataset["collection_method"],
        "scope": dataset["scope"],
        "request": dataset["request"],
        "source_retrieved_at_utc": dataset.get("source_retrieved_at_utc"),
        "provided_at_utc": dataset.get("provided_at_utc"),
        "staged_at_utc": staged_at_utc,
        "snapshot_date": dataset.get("snapshot_date"),
        "quality_status": C.QUALITY_STATUS,
        "requests": requests,
        "collection_status": collection_status,
        "counts": new_counts,
        "files": files,
        "license_raw": license_raw,
        "license_ref": license_ref,
        "license_review_status": "pending",
        "normalized_withheld": normalized_withheld,
        "metadata_dataset_id": plan["t_id"],
    }
    manifest = copy.deepcopy(manifest)
    if container is not None:
        manifest["container"] = copy.deepcopy(container)
    return manifest


def missing_keys(manifest: dict) -> list[str]:
    """List required manifest keys and counts.<k> entries absent from manifest."""
    if not isinstance(manifest, dict):
        raise C.ContractError("invalid_manifest")
    out = [key for key in MANIFEST_KEYS if key not in manifest]
    if "counts" in manifest:
        counts = manifest["counts"]
        for key in COUNT_KEYS:
            if not isinstance(counts, dict) or key not in counts:
                out.append("counts." + key)
    return out


def secret_shapes(obj: object) -> list[str]:
    """Return JSON paths of string values that look like they carry an API key."""
    found: list[str] = []

    def walk(value: object, path: str) -> None:
        if isinstance(value, str):
            if _SECRET_RE.search(value) and path not in found:
                found.append(path)
        elif isinstance(value, dict):
            for k, v in value.items():
                walk(v, path + "." + str(k))
        elif isinstance(value, (list, tuple)):
            for i, v in enumerate(value):
                walk(v, path + "[" + str(i) + "]")

    walk(obj, "$")
    return found
