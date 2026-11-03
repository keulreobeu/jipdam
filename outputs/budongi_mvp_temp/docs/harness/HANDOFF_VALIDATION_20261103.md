# KAN-41 검증 기록 — 2026-11-03

기준 main f29ad3d50215fdcd61f9bf034b1c049e06a0e2ac. 분리 development/publisher 사용.
원래 checkout은 이전 백업 branch로 wiki_contracts import가 누락돼 CLI 시작 실패.
최신 main의 CLI에는 해당 import가 없어 시작 가능하며 기존 checkout은 수정하지 않았다.
Git lifecycle도 main에 없으므로 현재 PC 기존 모듈을 게시 도구로만 재사용한다.
gstack investigate helper는 Git Bash NtCreateDirectoryObject 0xC0000022로 시작 실패;
degraded 조사로 재현→원인 확인→분리 main에서 검증했다. 도구 재설치는 하지 않았다.

## 실행 결과

`C:/Users/SSAFY/Desktop/jipdam/.venv/Scripts/python.exe -X utf8 scripts/verify_environment.py`
exit 0. 제품 376개(발견/실행 대상), 팀 35개와 합성 doctor/tool CLI를 통과했다.
제품에는 새 handoff 18개·GMS defer 3개·기존 provider 17개 회귀가 포함된다.
별도 `scripts/check_sdd.py --base origin/main`: features21/AC114/tasks43 passed.
`git diff --check` passed. `python -m harness providers`: GMS available=false,
reason=DEFERRED_GMS/external_calls=false; Codex 설치 available, 실제 인증/모델 실행은 미확인.

실제 KAN-41 exact scope로 만든 로컬 백업:
checkpoint `256cbc22e00bbd375a670a64e9a2b2afa071fb384360287340b952c427f5e1e3`,
4.625초, local_saved, missing_count0, 모델 호출0. 이 WIP snapshot은 이후 문서 수정 전 버전이다.
최초 원격 artifact publish는 자동 승인 검토가 payload·목적지의 명시 승인 부족으로 실행 전에
거부했다. 이후 사용자가 해당 고정 백업 게시·복원 검증을 명시 승인했다.
Git 전담 agent가 commit/push/read-back을 완료했다: `portable_verified`, 11.047초,
commit `6181fd283c77a73b29b74786aad97ad3b09337c0`, base_ref `refs/heads/main`.
원격 ref는 `refs/heads/codex/handoff/256cbc22e00bbd375a670a64e9a2b2afa071fb384360287340b952c427f5e1e3`.
같은 PC의 독립 clone에서 실제 원격 artifact·base·manifest/blob SHA를 검증하고 새 작업으로
복원했다: `restore_verified`, 14.593초, 새 PAUSED task `RESTORE-256cbc22e00bbd375a670a64`,
handoff 재개 ID `d5ef97cc26da4df6a727324423bd4371`, 모델0. 원래 root index 해시도 그대로다.
원래 session/Usage SQLite를 복원하지 않았다. 물리 PC A→B 성공으로 보고하지 않는다.
기능 전달 branch와 WIP artifact는 구분한다. 최종 코드 candidate는 아직 publisher에 게시 전이며
전담 Git agent가 한 차례 사용 한도 오류로 종료됐으나 다음 재개 턴에서 읽기 전용 동작을
확인했다. 직접 commit/push로 대체하지 않으며 정식 source snapshot은 전담 agent에게 전달한다.

후속 로컬 검토에서 POSIX의 unstaged chmod를 index mode로 덮는 경로를 발견해 수정했다.
Windows는 Git index mode를 유지하며 POSIX는 실제 worktree 실행 비트를 따로 저장한다.
이 수정과 이후 문서는 위의 고정 WIP artifact에 소급 포함되지 않는다.
수정 후 `python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_handoff.py -q`:
19개, 59.629초, OK. 이전 제품376/팀35 전체 통과와 구분한다.
실제 복원 새 작업 read-back: PAUSED/attempt0/lease null/pid null/worktree 일치,
provider codex/allow_fallback false/resume_session false. 복원 중 실제 모델 실행은 없었다.

임시 bare remote/독립 clone roundtrip, staged/unstaged/untracked/ignored 명시 include,
새 PAUSED task와 실제 WIP 기반 새 attempt(mock), stop ACK/실제 자식 종료,
중복 lock/HEAD 변경/충돌 index, 악성 경로/키/raw/DB/크기·수량,
잘못된 SHA/manifest/blob, remote reject/read-back 실패와 동일 commit 재시도,
복원 이후 수동 수정 보호를 테스트했다. 전부 합성 fixture이며 유료/외부 모델 호출은 없다.

기본 sandbox에서는 임시폴더 생성 WinError 5가 있어 같은 검증을 승인된 비격리 실행으로 수행한다.
GMS/LLM 실호출은 0회. 과거 4건 실패/1,085,783토큰 원장은 변경하지 않는다.

## 상태 한계

임시 bare remote+독립 clone은 물리 PC A→B 시험이 아니다. 성능·복원 성공을 물리 PC 간 결과로
보고하지 않는다. 실제 원격 branch read-back과 fixture 원격을 구분한다.
필수 문서는 로컬 Spec/ADR/Task/운영 안내로 제공한다. 위키 판단: SKIP(사용자 v5.4는 추가
장문 Confluence 자동 생성을 금지하며 이번 단계는 코드와 필수 로컬 계약 갱신이다).
현재 main CLI에는 wiki 명령이 없고 이전 checkout의 wiki는 누락 모듈로 실행되지 않는다.
원격 위키 게시/동기화가 성공했다고 주장하지 않는다. KAN-6은 변경하지 않는다.
v5.4.1: review 목적 신규 산출물 0개; 본 기록은 기존 필수 AC 검증 증거로 재사용한다.
고정 코드 SHA의 독립 검토 결과는 KAN-41에 귀속한다. no_findings와 사람 승인·main 병합은 별개다.
