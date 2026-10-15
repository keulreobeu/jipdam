# 개발 하네스·CLI 팀 공유 요약

마지막 정리: 2026-10-15. 이 문서는 현재 구현과 검증 경계를 빠르게 공유하기 위한 안내다. 세부 계약·명령은 [CLI 운영 안내](CLI_OPERATIONS.md), [구조](CLI_ARCHITECTURE.md), [구현·검증 기록](CLI_IMPLEMENTATION_REPORT.md), [현재 Task](../tasks/cli-harness.md), [운영 후속 Task](../tasks/harness-operations.md)를 기준으로 한다.

## 지금까지 만든 것

- 기존 `scripts/agent_harness.py`와 HARNESS-001 수동/native 역할 인계·Mock Gateway를 보존했다.
- 새 `python -m harness` 관리 CLI를 추가했다. 작업 등록·계획·상태·우선순위·의존성·실행기 선택·worker·보고·일시정지·재개·취소·재시도·검증·승인을 관리한다.
- 상태와 이벤트는 `.local_runtime/harness-managed/`의 SQLite에 저장한다. 코드는 HEAD 기반 별도 Git worktree에서 실행하고, 범위·파일 해시·검증·승인 뒤에만 로컬 자동 커밋이 가능하다.
- Codex CLI 비대화형 실행, 기존 GMS 코드 초안 경로, 과금 없는 Mock을 연결했다. GMS 초안은 사람이 검토·적용하고 다시 검증한다.
- 사용자가 승인한 최신 GMS 최소 잔액 보존은 1,000크레딧이다. 잔액·사전 입력 카운트·최대 예약·기존 공통 원장을 재사용하며 native Codex GMS 호환성은 미검증 상태로 유지한다.
- 실제 Git worktree, worker 관리, 복구, provider, 검증, 자동 커밋 경계를 테스트하고 공식 전체 검증 결과를 [운영 기록](OPERATIONS_UPDATE_20261015.md#final-verification)에 남겼다.

## 도구별 지원 상태

| 도구/경로 | 현재 할 수 있는 일 | 관리 하네스와 연결 | 상태와 한계 |
| --- | --- | --- | --- |
| Codex CLI | `python -m harness run`을 통한 격리 작업·JSONL 결과·세션 재개·사용량 관측 | 직접 provider | 설치 CLI 0.162.1의 실제 read-only smoke 및 별도 worktree 관리 검증 완료. 인증은 각 팀원 로컬 계정을 사용 |
| Claude Code CLI | 같은 저장소 규칙·Spec·Task·검증 명령을 따라 수동으로 작업. 필요하면 기존 `agent_harness.py`에서 공통 task/context를 전달하고 결과를 제출 | 자동 provider 아님 | 공통 JSON/상태의 수동 인계 형태만 가능. Claude 프로세스 실행·세션 재개·usage 연결·네이티브 hook은 미구현·미검증 |
| Antigravity | 공통 `AGENTS.md`와 프로젝트 절차를 사용한 수동 작업·검증 | 자동 provider 아님 | native 실행·hook 미검증. 생성된 Codex 전용 gstack 스킬을 실행할 수 있다고 가정하지 않음 |
| GMS | 관리 하네스의 제한된 코드·테스트·문서 초안과 기존 예산 runner 사용 | draft provider | 연결된 credentials 서버가 준비됐을 때만 가능. 초안 수동 검토·적용·`validate`·승인이 필요. 현재 상태는 `providers` 명령으로 확인 |
| Mock | 오프라인 계약·상태 흐름 점검 | 직접 provider | 외부 호출·실제 과금 없음. 실제 모델 품질·CLI 동작의 증거는 아님 |

### Claude CLI를 하네스 실행기로 확장하는 경로

작업 정의는 provider와 분리된 JSON으로 유지한다. Claude CLI 지원을 자동 실행으로 높이려면 별도 provider가 승인된 task를 받아 비대화형 실행하고, 구조화된 결과·오류 분류·종료 코드·세션 재개·취소·사용량(제공되는 경우)을 공통 계약에 맞춰 돌려줘야 한다. 로컬 인증과 호출 예산을 분리하고, Codex 경로와 같은 context 비밀 제외·worktree·검증·승인 경계를 검증해야 한다. CLI 옵션과 출력 형식은 설치된 Claude CLI의 실제 도움말/문서 및 smoke로 확인한 뒤 구현한다. 현재 상태에서 `--host claude`는 수동 역할/인계 표시이며 Claude 실행을 시작하지 않는다.

## 팀 작업 시작과 관리 명령

모든 도구는 저장소 루트에서 시작하고 공통 `AGENTS.md`, 제품 `AGENTS.md`, 관련 Spec·ADR·Task를 읽는다. 먼저 기존 Task에 연결하고, 코드 작업은 명시 scope·AC·검증 명령이 담긴 JSON으로 관리한다. 상세 예시는 [운영 안내](CLI_OPERATIONS.md)를 사용한다.

```powershell
python -m harness providers
python -m harness status
python -m harness plan --request .local_runtime/harness-managed/plan.json
python -m harness new-task --request .local_runtime/harness-managed/task.json
python -m harness run --task TASK-ID
python -m harness report --task TASK-ID
python -m harness validate --task TASK-ID
python -m harness approve --task TASK-ID --reviewer operator
```

검증 성공만으로 승인/완료가 되지는 않는다. GMS draft는 담당자가 허용된 worktree에 적용한 후 검증한다. 팀원은 managed DB, credential, logs, raw data, DB 파일을 Git에 공유하지 않는다. 같은 managed runtime을 여러 checkout/App에서 동시에 편집하지 않는다. 기본 저장소 검증은 루트에서 `python -X utf8 scripts/verify_environment.py`; 변경 브랜치는 `python -X utf8 scripts/check_sdd.py --base origin/main`이다.

## 빠른 진실 확인

- 자동 관리 CLI: `python -m harness --help`
- 설치·현재 접근 가능한 실행기: `python -m harness providers` (로컬 상태라 팀원별로 다를 수 있음)
- 작업·검증 보고: `python -m harness report --task TASK-ID`
- 공통 SDD·전체 구현 기록: 위의 Spec·Task·검증 기록 링크
- `python -m harness`의 managed provider와 legacy `scripts/agent_harness.py --host ...`의 수동 인계는 다른 실행 경로다.
