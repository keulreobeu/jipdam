# Codex 작업 프로토콜 — 집담

2026-10-13 공유 승인: 사용자의 현재 요청에 따라 PORTABLE-001/TASK-PORTABLE-001로 기존 MOLIT/제공 통계 원본의 Drive 패키지 공유·오프라인 DB 재구성과 구현 코드의 새 브랜치 푸시를 수행한다. COLLECT-001의 사전 기록/해시/개별 링크는 유지하며 새 원격 수집·키 조회·매칭 확정은 포함하지 않는다.

2026-10-13 제공 통계 파일 승인: 사용자가 이미 내려받아 제공한 30개 엑셀은 [STATS-001](docs/specs/14_statistics_storage_spec.md)·[TASK-STATS-001](docs/tasks/statistics-import.md)로 별도 `data/statistics/`에 오프라인 적재한다. 사용자 업데이트 날짜/일반 기준월 메모와 실제 파일의 기간은 구분하고 심리 dashboard/상세표 중복을 검수한다. 새 외부 수집·API·키·업로드·추천 연결은 해당 승인에 포함하지 않는다.

2026-10-13 후속 승인: [통합 후속 Plan](docs/plans/canonical-db-continuation-20261013.md)에 대한 사용자 진행 선택을 [CANONICAL-001](docs/specs/13_canonical_integration_spec.md)·[TASK-CANONICAL-001](docs/tasks/canonical-integration.md)로 추적한다. 기존 세 API 원본 기반 엔터티/공식ID근거 관계·미확정 후보·배치/버전/증분·등록 파일 입력 계약만 추가 승인한다. 후보 자동 승격·거래 병합·새출처 수집·좌표·시설·추천·Drive 업로드·Git자격증명 접근은 포함하지 않는다. 다른 보류 경계는 유지한다.

이 폴더는 진행 중인 임시 프로젝트다. 이전 저장소 `work/source_archive`는 참고 자료이며 그곳의 활성 단계·모델·성과를 이 프로젝트에 상속하지 않는다.

## 시작 순서

1. 현재 요청과 이 파일을 읽는다.
2. `docs/specs/00_project_spec.md`, `docs/specs/10_rental_recommendation_spec.md`와 관련 기능 Spec을 읽는다.
3. 관련 `docs/adr/` 및 `docs/tasks/current.md`를 읽는다.
4. 관련 코드·테스트와 `README.md`의 실제 실행 상태를 확인한다.

우선순위는 **현재 사용자의 명시적 지시 → 확정된 Spec → Accepted ADR → 검증 가능한 Acceptance Criteria/테스트 → 현재 Task → 코드 → Wiki/README**다. 충돌을 발견하면 어느 쪽이 현재 의도인지 확인하고 문서와 코드를 동기화한다. `CURRENT`는 확인된 구현, `TARGET`은 계획, `OPEN QUESTION`은 미결정 사항이다.

## 작업 루프

팀 SDD 운영은 루트 `docs/sdd.md`와 별도 템플릿을 따른다. 새 작업은 고유 Task 파일·ID로 보존하고 `current.md`에서 연결한다. 시범 등록된 Spec·Task는 TOML 메타데이터와 루트 추적 원장을 유지한다. 기본 검증은 루트 `python -X utf8 scripts/verify_environment.py`, 브랜치 변경 검사는 `python -X utf8 scripts/check_sdd.py --base origin/main`이다. baseline은 소급 승인이 아니며 verified Task도 실제 제품 평가 완료를 의미하지 않는다.

요청 → 필요한 질문·Plan → Spec 확인/갱신 → 중요한 결정이면 ADR → Task → 구현 → 관련 테스트·평가 → Acceptance Criteria 확인 → Spec과 코드의 차이 확인 → 문서 갱신.

