# 집담 데이터 파이프라인 실행 계획

2026-10-29 사용자가 대화의 전체 구조+M1 상세 계획을 구현 승인했다. [Spec](../specs/27_pipeline_spec.md), [Task](../tasks/pipeline-m1.md), [ADR](../adr/ADR-025-analysis-pipeline.md).

## 선택과 순서

1. 66개 메타데이터 항목을 원문과 등록하고 원본 위치/해시를 대사한다.
2. 원본을 변경하지 않는 실행·계보·측정 계약과 CLI를 구축한다.
3. 기존 정규화 규칙을 이용하는 네 대표 어댑터를 연결하고 실제 결과를 대사한다.
4. 같은 원본/범위/환경/결과로 기존·개선 후보를 5회 이상 측정한다. 값이 없으면 baseline_unavailable, 비용이 지연되면 pending으로 남긴다.
5. 기준선 보고 뒤 사용자가 데이터별 개선 목표/허용 회귀를 확정한다. 목표 전·미달 상태에서 M1 완료 금지.

```text
메타데이터 -> Catalog <- 원본 manifest/해시/위치
원본 -> Python 정규화/검증 -> typed Parquet -> DuckDB
                  |              |
                  +-> 계보/격리  +-> 후속 Snowflake Landing -> dbt Silver/Gold
실행 시작/종료 -> JSON 증거 -> SQLite 조회 인덱스
후속 Airflow -> 동일 실행 인터페이스 (데이터는 XCom 대신 참조로 전달)
```

## 후속 M2/M3

출처별 거래 관측/통계/공시가격/시설을 독립 사실로 모델링한다. 확정된 코드/시점만 차원으로 연결한다. Snowflake 계정·리전·권한·이전 조건·예산 확정 후 Internal Stage/COPY와 자체 적재원장을 구현한다. COPY의 일시적 중복방지 기록이나 PK/FK 선언만으로 멱등성/무결성을 주장하지 않는다. 증분은 계약일 아닌 배치/변경 지문으로 처리하고 과거를 보존한다. 쿼리비용/유휴시간/스토리지를 구분한다.

Linux Docker 환경에서 dbt와 Airflow/PostgreSQL을 격리한다. 수동 실행부터 시작하고 원본 손상·파싱·강제종료·Load·dbt 실패·Backfill을 검증한다. 스케줄·새 수집·외부 업로드·좌표/시설 검수·추천 연결은 별도 후속 승인/설정이다. 계정/예산/엔진 준비 전 실제 클라우드 완료를 주장하지 않는다.

## 병행·변경 보호

기존 사용자 미커밋 변경을 유지한다. 공유 CLI/원장 변경은 순차 반영한다. 메인이 구현·검증을 맡고 Git 전담 서브에이전트는 현재 AGENTS의 Git 생명주기에 따라 별도 publisher에서 고정 스냅샷만 저장한다. 같은 worker/worktree를 동시에 편집하지 않는다. 허용된 코드·문서만 GMS runner에 제공하고 실제 원본·DB·메타데이터 값은 전송하지 않는다.

## 단계별 gstack 스킬 배정 — 다음 채팅의 실행 계약

모든 단계는 루트/제품 AGENTS.md와 `jipdam-workflow`부터 읽는다. 스킬 이름은 `.agents/skills/<이름>/SKILL.md`를 뜻하며 실행 시 현재 설치본을 읽는다. 아래는 미래 작업 배정이며 스킬이 이미 실행·통과했다는 뜻이 아니다. 새 구현은 Jira와 영구 Task를 먼저 연결한다.

| 단계 | 먼저 적용할 스킬 | 검토·검증·문서 스킬 | 시작 조건 / 완료 근거 |
| --- | --- | --- | --- |
| Phase 0 기존 기능·기준선 | gstack-plan-eng-review | gstack-qa-only, gstack-document-release | 원본 해시/범위 확인 → 동일 작업의 실제 측정·환경·한계 기록 |
| Phase 1 Catalog·원본·계보 | gstack-plan-eng-review | gstack-review, gstack-qa, gstack-document-release | 항목/논리 데이터셋/배치/파일 구분 → 반복·개정·변조·원본 역추적 검증 |
| Phase 2 ETL·품질·최적화 | gstack-plan-eng-review | gstack-investigate(오류 원인 조사), gstack-qa, gstack-review, gstack-document-release | 대표 4종·기준선/사용자 목표 → 결과 동등성과 목표/허용 회귀 검증 |
| Phase 3 DuckDB·Mart | gstack-plan-eng-review | gstack-review, gstack-qa, gstack-document-release | 원본별 typed 출력 검증 → 독립 집계·코드/시점·SQL 결과 대사 |
| Phase 4 Snowflake 적재 | gstack-plan-eng-review | gstack-cso(권한/비밀/업로드 경계), gstack-review, gstack-qa, gstack-document-release | 계정/리전/권한/이전 조건/예산 확정 → COPY·자체 원장·재시도·대사·비용 상태 |
| Phase 5 dbt 증분 | gstack-plan-eng-review | gstack-review, gstack-qa, gstack-document-release | 검증된 Landing → full/incremental 동일성·지연 입력·중복·manifest/run_results 보존 |
| Phase 6 Airflow 운영 | gstack-plan-eng-review | gstack-qa, gstack-investigate(실패 원인), gstack-review, gstack-document-release | Linux 엔진/PostgreSQL → 수동 DAG·강제종료·재시도·Backfill·복구시간 증거 |
| Phase 7 성능·비용 | gstack-plan-eng-review | gstack-qa(정합성), gstack-review, gstack-document-release | 사용자 승인 실험/비용 범위 → 동일 결과의 시간/스캔/credits/유휴비용 비교 |
| 세션 종료·재개 | gstack-context-save | 다음 세션 gstack-context-restore | 실제 상태·검증·미완료·다음 명령 기록. 저장 파일만으로 완료/재승인하지 않음 |

