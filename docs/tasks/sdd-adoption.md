# Task — SDD 운영 체계와 평가 시범 적용

```toml
kind = "task"
id = "TASK-SDD-001"
status = "verified"
owner = "keulreobeu"
specs = ["docs/specs/sdd_workflow_spec.md", "outputs/budongi_mvp_temp/docs/specs/08_evaluation_spec.md"]
scope = ["docs/", ".github/", "AGENTS.md", "README.md", ".agents/skills/jipdam-workflow/SKILL.md", "scripts/check_sdd.py", "scripts/verify_environment.py", "tests/test_sdd.py", "outputs/budongi_mvp_temp/AGENTS.md", "outputs/budongi_mvp_temp/docs/specs/08_evaluation_spec.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/tests/test_required_facts.py"]
acs = ["SDD-001-AC-01", "SDD-001-AC-02", "SDD-001-AC-03", "SDD-001-AC-04", "SDD-001-AC-05", "SDD-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/bootstrap.py --app-only"
result = "passed"
evidence = "docs/sdd/validation.md#local-checks"
acs = ["SDD-001-AC-01", "SDD-001-AC-02", "SDD-001-AC-03", "SDD-001-AC-04"]

[[verification]]
command = "gh run view 36823087083 --repo keulreobeu/jipdam --json conclusion,jobs"
result = "passed"
evidence = "docs/sdd/validation.md#github-ci"
acs = ["SDD-001-AC-05"]

[[verification]]
command = "gh api repos/keulreobeu/jipdam/branches/main/protection"
result = "passed"
evidence = "docs/sdd/validation.md#main-protection"
acs = ["SDD-001-AC-06"]
```

## 목표·확정 근거

변경 유형: tooling. 사용자 D1~D8 선택과 2026-10-01 구현 요청을 [Spec](../specs/sdd_workflow_spec.md)·[ADR](../adr/ADR-003-sdd-workflow.md)에 반영한다. [평가 baseline](../../outputs/budongi_mvp_temp/docs/specs/08_evaluation_spec.md)은 기존 동작을 정리하며 소급 승인하지 않는다.

의존성: 기본 CI 성공 → main 필수 검사 적용 → 설정 읽기 검증. 실제 데이터·Golden·모델 추론·전체 기능 전환·제품 API/평가 형식 변경은 제외한다.

## 완료 기준

- [x] SDD-001-AC-01 운영 규칙·템플릿·상태·ID 검사가 있다.
- [x] SDD-001-AC-02 요구·AC·문서·테스트의 잘못된 참조를 거부한다.
- [x] SDD-001-AC-03 이번 변경의 Task 연결과 설명 문서 면제를 검사한다.
- [x] SDD-001-AC-04 완료 AC와 passed 증거를 요구한다.
- [x] SDD-001-AC-05 로컬·Windows/Linux CI와 평가 시범 기능이 통과한다.
- [x] SDD-001-AC-06 main 필수 CI·리뷰 권장 설정을 읽어 확인한다.

## 실행 계획과 결과

운영 문서·분리 템플릿 → 추적 원장·평가 AC → 검사기·집중 테스트 → 공통 진입점·PR·CI → 로컬 검증 → PR CI → main 보호 → 결과 기록 → 최종 CI·병합 순서로 적용한다.

실제 결과는 [검증 기록](../sdd/validation.md)에 작성한다. 전체 제품 평가의 미완료 상태는 [기존 평가 Task](../../outputs/budongi_mvp_temp/docs/tasks/current.md)에 유지한다.

독립 검토에서 CI가 탐색하지 않는 파일의 테스트를 AC 근거로 받을 수 있음을 확인했다. 실제 CI와 검사기가 TEST_ROOTS를 공유하고 파일·패키지 탐색 규칙을 검사하도록 수정했다. 변경 경로의 저장소 밖 symlink와 마지막 검증 실패를 과거 passed 기록으로 덮는 경우도 차단했다. 추가 회귀 검사가 수정 전 실패하고 수정 후 통과한 것을 확인했다.

네 가지 PR/push CI가 성공하고 main 보호 설정을 실제 API 응답으로 확인했다. 도입 Task의 AC는 모두 검증되었다. 템플릿에 Plan·ADR의 자체 ID와 명시적 범위·관련 AC·검증 결과 칸도 보완했다. 기존 제품 평가 Task의 실제 Golden 미완료는 유지한다.
