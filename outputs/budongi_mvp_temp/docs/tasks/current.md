# Current Task — Required Fact Coverage Evaluation

```toml
kind = "task"
id = "TASK-EVAL-001"
status = "in_progress"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/08_evaluation_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/eval.py", "outputs/budongi_mvp_temp/tests/test_storage_tools.py", "outputs/budongi_mvp_temp/tests/test_required_facts.py", "outputs/budongi_mvp_temp/docs/specs/08_evaluation_spec.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["EVAL-001-AC-01", "EVAL-001-AC-02", "EVAL-001-AC-03", "EVAL-001-AC-04", "EVAL-001-AC-05", "EVAL-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/bootstrap.py --app-only"
result = "passed"
evidence = "docs/sdd/validation.md#product-evaluation"
acs = ["EVAL-001-AC-01", "EVAL-001-AC-02", "EVAL-001-AC-03", "EVAL-001-AC-04", "EVAL-001-AC-05", "EVAL-001-AC-06"]
```

Status: Required-fact coverage implemented and synthetic tests passed; actual Golden scoring remains pending.

ID는 기존 작업을 계속 추적하기 위해 부여했다. 실제 Golden의 미완료 때문에 in_progress를 유지한다. SDD 운영 체계의 완료는 루트 [TASK-SDD-001](../../../../docs/tasks/sdd-adoption.md)로 별도 관리한다. 다음 제품 작업은 새 영구 Task 파일을 만들고 이 문서에서 연결한다.

팀 공유 환경 정리는 별도 [Team Environment Task](../../../../docs/tasks/team-environment.md)에서 관리한다. 이 제품 평가 Task와 실제 Golden의 미완료 상태는 유지한다.

## Goal

Evaluate each Golden `required_facts` item against its generated answer deterministically, report matched/missing/unmeasured facts without treating unsupported formats as success, and keep full claim precision distinct from required fact coverage.

## Related Spec

- `docs/specs/08_evaluation_spec.md`
- `docs/specs/06_agent_tools_spec.md`
- `docs/budongi_advanced_llm_evaluation_plan.md` (Golden schema)

## Fact contract

- String values use normalized exact substring matching. ISO dates also accept `YYYY년 M월 D일` and `YYYY.M.D` forms.
- Numeric values require a `unit`, then use exact decimal comparison with the Golden tolerance. The answer must contain the same unit or a documented alias (`m`/`미터`, `㎡`/`m²`/`제곱미터`, `원`/`만원`/`억 원` conversions, `년`).
- Each fact is checked only in a sentence containing its `entity_aliases`; if omitted, the canonical `entity` ID is the default alias. Aliases should list user-facing apartment names when answers use names instead of IDs.
- Missing answer claim is `missing`; unknown type, unsupported/missing numeric unit, null value, malformed tolerance/aliases, or absent `required_facts` is `not_measured`.
- Per-question status passes only when all required facts are scorable and matched; any missing fact fails; otherwise status is not measured.

## Acceptance Criteria

- [x] EVAL-001-AC-01 Numeric facts respect units and tolerance.
- [x] EVAL-001-AC-02 Text/date facts match documented normalization.
- [x] EVAL-001-AC-03 Facts require entity/alias context in the same answer sentence.
- [x] EVAL-001-AC-04 Missing/malformed facts and absent predictions do not become false passes.
- [x] EVAL-001-AC-05 Coverage excludes unmeasured facts and exposes counts and reproducible CSV evidence.
- [x] EVAL-001-AC-06 Existing metrics remain available; full claim precision and actual-data/Phase readiness remain unclaimed.

확인 명령·결과와 집중 테스트는 루트 [SDD 검증 기록](../../../../docs/sdd/validation.md#product-evaluation)에 연결한다. 실제 Golden 평가는 별도 미완료 조건이다.
