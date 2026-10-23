from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from budongi.rental_readiness import rental_readiness


class RentalReadinessTests(unittest.TestCase):
    def _status_fixture(self, root, status='unknown', *, broken=False):
        database = root / 'serving.db'
        metadata = dict.fromkeys(('schema_version','catalog_version','source_schema_version',
            'source_snapshot_date','source_db_sha256','review_manifest_sha256','quality_status','by_kind',
            'coordinates_available','facility_data_available','coverage_available','source_batch_id',
            'snapshot_date','source_dataset_id','unsupported_source_fields'), '')
        metadata.update(schema_version='2', catalog_version='2', source_schema_version='3',
            quality_status='source_unverified', source_batch_id='synthetic-test',
            by_kind=json.dumps({'jeonse': {'observations': 2, 'linked': 1}}))
        connection = sqlite3.connect(database)
        with connection:
            connection.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
            connection.executemany('INSERT INTO metadata VALUES(?,?)', metadata.items())
            connection.execute('CREATE TABLE rental_observations(observation_id TEXT,source_status TEXT)')
            connection.executemany('INSERT INTO rental_observations VALUES(?,?)', [('reviewed',status),('unlinked','unknown')])
            if not broken:
                connection.execute('CREATE TABLE reviewed_relations(observation_id TEXT)')
                connection.execute("INSERT INTO reviewed_relations VALUES('reviewed')")
        connection.close()
        return database

    def test_reviewed_unknown_and_correction_block_without_promoting_links(self):
        for status in ('unknown', 'correction_pending'):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                result = rental_readiness(canonical_db=root/'missing.db', database=self._status_fixture(root, status))
                gate = next(g for g in result['gates'] if g['purpose']=='확정 연결 거래의 취소·정정 상태')
                self.assertEqual(gate['status'], 'needs_input')
                self.assertIn('1건', gate['reason'])
                self.assertFalse(result['real_validation_complete'])

    def test_status_gate_excludes_unlinked_unknown_and_accepts_reviewed_statuses(self):
        for status in ('valid', 'cancelled'):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                result = rental_readiness(canonical_db=root/'missing.db', database=self._status_fixture(root, status))
                gate = next(g for g in result['gates'] if g['purpose']=='확정 연결 거래의 취소·정정 상태')
                self.assertEqual(gate['status'], 'ready')
                self.assertEqual(result['status'], 'blocked')  # source still unavailable

    def test_broken_status_query_does_not_leave_ready_metadata_as_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = rental_readiness(canonical_db=root/'missing.db', database=self._status_fixture(root, broken=True))
            gate = next(g for g in result['gates'] if g['purpose']=='확정 연결 거래의 취소·정정 상태')
            self.assertEqual(gate['status'], 'blocked')
            self.assertIsNone(result['serving'])

    def test_status_count_must_match_confirmed_relation_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = self._status_fixture(root, 'valid')
            connection = sqlite3.connect(database)
            with connection:
                connection.execute('DELETE FROM reviewed_relations')
            connection.close()
            result = rental_readiness(canonical_db=root/'missing.db', database=database)
            gate = next(g for g in result['gates'] if g['purpose']=='확정 연결 거래의 취소·정정 상태')
            self.assertEqual(gate['status'], 'blocked')

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
