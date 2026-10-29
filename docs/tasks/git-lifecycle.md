# TASK-GIT-AUTO-001 — KAN-29

```toml
kind = "task"
id = "TASK-GIT-AUTO-001"
status = "verified"
owner = "keulreobeu"
specs = ["docs/specs/git_lifecycle_spec.md"]
scope = ["harness/__main__.py", "outputs/budongi_mvp_temp/src/jipdam_harness/git_lifecycle.py", "outputs/budongi_mvp_temp/src/jipdam_harness/git_cli.py", "outputs/budongi_mvp_temp/tests/test_git_lifecycle.py", "tooling/git-lifecycle.json", "tooling/codex-agents/gstack_committer.toml", ".codex/config.toml", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", ".agents/skills/jipdam-workflow/SKILL.md", "docs/git-lifecycle.md", "docs/specs/git_lifecycle_spec.md", "docs/adr/ADR-004-delegated-git-publication.md", "docs/tasks/git-lifecycle.md", "docs/sdd.md", "docs/sdd/traceability.json", "README.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/wiki/pages/WIKI-3B0062F3268E3C7A.md"]
acs = ["GIT-AUTO-001-AC-01", "GIT-AUTO-001-AC-02", "GIT-AUTO-001-AC-03", "GIT-AUTO-001-AC-04", "GIT-AUTO-001-AC-05"]
[[verification]]
command = ".venv/Scripts/python.exe -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_git_lifecycle.py -v"
result = "passed"
evidence = "docs/tasks/git-lifecycle.md#runtime-verification"
acs = ["GIT-AUTO-001-AC-01", "GIT-AUTO-001-AC-02", "GIT-AUTO-001-AC-03", "GIT-AUTO-001-AC-04"]

[[verification]]
command = "C:/Users/SSAFY/Desktop/jipdam/.venv/Scripts/python.exe -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "docs/tasks/git-lifecycle.md#publisher-verification"
acs = ["GIT-AUTO-001-AC-01", "GIT-AUTO-001-AC-02", "GIT-AUTO-001-AC-03", "GIT-AUTO-001-AC-04", "GIT-AUTO-001-AC-05"]

```

2026-10-29 현재 대화의 직접 실행 승인. Jira [KAN-29](https://kwulreobeu.atlassian.net/browse/KAN-29).
기존 미저장 제품/수집/위키/서브에이전트 설정은 보존한다. origin/main 기반 publisher에는 이번
자동화의 변경 부분만 전달한다. main 병합이나 branch 삭제 없이 실제 push 브랜치를 남긴다.

- [x] GIT-AUTO-001-AC-01 scope·source/index·스냅샷·공통 잠금
- [x] GIT-AUTO-001-AC-02 단계별 commit/push·실패/재시도·민감정보
- [x] GIT-AUTO-001-AC-03 실제 publisher 검증과 증거 무효화
- [x] GIT-AUTO-001-AC-04 branch-only 및 finish/receipt 게이트
- [x] GIT-AUTO-001-AC-05 로컬 활성화·서브에이전트 전달·SDD

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


## Publisher verification

git_committer 서브에이전트가 origin/main 기준의 격리 publisher에서 source 경로를 publisher에
고정하고 전체 verify_environment를 실행해 exit 0을 확인했다. 제품 테스트 300개(192.868초),
공통 도구 테스트 35개(2.317초), 합성 CLI smoke가 모두 성공했다. 새 Git 통합 17개도 이 실행에
포함된다. SDD는 features17/AC97/tasks39/changed_paths18을 통과했고 8개 CLI help도 exit 0이다.
최종 stage 확인에서 테스트 EOF의 빈 줄 1개를 발견해 고정 사본 v2로 수정했다.
실행 코드·테스트 assertions는 바뀌지 않았으며 staged whitespace/SDD를 다시 검사한다.
원본 checkout의 미저장 제품/위키/설정은 포함하지 않고 origin/main에 이번 overlay만 합성했다.

## Local activation and wiki

현재 `.codex/config.toml`은 기존 다섯 역할을 보존하고 gstack_committer를 추가했다.
프로젝트 정책 enabled=true이며 기존 managed autocommit은 false를 조회하고 false로 유지했다.
전담 역할은 legacy autocommit 경로를 다시 켜지 않고 스냅샷 저장만 수행한다.
현재 세션의 실제 commit/push는 git_committer worker가 수행했고 메인은 Git 쓰기를 하지 않았다.

위키 maintenance/catalog/search/event 결과는 CREATE / verified_reusable_knowledge다.
기존 6개 원격 문서와 local catalog를 확인했으며 Git 실제 쓰기·복구 계약은 기존 역할 개요와
독립된 주제로 판단했다. WIKI-3B0062F3268E3C7A revision1을 게시하고 전체 HTML을 다시 읽었다.
[게시 문서](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/2129921),
remote version1, hash89dc091baa0327281a9701c86de153709363eb65c7fb5a5f937afee4ebc3b2dc.
공식 connector receipt와 Jira comment10144의 receipt가 DONE이며 decision.blocking=false,
execution=DONE, pending=[]를 확인했다. 원본은 docs/git-lifecycle.md 해시
34d9aaf228fe657661ec5e24d9f4b138679039c8434ddd628960bfef9c944013이다.
문서는 미병합 branch/local 버전으로 실제 main 병합/삭제/배포를 완료했다고 게시하지 않았다.


## Branch delivery

실행 코드 전달: git_committer 서브에이전트가 단계2를
5b8508f6b95a0d200d8f79a75ba79b3a64b091a3에 커밋했고 origin의 정확한 branch ref를
push 후 ls-remote로 다시 읽어 같은 SHA를 확인했다. 단계1의 부모는 유지했다.
[자동화 전용 branch](https://github.com/keulreobeu/jipdam/tree/codex/git-lifecycle-kan29).
최종 문서/정책/위키 결과는 같은 branch에 후속 단계로 저장하며 source/index는 보존한다.
현재 요청의 branch_only 범위를 완료하고 main 병합·branch 종료는 실행하지 않는다.
