"""Merge per-unit outsource fragments into plan.json (drafted by agy gemini-3.8-flash, reviewed by the Opus lead)."""
from __future__ import annotations

import heapq
import json
from pathlib import Path
import sys
from typing import Any


def _get_list(data: dict[str, Any], key: str) -> list[str]:
    val = data.get(key)
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return list(val)


def _normalize_path(p: str) -> str:
    return p.replace("\\", "/")


def merge(plan_dir: Path) -> dict[str, Any]:
    plan_dir = Path(plan_dir)

    base_path = plan_dir / "plan.base.json"
    if not base_path.is_file():
        raise FileNotFoundError(f"Missing base plan file: {base_path}")

    base_data = json.loads(base_path.read_text(encoding="utf-8"))
    if not isinstance(base_data, dict):
        raise ValueError("plan.base.json must be a JSON object")
    if "units" in base_data:
        raise ValueError("base_has_units")

    units_dir = plan_dir / "units"
    if not units_dir.is_dir():
        raise ValueError("no_units")

    unit_files = sorted(
        [p for p in units_dir.iterdir() if p.is_file() and p.name.endswith(".json")],
        key=lambda p: p.name,
    )
    if not unit_files:
        raise ValueError("no_units")

    units: list[dict[str, Any]] = []
    for f in unit_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Unit file {f.name} must be a JSON object")
        units.append(data)

    # Validate duplicate unit IDs
    seen_unit_ids: set[str] = set()
    for unit in units:
        uid = unit.get("id")
        if uid in seen_unit_ids:
            raise ValueError("duplicate_unit_id")
        if uid is not None:
            seen_unit_ids.add(uid)

    # Validate duplicate deliverables
    seen_deliverables: set[str] = set()
    for unit in units:
        unit_seen: set[str] = set()
        for deliverable in _get_list(unit, "deliverables"):
            if deliverable in seen_deliverables or deliverable in unit_seen:
                raise ValueError("duplicate_deliverable")
            unit_seen.add(deliverable)
        seen_deliverables.update(unit_seen)

    # Validate hidden listed as visible
    # "hidden_listed_as_visible:<path>" when a hidden test path also appears in any unit's "tests" or "context_files".
    visible_paths: set[str] = set()
    for unit in units:
        for p in _get_list(unit, "tests"):
            visible_paths.add(p)
            visible_paths.add(_normalize_path(p))
        for p in _get_list(unit, "context_files"):
            visible_paths.add(p)
            visible_paths.add(_normalize_path(p))

    for unit in units:
        for p in _get_list(unit, "hidden_tests"):
            if p in visible_paths or _normalize_path(p) in visible_paths:
                raise ValueError(f"hidden_listed_as_visible:{p}")

    # Validate missing test files
    # "missing_test_file:<path>" when a path in a unit's "tests" or "hidden_tests" does not exist as a file relative to plan_dir.
    for unit in units:
        for p in _get_list(unit, "tests"):
            test_path = plan_dir / p
            if not test_path.is_file():
                raise ValueError(f"missing_test_file:{p}")
        for p in _get_list(unit, "hidden_tests"):
            test_path = plan_dir / p
            if not test_path.is_file():
                raise ValueError(f"missing_test_file:{p}")

    # Validate unknown dependencies
    # "unknown_dependency:<id>" when "depends_on" names a unit id that is not present.
    unit_map: dict[str, dict[str, Any]] = {u["id"]: u for u in units if "id" in u}
    for unit in units:
        for dep in _get_list(unit, "depends_on"):
            if dep not in unit_map:
                raise ValueError(f"unknown_dependency:{dep}")

    # Topological ordering with tie-break
    # Order units topologically by "depends_on" (dependencies first); among units that are ready at the same time
    # order by the unit's "order" field (int, default 0) and then by "id".
    in_degree: dict[str, int] = {}
    dependents: dict[str, list[str]] = {u["id"]: [] for u in units}

    for u in units:
        uid = u["id"]
        deps = set(_get_list(u, "depends_on"))
        in_degree[uid] = len(deps)
        for dep in deps:
            dependents[dep].append(uid)

    heap: list[tuple[int, str]] = []
    for u in units:
        uid = u["id"]
        if in_degree[uid] == 0:
            order_raw = u.get("order")
            order_val = int(order_raw) if order_raw is not None else 0
            heapq.heappush(heap, (order_val, uid))

    ordered_units: list[dict[str, Any]] = []
    while heap:
        order_val, uid = heapq.heappop(heap)
        ordered_units.append(unit_map[uid])
        for dep_uid in dependents[uid]:
            in_degree[dep_uid] -= 1
            if in_degree[dep_uid] == 0:
                dep_unit = unit_map[dep_uid]
                d_order_raw = dep_unit.get("order")
                d_order_val = int(d_order_raw) if d_order_raw is not None else 0
                heapq.heappush(heap, (d_order_val, dep_uid))

    if len(ordered_units) < len(units):
        raise ValueError("dependency_cycle")

    # Construct merged plan
    plan_data = dict(base_data)
    plan_data["units"] = ordered_units
    serialized = json.dumps(plan_data, indent=2, ensure_ascii=False) + "\n"
    target_bytes = serialized.encode("utf-8")

    plan_file = plan_dir / "plan.json"
    written = False
    if plan_file.is_file():
        existing_bytes = plan_file.read_bytes()
        if existing_bytes != target_bytes:
            plan_file.write_bytes(target_bytes)
            written = True
    else:
        plan_file.write_bytes(target_bytes)
        written = True

    return {
        "units": len(ordered_units),
        "written": written,
        "order": [u["id"] for u in ordered_units],
    }


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print(json.dumps({"error": "invalid_arguments"}))
        return 2

    plan_dir = Path(argv[0])
    try:
        result = merge(plan_dir)
        print(json.dumps(result))
        return 0
    except ValueError as e:
        print(json.dumps({"error": str(e)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
