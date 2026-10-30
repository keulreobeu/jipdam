"""COLLECT-001 Issue parsing and overlap search."""
from __future__ import annotations

import re

from budongi.team_collection import contract as C

SEOUL_WIDE: frozenset[str] = frozenset({"서울", "서울전체", "서울특별시", "서울시", "서울25구", "11"})
"""Normalized region tokens representing all of Seoul."""

_YEAR_RE = re.compile(r"^[0-9]{4}$")
_YM_6_RE = re.compile(r"^([0-9]{4})(0[1-9]|1[0-2])$")
_YM_SEP_RE = re.compile(r"^([0-9]{4})[-.](0[1-9]|1[0-2])$")
_SCOPE_PERIOD_RE = re.compile(r"^[0-9]{4}(?:0[1-9]|1[0-2])$")
_REGION_DELIM_RE = re.compile(r"[,·/;]")


def _normalize(text: str) -> str:
    return "".join(c for c in text if not c.isspace()).casefold()


def _parse_period_part(part: str, is_start: bool) -> str | None:
    if _YEAR_RE.match(part):
        return f"{part}01" if is_start else f"{part}12"
    m6 = _YM_6_RE.match(part)
    if m6:
        return f"{m6.group(1)}{m6.group(2)}"
    m_sep = _YM_SEP_RE.match(part)
    if m_sep:
        return f"{m_sep.group(1)}{m_sep.group(2)}"
    return None


def parse_period(text: str | None) -> tuple[str, str] | None:
    """Return the inclusive month range ('YYYYMM', 'YYYYMM') of a period text, or None."""
    if not isinstance(text, str):
        return None
    s = text.strip()
    if not s:
        return None
    if "~" in s:
        parts = s.split("~")
        if len(parts) != 2:
            return None
        start_part, end_part = parts[0].strip(), parts[1].strip()
    else:
        start_part = end_part = s

    p_start = _parse_period_part(start_part, is_start=True)
    if p_start is None:
        return None
    p_end = _parse_period_part(end_part, is_start=False)
    if p_end is None:
        return None
    if p_start > p_end:
        return None
    return (p_start, p_end)


def parse_issue(issue: dict) -> dict:
    """Return the structured view of one issue dict, or raise ContractError('invalid_issue')."""
    if not isinstance(issue, dict):
        raise C.ContractError("invalid_issue")
    if "number" not in issue:
        raise C.ContractError("invalid_issue")
    number = issue["number"]
    if isinstance(number, bool) or not isinstance(number, int):
        raise C.ContractError("invalid_issue")

    raw_title = issue.get("title")
    title = "" if raw_title is None else raw_title
    state = issue.get("state")
    raw_body = issue.get("body")
    body = "" if raw_body is None else raw_body
    is_pr_val = issue.get("is_pr", False)
    is_pr = False if is_pr_val is None else bool(is_pr_val)

    title_stripped = title.strip() if isinstance(title, str) else ""
    is_collection = title_stripped.startswith("[수집]")

    source: str | None = None
    kind: str | None = None
    region: str | None = None
    period: str | None = None

    if is_collection:
        after_prefix = title_stripped[len("[수집]"):]
        parts = after_prefix.split("|")
        if len(parts) == 4:
            s_parts = [p.strip() for p in parts]
            source = s_parts[0] if s_parts[0] != "" else None
            kind = s_parts[1] if s_parts[1] != "" else None
            region = s_parts[2] if s_parts[2] != "" else None
            period = s_parts[3] if s_parts[3] != "" else None

    if region is None:
        regions: tuple[str, ...] | None = None
        seoul_wide = False
    else:
        raw_pieces = _REGION_DELIM_RE.split(region)
        norm_pieces = []
        for p in raw_pieces:
            norm_p = _normalize(p)
            if norm_p:
                norm_pieces.append(norm_p)
        regions = tuple(sorted(set(norm_pieces)))
        seoul_wide = any(p in SEOUL_WIDE for p in regions)

    parsed_period = parse_period(period)
    if parsed_period is not None:
        period_start, period_end = parsed_period
    else:
        period_start, period_end = None, None

    sections: dict[str, str | None] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    def _flush_section() -> None:
        nonlocal current_heading, current_lines
        if current_heading is not None:
            val = "\n".join(current_lines).strip()
            final_val = None if (val == "" or val == "_No response_") else val
            if current_heading not in sections:
                sections[current_heading] = final_val
        current_lines = []

    body_str = body if isinstance(body, str) else ""
    for line in body_str.splitlines():
        if line.startswith("### "):
            _flush_section()
            current_heading = line[4:].strip()
        elif current_heading is not None:
            current_lines.append(line)
    _flush_section()

    status = sections.get("상태")
    review_val = sections.get("데이터 검수 구분")
    synthetic = isinstance(review_val, str) and ("합성" in review_val)

    return {
        "number": number,
        "title": title,
        "state": state,
        "is_pr": is_pr,
        "is_collection": is_collection,
        "source": source,
        "kind": kind,
        "region": region,
        "period": period,
        "regions": regions,
        "seoul_wide": seoul_wide,
        "period_start": period_start,
        "period_end": period_end,
        "sections": sections,
        "status": status,
        "synthetic": synthetic,
    }


