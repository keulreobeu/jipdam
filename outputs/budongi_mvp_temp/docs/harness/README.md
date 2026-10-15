# 집담 개발 하네스

2026-10-15 자동 CLI 실행·App 관리 하네스는 [CLI 운영](CLI_OPERATIONS.md),
[구조](CLI_ARCHITECTURE.md), [구현·검증](CLI_IMPLEMENTATION_REPORT.md)을 따른다.
이 페이지 아래 내용은 보존된 HARNESS-001 수동/native 역할 인계와 Mock Gateway 계약이다.

Codex Master가 필요한 native 역할만 실행하고 공통 Python CLI가 상태·증거를 관리한다.
제품의 추천/LLM/키 보관함과 독립적이며 새 gateway는 Mock만 사용한다.
[계약](../specs/19_harness_spec.md), [Task](../tasks/harness-integration.md),
[Phase 0](origins.md), [검증 기록](validation.md), [Master 절차](master-workflow.md).

저장소 루트에서 Python 3.11+로 실행한다. 추가 의존성은 없다.

```powershell
python -X utf8 scripts/agent_harness.py doctor
python -X utf8 scripts/agent_harness.py status
python -X utf8 scripts/agent_harness.py budget
python -X utf8 scripts/agent_harness.py budget --provider gms
```

정본은 `.local_runtime/harness/runs.db`다. task/run/event/checkpoint/artifact/provider_usage,
gateway_requests/gateway_policy를 저장한다. SQLite 트랜잭션이 상태와 이벤트를 함께 기록한다.
이벤트는 append-only이고 cursor는 event id다. 프롬프트/응답/키는 provider 원장에 저장하지 않는다.
하네스 작업 목표·코드 경로·담당자의 증거 요약은 로컬 DB에 남으므로 민감정보를 입력하지 않는다.
이벤트/체크포인트는 CLI JSON으로 내보낼 수 있으며 DB 백업은 모든 worker 중단 후 수행한다.
현재는 단일 PC의 로컬 SQLite다. 활성 DB를 여러 PC에서 Drive 동기화하는 분산 잠금은 지원하지 않는다.

Task JSON 예시를 `.local_runtime/harness/task.json`에 저장한다.

```json
{
  "task_id": "TASK-HARNESS-DEMO",
  "kind": "feature",
  "objective": "영구 SDD Task의 명시된 기능 구현",
  "scope_paths": ["outputs/budongi_mvp_temp/src/example.py", "outputs/budongi_mvp_temp/tests/test_example.py"],
  "acceptance_criteria": ["EXAMPLE-001-AC-01"]
}
```

kind는 Master가 선택한다: direct(Master→Evaluator), bug(Engineer→Evaluator),
feature(Planner→Engineer→Reviewer→Evaluator), audit(Reviewer→Evaluator).
짧은 설명은 하네스/하위 에이전트가 필요 없다. 큐는 한 단계씩 배정한다. 동시에 최대 2개 claim,
한쪽이 writer인 겹치는 범위는 직렬화하고 독립 read-only 범위는 함께 진행할 수 있다.

```powershell
python -X utf8 scripts/agent_harness.py new-task --request .local_runtime/harness/task.json
python -X utf8 scripts/agent_harness.py run --task TASK-HARNESS-DEMO --host codex
python -X utf8 scripts/agent_harness.py checkpoint --task TASK-HARNESS-DEMO
python -X utf8 scripts/agent_harness.py context --task TASK-HARNESS-DEMO
python -X utf8 scripts/agent_harness.py events --after 0
```

run은 **작업 JSON을 배정**한다. 자동으로 모델·셸을 실행하지 않는다. 반환 JSON을 job.json에 저장하고
Master가 현재 호스트의 native delegation으로 해당 역할을 호출한다. `.codex/agents/jipdam_*.toml`의
등록 형식은 [공식 Codex 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)를 확인했다.
현재 세션이 custom role을 발견하지 못하면 일반 native agent에 같은 역할 지침을 주고 fallback을 기록한다.
config의 동시 제한은 새 세션에서 적용되며 이미 실행 중인 세션의 제한을 바꿨다고 가정하지 않는다.

result.json의 정확한 v1 필드는 다음과 같다. artifacts는 실제 변경·산출물 경로이며 scope 안에 있어야 한다.
verification은 command/실제 exit_code/증거 파일의 SHA256을 기록한다. 없는 체크를 passed로 만들지 않는다.

