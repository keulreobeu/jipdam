# 집담 — Claude Code 프로젝트 규칙

@AGENTS.md
@outputs/budongi_mvp_temp/AGENTS.md

공통 계약은 위 파일과 관련 Spec·ADR·Task를 따른다. 작업 전 `.agents/skills/jipdam-workflow/SKILL.md`를 읽는다.
`python -X utf8 scripts/bootstrap.py --host claude`는 고정 gstack commit에서 Claude host-native skills만 생성해 프로젝트 `.claude/skills/`에 등록한다. Codex용 스킬 설치가 필요하면 `--host codex`를 선택한다. 프로젝트를 다시 연 뒤 `/gstack-investigate`, `/gstack-review` 등으로 호출할 수 있다. gstack skill은 Claude Code의 도구 권한·Git 승인 설정을 바꾸지 않는다. 일반 개발과 검증은 루트 README의 공통 명령을 사용한다.
