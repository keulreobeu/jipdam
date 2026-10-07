# TASK-RENT-WEB-001 — 로컬 웹 입력·후보 비교

```toml
kind = "task"
id = "TASK-RENT-WEB-001"
status = "draft"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/", "outputs/budongi_mvp_temp/tests/", "outputs/budongi_mvp_temp/docs/specs/09_runtime_spec.md", "outputs/budongi_mvp_temp/docs/tasks/rental-web-demo.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-01", "RENT-001-AC-04", "RENT-001-AC-05", "RENT-001-AC-08"]

[[verification]]
command = "manual: PLAN-RENT-001의 관련 제품 AC 시나리오를 실행하고 실제 결과를 기록"
result = "not_run"
evidence = "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md#product-verification-pending"
acs = ["RENT-001-AC-01", "RENT-001-AC-04", "RENT-001-AC-05", "RENT-001-AC-08"]
```

## 목표·범위

Python 단일 앱의 loopback HTTP 진입점과 정적 HTML/JS를 구현한다. POST /api/recommendations는 공통 추천 계약을 호출한다. 로딩·입력 오류·데이터 미준비·0건·1~2건·성공 비교, 날짜·직선거리·관리비/대출 미포함·미확인 조건·출처를 표시한다. 지도·대화 세션·별도 프런트 빌드·외부 배포는 추가하지 않는다. 구현 후 실제 실행 명령을 README에 기록한다.

승인 근거: [PLAN-RENT-001](../plans/rental-recommendation-mvp.md#확정-근거)의 최종 사용자 적용 요청. 이번 문서 변경에서 이 제품 구현을 수행하거나 완료 처리하지 않는다. 담당자 기본값은 기존 프로젝트 owner이며 착수 시 실제 담당자를 확정한다.

## 의존·제외 범위

선행 조건: TASK-RENT-REC-001과 [TASK-CRED-001](api-credential-vault.md)의 loopback 서버·로컬 설정 화면 기반. 추천 비교 화면은 CRED-001 보관함 설정과 같은 Python 앱에 통합한다. 실수집/매칭은 별도 보류 해제까지 금지하며 합성 입력으로 가능한 구현과 구분한다. 외부 CLI 리뷰·push/PR/배포는 이 Task의 자동 권한이 아니다.

## 완료 기준

- [ ] RENT-001-AC-01 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [ ] RENT-001-AC-04 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [ ] RENT-001-AC-05 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [ ] RENT-001-AC-08 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.

## 검증·결과

제품 검증은 **not_run**, 구현 미착수다. [검증 시나리오](../plans/rental-recommendation-mvp.md#product-verification-pending)를 따르고 작성·실행한 실제 unittest 메서드만 추적 원장에 연결한다. README에 계획 명령을 실행 가능한 명령으로 표시하지 않는다.
