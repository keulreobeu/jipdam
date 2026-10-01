# Project Spec — 집담

상태: CURRENT와 TARGET을 분리해 관리. 기준: 2026-09-29의 저장소 코드·README·`docs/budongi_advanced_llm_evaluation_plan.md`. 이 문서는 확인되지 않은 과거 결정을 소급해 확정하지 않는다.

## 이름과 저장소

- **CURRENT**: 서비스 이름은 집담(Jipdam), 저장소는 `keulreobeu/jipdam`이다. 배포 패키지와 새 CLI는 `jipdam`, 기존 Python 모듈·CLI·작업 폴더·snapshot ID는 호환성을 위해 유지한다.

## 목적과 범위

- **TARGET**: 출처와 시점이 추적되는 부동산 정보 질의 시스템을 단계별로 만들고 검증한다. 실행 순서와 단계별 완료 조건은 [실행 계획](../budongi_advanced_llm_evaluation_plan.md)의 Phase 0~17을 따른다.
- **CURRENT**: Python/SQLite 기반 2023년 이하 스냅샷 적재 계약, 세 Data Tool, 단일 로컬 모델 Tool Calling 경로, 합성 데이터 테스트와 1차 결정적 평가기가 있다. 실제 검수된 역사 스냅샷과 약 200건 Golden은 없다.
- **CURRENT**: `outputs/budongi_mvp_temp`는 임시 작업 폴더다. 이전 Gemma 4 저장소는 출처를 밝힌 참고 자료이며 현재 구현으로 취급하지 않는다.
- **CURRENT**: 팀 공유는 워크스페이스 루트의 Git 저장소·README·설치 스크립트로 관리하며, 제품의 기존 상대 경로를 유지한다. gstack은 원본 commit을 고정해 로컬 runtime에 설치하고 Codex용 스킬만 등록한다. 계약은 [Team Environment Spec](../../../../docs/team_environment_spec.md)에 있다.
- **TARGET**: 첫 범위는 FACT/FILTER/COMPARE/NO_MATCH다. 의미 검색, Hybrid, 별도 Router, 최신화, LoRA는 초기 평가 이후 단계다.

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
- [Runtime and Container](09_runtime_spec.md): CLI 컨테이너, 영속 파일, 선택형 로컬 모델

## Acceptance Criteria

- 새 기능의 Spec은 입력·출력·오류·완료 기준을 정하고 Task가 그 Spec을 참조한다.
- 현재 구현이라고 적은 항목은 코드 또는 재현 가능한 검사로 확인할 수 있다.
- 단계 완료는 실행 계획의 조건과 실제 데이터·평가 산출물로만 판정한다.

## OPEN QUESTION

- 임시 코드의 최종 저장소 위치와 문서 이관 방식.
- 보류 중인 실제 데이터 수집·단지 매칭을 언제, 어떤 검수 체계로 재개할지.