def find_overlaps(planned: dict, issues: list) -> list[dict]:
    """Validate planned scope, parse issues and return hit dicts sorted by number ascending."""
    if not isinstance(planned, dict) or "source" not in planned:
        raise C.ContractError("invalid_scope:source")
    source = planned["source"]
    if not isinstance(source, str) or not source.strip():
        raise C.ContractError("invalid_scope:source")

    if "kind" not in planned:
        raise C.ContractError("invalid_scope:kind")
    kind = planned["kind"]
    if not isinstance(kind, str) or not kind.strip():
        raise C.ContractError("invalid_scope:kind")

    if "regions" not in planned:
        raise C.ContractError("invalid_scope:regions")
    regions = planned["regions"]
    if isinstance(regions, str) or not isinstance(regions, (list, tuple, set, frozenset)):
        raise C.ContractError("invalid_scope:regions")
    if len(regions) < 1:
        raise C.ContractError("invalid_scope:regions")
    for r in regions:
        if not isinstance(r, str) or not _normalize(r):
            raise C.ContractError("invalid_scope:regions")

    if "period_start" not in planned or "period_end" not in planned:
        raise C.ContractError("invalid_scope:period")
    p_start = planned["period_start"]
    p_end = planned["period_end"]
    if not isinstance(p_start, str) or not isinstance(p_end, str):
        raise C.ContractError("invalid_scope:period")
    if not _SCOPE_PERIOD_RE.match(p_start) or not _SCOPE_PERIOD_RE.match(p_end):
        raise C.ContractError("invalid_scope:period")
    if p_start > p_end:
        raise C.ContractError("invalid_scope:period")

    tokens_val = planned.get("tokens")
    if tokens_val is None:
        planned_tokens: list[str] = []
    elif isinstance(tokens_val, (list, tuple)):
        if not all(isinstance(t, str) for t in tokens_val):
            raise C.ContractError("invalid_scope:tokens")
        planned_tokens = list(tokens_val)
    else:
        raise C.ContractError("invalid_scope:tokens")

    if not isinstance(issues, (list, tuple)):
        raise C.ContractError("invalid_issue")

    planned_norm_source = _normalize(source)
    planned_norm_kind = _normalize(kind)
    planned_norm_regions = {_normalize(r) for r in regions}
    planned_seoul_wide = any(r in SEOUL_WIDE for r in planned_norm_regions)

    hits: list[dict] = []

    for issue in issues:
        parsed = parse_issue(issue)

        if parsed["is_pr"] or not parsed["is_collection"] or parsed["synthetic"]:
            continue

        candidates: list[str] = []
        if parsed["source"] is not None:
            candidates.append(parsed["source"])
        sec_source = parsed["sections"].get("출처·데이터 종류")
        if sec_source is not None:
            candidates.append(sec_source)

        if not candidates:
            source_undetermined = True
            source_matches = True
        else:
            source_undetermined = False
            cand_match = False
            for cand in candidates:
                norm_c = _normalize(cand)
                if norm_c and (planned_norm_source in norm_c or norm_c in planned_norm_source):
                    cand_match = True
                    break

            token_match = False
            if not cand_match:
                raw_title_str = parsed["title"] if isinstance(parsed["title"], str) else ""
                raw_body_val = issue.get("body")
                raw_body_str = raw_body_val if isinstance(raw_body_val, str) else ""
                corpus = f"{raw_title_str}\n{raw_body_str}"
                for tok in planned_tokens:
                    tok_stripped = tok.strip()
                    if len(tok_stripped) >= 4 and tok_stripped in corpus:
                        token_match = True
                        break

            source_matches = cand_match or token_match

        if not source_matches:
            continue

        if parsed["kind"] is None:
            kind_undetermined = True
            kind_matches = True
        else:
            kind_undetermined = False
            norm_k = _normalize(parsed["kind"])
            kind_matches = bool(norm_k and (planned_norm_kind in norm_k or norm_k in planned_norm_kind))

        if not kind_matches:
            continue

        if parsed["regions"] is None:
            region_undetermined = True
            region_matches = True
        else:
            region_undetermined = False
            region_matches = (
                planned_seoul_wide
                or parsed["seoul_wide"]
                or bool(planned_norm_regions.intersection(parsed["regions"]))
            )

        if not region_matches:
            continue

        if parsed["period_start"] is None:
            period_undetermined = True
            period_matches = True
            period_overlap: tuple[str, str] | None = None
        else:
            period_undetermined = False
            overlap_start = max(p_start, parsed["period_start"])
            overlap_end = min(p_end, parsed["period_end"])
            if overlap_start <= overlap_end:
                period_matches = True
                period_overlap = (overlap_start, overlap_end)
            else:
                period_matches = False
                period_overlap = None

        if not period_matches:
            continue

        status = parsed["status"]
        blocking = not (isinstance(status, str) and status.startswith("실패"))

        undetermined_fields: list[str] = []
        if kind_undetermined:
            undetermined_fields.append("kind")
        if period_undetermined:
            undetermined_fields.append("period")
        if region_undetermined:
            undetermined_fields.append("region")
        if source_undetermined:
            undetermined_fields.append("source")
        undetermined_fields.sort()

        hit = {
            "number": parsed["number"],
            "title": parsed["title"],
            "state": parsed["state"],
            "status": status,
            "blocking": blocking,
            "undetermined": undetermined_fields,
            "period_overlap": period_overlap,
        }
        hits.append(hit)

    hits.sort(key=lambda h: h["number"])
    return hits
