# 오프라인 데이터 파이프라인 사용·재개 안내

계약: [PIPELINE-001](specs/27_pipeline_spec.md), [실행 계획·스킬 배정](plans/pipeline-m1.md), [진행·검증](tasks/pipeline-m1.md), Jira KAN-28.

## 설치와 시작

프로젝트의 Python 3.11+ 환경에서 분석 의존성만 선택 설치한다. 기존 추천 앱의 기본 의존성에 Airflow/dbt를 넣지 않는다.

```powershell
cd outputs/budongi_mvp_temp
python -m pip install -e '.[pipeline]'
$env:PYTHONPATH = (Resolve-Path src).Path
python -X utf8 -m budongi.cli pipeline --help
```

이후 예시는 제품 폴더 기준이다. `--root`는 `pipeline` 뒤, 하위 명령 앞에 둔다. 기본값은 `data/pipeline`이다. 원본·DB·워크북·실행 요청·측정 JSON은 Git에 넣지 않는다.

```powershell
python -m budongi.cli pipeline catalog import --workbook C:/path/metadata.xlsx --namespace collector
python -m budongi.cli pipeline inventory --request C:/path/inventory.json
python -m budongi.cli pipeline inventory
python -m budongi.cli pipeline plan --request C:/path/request.json
python -m budongi.cli pipeline run --request C:/path/request.json
python -m budongi.cli pipeline status
python -m budongi.cli pipeline lineage --run-id RUN_ID --record-id RECORD_ID
python -m budongi.cli pipeline benchmark --request C:/path/request.json --repetitions 5
python -m budongi.cli pipeline report
```

## 입력 계약

inventory JSON에는 `datasets`와 `files` 배열을 둔다. dataset은 dataset_id/adapter_id/mapping_version/contract와 선택 catalog_refs(snapshot_id/entry_id)를 명시한다. 등록 항목을 자동 동일 데이터셋으로 병합하지 않는다. file은 input_id/dataset_id/mapping_version/path/sha256/descriptor를 명시한다. 파일명만으로 원본을 확정하지 않는다. 없는 파일은 inventory 기록의 missing 상태로 남고 실행 입력으로 등록되지 않는다. input_id의 다른 콘텐츠나 위치는 새 ID로 등록한다.

run 요청은 다음 모양이다. `output_root`는 Catalog root와 같아야 하며 입력 원본이나 기존 DB를 출력으로 지정하지 않는다.

```json
{
  "dataset_id": "registered-dataset",
  "adapter_id": "assessed_csv",
  "mapping_version": "molit_house_price_csv_v1",
  "batch_id": "explicit-batch",
  "input_refs": ["registered-input-id"],
  "output_root": "C:/explicit/analysis-root",
  "engine": "python"
}
```

선택 `max_input_rows`는 명시적 표본 실행이며 전체 검증으로 세지 않는다. `timeout_seconds` 기본은 3600초다. 등록하지 않은 필드·엔진·어댑터·다른 root는 차단한다. CLI는 성공/검증된 재사용 0, 실행 실패 1, 잘못된 입력/준비 조건 2로 종료한다.

| 어댑터 | 필수 계약·descriptor | 보존하는 의미 |
| --- | --- | --- |
| molit_xml | contract: observation_from/snapshot_date; 파일: service/page/per_page/district/month/source_ref | 기존 parse_page/normalize_row, 서비스별 source namespace·관측기간 |
| statistics_xlsx | 파일: 원래 파일명이 바뀌었으면 provided_filename | 등록 통계 profile, 원본 시트·행·열·Decimal·주기·표현 |
| assessed_csv | ZIP이면 명시 member; encoding 기본 utf-8 | 전국 입력/서울 출력, 공시가격 원 정수·면적 문자열·출처 코드 |
| neis_json | contract: expected_total_rows; 파일: page/expected_rows | 페이지 전체 대사, 정상·제외·거부 우선순위, 미제공 좌표 NULL |

## 상태·실패·계보

`metadata/`는 불변 워크북, Catalog는 항목/논리 데이터셋/파일/위치/배치를 분리한다. 워크북의 수식과 설명은 실행하지 않는다. 원본 수치는 원문 셀과 타입으로 보존하고 검수 상태는 미확인에서 자동 승격하지 않는다.

`work/<run_id>/`에서 입력 복사·해시 확인 후 별도 worker가 변환한다. `outputs/<run_id>/`에는 data.parquet, quarantine.jsonl, worker-result.json, run.json이 게시된다. Parquet는 공통 계보 필드와 출처별 typed 핵심 열, 전체 정규화 payload_json을 보존한다. 원본을 대신하지 않는다. 공시가격의 서울 밖 행은 수량과 필터·입력 해시로 추적하고 수백만 제외행의 사본을 만들지 않는다.

