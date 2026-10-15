# Harness validation — 2026-10-14

브랜치: `codex/data-portability-20261013`. 기존 사용자/동시 작업의 미커밋 변경을 보존했다.
현재 범위는 HARNESS-001 최소 오프라인 코어다. 실제 데이터 추천·GMS/타 호스트 완전 통합 완료를 뜻하지 않는다.
[Task](../tasks/harness-integration.md) · [Spec](../specs/19_harness_spec.md) · [운영](README.md) · [Phase 0](origins.md).

## 단계와 실제 에이전트

| 단계 | 실제 담당 | 산출물·판정 | 토큰·미검증 |
| --- | --- | --- | --- |
| Phase 0 | Master + `/root/source_assessment` | ZIP827개 정적조사·해시·라이선스 미확인·독립 구현 결정 | native tokens unknown; source 실행0 |
| 구조/코어 | Master(Planner/Engineer 역할) | contracts/state/CLI·Spec/Plan/ADR/Task·선택적 역할 | 별도 Planner/Engineer subagent 실행0; Master tokens unknown |
| Mock Gateway | Master | reservation/settlement/unknown/circuit/cache/limits | Mock tokenizer만, 실제30,000할당 unverified |
| 독립 리뷰 | `/root/harness_review` | Windows case/후행점·공백 aliases 및 JSON 비밀검사 P1 재현→수정→재확인 | 미해결P1 없음; native tokens unknown |
| 독립 평가 | `/root/harness_evaluator` | 실제Task ID 오탐 발견→수정→16개/CLI6 재검증·팀27 | generic native fallback; custom TOML discovery not_run |
| 통합 재검증 | Master | 권한 오류 분리 후 제품225개 통과·SDD기본/브랜치 통과 | synthetic fixtures, 실제 제품 품질 평가는 아님 |

Source/Reviewer/Evaluator 세 native subagent만 실행했다. 이 세션의 generic native API를 사용했으며
새 custom TOML 역할을 실제로 발견·호출했다고 표시하지 않는다. Master가 같은 파일의 쓰기를 담당했다.
Reviewer 결과를 실제 보고서로 수신 후 로컬 원장에 import했으며 claim 시각을 과거 native 시작시각으로 위장하지 않았다.
실제 검토 결과·Evaluator JSON의 증거파일/해시를 확인하고 audit run을 제출했다.

## 검증

환경: Windows, 기존 `.venv` Python3.12.10, PYTHONPATH 제품src. TEMP/TMP는 `.local_runtime/harness_reference/tmp`.

| 명령/검사 | 실제 결과 | 증거 |
| --- | --- | --- |
| `python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p 'test_harness*.py' -v` | 16/16 PASS, 독립 재실행3.711초 | `.local_runtime/harness/evaluation/native-final.log` |
| `.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -v` (루트) | 27/27 PASS | `root-configured.log` 및 `independent-evaluation-summary.json` |
| 같은 venv unittest (cwd=제품) | 225/225 PASS,90.304초, 권한 제약 밖 실행 | `.local_runtime/harness/evaluation/product-unsandboxed.log` |
| CLI doctor/budget gms/budget mock/new-task/checkpoint/context | 6/6 PASS; realistic TASK-HARNESS ID 포함 | evaluator의 CLI logs |
| `scripts/register_gstack.py --check` | 58 unique/non-nested PASS | `registration.log` |
| `scripts/check_sdd.py` | PASS:13features/77AC/31tasks/100changed paths (당시 snapshot) | 실제 command output |
| `scripts/check_sdd.py --base origin/main` | PASS:13features/77AC/31tasks/151changed paths (당시 snapshot) | 실제 command output |
| HARNESS만 필터한 registry 사본 + `check_sdd.validate` | 1feature/5AC/1Task/24paths PASS; 전체CI와 구분 | `sdd-harness-only.txt` |
| `.venv/Scripts/python.exe -X utf8 scripts/verify_environment.py --gstack` | PASS: 제품225/팀27/SDD/합성CLI/pinned gstack58 | `verify-final.log` |
| `git diff --check` (이번 shared paths) | PASS, CRLF 안내만 | 실제 command output |
| gstack plan-eng-review helper | NOT_RUN/실패: Git Bash NtCreateDirectoryObject 0xC0000022 | Plan의 PARTIAL/NOT CLEARED 보존 |
| bootstrap/reinstall, Claude/Antigravity native, 실제 GMS Gateway | NOT_RUN | 기존 설치 유지·실제 호환성 게이트 |

