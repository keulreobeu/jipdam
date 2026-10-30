"""Public, synthetic tests for the facility preflight API."""
import hashlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from budongi.team_package import validate_package


class TeamPackageTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'raw').mkdir(); (root / 'normalized').mkdir()
        raw = b'name,code\nTest,001\n'
        (root / 'raw/a.csv').write_bytes(raw)
        record = dict(name='Test', facility_type_code='001', entity_level='facility',
                      record_type='facility', source_file_ref='raw/a.csv',
                      source_content_sha256=hashlib.sha256(raw).hexdigest(), source_section='data',
                      source_row_number=1, validation_status='accepted', validation_reason=None)
        normalized = (json.dumps(record) + '\n').encode()
        (root / 'normalized/a.jsonl').write_bytes(normalized)
        def entry(path, data, fmt):
            return dict(path=path, format=fmt, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), section='data', rows=1)
        manifest = dict(delivery_schema_version='team_collection_v1', source_id='s', dataset_id='d', provider='p',
                        documentation_url='https://example.org/', record_url='https://example.org/r', batch_id='b',
                        mapping_version='v', collector='c', approval_ref='a', license_ref='l', license_review_status='pending',
                        scope=dict(regions=None, period=None, filters=None), source_retrieved_at_utc=None,
                        provided_at_utc=None, staged_at_utc=None, quality_status='synthetic_only', requests=[],
                        missing_fields=[], errors=[], source_missing_dates=[], counts=dict(raw=1, accepted=1, excluded=0, rejected=0),
                        files=[entry('raw/a.csv', raw, 'csv'), entry('normalized/a.jsonl', normalized, 'jsonl')])
        (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        return manifest, record

    def test_valid_and_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root)
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            report = validate_package(root)
            self.assertTrue(report['valid'], report)
            self.assertEqual(report, validate_package(root))
            self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_malformed_status_is_unknown_not_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); manifest, record = self.fixture(root)
            record['validation_status'] = []
            data = (json.dumps(record) + '\n').encode()
            (root / 'normalized/a.jsonl').write_bytes(data)
            manifest['files'][1].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            result = validate_package(root)
            self.assertIsNone(result['counts']['rejected'])
            self.assertTrue(any(e['field'] == 'validation_status' and e['reason'] == 'invalid_value' for e in result['errors']))

    def test_missing_file_has_unknown_count(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); manifest, _ = self.fixture(root)
            manifest['files'][0]['path'] = 'raw/missing.csv'
            (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            result = validate_package(root)
            self.assertIsNone(result['counts']['raw'])
            self.assertTrue(any(e['reason'] == 'file_missing' for e in result['errors']))

    def test_credential_url_is_rejected_without_reflection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); manifest, _ = self.fixture(root)
            manifest['record_url'] = 'https://example.org/?access_token=SECRET'
            (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            result = validate_package(root)
            self.assertFalse(result['valid'])
            self.assertNotIn('SECRET', json.dumps(result))

    def test_long_csv_source_row_stays_structured_without_integer_conversion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); manifest, record = self.fixture(root)
            record['source_row_number'] = '9' * 5000
            stream = io.StringIO(newline='')
            writer = csv.DictWriter(stream, fieldnames=list(record))
            writer.writeheader(); writer.writerow(record)
            data = stream.getvalue().encode('utf-8')
            (root / 'normalized/a.csv').write_bytes(data)
            manifest['files'][1].update(path='normalized/a.csv', format='csv', bytes=len(data),
                                        sha256=hashlib.sha256(data).hexdigest())
            (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            report = validate_package(root)
            self.assertIs(type(report['valid']), bool)
            self.assertNotIn(str(root), json.dumps(report))

    def test_refresh_credential_query_is_rejected_without_reflection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); manifest, _ = self.fixture(root)
            manifest['record_url'] = 'https://example.invalid/?refresh_token=synthetic-marker'
            (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            report = validate_package(root)
            self.assertFalse(report['valid'])
            self.assertNotIn('synthetic-marker', json.dumps(report))

    def test_null_additional_path_and_null_zero_row_version_are_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); manifest, _ = self.fixture(root)
            manifest['files'].append(dict(path=None, format='json', bytes=0, sha256='0'*64, section='meta', rows=None))
            (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            self.assertFalse(validate_package(root)['valid'])
            manifest['files'].pop()
            for entry in manifest['files']:
                path = root / entry['path']
                data = b'name,code\n' if entry['format'] == 'csv' else b''
                path.write_bytes(data)
                entry.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), rows=0)
            manifest['counts'] = dict(raw=0, accepted=0, excluded=0, rejected=0)
            (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            self.assertTrue(validate_package(root)['valid'])
            manifest['delivery_schema_version'] = None
            (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            self.assertFalse(validate_package(root)['valid'])

    def test_present_null_schema_is_not_treated_as_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); manifest, _ = self.fixture(root)
            data = b'null'
            (root / 'schema.json').write_bytes(data)
            manifest['files'].append(dict(path='schema.json', format='json', bytes=len(data),
                                         sha256=hashlib.sha256(data).hexdigest(), section='meta', rows=None))
            (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            report = validate_package(root)
            self.assertFalse(report['valid'])
            self.assertTrue(any(e['file'] == 'schema.json' and e['reason'] == 'invalid_type' for e in report['errors']))

    def test_excessively_nested_json_returns_structured_error(self):
        data = ('[' * 10000 + '0' + ']' * 10000).encode()
        for target in ('manifest.json', 'normalized/a.jsonl'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); manifest, _ = self.fixture(root)
                (root / target).write_bytes(data)
                if target != 'manifest.json':
                    manifest['files'][1].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                    (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                report = validate_package(root)
                self.assertFalse(report['valid'])
                self.assertTrue(any(e['file'] == target and e['reason'] == 'invalid_json' for e in report['errors']))


if __name__ == '__main__':
    unittest.main()
