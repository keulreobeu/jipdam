# Current Tasks — 전월세 제품 전환과 보존된 평가 기록

2026-10-30 [TASK-BENCH-FACILITY-001](facility-benchmark.md): KAN-31. 시설 제출 패키지 검증기·고정 독립 평가·실제 Codex Baseline/반복과 Objective 중복 제거 pilot. 실제 숫자는 [실측 보고](../harness/FACILITY_BENCHMARK.md)에 기록한다.

2026-10-30 [TASK-OBS-001](observability.md): KAN-30. 관측성 v2.3의 Codex-first shadow Usage·불변 원장·원본 과제 품질 집계 적용. [운영/적용 표](../harness/OBSERVABILITY.md). 실제 Baseline·절감률·Cloud/Claude 측정은 별도 게이트.

2026-10-29 [TASK-GIT-AUTO-001](../../../../docs/tasks/git-lifecycle.md): KAN-29. 전담 Git 서브에이전트의 단계별 저장·로컬 활성화·자동화 전용 branch 전달.

2026-10-28 [TASK-KAN8-EXISTING-001](kan8-existing-data-20261028.md): KAN-8 기존 안전·교육·의료 자료의 중복 확인과 패키지 검증; 잔여 범위·재현 검증 진행 중.

2026-10-28 [TASK-KAN9-SOURCE-001](kan9-source-review-20261028.md): KAN-9 공원·교통 기존 기록과 첫 공원 원본 후보 확인; 신규 수집 승인·예약 대기.

2026-10-28 [TASK-KAN10-EXISTING-001](kan10-existing-data-20261028.md): KAN-10 기존 단지·보행 자료 중복 및 보관본 검증 진행.

2026-10-28 [TASK-GSTACK-AGENTS-001](../../../../docs/tasks/gstack-subagents-20261028.md): KAN-25. gstack 기반 Codex 서브에이전트 역할 구성.

2026-10-26 [TASK-ENV-003](../../../../docs/tasks/environment-setup-20261026.md): KAN-24. 20261023 최신본 Windows CLI·가상환경·gstack 설치 및 누락 등록기 복구·검증.

2026-10-22 [TASK-PERSONAL-METADATA-001](personal-data-metadata-20261022.md): KAN-21. 이진호 수집·제공 원본만 4시트 메타데이터 Excel 작성. 실측/수집 이력/원본 미확보를 구분한다.

2026-10-22 [TASK-WIKI-001](wiki-lifecycle.md): KAN-19. 사용자 정책 v1.0 기반 위키 판단·갱신·상태·재검토·복구·Confluence 연동.

2026-10-21 [TASK-LEGAL-RAG-CORPUS-001](legal-rag-source-snapshot-20261021.md): KAN-13. 별도 RAG 실험용 법률·표준계약서·보증기관 원문 패키지와 출처 기록; 원문 미리보기 1차 완료, 법률 검수·semantic eval·문서별 이용조건은 미완료.

2026-10-21 [TASK-CREDENTIAL-LAUNCHER-001](../../../../docs/tasks/credential-server-launcher.md): API 키 보관함 서버 Windows EXE 실행기.

2026-10-21 [TASK-SERVER-LAUNCHER-001](../../../../docs/tasks/server-launcher.md): Windows 저장소 루트 런처로 현재 검수 serving 전월세 MVP 서버를 원클릭 실행.

2026-10-21 [TASK-AUDIT-GMS-001](audit-personal-gms-20261021.md): 현재 문서/SDD/readiness 재검증과 개인 GMS 키별 정책·자동 사용 내역. 아래 과거 GMS 5,000·만료 기록은 당시 이력이며 현재 최소 보존은1,000이다. 2026-10-20 승인 검수 serving의 연결은203,159건이고 거래 상태 unknown으로 추천 차단을 유지한다.

2026-10-20 [TASK-JIRA-AUTO-001](../../../../docs/tasks/jira-task-lifecycle.md): Codex·Claude 저장소 작업 전 Jira 이슈 생성/연결, 검증 후 완료 처리. Claude Code 공식 Atlassian MCP OAuth 설정 포함.

