# Claude Code용 gstack 연결

```toml
kind = "spec"
id = "CLAUDE-GSTACK-001"
status = "approved"
owner = "keulreobeu"
revision = 2
approved_by = "사용자"
approved_at = "2026-10-20"
approval_ref = "현재 대화: Claude Code에서도 gstack 스킬을 사용할 수 있도록 받아와 달라는 요청; 후속 요청에서 GitHub에는 Codex·Claude 지원을 함께 두고 실제 bootstrap은 현재 host 하나만 설치하도록 승인"
```

## CLAUDE-GSTACK-001-REQ-01 host별 스킬 등록

프로젝트 bootstrap은 `--host codex` 또는 `--host claude`를 필수로 받아 선택한 host 하나의 native skill만 설치한다. Claude 선택 시 `tooling/gstack.lock.json`에 고정된 원본의 upstream Claude renderer로 skill 문서를 생성해 프로젝트 `.claude/skills/`에 등록한다. Claude 문서는 Codex용 manifest를 재사용하지 않고 upstream Claude renderer 결과를 사용한다. helper와 state 참조는 프로젝트의 무시된 `.local_runtime/`에 연결한다. GitHub에는 양쪽 host의 설치 지원을 함께 보존한다.

### CLAUDE-GSTACK-001-AC-01

locked commit의 고유 Claude skill 56개가 `.claude/skills/`에서 검색되고 frontmatter 이름이 각 skill 폴더와 일치한다.

### CLAUDE-GSTACK-001-AC-03

`--host claude` 설치 후 프로젝트 gstack 검색 경로에는 Claude 등록본만 있고, `--host codex` 설치 후에는 Codex 등록본만 있다. host 전환은 이 프로젝트 installer marker와 lock이 일치하는 이전 등록본만 제거한다.

## CLAUDE-GSTACK-001-REQ-02 사용자 설정·권한 경계

등록은 Claude 전역 settings와 사용자 전역 skill을 변경하지 않는다. 이름이 충돌하는 사용자 소유 프로젝트 skill을 덮어쓰지 않는다. gstack은 Claude Code의 도구 권한, Git 승인, 원격 push 권한을 변경하거나 우회하지 않는다.

### CLAUDE-GSTACK-001-AC-02

등록 대상은 프로젝트 `.claude/skills/gstack*`로 한정되고, 기존 user-owned skill 충돌은 오류로 거부되며, Git 권한은 host 설정의 책임임을 README와 skill 운영 문서에 알린다.
