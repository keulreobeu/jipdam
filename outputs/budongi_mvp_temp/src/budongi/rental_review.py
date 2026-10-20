"""Offline review-package validation. This module never creates or approves matches."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

from .rental_recommendation import RentalDataUnavailable, FACILITY_KINDS


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ValueError('missing review text')
    value.encode('utf-8')
    return value


def _time(value: object) -> str:
    value = _text(value)
    if datetime.fromisoformat(value.replace('Z', '+00:00')).tzinfo is None:
        raise ValueError('review time requires timezone')
    return value


def _coordinate(row: dict) -> None:
    if row.get('crs') != 'EPSG:4326':
        raise ValueError('only normalized WGS84 is accepted')
    for key, low, high in [('latitude', -90, 90), ('longitude', -180, 180)]:
        value = row[key]
        if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError('invalid coordinate')
    _text(row.get('method'))


def load_review_package(path: Path, source_hash: str, *, allow_synthetic: bool = False) -> dict:
    """Validate manifest, file hashes, declared approval and every record's lineage.

    Approval references are operator-supplied evidence, not a digital signature.
    The importer must only be invoked with an already authorized review package.
    """
    try:
        root = path.resolve(strict=True)
        manifest_bytes = (root / 'manifest.json').read_bytes()
        manifest = json.loads(manifest_bytes)
        if manifest['schema_version'] != 'rental_review_v1' or manifest['source_db_sha256'] != source_hash:
            raise ValueError('package source/version mismatch')
        quality = manifest['quality_status']
        if quality not in ('reviewed_real', 'synthetic_only') or (quality == 'synthetic_only' and not allow_synthetic):
            raise ValueError('synthetic package requires explicit opt-in')
        for key in ('approval_ref', 'approved_by'):
            _text(manifest[key])
        _time(manifest['approved_at_utc'])
        if 'snapshot_date' in manifest:
            cutoff = date.fromisoformat(manifest['snapshot_date'])
            approved_day = datetime.fromisoformat(manifest['approved_at_utc'].replace('Z','+00:00')).astimezone(timezone(timedelta(hours=9))).date()
            if cutoff.isoformat() != manifest['snapshot_date'] or cutoff > approved_day:
                raise ValueError('serving cutoff must be an explicitly approved calendar date')
        files = {}
        for entry in manifest['files']:
            relative = entry['path']
            if not isinstance(relative, str) or Path(relative).is_absolute() or '..' in Path(relative).parts:
                raise ValueError('invalid package path')
            candidate = (root / relative).resolve(strict=True)
            if not candidate.is_relative_to(root) or candidate.stat().st_size > 50 * 1024 * 1024:
                raise ValueError('package file outside root or too large')
            if file_sha256(candidate) != entry['sha256'] or relative in files:
                raise ValueError('package hash mismatch or duplicate file')
            files[relative] = entry
        records_refs = manifest.get('records_files')
        if records_refs is None:
            records_refs = [manifest['records_file']]
        if (not isinstance(records_refs, list) or not records_refs or
                any(not isinstance(ref, str) or ref not in files for ref in records_refs) or
                len(set(records_refs)) != len(records_refs)):
            raise ValueError('records files must be uniquely declared and hashed')
        records = {category: [] for category in ('relations', 'coordinates', 'facilities', 'coverage')}
        for records_ref in records_refs:
            part = json.loads((root / records_ref).read_bytes())
            if not isinstance(part, dict) or set(part) - set(records):
                raise ValueError('unsupported record collection')
            for category in records:
                rows = part.get(category, [])
                if not isinstance(rows, list):
                    raise ValueError('record collection must be list')
                records[category].extend(rows)
        for category in records:
            for row in records[category]:
                if not isinstance(row, dict) or row['review_status'] not in ('confirmed', 'pending', 'rejected'):
                    raise ValueError('invalid review status')
                for key in ('evidence', 'reviewed_by', 'source_id', 'source_file_ref'):
                    _text(row[key])
                _time(row['reviewed_at_utc'])
                date.fromisoformat(row['source_date'])
                evidence_file = files.get(row['source_file_ref'])
                if not evidence_file or row['source_content_sha256'] != evidence_file['sha256']:
                    raise ValueError('record lineage is not declared in manifest')
                if type(row['source_row_number']) is not int or row['source_row_number'] < 1:
                    raise ValueError('invalid source row')
                if category == 'relations':
                    _text(row['observation_id'])
                    _text(row['complex_id'])
                    if row.get('source_status') not in ('valid', 'cancelled', 'correction_pending', 'unknown'):
                        raise ValueError('explicit transaction status is required')
                elif category in ('coordinates', 'facilities'):
                    _coordinate(row)
                    _text(row['complex_id'] if category == 'coordinates' else row['facility_id'])
                    if category == 'facilities' and row['category'] not in FACILITY_KINDS:
                        raise ValueError('unsupported facility')
                else:
                    if row['category'] not in FACILITY_KINDS or row['coverage_status'] not in ('complete', 'partial', 'unknown'):
                        raise ValueError('invalid coverage')
                    _text(row['sgg_cd'])
                    _time(row['checked_at_utc'])
                    area = row['coverage_area']
                    _coordinate({**area, 'crs': 'EPSG:4326', 'method': 'reviewed-circle'})
                    radius = area['radius_m']
                    if type(radius) not in (float, int) or not math.isfinite(radius) or radius <= 0:
                        raise ValueError('invalid coverage radius')
        return {**records, 'manifest': manifest,
                'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest()}
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        raise RentalDataUnavailable('검수 패키지의 버전·승인·해시·계보·좌표 계약을 확인해 주세요.') from exc
