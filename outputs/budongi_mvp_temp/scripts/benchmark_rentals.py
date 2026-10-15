"""Repeatable local rental DB benchmark. No provider/model/tile requests."""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import sys
import tempfile
import shutil
from time import perf_counter

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'src'))
from budongi.canonical_rental import (open_rental_serving_reader, canonical_rental_status,
    recommend_canonical_rentals, canonical_complex_detail, recommendation_query, prepare_canonical_rental_serving)
from budongi.rental_recommendation import validate_rental_request


def create_fixture(directory: Path, candidates: int = 1000) -> Path:
    """Reuse the repository's explicitly fictional canonical/review fixture contract."""
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('Fixture directory must be new or empty')
    directory.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(APP / 'tests'))
    from test_canonical_rental import CanonicalRentalServingTests
    fixture = CanonicalRentalServingTests()
    source = directory / 'source.sqlite3'
    fixture._source(source, linked=False)
    with closing(sqlite3.connect(source)) as db, db:
        for index in range(candidates):
            cid = f'load-{index:04}'
            db.execute('INSERT INTO complexes VALUES (?,?,?,?,?,NULL,NULL,0)',
                       (cid, '11110', 'synthetic', cid, 'fictional fixture'))
            for history in range(120 if index == 0 else 20):
                oid = f'{cid}-obs-{history:03}'
                day = (date(2026, 4, 1) + timedelta(days=history)).isoformat()
                # All prices come from the same synthetic contract; no actual data is promoted.
                db.execute('INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                           (oid,None,'11110',day,f'합성 단지 {index:04}','합성동','1-1','wolse',59.5,
                            200_000_000,600_000,5,2015,None,None,None,'synthetic-v1','molit_apt_rent','15126474','raw-1'))
                db.execute("INSERT INTO batch_observations VALUES ('batch-a',?)", (oid,))
    package = fixture._review(source, directory)
    records = fixture._records(package)
    common = records['relations'][0]
    for index in range(candidates):
        cid = f'load-{index:04}'
        records['relations'].extend({**common,'observation_id':f'{cid}-obs-{history:03}','complex_id':cid}
                                    for history in range(120 if index == 0 else 20))
        if index == 0 or index % 23:  # Explicitly exercise unknown coordinates as well.
            records['coordinates'].append({**common,'complex_id':cid,'latitude':37.56+(index%25)*0.001,
                                           'longitude':126.97+(index//25)*0.001,'crs':'EPSG:4326','method':'synthetic'})
    for kind in ('station','supermarket','park','hospital'):
        records['coverage'].append({**common,'category':kind,'sgg_cd':'11110','coverage_status':'complete',
            'checked_at_utc':'2026-10-12T00:00:00Z',
            'coverage_area':{'latitude':37.58,'longitude':127.0,'radius_m':10000}})
        for index in range(500):
            records['facilities'].append({**common,'facility_id':f'{kind}-{index:04}','category':kind,
                'name':f'합성 {kind} {index}','latitude':37.555+(index%25)*0.002,
                'longitude':126.965+(index//25)*0.002,'crs':'EPSG:4326','method':'synthetic'})
    fixture._save_records(source, package, records)
    database = directory / 'serving.sqlite3'
    prepare_canonical_rental_serving(source, database, review_package=package, allow_synthetic=True)
    return database


def measure(database, call, *, allow_synthetic=False, unindexed=False):
    comparison = None
    if unindexed:
        # Compare identical serving rows; never drop indexes in the source or published file.
        comparison = tempfile.TemporaryDirectory(prefix='rental-index-comparison-', dir=APP/'data'/'rental')
        target = Path(comparison.name)/'comparison.sqlite3'
        shutil.copy2(database,target)
        with closing(sqlite3.connect(target)) as modified, modified:
            for index in ('rental_search','rental_complex_latest','rental_kind_date'):
                modified.execute('DROP INDEX ' + index)
            modified.execute('ANALYZE')
        database = target
    samples, signature = [], None
    for run in range(105):
        started = perf_counter()
        connection = open_rental_serving_reader(database, allow_synthetic=allow_synthetic)
        opened = perf_counter()
        try:
            result = call(connection)
            queried = perf_counter()
            encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True).encode('utf-8')
            assembled = perf_counter()
        finally:
            connection.close()
        digest = hashlib.sha256(encoded).hexdigest()
        if signature is not None and signature != digest: raise AssertionError('Results changed during identical requests')
        signature = digest
        if run >= 5: samples.append({'connection':(opened-started)*1000,'query':(queried-opened)*1000,
                                     'response':(assembled-queried)*1000,'total':(assembled-started)*1000})
    if comparison is not None: comparison.cleanup()
    summary = {key:{'p50_ms':round(sorted(row[key] for row in samples)[49],3),
                    'p95_ms':round(sorted(row[key] for row in samples)[94],3)} for key in samples[0]}
    return {'warmups':5,'runs':100,'timing':summary,'status':result['status'],'signature':signature}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path)
    parser.add_argument('--create-synthetic',type=Path)
    parser.add_argument('--allow-synthetic',action='store_true')
    parser.add_argument('--candidate',default='missing-reviewed-candidate')
    parser.add_argument('--compare-indexes',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.create_synthetic:
        if not args.allow_synthetic: parser.error('Synthetic creation requires --allow-synthetic')
        args.database = create_fixture(args.create_synthetic)
    if not args.database: parser.error('--database or --create-synthetic is required')
    request = {'rental_type':'wolse','max_deposit_krw':500_000_000,'max_monthly_rent_krw':1_000_000,
               'districts':['11110'],'conditions':[{'kind':kind,'max_distance_m':1000,'required':kind=='park'}
                                                for kind in ('station','supermarket','park','hospital')]}
    with closing(open_rental_serving_reader(args.database,allow_synthetic=args.allow_synthetic)) as db:
        state = canonical_rental_status(db)
        sql, params, *_ = recommendation_query(validate_rental_request(request), state)
        plans = [row[3] for row in db.execute('EXPLAIN QUERY PLAN '+sql,params)]
        facility_plan = [row[3] for row in db.execute('EXPLAIN QUERY PLAN SELECT f.* FROM facility_rtree r JOIN facilities f ON f.id=r.id WHERE r.min_lat<=? AND r.max_lat>=? AND r.min_lon<=? AND r.max_lon>=?',(38,37,128,126))]
    output = {'database':str(args.database.resolve()),'state':state,'request':request,
              'query_plan':plans,'facility_query_plan':facility_plan,'paths':{}}
    for name,call in [('recommendations',lambda db:recommend_canonical_rentals(db,request)),
                      ('detail',lambda db:canonical_complex_detail(db,args.candidate))]:
        indexed = measure(args.database,call,allow_synthetic=args.allow_synthetic)
        output['paths'][name] = {'indexed':indexed}
        if args.compare_indexes:
            baseline = measure(args.database,call,allow_synthetic=args.allow_synthetic,unindexed=True)
            if indexed['signature'] != baseline['signature']: raise AssertionError('Index comparison changed results/lineage')
            output['paths'][name]['without_rental_indexes_file_copy'] = baseline
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'quality_status':state['quality_status'],'paths':output['paths']},ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
