# Evaluation Spec

```toml
kind = "spec"
id = "EVAL-001"
status = "baseline"
owner = "keulreobeu"
revision = 1
```

기존 required-fact coverage 구현을 정리한 baseline이며 과거 승인을 소급하지 않는다. ID별 검증은 루트 `docs/sdd/traceability.json`을 따른다. 실제 데이터 평가와 전체 claim precision은 이 baseline 검증 범위 밖이다.

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

## EVAL-001-REQ-01 값과 단위의 비교

숫자는 단위·허용 오차, 문자열과 날짜는 현재 정규화 계약으로 비교한다.

### EVAL-001-AC-01 숫자·단위·허용 오차

현재 단위 정규식 경계에서 원/만원/억원 환산과 m/미터·㎡ alias를 지원하며 허용 오차의 경계는 포함한다. 경계 밖의 값은 missing이다. 원 단위 표기를 한글 서술에 바로 붙인 `900,000,000원입니다`는 현재 미지원이며 `900,000,000원 입니다`는 지원한다.

### EVAL-001-AC-02 문자열·날짜 정규화

문자열은 casefold·공백 정규화 후 substring으로, 유효한 ISO 날짜는 한국어·점 구분 날짜와 비교한다. 다른 날짜는 missing이고 잘못된 Golden 날짜는 not_measured다.

## EVAL-001-REQ-02 entity 문맥

같은 문장에 canonical ID 또는 명시한 alias가 있는 사실만 비교한다.

### EVAL-001-AC-03 entity·alias·문장 경계

다른 entity·ID 접두사가 비슷한 entity·다른 문장에만 있는 값은 성공으로 처리하지 않는다. alias가 없으면 canonical ID를 사용한다.

## EVAL-001-REQ-03 누락과 미측정

답변에 측정 가능한 사실이 없으면 missing이고 지원하지 않는 Golden 입력·단위·alias·tolerance는 not_measured다.

### EVAL-001-AC-04 false pass 방지

비어 있거나 잘못된 required_facts, null·bool·미지원 값, 숫자 단위 누락, 잘못된 alias·tolerance와 prediction 누락은 성공으로 처리하지 않는다. missing이 있으면 표본 실패이며 나머지 미측정만 있으면 표본 not_measured다.

## EVAL-001-REQ-04 집계와 재현 가능한 증거

coverage는 matched/(matched+missing)으로 계산하고 미측정 수를 별도로 보존한다. 기존 지표와 실제 평가 미완료 상태를 유지한다.

### EVAL-001-AC-05 집계·CSV 근거·재현

CSV에 표본 및 fact별 상태·entity·field·value·unit·tolerance·alias·판정 사유를 보존한다. 같은 입력은 같은 결과를 만들며 측정 사실이 없으면 coverage는 null이다.

### EVAL-001-AC-06 기존 지표와 평가 경계

Tool 선택·인자·entity·grounding 지표가 유지된다. generation은 전체 claim precision 보류 상태를 유지하고 합성 coverage를 실측 성능으로 선언하지 않는다.

## 전체 평가 완료 조건

OPEN QUESTION: 단위 뒤 한글 서술이 붙는 표기까지 지원할지 별도 제품 변경에서 정한다. 이번 SDD 도입은 현재 동작을 보존하고 이 제한을 테스트·baseline에 기록한다.

- 합성 테스트와 실제 Golden 평가를 별도로 보고한다.
- 평가 결과는 같은 입력·버전으로 재실행 가능하며 Tool 선택 → 인자 → 조회 → 답변 중 첫 실패 단계를 구분한다.
- 전체 claim precision 및 사람 검수 실제 Golden 평가가 보류된 동안 평가 완료를 선언하지 않는다.
