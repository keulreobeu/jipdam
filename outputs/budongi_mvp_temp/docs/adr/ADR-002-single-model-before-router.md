# ADR-002 — 첫 Tool Calling MVP는 단일 모델로 검증

Status: Accepted for current MVP (2026-09-29 문서화). 근거: `docs/budongi_advanced_llm_evaluation_plan.md` Phase 2·15와 현재 `src/budongi/agent.py`.

## Context

별도 Router나 다중 모델을 넣기 전 Tool 선택·인자·조회·답변 각각의 실패를 측정해야 한다. 현재 실제 Golden이 없으므로 추가 구조의 이득을 입증할 수 없다.

## Decision

첫 MVP는 단일 로컬 4B급 모델의 제한된 Tool Calling을 사용한다. 별도 Router·모델 라우팅은 후속 비교 평가와 사용자 결정 뒤 도입한다.

## Reason

한 경로의 실패 지점을 먼저 확인할 수 있고 비교 기준선을 만든다. 추가 모델의 지연·메모리·운영 복잡성을 측정 전부터 떠안지 않는다.

## Alternatives

- 규칙 기반 질문 Router를 즉시 추가.
- 질의별 2B/4B/8B 모델 라우팅을 즉시 추가.

## Consequences

현재는 단일 모델의 Tool 선택 오류가 그대로 품질에 영향을 준다. 도입 여부는 같은 평가셋에서 정확도·p95 지연·메모리를 비교해 판단한다.
