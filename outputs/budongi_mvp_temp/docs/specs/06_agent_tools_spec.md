# Agent Tools Spec

## CURRENT — 허용 도구

| Tool | 입력 | 출력 | 사용 시점 |
| --- | --- | --- | --- |
| `search_apartments` | 지역, 최고 거래가(원), 면적(㎡), 최소 준공연도, 최대 행 수 | 단지와 최신 유효 거래 | 명시된 단지 조건 검색 |
| `search_transactions` | 단지 ID, 계약일 범위, 최고 거래가, 면적, 최대 행 수 | 유효 거래 기록 | 특정 거래 사실 확인 |
| `get_apartment_detail` | 필수 단지 ID | 단지·위치·최신 유효 거래 | 알려진 단지 상세 조회 |

정확한 JSON 인자 이름·범위는 `src/budongi/tools.py`의 `TOOL_SPECS`와 `_validate`가 실행 계약이다. 모든 결과에 snapshot 메타·행 수가 포함된다. 결과 행은 가능한 경우 원천·원천 ID·효력일을 포함한다. 빈 결과는 빈 행 목록으로 반환한다. 알 수 없는 Tool/인자, 잘못된 타입·범위, 없는 snapshot은 오류다.

## 실행 경계

- 모델은 로컬 HTTP 엔드포인트만 사용한다. SQL이나 DB 연결을 모델에 노출하지 않는다.
- 한 질문당 최대 5회 호출, 각 조회 최대 20행, 기본 모델 HTTP 타임아웃 30초다.
- 호출 로그에는 제안·검증 인자, 상태, 소요 시간, 행 수, 반환 ID, snapshot ID를 남긴다.
- 도구 오류와 호출 한도 초과 시 확인되지 않은 답변을 내지 않는다. 성공한 Tool 결과가 있으면 가격·ISO 날짜와 명시적인 `단지 ID:`, `거래 ID:`, `출처: source/source_id` claim을 대조한다. 하나라도 지원되지 않으면 원 답변을 검증된 Tool 요약으로 대체하고 유형별 claim을 기록한다.
- 이 검사는 검출 가능한 구조화 claim의 근거 일치만 확인한다. 자유 서술 전체의 사실 완전성·누락 여부와 비구조화 주장을 보증하지 않는다.

## CURRENT / TARGET / OPEN QUESTION

- **CURRENT**: `answer_grounding_v2`가 가격·ISO 날짜·명시 ID·출처 쌍의 근거 일치를 기록한다. 실패 답변은 안전 요약으로 교체된다.
- **CURRENT 합성 백엔드**: [RENT-001](10_rental_recommendation_spec.md)의 recommend_rentals는 별도 RENTAL_ALLOWED_TOOLS에서 하나의 읽기 전용 호출로 구현했다. 기존 LLM agent에는 연결하지 않았다. **TARGET**: 후속 LLM Task에서 전월세 Tool schema·인자·설명 검증과 호출 제한을 연결한다. 지금의 세 Tool·인자·CLI는 보존한다. 백엔드가 후보·순위·기본 설명을 결정하며 선택형 LLM 설명이 숫자 역할·조건·거리 종류·순위·출처를 바꾸면 기본 설명을 사용한다. 기존 answer_grounding_v2가 이 신규 계약까지 검증한다고 주장하지 않는다. 호출 5회·결과 20행·로컬 모델·타임아웃 경계를 유지한다.
- **OPEN QUESTION**: 장래 Tool의 서비스 분리, 통계·비교 계산 Tool, 도구별 타임아웃과 오류 노출 방식은 평가 후 결정한다.

## Acceptance Criteria

- 합성 fixture에서 허용 목록, 인자 거부, 행·호출 한도, 빈 결과, 오류 로그, 지원되지 않는 금액 차단을 확인한다.
- 실제 정확도·완료 판정에는 검수된 실제 snapshot과 Golden이 필요하다.
