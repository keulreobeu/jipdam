# TASK-CANONICAL-MASK-RULES-001 — 마스킹 전월세의 안전한 후보 규칙

```toml
kind = "task"
id = "TASK-CANONICAL-MASK-RULES-001"
status = "ready"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/collection_integrate.py", "outputs/budongi_mvp_temp/tests/test_collection_integration.py", "outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md", "outputs/budongi_mvp_temp/docs/tasks/canonical-mask-rules.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/plans/canonical-mask-rule-context.md", "docs/sdd/traceability.json"]
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

- [ ] `***`는 literal identity로 사용되지 않는다.
- [ ] 완전하고 정확한 비마스크 기준의 기존 후보 회귀가 유지된다.
- [ ] 부족/모호한 근거는 pending/unverified 경계 밖으로 승격되지 않는다.
- [ ] 합성 테스트와 제품 회귀 및 SDD 증거를 기록한다.

## 검증·상태

GMS가 코드를 수정하지 않는 초안을 반환한 뒤 담당자가 검토·수동 적용한다. 실제 자료 준비는 이 Task의 선행 조건이 아니다. 코드/테스트/로컬 검증이 완료되기 전까지 ready 상태를 유지한다.
