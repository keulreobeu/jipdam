"""Portable input integrity and safe extraction contracts."""
import importlib.util
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / 'scripts/shared_data.py'
_spec = importlib.util.spec_from_file_location('shared_data', _path)
shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(shared)


class SharedDataTests(unittest.TestCase):
    def test_parts_restore_exact_zip_and_reject_corruption_and_overwrite(self):
        spec = importlib.util.spec_from_file_location('join_parts', _path.with_name('join_shared_parts.py'))
        joiner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(joiner)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            whole = root / 'original.zip'
            with zipfile.ZipFile(whole, 'w') as z:
                z.writestr('original-data', b'complete source data')
            payload = whole.read_bytes()
            parts = []
            for n, b in enumerate((payload[:37], payload[37:]), 1):
                p = root / f'part{n}'
                p.write_bytes(b)
                parts.append({'name': p.name, 'bytes': len(b), 'sha256': shared.sha256(p)})
            manifest = root / 'parts.json'
            manifest.write_text(json.dumps({'schema_version': 'jipdam_zip_parts_v1', 'bytes': len(payload), 'sha256': shared.sha256(whole), 'parts': parts}), encoding='utf-8')
            restored = root / 'restored.zip'
            self.assertEqual(joiner.join_parts(manifest, restored), shared.sha256(whole))
            self.assertEqual(restored.read_bytes(), payload)
            with self.assertRaisesRegex(ValueError, 'already exists'):
                joiner.join_parts(manifest, restored)
            (root / 'part2').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'Part hash mismatch'):
                joiner.join_parts(manifest, root / 'invalid.zip')

    def test_manifest_tamper_and_path_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'input').write_bytes(b'original')
            m = {'schema_version': 'jipdam_portable_v1', 'kind': 'statistics', 'files': [
                {'path': 'input', 'bytes': 8, 'sha256': shared.sha256(root / 'input')}]}
            (root / 'manifest.json').write_text(json.dumps(m), encoding='utf-8')
            self.assertEqual(shared.verify(root)['kind'], 'statistics')
            (root / 'input').write_bytes(b'changed!')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                shared.verify(root)
            for path in ('../escape', '/absolute', 'C:/outside', 'x\\escape'):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    shared.inside(root, path)

    def test_zip_crc_path_and_existing_output_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'input.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('raw/data.xml', b'XML')
            shared.extract(archive, root / 'new')
            self.assertEqual((root / 'new/raw/data.xml').read_bytes(), b'XML')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                shared.extract(archive, root / 'new')
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('../outside.xml', b'XML')
            with self.assertRaises(ValueError):
                shared.extract(archive, root / 'unsafe')
            self.assertFalse((root / 'outside.xml').exists())

    def test_logical_digest_detects_changed_data_and_separates_environment_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'db.sqlite3'
            c = sqlite3.connect(path)
            try:
                c.execute('CREATE TABLE batches (id TEXT PRIMARY KEY,archive_root TEXT,value INTEGER)')
                c.execute("INSERT INTO batches VALUES ('b','old',100)")
                c.commit()
                first = shared.database_facts(path, omit={'batches': {'archive_root'}})
                c.execute("UPDATE batches SET archive_root='new'")
                c.commit()
                self.assertEqual(first, shared.database_facts(path, omit={'batches': {'archive_root'}}))
                c.execute('UPDATE batches SET value=101')
                c.commit()
                self.assertNotEqual(first, shared.database_facts(path, omit={'batches': {'archive_root'}}))
            finally:
                c.close()


if __name__ == '__main__':
    unittest.main()
