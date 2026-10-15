from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from budongi.rental_readiness import rental_readiness


class RentalReadinessTests(unittest.TestCase):
    def test_corrupt_serving_metadata_is_a_blocked_gate_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as temporary:
            database=Path(temporary)/'serving.db'
            keys={'schema_version','catalog_version','source_schema_version','source_snapshot_date',
                  'source_db_sha256','review_manifest_sha256','quality_status','by_kind',
                  'coordinates_available','facility_data_available','coverage_available','source_batch_id',
                  'snapshot_date','source_dataset_id','unsupported_source_fields'}
            values={key:'unavailable' for key in keys}
            values.update(schema_version='2',catalog_version='2',quality_status='source_unverified',by_kind='invalid-json')
            connection=sqlite3.connect(database)
            with connection:
                connection.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
                connection.executemany('INSERT INTO metadata VALUES(?,?)',values.items())
            connection.close()
            result=rental_readiness(canonical_db=Path(temporary)/'missing-source.db',database=database)
            gate=next(g for g in result['gates'] if g['purpose']=='실제 추천·상세 성능 검증')
            self.assertEqual(gate['status'],'blocked')
            self.assertIsNone(result['serving'])

    def test_missing_source_and_serving_do_not_create_files_or_claim_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = rental_readiness(canonical_db=root/'source.db', database=root/'serving.db')
            self.assertEqual(result['status'], 'blocked')
            self.assertFalse(result['real_validation_complete'])
            self.assertEqual(list(root.iterdir()), [])
            self.assertTrue(any(g['status']=='needs_input' for g in result['gates']))

    def test_remote_or_credential_endpoint_never_calls_model(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('no network')):
            for endpoint in ('https://example.com/v1/chat/completions',
                             'http://user:secret@localhost/v1/chat/completions',
                             'http://localhost/v1/chat/completions?token=x', 'http://localhost:bad/v1/chat/completions'):
                result = rental_readiness(canonical_db='missing-source', database='missing-serving', model='local',endpoint=endpoint)
                self.assertEqual(result['gates'][-1]['status'], 'blocked')

    def test_configured_model_is_not_claimed_as_verified(self):
        result = rental_readiness(canonical_db='missing-source', database='missing-serving', model='user-selected-local')
        self.assertEqual(result['gates'][-1]['status'], 'configured')
        self.assertFalse(result['real_validation_complete'])
