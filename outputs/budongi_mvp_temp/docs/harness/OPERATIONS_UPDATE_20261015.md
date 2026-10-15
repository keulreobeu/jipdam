# GMS 1,000 보존·자동 커밋 후속

사용자 승인: 현재 대화의 GMS 최대 사용·최소1,000 보존·새 브랜치·오토커밋 요청.
[Spec](../specs/21_harness_operations_spec.md), [Task](../tasks/harness-operations.md).

## 현재 설정

- 작업 브랜치: `codex/cli-gms-autocommit-20261015`.
- GMS 저장 정책: `reserve_only`, `reserve_credits=1000`. 기존 선택 credential ID와 입력4,000/출력2,000 기술 상한은 유지했다.
- 저장 전후 call_count32와 uncertain held183이 동일함을 실제 로컬 API로 확인했다. 원장을 초기화하지 않았다.
- `python -m harness autocommit --enable`로 현재 managed DB의 자동 커밋을 활성화했다.

```powershell
python -m harness autocommit
python -m harness autocommit --enable
python -m harness autocommit --disable
python -m harness autocommit --task TASK-ID
python -m harness codex-gms-check
```

자동 커밋은 검증 성공과 필요한 approve 뒤에 수행한다. 작업 worktree가 detached면
`codex/harness-<task-id>` 브랜치를 만든다. 원래 App checkout의 미커밋 변경을 옮기거나 덮지 않는다.
검증 결과의 base commit/파일 SHA256/범위가 일치해야 한다. 원래 index에 staged 변경이 있으면
커밋을 보류한다. 임시 index에는 허용 파일만 올리고 commit 뒤 해당 index 항목만 동기화한다.
크래시 재요청은 commit receipt와 base를 검증하고 중복 commit을 막는다. 사용자 staging이 생기면
복구를 자동 추측하지 않고 보류한다. API 키 할당/비밀 패턴·민감 파일·raw/DB/log/runtime은 차단한다.
실패는 report의 commit_status/commit_error에 기록하며 테스트 성공 상태를 바꾸지 않는다.
push/merge/amend/force/reset은 수행하지 않는다. hooks/GPG 설정은 전역으로 변경하지 않는다.

## Codex CLI와 GMS의 현재 경계

실제 설치 CLI0.162.1을 작업별 local custom provider로 실행해 `/v1/responses` 요청을 확인했다.
서버는 임시 인증 헤더로 보호하고 구조 메타데이터만 저장했으며 upstream 호출은0회다.
관측 요청은91,717바이트, 배열 input/stream=true다. 입력 원문·도구 내용·인증 헤더는 보관하지 않았다.

**native_gms_ready=false**다. 기존 gms-work는 입력을 초안 프롬프트로 바꾸고 출력 텍스트만 추출한다.
Codex native 경로에는 전체 Responses 요청 동결/count·배열 입력·도구 결과·raw output·SSE·공통 정산이 필요하다.
현재 입력4,000 정책은 앞서 실제 Codex 호출에서 관측한28,467토큰 입력보다 작다.
instruction/tool을 빼서 count를 낮추거나 키를 CLI 환경변수에 직접 넣지 않았다.
호환 bridge·도구 왕복·예산 정책을 검증하기 전에는 native GMS를 제공한다고 표시하지 않는다.
GMS **코드·테스트·문서 초안 adapter는 실제 작동**하며 계속 우선 사용한다.

근거: [공식 gateway 요구](https://learn.chatgpt.com/docs/enterprise/gateway-compatibility),
[custom provider](https://learn.chatgpt.com/docs/config-file/config-advanced),
[전체 입력 카운트](https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count).

## 실제 검증과 GMS 활용

새 최소 보존 경계/최대 예약/uncertain 보류/재시작/누적 호환 회귀를 추가했고 기존 관련34개를 실행했다.
오토커밋의 실제 Git·승인 관리·App 변경 보호·크래시 receipt·원본 staged index·일반 키/경로 차단9개와
합성 gateway probe1개를 실행했다. LUNA의 첫 큰 Git 테스트 초안은 output_limited로 적용하지 않았다.
작은 경로 테스트 초안은 입력200/출력305토큰으로 available, 실제 reserve1000 정책에서 수신해 검토·반영했다.
독립 read-only 검토가 발견한 크래시 index 복구와 접두사 없는 API 키 할당 차단을 수정하고 실제 검사했다.

## Final verification

최종 `.venv/Scripts/python.exe -X utf8 scripts/verify_environment.py --gstack` exit0.
제품281개·팀27개·합성CLI·고정gstack58 통과. 기본/브랜치 SDD도 통과했다.
이전280개 전체 통과 후 추가한 작업 소스 import 회귀까지 포함한 최종 결과다.
최종 공식 key-info(2026-10-15 13:12:09 KST)는 잔액29,078, reserve_only 최소1,000, uncertain 보류183이다.
이 설정/한도 변경으로 원장이나 보류를 초기화하지 않았다.

기준 커밋 `d823032`에 기존 미커밋 MVP/하네스 코드·문서139개를 검토된 경로 manifest로 보존했다.
데이터/DB/키/런타임은 포함하지 않았고 사용자 원본 파일을 되돌리지 않았다.
실제 저장소 CLI smoke TASK-CLI-INTEGRATION-SMOKE: 등록→별도 HEAD worktree→Planner8검사→명시 approve→COMPLETED.
코드 변경이 없는 실행이라 auto_commit=no_changes로 기록했고 불필요한 commit을 만들지 않았다.
검증 subprocess의 import 경로는 작업 worktree src를 우선하도록 고정했고 실제 수정 모듈 import 시험13개 suite가 통과했다.
