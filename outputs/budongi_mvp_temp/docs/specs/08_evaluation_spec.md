# Evaluation Spec

## CURRENT

- `tests/`는 합성 입력으로 DB·Tool·Agent의 주요 계약을 검사한다.
- `src/budongi/eval.py`는 Golden과 실행 로그의 Tool 이름 순서, 인자 Exact Match, 반환 Entity Precision/Recall을 계산한다.
- 실행 로그의 `grounding_check.status` 및 실패 수로 구조화 claim 검사를 `passed`, `failed`, `not_run`/`not_measured`로 보고한다. pass rate의 분모에는 실제 검사한 표본만 포함한다.
- Golden `required_facts`의 문자열/날짜·숫자 값 coverage를 결정적으로 비교한다. 숫자에는 unit이 필수이며 같은 unit 또는 제한된 alias와 지정 tolerance를 적용한다. KRW/만원/억원 표기는 원 단위로 환산한다. 문자열/숫자 값은 같은 문장에 Golden entity ID 또는 `entity_aliases` 중 하나도 있어야 일치한다. 지원하지 않는 값 형식·단위·alias는 `not_measured`로 남긴다.
- 리포트는 표본별 required fact matched/missing/not_measured와 상세 근거를 CSV에 기록하고, 집계 coverage는 matched/(matched+missing)으로 계산해 not_measured를 분모에서 제외한다. 실행 로그가 없는 표본은 required fact not_measured다.
- 필수 사실 coverage는 답변의 누락을 재며, 답변 전체의 잘못된 추가 주장을 재는 claim precision과 구분한다. `generation_check`는 전체 generation 사실성을 의미하지 않으므로 미측정으로 유지한다.
- Fact 단위 결과는 entity, aliases, field, value, unit, tolerance와 판정 사유를 detail CSV에 보존한다. Required fact가 비었거나 prediction이 없으면 표본 상태는 `not_measured`다.
- 실제 검수된 2023 스냅샷과 약 200건 Golden이 없으므로 실제 정확도 또는 Phase 0~5 완료를 주장하지 않는다.

## TARGET

- FACT 50, FILTER 60, COMPARE 60, NO_MATCH 30 안팎의 사람 검수 Golden을 구성하고 Tool 선택·인자·반환 ID·필수 사실·출처·기준일을 단계별로 평가한다.
- 단지·거래·사건·질문 재표현 묶음을 Train/Validation/Test에 걸쳐 누출시키지 않는다. 최종 Test는 설정 확정 후 사용한다.
- `run_id`별 모델·Prompt·Tool schema·snapshot·평가 버전과 오류 유형을 기록한다. 미측정 값을 0 또는 성공으로 취급하지 않는다.
- Golden의 entity alias 작성 품질을 실제 사람 검수 케이스로 검증하고 alias가 모호한 경우의 평가 규칙을 다듬는다.

## Acceptance Criteria

- 합성 테스트와 실제 Golden 평가를 별도로 보고한다.
- 평가 결과는 같은 입력·버전으로 재실행 가능하며 Tool 선택 → 인자 → 조회 → 답변 중 첫 실패 단계를 구분한다.
- 전체 claim precision 및 사람 검수 실제 Golden 평가가 보류된 동안 평가 완료를 선언하지 않는다.
