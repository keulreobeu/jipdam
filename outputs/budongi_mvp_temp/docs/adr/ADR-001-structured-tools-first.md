# ADR-001 — Structured Data Tool을 초기 경로로 사용

Status: Accepted for current MVP (2026-09-29 문서화). 근거: `docs/budongi_advanced_llm_evaluation_plan.md`의 Phase 0~8과 현재 `src/budongi/tools.py`. 이 기록은 과거 회의의 결정 이유를 추정하지 않는다.

## Context

지역·가격·면적·계약일 같은 정확 조건과 실거래 수치는 출처·시점이 명확해야 한다. 현재 임시 MVP에는 의미 검색 인덱스나 검수된 실제 역사 스냅샷이 없다.

## Decision

초기 FACT/FILTER/COMPARE는 검증된 세 Data Tool과 파라미터화된 SQL을 사용한다. 의미 검색·Hybrid는 Structured 경로의 실제 평가 뒤 별도 단계에서 결정한다.

## Reason

명시 조건과 숫자를 결정적으로 검증하고, 원천 ID·날짜·snapshot을 함께 반환할 수 있다. 현 계획의 단계별 실험 순서와 일치한다.

## Alternatives

- Vector 검색으로 모든 질의를 처리: 명시 조건의 정확성·재현성 요구에 맞지 않는다.
- 초기부터 Structured + RAG 결합: 현재 문서 집합과 평가 기준이 없어 효과를 검증할 수 없다.

## Consequences

초기 설명형·비정형 문서 질의는 지원 범위 밖이다. 향후 의미 검색을 넣을 때 검색 계약과 Golden, 지연·자원 비용을 따로 측정해야 한다.
