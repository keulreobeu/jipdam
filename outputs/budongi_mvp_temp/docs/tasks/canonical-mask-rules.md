# TASK-CANONICAL-MASK-RULES-001 — 마스킹 전월세의 안전한 후보 규칙

```toml
kind = "task"
id = "TASK-CANONICAL-MASK-RULES-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/collection_integrate.py", "outputs/budongi_mvp_temp/tests/test_collection_integration.py", "outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md", "outputs/budongi_mvp_temp/docs/tasks/canonical-mask-rules.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/plans/canonical-mask-rule-context.md", "docs/sdd/traceability.json"]
acs = ["CANONICAL-001-AC-03"]

[[verification]]
command = "python -X utf8 -m unittest discover -s tests -p test_collection_integration.py (TEMP/TMP=outputs/budongi_mvp_temp/.local_runtime/gms-test-temp)"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/canonical-mask-rules.md#verification"
acs = ["CANONICAL-001-AC-03"]

[[verification]]
command = "python -X utf8 -m unittest discover -s tests (TEMP/TMP=outputs/budongi_mvp_temp/.local_runtime/gms-test-temp)"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/canonical-mask-rules.md#verification"
acs = ["CANONICAL-001-AC-03"]
```

## 목적

공개 거래자료의 마스킹 문자열을 실제 단지명·행정동·지번처럼 비교해 잘못된 후보가 만들어지지 않게 한다. 불완전하거나 모호한 행은 검수 가능한 미확정 후보로만 남기며, 거래·관계를 자동 확정하지 않는다.

## 범위

- `collection_integrate._candidates`의 deterministic candidate proposal 규칙을 점검하고 보완한다.
- `***` 마스크, 빈 값, 일부 필드만 남은 합성 행, 완전한 비마스크 필드 행, 여러 공식 ID가 일치하는 충돌 행을 합성 테스트한다.
- 충분한 비마스크 근거가 부족하면 매칭 후보를 만들지 않거나 모호 상태로 보존한다.
- 결과는 `pending`/`unverified`이며 `confidence_score`를 임의로 부여하지 않는다.

## 제외

실제 canonical DB/raw 행의 GMS 전송, 실제 수집, 지오코딩, aptSeq가 없는 전월세 행의 공식 ID 생성, 거래 병합, 후보 자동 승격/확정, 검수 패키지 생성은 포함하지 않는다. 검수자는 전체 원본 거래를 수동 대조하지 않는다. 이 작업은 검수해야 할 제한된 후보만 설명 가능하게 만드는 준비 단계다.

## 완료 기준

- [x] `***`는 literal identity로 사용되지 않는다.
- [x] 완전하고 정확한 비마스크 기준의 기존 후보 회귀가 유지된다.
- [x] 부족/모호한 근거는 pending/unverified 경계 밖으로 승격되지 않는다.
- [x] 합성 테스트와 제품 회귀 및 SDD 증거를 기록한다.

## Verification

GMS가 코드를 직접 수정하지 않고 검토용 텍스트 초안만 반환해야 한다. 실행 시도는 provider 결과/정산이 불확정되어 managed task `TASK-CANONICAL-MASK-RULES-001-GMS2`가 `WAITING_FOR_PROVIDER`로 남았다. count 예약은 settled됐고 생성은 uncertain 197크레딧 hold로 기록되어 재시도하지 않았다. 이전 183크레딧 hold도 유지했다. 결과 텍스트는 받지 못해 코드는 Spec/기존 함수와 합성 회귀를 바탕으로 담당자가 직접 작성했다.

`collection_integrate._candidates()`는 공식 라벨 쪽에서 trim 뒤 전부 별표인 법정동·지번·단지명을 제외한다. 따라서 `***`가 양쪽에 동일하게 있어도 후보가 되지 않는다. 불완전 값의 부분 매칭/퍼지 확장은 추가하지 않았다. 완전한 동일 라벨은 종전과 같이 근거가 있는 pending/unverified 후보이고 `confidence_score=NULL`이며 `observations.complex_id`는 수정하지 않는다.

합성 검증: 해당 통합 파일 13개 테스트 통과(26.396초), 제품 전체 282개 테스트 통과(100.739초). 통합 `verify_environment.py`는 기존 미추적 branch bundle에 대한 SDD 범위 오류로 계속 막혀 있다. bundle은 수정·삭제·스테이징하지 않았다.
