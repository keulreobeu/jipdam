# PIPELINE-001 — 출처를 보존하는 분석 파이프라인

```toml
kind = "spec"
id = "PIPELINE-001"
status = "approved"
owner = "Codex"
revision = 2
approved_by = "사용자"
approved_at = "2026-10-29"
approval_ref = "2026-10-29 PLEASE IMPLEMENT THIS PLAN: 집담 데이터 파이프라인 설계 — 전체 구조와 M1 상세"
```

## 목표와 경계

66개 메타데이터 항목을 원문·스냅샷으로 등록하고 네 대표 입력(XML, 통계 XLSX, 공시가격 CSV, 학교 JSON)을 오프라인 분석 출력으로 변환한다. 원본·canonical v3·statistics v1·추천 DB는 보존한다. Python은 파싱/정규화, dbt는 분석 모델을 담당한다. Snowflake/dbt/Airflow는 후속 단계이며 계정·예산·Linux 환경 없이 실행하지 않는다. 새 수집·매칭·좌표 검수·추천 연결·원격 업로드는 포함하지 않는다.

## PIPELINE-001-REQ-01 Catalog와 입력 무결성

워크북 바이트와 SHA-256, namespace/원래 ID/시트/셀을 보존한다. 메타데이터는 데이터이며 명령이 아니다. 등록 항목, 논리 데이터셋, 배치, 콘텐츠, 저장 위치를 분리한다. 수치 원문과 미측정 상태를 보존하고 수집/파싱/품질/관계/이용조건 상태를 분리한다. 위치는 명시 등록하며 파일명만으로 해시나 논리적 동일성을 추정하지 않는다.

### PIPELINE-001-AC-01

66개 실제 항목 수입·동일 재수입·개정·namespace 충돌·셀 위치·원본 해시와 미측정/0 구분을 검증한다.

## PIPELINE-001-REQ-02 오프라인 실행·계보·게시

등록된 네 어댑터만 실행한다. 요청은 dataset_id/adapter_id/batch_id/mapping_version/input_refs/output_root를 명시한다. 각 input_ref는 등록된 파일의 SHA-256과 상대 역할을 가진다. 임의 코드·셸·출처 승인을 실행하지 않는다. 입력과 기존 DB에 쓰지 않고 작업 공간에서 변환한다. 같은 배치·버전·입력 재실행은 출력 무결성을 확인한 후 재사용하며 같은 배치의 입력 변경은 거부한다. output_root 아래 실행별 출력만 만들고 기존 출력은 덮어쓰지 않는다. 모든 게시 파일의 해시와 논리 결과 digest를 기록한다. 오류·강제 종료·동시 실행은 성공으로 표시하지 않는다.

### PIPELINE-001-AC-02

반복/변경배치 거부, 입력 변조, 출력 변조, 잠금, 중단 복구, 실패 비게시와 CLI 종료코드(0 성공/재사용, 1 실행실패, 2 차단)를 검증한다.

## PIPELINE-001-REQ-03 네 데이터 계약

MOLIT는 기존 normalize_row와 관측기간/서비스 분리, 통계는 기존 통계 importer의 원본 셀·Decimal·source_view, 공시가격은 서울 필터와 원 정수/면적 Decimal 문자열/원천 ID, 학교는 기존 검증 우선순위와 원본 페이지/행을 유지한다. accepted_input_rows+excluded_rows+rejected_rows=input_rows를 검증하고 output_rows는 별도로 센다. 처리 대상의 원문과 원본 위치를 보존하며 알려진 excluded/rejected 학교행은 별도 격리에 남긴다. 금액/코드/날짜 오류를 정상으로 바꾸지 않는다. 거래/공시가격의 필수값 오류는 최종 게시를 차단한다.

### PIPELINE-001-AC-03

네 어댑터의 정확한 단위/정밀도/NULL, 출처 namespace, 전체 대사, 1:N 계보와 실제 원본 결과 비교를 검증한다. 합성 결과를 실제 검증으로 표시하지 않는다.

## PIPELINE-001-REQ-04 측정과 성능 목표

실행/단계/시도·입력지문·Git/dirty·환경·단조시간·건수/바이트·메모리를 기록한다. 메모리는 프로세스 트리의 동시 RSS 합계 최대 관측값(표본 간격/누락 포함)이다. 원본 JSON이 정본이며 SQLite는 단일 기록 경로의 조회 인덱스다. 신규 산출물은 typed Parquet와 DuckDB SQL로 조회 가능하다. 기준선/개선 모두 같은 입력·변환·범위·환경·결과로 최소 5회 실행하며 중복값을 포함한 논리 결과 digest를 비교한다. 메모리/기준선 누락은 0이 아닌 unavailable이다.

### PIPELINE-001-AC-04

측정·실패·재시도 기록, 서로 다른 결과의 비교 거부, 5회 결과/중앙값/p95와 기준선 부재 상태를 검증한다. 실제 성능 목표는 기준선 뒤 사용자 확정 전까지 pending이며 M1 완료를 차단한다.

2026-10-29 사용자는 측정한 범위와 목표를 확정했다. 통계 전체 입력은 기준선 중앙시간 25,913.4247ms의 80% 이하, 나머지 MOLIT 10,000행/학교 전체/공시가격 100,000행은 각 기준선 중앙시간의 110% 이하, 네 유형 모두 최대 관측 RSS의 110% 이하이며 결과는 완전히 같아야 한다. 거래·공시가격 전체 처리시간 목표는 후속 전체 5회 기준선 이후에 정한다. 표본 목표를 전체 성능으로 표시하지 않는다.

`pipeline report --request <JSON>`은 사용자 확정 근거와 dataset별 baseline/candidate benchmark ID·시간/RSS 비율 한도를 받아 보존한 실제 성공 실행을 다시 확인한다. 두 집합은 각 5회 이상의 서로 다른 실행이어야 하며 Catalog에 고정한 영수증/출력 해시, 의미·환경·건수·논리 지문을 대조한다. 이번 최적화의 ID/payload/행 순서까지 보호하기 위해 Parquet와 격리 파일 해시도 같아야 한다. 미측정 메모리나 변조·불일치를 목표 달성으로 표시하지 않는다. 성능 보고만으로 전체 M1을 자동 완료하지 않고 최종 Task AC로 수용한다.

## PIPELINE-001-REQ-05 인터페이스·후속 구조

pipeline catalog import/inventory/plan/run/status/lineage/benchmark/report CLI와 버전 JSON을 제공한다. 선택 의존성만 추가하며 기존 CLI를 유지한다. 후속 구조는 독립 DuckDB Mart → Snowflake Internal Stage/적재원장 → dbt 증분/검증 → Linux Airflow/PostgreSQL이다. Snowflake PK/FK를 검증으로 대체하지 않고 지연 비용·예산·검수 게이트를 보존한다.

### PIPELINE-001-AC-05

CLI·관련 기존 34개 회귀·SDD/환경 검사와 운영 문서를 확인한다. 위키 판단과 동기화 상태를 Task에 남긴다. 미준비 클라우드·미확정 목표를 완료로 표시하지 않는다.

관련: [Plan](../plans/pipeline-m1.md), [ADR-025](../adr/ADR-025-analysis-pipeline.md), [Task](../tasks/pipeline-m1.md).
