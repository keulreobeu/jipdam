from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
import tempfile
import json
import threading
import unittest
from types import SimpleNamespace
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch
from budongi.rental_review import file_sha256
from budongi.rental_recommendation import RentalDataUnavailable, straight_distance_m

from budongi.canonical_rental import (
    canonical_complex_detail,
    canonical_rental_status,
    open_rental_serving_reader,
    prepare_canonical_rental_serving,
    recommend_canonical_rentals,
)
from budongi.rental_server import _RentalRequestHandler, create_rental_server


class CanonicalRentalServingTests(unittest.TestCase):
    @contextmanager
    def _writer(self, path):
        connection = sqlite3.connect(path)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _review(self, source, root, *, coordinates=False):
        package = root / 'review'
        package.mkdir(exist_ok=True)
        evidence = package / 'evidence.json'
        evidence.write_text('[{"kind":"synthetic fixture, never real approval"}]', encoding='utf-8')
        common = {'review_status': 'confirmed', 'evidence': 'fictional test review', 'reviewed_by': 'test-reviewer',
                  'reviewed_at_utc': '2026-10-12T00:00:00Z', 'source_id': 'synthetic-test',
                  'source_date': '2026-10-12', 'source_file_ref': 'evidence.json',
                  'source_content_sha256': file_sha256(evidence), 'source_row_number': 1}
        relations = [{**common, 'observation_id': key, 'complex_id': 'complex-a', 'source_status': 'valid'}
                     for key in ('obs-old', 'obs-new')]
        records = {'relations': relations, 'coordinates': [{**common, 'complex_id': 'complex-a',
                   'latitude': 37.5665, 'longitude': 126.978, 'crs': 'EPSG:4326', 'method': 'synthetic'}] if coordinates else [],
                   'facilities': [], 'coverage': []}
        (package / 'records.json').write_text(json.dumps(records), encoding='utf-8')
        self._write_manifest(source, package)
        return package

    def _write_manifest(self, source, package):
        manifest = {'schema_version': 'rental_review_v1', 'source_db_sha256': file_sha256(source),
                    'quality_status': 'synthetic_only', 'approval_ref': 'test fixture only',
                    'approved_by': 'test-reviewer', 'approved_at_utc': '2026-10-12T00:00:00Z',
                    'records_file': 'records.json', 'files': [
                        {'path': name, 'sha256': file_sha256(package / name)} for name in ('records.json', 'evidence.json')]}
        (package / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')

    def _records(self, package):
        return json.loads((package / 'records.json').read_text(encoding='utf-8'))

    def _save_records(self, source, package, records):
        (package / 'records.json').write_text(json.dumps(records), encoding='utf-8')
        self._write_manifest(source, package)

    def _facilities(self, records, *, complete=True):
        common = records['relations'][0]
        records['facilities'] = [{**common, 'facility_id': 'park-a', 'category': 'park', 'name': '합성 공원',
            'latitude': 37.5665, 'longitude': 126.979, 'crs': 'EPSG:4326', 'method': 'synthetic'}]
        records['coverage'] = [{**common, 'category': 'park', 'sgg_cd': '11110',
            'coverage_status': 'complete' if complete else 'partial', 'checked_at_utc': '2026-10-12T00:00:00Z',
            'coverage_area': {'latitude': 37.5665, 'longitude': 126.978, 'radius_m': 10000}}]

    def _request(self, **extra):
        return {'rental_type': 'wolse', 'max_deposit_krw': 500_000_000,
                'max_monthly_rent_krw': 1_000_000, **extra}

    def test_raw_complex_id_and_verified_boolean_do_not_grant_eligibility(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source, linked=True, coordinates_verified=1)
            before = file_sha256(source)
            prepare_canonical_rental_serving(source, target)
            with closing(open_rental_serving_reader(target)) as db:
                self.assertEqual(canonical_rental_status(db)['confirmed_complex_observations'], 0)
                self.assertEqual(recommend_canonical_rentals(db, self._request())['status'], 'data_not_ready')
            self.assertEqual(before, file_sha256(source))

    def test_same_input_output_and_invalid_package_leave_original_and_serving_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source, linked=True)
            before = file_sha256(source)
            with self.assertRaises(RentalDataUnavailable):
                prepare_canonical_rental_serving(source, source)
            prepare_canonical_rental_serving(source, target)
            serving_hash = file_sha256(target)
            package = self._review(source, Path(folder))
            (package/'evidence.json').write_text('tampered', encoding='utf-8')
            with self.assertRaises(RentalDataUnavailable):
                prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            self.assertEqual(before, file_sha256(source))
            self.assertEqual(serving_hash, file_sha256(target))

    def test_pending_rejected_links_and_synthetic_opt_in(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source, linked=True)
            package = self._review(source, Path(folder))
            with self.assertRaises(RentalDataUnavailable):
                prepare_canonical_rental_serving(source, target, review_package=package)
            records = self._records(package)
            records['relations'][0]['review_status'] = 'pending'
            records['relations'][1]['review_status'] = 'rejected'
            self._save_records(source, package, records)
            prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            with self.assertRaises(RentalDataUnavailable):
                open_rental_serving_reader(target)
            with closing(open_rental_serving_reader(target, allow_synthetic=True)) as db:
                self.assertEqual(canonical_rental_status(db)['confirmed_complex_observations'], 0)

    def test_package_missing_lineage_review_and_invalid_coordinate_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source, linked=False)
            package = self._review(source, Path(folder), coordinates=True)
            original = self._records(package)
            for kind, key, value in [('relations','reviewed_by',''), ('relations','source_content_sha256','f'*64),
                                     ('relations','complex_id','missing'), ('coordinates','latitude',91),
                                     ('coordinates','method',''), ('coordinates','crs','EPSG:5179')]:
                records = json.loads(json.dumps(original)); records[kind][0][key] = value
                self._save_records(source, package, records)
                with self.subTest(kind=kind, key=key), self.assertRaises(RentalDataUnavailable):
                    prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)

    def test_latest_ties_cancelled_and_unreviewed_correction(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source, linked=False)
            with self._writer(source) as db:
                db.execute("UPDATE observations SET contract_date='2026-09-01' WHERE observation_id='obs-old'")
            package = self._review(source, Path(folder))
            prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            with closing(open_rental_serving_reader(target, allow_synthetic=True)) as db:
                self.assertEqual(recommend_canonical_rentals(db, self._request())['results'][0]['observation_id'], 'obs-old')
            records = self._records(package); records['relations'][0]['source_status'] = 'cancelled'
            self._save_records(source, package, records)
            prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            with closing(open_rental_serving_reader(target, allow_synthetic=True)) as db:
                self.assertEqual(recommend_canonical_rentals(db, self._request())['results'][0]['observation_id'], 'obs-new')
            records['relations'][0]['source_status'] = 'correction_pending'; self._save_records(source, package, records)
            prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            with closing(open_rental_serving_reader(target, allow_synthetic=True)) as db:
                self.assertEqual(recommend_canonical_rentals(db, self._request())['status'], 'data_not_ready')

    def test_rtree_exact_radius_and_required_preferred_unknown_states(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source, linked=False)
            package = self._review(source, Path(folder), coordinates=True)
            records = self._records(package); self._facilities(records); self._save_records(source, package, records)
            prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            distance = straight_distance_m((37.5665,126.978),(37.5665,126.979))
            with closing(open_rental_serving_reader(target, allow_synthetic=True)) as db:
                result = recommend_canonical_rentals(db, self._request(conditions=[{'kind':'park','max_distance_m':distance,'required':True}]))
                self.assertEqual(result['status'], 'ok')
                self.assertEqual(result['results'][0]['conditions'][0]['status'], 'met')
                result = recommend_canonical_rentals(db, self._request(conditions=[{'kind':'park','max_distance_m':distance-0.01,'required':True}]))
                self.assertEqual(result['status'], 'no_match')
                preferred = recommend_canonical_rentals(db, self._request(conditions=[{'kind':'hospital','max_distance_m':1000,'required':False}]))
                self.assertEqual(preferred['status'], 'ok')
                self.assertEqual(preferred['results'][0]['conditions'][0]['status'], 'unknown')
                required = recommend_canonical_rentals(db, self._request(conditions=[{'kind':'hospital','max_distance_m':1000,'required':True}]))
                self.assertEqual(required['status'], 'data_not_ready')
            records['coverage'][0]['coverage_status'] = 'partial'; self._save_records(source, package, records)
            prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            with closing(open_rental_serving_reader(target, allow_synthetic=True)) as db:
                self.assertEqual(recommend_canonical_rentals(db, self._request(conditions=[{'kind':'park','max_distance_m':100,'required':True}]))['status'], 'data_not_ready')

    def test_final_conditions_are_evaluated_before_limit_and_rank_is_deterministic(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source, linked=False)
            with self._writer(source) as db:
                for index in range(30):
                    cid, oid = f'complex-{index:02}', f'obs-{index:02}'
                    db.execute('INSERT INTO complexes SELECT ?,sgg_cd,identifier_namespace,?,identity_basis,NULL,NULL,0 FROM complexes WHERE complex_id=?', (cid,cid,'complex-a'))
                    db.execute('INSERT INTO observations SELECT ?,NULL,sgg_cd,contract_date,apartment_name,legal_dong,jibun,kind,area_sqm,deposit_krw,monthly_rent_krw,floor,build_year,source_record_id,source_effective_from,source_effective_to,mapping_version,source_id,dataset_id,raw_item_id FROM observations WHERE observation_id=?',(oid,'obs-new'))
                    db.execute("INSERT INTO batch_observations VALUES ('batch-a',?)",(oid,))
                db.execute("UPDATE observations SET contract_date='2026-08-01' WHERE observation_id='obs-29'")
            package = self._review(source, Path(folder), coordinates=True); records = self._records(package)
            common = records['relations'][0]
            records['relations'].extend({**common,'observation_id':f'obs-{index:02}','complex_id':f'complex-{index:02}'} for index in range(30))
            records['coordinates'].append({**records['coordinates'][0], 'complex_id':'complex-29'})
            self._facilities(records); self._save_records(source, package, records)
            prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            request = self._request(limit=1, conditions=[{'kind':'park','max_distance_m':1000,'required':True}])
            with closing(open_rental_serving_reader(target, allow_synthetic=True)) as db:
                first = recommend_canonical_rentals(db, request)
                self.assertEqual(first['results'][0]['complex_id'], 'complex-a')
                self.assertEqual(first, recommend_canonical_rentals(db, request))
                request['limit'] = 5
                two = recommend_canonical_rentals(db,request)
                self.assertEqual(two['count'],2)
                self.assertEqual(two['eligible_count'],2)
                request['limit'] = 1
                request['conditions'][0]['required'] = False
                self.assertEqual(recommend_canonical_rentals(db, request)['results'][0]['complex_id'], 'complex-a')

    def test_catalog_version_errors_and_detail_empty_page_is_not_unknown_id(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source, linked=False)
            package = self._review(source, Path(folder))
            prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            with closing(open_rental_serving_reader(target, allow_synthetic=True)) as db:
                detail = canonical_complex_detail(db, 'complex-a', offset=100)
                self.assertEqual(detail['status'], 'ok'); self.assertEqual(detail['observations'], [])
                self.assertEqual(detail['previous_offset'], 0)
                self.assertIn('raw_item_id', detail['unsupported_fields'])
                self.assertTrue(all({'key','type','unit','section','source','validity'} <= set(field) for field in detail['fields']))
                self.assertEqual(canonical_complex_detail(db, 'does-not-exist')['status'], 'not_found')
            with self._writer(target) as db:
                db.execute("UPDATE metadata SET value='999' WHERE key='schema_version'")
            with self.assertRaises(RentalDataUnavailable): open_rental_serving_reader(target, allow_synthetic=True)

    def test_source_versions_and_sealed_report_mismatch_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source,linked=False)
            with self._writer(source) as db: db.execute('PRAGMA user_version=99')
            with self.assertRaises(RentalDataUnavailable): prepare_canonical_rental_serving(source,target)
            with self._writer(source) as db: db.execute('PRAGMA user_version=2')
            prepare_canonical_rental_serving(source,target)
            with closing(open_rental_serving_reader(target)) as db:
                self.assertEqual(canonical_rental_status(db)['source_schema_version'],2)
            (Path(folder)/'quality-report.json').write_text(json.dumps({'schema_version':'canonical_real_estate_v2',
                            'files':{'source.db':'f'*64}}),encoding='utf-8')
            with self.assertRaises(RentalDataUnavailable): prepare_canonical_rental_serving(source,target)

    def test_nearest_unmet_distance_and_stale_data_do_not_reuse_old_spatial_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source,linked=False)
            package = self._review(source,Path(folder),coordinates=True)
            records = self._records(package); self._facilities(records); self._save_records(source,package,records)
            prepare_canonical_rental_serving(source,target,review_package=package,allow_synthetic=True)
            request = self._request(conditions=[{'kind':'park','max_distance_m':10,'required':False}])
            with closing(open_rental_serving_reader(target,allow_synthetic=True)) as db:
                check = recommend_canonical_rentals(db,request)['results'][0]['conditions'][0]
                self.assertEqual(check['status'],'unmet'); self.assertGreater(check['distance_m'],10)
                self.assertEqual(check['facility']['id'],'park-a')
            records['facilities'][0]['source_date']='2025-01-01'; self._save_records(source,package,records)
            prepare_canonical_rental_serving(source,target,review_package=package,allow_synthetic=True)
            request['conditions'][0]['max_distance_m']=1000
            with closing(open_rental_serving_reader(target,allow_synthetic=True)) as db:
                self.assertEqual(recommend_canonical_rentals(db,request)['results'][0]['conditions'][0]['status'],'unknown')

    def test_new_review_dataset_cutoff_preserves_original_transaction_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.db', Path(folder)/'serving.db'
            self._source(source,linked=False)
            package = self._review(source,Path(folder),coordinates=True)
            records = self._records(package); self._facilities(records)
            for key in ('facilities','coverage'):
                records[key][0]['source_date']='2026-10-14'
                records[key][0]['reviewed_at_utc']='2026-10-14T00:00:00Z'
            records['coverage'][0]['checked_at_utc']='2026-10-14T00:00:00Z'
            self._save_records(source,package,records)
            manifest = json.loads((package/'manifest.json').read_text(encoding='utf-8'))
            manifest.update(snapshot_date='2026-10-14',approved_at_utc='2026-10-14T00:00:00Z')
            (package/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            prepare_canonical_rental_serving(source,target,review_package=package,allow_synthetic=True)
            with closing(open_rental_serving_reader(target,allow_synthetic=True)) as db:
                result = recommend_canonical_rentals(db,self._request(conditions=[{'kind':'park','max_distance_m':1000,'required':True}]))
                self.assertEqual(result['status'],'ok')
                self.assertEqual(result['snapshot_date'],'2026-10-14')
                self.assertEqual(result['source_snapshot_date'],'2026-10-12')
                self.assertEqual(result['results'][0]['provenance']['snapshot_date'],'2026-10-12')
            manifest['snapshot_date']='2026-10-15'
            (package/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            with self.assertRaises(RentalDataUnavailable):
                prepare_canonical_rental_serving(source,target,review_package=package,allow_synthetic=True)

    def _source(self, path: Path, *, linked: bool, coordinates_verified: int = 0) -> None:
        connection = sqlite3.connect(path)
        connection.executescript(
            """PRAGMA user_version=3;
               CREATE TABLE batches(batch_id TEXT PRIMARY KEY,snapshot_date TEXT,complete INTEGER);
               CREATE TABLE batch_observations(batch_id TEXT,observation_id TEXT,
                   PRIMARY KEY(batch_id,observation_id));
               CREATE TABLE sources(source_id TEXT PRIMARY KEY,dataset_id TEXT);
               CREATE TABLE raw_items(raw_item_id TEXT PRIMARY KEY,file_id TEXT,row_number INTEGER);
               CREATE TABLE raw_files(file_id TEXT PRIMARY KEY,file_ref TEXT,sha256 TEXT);
               CREATE TABLE complexes(complex_id TEXT PRIMARY KEY,sgg_cd TEXT,
                   identifier_namespace TEXT,source_complex_id TEXT,identity_basis TEXT,
                   latitude REAL,longitude REAL,coordinates_verified INTEGER);
               CREATE TABLE observations(
                   observation_id TEXT PRIMARY KEY,complex_id TEXT,sgg_cd TEXT,contract_date TEXT,
                   apartment_name TEXT,legal_dong TEXT,jibun TEXT,kind TEXT,area_sqm REAL,
                   deposit_krw INTEGER,monthly_rent_krw INTEGER,floor INTEGER,build_year INTEGER,
                   source_record_id TEXT,source_effective_from TEXT,source_effective_to TEXT,
                   mapping_version TEXT,source_id TEXT,dataset_id TEXT,raw_item_id TEXT);
               CREATE TABLE match_candidates(review_status TEXT CHECK(review_status='pending'));
               """
        )
        connection.execute("INSERT INTO batches VALUES ('batch-a','2026-10-12',1)")
        connection.execute("INSERT INTO sources VALUES ('molit_apt_rent','15126474')")
        connection.execute("INSERT INTO raw_files VALUES (?,?,?)", ("file-a", "2026/10/page.xml", "a" * 64))
        connection.execute("INSERT INTO complexes VALUES ('complex-a','11110','molit','official-a','official_id',37.5665,126.9780,?)",
                           (coordinates_verified,))
        rows = [
            ("obs-old", "complex-a" if linked else None, "2026-02-01", 200_000_000, 600_000),
            ("obs-new", "complex-a" if linked else None, "2026-09-01", 350_000_000, 850_000),
        ]
        for index, (observation_id, complex_id, contract_date, deposit, rent) in enumerate(rows, 1):
            raw_id = f"raw-{index}"
            connection.execute("INSERT INTO raw_items VALUES (?,?,?)", (raw_id, "file-a", index))
            connection.execute(
                "INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (observation_id, complex_id, "11110", contract_date, "검수 단지", "청운동", "1-1",
                 "wolse", 59.5, deposit, rent, 5, 2015, None, None, None,
                 "mapping-v1", "molit_apt_rent",
                 "15126474", raw_id),
            )
            connection.execute("INSERT INTO batch_observations VALUES ('batch-a',?)", (observation_id,))
        connection.commit()
        connection.close()

    def test_unlinked_observations_are_not_recommended_and_database_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as folder:
            source = Path(folder) / "source.sqlite3"
            target = Path(folder) / "serving.sqlite3"
            self._source(source, linked=False)
            result = prepare_canonical_rental_serving(source, target)
            self.assertEqual(result["observations"], 2)
            connection = open_rental_serving_reader(target)
            try:
                status = canonical_rental_status(connection)
                self.assertEqual(status["status"], "data_not_ready")
                self.assertEqual(status["observations"], 2)
                self.assertEqual(status["confirmed_complex_observations"], 0)
                response = recommend_canonical_rentals(connection, {
                    "rental_type": "wolse", "max_deposit_krw": 500_000_000,
                    "max_monthly_rent_krw": 1_000_000,
                })
                self.assertEqual(response["status"], "data_not_ready")
                self.assertEqual(response["results"], [])
                with self.assertRaises(sqlite3.OperationalError):
                    connection.execute("DELETE FROM rental_observations")
            finally:
                connection.close()

    def test_only_confirmed_official_links_use_latest_contract_and_keep_provenance(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as folder:
            source = Path(folder) / "source.sqlite3"
            target = Path(folder) / "serving.sqlite3"
            self._source(source, linked=True)
            package = self._review(source, Path(folder))
            prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            connection = open_rental_serving_reader(target, allow_synthetic=True)
            try:
                result = recommend_canonical_rentals(connection, {
                    "rental_type": "wolse", "max_deposit_krw": 400_000_000,
                    "max_monthly_rent_krw": 900_000,
                })
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["count"], 1)
                candidate = result["results"][0]
                self.assertEqual(candidate["observation_id"], "obs-new")
                self.assertEqual(candidate["deposit_krw"], 350_000_000)
                self.assertEqual(candidate["provenance"]["source_file_ref"], "2026/10/page.xml")
                # Budget is applied after selecting the latest transaction; do not fall back to an older cheaper row.
                older_budget = recommend_canonical_rentals(connection, {
                    "rental_type": "wolse", "max_deposit_krw": 300_000_000,
                    "max_monthly_rent_krw": 1_000_000,
                })
                self.assertEqual(older_budget["status"], "no_match")
                self.assertEqual(older_budget["results"], [])
                detail = canonical_complex_detail(connection, "complex-a")
                self.assertEqual(detail["status"], "ok")
                self.assertEqual(len(detail["observations"]), 2)
                self.assertIsNone(detail["complex"]["coordinates"])
            finally:
                connection.close()

    def test_loopback_api_status_chat_and_csrf(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as folder:
            source = Path(folder) / "source.sqlite3"
            target = Path(folder) / "serving.sqlite3"
            self._source(source, linked=False)
            prepare_canonical_rental_serving(source, target)
            server = create_rental_server(port=0, database=target, model=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(server.origin + "/api/status", timeout=3) as response:
                    status = json.loads(response.read().decode("utf-8"))
                self.assertEqual(status["status"], "data_not_ready")

                body = json.dumps({"message": "종로구 월세를 찾고 있어요."}).encode("utf-8")
                request = Request(server.origin + "/api/chat", data=body, headers={
                    "Content-Type": "application/json", "Origin": server.origin,
                    "X-Jipdam-CSRF": server.csrf_token,
                })
                with urlopen(request, timeout=3) as response:
                    chat = json.loads(response.read().decode("utf-8"))
                self.assertEqual(chat["mode"], "guided_fallback")
                self.assertEqual(chat["storage"], "memory_only")

                bad = Request(server.origin + "/api/chat", data=body, headers={
                    "Content-Type": "application/json", "Origin": server.origin,
                })
                with self.assertRaises(HTTPError) as raised:
                    urlopen(bad, timeout=3)
                self.assertEqual(getattr(raised.exception, "code", None), 403)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_only_explicitly_verified_wgs84_coordinates_reach_the_map(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as folder:
            source = Path(folder) / "source.sqlite3"
            target = Path(folder) / "serving.sqlite3"
            self._source(source, linked=True, coordinates_verified=1)
            package = self._review(source, Path(folder), coordinates=True)
            prepare_canonical_rental_serving(source, target, review_package=package, allow_synthetic=True)
            connection = open_rental_serving_reader(target, allow_synthetic=True)
            try:
                detail = canonical_complex_detail(connection, "complex-a")
                self.assertEqual(detail['complex']['coordinates']['latitude'], 37.5665)
                self.assertEqual(detail['complex']['coordinates']['review']['method'], 'synthetic')
            finally:
                connection.close()

    def test_model_draft_is_allowlisted_and_rejects_invalid_values(self) -> None:
        draft = _RentalRequestHandler._safe_draft({
            "rental_type": "wolse", "max_deposit_krw": True,
            "max_monthly_rent_krw": 1_000_000, "districts": ["종로구", "not-a-district"],
            "area_min_sqm": float("nan"), "area_max_sqm": 59.5,
            "conditions": [{"kind": "park", "max_distance_m": 700, "required": True},
                           {"kind": "unknown", "max_distance_m": 500, "required": False}],
            "workplace": {"latitude": 37.5}, "sql": "SELECT * FROM observations",
        })
        self.assertEqual(draft, {
            "rental_type": "wolse", "max_monthly_rent_krw": 1_000_000,
            "area_max_sqm": 59.5, "districts": ["11110"],
            "conditions": [{"kind": "park", "max_distance_m": 700.0, "required": True}],
        })

    def test_local_model_structured_reply_returns_a_confirmable_draft(self) -> None:
        payload = {"choices": [{"message": {"content": json.dumps({
            "reply": "월세 상한이 100만 원이 맞을까요?",
            "draft": {"rental_type": "wolse", "max_monthly_rent_krw": 1_000_000,
                      "districts": ["종로구"]},
        }, ensure_ascii=False)}}]}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self, _limit):
                return json.dumps(payload, ensure_ascii=False).encode("utf-8")

        handler = object.__new__(_RentalRequestHandler)
        handler.server = SimpleNamespace(
            model="local-test", endpoint="http://127.0.0.1:11434/v1/chat/completions")
        with patch("budongi.rental_server._model_request", return_value=Response()):
            reply, draft = handler._followup([{"role": "user", "content": "종로구 월세요."}], {})
        self.assertEqual(reply, "월세 상한이 100만 원이 맞을까요?")
        self.assertEqual(draft, {"rental_type": "wolse", "max_monthly_rent_krw": 1_000_000,
                                 "districts": ["11110"]})

    def test_chat_confirmation_removal_manual_draft_failure_reset_and_expiry(self):
        with tempfile.TemporaryDirectory() as folder:
            server = create_rental_server(port=0, database=Path(folder)/'missing.db', model='local-test')
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            def send(body):
                request = Request(server.origin+'/api/chat', data=json.dumps(body).encode(), headers={
                    'Content-Type':'application/json','Origin':server.origin,'X-Jipdam-CSRF':server.csrf_token})
                with urlopen(request,timeout=3) as response: return json.loads(response.read())
            try:
                with patch('budongi.rental_server.recommend_canonical_rentals', side_effect=AssertionError('no search before confirmation')):
                    with patch.object(_RentalRequestHandler, '_followup', return_value=('전세로 변경할까요?', {'rental_type':'jeonse','conditions':[]})):
                        first = send({'message':'전세로 바꿔 주세요','draft':self._request(area_min_sqm=50, conditions=[{'kind':'park','max_distance_m':1000,'required':False}])})
                    self.assertEqual(first['draft']['max_monthly_rent_krw'],0)
                    self.assertEqual(first['draft']['conditions'],[])
                    with patch.object(_RentalRequestHandler,'_followup', return_value=('면적 조건은 제거할까요?', {'area_min_sqm':None})) as model:
                        amended = send({'session_id':first['session_id'],'message':'면적을 제거하고 예산은 4억으로','draft':self._request(max_deposit_krw=400_000_000)})
                        self.assertEqual(model.call_args.args[1]['max_deposit_krw'],400_000_000)
                    self.assertEqual(amended['draft_patch'],{'area_min_sqm':None})
                    with patch.object(_RentalRequestHandler,'_followup',side_effect=OSError('timeout')):
                        fallback = send({'session_id':first['session_id'],'message':'다시 확인해 주세요'})
                    self.assertEqual(fallback['mode'],'guided_fallback')
                    self.assertEqual(fallback['draft']['max_deposit_krw'],400_000_000)
                    self.assertEqual(fallback['draft_patch'],{})
                    server.sessions[first['session_id']]['updated'] = 0
                    with self.assertRaises(HTTPError) as raised: send({'session_id':first['session_id'],'message':'만료'})
                    self.assertEqual(raised.exception.code,400)
                    with patch.object(_RentalRequestHandler,'_followup',return_value=('예산은 얼마인가요?',{})):
                        fresh = send({'message':'새 대화'})
                    send({'session_id':fresh['session_id'],'reset':True})
                    self.assertNotIn(fresh['session_id'],server.sessions)
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=3)

    def test_malformed_model_json_and_remote_redirect_never_become_conditions(self):
        from budongi.rental_server import _NoModelRedirect
        from urllib.error import URLError
        handler = object.__new__(_RentalRequestHandler)
        handler.server = SimpleNamespace(model='local-test',endpoint='http://127.0.0.1:11434/v1/chat/completions')
        class Response:
            def __init__(self, body): self.body = body
            def __enter__(self): return self
            def __exit__(self,*_): pass
            def read(self,_): return self.body
        for body in [b'{}',b'null',b'{invalid',json.dumps({'choices':[{'message':{'content':'not json'}}]}).encode(),
                     json.dumps({'choices':[{'message':{'content':json.dumps({'reply':'추천 A','draft':{'sql':'SELECT'}})}}]}).encode()]:
            with self.subTest(body=body), patch('budongi.rental_server._model_request',return_value=Response(body)):
                with self.assertRaises(OSError): handler._followup([],self._request())
        with self.assertRaises(URLError): _NoModelRedirect().redirect_request(None,None,None,None,None,'https://remote.test')

    def test_http_db_failure_invalid_input_host_origin_csrf_and_map_asset_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            server = create_rental_server(port=0,database=Path(folder)/'missing.db')
            thread = threading.Thread(target=server.serve_forever,daemon=True); thread.start()
            def check(path, code, body=None, headers=None):
                request = Request(server.origin+path,data=body if isinstance(body,bytes) else json.dumps(body).encode() if body is not None else None,
                    headers={'Content-Type':'application/json','Origin':server.origin,'X-Jipdam-CSRF':server.csrf_token,**(headers or {})})
                try: response=urlopen(request,timeout=3)
                except HTTPError as error: response=error
                with response:
                    self.assertEqual(response.code,code)
                    return response.headers,response.read()
            try:
                _,body=check('/api/status',503); self.assertEqual(json.loads(body)['status'],'db_unavailable')
                check('/api/recommendations',503,{'request':self._request()})
                check('/api/chat',403,{'message':'hi'},{'Origin':'https://remote.test'})
                check('/api/chat',403,{'message':'hi'},{'X-Jipdam-CSRF':'wrong-token'})
                check('/api/status',421,headers={'Host':'untrusted.test'})
                check('/api/chat',400,{'message':'\ud800'})
                check('/api/recommendations',400,b'{"request":{"limit":'+b'9'*5000+b'}}')
                check('/api/status?other=1',400)
                headers,page=check('/',200)
                self.assertIn('https://tile.openstreetmap.org',headers['Content-Security-Policy'])
                self.assertEqual(headers['Referrer-Policy'],'strict-origin-when-cross-origin')
                self.assertIn(b'/static/vendor/leaflet/leaflet.js',page)
                _,asset=check('/static/vendor/leaflet/leaflet.js',200); self.assertIn(b'1.9.4',asset)
                check('/static/vendor/leaflet/../../rental_server.py',404)
            finally:
                server.shutdown();server.server_close();thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
