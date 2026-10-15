# 하네스 복구 안내

GMS LUNA 초안을 로컬에서 명령·상태 계약과 대조해 검토했다.

| 상황 | 안전한 처리 |
|---|---|
| 중복 worker 또는 lock 오류 | `python -m harness status --task <task-id>`로 상태를 확인하고 lock을 우회하지 마세요. |
| worker가 죽은 것으로 보임 | 상태와 PID를 확인하고 해당 PID가 실제로 종료됐는지 검증한 뒤 `python -m harness resume --task <task-id> --recover-running`을 실행하세요. |
| 일반적인 429 응답 | 할당량 초과로 단정하지 말고 제한된 횟수만 재시도하세요: `python -m harness retry --task <task-id>`. |
| quota 오류와 함께 파일이 변경됨 | 자동으로 provider를 바꾸지 마세요. `python -m harness status --task <task-id>`로 상태를 확인하고 task worktree의 변경 사항을 검토하세요. |
| GMS 요청 결과가 불확실함 | 자동 재시도하지 말고 기존 budget ledger를 직접 확인하세요. |
| GMS 초안이 `WAITING_FOR_APPROVAL` | task worktree에서 초안을 직접 검토·적용한 뒤 `python -m harness validate --task <task-id>`로 검증하고, 검토 후 `python -m harness approve --task <task-id> --reviewer <reviewer>`를 실행하세요. |
| `REVIEW_REQUIRED` | diff를 직접 검토한 뒤 승인할 때 `python -m harness approve --task <task-id> --reviewer <reviewer>`를 실행하세요. |
