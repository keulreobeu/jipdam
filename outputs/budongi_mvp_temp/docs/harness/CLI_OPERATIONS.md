현재 사용자 지시의 GMS 최소 보존1,000·오토커밋은 [최신 후속 운영](OPERATIONS_UPDATE_20261015.md)을 우선한다.

# CLI-First 하네스 운영

위키는 [자동 관리 운영](../wiki/AUTOMATION.md)을 따른다. run/validate 검증 성공 뒤
판단을 report.result.wiki에 기록하고, 미완료 문서는 완료 승인 전에 해결한다.
worker는 매시간 재검토하며 Codex·Claude는 작업 종료 전 Confluence/Jira outbox를 처리한다.
팀원은 본인 Atlassian 인증을 사용하며 권한 부족 시 [요청 안내](../wiki/TEAM_ACCESS.md)를 제공하고 DRAFT/SYNC_PENDING을 보존한다.

저장소 루트에서 Python 3.11+로 실행한다. [설계](CLI_ARCHITECTURE.md),
[검증/구현 결과](CLI_IMPLEMENTATION_REPORT.md), [Task](../tasks/cli-harness.md).
기존 `scripts/agent_harness.py`는 HARNESS-001 수동/native 역할 인계를 계속 제공한다.
새 `python -m harness`가 App과 독립 worker의 자동 실행 관리 인터페이스다.

```powershell
./scripts/install_codex_cli.ps1
python -m harness providers
python -m harness status
python -m harness tasks --state FAILED
python -m harness tasks --state REVIEW_REQUIRED
python -m harness tasks --state WAITING_FOR_APPROVAL
```

CLI 설치는 공식 `npm install --global @openai/codex`다. 2026-10-15 독립 CLI 0.162.1을 설치하고
실제 `exec --help`, `exec resume --help`를 확인했다. App 내장 0.155.1과 공존하며 npm CLI를 먼저 찾는다.
로그인은 기존 Codex 인증을 사용하고 재설정하지 않는다. 필요할 때 사용자가 `codex login`을 수행한다.
실행 권한 우회 옵션은 사용하지 않는다.

작업 JSON은 `.local_runtime/harness-managed/task.json`처럼 Git 제외 경로에 저장한다.
App은 목표를 명시 작업·scope·AC·의존성으로 정리한 뒤 이 명령을 실행한다. `python -m harness plan --request PATH`는 {objective, tasks} JSON을 검수해 등록 전 실행 순서를 보여준다.
실제 등록은 검토된 각 task를 new-task로 수행한다. Python은 실행 순서를
결정하고 검증한다. 자연어를 임의로 테스트 성공 조건으로 바꾸지 않으며 별도 Planner LLM 호출은 필수가 아니다.

```json
{
  "task_id": "TASK-CLI-DEMO",
  "objective": "현재 커밋의 하네스 계약 테스트를 실행하고 결과를 정리한다",
  "priority": "normal",
  "scope": {
    "allowed_paths": ["outputs/budongi_mvp_temp/src/jipdam_harness", "outputs/budongi_mvp_temp/tests"],
    "forbidden_paths": []
  },
  "acceptance_criteria": ["기존 하네스 계약 테스트 통과"],
  "context_files": [],
  "depends_on": [],
  "execution": {
    "preferred_provider": "mock",
    "fallback_provider": "gms",
    "allow_fallback": false,
    "max_attempts": 2,
    "timeout_seconds": 120,
    "total_timeout_seconds": 300,
    "sandbox": "read-only"
  },
  "safety": {"require_approval": true, "allow_destructive_operations": false},
  "validation": [{
    "argv": ["python", "-m", "unittest", "discover", "-s", "outputs/budongi_mvp_temp/tests", "-p", "test_harness*.py"],
    "acs": ["기존 하네스 계약 테스트 통과"]
  }]
}
```

```powershell
python -m harness new-task --request .local_runtime/harness-managed/task.json
python -m harness run --task TASK-CLI-DEMO
python -m harness report --task TASK-CLI-DEMO
python -m harness approve --task TASK-CLI-DEMO --reviewer operator
python -m harness priority --task TASK-OTHER --value high
python -m harness provider --task TASK-OTHER --name codex
python -m harness pause --task TASK-OTHER
python -m harness resume --task TASK-OTHER
python -m harness retry --task TASK-OTHER
python -m harness cancel --task TASK-OTHER
```

`run`은 현재 HEAD에서 별도 detached Git worktree를 만든다. **현재 미커밋 변경은 포함되지 않는다.**
코드가 커밋된 기준인지 먼저 확인한다. 기존 사용자 변경을 자동 commit/복사하지 않는다.
성공은 검증 후 REVIEW_REQUIRED, 승인하면 COMPLETED다. 승인 시 결과 해시·현재 변경 파일과 HEAD를 재확인한다.
승인은 결과 수락 기록이며 원래 브랜치로 merge하지 않는다. 검토할 worktree 경로는 report에 있다.
작업자는 그 worktree의 실제 diff를 확인하고 별도 승인 범위에서 필요한 Git 작업을 수행한다.

