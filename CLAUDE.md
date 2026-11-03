# 집담 — Claude Code 프로젝트 규칙

@AGENTS.md
@outputs/budongi_mvp_temp/AGENTS.md

공통 계약은 위 파일과 관련 Spec·ADR·Task를 따른다. 작업 전 `.agents/skills/jipdam-workflow/SKILL.md`를 읽는다.
`python -X utf8 scripts/bootstrap.py --host both`는 고정 gstack commit에서 Codex(`.agents/skills/`)와 Claude host-native skills(`.claude/skills/`)를 함께 등록한다. `--host claude` 또는 `--host codex`는 그 host만 갱신하고 다른 host 등록본은 지우지 않는다. 프로젝트를 다시 연 뒤 `/gstack-investigate`, `/gstack-review` 등으로 호출할 수 있다. gstack skill은 Claude Code의 도구 권한·Git 승인 설정을 바꾸지 않는다. 일반 개발과 검증은 루트 README의 공통 명령을 사용한다.
