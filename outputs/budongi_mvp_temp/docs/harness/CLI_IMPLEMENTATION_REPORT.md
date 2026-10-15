# CLI 하네스 구현·검증 기록 — 2026-10-15

## 구현 범위

[CLI-HARNESS-001](../specs/20_cli_harness_spec.md), [TASK-CLI-HARNESS-001](../tasks/cli-harness.md).
등록·상태·보고·우선순위·의존성·독립 worker·실행기 변경·일시정지·재개·취소·재시도·승인·수동 초안 재검증을 구현했다.
SQLite 상태/이벤트, lease/PID 복구, OS 잠금, worktree, timeout/프로세스 트리 종료,
Codex JSONL/session/usage와 GMS 기존 runner 초안 adapter/Mock을 제공한다.
기존 미커밋 제품·데이터·원장·수동 native 하네스를 보존했다. [운영 명령](CLI_OPERATIONS.md).

## 검증

새 수용 테스트 35개(실제 Git/worktree·검증 프로세스 12, provider 15, Planner 8)를 구현했다.
제품 전체 265개 통과 후 UTF-8 실제 child/loopback 회귀와 중복 의존성 검사를 추가했다.
루트 팀 검사 27개 통과, 고정 gstack 58개 정적 검증 통과.
최종 공식 환경 검사 결과는 아래 최종 검증 절을 따른다.

## 실제 연결

공식 npm Codex CLI 0.162.1 설치 성공. App 내장 0.155.1과 공존한다.
exec/resume 옵션은 설치 버전 help로 확인했다. 기존 ChatGPT 로그인을 변경하지 않았다.
설치 CLI의 실제 read-only 최소 요청 성공: HARNESS_SMOKE_OK,
session 01a13d0c-1d92-7683-9431-cec48e6c65ae, input_tokens 28467/output_tokens 9/cached_input_tokens 0.
이는 최소 추가 prompt에도 프로젝트/사용자 규칙 등 CLI 문맥 비용이 있음을 보여준다. 입력 크기를 임의 추정하지 않는다.
raw 인증/CLI stderr는 보고하지 않는다. 로컬 sanitized 증거는 ignored runtime에 있다.

GMS는 초기 8765/8785 연결 실패 후 사용자 Windows 세션에서 기존 credentials 서버를 8786으로 준비했다.
저장 정책 enabled/reserve_only/reserve_credits=5000을 확인했으며 변경하지 않았다.
SOL 구조 검토는 input 1123/count 20크레딧 후 생성 결과 불확실로 최대183크레딧을 uncertain 보류했다.
같은 불확실 요청을 재시도하지 않았다. LUNA 첫 Planner 초안은 output_limited(185/1000토큰)로 적용하지 않았고,
정산이 확인된 뒤 별도 보완 초안(182/775), 테스트 초안(195/817), 복구 문서(1230/770)를 받아 로컬 검토·반영했다.
새 adapter의 실제 Planner 기능 검토도 draft 성공(618/728)했으며 중복 의존성 지적을 로컬 코드/테스트에 반영했다.
초안 성공을 코드 검증으로 계산하지 않았다. 실제 테스트 결과를 별도로 기록한다.

초기 adapter 실패는 실제 하위 Python의 Windows 기본 인코딩이 UTF-8 stdin 문맥과 달랐기 때문이다.
로컬 GET/state와 CSRF는 성공하고 한국어 prepared payload만 실패하며 원격 원장 접수0건인 것을 확인했다.
하위 stdin의 명시 UTF-8 디코딩/환경을 적용하고 실제 child+합성 HTTP 왕복 및 라이브 초안으로 재검증했다.
첫 오류들을 확인 없이 유료 생성 재시도로 바꾸지 않았다. 키/정책/원장을 우회하거나 초기화하지 않았다.

## 독립 검토와 한계

