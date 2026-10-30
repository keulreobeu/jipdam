"""Build and check the manifest.json document of a team_collection_v1 package."""
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
_SECRET_URL_RE = re.compile(r":8088/[^/\s]{20,}/(?:json|xml)", re.IGNORECASE)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _matches(pattern: re.Pattern, value: object) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _empty(value: object) -> bool:
    return value is None or value == ""


def build_manifest(plan: dict, *, requests: list, files: list, counts: dict, owner: str,
                   dataset: dict, license: dict, staged_at_utc: str,
                   container: dict | None = None, normalized_withheld: bool = False) -> dict:
    """Return a new team_collection_v1 manifest dict or raise ContractError."""
    if not isinstance(plan, dict):
        raise C.ContractError("plan_missing:" + _PLAN_KEYS[0])
    for key in _PLAN_KEYS:
        if key not in plan:
            raise C.ContractError("plan_missing:" + key)
    if not _matches(C.SOURCE_ID_RE, plan["source_id"]):
        raise C.ContractError("invalid_source_id")
    batch_id = plan["batch_id"]
    if not _matches(C.BATCH_ID_RE, batch_id) or len(batch_id) > C.BATCH_ID_MAX:
        raise C.ContractError("invalid_batch_id")
    if not isinstance(plan["record_type"], str) or plan["record_type"] not in C.RECORD_TYPES:
        raise C.ContractError("invalid_record_type")

    if not isinstance(dataset, dict):
        raise C.ContractError("dataset_missing:" + _DATASET_KEYS[0])
    for key in _DATASET_KEYS:
        if key not in dataset:
            raise C.ContractError("dataset_missing:" + key)

    if not isinstance(license, dict):
        raise C.ContractError("license_missing")
    license_raw = license.get("raw")
    license_ref = license.get("ref")
    if _empty(license_raw) and _empty(license_ref):
        raise C.ContractError("license_missing")

    if not isinstance(owner, str) or not owner.strip():
        raise C.ContractError("invalid_owner")
    if not _matches(C.UTC_Z_RE, staged_at_utc):
        raise C.ContractError("invalid_staged_at_utc")
    for field in ("source_retrieved_at_utc", "provided_at_utc"):
        value = dataset.get(field)
        if value is not None and not _matches(C.UTC_Z_RE, value):
            raise C.ContractError("invalid_utc:" + field)
    if not isinstance(normalized_withheld, bool):
        raise C.ContractError("invalid_normalized_withheld")

    if not isinstance(requests, (list, tuple)):
        raise C.ContractError("invalid_request")
    if len(requests) == 0:
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
    elif any(s == "inconsistent" for s in statuses):
        collection_status = "inconsistent"
    else:
        collection_status = "partial"

    if not isinstance(files, (list, tuple)):
        raise C.ContractError("invalid_file_entry")
    seen = set()
    for entry in files:
        if (not isinstance(entry, dict)
                or not isinstance(entry.get("path"), str) or not entry["path"]
                or not _is_int(entry.get("bytes")) or entry["bytes"] < 0
                or not _matches(C.SHA256_RE, entry.get("sha256"))):
            raise C.ContractError("invalid_file_entry")
        if entry["path"] in seen:
            raise C.ContractError("duplicate_file_path")
        seen.add(entry["path"])

    if not isinstance(counts, dict):
        raise C.ContractError("missing_count:" + COUNT_KEYS[0])
    for key in COUNT_KEYS:
        if key not in counts:
            raise C.ContractError("missing_count:" + key)
    for key in COUNT_KEYS:
        value = counts[key]
        if key == "expected_rows" and value is None:
            continue
        if not _is_int(value) or value < 0:
            raise C.ContractError("invalid_count:" + key)

    if container is not None and not isinstance(container, dict):
        raise C.ContractError("invalid_container")

    kind = dataset.get("kind")
    if kind is None:
        kind = plan["record_type"]
    values = {
        "delivery_schema_version": C.DELIVERY_SCHEMA_VERSION,
        "kind": kind,
        "record_type": plan["record_type"],
        "source_id": plan["source_id"],
        "dataset_id": plan["dataset_id"],
        "provider": dataset["provider"],
        "source": dataset["source"],
        "documentation_url": dataset.get("documentation_url"),
        "dataset": dataset["name"],
        "batch_id": plan["batch_id"],
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
        "requests": list(requests),
        "collection_status": collection_status,
        "counts": {key: counts[key] for key in COUNT_KEYS},
        "files": list(files),
        "license_raw": license_raw,
        "license_ref": license_ref,
        "license_review_status": "pending",
        "normalized_withheld": normalized_withheld,
        "metadata_dataset_id": plan["t_id"],
    }
    manifest = {key: copy.deepcopy(values[key]) for key in MANIFEST_KEYS}
    if container is not None:
        manifest["container"] = copy.deepcopy(container)
    return manifest


def missing_keys(manifest: dict) -> list[str]:
    """Return the required manifest keys and counts.<k> entries absent from manifest."""
    if not isinstance(manifest, dict):
        raise C.ContractError("invalid_manifest")
    result = [key for key in MANIFEST_KEYS if key not in manifest]
    if "counts" in manifest:
        counts = manifest["counts"]
        for key in COUNT_KEYS:
            if not isinstance(counts, dict) or key not in counts:
                result.append("counts." + key)
    return result


def _flagged(text: str) -> bool:
    if "servicekey=" in text.lower():
        return True
    return _SECRET_URL_RE.search(text) is not None


def _walk(obj: object, path: str, found: list[str]) -> None:
    if isinstance(obj, str):
        if _flagged(obj):
            found.append(path)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            _walk(value, path + "." + str(key), found)
    elif isinstance(obj, (list, tuple)):
        for index, value in enumerate(obj):
            _walk(value, path + "[" + str(index) + "]", found)


def secret_shapes(obj: object) -> list[str]:
    """Return the JSON paths of every string value that looks like it carries an API key."""
    found: list[str] = []
    _walk(obj, "$", found)
    return found
