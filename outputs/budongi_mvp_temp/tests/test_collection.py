from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from budongi.collection import (CollectionError, collection_status, create_plan, fetch_collection,
                                load_plan, load_query, parse_page, query_folder, read_json, write_json)
from budongi.collection_db import build_databases, normalize_row, pack_collection

KEY = "synthetic-secret-no-real-provider-access"
RECORD = "https://github.com/keulreobeu/jipdam/issues/5"


def item(name="시험단지", service="rental", day=15):
    values = {"sggCd": "11110", "umdNm": "청운동", "aptNm": name, "jibun": "1-1",
              "dealYear": "2026", "dealMonth": "9", "dealDay": str(day), "excluUseAr": "59.95",
              "floor": "3", "buildYear": "2017", "unknownFutureField": "보존할 값"}
    if service == "rental":
        values.update(deposit="50,000", monthlyRent="0", preDeposit="단위미확인")
    else:
        values.update(dealAmount="70,000", aptSeq="11110-100", cdealType=" ")
    return values


def payload(rows, *, page=1, per_page=1000, total=None, result="000"):
    xml = "".join("<item>" + "".join(f"<{k}>{v}</{k}>" for k, v in row.items()) + "</item>" for row in rows)
    return (f"<response><header><resultCode>{result}</resultCode></header><body><items>{xml}</items>"
            f"<pageNo>{page}</pageNo><numOfRows>{per_page}</numOfRows><totalCount>{len(rows) if total is None else total}</totalCount>"
            "</body></response>").encode()


class Response:
    def __init__(self, raw): self.raw = raw
    def __enter__(self): return self
    def __exit__(self, *_): return None
    def read(self, maximum): return self.raw[:maximum]


