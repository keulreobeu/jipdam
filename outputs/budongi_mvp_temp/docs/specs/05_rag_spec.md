# RAG Spec

## CURRENT

이 임시 MVP에는 의미 검색 인덱스, `semantic_search`, Hybrid RAG가 없다. 이전 Gemma 4 프로젝트의 RAG 자산과 성과를 현재 구현으로 취급하지 않는다.

## TARGET

- [RENT-001](10_rental_recommendation_spec.md)의 첫 전월세 추천에는 RAG·Hybrid를 추가하지 않는다. 기존 실행 계획 Phase 7의 청약 제도·용어·공공 문서 의미 검색은 선택형 후속 연구로 보존하며 제품 선행 조건이 아니다.
- 지역·가격·면적·계약일 같은 정확 조건은 Structured Search가 담당한다. Hybrid가 필요하면 구조화 후보를 먼저 좁히고 관련 문서를 검색한다.
- 검색 결과는 문서/단지/거래 ID, 날짜, 출처, 순위·점수를 유지하며 답변은 근거가 있는 내용만 말한다.
- 채택 전 동일 Golden에서 Structured only, 의미 검색, 결합, 재정렬을 비교하고 Recall/MRR, 사실성, 지연·자원 사용량을 평가한다.

## OPEN QUESTION

- 어떤 검수된 문서 집합과 버전을 인덱싱할지, 갱신·삭제 규칙은 무엇인지.
- 구조화 사실과 문서 설명이 충돌할 때 우선순위와 사용자 표시 방식.
- Hybrid의 재정렬·Top-K·타임아웃·fallback 및 평가 기준.

## Acceptance Criteria

- 현재 단계에서는 RAG 결과나 지표를 주장하지 않는다.
- 도입 Task는 자료 출처, 인덱스 버전, 검색 계약, 평가셋과 측정 기준을 먼저 확정한다.
