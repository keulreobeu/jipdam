# Python-only WIP 백업과 복원

현재 `python -m harness handoff --help`에서 제공하는 명령이다. GMS/LLM 호출 없이
미완성 작업을 보존하며 제품 테스트·완료 선언·main 병합을 수행하지 않는다.
[계약](../specs/28_handoff_spec.md), [Task](../tasks/handoff.md).
의존성을 설치한 Python(이 PC는 저장소 루트 `.venv/Scripts/python.exe`)을 사용한다.

먼저 기존 `new-task --request`로 명시 scope/AC/validation을 가진 작업을 등록한다.
worker가 이미 실행한 task는 그 worktree를 사용하고, 실행 전 task는 현재 폴더를 사용한다.
작업파일은 해당 scope에 있어야 한다. 다른 작업의 dirty 파일은 인벤토리에서 제외 사유를 기록한다.

```powershell
python -m harness handoff backup --task TASK-ID
```

pause 요청 후 worker의 PAUSED/no-lease ACK와 잠금 확보까지 최대 10초 기다린다.
미확인 시 blocked이며 snapshot을 만들지 않는다. 멈춘 worker가 lease를 남긴 경우 기존
`resume --recover-running`의 종료 확인·복구 계약으로 먼저 해결한다. 필요한 ignored 파일은
`--include src/generated.txt --required-path src/generated.txt`로 명시한다. 필수 파일 누락은
portable 성공을 차단한다. 비밀/DB/raw/runtime·링크는 include로도 허용하지 않는다.

결과 `local_saved`와 checkpoint/ref/manifest SHA를 보관한다. staged와 작업폴더 바이트는
각각 저장되고 사용자 index는 쓰지 않는다. `.local_runtime/handoff/checkpoints/`는 로컬
저장소이며 DB/사용량/키는 포함하지 않는다. 자체 handoff runtime은 한 제외 디렉터리로
인벤토리에 기록해 동일 백업의 ID가 runtime 영수증 때문에 바뀌지 않게 한다.
파일당 2MB, 전체 20MB, 인벤토리 20,000개, manifest 4MB를 넘으면 blocked다.

Git 전담 agent가 승인된 기존 remote에 게시한다. **backup은 publish를 자동 호출하지 않는다.**

```powershell
python -m harness handoff publish --checkpoint CHECKPOINT --remote origin --base-ref refs/heads/main
```

source HEAD는 지정 원격 base ref의 SHA와 같아야 한다. orphan artifact branch에는
manifest와 검사한 blob만 포함한다. 기존 Git history·키·DB·다른 작업을 push하지 않는다.
표준 Git commit/hooks를 사용하며 실패 시 publisher를 보존한다. push/read-back 오류는
`local_saved`, `next_action=retry_delegated_publish`다. 같은 checkpoint로 재시도한다.
실제 원격 ref/SHA 확인 뒤만 `portable_verified`다. 이 상태는 타 PC의 실제 복원 성공과 다르다.
원격 main이 이동했으면 이전 base SHA를 보존한 승인 ref를 명시하거나 새 백업을 준비한다.

다른 PC의 같은 프로젝트 checkout에서 checkpoint와 게시한 **commit SHA**를 명시한다.

```powershell
python -m harness handoff restore --checkpoint CHECKPOINT --expected-sha COMMIT_SHA --remote origin --base-ref refs/heads/main
```

원격 SHA·manifest·blob·경로·기준 commit을 검사한 뒤 전용 새 폴더
`.local_runtime/harness-managed/worktrees/RESTORE-ID/`에 복원한다(custom state-dir도 지원).
기존 폴더와 index를 덮어쓰지 않는다. 원래 관리폴더에 새 task를 등록하며 원장을 복사하지 않는다.
`restore_verified`는 index/작업파일 read-back과 새 PAUSED task 생성 완료다. 기존 세션/Usage
원장이 복원됐다는 뜻은 아니다. `new_run_id`는 handoff 재개 식별자이고 모델 실행/관측 run이 아니다.
새 task는 `new_task_id`로 반환되며 실행 전에 복원 폴더에서 코드를 검토한다.

```powershell
python -m harness resume --task RESTORE-ID
python -m harness run --task RESTORE-ID
```

