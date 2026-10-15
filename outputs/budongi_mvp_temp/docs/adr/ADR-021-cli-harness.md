# ADR-021 — Additive CLI-managed execution

Status: Accepted, 2026-10-15 사용자 첨부 계획 실행 요청.

HARNESS-001의 native 역할 Store와 Mock 예산 계약은 유지한다. 별도 managed DB는
새 lifecycle/provider/worktree/approval 필드의 호환성 충돌을 피한다. contracts와
기존 LocalGMSWork를 재사용하여 provider별 인증·예산의 이중 구현을 막는다.

Codex는 로컬에서 확인한 exec --json을 사용한다. worker는 App 밖에서도 실행하는 Python 프로세스다.
모든 코드 실행은 HEAD에서 만든 별도 worktree에서 진행하며 자동 병합하지 않는다.
GMS는 이미 검증된 Responses 초안 생성만 노출하고 tool/shell 실행을 주장하지 않는다.
따라서 quota 전환 후 GMS 초안은 검토/수동 적용/재검증이 필요하다.

SQLite 이벤트가 정본이고 JSONL/report는 재생성 가능하다. OS sandbox는 Codex 담당이며
scope는 사후 변경 검사다. 앱과 별도 CLI의 같은 checkout 쓰기는 이 구조에서 수행하지 않는다.