- 워크스페이스 루트의 `.agents/skills/`에 설치된 gstack을 기본 개발 스킬로 사용한다. 먼저 `jipdam-workflow`를 읽고 요청에 맞는 기획·설계·리뷰·디버깅·QA·문서 스킬을 선택한다. 작은 수정에 전체 체인을 실행하지 않는다. gstack 결과 자체는 공식 요구사항이 아니다. 확정된 변경점만 저장소 Spec/ADR에 반영한다. 설치·확장 방법은 워크스페이스의 `docs/gstack.md`에 있다.
- 작은 버그·리팩터링은 Task와 관련 검사로 충분하다. 새 기능·Tool·계약은 Spec과 Task를, 구조·데이터 모델·Router/RAG 전략 변경은 Plan·Spec·ADR·Task를 먼저 다룬다.
- 사용자 경험, 외부 서비스·비용, 보안·개인정보, 호환성 없는 API/스키마 변경, 데이터 삭제, 되돌리기 어려운 설계 선택은 사용자와 결정한다. 함수명·내부 구조·테스트 fixture 같은 되돌리기 쉬운 구현은 작업자가 판단한다.
- 구현 중 새 제품·구조 결정이 드러나면 해당 Spec/ADR부터 갱신한다. 범위 밖 기능을 임의로 추가하지 않는다.
- 완료 보고에는 변경 사항, 실제 실행한 검사와 결과, 미완료 조건 및 다음 한 단계를 명시한다. 확인하지 않은 결과나 단계를 완료로 표시하지 않는다.

## GMS 코드 작업

2026-10-14 사용자는 등록한 GMS 키로 현재 구축 및 명확한 코드 작업을 수행하도록 승인했고 최소 5,000크레딧 보존을 지정했다. [GMS-BUDGET-001](docs/specs/18_gms_budget_spec.md)·[Plan](docs/plans/gms-budget-work.md)·[Task](docs/tasks/gms-budget-work.md)을 따른다. 사용자가 선택한 키/웹 정책과 공식 key-info 잔액·만료, 매번 입력 카운트/최대 출력 비용 예약을 적용한다. Task/AC와 필요한 src/tests/docs 문맥만 담은 JSON을 `python -X utf8 -m budongi.cli gms-work --request <작업 JSON> --execute`로 실행해 코드/테스트/기계적 문서 초안을 우선 작성한다. 기본은 견적만 조회한다. 실제 데이터/DB/raw·.env·다른 키·로그·런타임은 전송하지 않는다. 모델은 직접 셸/파일/DB/Git을 조작하지 않으며 담당자가 결과를 검토·적용·테스트한다.

정책 미설정/비활성·잔액/카운트 미확인·초과·만료는 무생성으로 이유를 보고한다. 임의 키 조회·직접 provider 호출로 예산을 우회하지 않는다. 현재 작업의 보수적 초기 상한은 전체 500크레딧/10,000토큰, 호출당 입력 4,000/출력 2,000토큰/280크레딧이다. 사용 원장은 설정 변경/재시작으로 지우지 않는다. 이 채팅 모델 자체나 부동산 추천의 로컬 LLM 경계를 전환한 것은 아니며 기존 데이터 보류는 유지한다.

## 이 프로젝트의 필수 경계

- 수집/Drive 업로드 전 [COLLECT-001](../../docs/specs/data_collection_record_spec.md)과 [수집 현황·절차](../../docs/data-collection.md)의 필수 기록을 따른다. GitHub `[수집]` Issue에서 출처·종류·지역·기간/필터가 겹치는 완료·예약 범위를 확인하고 미수집/실패분만 예약한다. ZIP 업로드 전 같은 Issue에 범위별 결과·건수·방법/단위·검수/합성·수집 시각·manifest·ZIP 해시를 적고, 업로드 후 개별 Drive 링크를 추가한다. 기록 누락 상태에서는 수집/업로드를 진행하지 않는다. 합성 fixture는 실제 수집 범위로 세지 않으며 기존 수집·매칭 보류는 유지한다.

