# ADR-022 — Budget-gated GMS routing and reviewed auto commits

Accepted, 2026-10-15 사용자 추가 지시.

최소 보존을1,000으로 낮추되 기존 공통 예산·원장 경로를 보존한다. Codex provider를 upstream GMS에
직접 연결하면 키/전체 요청 count/최대 비용 예약이 우회되므로 그렇게 설정하지 않는다.
native Responses/tool/stream 호환성은 로컬 protocol probe와 검증된 budget bridge가 필요하며
단순 Responses 텍스트 생성 성공을 Codex native 호환 성공으로 취급하지 않는다.

오토커밋은 사용자 승인 결과를 보존하는 별도 Git 단계다. 별도 임시 index로 허용 경로만 commit하고
사용자 index가 비어 있지 않으면 안전하게 보류한다. 민감 경로와 원본 데이터는 대상에서 제외한다.
실행 worktree는 codex/ 작업 브랜치에 연결하고 승인 후 로컬 commit하며 push/merge는 하지 않는다.