2026-10-14 [TASK-RENT-CONTINUE-001](continuation-parts-1to5.md): 1~5번을 목적별로 실행. 기본 canonical v3 복구·실제 prepare, 검수/모델 준비 검사, 실제 Drive 다운로드·해시와 문서/Git 정리. [Plan](../plans/continuation-parts-1to5.md), [후속 검증](../continuation-validation-20261014.md). 사용자 검수 패키지·로컬 모델은 미준비.

2026-10-14 [TASK-GMS-MODELS-001](gms-model-routing.md): simple→gpt-6-luna, complex→gpt-6.1-sol, 공식 GMS 요율·같은 모델 사전 카운트/최대 예약·공통 원장. 실제 두 모델 실행과 정수 크레딧 계정 표시를 반영한 예약 보완. 2026-10-15 최신 웹 UI의 두 모델 호출·정산과 reserve_only/5,000 보존·누적 입력 비활성을 검증해 Task는 verified다. 이후 코드·테스트·기계적 문서 작업은 GMS를 최대한 사용한다.

2026-10-14 [TASK-HARNESS-001](harness-integration.md): verified (bounded offline core), Phase 0·선택적 native 역할·Python 공통 상태/체크포인트/원장·Mock Provider. [운영](../harness/README.md). 실제 GMS·타 호스트 native는 별도 검증.

2026-10-14 [TASK-GMS-BUDGET-001](gms-budget-work.md): verified, 공식 잔액·5,000 보존·전체/호출 토큰/비용·유료 카운트 조회 비용 예약/대사·최대 생성 예약/usage 정산·GMS 코드 runner와 공통 지침. [Plan](../plans/gms-budget-work.md). 실제 GMS 코드 초안 1회 생성·검토/반영, 최종 잔여 29,845·이번 작업 차감 155, 제품194/팀SDD22·CLI/웹 검증 통과. 초기 전체 한도500 기록이며 현재는 reserve_only·5,000 보존만 적용한다. 만료 2026-10-16 18:00 KST.

2026-10-14 [TASK-GMS-001](gms-connection.md): verified, 암호화 보관함의 키 등록/교체와 별도 GMS 연결 확인·3만 크레딧 사용량/시간 계산. 합성 GMS 12개·전체 제품 166개·팀/SDD 22개·CLI 및 브라우저 계산 흐름 검증 통과. 당시의 실제 키 시험 게이트는 후속 TASK-GMS-BUDGET-001/TASK-GMS-MODELS-001의 실제 성공 증거로 해소됐다.

2026-10-13 [TASK-TEAM-DATA-001](team-data-contract.md): 3인 수집 전 공통 제출 스키마·기존 DB 호환을 확정하고 실제 매칭/좌표/도메인 매핑은 수집 후 검수로 분리. [팀 수집 가이드](../team-data-contract.md).

2026-10-13 [TASK-PORTABLE-001](data-portability.md): 기존 MOLIT/통계 원본의 Drive 보관·새 환경 DB 재구성·새 브랜치 코드 제출. 상세 상태는 [공유 검증](../shared-data-validation-20261013.md)을 따른다.

2026-10-14 [TASK-PORTABLE-DOWNLOAD-001](data-portability-download.md): Drive에 보관된 통계/MOLIT 패키지를 필요할 때 내려받아 파일별 크기·해시 검증 후 복원할 CLI. 실제 통계/MOLIT 다운로드·조각/전체 해시·CRC·기존 출력 보호 통과, verified.

```toml
kind = "task"
id = "TASK-EVAL-001"
status = "in_progress"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/08_evaluation_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/eval.py", "outputs/budongi_mvp_temp/tests/test_storage_tools.py", "outputs/budongi_mvp_temp/tests/test_required_facts.py", "outputs/budongi_mvp_temp/docs/specs/08_evaluation_spec.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["EVAL-001-AC-01", "EVAL-001-AC-02", "EVAL-001-AC-03", "EVAL-001-AC-04", "EVAL-001-AC-05", "EVAL-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/bootstrap.py --app-only"
result = "passed"
evidence = "docs/sdd/validation.md#product-evaluation"
acs = ["EVAL-001-AC-01", "EVAL-001-AC-02", "EVAL-001-AC-03", "EVAL-001-AC-04", "EVAL-001-AC-05", "EVAL-001-AC-06"]
```

Status: Required-fact coverage implemented and synthetic tests passed; actual Golden scoring remains pending.

