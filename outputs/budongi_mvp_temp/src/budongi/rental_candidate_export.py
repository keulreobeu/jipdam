"""Export pending canonical rental match candidates for local human review."""
from __future__ import annotations

import csv
import hashlib
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


class CandidateExportError(ValueError):
    """Raised when a candidate report cannot be safely exported."""


PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PAIR_FIELDS = (
    "observation_id", "candidate_complex_id", "identifier_namespace", "source_complex_id",
    "kind", "sgg_cd", "legal_dong", "jibun", "apartment_name", "contract_date",
    "source_id", "batch_ids", "supporting_observation_ids", "candidate_link_rows",
    "review_status", "confidence", "confidence_score", "match_basis",
)
_GROUP_FIELDS = (
    "kind", "sgg_cd", "legal_dong", "jibun", "apartment_name", "candidate_complex_id",
    "identifier_namespace", "source_complex_id", "candidate_observations", "candidate_link_rows",
    "first_contract_date", "last_contract_date", "candidate_complex_count", "ambiguous",
    "review_status", "confidence",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _csv_cell(value: object) -> str:
    """Neutralize spreadsheet formula prefixes in values sourced from public data."""
    if value is None:
        return ""
    text = str(value)
    probe = text.lstrip(" \t\r\n")
    if probe.startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
        return "'" + text
    return text


def _write_csv(path: Path, fields: tuple[str, ...], rows: Iterable[sqlite3.Row]) -> int:
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            values = {}
            for field in fields:
                value = row[field]
                if field in {"batch_ids", "supporting_observation_ids"} and value:
                    value = ",".join(sorted(set(value.split(","))))
                values[field] = _csv_cell(value)
            writer.writerow(values)
            count += 1
    return count


def _pairs_query(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute("""
        SELECT m.observation_id, m.complex_id AS candidate_complex_id,
               c.identifier_namespace, c.source_complex_id, o.kind, o.sgg_cd,
               o.legal_dong, o.jibun, o.apartment_name, o.contract_date, o.source_id,
               group_concat(DISTINCT m.batch_id) AS batch_ids,
               group_concat(DISTINCT m.supporting_observation_id) AS supporting_observation_ids,
               COUNT(*) AS candidate_link_rows, m.review_status, m.confidence,
               m.confidence_score, m.match_basis
        FROM match_candidates m
        JOIN observations o ON o.observation_id=m.observation_id
        JOIN complexes c ON c.complex_id=m.complex_id
        WHERE o.kind IN ('jeonse','wolse') AND o.complex_id IS NULL
          AND m.review_status='pending' AND m.confidence='unverified'
        GROUP BY m.observation_id, m.complex_id
        ORDER BY o.kind, o.sgg_cd, o.legal_dong, o.jibun, o.apartment_name,
                 m.complex_id, o.contract_date, m.observation_id
    """).fetchall()


def _groups_query(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute("""
        WITH pairs AS (
            SELECT DISTINCT m.observation_id, m.complex_id, o.kind, o.sgg_cd,
                   o.legal_dong, o.jibun, o.apartment_name, o.contract_date
            FROM match_candidates m JOIN observations o ON o.observation_id=m.observation_id
            WHERE o.kind IN ('jeonse','wolse') AND o.complex_id IS NULL
              AND m.review_status='pending' AND m.confidence='unverified'
        ), per_complex AS (
            SELECT kind, sgg_cd, legal_dong, jibun, apartment_name, complex_id,
                   COUNT(DISTINCT observation_id) AS candidate_observations,
                   COUNT(*) AS candidate_link_rows,
                   MIN(contract_date) AS first_contract_date,
                   MAX(contract_date) AS last_contract_date
            FROM pairs
            GROUP BY kind, sgg_cd, legal_dong, jibun, apartment_name, complex_id
        ), ambiguity AS (
            SELECT kind, sgg_cd, legal_dong, jibun, apartment_name,
                   COUNT(DISTINCT complex_id) AS candidate_complex_count
            FROM pairs
            GROUP BY kind, sgg_cd, legal_dong, jibun, apartment_name
        )
        SELECT p.kind, p.sgg_cd, p.legal_dong, p.jibun, p.apartment_name,
               p.complex_id AS candidate_complex_id, c.identifier_namespace, c.source_complex_id,
               p.candidate_observations, p.candidate_link_rows,
               p.first_contract_date, p.last_contract_date, a.candidate_complex_count,
               CASE WHEN a.candidate_complex_count > 1 THEN 'yes' ELSE 'no' END AS ambiguous,
               'pending' AS review_status, 'unverified' AS confidence
        FROM per_complex p JOIN ambiguity a USING(kind,sgg_cd,legal_dong,jibun,apartment_name)
        JOIN complexes c ON c.complex_id=p.complex_id
        ORDER BY p.kind,p.sgg_cd,p.legal_dong,p.jibun,p.apartment_name,p.complex_id
    """).fetchall()


def export_rental_candidates(canonical_db: Path, output_dir: Path, *, project_root: Path = PROJECT_ROOT) -> dict:
    """Write a non-importable CSV report without mutating canonical or serving data."""
    database = Path(canonical_db).expanduser().resolve()
    if not database.is_file():
        raise CandidateExportError("canonical SQLite 파일을 찾을 수 없습니다.")
    product_root = Path(project_root).expanduser().resolve()
    local_root = (product_root / ".local_runtime").resolve()
    destination = Path(output_dir).expanduser()
    if not destination.is_absolute():
        destination = product_root / destination
    destination = destination.resolve()
    if destination == local_root or not destination.is_relative_to(local_root):
        raise CandidateExportError("출력은 제품 .local_runtime 하위의 새 폴더여야 합니다.")
    if destination.exists():
        raise CandidateExportError("기존 출력 폴더는 덮어쓰지 않습니다.")

    before_hash = _sha256(database)
    uri = database.as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        required = {"observations", "match_candidates", "complexes"}
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not required.issubset(tables):
            raise CandidateExportError("canonical 스키마에 필요한 표가 없습니다.")
        pair_rows = _pairs_query(connection)
        group_rows = _groups_query(connection)
    except sqlite3.Error as exc:
        raise CandidateExportError("canonical 후보를 읽을 수 없습니다.") from exc
    finally:
        if "connection" in locals():
            connection.close()

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".rental-candidate-export-", dir=destination.parent))
    try:
        pair_count = _write_csv(temporary / "candidate_pairs.csv", _PAIR_FIELDS, pair_rows)
        group_count = _write_csv(temporary / "candidate_groups.csv", _GROUP_FIELDS, group_rows)
        ambiguous_groups = len({
            (row["kind"], row["sgg_cd"], row["legal_dong"], row["jibun"], row["apartment_name"])
            for row in group_rows if row["ambiguous"] == "yes"
        })
        created = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        file_hashes = {
            name: _sha256(temporary / name)
            for name in ("candidate_pairs.csv", "candidate_groups.csv")
        }
        (temporary / "README.txt").write_text(
            "전월세 단지 후보 검토 참고표\n\n"
            "이 출력은 canonical의 pending/unverified 후보를 사람이 살펴보기 위한 로컬 참고자료입니다.\n"
            "검수 승인·관계 확정·추천 serving 입력이 아니며 rental_review_v1 패키지로 가져올 수 없습니다.\n"
            "candidate_pairs.csv는 관측-후보 단지 관계, candidate_groups.csv는 동일 라벨 묶음과 복수 후보 여부입니다.\n"
            "매매, 원본 payload, 거래 금액은 제외했습니다. 결정은 여기서 저장하거나 자동 반영하지 않습니다.\n\n"
            f"생성 시각(UTC): {created}\n원본 canonical SHA-256: {before_hash}\n"
            f"관측-후보 쌍: {pair_count}\n후보 그룹 행: {group_count}\n"
            f"복수 후보 그룹: {ambiguous_groups}\n\n"
            f"candidate_pairs.csv SHA-256: {file_hashes['candidate_pairs.csv']}\n"
            f"candidate_groups.csv SHA-256: {file_hashes['candidate_groups.csv']}\n",
            encoding="utf-8",
            newline="",
        )
        if _sha256(database) != before_hash:
            raise CandidateExportError("읽기 전후 canonical 해시가 달라 출력하지 않았습니다.")
        temporary.rename(destination)
    except Exception:
        for child in temporary.iterdir():
            child.unlink()
        temporary.rmdir()
        raise
    return {
        "status": "exported_review_reference_only",
        "output_dir": str(destination),
        "source_db_sha256": before_hash,
        "candidate_pair_rows": pair_count,
        "candidate_group_rows": group_count,
        "ambiguous_groups": ambiguous_groups,
        "importable_review_package": False,
    }