```json
{
  "run_id": "job의 run_id", "task_id": "TASK-HARNESS-DEMO",
  "role": "evaluator", "host": "codex", "status": "passed",
  "artifacts": [{"path": "outputs/budongi_mvp_temp/tests/test_example.py", "sha256": "실제 SHA256"}],
  "verification": [{"ac": "EXAMPLE-001-AC-01", "command": "실제 실행 명령", "exit_code": 0,
                    "evidence": ".local_runtime/harness/test-result.txt", "sha256": "실제 SHA256"}],
  "errors": [], "token_usage": null, "provenance": "실제 host/agent ID와 실행 근거"
}
```

status는 passed/failed/blocked다. token_usage는 측정됐을 때만 input_tokens/output_tokens 비음수 정수이며
미제공은 null이다. 로컬 담당자가 결과와 실제 출력 파일을 확인한 뒤 제출한다. 하네스는 해시/범위/AC를
검증하지만 명령 문자열을 실행하지 않으며, 거짓 수동 증명까지 자동 판별하는 sandbox는 아니다.

```powershell
python -X utf8 scripts/agent_harness.py submit --job .local_runtime/harness/job.json --result .local_runtime/harness/result.json
python -X utf8 scripts/agent_harness.py run --task TASK-HARNESS-DEMO --host codex
python -X utf8 scripts/agent_harness.py stop --task TASK-HARNESS-DEMO
python -X utf8 scripts/agent_harness.py resume --task TASK-HARNESS-DEMO
```

각 단계는 고유 run_id, 같은 단계의 재시도는 같은 run_id와 증가한 attempt/새 lease를 사용한다(최대3회).
stop은 DB claim과 늦은 결과를 차단한다. Master는 **실제 native worker도 interrupt**해야 한다.
죽은 프로세스가 running을 남기면, 이전 worker의 종료를 확인한 뒤
`resume --task ID --recover-running`을 실행한다. 이후 다른 host로 claim할 수 있다.
DB의 완료 단계는 보존하고 checkpoint의 과거 상태로 롤백하지 않는다. 이미 실행된 외부 효과를 자동 재시도하지 않는다.

CLI/Claude/Antigravity는 `context`, `resume`, `run --host cli|claude|antigravity`, `submit`으로 동일 작업을
수동 인계한다. 이 명령의 성공은 각 도구의 native subagent/hook 등록 성공을 의미하지 않는다.
검증하지 않은 hook/CLI 옵션은 설치하지 않았다. scope 선언은 host sandbox를 대신하지 않는다.

Mock 요청 JSON은 request_id/text와 선택 model(mock-v1), operation(responses), prompt_version,
snapshot, permissions, category(development|quality|demo), max_output_tokens를 받는다.

```powershell
python -X utf8 scripts/agent_harness.py mock-call --request .local_runtime/harness/mock-request.json
```

기본 30,000/예비3,000은 합성 시나리오다. 입력 bytes/4 계산도 Mock 전용이며 실제 tokenizer라고 주장하지 않는다.
영속 예약/정산/호출 한도·카테고리 한도/불명확 소비/회로 차단기를 공유한다. 성공 응답 캐시는 프로세스 메모리 TTL
60초/128건이다. 요청 ID는 재시작해도 재사용 호출을 막고, 원문 없는 영속 원장에서 이미 완료됐으면
already_completed로 반환한다. 다른 payload에 같은 ID는 오류다. policy를 변경해도 원장은 초기화하지 않으며
현재 버전은 정책 변경 자체를 거부한다. retry는 provider가 무소비를 명시한 Mock 429에만 1회 허용한다.
timeout/500/usage 누락은 최대 예약을 보류하고 로컬 결정적 점검 fallback으로 이어진다.
향후 실제 GMS는 기존 보관함·GMSBudgetManager의 실잔액/크레딧/유료 count 정책을 통합해야 하며
이 DB나 env key로 우회할 수 없다. 새 하네스에 live 활성화 옵션은 없다.

검사:

```powershell
$env:PYTHONPATH = (Resolve-Path outputs/budongi_mvp_temp/src).Path
python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p 'test_harness*.py' -v
python -X utf8 scripts/verify_environment.py
python -X utf8 scripts/check_sdd.py --base origin/main
```
