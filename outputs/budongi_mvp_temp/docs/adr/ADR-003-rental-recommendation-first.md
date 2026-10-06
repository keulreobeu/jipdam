# ADR-003 — 최신 전월세 추천을 제품 주 흐름으로 전환

Status: Accepted. 담당자: keulreobeu. 날짜: 2026-10-06.

관련 계약: [RENT-001](../specs/10_rental_recommendation_spec.md), [PLAN-RENT-001](../plans/rental-recommendation-mvp.md), [TASK-RENT-DOC-001](../tasks/rental-spec-transition.md). 확정 근거는 사용자의 전월세 추천 요청·D1~D15 답변과 최종 `PLEASE IMPLEMENT THIS PLAN` 요청이다. 루트 SDD ADR-003과 별개의 제품 ADR다.

## Context

기존 구현은 2023 이하 매매 중심 스냅샷·세 Tool·로컬 4B·합성 평가다. 기존 실행 계획은 역사 자료 평가 완료 뒤 최신화·검색·모델 연구를 진행하지만, 새 목표는 서울 아파트 전월세 단지 후보의 예산·생활조건 비교다. 현재 전월세·시설 적재와 추천·웹은 구현되지 않았다. 실데이터 수집·매칭 보류는 계속된다.

## Decision

- 최신 임대차 데이터 계약 → 결정적 추천·CLI → 작은 로컬 웹 비교 → 선택형 LLM 설명·제품 평가를 주 제품 순서로 삼는다. 2023 Golden 완료를 선행 조건으로 요구하지 않는다.
- 백엔드가 예산·필수 조건과 순위를 판단하고 LLM은 검증된 결과만 설명한다. 모델 없이 기본 결과가 실행되어야 한다.
- 최신 임대차의 별도 스냅샷·DB로 기존 역사 cutoff와 평가를 보존한다. 2024 이후 자료를 역사/학습 입력에 합치지 않는다.
- Python·SQLite 단일 앱에 정적 웹 입력·비교 화면을 붙인다. 현재 매물·실제 통근시간·총주거비·전세안전 판정은 첫 범위 밖이다.
- RAG·Hybrid·LoRA·모델 Router·Judge·대형 모델 비교, 매매·청약 확대는 선택형 후속 연구다. 효과가 필요한 제품 실패 사례와 별도 계약이 있을 때 재개한다.

## Alternatives

| 대안 | 판단 |
| --- | --- |
| 기존 2023 평가·연구를 먼저 완료 | 현재 실거주 추천에 필요한 최신 임대차·시설 결합을 늦추므로 제품 선행 순서에서 제외 |
| LLM이 추천 순위와 수치를 생성 | 재현 가능한 예산·조건 검증이 어려워 선택하지 않음 |
| Python API와 별도 프런트 앱 | 같은 데모에 빌드·의존성·운영 절차가 늘어 후속 선택지로 보존 |
| 현재 전월세 매물부터 추천 | 실거래 API에 없는 매물 사용권한·갱신·품절 계약이 추가되어 첫 범위에서 제외 |

## Consequences

ADR-001의 구조화 데이터 우선 원칙과 ADR-002의 단일 로컬 모델 원칙은 유지한다. 세 Tool이라는 CURRENT와 최초 FACT/FILTER/COMPARE 연구 범위를 새 추천 Tool의 TARGET와 구분한다. 기존 코드·데이터·평가 이력을 삭제하거나 과거 완료로 바꾸지 않는다.

최신 계약의 보증금·월세 쌍, 시설 커버리지와 직선거리, 출처·수집일·관측 기간이 새로운 검증 대상이다. 실제 자료 보류 중에는 합성 데모만 구현할 수 있으며, 실제 추천 품질은 사람 검수 데이터와 Golden을 확보한 뒤 별도로 평가한다. 데이터 공급자·인증·비용은 있는 것으로 가정하지 않는다.

## Verification

RENT-001-AC-11 문서 적용은 [문서 Task](../tasks/rental-spec-transition.md#doc-validation), AC-01~10 제품 검증은 [Plan](../plans/rental-recommendation-mvp.md#product-verification-pending)을 따른다. 제품 검증은 not_run이며 이 ADR 채택은 제품 구현 완료가 아니다.
