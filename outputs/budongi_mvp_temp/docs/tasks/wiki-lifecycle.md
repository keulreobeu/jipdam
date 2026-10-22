# TASK-WIKI-001 — Wiki lifecycle automation

```toml
kind = "task"
id = "TASK-WIKI-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/25_wiki_lifecycle_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/jipdam_harness/", "outputs/budongi_mvp_temp/tests/test_wiki_lifecycle.py", "outputs/budongi_mvp_temp/docs/wiki/", "outputs/budongi_mvp_temp/docs/specs/25_wiki_lifecycle_spec.md", "outputs/budongi_mvp_temp/docs/tasks/wiki-lifecycle.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/harness/CLI_OPERATIONS.md", "outputs/budongi_mvp_temp/docs/adr/ADR-024-wiki-lifecycle.md", "docs/sdd/traceability.json", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", ".agents/skills/jipdam-workflow/SKILL.md", "docs/sdd.md"]
acs = ["WIKI-001-AC-01", "WIKI-001-AC-02", "WIKI-001-AC-03", "WIKI-001-AC-04"]

[[verification]]
command = "python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_wiki_lifecycle.py -q"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/wiki/VALIDATION.md"
acs = ["WIKI-001-AC-01", "WIKI-001-AC-02", "WIKI-001-AC-03", "WIKI-001-AC-04"]

[[verification]]
command = "python -X utf8 -m unittest discover -s tests -q (product and workspace roots); TASK-WIKI-001 scoped check_sdd.validate"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/wiki/VALIDATION.md#완료-기록"
acs = ["WIKI-001-AC-04"]
```

Jira: [KAN-19](https://kwulreobeu.atlassian.net/browse/KAN-19). 사용자 첨부 v1.0을 승인 근거로 한다.
기존 대량 미커밋 작업을 보존하고 현재 요청의 경로만 수정한다.

- [x] WIKI-001-AC-01 판단/중복/근거
- [x] WIKI-001-AC-02 게시/보안/멱등/충돌
- [x] WIKI-001-AC-03 상태/재검토/병합/검색
- [x] WIKI-001-AC-04 하네스/복구/운영

## Design

기존 native Store/managed 실행 DB는 보존하고 wiki 전용 SQLite를 추가한다.
하네스 검증 결과에 wiki 판단을 연결하되 결과 worktree 파일을 App에서 수정하지 않는다.
규칙 기반 분류/템플릿을 기본으로 하고 의미/근거 검토는 명시 reviewer와 catalog 해시에 묶는다.
Confluence 검색에서 현재 프로젝트 위키를 찾지 못했으므로 외부 대상 추정은 하지 않는다.

후속 사용자 지정 공간 확인: space 65816/homepage65913 아래 `집담 개발 위키`(360449)를 생성했다.
정책 원문은131074다. 팀원도 같은 위키를 사용하고 권한 부족 시 관리자에게 본인 계정의
보기·작성·편집 권한을 요청하도록 안내한다. 개인 OAuth는 공유하지 않는다.
GMS SOL 초안 검토를 기존 runner/8786으로 시도했으나 로컬 설정 서버 미연결로 차단됐다.
유료 호출·키 우회 없이 로컬 담당자가 구현·검토·검증했다.

## Validation

실제 실행 결과와 전체 환경 검사 한계는 [검증 기록](../wiki/VALIDATION.md)에 보존한다.
Confluence full read-back 및 Jira10043 댓글 영수증으로 실제 동기화를 확인했다.
판단 CREATE2/UPDATE2, ACTIVE2, 외부 동기화 대기0으로 완료했다.
최종26개 위키 검사에 팀원 clone 복원·수동 변경 차단을 포함한다. managed13개는 샌드박스
파일 교체 제한이 발생해 제한 밖에서 재확인했다. 사용자별 계정 권한을 실제 부여한 것은 아니다.