첫 시스템 Python 시도는 의존성(openpyxl/cryptography) 누락과 cwd에 따른 scripts package 해석으로 실패했다.
기존 venv/제품cwd로 수정 후, sandbox 실행의40건 오류는 loopback10013(26), review-path resolve5(13),
합성 WinCred5(1)로 분류됐다. 같은 테스트를 승인된 권한 밖 실행에서225개 모두 통과했다.
초기 SDD 실패는 다른 진행 중 작업의 GMS-BUDGET-001 REQ04/AC04 원장 누락이었고 해당 등록 후 정상 통과했다.
이 실패들을 지우거나 하네스 성공으로 바꾸지 않고 원시 로그를 ignored runtime에 보존했다.

주요 AC: stage/완료AC/증거해시 검증, stop fencing, 실제 child process kill 후 동일 run_id/attempt 재개,
실패 attempt 이벤트 보존, 대소문자/후행점·공백 경로, nested/quoted secret fixture, cursor, unsupported provider,
동시10threads 및10별도process가 같은27000 예산에서9개×3000만 예약, usage누락/timeout/500 최대보류,
429 무소비1회 retry, cache/request id 재시작, category/call limits/circuit persistence를 실제 검사했다.

## 호스트와 GMS 상태

| 경로 | 상태 | 근거·제한 |
| --- | --- | --- |
| Python 공통 코어/CLI | verified (오프라인 범위) | 실제 CLI/kill/restart/JSON evidence |
| Codex native generic delegation | verified | 실제 source/reviewer/evaluator 실행과 결과 |
| Codex custom TOML | partial | 공식 schema/로컬 TOML 정적검사, 자동발견/새세션 실행 미확인 |
| Claude/Antigravity | partial manual / native not_run | 공통 JSON·context·resume 호스트라벨 테스트; 실제 앱 세션 아님 |
| Mock provider | verified synthetic | responses/mock-v1/합성 usage만 |
| 새 GMS Gateway live | disabled/unverified | 라이브 구현·스위치 없음,30,000단위/operation별 호환 미확인 |
| 기존 GMS budgeted runner | 생성 blocked | 최신 사용자 추가허용 뒤 제한된 문서초안 시도, 전체500크레딧 한도 차단 |

Codex custom agent 형식은 [공식 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)를 확인했다.
`codex-cli0.155.1` help/version은 확인했고 `--strict-config features`는 해당 조합 미지원으로 실패했으므로
custom TOML 발견의 증거로 사용하지 않는다. 글로벌 provider/인증/모델 설정은 바꾸지 않았다.

## 비용과 원장

초기 요청에서는 유료 통신을 실행하지 않았다. 이후 사용자가 현재 작업 GMS 사용을 추가 허용했다.
기존 gms-work를 사용한 문서 초안 요청은 sandbox loopback에서 먼저 실패했고, 권한 밖 재시도에서는
입력 count1회가20크레딧으로 정산된 뒤 전체 한도에서 생성 예약이 차단됐다. 생성은0회이며
초안이 없으므로 모델 출력을 적용하지 않았다. count의 청구 토큰은 제공되지 않아0이라고 추정하지 않는다.
key-info 메타데이터 통신도 포함되므로 전체 외부 API0회라고 보고하지 않는다. 직접 키 조회/환경변수 우회/
새 provider 활성화/정책 한도 증액/재시도는 하지 않았다.

당시 공유 원장의 누적466.32크레딧/6075토큰·held0, 전체500크레딧/10000토큰/5000크레딧 보존이었다.
이 누적 수치는 다른 Task 사용을 포함한다. 이번 Task의 확인된 차감은 count20크레딧, 생성토큰0이다.
새 하네스 원장의 별도 Mock 예제는 입력15+출력8=합성23토큰/1call,held0,available26977이다.
실제 quota/과금으로 혼동하지 않는다. Codex Master/subagent 실제 토큰은 미노출로 unknown/null이다.

