# TASK-HANDOFF-001 / KAN-41

```toml
kind = "task"
id = "TASK-HANDOFF-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/28_handoff_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/jipdam_harness/handoff.py", "outputs/budongi_mvp_temp/src/jipdam_harness/handoff_cli.py", "outputs/budongi_mvp_temp/src/jipdam_harness/managed_cli.py", "outputs/budongi_mvp_temp/tests/test_handoff.py", "outputs/budongi_mvp_temp/docs/specs/28_handoff_spec.md", "outputs/budongi_mvp_temp/docs/plans/handoff-20261103.md", "outputs/budongi_mvp_temp/docs/adr/ADR-028-portable-handoff.md", "outputs/budongi_mvp_temp/docs/tasks/handoff.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/harness/HANDOFF.md", "outputs/budongi_mvp_temp/docs/harness/HANDOFF_VALIDATION_20261103.md", "docs/sdd/traceability.json"]
acs = ["HANDOFF-001-AC-02", "HANDOFF-001-AC-03", "HANDOFF-001-AC-04"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/harness/HANDOFF_VALIDATION_20261103.md"
acs = ["HANDOFF-001-AC-02", "HANDOFF-001-AC-03", "HANDOFF-001-AC-04"]
```

- [x] HANDOFF-001-AC-02 중단 ACK·scope·경로/비밀·한도·index 보존.
- [x] HANDOFF-001-AC-03 임시 bare 원격/독립 clone SHA 검증과 새 작업 복원·반례.
- [x] HANDOFF-001-AC-04 모델 0회와 실제 로컬 시간·결과 구분.

기준 main=f29ad3d50215fdcd61f9bf034b1c049e06a0e2ac. branch_only.
실제 PC A→B 증거는 아직 없으며 원격 read-back/독립 로컬 복원과 구분한다.
후속 TASK-LEAN-CHECK-001, TASK-LEAN-METRICS-001, LIGHT/STANDARD/STRICT,
Finish, GGUF/Claude는 이 Task의 구현 완료 조건이 아니다.

2026-11-03 v5.4.1 delta: 같은 KAN-41에 연결한다. 별도 Task/PR/장문 review pack은 생성하지 않는다.
운영 기준/최소 템플릿은 [HANDOFF.md](../harness/HANDOFF.md#조건부-독립-검토--v541)를 재사용한다.
구현 후보는 STRICT이며 독립 검토 전 independent_review_pending이다. backup 실행은 이 상태로 막지 않는다.
후보 snapshot 시 review_requested=true, review_invoked=false, review_skipped_reason=fixed_sha_pending,
new_artifacts_created_for_review=0, chat_tokens=unknown. 고정 SHA 이후 결과/범위·한계를 같은 Task에 기록한다.
RV-01~12의 자동 라우팅/계측/Finish는 DESIGNED_ONLY이며 이번 delta 문서 반영을 실사용 평가로 세지 않는다.

수정 후 전체 Python/SDD/합성 검증 passed(제품383/팀35, 실제 실행 로그). 구현 후보의 고정 SHA 독립 검토는 KAN-41의
해당 SHA 댓글에 기록한다. 사용자 명시 승인 후 실제 원격 WIP artifact 게시와 독립 clone 복원을
확인했다(세부 SHA/시간은 검증 기록). 물리 PC 간 실행은 미측정이다. 후속 POSIX mode 수정은
handoff 19개 회귀를 통과했다. 코드 최종 게시·STRICT 독립 검토 전 status는 in_progress이며
고정 SHA의 검토 결과와 관련 한계는 KAN-41에서 확인한다. Jira는 열어 둔다.
위키 판단 SKIP/미게시: 사용자 v5.4.1의 기존 근거 재사용·장문 생성 금지에 따른다.

독립 검토 cfbce84259dcc8a9175700de412d49e9c9037037의 findings 4건을 수정했고 handoff23개,
전체383/35를 통과했다. 원래 결과를 지우지 않고 KAN-41 댓글10196에 보존했다.
새 후보 SHA에 재검토가 필요하다. CI/물리 PC 시험은 미확인이며 main 준비 완료로 표시하지 않는다.

2026-11-03 CI 조회 정정: SHA70f7408의 Actions41574411502는 push 마지막 변경의
검증 문서에 같은 commit에서 갱신한 Task가 없어 SDD 실패였다. --base origin/main 검사와
push before..after 범위의 차이를 기록한다. 후속 KAN-42에 포함한 HANDOFF 회귀는 Ubuntu에서
의도적 CRLF WIP를 diff whitespace 오류로 판정해2건 실패했다. 합성 base에 CRLF를 허용하되
통상 trailing-space 검사는 유지하는 .gitattributes를 명시했고 진짜 trailing spaces 거부 반례를
추가했다. runtime backup/restore나 사용자 Git whitespace 설정은 변경하지 않았다.
CI/실제 물리 PC 게이트는 여전히 미완료이며 최신 결과는 KAN-42의 검증 기록을 따른다.
