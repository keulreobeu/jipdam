# TASK-RENT-REAL-001 — 실제 전월세 수집·매칭·사람 검수

```toml
kind = "task"
id = "TASK-RENT-REAL-001"
status = "in_progress"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/rental_review.py", "outputs/budongi_mvp_temp/src/budongi/collection_integrate.py", "outputs/budongi_mvp_temp/scripts/", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md", "outputs/budongi_mvp_temp/docs/tasks/rental-real-data.md", "outputs/budongi_mvp_temp/docs/rental-review-package.md", "outputs/budongi_mvp_temp/docs/", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-07", "RENT-001-AC-10"]
[[verification]]
command = "manual: PLAN-RENT-001의 관련 제품 AC 시나리오를 실행하고 실제 결과를 기록"
result = "not_run"
evidence = "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md#product-verification-pending"
acs = ["RENT-001-AC-07", "RENT-001-AC-10"]

[[verification]]
command = "오프라인: 복원된 실제 MOLIT 전월세와 trade-detail aptSeq/name/sgg/dong/jibun 후보 대조"
result = "user approved exact unique-match scope; canonical integration now preserves official aptSeq entities from retained detailed raw rows"
evidence = "outputs/budongi_mvp_temp/docs/rental-identity-review-20261020.md"
acs = ["RENT-001-AC-07"]

[[verification]]
command = "복원된 전월세·trade-detail staging의 사용자 승인 5,156개 aptSeq 그룹/203,159관측을 canonical v3에 대사하고 검수 패키지로 serving 생성"
result = "passed: serving has 203,159 confirmed links; source status remains unknown and recommendation returns data_not_ready"
evidence = "outputs/budongi_mvp_temp/docs/rental-identity-review-20261020.md"
acs = ["RENT-001-AC-07"]
```

## 목표·범위

2026-10-20 사용자 요청은 기존에 승인·보존된 MOLIT 전월세 관측을 사람 검수해 실제 단지에 연결하도록 이 Task의 **기존 데이터 매칭 범위만** 재개한다. 새로운 수집/출처/좌표/시설은 승인하지 않았다. 요청월·수집일·페이지/행·해시·정규화 버전·한계를 추적하고 불명확한 매칭은 격리한다. 오래된 2023 연구의 완료를 선행 조건으로 삼지 않는다. 실제 추천 품질은 신규 실제 자료로 검수하고 합성 데모와 별도로 보고한다.

승인 근거: 기존 자료 범위는 [PLAN-RENT-001](../plans/rental-recommendation-mvp.md#확정-근거), 매칭 재개는 2026-10-20 현재 사용자 요청이다. 후보 생성은 사람 검수·승인을 대체하지 않는다. 담당자는 기존 프로젝트 owner다.

## 의존·제외 범위

매칭 재개 범위: 기존 `rental.sqlite3`와 대응하는 MOLIT trade-detail staging만 오프라인으로 사용한다. `aptSeq` 직접 일치와 구·이름·법정동·지번 대조를 후보로 기록하되, 사용자가 연결 규칙을 검수하기 전 confirmed 관계나 추천 반영을 만들지 않는다. 원천 취소/정정 상태가 미기록이면 임의로 valid로 채우지 않는다. 신규 수집, 새 출처, 좌표, 시설, Drive/GitHub 업로드, 외부 CLI 리뷰, push/PR/배포는 제외한다.

## 완료 기준

- [ ] RENT-001-AC-07 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [ ] RENT-001-AC-10 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.

## 검증·결과

2026-10-14: 기존 전월세 238,620건 수집·canonical은 별도 완료 Task로 보존한다. 실제 확정 관계·좌표·시설·커버리지와 사람 검수 Golden은 아직 없다.

2026-10-20: 사용자가 같은 `aptSeq`와 구·단지명·법정동·지번이 유일하게 일치하는 5,156개 그룹 203,159건을 승인했다. 예외 35,461건은 미확정으로 남겼다. canonical 통합은 보존된 상세 원본의 official `aptSeq` 엔터티를 관측 유효기간과 독립적으로 보존하도록 보완했고 새 canonical을 생성했다. 승인 검수 패키지를 별도 serving에 반영해 연결 관측/관계 203,159건, source status `unknown` 203,159건, 미연결 `unreviewed` 35,461건을 대사했다. 직접 추천 요청은 `data_not_ready`와 0건을 반환했다. 원본 canonical/관측 DB는 수정하지 않았다. 좌표·시설·coverage·실모델이 없어 실제 추천 readiness 및 실추천 검증은 미완료다. 해시·명령·결과는 [사람 검수 및 적용 기록](../rental-identity-review-20261020.md)에 있다.

단지 연결·검수 패키지 적용은 완료했지만, 이 serving은 원천 거래 상태가 `unknown`이라 실제 추천 결과를 만들지 않는다. 추천/상세 성공·성능, 실모델, Golden 검증은 **not_run**이다. 상태·좌표·시설 게이트를 승인된 근거로 충족한 뒤 [검증 시나리오](../plans/rental-recommendation-mvp.md#product-verification-pending)를 실행한다. 실제 unittest 메서드는 실행한 경우에만 추적 원장에 연결한다. README에 계획 명령을 실행 가능한 명령으로 표시하지 않는다.
