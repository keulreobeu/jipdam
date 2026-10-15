# CLI-First App-Managed Harness 실행 계획

기존 contracts의 경로/비밀/해시와 GMS runner를 재사용한다. v1 Store/Mock Gateway는 호환 보존한다.
확장 상태는 독립 managed DB, 최소 Python 모듈로 작업·라우팅·검증·프로세스·격리를 나눈다.
App은 Python CLI를 실행하며 존재하지 않는 App API나 버튼을 가정하지 않는다.

1. CLI 설치/옵션·로그인 확인, 기존 하네스·출처 조사.
2. Spec/ADR/Task, SQLite 상태·관리 CLI·실행기·worktree·worker 구현.
3. Mock/fake CLI/실제 임시 Git E2E, 독립 리뷰·수정·기존 회귀/SDD.
4. 실제 CLI 최소 read-only smoke, GMS 준비 상태와 미검증 경계 기록.

검토 항목: 상태와 이벤트의 원자성, 프로세스 사망과 lease, Git scope·승인 게이트,
429/quota 구분·무변경 전환, 테스트의 신뢰 경계, 로그/컨텍스트 비밀 제외.
새 외부 데이터 수집·매칭·push·merge·배포는 실행하지 않는다.
