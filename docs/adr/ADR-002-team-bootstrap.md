# ADR-002 — 팀 공유와 gstack 재현 설치

Status: Accepted (2026-10-01). 사용자 요청: 현재 환경을 팀 공유가 가능하도록 정리하고 반영한다.

## Decision

워크스페이스 루트를 공유 저장소로 만들되 현재 애플리케이션 경로는 유지한다. gstack은 submodule로 추가하지 않고 commit을 고정한 설치 스크립트로 관리한다. 원본 checkout은 Git에서 제외한 `.local_runtime/tooling/.agents/skills/gstack/`에 둔다.

공식 setup의 프로젝트 로컬 설치 탐지를 사용하기 위해 원본의 부모 경로를 `.agents/skills/`로 유지한다. 이 경로는 루트 스킬 탐색 경로 밖에 있다. setup 후 Codex용 manifest·metadata·section만 루트 `.agents/skills/`에 등록한다. 소스 전체·fixture·다른 host용 생성본을 복사하지 않는다.

## Reason

현재 source checkout을 `.agents/skills/gstack/`에 넣으면 Codex에 원본과 fixture 스킬도 노출된다. 또한 외부 Git 저장소를 그대로 Git add하면 팀원의 clone으로 원본을 복원할 관리 정보가 부족하다. 원본을 runtime에 두면 스킬 중복을 제거하고, 고정 commit과 upstream Bun lock으로 재설치를 관리할 수 있다.

## Consequences

팀원의 첫 전체 설치는 인터넷과 Git/Bun/Node/Bash가 필요하다. 모델 없는 기본 검증은 Python만으로 실행한다. Windows의 브라우저 QA를 실제 확인하고 Linux/macOS 설치 진입점은 제공하지만 이 PC에서 실행 검증했다고 주장하지 않는다.

집담 전용 개선은 추적되는 `jipdam-workflow`에 저장한다. gstack 자체 템플릿을 고치면 원본 checkout에 보존하되 팀 공유는 별도 fork와 lock 변경으로 배포한다. 설치 스크립트가 로컬 수정을 자동 reset하지 않는다.
