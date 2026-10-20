# Team Environment Spec

기준: 2026-10-01, 팀원이 GitHub checkout에서 설치하고 작업할 수 있도록 정리하라는 사용자 요청.

## 계약

- 공유 저장소의 루트는 이 워크스페이스다. 애플리케이션 경로 `outputs/budongi_mvp_temp/`를 유지하고 루트 README에서 설치·검증·개발 진입점을 제공한다. 제품 코드·데이터·Tool 계약을 이번 작업에서 변경하지 않는다.
- Python 3.11 이상으로 모델 없이 기본 검증을 실행한다. Git, Bun 1.3.14 이상, Node.js 22 이상은 전체 gstack 설치에 필요하다. Windows는 Git for Windows의 Bash를 사용하고 Linux/macOS는 Bash를 사용한다.
- gstack 원본은 `tooling/gstack.lock.json`의 정확한 commit에서 `.local_runtime/tooling/.agents/skills/gstack/`로 받는다. 전체 bootstrap은 `--host codex` 또는 `--host claude`를 요구하며 선택된 host의 upstream setup/render와 프로젝트 등록만 실행한다. 사용자 전역 host 설정을 변경하지 않는다.
- 공유하는 스킬 원본은 `.agents/skills/jipdam-workflow/`다. Codex와 Claude Code용 gstack 스킬 지원은 모두 저장소에 두고, 선택한 host의 생성본만 각 프로젝트 탐색 경로에 등록하며 Git 대상에서는 제외한다. 원본·fixture·선택하지 않은 host용 스킬이 프로젝트 탐색 경로에 들어가지 않는다. host를 전환하면 installer marker가 일치하는 이전 등록본만 제거한다.
- 제품 개발과 Python 검증은 Codex·Claude Code·Antigravity에서 같은 명령과 계약을 사용한다. Claude Code는 `CLAUDE.md`로 공통 규칙을 import하고 `.claude/skills/`에서 Claude host native gstack을 읽는다. Antigravity는 `AGENTS.md`를 사용하며 Codex manifest 호환은 검증됐다고 보지 않는다.
- 설치는 요청한 commit과 Bun lockfile을 확인한다. 다른 commit의 기존 checkout은 자동 reset하지 않는다. 설치 실패 시 완료로 보고하지 않는다.
- 별도 경로로 옮긴 checkout에서 기본 검증·전체 gstack 설치·스킬 중복 검사·브라우저 smoke를 확인한다. 실제 모델·데이터 평가는 별도 완료 조건이다.

## Acceptance Criteria

- [x] 루트 README와 플랫폼별 설치 진입점이 있다.
- [x] 실제 코드 테스트와 합성 스냅샷 조회가 네트워크·모델·실데이터 없이 통과한다.
- [x] Git 공유 대상에 런타임·모델·원천 데이터·원본 gstack Git 저장소가 없다.
- [x] Codex 스킬 경로에는 고정 gstack 56개와 프로젝트 전용 스킬의 고유 manifest만 있다.
- [x] host 선택은 Codex와 Claude Code 중 하나만 설치하며 반대 host의 프로젝트 gstack 등록본을 남기지 않는다.
- [x] 새 checkout에서 고정 commit의 전체 gstack 설치와 브라우저 smoke가 통과한다.
- [x] GitHub CI가 기본 검증을 실행하고 첫 Windows/Linux × Python 3.11/3.12 실행이 모두 성공했다. 근거는 [검증 기록](team_environment_validation.md#github-게시와-ci)에 있다.

SDD 확장 계약·적용 상태는 별도 [SDD Spec](specs/sdd_workflow_spec.md)과 [도입 Task](tasks/sdd-adoption.md)를 따른다.