위 두 명령은 receipt의 **management_root**에서 같은 **state_dir**로 별도 명시 실행한다.
코드 검토는 destination에서 한다. 기본 provider는 Codex이며 GMS fallback과
기존 session resume는 비활성이다. 새 attempt는 기존 WIP에서 시작하고 기존 base HEAD를 유지한다.
원격 누락/위변조는 blocked, 적용 중 실패는 `restore_incomplete`다. 실패한 목적지와 아티팩트는
검토용으로 보존하며 자동 reset/delete하지 않는다. 재복원은 저장한 SHA/파일/index fingerprint가
같을 때만 멱등이며 수동 변경은 거부한다. ignored 필수 파일은 실제 사용 전에 다시 확인한다.

`portable_verified`나 `restore_verified`는 제품 AC/독립 품질/전체 테스트 통과를 의미하지 않는다.
소규모 180초 이내는 목표이며 물리 PC 간 시간은 실제 실행 뒤만 보고한다. Finish/Lean/GGUF는 후속이다.

## 조건부 독립 검토 — v5.4.1

2026-11-03 추가 제공한 `Jipdam_Harness_ChatGPT_조건부독립검토_운영추가_v5_4_1_20261103.md`와
`Jipdam_Harness_ChatGPT_최소전달_재사용템플릿_v5_4_1_20261103.md`의 delta를 적용한다.
기존 v5.4 문서·Spec을 복제하지 않고 이 운영 기준과 아래 단일 템플릿을 재사용한다.

Python/SDD/scope/secret/diff/테스트를 먼저 실행한다. 결정적 실패는 구현자에게 짧게 반환하며
Chat에 재설명하지 않는다. LIGHT는 기본 생략, STANDARD는 검토 이득이 있을 때만 선택,
STRICT(backup/restore·인증·권한·삭제·Git 정책·외부명령·검증 우회 등)는 독립 검토가 필수다.
Chat을 못 쓰면 다른 독립 채널 또는 `independent_review_pending`이며 완료/ready_for_main으로
승격하지 않는다. **실제 backup 명령은 독립 리뷰를 기다리지 않는다.** 구현 후보의 Finish 게이트와 분리한다.

`chat_manual`, `risk_based`는 운영상의 설계 이름이다. 현재 CLI 옵션/Chat API/provider가 아니다.
자동 메시지 전송·예약·새 Chat 생성·GMS·새 프레임워크는 추가하지 않는다. 가능한 PR/diff,
고정 base/head SHA, 기존 Task/AC, CI URL을 재사용하며 검토 전용 새 파일은 기본 0개다.
연결 부재 시 허용 파일의 최소 diff만 전달한다. 민감정보/DB/raw/runtime/전체 ZIP은 전달하지 않는다.

독립 검토는 고정 diff와 AC·반례를 기준으로 하며 구현자의 성공 설명을 증거로 삼지 않는다.
결과는 기존 Task/PR에 `review_channel, reviewed_sha, scope, status(findings/no_findings/incomplete/skipped),
findings, checks, limitations, requires_revalidation, human_approval=separate_required`만 기록한다.
수정 후 SHA가 바뀌면 이전 결과는 무효이며 새 diff·재현 케이스·Python/CI를 확인한다.
`no_findings`는 사람 승인·CI·AC·병합 허가를 대신하지 않는다. 부분 검토는 partial/incomplete다.
Chat의 실행 환경/접근은 실제 확인한 범위만 인정하며 불신 코드를 자동 실행하지 않는다.
Chat token/비용 미관측은 unknown이다. 절감률/무료 무제한을 추정하지 않는다.

단계별 review_requested/invoked/skipped_reason, 준비시간·신규 산출물 수·결함·재검증 시간은
현재 Task 근거를 재사용한다. 자동 계측/Lean 라우팅 및 Finish 구현(RV-01~12)은 후속 범위로
남기며 동작했다고 주장하지 않는다. 기존 4건 실패/공식 토큰 원장도 불변이다.

### 재사용 최소 요청 템플릿

```text
Jipdam 독립 코드 리뷰 요청
PR 또는 고정 ref: <PR URL 또는 base/head SHA>
작업/AC: <기존 TASK-ID/경로/AC>
검토 초점·위험도: <한 문장> / LIGHT|STANDARD|STRICT
CI: <해당 SHA workflow URL 또는 미확인>

연결된 GitHub diff·기존 Task/AC·CI를 우선 읽고 새 반례를 검토하세요.
결함은 severity·file:line·근거·최소 재현·권장 수정으로 보고하세요.
검토/실행하지 못한 범위는 incomplete/partial로 표시하세요.
문제 미발견을 승인/전체 테스트 성공으로 주장하지 마세요. 승인 없는 Git 쓰기/병합은 하지 마세요.
```