ID는 기존 작업을 계속 추적하기 위해 부여했다. 실제 Golden의 미완료 때문에 in_progress를 유지한다. SDD 운영 체계의 완료는 루트 [TASK-SDD-001](../../../../docs/tasks/sdd-adoption.md)로 별도 관리한다. 다음 제품 작업은 새 영구 Task 파일을 만들고 이 문서에서 연결한다.

팀 공유 환경 정리는 별도 [Team Environment Task](../../../../docs/tasks/team-environment.md)에서 관리한다. 이 제품 평가 Task와 실제 Golden의 미완료 상태는 유지한다.

2026-10-06의 로컬 환경 검수 후속 작업은 [TASK-ENV-001](../../../../docs/tasks/environment-repair-20261006.md)에서 bunx 명령 연결 및 가상환경·CLI 설치를 추적한다.

2026-10-12 현재 PC의 프로젝트 환경 구성은 [TASK-ENV-002](../../../../docs/tasks/environment-setup-20261012.md)에서 프로젝트 로컬 Bun·고정 gstack·브라우저 설치 및 가상환경·CLI 검증을 추적한다.

## 전월세 제품 우선 작업

2026-10-13 제공 통계 수입: [TASK-STATS-001](statistics-import.md)에서 이전 12개+신규 18개 엑셀의 통계 전용 DB/raw 보존과 530,556셀 대사·심리 중복/파일 기준 검수를 완료했다. 통계 8개 검사 통과, 전체 검증의 기존 수집 rename 접근 오류는 [검증 기록](../statistics-validation-20261013.md)에 남겼다. 실제 거래 canonical/추천 데이터와 별도다.

2026-10-20 팀 reference 자료 수입: [TASK-TEAM-REF-001](team-reference-import-20261020.md)에서 HUG 전세보증 사고·학원·도서관·어린이보호구역 4개 ZIP의 Issue 해시/manifest를 대조하고 157,602 accepted 행을 별도 `team_reference.sqlite3`에 보존했다. `source_unverified`를 유지하며 전월세 canonical/serving·추천·좌표 매칭과 분리한다.

2026-10-06 승인된 [RENT-001](../specs/10_rental_recommendation_spec.md)·[PLAN-RENT-001](../plans/rental-recommendation-mvp.md)을 따른다. 이 파일의 TASK-EVAL-001 메타데이터와 체크·검증 이력은 그대로 보존하며, 실제 역사 Golden 미완료로 in_progress를 유지한다. 해당 연구 완료는 새 전월세 추천의 선행 조건이 아니다.

