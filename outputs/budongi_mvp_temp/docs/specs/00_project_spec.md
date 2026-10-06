# Project Spec — 집담

상태: CURRENT는 2026-09-29 기반 구현을 보존하고 TARGET는 2026-10-06 사용자가 승인한 전월세 추천 방향을 따른다. 이 문서는 과거 승인·제품 구현·평가 완료를 소급하지 않는다.

## 이름과 저장소

- **CURRENT**: 서비스 이름은 집담(Jipdam), 저장소는 `keulreobeu/jipdam`이다. 배포 패키지와 새 CLI는 `jipdam`, 기존 Python 모듈·CLI·작업 폴더·snapshot ID는 호환성을 위해 유지한다.

## 목적과 범위

- **TARGET**: 신혼·첫집·사회초년생의 예산·직장 위치·생활시설 조건에 맞는 서울 아파트 전월세 단지 후보를 추천·비교하는 로컬 웹 데모다. 공식 계약은 [RENT-001](10_rental_recommendation_spec.md), API 키 보관함은 [CRED-001](11_api_credential_vault_spec.md), 제품 실행 순서는 [PLAN-RENT-001](../plans/rental-recommendation-mvp.md), 결정 이유는 [ADR-003](../adr/ADR-003-rental-recommendation-first.md)·[ADR-004](../adr/ADR-004-local-api-credential-vault.md)다. 기존 [LLM 실행 계획](../budongi_advanced_llm_evaluation_plan.md)은 선택형 연구로 보존한다.
- **CURRENT**: Python/SQLite 기반 2023년 이하 스냅샷 적재 계약, 세 Data Tool, 단일 로컬 모델 Tool Calling 경로, 합성 데이터 테스트와 1차 결정적 평가기가 있다. 실제 검수된 역사 스냅샷과 약 200건 Golden은 없다.
- **CURRENT**: 봉인된 합성 rental_v1 스냅샷의 결정적 추천·recommend CLI·rental-demo가 구현됐다. 실제 데이터 정규화·수집·매칭과 추천 HTTP·웹은 아직 없다.
- **CURRENT**: CRED-001의 Windows loopback API 키 설정 화면·암호화 저장·폴더/별칭 관리가 구현됐다. Windows Credential Manager에 master key를 저장하며, 실제 사용자 로그온 세션에서의 WinCred 영속 저장 통합 검증은 현재 자동 실행 환경 제약으로 미완료다. 공급자 API 호출은 연결되지 않았다.
- **CURRENT**: `outputs/budongi_mvp_temp`는 임시 작업 폴더다. 이전 Gemma 4 저장소는 출처를 밝힌 참고 자료이며 현재 구현으로 취급하지 않는다.
- **CURRENT**: 팀 공유는 워크스페이스 루트의 Git 저장소·README·설치 스크립트로 관리하며, 제품의 기존 상대 경로를 유지한다. gstack은 원본 commit을 고정해 로컬 runtime에 설치하고 Codex용 스킬만 등록한다. 계약은 [Team Environment Spec](../../../../docs/team_environment_spec.md)에 있다.
- **TARGET**: 최신 임대차 데이터 계약 → 결정적 추천·CLI → Windows Credential Manager로 암호화 키를 보호하는 로컬 API 키 보관함 → Python 단일 앱의 웹 입력·비교 → 선택형 로컬 4B 설명·제품 평가를 진행한다. 여러 공급자 키와 키별 별칭·분류 폴더를 관리하고 폴더 삭제 시 그 키들을 연쇄 삭제한다. 예산은 보증금·월세 각각, 직장·역·마트·공원·병원은 직선거리와 필수/선호로 처리한다. 현재 매물·총주거비·통근시간·전세안전 판정은 제외한다. 2023 Golden 완료는 선행 조건이 아니며 RAG·Hybrid·Router·LoRA 연구는 후순위다.

## 사용자와 시스템의 책임

- 사용자는 제품 동작, 데이터·비용·보안, 계약을 깨는 변경, 주요 구조를 결정한다.
- Planning 과정은 모호한 요구·대안·완료 조건을 정리한다. 확정된 요구는 Spec에, 채택 이유는 ADR에 기록한다.
- Codex는 승인된 범위의 Task를 구현하고 테스트·평가 결과를 근거로 보고한다.

## 현재 데이터 흐름

```text
검수된 정규화 CSV → 불변 SQLite snapshot → 검증된 Data Tool 3개
                                           ↑
질문 → 단일 로컬 모델의 Tool Calling ────────────→ 근거 기반 답변·호출 로그
```

`data/provisional/`의 조회 시점 원본과 임시 카탈로그는 역사 스냅샷이 아니다. `data/historical/`은 검수된 고정 입력과 서빙 DB, `data/eval/`은 사람 검수 Golden을 위한 위치다.

## 공통 불변 조건

1. 모델은 임의 SQL을 실행하거나 원천 데이터를 고치지 않는다.
2. 금액은 원 정수, 면적은 ㎡, 거리는 m로 다루고 출처 ID·날짜·스냅샷을 보존한다.
3. 공급액과 실거래가를 혼동하지 않는다. 없는 사실을 채워 넣지 않는다.
4. 2024년 이후 수집 자료를 2023 역사 스냅샷에 섞지 않는다.
5. 합성 데이터 실행과 실제 자료 평가를 분리해 보고한다.

## 기능별 공식 문서

- [데이터 모델](02_data_model_spec.md): 스냅샷·단위·출처 계약
- [Structured Search](03_structured_search_spec.md): 결정적 조회 경계
- [Router](04_router_spec.md): 현재 부재와 도입 결정 조건
- [RAG](05_rag_spec.md): 후속 의미 검색 범위
- [Agent Tools](06_agent_tools_spec.md): 현재 허용 도구와 호출 계약
- [평가](08_evaluation_spec.md): 테스트와 실측 판정
- [Runtime and Container](09_runtime_spec.md): 현재 CLI 컨테이너와 전월세 로컬 웹 TARGET
- [전월세 추천](10_rental_recommendation_spec.md): 승인된 RENT-001 계약, 합성 추천·CLI 구현; 실제 추천·웹 비교는 후속
- [API 키 보관함](11_api_credential_vault_spec.md): 승인된 CRED-001 계약, 설정 화면·저장소 구현 및 검증 상태
- [전환 Plan](../plans/rental-recommendation-mvp.md) / [현재 Task](../tasks/current.md): 적용 순서와 실제 완료 경계

## Acceptance Criteria

- 새 기능의 Spec은 입력·출력·오류·완료 기준을 정하고 Task가 그 Spec을 참조한다.
- 현재 구현이라고 적은 항목은 코드 또는 재현 가능한 검사로 확인할 수 있다.
- 제품 완료는 RENT-001·CRED-001 후속 Task의 실제 검증으로, 보존된 연구 Phase 완료는 기존 연구 계획의 조건으로 각각 판정한다. 합성 데모·문서 완료를 실데이터 MVP 완료로 승격하지 않는다.

## OPEN QUESTION

- 임시 코드의 최종 저장소 위치와 문서 이관 방식.
- 보류 중인 실제 데이터 수집·단지 매칭을 언제, 어떤 검수 체계로 재개할지.

## TARGET 데이터 흐름

```text
별도 검수 rental 스냅샷 → 결정적 필수 조건·선호 순위 → CLI·웹 후보 비교
                                                   → 선택형 로컬 LLM 설명
```

새 경로는 아직 미구현이다. 실수집·단지 매칭 보류를 유지하고 역사/최신 DB를 분리한다.
