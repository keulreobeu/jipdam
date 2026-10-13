"""Verify and rebuild the source packages shared with the Jipdam team.

Run this copy inside an extracted portable ZIP with Python 3.11+.
Dependencies: pip install 'openpyxl>=3.1' 'cryptography>=42'.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import sys
import zipfile
from pathlib import Path, PurePosixPath
from unittest.mock import patch


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def inside(root: Path, relative: str) -> Path:
    p = PurePosixPath(relative)
    if not relative or p.is_absolute() or '..' in p.parts or '\\' in relative or ':' in relative:
        raise ValueError('Unsafe package path')
    target = (root / p).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Package path escapes root')
    return target


def verify(root: Path) -> dict:
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 'jipdam_portable_v1':
        raise ValueError('Unsupported portable package')
    for entry in manifest['files']:
        path = inside(root, entry['path'])
        if path.stat().st_size != entry['bytes'] or sha256(path) != entry['sha256']:
            raise ValueError('Package file hash mismatch: ' + entry['path'])
    return manifest


def extract(archive: Path, destination: Path) -> None:
    if destination.exists():
        raise ValueError('Extraction output already exists')
    with zipfile.ZipFile(archive) as z:
        names = [i.filename for i in z.infolist()]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP member')
        for info in z.infolist():
            inside(destination, info.filename)
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('ZIP links are not supported')
        if z.testzip() is not None:
            raise ValueError('ZIP CRC failure')
        destination.mkdir(parents=True)
        z.extractall(destination)


def database_facts(path: Path, *, omit: dict[str, set[str]] | None = None) -> dict:
    """Digest every logical row; disregard only explicitly named vintage fields."""
    c = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        if c.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or c.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('SQLite integrity failure')
        result = {}
        for (table,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            quote = lambda s: '"' + s.replace('"', '""') + '"'
            cols = [r[1] for r in c.execute('PRAGMA table_info(' + quote(table) + ')') if r[1] not in (omit or {}).get(table, set())]
            selected = ','.join(map(quote, cols))
            digest = hashlib.sha256()
            count = 0
            for row in c.execute('SELECT ' + selected + ' FROM ' + quote(table) + ' ORDER BY ' + selected):
                digest.update((json.dumps(tuple(row), ensure_ascii=False, separators=(',', ':')) + '\n').encode())
                count += 1
            result[table] = {'rows': count, 'sha256': digest.hexdigest(), 'columns': cols}
        return result
    finally:
        c.close()


def rebuild(root: Path, output: Path) -> dict:
    manifest = verify(root)
    if output.exists():
        raise ValueError('Use a new output directory')
    # Only import the exact runtime whose bytes were verified above.
    sys.path.insert(0, str(root / 'runtime' / 'src'))
    output.mkdir(parents=True)
    # SQLite's sort files must use the same drive selected for the rebuild.
    temp_root = (output / '.sqlite-temp').resolve()
    temp_root.mkdir()
    for variable in ('TMP', 'TEMP', 'SQLITE_TMPDIR'):
        os.environ[variable] = str(temp_root)
    def forbidden(*args, **kwargs):
        raise RuntimeError('Network access is forbidden during source rebuild')
    with patch.object(socket, 'socket', forbidden), patch.object(socket, 'create_connection', forbidden):
        kind = manifest['kind']
        if kind == 'molit':
            from budongi.collection_db import build_databases
            from budongi.collection_integrate import integrate_collection
            extract(root / 'inputs' / 'molit-source.zip', output / 'full')
            full = output / 'full'
            build_databases(full, output / 'observations')
            shutil.copytree(root / 'inputs' / 'pilot', output / 'pilot')
            build_databases(output / 'pilot', output / 'pilot-db')
            # Preserve the original historical knowledge: pilot was integrated first.
            integrate_collection(output / 'pilot', output / 'pilot-db', output / 'canonical-pilot')
            integrate_collection(full, output / 'observations', output / 'canonical', previous=output / 'canonical-pilot')
            actual = {'canonical': database_facts(output / 'canonical' / 'canonical.sqlite3', omit={'batches': {'archive_root'}})}
            for name in ('rental', 'sales', 'staging'):
                vintage_fields = {'rental_snapshots': {'created_at_utc'}, 'rental_observations': {'ingested_at_utc'}} if name == 'rental' else None
                actual[name] = database_facts(output / 'observations' / (name + '.sqlite3'), omit=vintage_fields)
        elif kind == 'statistics':
            from budongi.statistics_storage import import_statistics
            inputs = [inside(root, p) for p in manifest['statistics_inputs']]
            db = output / 'statistics.sqlite3'
            import_statistics(db, manifest['batch_id'], inputs)
            c = sqlite3.connect(db)
            try:
                with c:
                    for review in manifest['metadata_reviews']:
                        c.execute('INSERT INTO metadata_reviews VALUES(?,?,?,?,?)', review)
            finally:
                c.close()
            actual = {'statistics': database_facts(db, omit={'import_batches': {'imported_at_utc'}})}
        else:
            raise ValueError('Unknown package kind')
    if actual != manifest['expected_database_facts']:
        raise ValueError('Rebuilt database differs from the packaged baseline')
    result = {'kind': kind, 'status': 'verified', 'network_access': 'blocked', 'database_facts': actual}
    (output / 'rebuild-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['verify', 'rebuild'])
    p.add_argument('--package-root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    if args.action == 'rebuild' and args.output is None:
        p.error('rebuild requires --output')
    try:
        result = verify(args.package_root) if args.action == 'verify' else rebuild(args.package_root, args.output)
        print(json.dumps({'status': 'verified', 'kind': result['kind']}, ensure_ascii=False))
    except (ValueError, OSError, sqlite3.Error, zipfile.BadZipFile) as exc:
        print(json.dumps({'status': 'failed', 'reason': str(exc)}, ensure_ascii=False))
        raise SystemExit(2) from None


if __name__ == '__main__':
    main()
