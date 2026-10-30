# TASK-PIPELINE-001 — M1 Catalog·오프라인 ETL·기준선

```toml
kind = "task"
id = "TASK-PIPELINE-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/27_pipeline_spec.md"]
scope = [".github/workflows/verify.yml", "outputs/budongi_mvp_temp/.gitignore", "outputs/budongi_mvp_temp/src/budongi/pipeline/", "outputs/budongi_mvp_temp/src/budongi/cli.py", "outputs/budongi_mvp_temp/tests/test_pipeline.py", "outputs/budongi_mvp_temp/pyproject.toml", "outputs/budongi_mvp_temp/docs/specs/27_pipeline_spec.md", "outputs/budongi_mvp_temp/docs/plans/pipeline-m1.md", "outputs/budongi_mvp_temp/docs/adr/ADR-025-analysis-pipeline.md", "outputs/budongi_mvp_temp/docs/tasks/pipeline-m1.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/pipeline.md", "outputs/budongi_mvp_temp/docs/wiki/pages/", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json"]
acs = ["PIPELINE-001-AC-01", "PIPELINE-001-AC-02", "PIPELINE-001-AC-03", "PIPELINE-001-AC-04", "PIPELINE-001-AC-05"]
```

Jira: [KAN-28](https://kwulreobeu.atlassian.net/browse/KAN-28), 진행 중 / agent-codex. 2026-10-29 사용자 구현 승인. 기존 미커밋 변경은 이 작업의 소유가 아니다.

## 완료 기준

- [x] PIPELINE-001-AC-01 메타데이터 66개·원본·개정·입력 대사
- [x] PIPELINE-001-AC-02 안전한 실행·반복·실패·게시·복구
- [x] PIPELINE-001-AC-03 대표 4종 정확성·계보·실제 대사
- [ ] PIPELINE-001-AC-04 동일조건 기준선·목표 확정·성능 검증
- [x] PIPELINE-001-AC-05 CLI·회귀·SDD·문서·위키

## 진행·검증

시작: 새 브랜치 codex/pipeline-m1-20261029. 성능 목표는 실제 기준선 이후 사용자 확정 대기. Snowflake 계정/예산과 Linux 엔진 준비는 M2/M3 후속 조건이다. 아직 실제 성능이나 M1 완료를 주장하지 않는다.

GMS 우선 경로: `harness providers`가 local_server_unavailable을 반환했고, 필요한 코드 초안만 명시한 TASK-PIPELINE-001 요청을 `gms-work --port 8786 --execute`로 시도했다. 로컬 설정 서버 연결 차단으로 count/생성은 실행하지 못했다. 키·보존 예산 우회 없이 로컬 구현으로 진행했다.

2026-10-29 후속 사용자 요청: 구현 뒤 Plan에 단계별 적합 gstack 스킬·시작/완료 조건·검증 명령·재개 체크포인트를 미리 할당해 다른 채팅에서 이어갈 수 있게 한다.

## 실제 검증 — 2026-10-29

메타데이터 lee 48 / seo 11 / kim 7 = 66개 등록 항목과 원문 워크북을 보존했다. 등록 항목 수는 거래·고유 데이터셋 수가 아니다. 명시적인 복원 경로에서 1,106개 입력 파일을 SHA-256으로 등록했다. 나머지 등록 항목 전체의 원본 확보·품질·이용조건 검수 완료를 뜻하지 않는다.

최종 코드의 `real-20261029-v2` 전체 실행과 보관 결과 대사:

| 유형 | 입력 | 수용 | 제외 | 거부 | 출력 / 실제 대사 | 불일치 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MOLIT 세 API | 384,211 | 374,892 | 9,319 | 0 | 374,892행 | 0 |
| 통계 XLSX | 3,832 원본 계열행 | 3,832 | 0 | 0 | 530,556셀 | 0 |
| NEIS JSON | 12,672 | 12,554 | 84 | 34 | 12,554행 | 0 |
| 전국 공시가격 CSV → 서울 | 15,851,336 | 2,782,147 | 13,069,189 | 0 | 2,782,147행 | 0 |

MOLIT는 모든 출력의 서비스별 원본 위치·핵심 정규화값, 통계는 모든 셀의 Decimal·결측·기간·단위·차원·source_view, 학교는 모든 수용행의 핵심 필드·위치와 118개 제외/거부 결과, 공시가격은 모든 서울 출력의 원 정수·면적·코드·이름·원본 행을 대사했다. 독립 대사는 기존 SQLite/JSONL을 읽기 전용으로 사용했다. 결과 동등성은 출처 자체의 정확성·좌표·관계 검수 승인이 아니다.

| 유형 | 최종 전체 run_id |
| --- | --- |
| MOLIT | 2b7e3120fdcc4b4e845a10d058378dd6 |
| 통계 | 1a7def6280eb421494409f1ba1b4717f |
| 학교 | 663c188beef7426b919e99b386ddeb48 |
| 공시가격 | 2da87ef637ee49f899f94f4815439fbf |

명령·근거는 현재 PC의 ignored `.local_runtime/pipeline-work/prepare_real.py`, `run_current.py`, `real-runs-v2.json`, `real-comparison-v2.json`과 `data/pipeline/outputs/<run_id>/run.json`에 있다. 다른 PC에서는 검증된 원본을 별도로 복원·위치 등록해야 한다. 이 경로의 실제 데이터와 요청은 Git에 넣지 않는다.

검사:

- `python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_pipeline.py -v`: 17개 통과. 원/Decimal·namespace·1:N·같은 배치 충돌·변조·실패 비게시·복구·worker 생존/지연 기동·CLI 0/1/2를 검증했다.
- `python -X utf8 scripts/verify_environment.py`: 제품 352개와 루트 35개 테스트, 모델 없는 합성 CLI smoke 통과. 기존 관련 34개 회귀를 포함한다. 근거 `.local_runtime/pipeline-work/environment-check-final.txt`. 첫 제한 실행의 로컬 소켓 WinError 10013은 권한을 허용한 전체 재실행에서 해소됐다.
- `python -X utf8 scripts/check_sdd.py` 및 `--base origin/main`, `git diff --check`: 통과. 이후 문서 최종 변경도 재확인한다.
- 실제 Windows 링크 생성 권한이 없어 링크 이탈 시험은 OS 링크 판정을 모의했다. 실제 junction 생성/강제 종료 OS 통합 시험과 다른 CI 플랫폼은 수행했다고 주장하지 않는다.

## 리뷰와 문서 판단

gstack-review의 native 적대적 검토에서 찾은 지역코드 검증 순서, 게시 영수증의 Catalog 해시 고정, 내부 출력 경로 링크, 살아 있는 worker와 지연 기동 경합, CLI 차단 종료코드를 수정하고 재현 회귀를 추가했다. 최종 후속 검토에서 해당 수정 범위의 추가 구체 결함은 보고되지 않았다. 같은 Codex 하네스 검토이며 외부 모델 검토가 아니다. 최초 helper 기동 실패로 저장형 gstack 리뷰의 정식 완료를 주장하지 않는다.

문서 coverage: README의 시작 링크, pipeline.md의 참조/사용법, Plan의 구조·단계·재개, Spec/ADR의 계약·결정, 이 Task의 증거를 갱신했다. 신규 GUI·릴리스 버전·배포는 없다.

위키 maintenance/catalog/ACTIVE 검색 및 지정 공간 목록 9개를 대조했다. 기존 보유 현황 DATA-CATALOG와 다른 실행 인터페이스 주제이므로 CREATE. `WIKI-A2670961AE008864` revision 1, [Confluence read-back](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/1900545), remote version 1 / SHA-256 `8afc8e251492f58f62047e7603fba90208b7439883f0dee198b968369135e68f`. 공식 연결의 read-back으로 wiki/Jira outbox receipt를 기록했고 decision `TASK-PIPELINE-001-CONTRACT-20261029`는 DONE / blocking=false다. [Jira 기록](https://kwulreobeu.atlassian.net/browse/KAN-28?focusedCommentId=10143). 문서는 로컬 기능 브랜치 계약이며 M1 완료·main 배포로 게시하지 않았다.

## 미완료와 다음 실행

성능 기준선은 현재 계측 어댑터로 동일 범위 5회씩 측정한다. 거래·공시가격의 표본과 통계·학교의 전체 범위를 구분하며 과거 미계측 코드의 속도를 소급하지 않는다. 사용자 성능 목표/허용 회귀 미확정 때문에 AC-04와 M1은 미완료, KAN-28은 진행 중이다. 다음 담당자는 Plan의 Phase 2 배정 스킬을 사용해 기준선·목표를 확정한 뒤 결과 동등성을 유지하는 최적화를 이어간다.

Snowflake/dbt/Airflow 및 나머지 유형 ETL은 후속 Task다. 계정·예산·Linux 엔진 준비, 이용조건·좌표·관계 검수와 추천 연결을 자동 완료하지 않는다.
