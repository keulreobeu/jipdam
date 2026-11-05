# TASK-LEAN-CHECK-001 / KAN-42

```toml
kind = "task"
id = "TASK-LEAN-CHECK-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/32_lean_foundations_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/jipdam_harness/input_check.py", "outputs/budongi_mvp_temp/src/jipdam_harness/input_check_cli.py", "outputs/budongi_mvp_temp/src/jipdam_harness/managed_cli.py", "outputs/budongi_mvp_temp/src/jipdam_harness/autocommit.py", "outputs/budongi_mvp_temp/tests/test_input_check.py", "outputs/budongi_mvp_temp/tests/test_harness_operations.py", "outputs/budongi_mvp_temp/docs/specs/32_lean_foundations_spec.md", "outputs/budongi_mvp_temp/docs/tasks/lean-input-check.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/plans/lean-foundations-20261103.md", "outputs/budongi_mvp_temp/docs/harness/INPUT_CHECK.md", "outputs/budongi_mvp_temp/docs/harness/LEAN_VALIDATION_20261103.md", "docs/sdd/traceability.json"]
acs = ["LEAN-CORE-001-AC-01", "LEAN-CORE-001-AC-02", "LEAN-CORE-001-AC-03", "LEAN-CORE-001-AC-04", "LEAN-CORE-001-AC-05", "LEAN-CORE-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/harness/LEAN_VALIDATION_20261103.md"
acs = ["LEAN-CORE-001-AC-01", "LEAN-CORE-001-AC-02", "LEAN-CORE-001-AC-03", "LEAN-CORE-001-AC-04", "LEAN-CORE-001-AC-05", "LEAN-CORE-001-AC-06"]
```

- [x] LEAN-CORE-001-AC-01 결정적인 결과·순서·hash.
- [x] LEAN-CORE-001-AC-02 bounded parser·깊이/정수/행/열.
- [x] LEAN-CORE-001-AC-03 미실행/실패/timeout의 허위 PASS 차단.
- [x] LEAN-CORE-001-AC-04 path/secret/DB/raw/runtime 경계.
- [x] LEAN-CORE-001-AC-05 필수 검증·provider0.
- [x] LEAN-CORE-001-AC-06 고정 반례/과거 실패 불변.

입력 검사 CLI 구현과 로컬21개 경계 검증을 통과했다. 실제 junction 외부 읽기 차단,
테스트0건/모두skip UNKNOWN, 정수/깊이/CSV/manifest·토큰URL·Unicode JSONL 반례를 포함한다.
전체 회귀411/35 및 첫 게시 SHA9a57bd3의 등록6검사는 통과했다. 이후 독립 리뷰의
파일명 비밀 형태·pytest0건·staged diff 경계를 보완해 입력21개를 재검증했다.
최신 고정 SHA 독립 검토/게시 전이며 전체 AC 완료로 승격하지 않는다.
source base70f7408/명시 선행 HANDOFF dependency. main merge/PR 생성/실모델 호출 없음.

최신 전체 검증: 제품411/팀35/합성CLI passed. 독립 검토·최종 게시 전이라 status는 in_progress다.

fbecac44a78e9fde12b0b26370f02fffc55b422d의 세 경계 수정 delta는 독립 pure/mocked 재검토
no_findings였다. 해당 SHA 등록6검사21/10/32/9/23/SDD도 PASS. 전체 변경/CI/사람 승인과는
별도 증거다. 앞선9a57bd3 원격 CI에서 다른 handoff/metrics fixture가 실패해 현재 보완 중이며
최종 CI·최신 SHA 검토 전 완료로 표시하지 않는다.
