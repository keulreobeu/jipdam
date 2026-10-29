# TASK-GIT-AUTO-001 — KAN-29

```toml
kind = "task"
id = "TASK-GIT-AUTO-001"
status = "in_progress"
owner = "keulreobeu"
specs = ["docs/specs/git_lifecycle_spec.md"]
scope = ["harness/__main__.py", "outputs/budongi_mvp_temp/src/jipdam_harness/git_lifecycle.py", "outputs/budongi_mvp_temp/src/jipdam_harness/git_cli.py", "outputs/budongi_mvp_temp/tests/test_git_lifecycle.py", "tooling/git-lifecycle.json", "tooling/codex-agents/gstack_committer.toml", ".codex/config.toml", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", ".agents/skills/jipdam-workflow/SKILL.md", "docs/git-lifecycle.md", "docs/specs/git_lifecycle_spec.md", "docs/adr/ADR-004-delegated-git-publication.md", "docs/tasks/git-lifecycle.md", "docs/sdd.md", "docs/sdd/traceability.json", "README.md", "outputs/budongi_mvp_temp/docs/tasks/current.md"]
acs = ["GIT-AUTO-001-AC-01", "GIT-AUTO-001-AC-02", "GIT-AUTO-001-AC-03", "GIT-AUTO-001-AC-04", "GIT-AUTO-001-AC-05"]
[[verification]]
command = ".venv/Scripts/python.exe -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_git_lifecycle.py -v"
result = "passed"
evidence = "docs/tasks/git-lifecycle.md#runtime-verification"
acs = ["GIT-AUTO-001-AC-01", "GIT-AUTO-001-AC-02", "GIT-AUTO-001-AC-03", "GIT-AUTO-001-AC-04"]

```

2026-10-29 현재 대화의 직접 실행 승인. Jira [KAN-29](https://kwulreobeu.atlassian.net/browse/KAN-29).
기존 미저장 제품/수집/위키/서브에이전트 설정은 보존한다. origin/main 기반 publisher에는 이번
자동화의 변경 부분만 전달한다. main 병합이나 branch 삭제 없이 실제 push 브랜치를 남긴다.

- [ ] GIT-AUTO-001-AC-01 scope·source/index·스냅샷·공통 잠금
- [ ] GIT-AUTO-001-AC-02 단계별 commit/push·실패/재시도·민감정보
- [ ] GIT-AUTO-001-AC-03 실제 publisher 검증과 증거 무효화
- [ ] GIT-AUTO-001-AC-04 branch-only 및 finish/receipt 게이트
- [ ] GIT-AUTO-001-AC-05 로컬 활성화·서브에이전트 전달·SDD

## 검증 및 전달

구현 중. 실행한 검사 결과와 원격 read-back만 기록한다. 기존 로컬 autocommit 테스트 9개의
성공은 이 원격 생명주기의 합격 증거로 재사용하지 않는다. 이전 검토의 중간커밋 차단/잠금
중복 획득 재현은 새 독립 경로의 회귀 기준이다.

GMS: `.venv/Scripts/python.exe -m harness providers`에서 local_server_unavailable 확인.
생성 호출 없음. 키 직접 조회·정책 변경·예산 우회 없음.

위키: 검증 뒤 실제 maintenance/catalog/search/event 및 필요 시 connector 동기화 결과를 추가한다.


## Runtime verification

2026-10-29: git_runtime 서브에이전트가 최신 코드의 실제 로컬 bare 원격 통합 테스트 17개를
81.988초에 모두 통과(exit 0)했다. source/index 보존, 고정 스냅샷 뒤 추가 편집,
공통 잠금, 다단계 저장, push 실패/응답 유실, history/민감정보, hook 변조,
Windows CRLF, 0건 테스트 거부, 최신 main 통합/충돌/재시도, branch_only를 확인했다.

현재 로컬 `python -m harness git --help`는 refresh-base를 포함한 8개 명령을 표시하며 exit 0이다.
역할 TOML·활성 정책을 파싱했고 기존 5개 미저장 역할과 빈 source index를 보존했다.
첫 단계는 git_committer 서브에이전트가 14개 자동화 규칙 파일만 커밋·push했다.
commit/read-back: 448c964309e511575b3f6f233f57cb17a423e039.
[첫 단계 CI](https://github.com/keulreobeu/jipdam/actions/runs/40828174060)는 success다.
실제 main 병합/branch 삭제는 현재 branch_only 전달에 포함하지 않으며 시험하지 않았다.