| 순서 | Task | 이번 적용 상태 |
| --- | --- | --- |
| 1 | [TASK-RENT-DOC-001 문서 전환](rental-spec-transition.md) | 문서 적용·검증 기록 참조 |
| 2 | [TASK-RENT-DATA-001 데이터 계약](rental-data-contract.md) | in_progress, 합성 저장 테스트 통과·공식 필드/단위 확인 대기 |
| 3 | [TASK-RENT-REC-001 추천·CLI](rental-recommendation-cli.md) | verified, 합성 추천·CLI AC-01~06 검증; 실제 데이터·웹 별도 |
| 4 | [TASK-CRED-001 암호화 API 키 보관함](api-credential-vault.md) | verified, 보관함·loopback 설정 화면 및 현재 Windows 사용자 세션의 합성 WinCred round-trip 검증; 실제 API 호출 제외 |
| 5 | [TASK-RENT-WEB-001 웹 비교](rental-web-demo.md) | draft, 보관함 Task 뒤에 설정 화면과 추천 비교를 통합 |
| MVP | [TASK-RENT-MVP-001 대화형 DB 추천](rental-mvp.md) | in_progress, 검수 serving v2·공통 판정·채팅/확인·니즈/100행 상세·Leaflet+OSM 구현·검증. 실제 확정 연결·실모델은 사용자 확인 준비 조건 ([최신 증거](../rental-mvp-validation-20261013.md#2026-10-14-구현-검증)) |
| 6 | [TASK-RENT-LLM-001 설명·평가](rental-explanation-evaluation.md) | draft |
| 별도 | [TASK-RENT-REAL-001 실데이터](rental-real-data.md) | in_progress, 승인된 203,159건 serving 확정 연결 완료; source status unknown으로 추천 차단, 예외 35,461건 미확정; 좌표·시설·실모델 추가 게이트 |
| 첨부 점검 | [TASK-RENT-RESTORE-001 DB 복원](rental-upload-restore-20261012.md) | verified, 첨부 합성 DB 복원·조회·수집 범위 점검; 실제 수집 자료 없음 |
| 수집 기록 | [TASK-COLLECT-001](../../../../docs/tasks/data-collection-record.md) | verified, GitHub 수집 예약·필수 요약·Drive 업로드 전 기록; 첨부 합성 배치 #3 게시 |
| 원시 수집·오프라인 DB | [TASK-MOLIT-001](molit-collection.md) | verified, 세 API 서울975 query/384,211 원본행·374,892 적재·원본 조인·재생성·ZIP 복원 및 GitHub #5 최종 기록 게시 검증; Drive 업로드는 별도 |

2026-10-15 통계 거래량 기간 정합 확장: [TASK-MOLIT-HISTORY-001](molit-statistics-history.md)은 verified다. 서울25구 202401~202608 총 2,400 query 중 #5의 겹치는 825건을 검증·재사용하고 1,575건을 새로 수집했다. 전월세 685,575행·매매 일반 192,142행·매매 상세 192,142행, 무결성/FK/원본 lineage 대사 통과. 최종 로컬 ZIP SHA-256은 `5c929e5869c17075810ba24eca5ca2c71227df643416e08464112760ac6f91e6`; Drive 업로드는 미실행. [완료 검증](../molit-statistics-history-validation-20261015.md).

2026-10-13 Goal 재개: 기존 ZIP을 새 경로에 복원해975query·원본/DB 해시·건수·무결성을 재확인했다. [재개 증거](../molit-resume-validation-20261013.md)와 사용자가 승인한 [통합 후속 계획](../plans/canonical-db-continuation-20261013.md)을 따른다. 새 수집·좌표·시설·추천·Drive 업로드는 포함하지 않는다.

후속 통합 [TASK-CANONICAL-001](canonical-integration.md)은 verified다. 실제 전체 관측·원본 조인·재실행·확대 증분·v3 사본의 전체 값 보존, 등록 파일 형식·CLI 계약, 최종 환경/SDD를 검증했다. [CANONICAL-001](../specs/13_canonical_integration_spec.md)·ADR-006과 [완료 감사](../canonical-validation-20261013.md#goal-completion-audit)를 따른다. 추천·좌표·시설·Golden·Drive 업로드의 별도 상태는 유지한다.

합성 추천·CLI의 AC-01~06은 추천 Task 검증을 따른다. TASK-RENT-MVP-001에서 canonical serving/API·채팅 확인 폼·니즈/전체 상세·내장 지도와 합성 성공/타일 장애/모바일 브라우저 경로를 검증했다. TASK-RENT-REAL-001에서 사용자는 2026-10-20 동일 aptSeq·구·단지명·법정동·지번의 유일 일치 203,159건을 승인하고 예외 35,461건은 미확정으로 남겼다. 원천 취소/정정 상태는 확인 전까지 unknown으로 보존하며 추천을 차단한다. 좌표·시설과 실모델 검증도 미완료다. [사람 검수 및 적용 기록](../rental-identity-review-20261020.md)을 따른다. GMS 코드 초안 활용 및 최신 앱 199개/팀 22개 검사 결과는 [최종 기록](../rental-mvp-validation-20261013.md#2026-10-14-최종-재검증)을 따른다. CRED-001의 OS 저장소 검증은 해당 Task의 실제 기록을 따른다. 문서 완료·합성 성공을 실제 추천 품질로 승격하지 않는다.

보관함 구현의 후속 검증·수정은 [TASK-CRED-QA-001](credential-vault-qa.md)에서 추적한다. 키 비노출·요청 처리·삭제 재확인·수정 창 취소의 회귀 검증이며 실제 API 호출은 포함하지 않는다.

보관함의 폴더와 제공자 구분, 저장 후 제공자 변경은 [TASK-CRED-PROVIDER-001](credential-provider-edit.md)에서 추적한다.

2026-10-12 사용자 요청에 따른 별칭·폴더 중심 관리와 폴더 이동은 [TASK-CRED-ALIAS-001](credential-alias-only.md)에서 추적한다. 화면의 연결 API 선택 목록을 대체하며 기존 키의 암호문 호환성을 유지한다.

Windows CI 동시성 테스트의 차단 해결은 [TASK-CRED-CI-001](credential-vault-ci.md)에서 추적한다.

## Goal

Evaluate each Golden `required_facts` item against its generated answer deterministically, report matched/missing/unmeasured facts without treating unsupported formats as success, and keep full claim precision distinct from required fact coverage.

## Related Spec

- `docs/specs/08_evaluation_spec.md`
- `docs/specs/06_agent_tools_spec.md`
- `docs/budongi_advanced_llm_evaluation_plan.md` (Golden schema)

## Fact contract

- String values use normalized exact substring matching. ISO dates also accept `YYYY년 M월 D일` and `YYYY.M.D` forms.
- Numeric values require a `unit`, then use exact decimal comparison with the Golden tolerance. The answer must contain the same unit or a documented alias (`m`/`미터`, `㎡`/`m²`/`제곱미터`, `원`/`만원`/`억 원` conversions, `년`).
- Each fact is checked only in a sentence containing its `entity_aliases`; if omitted, the canonical `entity` ID is the default alias. Aliases should list user-facing apartment names when answers use names instead of IDs.
- Missing answer claim is `missing`; unknown type, unsupported/missing numeric unit, null value, malformed tolerance/aliases, or absent `required_facts` is `not_measured`.
- Per-question status passes only when all required facts are scorable and matched; any missing fact fails; otherwise status is not measured.

## Acceptance Criteria

- [x] EVAL-001-AC-01 Numeric facts respect units and tolerance.
- [x] EVAL-001-AC-02 Text/date facts match documented normalization.
- [x] EVAL-001-AC-03 Facts require entity/alias context in the same answer sentence.
- [x] EVAL-001-AC-04 Missing/malformed facts and absent predictions do not become false passes.
- [x] EVAL-001-AC-05 Coverage excludes unmeasured facts and exposes counts and reproducible CSV evidence.
- [x] EVAL-001-AC-06 Existing metrics remain available; full claim precision and actual-data/Phase readiness remain unclaimed.

확인 명령·결과와 집중 테스트는 루트 [SDD 검증 기록](../../../../docs/sdd/validation.md#product-evaluation)에 연결한다. 실제 Golden 평가는 별도 미완료 조건이다.

## 2026-10-15 CLI-First 하네스

[TASK-CLI-HARNESS-001](cli-harness.md): 첨부 계획 실행·독립 Codex CLI 설치·App 관리 CLI·영속 worker·격리/복구·GMS 초안 adapter 검증.
기존 TASK-HARNESS-001 native/manual 계약을 보존하며 별도 managed runtime을 추가한다.

## 2026-10-15 GMS·오토커밋 후속

[TASK-HARNESS-OPS-001](harness-operations.md): 현재 GMS 보존1,000, native Codex gateway 호환성 점검, 전용 브랜치와 검증 후 자동 로컬 커밋.

2026-10-21 [TASK-PARK-RAG-GATEWAY-001](park-rag-gateway.md): KAN-18, 서울 공원 RAG GMS 키 보관함 generation과 Seoul Open Data 프록시.


2026-10-22 [TASK-DATA-CATALOG-001](data-catalog.md): KAN-20. 수집·통합·통계·법률 원문 데이터의 상태와 활용 가이드.

공유 위키 검토 대기 복구는 [TASK-WIKI-RECOVERY-001](wiki-review-recovery-20261028.md) / KAN-26에서 검증했다.
[TASK-WINDOWS-SNAPSHOT-001](windows-snapshot-publication-20261028.md): KAN-27 Windows 스냅샷 게시 접근 거부 조사·복구 (진행 중).

2026-10-29 [TASK-PIPELINE-001](pipeline-m1.md) / Jira KAN-28: 66개 메타데이터 Catalog·대표 4종 오프라인 ETL·계보·성능 기준선 구현. 전체 구조/단계별 gstack 스킬/다른 채팅 재개 절차는 [Plan](../plans/pipeline-m1.md). 사용자 성능 목표 확정 전 M1 완료 금지.

2026-10-30 [TASK-META-INTEGRATE-001](metadata-integration-20261030.md) / KAN-32: 4인 75항목 통합 메타데이터·수집자 검증 Jira·DB/PK 설계. [설계·분담](../metadata-db-design.md) / [재개·스킬](../plans/metadata-integration-20261030.md).