class Vault:
    def __init__(self): self.calls = []
    def get_secret(self, identifier):
        self.calls.append(identifier)
        return KEY


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def plan(self, path=None, services=("rental",), per_page=1000, record_url=RECORD):
        path = path or self.root / "batch"
        create_plan(path, batch_id=path.name, snapshot_date="2026-10-12", districts=["11110"],
                    months=["202609"], services=list(services), per_page=per_page, record_url=record_url)
        return path

    def fetch(self, path, opener, **kwargs):
        return fetch_collection(path, {s: s+"-opaque-id" for s in load_plan(path)["services"]},
                                vault=kwargs.pop("vault", Vault()), opener=opener, sleep=lambda _: None, **kwargs)

    def test_scope_boundary_record_gate_and_no_historical_database(self):
        path = self.root / "all"
        plan = create_plan(path, batch_id="all", snapshot_date="2026-10-12")
        self.assertEqual(set(plan["services"]),{"rental","trade","trade-detail"})
        self.assertEqual(plan["months"], [f"2025{n:02d}" for n in (10,11,12)] + [f"2026{n:02d}" for n in range(1,11)])
        self.assertEqual(collection_status(path)["query_count"], 975)
        with self.assertRaisesRegex(CollectionError, "github_collection_record_required"):
            fetch_collection(path, {}, opener=lambda *_: self.fail("Network before record"))
        self.assertFalse((path / "serving.sqlite3").exists())

    def test_completed_query_reexecution_uses_no_network_or_vault(self):
        path = self.plan()
        self.assertTrue(self.fetch(path, lambda *a, **k: Response(payload([item()])))["complete"])
        result = fetch_collection(path, {}, vault=object(), opener=lambda *a, **k: self.fail("Network"))
        self.assertEqual(result["new_queries"], 0)
        raw = next(path.rglob("*.xml")).read_bytes()
        self.assertEqual(raw, payload([item()]))

    def test_explicit_key_id_reused_across_services_without_provider_inference(self):
        from budongi.credential_vault import CredentialVault

        class MemoryStore:
            value = None
            def read(self): return self.value
            def write(self, value): self.value = value

        vault = CredentialVault(self.root / "vault.sqlite3", MemoryStore())
        folder = vault.create_folder("공공데이터 API")["id"]
        # Previously saved provider metadata must not override the explicit service-to-ID map.
        key = vault.add_credential(folder_id=folder, provider_id="molit_rental",
                                   alias="공공데이터 공통 인증키", api_key=KEY)
        services = ("rental", "trade", "trade-detail")
        path = self.plan(services=services)
        calls = []
        def opener(request, **kwargs):
            self.assertEqual(parse_qs(urlparse(request.full_url).query)["serviceKey"], [KEY])
            calls.append(request.full_url)
            return Response(payload([]))
        result = fetch_collection(path, {s: key["id"] for s in services}, vault=vault,
                                  opener=opener, sleep=lambda _: None)
        self.assertTrue(result["complete"])
        self.assertEqual(len(calls), 3)
        for file in path.rglob("*.json"):
            self.assertNotIn(KEY, file.read_text())

    def test_failed_response_saved_and_resume_calls_only_missing_page(self):
        path = self.plan(per_page=1)
        calls = []
        def first(request, **kwargs):
            page = int(parse_qs(urlparse(request.full_url).query)["pageNo"][0]); calls.append(page)
            if page == 2: return Response(b"not XML")
            return Response(payload([item()], page=page, per_page=1, total=2))
        self.assertFalse(self.fetch(path, first)["complete"])
        self.assertEqual(calls, [1,2])
        self.assertIn(b"not XML", [p.read_bytes() for p in path.rglob("*.xml")])
        calls.clear()
        def resume(request, **kwargs):
            page = int(parse_qs(urlparse(request.full_url).query)["pageNo"][0]); calls.append(page)
            return Response(payload([item()], page=page, per_page=1, total=2))
        self.assertTrue(self.fetch(path, resume)["complete"])
        self.assertEqual(calls, [2])

    def test_atomic_manifest_replace_survives_transient_reader_lock(self):
        path=self.root/'manifest.json';write_json(path,{'state':'old'})
        import os
        replace=os.replace
        blocked=[]
        def one_reader_lock(source,target):
            if not blocked:
                blocked.append(True)
                self.assertEqual(read_json(path),{'state':'old'})
                raise PermissionError('simulated read handle')
            return replace(source,target)
        with patch('budongi.collection.os.replace',side_effect=one_reader_lock),patch('budongi.collection.time.sleep'):
            write_json(path,{'state':'new'})
        self.assertEqual(read_json(path),{'state':'new'})
        self.assertFalse(path.with_name('manifest.json.tmp').exists())

    def test_journalled_response_recovers_after_manifest_commit_failure_without_api_or_vault(self):
        path=self.plan()
        write=write_json
        failed=[]
        def interrupted_commit(target,value):
            if target.name=='manifest.json' and value.get('pages') and not failed:
                failed.append(True)
                raise PermissionError('interrupted commit')
            return write(target,value)
        with patch('budongi.collection.write_json',side_effect=interrupted_commit):
            with self.assertRaises(PermissionError):
                self.fetch(path,lambda *a,**k:Response(payload([item()])))
        raw=next(path.rglob('*.xml')).read_bytes()
        result=fetch_collection(path,{},vault=object(),opener=lambda *a,**k:self.fail('Repeat API call'))
        self.assertTrue(result['complete']);self.assertEqual(result['new_queries'],0)
        self.assertEqual(next(path.rglob('*.xml')).read_bytes(),raw)

    def test_reflected_key_not_saved_and_transient_retry_is_bounded(self):
        path = self.plan()
        result = self.fetch(path, lambda *a, **k: Response(KEY.encode()))
        self.assertEqual(result["service_errors"]["rental"], "credential_reflected_response_blocked")
        self.assertEqual(list(path.rglob("*.xml")), [])
        for p in path.rglob("*.json"): self.assertNotIn(KEY, p.read_text())
        path2 = self.plan(self.root / "retry")
        calls=[]
        def fail(*a, **k):
            calls.append(1); raise urllib.error.URLError("echo "+KEY)
        self.fetch(path2, fail)
        self.assertEqual(len(calls),3)
        self.assertNotIn(KEY, (next(path2.rglob("manifest.json"))).read_text())

    def test_zero_partial_mismatch_and_tampering_are_distinct(self):
        path=self.plan()
        self.fetch(path, lambda *a, **k: Response(payload([])))
        self.assertEqual(collection_status(path)["queries"][0]["status"], "complete_zero")
        xml=next(path.rglob("*.xml")); xml.write_bytes(b"changed")
        self.assertEqual(collection_status(path)["queries"][0]["status"], "invalid")
        with self.assertRaises(CollectionError): build_databases(path, path/"db")
        with self.assertRaisesRegex(CollectionError,"pagination_metadata_mismatch"):
            parse_page(payload([],page=2),page=1,per_page=1000,code="11110",month="202609")

    def test_external_cache_is_verified_and_reused_without_credentials(self):
        source=self.plan(self.root/"source")
        self.fetch(source,lambda *a,**k:Response(payload([item()])))
        target=self.plan(self.root/"target")
        result=fetch_collection(target,{},cache_dirs=[source],vault=object(),opener=lambda *a,**k:self.fail("Network"))
        self.assertTrue(result["complete"])
        self.assertEqual(result["new_queries"],0)
        self.assertEqual(next(source.rglob("*.xml")).read_bytes(),next(target.rglob("*.xml")).read_bytes())
        # A saved response with an interrupted journal commit is also reusable from a donor.
        manifest_path=next(source.rglob('manifest.json'))
        manifest=read_json(manifest_path)
        manifest['status']='partial';manifest['pages']=[];manifest['attempts'][0]['status']='received'
        write_json(manifest_path,manifest)
        target2=self.plan(self.root/'target2')
        result=fetch_collection(target2,{},cache_dirs=[source],vault=object(),opener=lambda *a,**k:self.fail('Network for cached response'))
        self.assertTrue(result['complete']);self.assertEqual(result['new_queries'],0)
        self.assertEqual(read_json(manifest_path)['status'],'partial')

    def test_partial_external_cache_reuses_pages_and_fetches_only_missing_page(self):
        source=self.plan(self.root/'partial-source',per_page=1)
        def interrupted(request,**kwargs):
            page=int(parse_qs(urlparse(request.full_url).query)['pageNo'][0])
            return Response(payload([item()],page=1,per_page=1,total=2) if page==1 else b'failed XML')
        self.fetch(source,interrupted)
        target=self.plan(self.root/'partial-target',per_page=1)
        calls=[]
        def resume(request,**kwargs):
            page=int(parse_qs(urlparse(request.full_url).query)['pageNo'][0]);calls.append(page)
            return Response(payload([item()],page=page,per_page=1,total=2))
        result=self.fetch(target,resume,cache_dirs=[source])
        self.assertTrue(result['complete']);self.assertEqual(calls,[2])

    def test_interrupted_http_error_response_cannot_be_promoted_to_success(self):
        path=self.plan();self.fetch(path,lambda *a,**k:Response(payload([item()])))
        manifest_path=next(path.rglob('manifest.json'));manifest=read_json(manifest_path)
        manifest['status']='partial';manifest['pages']=[]
        manifest['attempts'][0].update(status='received',http_status=500)
        write_json(manifest_path,manifest)
        calls=[]
        def provider(*a,**k):calls.append(1);return Response(payload([]))
        result=self.fetch(path,provider)
        self.assertTrue(result['complete']);self.assertEqual(calls,[1])
        self.assertEqual(result['counts_by_service']['rental'],0)

    def test_offline_mapping_database_rebuild_and_source_separation(self):
        path=self.plan(services=("rental","trade","trade-detail"))
        def provider(request,**kwargs):
            service="rental" if "AptRent" in request.full_url else "trade"
            return Response(payload([item(service=service),item(service=service)]))
        self.fetch(path,provider)
        with patch("budongi.collection._open_request",side_effect=AssertionError("Offline")),patch("budongi.credential_vault.CredentialVault",side_effect=AssertionError("Vault")):
            first=build_databases(path,path/"db")
            second=build_databases(path,path/"db2")
        self.assertEqual(first["counts"],second["counts"])
        self.assertEqual(first["lineage_joins"], {"rental_observations": 2, "sale_observations": 4})
        staging=sqlite3.connect(path/"db/staging.sqlite3")
        self.assertEqual(staging.execute("SELECT COUNT(*) FROM staging_items").fetchone()[0],6)
        self.assertEqual(staging.execute("SELECT SUM(raw_rows) FROM raw_files").fetchone()[0],6)
        self.assertEqual(staging.execute("PRAGMA foreign_key_check").fetchall(),[])
        with self.assertRaises(sqlite3.IntegrityError):
            staging.execute("DELETE FROM staging_items")
        staging.close()
        for folder in ("db","db2"):
            c=sqlite3.connect(path/folder/"rental.sqlite3")
            self.assertEqual(c.execute("select count(*) from rental_observations").fetchone()[0],2)
            self.assertEqual(c.execute("select deposit_krw,monthly_rent_krw,previous_deposit_krw from rental_observations limit 1").fetchone(),(500000000,0,None))
            self.assertIn("unknownFutureField",c.execute("select raw_payload_json from rental_observations limit 1").fetchone()[0])
            self.assertEqual(c.execute("select quality_status from rental_snapshots").fetchone()[0],"source_unverified")
            self.assertEqual(c.execute("pragma foreign_key_check").fetchall(),[])
            c.close()
        c=sqlite3.connect(path/"db/sales.sqlite3")
        self.assertEqual(c.execute("select count(distinct source),count(*) from sale_observations").fetchone(),(2,4))
        self.assertEqual(c.execute("select count(source_record_id) from sale_observations").fetchone()[0],0)
        c.close()
        a=sqlite3.connect(path/"db/rental.sqlite3"); b=sqlite3.connect(path/"db2/rental.sqlite3")
        self.assertEqual(a.execute("select observation_id,raw_payload_json from rental_observations order by observation_id").fetchall(),b.execute("select observation_id,raw_payload_json from rental_observations order by observation_id").fetchall())
        a.close();b.close()
        with self.assertRaisesRegex(CollectionError,"output_exists"): build_databases(path,path/"db")

    def test_invalid_required_values_roll_back_and_record_row_error(self):
        path=self.plan(); raw=item();raw["deposit"]=" "
        raw2=item();raw2["monthlyRent"]="NaN"
        self.fetch(path,lambda *a,**k:Response(payload([raw,raw2,item()])))
        with self.assertRaises(CollectionError):build_databases(path,path/"db")
        self.assertFalse((path/"db").exists())
        report=json.loads((path/"normalization-errors.json").read_text())
        self.assertEqual(report["source_row_number"],1)
        self.assertEqual([e["source_row_number"] for e in report["errors"]],[1,2])
        self.assertEqual(report["counts"]["rental"],{
            "raw_rows":3,"imported":1,"excluded_outside_period":0,"rejected":2})

    def test_period_exclusions_remain_in_staging_with_row_lineage(self):
        path=self.root/"boundary"
        create_plan(path,batch_id="boundary",snapshot_date="2026-10-12",districts=["11110"],
                    months=["202510"],services=["rental"],record_url=RECORD)
        excluded=item(day=1);excluded.update(dealYear="2025",dealMonth="10")
        valid=item(day=12);valid.update(dealYear="2025",dealMonth="10")
        self.fetch(path,lambda *a,**k:Response(payload([excluded,valid])))
        result=build_databases(path,path/"db")
        self.assertEqual(result["counts"]["rental"],{
            "raw_rows":2,"imported":1,"excluded_outside_period":1,"rejected":0})
        c=sqlite3.connect(path/"db/staging.sqlite3")
        self.assertEqual(c.execute("SELECT source_row_number,validation_status,reason FROM staging_items ORDER BY source_row_number").fetchall(),
                         [(1,"outside_period","contract_date_outside_observation_period"),(2,"valid",None)])
        self.assertEqual(c.execute("SELECT COUNT(*) FROM staging_items s JOIN raw_files f ON f.file_ref=s.source_file_ref").fetchone()[0],2)
        c.close()

    def test_partial_build_package_and_cli(self):
        path=self.plan(services=("rental","trade"))
        self.fetch(path,lambda *a,**k:Response(payload([item()])),limit=1)
        with self.assertRaisesRegex(CollectionError,"incomplete_collection"):build_databases(path,path/"db")
        derived=build_databases(path,path/"db",allow_partial=True)
        self.assertFalse(derived["complete"])
        with self.assertRaisesRegex(CollectionError,"incomplete_collection"):
            pack_collection(path,self.root/"no.zip",db_directory=path/"db")
        result=pack_collection(path,self.root/"partial.zip",db_directory=path/"db",allow_partial=True)
        with zipfile.ZipFile(result["archive"]) as archive:
            self.assertIn("manifest.json",archive.namelist());self.assertIn("db/rental.sqlite3",archive.namelist())
            package=json.loads(archive.read("manifest.json"))
            self.assertEqual(package["quality_status"],"source_unverified")
            self.assertEqual(package["counts"],derived["counts"])
            self.assertEqual(package["observation_period"],["2025-10-12","2026-10-12"])
            self.assertTrue(any(n.endswith(".xml") for n in archive.namelist()))
            for n in archive.namelist():self.assertNotIn(KEY.encode(),archive.read(n))
        completed=subprocess.run([sys.executable,"-X","utf8","-m","budongi.cli","collection","status","--directory",str(path)],capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(completed.returncode,0,completed.stderr)
        self.assertFalse(json.loads(completed.stdout)["complete"])
        self.fetch(path,lambda *a,**k:Response(payload([item(service="trade")])))
        self.assertTrue(collection_status(path)["complete"])
        with self.assertRaisesRegex(CollectionError,"stale_database_rebuild"):
            pack_collection(path,self.root/"stale.zip",db_directory=path/"db")
        self.assertFalse((self.root/"stale.zip").exists())


if __name__ == "__main__": unittest.main()
