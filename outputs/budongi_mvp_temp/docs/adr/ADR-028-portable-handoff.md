# ADR-028 — WIP artifact와 실행 원장 분리

Accepted 2026-11-03, 사용자 v5.4 실행 요청. [HANDOFF-001](../specs/28_handoff_spec.md).

기존 pause/lease를 stop ACK로 사용하고 index/worktree를 따로 content-addressed 보관한다.
전체 .local_runtime/SQLite나 source Git history 복사는 민감정보와 다른 작업을 포함하므로 채택하지 않는다.
publish는 정상 commit/hooks를 사용하는 분리 artifact worktree와 orphan branch다.
restore는 검증된 원격 base에 payload를 적용한 새 저장소·새 작업이며 예전 세션이 아니다.
비검증 WIP 보존과 main 준비 판정은 별도이므로 backup에서 제품 테스트·AI 요약을 실행하지 않는다.
GMS 정책은 코드에서 기본 동결하며 legacy mock 테스트 외에 해제 경로를 제공하지 않는다.

독립 검토 반례에 따라 복원 clone은 기존 영수증·소유 경로·base SHA를 재검증해 재백업한다.
임의 foreign repo를 허용하는 완화는 하지 않는다. 파일/디렉터리 교체는 삭제/빈 디렉터리/쓰기
순서로 적용하며 재귀 삭제하지 않는다. v2 fingerprint는 실행 mode까지 포함한다. 초기 영수증의
알고리즘을 추정 변환하거나 수동 변경을 덮어쓰지 않고 별도 검토 상태로 보존한다.
