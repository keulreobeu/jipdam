# Router Spec

## CURRENT

별도 질문 Router는 없다. 단일 로컬 모델이 허용된 세 Data Tool 중 필요한 호출을 제안한다. 현재 실험 범위는 FACT/FILTER/COMPARE/NO_MATCH이며, 가상 스냅샷 스모크 결과를 실제 라우팅 정확도로 간주하지 않는다.

## TARGET

- 첫 전월세 MVP는 [RENT-001](10_rental_recommendation_spec.md)의 결정적 백엔드 추천과 선택형 단일 로컬 4B 설명을 사용한다. 별도 Router를 추가하지 않는다. 기존 실행 계획 Phase 15는 선택형 후속 연구이며 제품 선행 조건이 아니다.
- 별도 Router나 2B/4B/8B 모델 라우팅은 비교 평가에서 이득이 입증되고 사용자와 구조 결정을 마친 경우에만 도입한다.
- 향후 구조화 조회/의미 검색/Hybrid/일반 답변 분기를 도입하면 각 경로의 입력 조건, fallback, 오류 처리, 비용·지연, Golden 사례를 먼저 정의한다.

## OPEN QUESTION

- 단일 모델의 어느 실패 유형과 측정값을 별도 Router 도입 기준으로 삼을지.
- 일반 부동산 지식과 자료 기반 사실 질의를 서비스에서 어떻게 구분할지.
- Hybrid에서 두 검색이 충돌하거나 한쪽이 비어 있을 때 사용자에게 어떻게 설명할지.

## Acceptance Criteria

- 현재 코드는 별도 Router가 없음을 유지하고, Tool Calling 범위 밖 질의에 검증되지 않은 사실을 답하지 않는다.
- Router 도입 Task는 사람 검수 평가셋, 단일 모델 기준선, 정확도·p95 지연·피크 메모리·비용 비교 및 fallback 계약을 갖춘다.
