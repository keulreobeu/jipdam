# TASK-RENT-REC-001 — 결정적 추천·CLI·읽기 전용 Tool

```toml
kind = "task"
id = "TASK-RENT-REC-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/", "outputs/budongi_mvp_temp/tests/", "outputs/budongi_mvp_temp/docs/specs/00_project_spec.md", "outputs/budongi_mvp_temp/docs/specs/03_structured_search_spec.md", "outputs/budongi_mvp_temp/docs/specs/06_agent_tools_spec.md", "outputs/budongi_mvp_temp/docs/tasks/rental-recommendation-cli.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/09_runtime_spec.md", "outputs/budongi_mvp_temp/README.md", "README.md", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/AGENTS.md", ".agents/skills/jipdam-workflow/SKILL.md", "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md"]
acs = ["RENT-001-AC-01", "RENT-001-AC-02", "RENT-001-AC-03", "RENT-001-AC-04", "RENT-001-AC-05", "RENT-001-AC-06"]

[[verification]]
command = "python -X utf8 -m unittest discover -s tests -p test_rental_recommendation.py -v"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/rental-recommendation-cli.md#validation"
acs = ["RENT-001-AC-01", "RENT-001-AC-02", "RENT-001-AC-03", "RENT-001-AC-04", "RENT-001-AC-05", "RENT-001-AC-06"]
```

## 목표·범위

같은 스냅샷에서 유형·면적·기간 → 단지별 최신 계약 → 같은 계약의 두 예산 → 필수 met → 선호 상태 → 정해진 순위를 구현한다. recommend CLI와 읽기 전용 recommend_rentals를 공통 계약으로 연결하고 현재 세 Tool·역사 CLI는 보존한다. 내부 후보 검색과 최종 20행 출력 제한을 구분한다. 모델 없이 결과·기본 설명을 반환하고 입력/데이터 오류를 0건과 구분한다.

승인 근거: [PLAN-RENT-001](../plans/rental-recommendation-mvp.md#확정-근거)의 최종 사용자 적용 요청과 API 키 등록 후 다음 작업 진행 요청. 데이터 저장 기반은 재사용하며 공식 응답 필드 대조·실수집·매칭 보류와 독립적인 합성 입력 경로부터 구현한다. 담당자는 Codex다.

## 의존·제외 범위

선행 저장 기반: TASK-RENT-DATA-001의 구현·검증된 합성 스냅샷 적재 부분. 공식 응답 필드·단위 대조가 남은 데이터 Task 전체 완료를 주장하지 않는다. 실수집/매칭은 별도 보류 해제까지 금지하며 합성 입력으로 가능한 구현과 구분한다. 외부 CLI 리뷰·push/PR/배포는 이 Task의 자동 권한이 아니다.

## 완료 기준

- [x] RENT-001-AC-01 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [x] RENT-001-AC-02 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [x] RENT-001-AC-03 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [x] RENT-001-AC-04 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [x] RENT-001-AC-05 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [x] RENT-001-AC-06 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.

공통 인터페이스·CLI의 오류 동작은 이 Task에서 구현하고 검증한다. HTTP·비교 화면까지 포함한 전체 AC-08 완료는 후속 TASK-RENT-WEB-001이 소유하며 이 Task의 완료를 기다리는 순환 의존을 만들지 않는다.

## validation

2026-10-06 합성 입력의 `test_rental_recommendation.py` 15개 통과. AC-01은 서울 범위·0/1/2/5/20 후보·비완화, AC-02는 같은 최신 계약의 예산 쌍·경계·잘못된 타입, AC-03은 필터 후 최신 계약·기간·면적·유형·동률·취소/미검수 정정, AC-04는 필수 unknown/unmet 제외·거리 경계·미확정 위치 오류, AC-05는 선호 unknown·미지원·미검수/오래된 시설 범위, AC-06은 선호/직장/계약일/ID 순위·중복 조건을 검증했다. unittest 메서드는 추적 원장에 연결한다.

합성 CLI를 임시 폴더에서 실행하여 후보 2곳·역 선호 unknown·출처·매칭 근거를 확인하고 같은 입력의 함수/CLI JSON이 일치함을 검증했다. 읽기 전용 DB 쓰기 거부, 합성 허용 누락의 data_unavailable/exit 3, 입력 오류/exit 2, 손상 DB의 internal_error/exit 1도 확인했다. 기존 역사 Tool·LLM 허용 목록과 보관함 연결은 변경하지 않았다.

시설 `complete`만으로 충족을 추정하지 않는다. 정규화·검수된 커버리지 원이 요청 반경 전체를 포함하고 자료 기준일·검수일이 스냅샷 최근 12개월에 포함돼야 판정한다. 이 메타데이터는 내부 합성/검수 입력 계약이며 공급자 API의 원천 필드라고 주장하지 않는다.

현재 AC-01~06의 완료 범위는 합성 스냅샷의 결정적 추천·CLI다. 실제 수집·매칭, 공식 필드 대조, 웹 비교와 LLM 설명 검증은 별도 미완료다. source_unverified 자료는 합성 허용 플래그로 활성화하지 않는다. 최종 `python -X utf8 scripts/verify_environment.py` 통과: 제품 테스트 82개 중 81개 통과·native WinCred 1개 skip, 루트 테스트 18개 통과, 기존 모델 없는 역사 CLI smoke 통과. skip은 관리 자동 실행 세션의 Windows 로그온 자격 증명 부재이며 원래 CRED-001의 interactive round-trip 미완료를 유지한다.

`python -X utf8 scripts/check_sdd.py --base origin/main`과 `git diff --check` 통과. Spec·Plan·README·AGENTS·워크플로·추적 원장을 동기화했다. 외부 CLI 리뷰·실제 공급자 호출·모델 실행·브라우저 추천 QA는 수행하지 않았다. 다음 단계는 TASK-RENT-WEB-001의 로컬 HTTP 입력·비교 화면이다.
