"""Role-2 source registry and batch plans (fetch gates of ROLE2-COLLECT-001-REQ-01)."""
from __future__ import annotations

import json
import urllib.parse
from dataclasses import asdict
from importlib import resources
from pathlib import Path

from . import contract as C
from ._reuse import read_json, utc_z, write_json
from .base import RequestSpec

ContractError = C.ContractError


def load_registry(path: Path | None = None) -> dict:
    if path is None:
        text = resources.files(__package__).joinpath("role2_sources.json").read_text(encoding="utf-8")
    else:
        text = Path(path).read_text(encoding="utf-8")
    registry = json.loads(text)
    validate_registry(registry)
    return registry


def _origin(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ContractError("invalid_origin")
    return f"{parts.scheme}://{parts.netloc}".casefold()


def validate_registry(registry: dict) -> None:
    if registry.get("schema_version") != C.REGISTRY_SCHEMA or not registry.get("approval_ref"):
        raise ContractError("unsupported_registry")
    seen_t, seen_s = set(), set()
    for source in registry.get("sources", []):
        t_id, source_id = source.get("t_id"), source.get("source_id")
        if not C.T_ID_RE.fullmatch(t_id or "") or not C.SOURCE_ID_RE.fullmatch(source_id or ""):
            raise ContractError("invalid_source_identity")
        if t_id in seen_t or source_id in seen_s:
            raise ContractError("duplicate_source")
        seen_t.add(t_id)
        seen_s.add(source_id)
        if source.get("status") not in C.SOURCE_STATUSES or source.get("lane") not in C.LANES:
            raise ContractError("invalid_source_status")
        if source.get("record_type") not in (*C.RECORD_TYPES, C.RAW_ONLY):
            raise ContractError("invalid_record_type")
        if (source.get("license") or {}).get("class") not in C.LICENSE_CLASSES:
            raise ContractError("invalid_license_class")
        allow = {_origin(o) for o in source.get("origin_allowlist", [])}
        for request in source.get("requests", []):
            if not C.REQUEST_ID_RE.fullmatch(request.get("request_id", "")):
                raise ContractError("invalid_request_id")
            if _origin(request["url_template"]) not in allow:
                raise ContractError("origin_not_allowlisted")
            if source["lane"] in C.FILE_LANES and "{KEY}" in request["url_template"]:
                raise ContractError("keyed_template_in_file_lane")


def find_source(registry: dict, key: str) -> dict:
    for source in registry["sources"]:
        if key in {source["t_id"], source["source_id"]}:
            return source
    raise ContractError("unknown_source")


def http_acknowledged(registry: dict, origin: str) -> bool:
    ack = registry.get("http_key_exposure_ack") or {}
    return bool(ack.get("ref")) and origin.casefold() in {o.casefold() for o in ack.get("origins", [])}


def check_fetch_gate(registry: dict, plan: dict) -> dict:
    """Refuse before any network call unless the source and batch are approved and recorded."""
    source = find_source(registry, plan.get("source_id", ""))
    if source["status"] != "approved":
        raise ContractError("source_not_approved")
    if not C.RECORD_URL_RE.fullmatch(plan.get("record_url") or ""):
        raise ContractError("github_collection_record_required")
    if not plan.get("approval_ref"):
        raise ContractError("approval_ref_required")
    for request in plan["requests"]:
        origin = _origin(request["url_template"])
        if origin.startswith("http://") and "{KEY}" in request["url_template"] \
                and not http_acknowledged(registry, origin):
            raise ContractError("http_key_not_acknowledged")
    return source


def make_plan(registry: dict, key: str, *, batch_id: str, record_url: str, created_at_utc: str | None = None) -> dict:
    source = find_source(registry, key)
    if source["status"] != "approved":
        raise ContractError("source_not_approved")
    if not C.BATCH_ID_RE.fullmatch(batch_id) or len(batch_id) > C.BATCH_ID_MAX:
        raise ContractError("invalid_batch_id")
    if not C.RECORD_URL_RE.fullmatch(record_url or ""):
        raise ContractError("invalid_record_url")
    requests = []
    for item in source.get("requests", []):
        spec = RequestSpec(request_id=item["request_id"], lane=source["lane"], origin=_origin(item["url_template"]),
                           url_template=item["url_template"], params=tuple(map(tuple, item.get("params", []))),
                           method=item.get("method", "GET"), form=tuple(map(tuple, item.get("form", []))),
                           headers=tuple(map(tuple, item.get("headers", []))),
                           credential_ref=item.get("credential_ref"), quota_bucket=item.get("quota_bucket"),
                           section=item.get("section", ""), expected_rows=item.get("expected_rows"),
                           expected_kind=item.get("expected_kind", "any"))
        requests.append({k: list(map(list, v)) if isinstance(v, tuple) else v for k, v in asdict(spec).items()})
    if not requests:
        raise ContractError("plan_without_requests")
    return {"schema": C.PLAN_SCHEMA, "t_id": source["t_id"], "source_id": source["source_id"],
            "dataset_id": source["dataset_id"], "record_type": source["record_type"], "lane": source["lane"],
            "batch_id": batch_id, "record_url": record_url, "approval_ref": registry["approval_ref"],
            "license": source["license"], "quality_status": C.QUALITY_STATUS, "requests": requests,
            "created_at_utc": created_at_utc or utc_z()}


def write_plan(batch_dir: Path, plan: dict) -> dict:
    """Plans are immutable: an existing plan must match except for its creation time."""
    path = Path(batch_dir) / "plan.json"
    if path.exists():
        existing = read_json(path)
        if {k: v for k, v in existing.items() if k != "created_at_utc"} != \
                {k: v for k, v in plan.items() if k != "created_at_utc"}:
            raise ContractError("existing_plan_differs_use_new_batch")
        return existing
    write_json(path, plan)
    return plan


def load_plan(batch_dir: Path) -> dict:
    plan = read_json(Path(batch_dir) / "plan.json")
    if plan.get("schema") != C.PLAN_SCHEMA or plan.get("quality_status") != C.QUALITY_STATUS:
        raise ContractError("unsupported_plan")
    return plan


def spec_from_plan(item: dict) -> RequestSpec:
    values = dict(item)
    for name in ("params", "form", "headers"):
        values[name] = tuple(tuple(pair) for pair in values.get(name, []))
    return RequestSpec(**values)