worker는 App과 무관한 로컬 Python 프로세스다. 아래 명령은 단일 큐를 처리한다. 상시 실행은 일반
터미널이나 숨겨진 `Start-Process -WindowStyle Hidden`으로 시작할 수 있다. OS 서비스 자동 설치는 하지 않는다.

```powershell
python -m harness worker --once
python -m harness worker
```

우선순위 high/normal/low 및 의존성 COMPLETED 순서를 적용한다. 저장소 공통 OS 파일 잠금과 DB lease가
동일 저장소의 managed worker 중복 실행을 막는다. App은 관리 명령과 검토를 수행하고 worktree를 동시에 편집하지 않는다.
pause/cancel은 요청을 DB에 남기고 worker가 subprocess 트리를 종료한 뒤 상태를 기록한다.
worker가 죽었다면 PID 종료를 확인한 다음 아래 명령으로 lease를 교체한다. 살아 있는 PID는 복구를 거부한다.

```powershell
python -m harness resume --task TASK-OTHER --recover-running
```

재시도는 새 attempt이며 이미 발생한 외부 효과가 취소됐다는 의미가 아니다. Codex의 저장된 세션 ID는
동일 task/worktree/Codex 재시도에서 resume에 사용한다. task execution의 `resume_session:false`로 새 세션을 선택할 수 있다.
세션 ID/토큰은 CLI가 실제 제공한 경우에만 저장하고 나머지는 null이다. raw CLI stderr/명령 이벤트는 보관하지 않는다.

GMS는 기존 선택 정책·보관함·실잔액/만료·사전 count·최대 예약·공통 원장·현재1,000 보존을 재사용한다.
새 키 환경변수를 추가하지 않는다. 기존 `budongi.cli credentials --no-browser --port 8786` 서버가 준비돼야 한다.
`providers`는 로컬 정책만 조회하며 유료 count·잔액 원격 조회를 하지 않는다. 실행 시 서버가 준비 조건을 검사한다.
`--gms-port`와 `--codex-bin`은 전역 옵션이므로 관리 명령 앞에 둔다.

```powershell
python -m harness --gms-port 8786 providers
python -m harness --codex-bin "C:/Users/USER/AppData/Roaming/npm/codex.cmd" status
```

`execution.difficulty` simple/complex와 `max_output_tokens`는 기존 GMS 정책 이내다.
GMS는 코드 **초안**만 반환한다. WAITING_FOR_APPROVAL 결과를 담당자가 검토하고 허용 worktree에
수동 적용한 뒤 `python -m harness validate --task ID`로 결정적 검사를 다시 실행한다. 통과 후 approve한다.
GMS 초안을 자동 적용·tool calling 실행으로 표현하지 않는다. quota 전환은 allow_fallback=true,
명확한 quota 오류, 전환 직전 변경 없음 조건에서만 수행한다. 429 단독은 제한 재시도 대상이다.
GMS 중단/timeout 후 서버가 이미 수락한 호출은 완료될 수 있으므로 uncertain 대기 후 기존 원장을 대사한다.

상태 정본은 ignored `.local_runtime/harness-managed/state.sqlite3`다. events.jsonl과 reports/ID.json은
DB 파생 출력이며 앱 종료 후에도 남는다. 다른 worktree/App 모드에서 라이브 DB를 공유하지 않는다.
필요하면 report의 코드·검증 요약만 검토한 뒤 Git에 문서로 동기화한다. DB/로그/키는 Git에 넣지 않는다.
완료 worktree도 검토·복구를 위해 자동 삭제하지 않는다. 보존/정리는 사용자가 필요한 결과를 확보한 후 수행한다.

검증 명령은 shell=False와 제한된 unittest/pytest/compileall/Git diff 형식만 허용한다.
위험한 pytest basetemp/plugin/config 옵션을 거부하며 pytest 캐시/자동 plugin과 Python bytecode를 억제한다.
검증 코드는 신뢰된 로컬 프로젝트 코드여야 한다. 테스트 subprocess는 별도 OS sandbox가 아니고
worktree scope는 사후 변경 검사다. Codex sandbox와 동등한 파일 접근 격리로 해석하지 않는다.

설치/비대화형 JSONL의 기준은 [공식 Codex CLI 문서](https://learn.chatgpt.com/docs/codex/cli)와
[비대화형 실행 문서](https://learn.chatgpt.com/docs/non-interactive-mode)이며 실제 옵션은 로컬 help로 확인한다.
[상태별 복구 안내](CLI_RECOVERY.md)는 LUNA 초안을 로컬에서 검토한 별도 표다.
