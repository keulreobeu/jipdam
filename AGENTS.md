# Codex workspace — 집담

2026-10-13 공유 승인: 현재 사용자의 GitHub 브랜치 푸시·DB 원본 Drive 보관/재구성 요청은 PORTABLE-001/TASK-PORTABLE-001의 기존 MOLIT/제공 통계 원본 패키지 업로드와 코드의 새 브랜치 제출을 승인한다. 수집 Issue의 사전 결과/최종 ZIP 해시·후속 개별 링크 기록은 유지한다. 새 원격 수집·키 조회·매칭 확정 승인은 아니다.

현재 개발 대상은 `outputs/budongi_mvp_temp/`다. 작업 전에 그 폴더의 `AGENTS.md`와 관련 Spec·ADR·Task를 읽는다. `work/source_archive/`는 이전 프로젝트의 참고 자료다.

이 파일과 개발 폴더의 `AGENTS.md`는 AI 도구에 관계없이 공통 계약이다. Claude Code는 루트 `CLAUDE.md`가 두 파일을 import하고, Antigravity는 `AGENTS.md`를 프로젝트 규칙으로 사용한다. 아래 전체 gstack 자동 등록은 현재 Codex용이다. 다른 host의 네이티브 스킬 등록·실행은 지원된다고 가정하지 않으며 공통 개발·검증 진입점은 루트 README를 따른다.

## 기본 스킬

SDD 운영과 문서·Task·검증 계약은 [docs/sdd.md](docs/sdd.md)를 따른다. 코드·설정·계약 변경은 같은 변경에서 갱신한 영구 Task와 연결한다. 새 제품 요구는 사용자, 세부 구현과 AC별 증거 기반 완료는 담당자가 책임진다. `python -X utf8 scripts/verify_environment.py`는 SDD 검사도 실행한다. 기존 문서는 시범 적용 범위 밖까지 일괄 승인·전환하지 않는다.

