# TASK-GSTACK-AGENTS-001 — gstack 서브에이전트 설정

```toml
kind = "task"
id = "TASK-GSTACK-AGENTS-001"
status = "verified"
owner = "Codex"
specs = ["docs/specs/sdd_workflow_spec.md", "docs/team_environment_spec.md"]
scope = [".codex/config.toml", "tooling/codex-agents/", "docs/gstack-subagents.md", "outputs/budongi_mvp_temp/docs/wiki/pages/", "docs/tasks/gstack-subagents-20261028.md", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/docs/tasks/current.md"]
acs = ["SDD-001-AC-03"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "docs/tasks/gstack-subagents-20261028.md"
acs = ["SDD-001-AC-03"]
```

2026-10-28 사용자 요청; Jira [KAN-25](https://kwulreobeu.atlassian.net/browse/KAN-25). 기존 하네스 전용 역할은 유지하고 독립적인 gstack 역할을 추가한다.

| 역할 | 스킬 | 책임 |
| --- | --- | --- |
| gstack_planner | gstack-plan-eng-review | 설계와 AC 검토 |
| gstack_reviewer | gstack-review | 코드 리뷰 |
| gstack_investigator | gstack-investigate | 원인 조사 |
| gstack_qa | gstack-qa-only | CLI/API 읽기 전용 QA |
| gstack_docs | gstack-document-release | 문서 불일치 조사 |

역할은 부모가 명시적으로 배정할 때 사용한다. 각 역할은 집담 계약과 스킬을 읽고 근거 및 제한을 보고한다. 독립 조사 역할은 파일을 수정하지 않으며 기존 승인·원격 작업·실데이터 경계를 유지한다. 기존 하네스 역할과 두 서브에이전트 동시 실행 한도를 유지한다.

- [x] SDD-001-AC-03 설정 및 검증을 이 Task에 연결한다.

검증 진행: 역할 TOML 다섯 개와 설정의 상대 경로·실제 스킬 파일을 Python tomllib로 확인했고 `python -X utf8 scripts/check_sdd.py` 및 `--base origin/main`이 통과했다. 기존 사용자 수정은 보존했다. 기본 샌드박스의 전체 검사는 임시 디렉터리와 loopback 제약으로 실패했다. 권한 조정 후 재검사는 323개 중 1개가 디렉터리 rename의 WinError 5로 실패했으며, 해당 단일 테스트는 재실행 시 통과했다. 전체 검사가 통과한 것으로 표시하지 않는다. 실제 새 Codex 세션에서의 역할 호출은 아직 확인하지 않았다. 위키 maintenance/catalog/search 후 이벤트 TASK-GSTACK-AGENTS-001-20261028은 검증 미완료로 REVIEW_REQUIRED, blocking이다. 원격 게시 없음. Jira KAN-25는 진행 중으로 유지한다.

참고: [cannedJean/claude-skills](https://github.com/cannedJean/claude-skills)의 agy-delegate / agy-outsource에서 범위·산출물·AC·독립 검증·결과 보고 원칙을 참고했다. Codex 역할은 동일한 파일시스템을 공유하므로 격리 또는 hidden test 비밀을 주장하지 않는다. Antigravity/Claude CLI와 외부 스킬은 설치하거나 실행하지 않았다.

후속 SDD 재검사에서는 작업 중 별도로 생긴 미등록 Task `outputs/budongi_mvp_temp/docs/tasks/kan8-existing-data-20261028.md` 때문에 실패했다. 해당 파일은 이 작업에서 변경하지 않는다. Jira 댓글 10084에 결과를 기록했다.

## 2026-10-28 후속 검증

- 실제 Codex CLI 신규 세션에서 다섯 역할을 인식했다. `gstack_planner`, `gstack_reviewer`, `gstack_investigator`, `gstack_qa`, `gstack_docs`의 생성과 완료 이벤트를 각각 세션 원본 기록에서 확인했다. 각 스킬의 전체 업무 절차는 실행하지 않은 역할 생성 smoke다.
- 사용자 임시 폴더를 작업공간 내부로 설정하고 `.venv/Scripts/python.exe -X utf8 scripts/verify_environment.py`를 재실행했다. SDD 통과, 제품 unittest 323개와 팀 unittest 35개 통과, 합성 CLI smoke 통과, 종료 코드 0이다. 앞선 전체 검사 실패와 단일 재실행 기록은 위에 보존한다.
- 기능 QA 보고서와 원본 이벤트 증거는 로컬 `.local_runtime/gstack-role-qa-20261028/`, `gstack-role-qa-persistent/`, `gstack-role-qa-remaining/`에 보존한다. CLI 간략 JSON은 자식 생성 이벤트를 출력하지 않아 세션 원본의 started/completed 이벤트로 확인했다.
- 위키 판단 이벤트 `TASK-GSTACK-AGENTS-001-20261028`은 검증 전 REVIEW_REQUIRED로 기록되었다. 검증 완료에 따른 후속 판단·동기화는 진행 중이다.

## 위키 판단 및 완료

후속 이벤트 TASK-GSTACK-AGENTS-001-VERIFIED-20261028: CREATE / verified_reusable_knowledge / DONE / nonblocking. 검증된 역할 선택 안내이며 보안·핵심 운영 절차를 변경하지 않는 저위험 문서다. WIKI-6EFA6AB497CA1504 revision 1을 [Confluence](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/1409025/WIKI-6EFA6AB497CA1504+gstack)에 게시했고 실제 읽기 결과 버전 1 및 SHA-256 6996f08c7287dc889eb6153e7fa1b53ff41420d9adfbe1cb436000af1a76e259을 기록했다. Jira 댓글 10094 및 양쪽 delivery receipt DONE. 기존 이벤트 REVIEW_REQUIRED는 후속 이벤트로 해결됐다. 다른 작업의 WIKI-E162D573DBB6F1CD review 대기는 이번 작업 범위 밖이다.
