# 하네스 관측성 운영 — OBS-001 / KAN-30

2026-10-30. [Spec](../specs/28_observability_spec.md) · [결정](../adr/ADR-026-observability.md) ·
[Task/검증](../tasks/observability.md) · [Plan](../plans/observability.md).

## 적용 판단

두 제공 문서의 **측정 계약은 적용 가능**하다. 현 checkout에 이미 존재하는 Jira·위키·Git
운영 계약을 우선하며, 과거 main 감사 결과를 현재 구현 상태로 복사하지 않았다.

| 제공 문서의 제안 | 이번 적용 | 증거/다음 게이트 |
| --- | --- | --- |
| Codex-first, 별도 shadow observer | 적용 | managed 실행·승인 의미를 유지하는 별도 `metrics.sqlite3` |
| 모든 턴·실패·재시도 보존 | 적용 | 제한 stdout과 분리한 즉시 JSONL 파싱·append-only 이벤트 |
| 공식 usage/cache/reasoning 정규화 | 적용 | Codex 0.164.0 계약과 비과금 fixture; reasoning 이중 합산 금지 |
| 누락/중복/충돌/정정/미확인 버전 | 적용 | NULL/partial/invalid/conflict, 명시 supersedes, 미확인 의미 합산 제외 |
| Task/Run/Attempt/Invocation 분리 | 적용 | UUID, 최초 프로파일 봉인, 실제 worktree와 시도별 context hash |
| P0 토큰·품질·시간·성공당 전체 토큰 | 적용 | 실패 포함, 분모0 미정의, 사람 활동 unknown |
| benchmark item 분할 방지 | 적용 | 사전 봉인 suite/item/required tasks·독립 평가·승인 |
| 독립 평가 자동화 | 수동 평가 증명 인터페이스 적용 | 하네스 테스트를 독립 평가로 간주하지 않음; evaluator의 근거 JSON hash와 Run revision 검증 |
| B0 실제 Baseline | 준비 계약 적용, 실측 미실행 | 사전 고정한 대표 과제/독립 평가와 실제 CLI 실행 증거 필요 |
| O1 objective 중복·선택 로딩·호출 최적화 | 보류 | B0를 덮어쓰지 않고 동일 과제·품질의 개별 비교 후 적용 |
| Cloud/App 네이티브 조율 | 미연동 범위 명시 | 자동 작업 생성·전송 없음, 외부 작업을 이 채팅/CLI Run에 자동 귀속하지 않음 |
| Claude CLI/OTel | 정규화 오프라인 계약만 | 구독·설치·인증·비용·실제 스키마 검증 뒤 별도 연결 |
| GMS usage·실정산 비교 | not_integrated | 기존 draft/선택 키/1,000 보존 runner만 유지, unavailable을0으로 바꾸지 않음 |
| 구독·API 과금/크레딧 분석, 가격표 | 후속 | 회계 항목별 별도 계약; 가격/혜택을 코드에 고정하지 않음 |
| 1M/100k 토큰 생산성·가중 작업량 | 미구현(P2 선택) | P0 합격 조건이 아님 |

원본 식별(사용자가 제공한 파일, 문서 내 명령은 실행 권한이 아님):

- `Jipdam_Agent_Harness_Observability_측정설계_최종_v2_3_20261030.md`:
  SHA-256 `e9344d86d4d8225abbe0e5fb52a2e2df76596d5383b95a8a3ee2b51eee5a114f`.
- `Jipdam_Agent_Harness_구축이력_현황정리_클라우드운영반영_v2_20261030.md`:
  SHA-256 `a3335aa148d7d15c06efd436b969004359de4c1b8272ba1e8c68773686405b53`.