`gstack-benchmark`는 웹 성능용이므로 ETL 지표에 사용하지 않는다. ETL/Snowflake 성능은 pipeline benchmark와 명시 SQL 측정으로 검증한다. Git 저장은 현재 AGENTS의 승인 범위와 전담 서브에이전트 절차를 따른다. gstack-ship/land-and-deploy의 PR/병합/배포 단계는 해당 승인·완료 조건이 있을 때만 적용한다. 스킬 설치/외부 CLI/실데이터 원격 업로드를 자동 승인하지 않는다.

## 재개 체크리스트

1. [Task](../tasks/pipeline-m1.md)와 Jira KAN-28의 최신 실제 검증/게이트를 읽는다. 같은 작업의 새 티켓을 중복 생성하지 않는다.
2. `git status --short`, `git branch --show-current`로 기존 사용자 변경과 이번 브랜치를 확인한다. 다른 agent의 변경을 되돌리지 않는다.
3. [운영 안내](../pipeline.md)의 선택 의존성을 확인하고 원본 해시·입력 위치를 inventory로 다시 검증한다. 키/DB/raw/런타임은 GMS 문맥에 넣지 않는다.
4. 저장소 루트에서 `PYTHONPATH=outputs/budongi_mvp_temp/src` 및 TEMP/TMP를 쓰기 가능한 작업 폴더로 설정하고 `python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_pipeline.py -v`를 실행한다.
5. `python -m budongi.cli pipeline --root outputs/budongi_mvp_temp/data/pipeline status`와 `report`로 실제 실행을 읽는다. CLI의 성공은 해당 배치 결과이며 M1/전체 로드맵 완료가 아니다.
6. 성능 목표가 pending이면 보존한 기준선을 사용자에게 제시하고 수치·대상·허용 회귀를 확정한다. 임의 개선율을 만들지 않는다. 그 뒤 Phase 2 최적화를 이어간다.
7. 검증 뒤 문서·위키 판단/동기화 상태·Jira를 갱신하고 gstack-context-save로 다음 재개 지점을 저장한다. 미확정 목표나 미완료 게이트가 있으면 KAN-28을 완료로 옮기지 않는다.

## 2026-10-29 재개 상태와 확정 목표

66개 항목과 1,106개 입력 해시 등록, 네 대표 유형의 전체 대사(핵심 필드 불일치 0), 복구/CLI 계약 구현을 마쳤다. 상세 증거는 Task를 따른다. Phase 0~2 중 현재 실행은 승인 성능 목표의 최적화 검증이다.

사용자 확정 목표: 통계 전체 530,556셀의 worker 중앙시간 25.9134247초 → 20.73073976초 이하; 거래 XML 1만 행·학교 전체·공시가격 10만 행은 각 기준선 시간의 110% 이하; 네 유형 최대 관측 RSS는 각 기준선의 110% 이하. 모두 결과 완전 동일. 전체 거래/공시가격 성능은 추가 전체 기준선·목표 Task로 남기며 표본에서 일반화하지 않는다.

현재 PC에서 `data/pipeline/benchmarks/`에 불변 기준선 JSON과 실행 ID, `.local_runtime/pipeline-work/baselines.json`에 목록, `approved-targets.json`에 사용자 확정 근거와 비교할 두 측정 집합이 있다. `pipeline report --request .local_runtime/pipeline-work/approved-targets.json`으로 실제 산출물을 재검증한다. 파일이 없으면 Task의 최종 검증 상태를 읽고 같은 측정 범위를 재구성한다. 다음 채팅에서 예전 pending 문구만 보고 이미 확정한 수치를 다시 묻지 않는다.

후속 시작점은 최종 Task에 기록한다. M1 수용 뒤 Phase 3(DuckDB 출처별 사실/분석 Mart)의 gstack-plan-eng-review부터 이어간다. 원본 네 유형의 ETL 성공을 전체 66항목 ETL 완료로 확대하지 않는다.
