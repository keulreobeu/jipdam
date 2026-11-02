"""Read-only validation of the bounded facility submission profile."""
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl


def validate_package(package_root: Path | str) -> dict:
    root = Path(package_root)
    errors = []
    counts = dict.fromkeys(('raw', 'accepted', 'excluded', 'rejected'))

    def err(file, row, field, reason):
        errors.append(dict(file=file, row=row, field=field, reason=reason))

    def safe(name):
        if not isinstance(name, str) or not name or '\\' in name or name.startswith('/') or re.match(r'^[A-Za-z]:', name):
            return False
        parts = name.split('/')
        if any(p in ('', '.', '..') for p in parts):
            return False
        p = root
        try:
            if p.is_symlink():
                return False
            for part in parts:
                p = p / part
                if p.is_symlink():
                    return False
            return p.resolve().is_relative_to(root.resolve())
        except (OSError, ValueError, RuntimeError):
            return False

    def read(name):
        if not safe(name):
            err('manifest.json', None, 'files.path', 'unsafe_path')
            return None
        try:
            return (root / name).read_bytes()
        except (OSError, ValueError):
            err(name, None, 'path', 'file_missing')
            return None

    def parse_json(data, name):
        if data is None:
            return None
        try:
            return json.loads(data.decode('utf-8'), parse_constant=lambda x: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeError, RecursionError):
            err(name, None, 'json', 'invalid_json')
            return None

    def text(v):
        return isinstance(v, str) and bool(v.strip())

    def integer(v):
        return type(v) is int and v >= 0

    def require(obj, key, file='manifest.json', row=None):
        if key not in obj:
            err(file, row, key, 'required')
            return False
        return True

    manifest = parse_json(read('manifest.json'), 'manifest.json')
    if not isinstance(manifest, dict):
        if manifest is not None:
            err('manifest.json', None, 'manifest', 'invalid_type')
        manifest = {}
    for key in ('source_id', 'dataset_id', 'provider', 'documentation_url', 'batch_id', 'mapping_version', 'collector', 'record_url', 'approval_ref'):
        if require(manifest, key) and not text(manifest[key]):
            err('manifest.json', None, key, 'invalid_type' if not isinstance(manifest[key], str) else 'required')
    if not text(manifest.get('license_ref')) and not text(manifest.get('license_text')):
        err('manifest.json', None, 'license_ref', 'required')
    for key, options in (('delivery_schema_version', ('team_collection_v1',)), ('license_review_status', ('pending', 'verified', 'rejected')), ('quality_status', ('source_unverified', 'synthetic_only'))):
        if require(manifest, key) and manifest[key] not in options:
            err('manifest.json', None, key, 'invalid_value')
    for key in ('documentation_url', 'record_url'):
        if text(manifest.get(key)):
            try:
                u = urlsplit(manifest[key])
                keys = [re.sub(r'[^a-z0-9]', '', k.lower()) for k, _ in parse_qsl(u.query, keep_blank_values=True)]
                if u.scheme not in ('http', 'https') or not u.hostname or u.username is not None or u.password is not None or any(k in ('apikey', 'servicekey', 'token', 'authorization', 'accesstoken', 'refreshtoken', 'secret', 'clientsecret', 'key') for k in keys):
                    raise ValueError()
                _ = u.port
            except ValueError:
                err('manifest.json', None, key, 'invalid_value')
    if require(manifest, 'scope'):
        if not isinstance(manifest['scope'], dict):
            err('manifest.json', None, 'scope', 'invalid_type')
        else:
            for key in ('regions', 'period', 'filters'):
                if key not in manifest['scope']:
                    err('manifest.json', None, 'scope.' + key, 'required')
    for key in ('source_retrieved_at_utc', 'provided_at_utc', 'staged_at_utc', 'snapshot_date'):
        if key == 'snapshot_date' and key not in manifest:
            continue
        if not require(manifest, key) or manifest[key] is None:
            continue
        v = manifest[key]
        try:
            if not isinstance(v, str):
                raise ValueError()
            if key == 'snapshot_date':
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
                    raise ValueError()
                dt.date.fromisoformat(v)
            else:
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z', v):
                    raise ValueError()
                dt.datetime.fromisoformat(v[:-1] + '+00:00')
        except ValueError:
            err('manifest.json', None, key, 'invalid_value')
    for key in ('files', 'requests', 'missing_fields', 'errors', 'source_missing_dates'):
        if require(manifest, key) and not isinstance(manifest[key], list):
            err('manifest.json', None, key, 'invalid_type')
    for i, req in enumerate(manifest.get('requests', []) if isinstance(manifest.get('requests'), list) else [], 1):
        if not isinstance(req, dict):
            err('manifest.json', i, 'requests', 'invalid_type'); continue
        for k in ('collection_status', 'expected_rows', 'received_rows'):
            if k not in req:
                err('manifest.json', i, 'requests.' + k, 'required')
        if 'collection_status' in req and req['collection_status'] not in ('complete', 'complete_zero', 'partial', 'failed', 'not_collected'):
            err('manifest.json', i, 'requests.collection_status', 'invalid_value')
        for k in ('expected_rows', 'received_rows'):
            if k in req and not (k == 'expected_rows' and req[k] is None) and not integer(req[k]):
                err('manifest.json', i, 'requests.' + k, 'invalid_type')
        if req.get('collection_status') == 'complete_zero' and req.get('received_rows') != 0:
            err('manifest.json', i, 'requests.received_rows', 'invalid_value')
    declared = manifest.get('counts')
    if require(manifest, 'counts') and not isinstance(declared, dict):
        err('manifest.json', None, 'counts', 'invalid_type')
    if isinstance(declared, dict):
        for k in counts:
            if k not in declared:
                err('manifest.json', None, 'counts.' + k, 'required')
            elif not integer(declared[k]):
                err('manifest.json', None, 'counts.' + k, 'invalid_type')

    defaults = {}
    if safe('schema.json') and (root / 'schema.json').exists():
        schema = parse_json(read('schema.json'), 'schema.json')
        if not isinstance(schema, dict):
            err('schema.json', None, 'schema', 'invalid_type')
        elif not isinstance(schema.get('defaults', {}), dict):
            err('schema.json', None, 'defaults', 'invalid_type')
        else:
            defaults = schema.get('defaults', {})
    elif (root / 'schema.json').is_symlink():
        err('schema.json', None, 'path', 'unsafe_path')

    entries = manifest.get('files') if isinstance(manifest.get('files'), list) else []
    seen = set(); raw_hashes = {}; raw_total = 0; norm_total = 0
    raw_known = norm_known = True
    raw_found = norm_found = False
    records = []
    for i, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            err('manifest.json', i, 'files', 'invalid_type'); continue
        for k in ('path', 'format', 'bytes', 'sha256', 'section', 'rows'):
            if k not in entry:
                err('manifest.json', i, 'files.' + k, 'required')
        name = entry.get('path')
        if not safe(name):
            err('manifest.json', i, 'files.path', 'unsafe_path'); raw_known = norm_known = False; continue
        if name in seen:
            err('manifest.json', i, 'files.path', 'duplicate'); continue
        seen.add(name)
        israw = name.startswith('raw/'); isnorm = name.startswith('normalized/')
        raw_found |= israw; norm_found |= isnorm
        if not integer(entry.get('bytes')):
            err('manifest.json', i, 'files.bytes', 'invalid_type')
        digest = entry.get('sha256')
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            err('manifest.json', i, 'files.sha256', 'invalid_value')
        if not text(entry.get('section')):
            err('manifest.json', i, 'files.section', 'invalid_type')
        data = read(name)
        if data is None:
            if israw: raw_known = False
            if isnorm: norm_known = False
            continue
        actual_hash = hashlib.sha256(data).hexdigest()
        if israw: raw_hashes[name] = actual_hash
        if integer(entry.get('bytes')) and entry['bytes'] != len(data): err(name, None, 'bytes', 'bytes_mismatch')
        if isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest) and digest != actual_hash: err(name, None, 'sha256', 'sha256_mismatch')
        fmt = entry.get('format'); rows = entry.get('rows'); parsed = []; n = None
        if fmt in ('json', 'text') and not israw and not isnorm:
            if rows is not None: err(name, None, 'rows', 'invalid_rows')
        elif fmt in ('csv', 'jsonl'):
            if not integer(rows): err(name, None, 'rows', 'invalid_rows')
            try:
                content = data.decode('utf-8-sig')
                if fmt == 'csv':
                    reader = csv.reader(io.StringIO(content, newline=''), strict=True)
                    header = next(reader, None)
                    parsed_rows = list(reader)
                    n = len(parsed_rows)
                    if header is None or len(set(header)) != len(header): raise csv.Error()
                    if any(len(r) != len(header) for r in parsed_rows): raise csv.Error()
                    parsed = [dict(zip(header, r)) for r in parsed_rows]
                else:
                    n = 0
                    # JSON permits Unicode line separators (for example U+2028)
                    # inside strings. JSONL records are delimited by LF, so do
                    # not use str.splitlines(), which treats those characters
                    # as record boundaries.
                    for line in content.split('\n'):
                        if line.endswith('\r'): line = line[:-1]
                        if not line.strip(): continue
                        n += 1
                        try:
                            obj = json.loads(line, parse_constant=lambda x: (_ for _ in ()).throw(ValueError()))
                            if not isinstance(obj, dict): raise ValueError()
                            parsed.append((n, obj))
                        except (ValueError, RecursionError):
                            err(name, n, 'json', 'invalid_json')
                            if isnorm: norm_known = False
                            if israw: raw_known = False
                    if fmt == 'jsonl': parsed = parsed
            except (UnicodeError, csv.Error):
                err(name, None, 'csv' if fmt == 'csv' else 'json', 'invalid_csv' if fmt == 'csv' else 'invalid_json')
                n = None
            if n is not None and integer(rows) and n != rows: err(name, None, 'rows', 'rows_mismatch')
            if israw:
                if n is None: raw_known = False
                else: raw_total += n
            if isnorm:
                if n is None: norm_known = False
                else: norm_total += n
                records.extend((name, row, obj, fmt) for row, obj in (parsed if fmt == 'jsonl' else enumerate(parsed, 1)))
        else:
            err(name, None, 'format', 'unsupported_format')
            if israw: raw_known = False
            if isnorm: norm_known = False
    if not raw_found: err('manifest.json', None, 'files.raw', 'required'); raw_known = False
    if not norm_found: err('manifest.json', None, 'files.normalized', 'required'); norm_known = False
    counts['raw'] = raw_total if raw_known else None
    status_counts = dict.fromkeys(('accepted', 'excluded', 'rejected'), 0)
    status_known = norm_known
    for name, row, record, fmt in records:
        def val(k):
            return record[k] if k in record else defaults[k] if k in defaults else manifest.get(k)
        for k in ('delivery_schema_version', 'source_id', 'batch_id', 'mapping_version', 'record_type', 'quality_status', 'source_file_ref', 'source_content_sha256', 'source_section', 'source_row_number', 'validation_status', 'validation_reason', 'name', 'facility_type_code', 'entity_level'):
            v = val(k)
            if k not in record and k not in defaults and k not in manifest:
                err(name, row, k, 'required'); continue
            if k not in ('validation_reason', 'source_row_number') and not text(v):
                err(name, row, k, 'required' if isinstance(v, str) else 'invalid_type')
        for k in ('delivery_schema_version', 'source_id', 'batch_id', 'mapping_version'):
            if text(val(k)) and val(k) != manifest.get(k): err(name, row, k, 'metadata_mismatch')
        for k, expected in (('record_type', 'facility'), ('entity_level', 'facility')):
            if text(val(k)) and val(k) != expected: err(name, row, k, 'invalid_value')
        if text(val('quality_status')) and val('quality_status') not in ('source_unverified', 'synthetic_only'): err(name, row, 'quality_status', 'invalid_value')
        ref = val('source_file_ref')
        if not isinstance(ref, str) or ref not in raw_hashes:
            err(name, row, 'source_file_ref', 'provenance_mismatch')
        elif val('source_content_sha256') != raw_hashes[ref]:
            err(name, row, 'source_content_sha256', 'provenance_mismatch')
        number = val('source_row_number')
        # Only positivity is needed; converting an unbounded CSV digit string to
        # int would raise at Python's digit limit instead of returning a report.
        positive_row = type(number) is int and number > 0
        if fmt == 'csv' and isinstance(number, str):
            positive_row = bool(re.fullmatch(r'[0-9]+', number) and number.lstrip('0'))
        if not positive_row: err(name, row, 'source_row_number', 'invalid_value')
        status = val('validation_status')
        if not isinstance(status, str) or status not in status_counts:
            err(name, row, 'validation_status', 'invalid_value'); status_known = False
        else:
            status_counts[status] += 1
            if status != 'accepted' and not text(val('validation_reason')): err(name, row, 'validation_reason', 'required')
            if status == 'accepted' and val('validation_reason') is not None and not isinstance(val('validation_reason'), str): err(name, row, 'validation_reason', 'invalid_type')
        a, b = val('source_entity_id'), val('identifier_namespace')
        empty = lambda v: v is None or v == ''
        if not ((empty(a) and empty(b)) or (text(a) and text(b))): err(name, row, 'identifier_namespace', 'invalid_value')
        lat, lon = val('latitude'), val('longitude')
        if not (empty(lat) and empty(lon)):
            try:
                if empty(lat) or empty(lon) or isinstance(lat, bool) or isinstance(lon, bool) or (fmt != 'csv' and (not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)))): raise ValueError()
                x, y = float(lat), float(lon)
                if not math.isfinite(x) or not math.isfinite(y) or not (-90 <= x <= 90 and -180 <= y <= 180): raise ValueError()
            except (ValueError, TypeError, OverflowError): err(name, row, 'latitude/longitude', 'invalid_value')
    for k in status_counts: counts[k] = status_counts[k] if status_known else None
    if safe('validation.json') and (root / 'validation.json').exists():
        validation = parse_json(read('validation.json'), 'validation.json')
        if isinstance(validation, dict) and isinstance(validation.get('rejected'), list) and validation['rejected'] and status_counts['rejected'] == 0:
            err('validation.json', None, 'rejected', 'unsupported_layout'); counts['rejected'] = None
    elif (root / 'validation.json').is_symlink(): err('validation.json', None, 'path', 'unsafe_path')
    if raw_known and norm_known and raw_total != norm_total: err('manifest.json', None, 'counts.raw', 'counts_mismatch')
    if isinstance(declared, dict):
        for k, n in counts.items():
            if n is not None and integer(declared.get(k)) and declared[k] != n: err('manifest.json', None, 'counts.' + k, 'counts_mismatch')
        if all(integer(declared.get(k)) for k in counts) and declared['raw'] != sum(declared[k] for k in ('accepted', 'excluded', 'rejected')):
            err('manifest.json', None, 'counts.raw', 'counts_mismatch')
    errors.sort(key=lambda e: (e['file'], e['row'] or 0, e['field'], e['reason']))
    return {'schema_version': 'team_collection_validation_v1', 'record_type': 'facility', 'valid': not errors, 'counts': counts, 'errors': errors}


def main():
    if len(sys.argv) != 2:
        return 2
    report = validate_package(sys.argv[1])
    print(json.dumps(report, ensure_ascii=False, separators=(',', ':')))
    return 0 if report['valid'] else 2


if __name__ == '__main__':
    sys.exit(main())
