# Current Task — Required Fact Coverage Evaluation

Status: Required-fact coverage implemented and synthetic tests passed; actual Golden scoring remains pending.

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

- [x] Numeric facts respect units and tolerance; text/date facts match documented normalization.
- [x] Facts require entity/alias context in the same answer sentence; wrong-entity mentions do not receive credit.
- [x] Missing or malformed facts do not become false passes; summaries exclude unmeasured facts from the coverage denominator and expose counts.
- [x] Existing answer-grounding, tool selection, argument, and entity metrics remain available.
- [x] Overall answer claim precision and actual-data/Phase readiness remain unclaimed.
- [x] Synthetic behavior suite passes; no actual Golden or real snapshot is present for scoring.