이 프로젝트는 [gstack](https://github.com/garrytan/gstack)을 기본 개발 스킬로 사용한다. Codex용 스킬은 루트 `.agents/skills/gstack-*/SKILL.md`, router는 `.agents/skills/gstack/SKILL.md`에 있다. 원본·템플릿·런타임은 스킬 탐색 경로 밖의 `.local_runtime/tooling/.agents/skills/gstack/`에 있다. 요청에 필요한 Codex용 스킬만 읽는다. 원본과 fixture의 SKILL.md를 호출하지 않는다.

- 모호한 제품 요청: `gstack-office-hours`, 필요하면 `gstack-plan-ceo-review`.
- 구현 계획·구조·데이터 계약: `gstack-plan-eng-review`.
- 코드 검토: `gstack-review`. 버그 원인 조사: `gstack-investigate`.
- 동작 검증: `gstack-qa` 또는 읽기 전용 `gstack-qa-only`. 현재 프로젝트는 CLI/API 경로를 우선 검증한다.
- 문서 동기화: `gstack-document-release`, 새로운 사용 문서: `gstack-document-generate`.
- UI가 생기면 디자인·브라우저 관련 스킬을 사용한다. 릴리스·배포 요청에는 해당 스킬을 사용한다.

작은 수정에 전체 기획·리뷰 체인을 의무화하지 않는다. gstack의 계획·리뷰 결과는 초안이며 확정된 요구는 프로젝트 Spec, 결정 이유는 ADR, 실행 단위는 Task에 기록한다. 현재 사용자 요청과 프로젝트 데이터·평가 경계를 유지한다.

스킬 사용 전 집담 전용 `jipdam-workflow`를 읽는다. 등록된 스킬의 preamble은 현재 경로에서 상위 `tooling/gstack.lock.json`을 찾아 프로젝트 런타임 환경을 설정한다. 직접 helper를 실행할 때는 루트에서 다음을 현재 셸에 적용한다. Windows에서는 Git for Windows의 Bash를 사용하고 WSL의 `bash.exe`와 혼동하지 않는다.

```powershell
. ./scripts/enter-gstack.ps1
```

Bash에서는 `source scripts/enter-gstack.sh`를 사용한다. 스킬이 없으면 루트 README의 `python scripts/bootstrap.py`로 설치한다. 단순 제품 수정에 gstack 전체 재설치를 반복하지 않는다.

gstack이 제안하는 GitHub issue 작성, push/PR/merge/배포, 외부 CLI 리뷰, 자동화·원격 동기화는 현재 요청이 해당 동작을 포함할 때만 실행한다. 원격·인증·실데이터를 있는 것으로 가정하지 않는다. 브라우저 QA를 위해 실제 데이터 수집 보류를 해제하지 않는다.

## GMS 코드 작업 — 2026-10-14 승인

사용자는 등록한 GMS 키를 현재 구축 및 이후의 명확한 코드 작성 작업에 사용하도록 승인했고 최소 **5,000크레딧 보존**을 지정했다. [GMS-BUDGET-001](outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md)·[Plan](outputs/budongi_mvp_temp/docs/plans/gms-budget-work.md)·[Task](outputs/budongi_mvp_temp/docs/tasks/gms-budget-work.md)을 따른다. 보관함에 명시적으로 선택·저장한 정책을 사용하며 별칭/폴더에서 키를 추측하지 않는다.

명확한 Task/AC/수정 범위가 있는 코드·테스트·기계적 문서 초안은 정책이 활성이고 실잔액·만료·사전 입력 카운트·최대 비용 예약을 통과하면 `python -X utf8 -m budongi.cli gms-work --request <작업 JSON> --execute`를 우선 사용한다. 기본 명령은 견적만 조회한다. 요청 JSON의 files는 현재 제품 src/tests/docs의 필요한 코드·문서만 지정한다. 원본 DB/raw·실데이터·다른 키·로그·.env·런타임을 보내지 않는다. 모델 결과는 로컬 담당자가 검토·적용·검증하며 모델에 셸/파일/SQL/Git 실행을 맡기지 않는다.

키와 예산을 직접 환경변수/별도 provider로 우회하지 않는다. 예산 부족·정책 비활성·카운트/잔액 미확인·만료이면 GMS를 호출하지 않고 이유를 기록한다. 현재 Codex 채팅 모델 자체가 GMS로 전환된 것은 아니다. 현재 구축은 보수적인 전체 500크레딧·전체 10,000토큰·호출당 입력 4,000/출력 2,000토큰·최대 280크레딧 한도로 시작했고 웹에서 사용자가 변경한다. 전체 사용 원장은 변경/재시작으로 초기화하지 않는다. 새 수집/매칭/업로드의 승인을 포함하지 않는다.

## 데이터 수집·Drive 업로드 기록 (필수)

[수집 현황·절차](docs/data-collection.md)와 [COLLECT-001](docs/specs/data_collection_record_spec.md)을 따른다. 데이터 수집 전 GitHub의 `[수집]` Issue에서 완료·닫힌 기록과 예약·진행 범위를 검색하고 출처/종류/지역/기간·필터가 겹치는 범위를 제외한 뒤 담당자와 범위를 예약한다. 동시 예약은 재확인하고 중복 담당을 정리한 뒤 시작한다. ZIP을 공유 Drive에 올리기 전 같은 Issue에 실제 성공/0건/실패 범위·건수·방법·단위/가공·검수/합성 구분·수집 시각·manifest·최종 ZIP SHA-256을 반드시 기록한다. 기록이 없으면 수집/업로드를 진행하지 않는다. 업로드 뒤 개별 파일 링크를 추가한다. 원본·ZIP·DB·API 키는 Git에 넣지 않는다. 기존 실수집·매칭 보류는 별도 해제 전까지 유지한다.

## 확장과 업데이트

공통 프로젝트 규칙은 이 파일과 개발 폴더의 `AGENTS.md`, 집담 전용 절차는 추적되는 `.agents/skills/jipdam-workflow/`에서 발전시킨다. 일반화할 만한 gstack 변경은 runtime 원본의 해당 `SKILL.md.tmpl`에서 수정하고 `python scripts/bootstrap.py`로 재생성한다. 팀 공유에는 그 변경을 별도 fork commit에 보존하고 `tooling/gstack.lock.json`의 repository/commit/version을 함께 갱신한다. 생성된 `gstack-*/SKILL.md`를 직접 수정하면 재설치 때 사라진다. setup의 마지막 등록 단계는 Codex용 router·스킬 ID·팀 runtime 경로를 적용하고 fixture 스킬 유출을 검사한다.

업데이트 전에 원본의 diff와 로컬 수정을 확인하고 커밋 또는 패치로 보존한다. 자동 업데이트는 사용하지 않는다. 설치·사용·확장 경로는 `docs/gstack.md`를 참고한다.

## 현재 제품 방향 — 2026-10-06 승인, 2026-10-13 MVP 확장

[RENT-001](outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md)과 [전환 Plan](outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md)을 따른다. MVP는 서울 아파트 전월세 채팅·선택적 로컬 LLM 후속 질문·실제 canonical DB read-only 추천·니즈/전체 상세 화면과 지도다. 백엔드가 조건·순위를 계산하고 LLM은 조건 질문/구조화 초안만 제공한다. 사용자는 초안을 확인·수정한 뒤 검색한다. 실제 추천은 사용자가 확정 매칭 단지만 허용했으며 pending 후보 자동 확정·거래 병합은 금지다. 현재 전월세 확정 연결 0건이므로 `data_not_ready`가 정상 결과다. 좌표는 명시적 검수 상태와 WGS84 범위 확인이 있을 때만 노출한다. 기존 역사 DB·세 Tool·평가 CURRENT를 보존하고 실제 데이터 경계와 새 수집/좌표/시설 승인 조건은 유지한다. 2023 연구 완료를 선행 조건으로 삼지 않는다. 매매·청약 확대와 RAG/Hybrid/LoRA/다중 모델 연구는 첫 제품 우선순위에서 제외한다. 구현 상태·성능·미완료 게이트는 [TASK-RENT-MVP-001](outputs/budongi_mvp_temp/docs/tasks/rental-mvp.md)과 [검증 기록](outputs/budongi_mvp_temp/docs/rental-mvp-validation-20261013.md)을 따른다.

## 원시 데이터 수집의 한정 승인 — 2026-10-12

2026-10-13 제공 통계 파일 예외: 사용자가 Downloads의 이전 12개+신규 18개 엑셀을 함께 저장하고 통계 전용 DB를 만들도록 요청했다. [STATS-001](outputs/budongi_mvp_temp/docs/specs/14_statistics_storage_spec.md)·[TASK-STATS-001](outputs/budongi_mvp_temp/docs/tasks/statistics-import.md)의 제공 파일 원본 보존/오프라인 통계 적재/중복 대사와 사용자 업데이트 메타데이터 기록을 승인한다. 새 외부 수집·API/키 접근·Drive/GitHub 업로드·추천 연결을 포함하지 않는다.

2026-10-13 후속 한정 승인: 사용자가 [통합 후속 Plan](outputs/budongi_mvp_temp/docs/plans/canonical-db-continuation-20261013.md) 진행을 선택했다. [CANONICAL-001](outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md)·[TASK-CANONICAL-001](outputs/budongi_mvp_temp/docs/tasks/canonical-integration.md)의 기존 세 API 원본 기반 공통 엔터티/공식 출처 ID 관계/미확정 후보/반복·증분·버전/등록 파일 입력 계약 구현·검증을 승인한다. 후보 자동 확정/거래 병합은 금지한다. 새 실제 출처 수집·좌표·시설·추천·Drive 업로드·별도 Git 자격증명 접근은 승인하지 않는다. 이 예외는 아래2026-10-12보류 중 공식 ID 관계와 미확정 후보에만 추가 적용한다.

현재 사용자의 세 API 계획 검토·보완 후 진행 요청과 API 등록 완료 통보에 따라 [MOLIT-001](outputs/budongi_mvp_temp/docs/specs/12_molit_collection_spec.md)의 서울 25구·202510~202610 전월세/매매 일반/매매 상세 원본 수집·오프라인 정규화·관측 DB·staging·로컬 ZIP만 수집 보류에서 해제했다. Source Registry와 [TASK-MOLIT-001](outputs/budongi_mvp_temp/docs/tasks/molit-collection.md)로 범위·증거를 추적한다. 기존 완료 원본은 검증 후 재사용하고 GitHub #5 예약을 이어서 사용한다. 다른 데이터셋·단지 매칭·좌표·시설·추천 연결·Drive 업로드의 보류/별도 승인 경계는 유지한다. 이 첫 단계 성공은 통합 DB Goal 전체 완료가 아니다.

2026-10-15 추가 사용자 승인: 통계 거래량 자료와 같은 기간의 서울25구 아파트 실거래/전월세 범위를 202401~202608로 확장한다. [TASK-MOLIT-HISTORY-001](outputs/budongi_mvp_temp/docs/tasks/molit-statistics-history.md)와 GitHub #7을 따른다. 기존 202510~202608의 완료 원본은 검증·재사용하며 202401~202509의 누락 query만 수집한다. 전국 확대·새 dataset·매칭·좌표·시설·추천 연결·Drive 업로드는 포함하지 않는다.

2026-10-14 MVP 실행 계약: 검수 패키지의 승인 근거·검수자·시각·원본 해시가 있는 관계/좌표만 serving v2에 반영한다. 단지 ID/verified bool만으로 승격하지 않는다. Leaflet 1.9.4 로컬 자산과 OSM 타일은 사용자 승인 지도 보기 동작에 포함되며 지오코딩/시설 수집은 승인하지 않았다. 검수 패키지·실모델 미제공은 사용자 답변대로 데이터 준비 게이트로 관리한다.

2026-10-14 GMS 모델 선택 추가 승인: 작업 JSON의 `difficulty=simple`은 `gpt-6-luna`(6.0 LUNA), `complex`는 `gpt-6.1-sol`이다. 누락은 기존 SOL. 명시 model은 두 ID만 허용하고 난이도 충돌은 무통신 거부한다. 작업 `max_output_tokens`는 저장 정책 이내로만 낮출 수 있다. 모델별 공식 GMS 요율·동일 모델 입력 카운트·정수 크레딧 최대 예약·공통 누적 원장/5,000 보존을 사용한다. Task/AC: [TASK-GMS-MODELS-001](outputs/budongi_mvp_temp/docs/tasks/gms-model-routing.md) / GMS-BUDGET-001-AC-04. 과거 사용/위반 이력은 지우지 않는다.

2026-10-14 최신 예산 지시: 사용자는 누적사용량 대신 잔액 5,000 보존만 관리하도록 변경했다. 현재 선택 정책은 `budget_mode=reserve_only`; 누적/호출 크레딧·누적 토큰 한도는 실행을 차단하지 않는다. 이전 500/10,000/280 한도는 초기 이력이다. 원장은 관찰 기록으로 보존하며 입력/출력의 기술적 상한·만료·사전 카운트/최대 예약/계정 정산·비밀 경계를 유지한다. `cumulative`는 이전 정책 호환 모드이며 현재 요청에 적용하지 않는다.


2026-10-15 GMS 우선 사용: 사용자는 남은 크레딧을 활용해 가능한 코드·테스트·기계적 문서 작업을 최대한 GMS로 진행하도록 지시했다. 명확한 Task/AC/범위로 작업을 묶어 단순 초안은 LUNA, 구조·보안·복합 검토는 SOL을 우선 호출하고 로컬 담당자가 검토·적용·검증한다. 현재 reserve_only의 최소 5,000 보존과 기술적·만료·비밀 경계는 유지하며 호출 횟수 자체를 목표로 삼지 않는다.

## CLI-First 관리 하네스 — 2026-10-15

현재 사용자가 승인한 자동 CLI 실행/상태 관리 요청은 `python -m harness`를 사용한다.
[운영 계약](outputs/budongi_mvp_temp/docs/harness/CLI_OPERATIONS.md)과
[TASK-CLI-HARNESS-001](outputs/budongi_mvp_temp/docs/tasks/cli-harness.md)을 먼저 읽는다.
App은 자연어 목표를 scope/AC/검증 명령으로 정리하고 new-task/run/status/report/pause/resume/cancel/retry/approve/provider/priority를 명시 실행한다.
기존 scripts/agent_harness.py는 수동/native 역할 인계용이다. worker의 detached worktree를 App에서 동시에 편집하지 않는다.
GMS는 기존 선택 보관함/예산 runner만 사용하며 초안은 수동 적용/validate/approve를 거친다. 원격 push/merge/수집은 이 관리 요청에 포함되지 않는다.

## GMS와 자동 커밋 최신 지시 — 2026-10-15

사용자는 현재 대화에서 GMS 최소 보존을 **1,000크레딧**으로 변경했고 새 브랜치·검증 후 로컬 오토커밋을 승인했다.
[HARNESS-OPS-001](outputs/budongi_mvp_temp/docs/specs/21_harness_operations_spec.md)과
[TASK-HARNESS-OPS-001](outputs/budongi_mvp_temp/docs/tasks/harness-operations.md)을 따른다. 이전5,000은 이력이다.
기존 선택 키/공통 원장/사전 count/최대 예약/만료·기술 상한을 유지하며 GMS 코드·테스트·문서 초안을 우선 사용한다.
Codex native GMS는 전체 Responses·도구·스트림·예산 호환이 검증됐을 때만 사용한다. 키를 CLI에 직접 넣어 예산을 우회하지 않는다.
오토커밋은 검증·필요 승인 후 허용 범위만 codex/ 브랜치에 기록하고 push/merge/amend/reset은 하지 않는다.
