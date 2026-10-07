# TASK-RENT-LLM-001 — 선택형 LLM 설명과 추천 평가

```toml
kind = "task"
id = "TASK-RENT-LLM-001"
status = "draft"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/", "outputs/budongi_mvp_temp/tests/", "outputs/budongi_mvp_temp/docs/specs/08_evaluation_spec.md", "outputs/budongi_mvp_temp/docs/specs/06_agent_tools_spec.md", "outputs/budongi_mvp_temp/docs/tasks/rental-explanation-evaluation.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-09", "RENT-001-AC-10"]

[[verification]]
command = "manual: PLAN-RENT-001의 관련 제품 AC 시나리오를 실행하고 실제 결과를 기록"
result = "not_run"
evidence = "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md#product-verification-pending"
acs = ["RENT-001-AC-09", "RENT-001-AC-10"]
```

## 목표·범위

로컬 4B가 검증된 후보·순위·수치·조건만 설명하게 하고 근거 검증 실패/장애 시 기본 설명을 사용한다. 금액 역할·거리 종류·미확인 조건·순위·출처 변조를 검사하며 현재 answer_grounding_v2의 보증 범위를 과장하지 않는다. 기존 EVAL-001 baseline을 유지하고 신규 추천 합성 검증·실제 사람 Golden·전체 claim precision·미측정을 분리한다.

승인 근거: [PLAN-RENT-001](../plans/rental-recommendation-mvp.md#확정-근거)의 최종 사용자 적용 요청. 이번 문서 변경에서 이 제품 구현을 수행하거나 완료 처리하지 않는다. 담당자 기본값은 기존 프로젝트 owner이며 착수 시 실제 담당자를 확정한다.

## 의존·제외 범위

선행 조건: TASK-RENT-WEB-001. 실수집/매칭은 별도 보류 해제까지 금지하며 합성 입력으로 가능한 구현과 구분한다. 외부 CLI 리뷰·push/PR/배포는 이 Task의 자동 권한이 아니다.

## 완료 기준

- [ ] RENT-001-AC-09 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [ ] RENT-001-AC-10 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.

## 검증·결과

제품 검증은 **not_run**, 구현 미착수다. [검증 시나리오](../plans/rental-recommendation-mvp.md#product-verification-pending)를 따르고 작성·실행한 실제 unittest 메서드만 추적 원장에 연결한다. README에 계획 명령을 실행 가능한 명령으로 표시하지 않는다.