- CURRENT에는 위 기능에 더해 RENT-001 대화형 조건 입력, loopback API, canonical에서 재생성하는 read-only 전월세 serving DB와 결과/니즈·전체 상세/지도 UI의 첫 구현이 포함된다. LLM은 확인 질문과 제한된 draft만 만들며 사용자가 수정·검색을 확정한다. 실제 추천은 확정 단지만 허용한다. 현재 canonical 전월세의 확정 연결은 0건이어서 실제 상태는 `data_not_ready`; 실제 미준비·합성 브라우저/지도·회귀를 검증했으며 실모델/실제 매칭·좌표·시설은 사용자 확인 준비 조건이다. 검색·순위의 LLM 위임, 후보 자동 확정, 거래 병합, 외부 수집·지오코딩은 금지한다. 기존 2023 Golden 완료를 최신 추천의 선행 조건으로 삼지 않는다. Router·RAG·Hybrid·LoRA는 선택형 후속 연구다.
- LLM에 SQL·DB 직접 접근·원천 수정 권한을 주지 않는다. Tool 허용 목록, 인자 검증, 호출 5회, 결과 20행, 로컬 엔드포인트 및 타임아웃 제한을 유지한다.
- `공급액(만원)`은 실거래가가 아니다. 근거 없는 가격·거리·시설·학군·전망을 생성하지 않는다. 원 단위 가격, ㎡ 면적, m 거리를 쓰고 출처 ID·기준일을 추적한다.
- 신규 전월세 API 키는 CRED-001 보관함으로 암호화해 Windows 사용자 프로필에 관리한다. Windows Credential Manager를 사용할 수 없으면 평문 fallback 없이 fail-closed한다. 키 값은 브라우저 영속 저장소·LLM·로그·응답·Git에 남기지 않는다. 폴더 삭제는 확인 뒤 그 폴더의 키 전체를 연쇄 삭제하되, 키 저장·삭제 자체로 외부 API를 호출하지 않는다. 기존 역사 CLI 환경변수는 그대로 유지한다.
- 2024년 이후 자료를 2023 역사 스냅샷이나 학습 자료에 섞지 않는다. 데이터 수집·단지 매칭은 사용자의 보류 지시가 유지되는 동안 재개하지 않는다.
- 실제 역사 스냅샷, 사람 검수 Golden, 전체 생성 사실 평가가 없으면 Phase 0~5 완료 또는 실측 성능으로 보고하지 않는다.

제품 계약·실행 순서는 `docs/specs/10_rental_recommendation_spec.md`, `docs/specs/11_api_credential_vault_spec.md`, `docs/plans/rental-recommendation-mvp.md`, `docs/tasks/current.md`를 따른다. `docs/budongi_advanced_llm_evaluation_plan.md`는 보존된 선택형 연구 계획이다. 문서 Task 완료를 제품 AC·실데이터 품질 완료로 표시하지 않는다.

2026-10-12 한정 예외: 현재 사용자의 실행 요청과 세 API 등록 완료 통보는 [MOLIT-001](docs/specs/12_molit_collection_spec.md)의 서울 25구·202510~202610 전월세/매매 일반/매매 상세 원본 수집·오프라인 관측 DB/staging·로컬 ZIP을 승인한다. [TASK-MOLIT-001](docs/tasks/molit-collection.md), Source Registry와 GitHub #5 예약을 따른다. 단지 매칭·좌표·시설·추천 연결·Drive 업로드는 별도이며 기존 역사 DB는 보존한다. 키 선택은 CRED-001의 명시적 서비스→자격증명 ID이고 별칭/폴더/종전 공급자 메타데이터로 서비스 종류를 추측하지 않는다.

