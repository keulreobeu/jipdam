# Team Environment Spec

기준: 2026-10-01, 팀원이 GitHub checkout에서 설치하고 작업할 수 있도록 정리하라는 사용자 요청.

## 계약

- 공유 저장소의 루트는 이 워크스페이스다. 애플리케이션 경로 `outputs/budongi_mvp_temp/`를 유지하고 루트 README에서 설치·검증·개발 진입점을 제공한다. 제품 코드·데이터·Tool 계약을 이번 작업에서 변경하지 않는다.
- Python 3.11 이상으로 모델 없이 기본 검증을 실행한다. Git, Bun 1.3.14 이상, Node.js 22 이상은 전체 gstack 설치에 필요하다. Windows는 Git for Windows의 Bash를 사용하고 Linux/macOS는 Bash를 사용한다.
- gstack 원본은 `tooling/gstack.lock.json`의 정확한 commit에서 `.local_runtime/tooling/.agents/skills/gstack/`로 받는다. upstream 공식 setup이 자기 로컬 namespace에 전체 런타임을 설치하고, 프로젝트 등록 단계가 Codex 스킬만 루트 `.agents/skills/`로 가져온다. 사용자 전역 Codex 설정을 변경하지 않는다.
- 공유하는 스킬 원본은 `.agents/skills/jipdam-workflow/`다. 생성된 gstack 스킬·원본·모델·캐시·로그·DB·API 인증키는 Git 대상에서 제외한다. 원본·fixture·다른 host용 스킬이 프로젝트 스킬 탐색 경로에 들어가지 않는다.
- 제품 개발과 Python 검증은 Codex·Claude Code·Antigravity에서 같은 명령과 계약을 사용한다. Claude Code는 `CLAUDE.md`로 공통 규칙을 import하고 Antigravity는 `AGENTS.md`를 사용한다. 전체 gstack의 자동 등록·실행 검증 범위는 현재 Codex이며 다른 host의 네이티브 실행 지원으로 보고하지 않는다.
- 설치는 요청한 commit과 Bun lockfile을 확인한다. 다른 commit의 기존 checkout은 자동 reset하지 않는다. 설치 실패 시 완료로 보고하지 않는다.
- 별도 경로로 옮긴 checkout에서 기본 검증·전체 gstack 설치·스킬 중복 검사·브라우저 smoke를 확인한다. 실제 모델·데이터 평가는 별도 완료 조건이다.

## Acceptance Criteria

- [x] 루트 README와 플랫폼별 설치 진입점이 있다.
- [x] 실제 코드 테스트와 합성 스냅샷 조회가 네트워크·모델·실데이터 없이 통과한다.
- [x] Git 공유 대상에 런타임·모델·원천 데이터·원본 gstack Git 저장소가 없다.
- [x] Codex 스킬 경로에는 고유한 57개 manifest만 있다.
- [x] 새 checkout에서 고정 commit의 전체 gstack 설치와 브라우저 smoke가 통과한다.
- [x] GitHub CI가 기본 검증을 실행하도록 설정되어 있다. 실제 GitHub 실행은 미검증이다.