실제 native explorer가 기존 상태/GMS 재사용 경로를 조사했고 worker가 provider와 오프라인 검사를 구현했다.
독립 evaluator는 읽기 전용 상태·옵션·CLI·provider/기존 하네스 검사를 실행했다.
검토에서 draft 재검증 dead-end, 승인 후 변경, ignored 파일 변경, retry/pause 경합,
검증 예외·시간제한, pytest basetemp 우회, bytecode 부작용을 발견해 보완했다.
evaluator는 역할의 Git 변경 금지 때문에 worktree E2E를 독립 실행하지 않았다. Master가 실제 임시 Git 검사를 실행한다.
에이전트별 토큰은 제공되지 않아 unknown이다.

gstack engineering helper는 Git Bash NtCreateDirectoryObject 0xC0000022로 시작하지 못했다.
정식 gstack 리뷰 인증을 주장하지 않으며 로컬 설계·독립 검토·실행 검사로 증거를 남긴다.
CLI 설치의 첫 sandbox npm 시도는 DNS 실패였고 승인된 외부 설치 경로에서 성공했다.
초기 테스트의 sandbox TEMP ACL 오류는 workspace TEMP로 검증해 분리했다.

Codex 실제 파일 편집/세션 재개의 유료 smoke는 실행하지 않았다. 해당 경로는 fake CLI와 실제 Git/검증 subprocess로 검사했다.
GMS 자동 patch/tool 실행, OS 서비스 등록, 분산 실행, 자동 merge/정리,
지능형 독립 Planner, Claude/Antigravity native 실행은 완료로 주장하지 않는다.
GMS 초안은 담당자 수동 적용/validate/approve가 필요하다. 서버 호출이 이미 접수된 뒤 client를 종료해도
원격 작업이 취소되는 것은 아니므로 uncertain 원장을 확인한 뒤 재시도를 판단한다.

## GMS 최종 원장 확인

2026-10-15 10:08:22 KST 공식 key-info 잔액 29,092크레딧, 만료 2026-10-16 18:00 KST.
reserve_only 보존 5,000, uncertain 보류 183크레딧을 유지했다. 원장 대사 전 보류를 해제하지 않았다.
이번 LUNA는 코드·테스트·운영 문서·기능 검토 4개 결과를 성공 수신했고, 출력 제한 초안 1개는 적용하지 않았다.
SOL uncertain 1건은 성공으로 표시하거나 재시도하지 않았다. 계정 차감과 로컬 요율 원장은 서로 다른 관측이며 동일하다고 가정하지 않는다.

## 검증 중 발견한 환경·기존 검사 이력

첫 전체 root 디렉터리 직접 실행은 제품 scripts namespace import 경로가 달라 1개 import 오류였다. 공식 제품 cwd로 재실행해 265개 통과했다.
공식 진입점의 다음 실행은 기존 test_file_canonical의 CLI publication 1건이 collection_processing_failed로 실패했고,
즉시 같은 환경의 분리 재검증에서 관련 9개가 통과했다. 원인을 단정하거나 제품 코드를 변경하지 않았다.
별도 전용 TEMP에서 공식 전체 검사를 재실행한 결과는 최종 검증 절에 기록한다.
초기 29개 소켓 오류는 sandbox WinError10013이고 loopback 허용 환경에서 사라졌다.

전용 workspace TEMP의 후속 실행은 다른 기존 canonical stage 승격에서 os.rename WinError5가 발생했다.
실패 지점은 source_files.py의 완료된 임시 staging 디렉터리 승격이며 해당 코드는 이번 작업에서 변경하지 않았다.
workspace TEMP의 접근/잠금 영향을 분리하기 위해 사용자 기본 TEMP에서 공식 검사를 실행했다.

## Final verification

사용자 기본 TEMP에서 공식 `.venv/Scripts/python.exe -X utf8 scripts/verify_environment.py --gstack` exit0.
제품267개·팀27개·모델 없는 합성CLI·고정gstack58 통과. 새 하네스 수용35개는 제품267개에 포함된다.
기본 및 `--base origin/main` SDD도 통과했다.
이후 사용자의1,000보존·자동커밋 후속 요청은 [후속 검증](OPERATIONS_UPDATE_20261015.md)으로 별도 추적한다.
