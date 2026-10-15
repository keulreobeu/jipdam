# TASK-RENT-REAL-001 — 실제 전월세 수집·매칭·사람 검수

```toml
kind = "task"
id = "TASK-RENT-REAL-001"
status = "blocked"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["outputs/budongi_mvp_temp/scripts/", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/tasks/rental-real-data.md", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-07", "RENT-001-AC-10"]
blocked_reason = "기존 승인된 MOLIT 수집은 완료. 새 수집/매칭/좌표/시설은 별도 승인 경계이며 사용자가 실제 검수 패키지·로컬 모델 미준비로 답함."

[[verification]]
command = "manual: PLAN-RENT-001의 관련 제품 AC 시나리오를 실행하고 실제 결과를 기록"
result = "not_run"
evidence = "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md#product-verification-pending"
acs = ["RENT-001-AC-07", "RENT-001-AC-10"]
```

## 목표·범위

사용자의 보류 해제 후 승인된 서울 전월세 API 범위를 수집하고 단지·좌표·시설 원천/매칭/커버리지와 사람 검수 Golden을 준비한다. 요청월·수집일·페이지/행·해시·정규화 버전·한계를 추적하고 불명확한 매칭은 격리한다. 오래된 2023 연구의 완료를 선행 조건으로 삼지 않는다. 실제 추천 품질은 신규 실제 자료로 검수하고 합성 데모와 별도로 보고한다.

승인 근거: [PLAN-RENT-001](../plans/rental-recommendation-mvp.md#확정-근거)의 최종 사용자 적용 요청. 이번 문서 변경에서 이 제품 구현을 수행하거나 완료 처리하지 않는다. 담당자 기본값은 기존 프로젝트 owner이며 착수 시 실제 담당자를 확정한다.

## 의존·제외 범위

선행 조건: 사용자의 수집·단지 매칭 보류 해제 + TASK-RENT-DATA-001. 실수집/매칭은 별도 보류 해제까지 금지하며 합성 입력으로 가능한 구현과 구분한다. 외부 CLI 리뷰·push/PR/배포는 이 Task의 자동 권한이 아니다.

## 완료 기준

- [ ] RENT-001-AC-07 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [ ] RENT-001-AC-10 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.

## 검증·결과

2026-10-14: 기존 전월세 238,620건 수집·canonical은 별도 완료 Task로 보존한다. 실제 확정 관계·좌표·시설·커버리지와 사람 검수 Golden은 아직 없다. 새로운 수집/자동 매칭을 시작하지 않으며 [후속 준비](continuation-parts-1to5.md)와 `rental-readiness`를 통해 필요한 입력을 확인한다.

2026-10-15: 기존 pending/unverified 전월세 후보를 로컬 검토표로 내보내는 준비 도구를 추가한다. 이는 사용자 검수·승인 패키지·확정 관계가 아니며 이 Task의 blocked 상태나 추천의 `data_not_ready`를 바꾸지 않는다. 세부 범위와 검증은 [후보 검토표 Task](rental-candidate-review-export.md)를 따른다.

제품 검증은 **not_run**, 구현 미착수다. [검증 시나리오](../plans/rental-recommendation-mvp.md#product-verification-pending)를 따르고 작성·실행한 실제 unittest 메서드만 추적 원장에 연결한다. README에 계획 명령을 실행 가능한 명령으로 표시하지 않는다.