동일 배치·입력·코드·엔진은 출력 해시 확인 후 재사용한다. 같은 배치가 다른 입력/코드/엔진이면 새 배치 ID가 필요하다. 실행 OS 잠금은 프로세스 종료 시 풀린다. 다음 실행은 중단된 기록을 interrupted로 남기고 새 시도를 시작한다. 게시 뒤 인덱스 갱신 중 중단된 경우에는 완성된 영수증과 파일을 확인해 복구한다. 입력 손상과 잘못된 게시 결과는 오류이며 성공 0건으로 숨기지 않는다. 작업 폴더를 임의 삭제하지 말고 status와 실패 events를 먼저 확인한다.

## 측정과 제한

duration_ms는 격리 worker의 프로세스 실행·기동·파싱·검증·Parquet 쓰기를 포함한다. end_to_end_duration_ms는 입력 검증·복사와 출력 해시도 포함한다. stages는 입력 사본/worker/정규화·검증·쓰기 시간을 구분한다. input_bytes는 ZIP이면 압축된 입력 파일 크기다.

메모리는 100ms 간격 worker와 자식들의 동시 RSS 합계 최대값이다. 샘플 수·오류를 함께 기록한다. RSS는 공유 페이지 중복을 포함할 수 있고 실제 OS 고수위 값이나 유일 물리 메모리가 아니다. 누락은 null이다. CPU/RAM/Python·라이브러리/Git commit/dirty를 기록하고 저장장치 유형은 확인하지 못하면 unknown이다.

benchmark는 매회 새 worker·출력·배치를 사용한다. 초기 기준선은 현재 계측 어댑터의 실행이며 과거 미계측 CLI의 성능을 소급하지 않는다. 다른 결과·범위·환경은 incomparable이다. 5회 p95는 nearest-rank 탐색 통계이며 OS 파일 캐시는 통제하지 않는다. 공시가격에 한해 `--candidate-engine pandas_full|pandas_chunked|duckdb`로 같은 변환 규칙의 결과를 비교할 수 있다. 표본 실행에서 Pandas 행 수는 표본으로 제한하지만 ZIP 준비나 엔진 자체 읽기 비용은 실제 수행량을 포함한다.

개선율은 목표가 아니다. 목표 미등록 시 report는 targets_status=pending_user_targets, m1_complete=false를 반환한다. `report --request <목표 JSON>`으로 저장한 기준선/개선 측정을 대조한다. 요청은 assessment_id, approved_by, approval_ref, targets 배열을 가지며 각 항목에 dataset_id, baseline_id, candidate_id, source_signature, baseline_sha256, max_duration_ratio, max_memory_ratio를 명시한다. 기준선의 지문·해시를 승인 범위에 고정하며 다른 범위나 변경된 기준선으로 목표를 통과시킬 수 없다.

각 측정 집합의 서로 다른 성공 실행이 5회 이상이고 실제 게시 영수증/파일 해시가 온전해야 한다. 동일 의미/환경/건수/결과 지문과 이번 최적화의 Parquet·격리 파일 바이트까지 대조한다. 미측정 RSS나 표본 오류가 있으면 성능을 통과시키지 않는다. 불충족은 targets_status=not_met와 종료 코드 2다. 수용 가능한 결과는 assessments/에 보존하고 report는 실제 산출물을 다시 검사한다. 여러 평가가 있으면 `report --assessment-id <ID>`로 명시 선택한다. 성능 평가가 있어도 전체 M1 완료는 Task의 AC 수용으로 결정하며 보고서의 m1_complete=null은 성능만으로 판정하지 않았다는 뜻이다.

2026-10-29 확정 목표/측정 범위와 실제 결과는 [Task](tasks/pipeline-m1.md)에 있다. 거래·공시가격 표본 시간을 전체 성능으로 환산하지 않는다. 네 대표 이외 항목, 전체 원본 확보·라이선스 검수·좌표·매칭·추천·클라우드는 완료로 표시하지 않는다.

## 현재 PC에서 이어가기

저장소 루트의 `.local_runtime/pipeline-work/`에 명시적인 inventory.json, 네 실제 실행 요청과 표본 benchmark 요청이 있다. 경로는 이 PC의 복원 위치를 가리키며 다른 PC로 그대로 복사해 실행하지 않는다. 다른 PC는 원본 패키지를 확보·검증하고 새 위치를 등록한다. 코드·계약의 정본은 이 문서와 Plan/Spec/Task다.