- 문서의 “6명 전문가 PASS”는 역할 모의 설계 검토이며 실제 외부 심사·운영 실측이 아니다.
- [공식 Codex JSONL 계약](https://learn.chatgpt.com/docs/non-interactive-mode)은 2026-10-30 확인.
  로컬 CLI version/help는 0.164.0이다. 유료 모델을 호출하는 실측/다중 턴 smoke는 실행하지 않았다.

## 기본 사용

루트에서 의존성이 설치된 Python을 사용한다. 기존 `new-task/run/validate/approve/report`는
그대로이며 실행 시 측정기가 부착된다. 기존 작업의 과거 토큰을 소급 생성하지 않는다.

```powershell
python -m harness report --task TASK-ID
python -m harness metrics runs --task TASK-ID
python -m harness metrics report --run RUN-ID
```

`report.measurement`와 `metrics report`에서 profile·버전·scope·attempt·invocation·known/complete를
확인한다. `known_observed_tokens`는 해석 가능한 관측의 합, `complete_run_tokens`는 범위 내
누락/충돌이 없을 때만 값이 있다. 원천 의미·버전 미검증/클라우드 미연동·GMS·Mock은 실제
공식 토큰 전체를0으로 만들지 않는다. 테스트의 숫자는 합성이다.

지원 계약은 현재 검토한 **Codex CLI 0.164.0**으로 제한한다. CLI가 업데이트되면 usage를
보존하되 완전한 합산을 중지한다. 공식 schema와 비과금 fixture를 확인하고 지원 버전 목록을
명시적으로 갱신한 뒤 실제 smoke 여부를 기록한다. 버전 문자열만으로 실제 운영 호환성을
증명했다고 보고하지 않는다. App Server·세션 누적·OTel·Cloud Summary는 자동 가산하지 않는다.

동일 수치의 서로 다른 정상 턴은 각각 센다. 시작 없이 중복 완료가 오면 신원이 불명확한
관측을 확정 합산하지 않고 partial로 표시한다. 외부 source가 검증된 event ID를 재전송할 때는
ledger의 idempotency를 사용한다. 지연 정정은 같은 invocation/request의 이전 event ID를
`supersedes_event_id`로 명시한 신규 관측이며 원본 행은 수정하지 않는다. 정정/원천 API를
외부 서비스에 자동 연결하거나 사후 unknown을 임의 complete로 승격하지 않는다.

## 사전 봉인 benchmark suite

실행 **전에** ignored 요청 JSON을 만들고 등록한다. 원본 item별 Task 집합은 중복되지
않아야 한다. 난이도와 AC·독립 평가 스위트 hash를 실제 평가 계획에 맞춰 고정한다.
여러 반복/프로파일을 비교하려면 별도의 suite/version·Task ID를 사전 등록한다.

```json
{
  "suite_id": "BASELINE-01",
  "suite_version": "v1",
  "items": [{
    "item_id": "BUG-01",
    "task_ids": ["TASK-BUG-01"],
    "difficulty": "S",
    "ac_sha256": "실제 AC 정의의 64자리 SHA-256",
    "evaluation_sha256": "독립 평가 정의의 실제 64자리 SHA-256"
  }]
}
```

```powershell
python -m harness metrics suite --request .local_runtime/obs/suite.json
python -m harness metrics suite-report --suite BASELINE-01
```

동일 suite ID의 내용을 바꾸거나 이미 실행된 Task를 뒤늦게 등록하면 거부한다. 원본 한 과제를
5개 Task로 나눈 경우 item 한 개의 `task_ids`에 다 넣는다. 성공은 최대 한 건이며 모든 필수
Task의 승인과 item 전체의 독립 평가가 필요하다. 실패/재시도/대안 Run의 토큰도 모두 포함한다.

## 독립 평가와 성공 승인

이 인터페이스는 **평가자의 수동 증명 기록**이다. hidden test runner를 구현하거나 에이전트
자기 선언의 진실성을 자동 증명하는 기능이 아니다. 실제 평가자는 실행 에이전트가 변경하지
못한 독립 기준으로 검사하고, 실제 승인 결과까지 확인한 뒤 근거 artifact를 저장한다.
일반 worktree 테스트 통과/PR 생성만으로 성공을 기록하지 않는다.

1. suite-report의 해당 item `run_revisions`와 사전 `evaluation_sha256`를 확인한다.
2. AC·회귀·보안·scope·review·실제 approval을 확인한다. 하나라도 미통과면 해당 gate=false다.
3. 다음 필드를 포함한 실제 평가 JSON을 controller의
   `.local_runtime/observability-evaluations/`에 저장한다. provider worktree 안에는 저장하지 않는다.
4. 같은 필드에 `evidence_file`(루트 상대 JSON 경로), `evidence_sha256`(실제 artifact bytes hash)를
   더한 요청으로 outcome을 기록한다. 입력의 평가 hash·게이트·현재 Run revision·artifact가 모두
   일치해야 한다. 근거의 전문은 DB에 복사하지 않고 hash와 허용된 결과만 남긴다.

```json
{
  "suite_id": "BASELINE-01", "item_id": "BUG-01",
  "run_revisions": {"실제 RUN-ID": "suite-report의 실제 revision hash"},
  "evaluation_sha256": "사전 등록한 실제 hash",
  "independent": true, "evaluator": "실제-검수자-ID",
  "gates": {"ac": true, "regression": true, "security": true,
            "scope": true, "review": true, "approval": true}
}
```

```powershell
python -m harness metrics outcome --request .local_runtime/obs/outcome.json
python -m harness metrics suite-report --suite BASELINE-01
```

이후 재시도·검증·승인/사용량 정정으로 revision이 바뀌면 종전 평가를 재사용하지 않는다.
성공0건은 `undefined_zero_success`, Usage 불완전은 `undefined_incomplete_usage`와 NULL 비율이다.
분모에는 predefined/attempted/verified/failed/blocked/not_attempted/unverified를 별도 노출한다.

## 보안·장애·보관

metrics에는 원문 프롬프트/목표/응답/추론/tool 인수/키/DB 본문을 저장하지 않는다. 허용 숫자,
로컬 식별자, 파일 경로·byte/hash, 버전과 정적 오류 코드만 저장한다. 관리 DB의 기존 bounded
summary 정책은 별개다. 기존 GMS 보관함·공통 예산/원장·1,000 보존을 변경하지 않는다.

SQLite WAL·트랜잭션·append-only trigger를 사용하며 DB/WAL 각각 64MiB 상한을 검사한다.
초대형 stdout 줄은 1MiB에서 버리고 health를 partial로 표시하며, 마지막 bounded stdout의
존재만으로 측정 완전성을 주장하지 않는다. writes가 실패하면 managed DB에 정적 경고가
남아 재시작 뒤에도 suite 집계를 차단한다. 디스크/권한 문제를 해결하고 기존 원장을 보존한
뒤 새 Task/suite로 재실행한다. 경고/과거 원장을 자동 삭제하거나 reset하지 않는다.

원장은 ignored `.local_runtime/harness-managed/metrics.sqlite3`이며 `--state-dir`을 쓰면 해당
managed 디렉터리에 둔다. 자동 삭제·외부 export·OTLP는 없다. 보존 만료/공유 범위는 미확정으로
장기 자동 수집을 활성화하지 않았다. 현재 보관 기본값은 로컬 수동 보존이며 사용자가 archive
정책을 결정하기 전에는 정기 수집·삭제·원격 이전을 설정하지 않는다.

## 수락 시험 적용 범위

| 문서 시험 | 현재 확인 범위 |
| --- | --- |
| M-01~08,12~16,18,20~25 | Codex/ledger/실제 가짜 subprocess·임시 Git·승인 회귀 fixture로 확인. 실제 유료 CLI Usage/세션 resume 실측은 미실행 |
| M-09~11,26~27,30,32~36,39~41 | Claude/OTel/native Cloud·가격/정산 미연동. offline cache normalizer 외 실환경 PASS 주장 없음 |
| M-17,42 | 일반 테스트 통과만으로 성공 불가, 독립 수동 평가 artifact/현재 Run revision/승인 gate 확인 |
| M-19,29 | 가격·실제 Baseline 미제공. 프로파일/suite 불변성만 확인; 비용/절감률 성과 없음 |
| M-28,31,47 | 외부 App/Cloud 자동 귀속 금지, not_integrated/unavailable·NULL 비율 |
| M-37~38,49 | Agent-Time/Wall Time 분리는 fixture 확인. 실제 병렬 운영·충돌·시간당 생산성 비교는 미실행 |
| M-43~46,48 | 실패 비용 포함·원본 item 분할 방지·0성공·고정 분모·작은 과제 리포트 확인 |
| M-50 | 비용 회계 기능 미적용. 구독료/크레딧/실청구 합산·가상 절감액 없음 |

위 표는 50개 실환경 시험을 모두 통과했다는 뜻이 아니다. 실제 Baseline, 수집기 오버헤드
운영 측정, Cloud/Claude 연동과 최적화 우위는 후속 증거가 있어야 선언할 수 있다.