- 공통 SQLite: `.local_runtime/harness/runs.db` (Git 제외).
- Self audit Task: `TASK-HARNESS-SELF-AUDIT`, bounded offline audit verified.
- Reviewer run: `b80c322ecec74f89ac65b1a87b05471f`; Evaluator run: `42bec3a95d614a3fb4ce4f5c9b3c9fdd`.
- Job/result/log: `.local_runtime/harness/{reviewer-job.json,evaluator-job.json,evaluation/}`.
- `checkpoint --task TASK-HARNESS-SELF-AUDIT`와 `context`/`events`로 인계할 수 있다.
- 기존 실제 GMS 원장/보관함은 제자리에 유지하며 key/ciphertext/credential ID를 문서에 넣지 않는다.

## 이번 변경 파일

기존 작업 전체 git diff와 구분한 이번 소유 범위다. shared README/current/traceability는 항목 추가만 했다.

- `outputs/budongi_mvp_temp/src/jipdam_harness/__init__.py`
- `outputs/budongi_mvp_temp/src/jipdam_harness/contracts.py`
- `outputs/budongi_mvp_temp/src/jipdam_harness/state.py`
- `outputs/budongi_mvp_temp/src/jipdam_harness/gateway.py`
- `outputs/budongi_mvp_temp/src/jipdam_harness/cli.py`
- `scripts/agent_harness.py`
- `scripts/register_gstack.py`
- `outputs/budongi_mvp_temp/tests/test_harness.py`
- `outputs/budongi_mvp_temp/tests/test_harness_gateway.py`
- `tests/test_harness_discovery.py`
- `.codex/config.toml`
- `.codex/agents/jipdam_engineer.toml`
- `.codex/agents/jipdam_evaluator.toml`
- `.codex/agents/jipdam_planner.toml`
- `.codex/agents/jipdam_reviewer.toml`
- `.agents/skills/jipdam-harness/SKILL.md`
- `outputs/budongi_mvp_temp/docs/specs/19_harness_spec.md`
- `outputs/budongi_mvp_temp/docs/adr/ADR-020-portable-harness.md`
- `outputs/budongi_mvp_temp/docs/plans/harness-integration.md`
- `outputs/budongi_mvp_temp/docs/tasks/harness-integration.md`
- `outputs/budongi_mvp_temp/docs/harness/README.md`
- `outputs/budongi_mvp_temp/docs/harness/master-workflow.md`
- `outputs/budongi_mvp_temp/docs/harness/origins.md`
- `outputs/budongi_mvp_temp/docs/harness/validation.md`
- `outputs/budongi_mvp_temp/README.md`
- `outputs/budongi_mvp_temp/docs/tasks/current.md`
- `docs/sdd/traceability.json`

## 남은 확인

새세션의 Codex custom role 자동발견·실제 Claude/Antigravity native API/hook, 실제30,000할당 의미,
GMS operation/model별 live compatibility·usage/count요금 상한, 기존 크레딧 원장과의 실제 gateway 통합은 후속 Task다.
제품 설명/실데이터/매칭/추천 연구는 이번 하네스가 완료하지 않는다. 외부 push/PR/merge/수집은0회다.
stop은 DB fencing이며 Master가 native worker를 별도 interrupt해야 한다. Scope는 OS sandbox가 아니며
수동 result는 신뢰된 담당자가 실제 증거를 확인해야 한다. 다른PC active SQLite 동기화와 외부효과 exactly-once는 미지원이다.

## Final verification

`.venv/Scripts/python.exe -X utf8 scripts/verify_environment.py --gstack` 최종 exit0. 제품225개·팀27개 통과, 합성 CLI smoke 및 pinned gstack58개 검증 통과. 권한 제약으로 실패했던 동일 테스트를 안전한 합성 입력으로 실행했고, 외부 데이터 수집이나 모델 생성을 하지 않았다.

최종 통합 로그 SHA256: `98d7b578d59b3d677b69850b537aff7a594418aaf2c84bc10f3f12be74fe7bcc`. 원시 로그는 ignored runtime에 보관한다.
