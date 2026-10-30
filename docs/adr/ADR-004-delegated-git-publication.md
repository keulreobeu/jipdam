# ADR-004 — Delegated Git publication from immutable snapshots

Accepted, 2026-10-29 사용자 요청. 계약: [GIT-AUTO-001](../specs/git_lifecycle_spec.md).

메인 에이전트의 source checkout과 committer의 publisher worktree를 분리한다.
같은 checkout에서 메인이 편집하는 동안 서브에이전트가 stage/commit하면 검증하지 않은
파일 버전이나 다른 작업의 index가 섞일 수 있다. 고정 bytes 스냅샷을 handoff하고 publisher만
commit함으로써 source 편집을 계속할 수 있게 한다. 작업 시작 기준과 단계별 검증 HEAD는 구분한다.

기존 managed harness는 고정 base_commit에서 최종 검증/승인한 뒤 한 번 autocommit하는 계약이다.
그 내부의 HEAD 검사만 느슨하게 바꾸면 검증 증거가 틀어지므로 별도 git management 경로를 추가한다.
공유 상태와 잠금은 Git common directory로 식별한다. 다른 PC의 원격 경합은 Git의 non-force
push 및 GitHub 보호·조건부 병합으로 처리한다. GitHub 인증은 기존 connector/개인 Git 인증을 쓴다.

새 전용 daemon/주기적 자동 커밋/키 복사는 추가하지 않는다. agent가 단계 이벤트를 보내는 시점에
실행하며, 명시적 branch_only 전달은 병합하지 않는다. 메인은 판단과 검증, committer는 Git 쓰기를
담당한다. 역할 규칙은 업무 분담이며 인증·보안 격리가 아니다.