2026-10-15 추가 승인: 사용자가 제공 통계의 거래량 기간과 같은 서울25구 202401~202608 아파트 전월세·매매 일반·매매 상세 수집을 요청했다. [MOLIT-001](docs/specs/12_molit_collection_spec.md)·[TASK-MOLIT-HISTORY-001](docs/tasks/molit-statistics-history.md) 및 GitHub #7을 따른다. 검증된 기존202510~202608 XML을 재사용하고 202401~202509 누락만 수집한다. 범위를 전국·다른 dataset·매칭/좌표/시설/추천·Drive 업로드로 확대하지 않는다.

2026-10-14 MVP 실행 계약: 검수 패키지의 승인 근거·검수자·시각·원본 해시가 있는 관계/좌표만 serving v2에 반영한다. 단지 ID/verified bool만으로 승격하지 않는다. Leaflet 1.9.4 로컬 자산과 OSM 타일은 사용자 승인 지도 보기 동작에 포함되며 지오코딩/시설 수집은 승인하지 않았다. 검수 패키지·실모델 미제공은 사용자 답변대로 데이터 준비 게이트로 관리한다.

2026-10-14 GMS 난이도별 선택: `difficulty=simple`→`gpt-6-luna`, `complex`→`gpt-6.1-sol`(기본). 작업 출력 상한은 정책 이내로 낮추며 동일 모델 count/생성·공통 원장·5,000 보존을 유지한다. [Task](docs/tasks/gms-model-routing.md), GMS-BUDGET-001-AC-04.

2026-10-14 최신 예산 지시: 사용자는 누적사용량 대신 잔액 5,000 보존만 관리하도록 변경했다. 현재 선택 정책은 `budget_mode=reserve_only`; 누적/호출 크레딧·누적 토큰 한도는 실행을 차단하지 않는다. 이전 500/10,000/280 한도는 초기 이력이다. 원장은 관찰 기록으로 보존하며 입력/출력의 기술적 상한·만료·사전 카운트/최대 예약/계정 정산·비밀 경계를 유지한다. `cumulative`는 이전 정책 호환 모드이며 현재 요청에 적용하지 않는다.


2026-10-15 GMS 우선 사용: 사용자는 남은 크레딧을 활용해 가능한 코드·테스트·기계적 문서 작업을 최대한 GMS로 진행하도록 지시했다. 명확한 Task/AC/범위로 작업을 묶어 단순 초안은 LUNA, 구조·보안·복합 검토는 SOL을 우선 호출하고 로컬 담당자가 검토·적용·검증한다. 현재 reserve_only의 최소 5,000 보존과 기술적·만료·비밀 경계는 유지하며 호출 횟수 자체를 목표로 삼지 않는다.

## CLI-First 자동 관리 — 2026-10-15

새 자동 작업의 App/터미널 관리 진입점은 저장소 루트 `python -m harness`다.
[운영](docs/harness/CLI_OPERATIONS.md), [Spec](docs/specs/20_cli_harness_spec.md),
[Task](docs/tasks/cli-harness.md)를 따른다. 상태 변경은 관리 CLI만 사용하고 DB를 직접 편집하지 않는다.
자연어 목표를 명시 scope/AC/검증 명령/의존성으로 정리해 등록한다. Codex 기본, GMS는 기존 예산 runner의 검토 초안이다.
HEAD 기준 worktree에는 미커밋 변경을 자동 복사하지 않는다. 검증·승인 전 결과를 완료로 표시하지 않고 자동 merge하지 않는다.

## 2026-10-15 최신 GMS/커밋 승인

현재 최소 보존은 **1,000크레딧**이며 이전5,000 지시는 이력으로 보존한다.
[TASK-HARNESS-OPS-001](docs/tasks/harness-operations.md): 기존 예산/원장을 유지한 GMS 우선 작업과 검증·승인 뒤 범위별 로컬 오토커밋을 허용한다.
Codex native GMS의 도구/stream/full-payload count 미검증·입력 상한은 우회하지 않는다. 사용자 기존 index와 범위 밖 변경을 보호한다.
