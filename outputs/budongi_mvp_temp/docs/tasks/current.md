# Current Tasks — 전월세 제품 전환과 보존된 평가 기록

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

2026-10-06의 로컬 환경 검수 후속 작업은 [TASK-ENV-001](../../../../docs/tasks/environment-repair-20261006.md)에서 bunx 명령 연결 및 가상환경·CLI 설치를 추적한다.

## 전월세 제품 우선 작업

2026-10-06 승인된 [RENT-001](../specs/10_rental_recommendation_spec.md)·[PLAN-RENT-001](../plans/rental-recommendation-mvp.md)을 따른다. 이 파일의 TASK-EVAL-001 메타데이터와 체크·검증 이력은 그대로 보존하며, 실제 역사 Golden 미완료로 in_progress를 유지한다. 해당 연구 완료는 새 전월세 추천의 선행 조건이 아니다.

| 순서 | Task | 이번 적용 상태 |
| --- | --- | --- |
| 1 | [TASK-RENT-DOC-001 문서 전환](rental-spec-transition.md) | 문서 적용·검증 기록 참조 |
| 2 | [TASK-RENT-DATA-001 데이터 계약](rental-data-contract.md) | in_progress, 합성 저장 테스트 통과·공식 필드/단위 확인 대기 |
| 3 | [TASK-RENT-REC-001 추천·CLI](rental-recommendation-cli.md) | verified, 합성 추천·CLI AC-01~06 검증; 실제 데이터·웹 별도 |
| 4 | [TASK-CRED-001 암호화 API 키 보관함](api-credential-vault.md) | in_progress, 보관함·loopback 설정 화면 구현; interactive WinCred round-trip 확인 남음; 실제 API 호출 제외 |
| 5 | [TASK-RENT-WEB-001 웹 비교](rental-web-demo.md) | draft, 보관함 Task 뒤에 설정 화면과 추천 비교를 통합 |
| 6 | [TASK-RENT-LLM-001 설명·평가](rental-explanation-evaluation.md) | draft |
| 별도 | [TASK-RENT-REAL-001 실데이터](rental-real-data.md) | blocked, 수집·매칭 보류 |

합성 추천·CLI의 AC-01~06은 추천 Task 검증을 따르며 실제 추천 데이터·웹·모델 평가는 미완료다. CRED-001의 미완료 OS 저장소 검증은 해당 Task를 따른다. 문서 완료·합성 성공을 실제 추천 품질로 승격하지 않는다.

보관함 구현의 후속 검증·수정은 [TASK-CRED-QA-001](credential-vault-qa.md)에서 추적한다. 키 비노출·요청 처리·삭제 재확인·수정 창 취소의 회귀 검증이며 실제 API 호출은 포함하지 않는다.

보관함의 폴더와 제공자 구분, 저장 후 제공자 변경은 [TASK-CRED-PROVIDER-001](credential-provider-edit.md)에서 추적한다.

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
