from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from budongi.rental_demo import create_rental_demo
from budongi.rental_recommendation import (RentalDataUnavailable, RentalInputError, execute_rental_tool,
                                          observation_period, open_rental_reader, recommend_rentals,
                                          straight_distance_m, validate_rental_request)
from budongi.rental_storage import connect_rental, import_rental_snapshot, observation_id_for


class RentalRecommendationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'rental.sqlite3'
        self.db = connect_rental(self.path)
        self.addCleanup(self.db.close)

    def request(self, **overrides):
        return {'rental_type': 'wolse', 'max_deposit_krw': 100_000_000,
                'max_monthly_rent_krw': 700_000} | overrides

    def workplace(self):
        return {'latitude': 37.57, 'longitude': 126.98, 'verified': True,
                'source': 'synthetic fixture', 'source_ref': 'fictional workplace'}

    def make_snapshot(self, observations, *, complexes=None, facilities=(), coverage=(), cutoff='2026-10-06',
                      quality='synthetic_only', source_date='2026-10-01'):
        if complexes is None:
            complexes = [{'complex_id': key} for key in sorted({row['complex_id'] for row in observations})]
        raw = json.dumps({'observations': observations, 'complexes': complexes,
                          'facilities': list(facilities), 'coverage': list(coverage)}, sort_keys=True).encode()
        digest = hashlib.sha256(raw).hexdigest()
        (self.root / 'fixture.json').write_bytes(raw)
        total_rows = len(observations) + len(complexes) + len(facilities) + len(coverage)
        manifest = {'datasets': [{'source': 'synthetic_rental_test', 'source_date': source_date,
                    'retrieved_at_utc': cutoff + 'T00:00:00Z', 'files': [{'path': 'fixture.json', 'sha256': digest, 'rows': total_rows}]}]}
        index = 0

        def provenance():
            nonlocal index
            index += 1
            return {'source': 'synthetic_rental_test', 'source_file_ref': 'fixture.json',
                    'source_content_sha256': digest, 'source_row_number': index}

        obs_rows, complex_rows, matches, facility_rows, coverage_rows = [], [], [], [], []
        for item in observations:
            source = provenance()
            key = observation_id_for(**source)
            row = {'observation_id': key, 'apartment_name': 'fictional', 'sgg_cd': '11110',
                   'contract_date': '2026-09-01', 'rental_type': 'wolse', 'deposit_krw': 100_000_000,
                   'monthly_rent_krw': 700_000, 'area_sqm': 59.9, 'raw_payload': item} | item | source
            row.pop('complex_id')
            obs_rows.append(row)
            matches.append({'observation_id': key, 'complex_id': item['complex_id'], 'review_status': 'confirmed',
                            'match_basis': 'synthetic identity', 'evidence': 'fictional fixture identity',
                            'reviewed_by': 'synthetic fixture', 'reviewed_at_utc': cutoff + 'T00:00:00Z'})
        for item in complexes:
            complex_rows.append({'name': 'fictional', 'sgg_cd': '11110', 'latitude': 37.57, 'longitude': 126.98,
                                 'identity_evidence': 'synthetic identity'} | item | provenance())
        for item in facilities:
            source = provenance()
            facility_rows.append({'facility_observation_id': observation_id_for(**source), 'name': 'fictional facility',
                                 'sgg_cd': '11110', 'latitude': 37.57, 'longitude': 126.98} | item | source)
        for item in coverage:
            coverage_rows.append({'sgg_cd': '11110', 'coverage_status': 'complete', 'checked_at_utc': cutoff + 'T00:00:00Z',
                                  'raw_payload': {'coverage_area': {'latitude': 37.57, 'longitude': 126.98, 'radius_m': 10000}}}
                                 | item | provenance())
        import_rental_snapshot(self.db, snapshot_id='fixture', snapshot_date=cutoff, source_manifest=manifest,
                               observations=obs_rows, complexes=complex_rows, facilities=facility_rows,
                               coverage=coverage_rows, matches=matches, quality_status=quality)
        return obs_rows

    def recommend(self, **overrides):
        return recommend_rentals(self.db, snapshot_id='fixture', arguments=self.request(**overrides), allow_synthetic=True)

    def test_latest_contract_budget_pair_and_inclusive_boundaries(self):
        self.make_snapshot([
            {'complex_id': 'A', 'contract_date': '2026-08-01', 'deposit_krw': 1, 'monthly_rent_krw': 1},
            {'complex_id': 'A', 'deposit_krw': 100_000_001, 'monthly_rent_krw': 600_000},
            {'complex_id': 'B', 'contract_date': '2026-08-01', 'deposit_krw': 20_000_000, 'monthly_rent_krw': 800_000},
            {'complex_id': 'B', 'deposit_krw': 110_000_000, 'monthly_rent_krw': 200_000},
            {'complex_id': 'C'}, {'complex_id': 'D', 'monthly_rent_krw': 700_001}])
        result = self.recommend()
        self.assertEqual([row['complex']['id'] for row in result['candidates']], ['C'])
        self.assertEqual(result['candidates'][0]['contract']['deposit_krw'], 100_000_000)
        self.assertEqual(result['candidates'][0]['contract']['monthly_rent_krw'], 700_000)

    def test_filter_before_latest_period_type_area_and_stable_ties(self):
        observations = self.make_snapshot([
            {'complex_id': 'A', 'contract_date': '2025-10-06', 'area_sqm': 60},
            {'complex_id': 'A', 'rental_type': 'jeonse', 'monthly_rent_krw': 0},
            {'complex_id': 'A', 'contract_date': '2026-09-02', 'area_sqm': 85},
            {'complex_id': 'B', 'contract_date': '2025-10-05'},
            {'complex_id': 'C'}, {'complex_id': 'C', 'deposit_krw': 90_000_000}])
        result = self.recommend(area_min_sqm=50, area_max_sqm=60)
        contracts = {row['complex']['id']: row['contract'] for row in result['candidates']}
        self.assertEqual(contracts['A']['contract_date'], '2025-10-06')
        self.assertNotIn('B', contracts)
        self.assertEqual(contracts['C']['observation_id'], max(row['observation_id'] for row in observations[-2:]))
        self.assertEqual(observation_period(date(2024, 2, 29)), ('2023-02-28', '2024-02-29'))
        self.assertEqual(self.recommend(area_min_sqm=50, area_max_sqm=60), result)

    def test_cancelled_contract_is_excluded_and_unknown_status_stays_unknown(self):
        self.make_snapshot([{'complex_id': 'A', 'contract_date': '2026-08-01'},
                            {'complex_id': 'A', 'source_status': 'cancelled'}])
        result = self.recommend()
        self.assertEqual(result['candidates'][0]['contract']['contract_date'], '2026-08-01')
        self.assertIsNone(result['candidates'][0]['contract']['source_status'])

    def test_required_unknown_unmet_exclusion_and_preference_states(self):
        self.make_snapshot([{'complex_id': 'A'}, {'complex_id': 'B'}, {'complex_id': 'C'}],
                           complexes=[{'complex_id': 'A'}, {'complex_id': 'B', 'latitude': 37.60},
                                      {'complex_id': 'C', 'latitude': None, 'longitude': None}],
                           facilities=[{'category': 'station'}, {'category': 'park'}],
                           coverage=[{'category': 'station'}, {'category': 'park', 'coverage_status': 'partial'},
                                     {'category': 'hospital'}])
        result = self.recommend(workplace=self.workplace(), conditions=[
            {'kind': 'workplace', 'max_distance_m': 500, 'required': True},
            {'kind': 'station', 'max_distance_m': 500, 'required': True},
            {'kind': 'park', 'max_distance_m': 500, 'required': False},
            {'kind': 'hospital', 'max_distance_m': 500, 'required': False},
            {'kind': 'school', 'max_distance_m': 500, 'required': False}])
        self.assertEqual(result['row_count'], 1)
        row = result['candidates'][0]
        self.assertEqual(row['complex']['id'], 'A')
        self.assertEqual(row['unknown_preferences'], ['park', 'school'])
        self.assertEqual(row['unmet_preferences'], ['hospital'])
        self.assertEqual(row['preference_met_count'], 0)
        self.assertTrue(all(check['distance_type'] == 'straight_line' for check in row['conditions']))

    def test_radius_boundary_and_coverage_extent_are_not_assumed(self):
        target = (37.571, 126.98)
        boundary = straight_distance_m((37.57, 126.98), target)
        self.make_snapshot([{'complex_id': 'A'}], facilities=[{'category': 'station', 'latitude': target[0]}],
                           coverage=[{'category': 'station'}])
        condition = {'kind': 'station', 'max_distance_m': boundary, 'required': True}
        self.assertEqual(self.recommend(conditions=[condition])['row_count'], 1)
        condition['max_distance_m'] -= 0.001
        self.assertEqual(self.recommend(conditions=[condition])['row_count'], 0)
        condition['max_distance_m'] = 10001
        condition['required'] = False
        self.assertEqual(self.recommend(conditions=[condition])['candidates'][0]['conditions'][0]['status'], 'unknown')

    def test_missing_source_basis_date_never_becomes_facility_met(self):
        self.make_snapshot([{'complex_id': 'A'}], facilities=[{'category': 'station'}],
                           coverage=[{'category': 'station'}], source_date=None)
        result = self.recommend(conditions=[{'kind': 'station', 'max_distance_m': 500, 'required': False}])
        self.assertEqual(result['candidates'][0]['conditions'][0]['status'], 'unknown')

    def test_stale_facility_basis_date_is_unknown(self):
        self.make_snapshot([{'complex_id': 'A'}], facilities=[{'category': 'station'}],
                           coverage=[{'category': 'station'}], source_date='2025-10-05')
        self.assertEqual(self.recommend(conditions=[{'kind': 'station', 'max_distance_m': 500, 'required': False}])
                         ['candidates'][0]['conditions'][0]['status'], 'unknown')

    def test_future_contract_is_rejected_before_snapshot_can_be_used(self):
        with self.assertRaises(ValueError):
            self.make_snapshot([{'complex_id': 'A', 'contract_date': '2026-10-07'}])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM rental_snapshots').fetchone()[0], 0)

    def test_unreviewed_correction_status_is_not_silently_applied(self):
        self.make_snapshot([{'complex_id': 'A', 'source_status': 'corrected'}])
        with self.assertRaises(RentalDataUnavailable):
            self.recommend()

    def test_rank_preference_then_workplace_then_date_then_id_and_unknown_distance(self):
        self.make_snapshot([{'complex_id': key, 'contract_date': day} for key, day in
                            [('A', '2026-09-02'), ('B', '2026-09-02'), ('C', '2026-09-01'), ('D', '2026-09-02'),
                             ('E', '2026-09-02'), ('F', '2026-09-03')]],
                           complexes=[{'complex_id': 'A', 'latitude': 37.572}, {'complex_id': 'B', 'latitude': 37.58},
                                      {'complex_id': 'C'}, {'complex_id': 'D'}, {'complex_id': 'E'},
                                      {'complex_id': 'F', 'latitude': None, 'longitude': None}],
                           facilities=[{'category': 'station'}], coverage=[{'category': 'station'}])
        result = self.recommend(workplace=self.workplace(), limit=20,
                                conditions=[{'kind': 'station', 'max_distance_m': 500, 'required': False}])
        self.assertEqual([row['complex']['id'] for row in result['candidates']], ['D', 'E', 'C', 'A', 'B', 'F'])
        self.assertEqual(result, self.recommend(workplace=self.workplace(), limit=20,
                         conditions=[{'kind': 'station', 'max_distance_m': 500, 'required': False}]))

    def test_seoul_scope_default_limit_partial_and_no_match(self):
        self.make_snapshot([{'complex_id': f'{i:02d}'} for i in range(23)],
                           complexes=[{'complex_id': f'{i:02d}', 'sgg_cd': '11110' if i < 22 else '28110'} for i in range(23)])
        self.assertEqual(self.recommend()['row_count'], 5)
        self.assertEqual(self.recommend(limit=20)['row_count'], 20)
        self.assertEqual(self.recommend()['eligible_count'], 22)
        empty = self.recommend(max_deposit_krw=0)
        self.assertEqual((empty['status'], empty['row_count']), ('no_match', 0))
        self.assertIn('management_fee', empty['excluded_costs'])

    def test_empty_snapshot_and_unverified_data_are_distinct(self):
        self.make_snapshot([])
        self.assertEqual(self.recommend()['status'], 'no_match')
        with self.assertRaises(RentalDataUnavailable):
            recommend_rentals(self.db, snapshot_id='fixture', arguments=self.request())
        with self.assertRaises(RentalDataUnavailable):
            recommend_rentals(self.db, snapshot_id='missing', arguments=self.request(), allow_synthetic=True)
        with self.assertRaises(RentalDataUnavailable):
            open_rental_reader(self.root / 'missing.sqlite3')
        self.assertFalse((self.root / 'missing.sqlite3').exists())

    def test_source_unverified_snapshot_is_not_enabled_by_demo_flag(self):
        self.make_snapshot([{'complex_id': 'A'}], quality='source_unverified')
        with self.assertRaises(RentalDataUnavailable):
            self.recommend()

    def test_input_validation_rejects_wrong_types_unresolved_workplace_and_duplicate_conditions(self):
        condition = {'kind': 'station', 'max_distance_m': 500, 'required': True}
        invalid = [{'max_deposit_krw': True}, {'max_monthly_rent_krw': -1}, {'limit': 21}, {'limit': True},
                   {'area_min_sqm': float('nan')}, {'area_max_sqm': float('inf')},
                   {'area_min_sqm': 70, 'area_max_sqm': 60}, {'districts': ['부산']},
                   {'conditions': [condition, condition]}, {'conditions': [condition | {'kind': 'school'}]},
                   {'workplace': self.workplace() | {'verified': False}},
                   {'workplace': self.workplace() | {'latitude': 91}},
                   {'workplace': {'place_id': 'unresolved', 'verified': True}},
                   {'conditions': [condition | {'kind': 'workplace'}]}, {'api_key': 'must-not-be-accepted'},
                   {'rental_type': 'jeonse', 'max_monthly_rent_krw': 1}]
        for overrides in invalid:
            with self.subTest(fields=list(overrides)), self.assertRaises(RentalInputError):
                validate_rental_request(self.request(**overrides))
        with self.assertRaises(RentalInputError):
            validate_rental_request({'rental_type': 'wolse', 'max_deposit_krw': 1})

    def test_readonly_tool_cli_parity_errors_and_source_evidence(self):
        demo = create_rental_demo(self.root / 'demo')
        arguments = json.loads(Path(demo['request_file']).read_text(encoding='utf-8'))
        reader = open_rental_reader(Path(demo['rental_db']))
        self.addCleanup(reader.close)
        result = execute_rental_tool(reader, snapshot_id=demo['snapshot_id'], tool='recommend_rentals',
                                     arguments=arguments, allow_synthetic=True)
        self.assertEqual(result['row_count'], 2)
        with self.assertRaises(sqlite3.OperationalError):
            reader.execute('CREATE TABLE forbidden (id INTEGER)')
        with self.assertRaises(RentalInputError):
            execute_rental_tool(reader, snapshot_id=demo['snapshot_id'], tool='sql', arguments={})
        command = [sys.executable, '-X', 'utf8', '-m', 'budongi.cli', 'recommend', '--rental-db', demo['rental_db'],
                   '--snapshot-id', demo['snapshot_id'], '--request', demo['request_file']]
        completed = subprocess.run(command + ['--allow-synthetic'], capture_output=True, encoding='utf-8', check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), result)
        row = result['candidates'][0]
        self.assertEqual(row['source']['source_record_id'], None)
        self.assertEqual(len(row['source']['source_content_sha256']), 64)
        self.assertIsNotNone(row['complex']['source']['source_file_ref'])
        completed = subprocess.run(command, capture_output=True, encoding='utf-8', check=False)
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(json.loads(completed.stdout)['status'], 'data_unavailable')
        request_path = Path(demo['request_file'])
        request_path.write_text('{"rental_type":"wolse","max_deposit_krw":true}', encoding='utf-8')
        completed = subprocess.run(command + ['--allow-synthetic'], capture_output=True, encoding='utf-8', check=False)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)['status'], 'input_error')
        request_path.write_text(json.dumps(arguments), encoding='utf-8')
        Path(demo['rental_db']).write_bytes(b'not a SQLite database')
        completed = subprocess.run(command + ['--allow-synthetic'], capture_output=True, encoding='utf-8', check=False)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(json.loads(completed.stdout)['status'], 'internal_error')


if __name__ == '__main__':
    unittest.main()
