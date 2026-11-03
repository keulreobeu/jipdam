# ADR-028 — WIP artifact와 실행 원장 분리

Accepted 2026-11-03, 사용자 v5.4 실행 요청. [HANDOFF-001](../specs/28_handoff_spec.md).

기존 pause/lease를 stop ACK로 사용하고 index/worktree를 따로 content-addressed 보관한다.
전체 .local_runtime/SQLite나 source Git history 복사는 민감정보와 다른 작업을 포함하므로 채택하지 않는다.
publish는 정상 commit/hooks를 사용하는 분리 artifact worktree와 orphan branch다.
restore는 검증된 원격 base에 payload를 적용한 새 저장소·새 작업이며 예전 세션이 아니다.
비검증 WIP 보존과 main 준비 판정은 별도이므로 backup에서 제품 테스트·AI 요약을 실행하지 않는다.
GMS 정책은 코드에서 기본 동결하며 legacy mock 테스트 외에 해제 경로를 제공하지 않는다.
