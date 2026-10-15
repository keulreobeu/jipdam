# CLI-First App-Managed Harness

```toml
kind = "spec"
id = "CLI-HARNESS-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-15"
approval_ref = "첨부 Principal Agent Systems Architect 계획 실행·Codex CLI 설치·목표 설정 요청"
```

## CLI-HARNESS-001-REQ-01 영속 관리

HARNESS-001 수동/native 계약은 보존하고 독립 managed SQLite 상태·트랜잭션 이벤트를 추가한다.
App은 같은 저장소에서 명시 CLI로 등록/상태/우선순위/일시정지/재개/취소/재시도/승인/실행기 변경/보고를 수행한다.
작업은 안정 ID, 목표, scope, AC, 의존성, 실행/안전/검증 정책을 가진다. 승인된 로컬 작업 명세만 실행한다.
App이 분해한 명시 tasks를 plan 명령으로 검수하며 Python Planner는 순환/누락/중복을 거부하고
의존성 우선·ready 작업 사이 우선순위/ID 순서를 결정한다. 별도 자연어 자동 분해 모델은 강제하지 않는다.
COMPLETED는 모든 결정적 검증 및 필요한 승인 충족이다. 자연어 AC만으로 자동 완료하지 않는다.

### CLI-HARNESS-001-AC-01

등록 멱등성, 상태 이벤트, 의존성·우선순위·승인·완료 게이트, 재시작 보고를 검증한다.

## CLI-HARNESS-001-REQ-02 실행·격리·복구

Codex CLI 비대화형 JSONL/종료코드/세션/usage, 시간제한/프로세스 트리 정리를 지원한다.
실행은 별도 Git worktree에서 수행하고 자동 merge/push하지 않는다. 미커밋 원본은 덮지 않는다.
기본 worktree는 HEAD 기반이며 미커밋 변경은 자동 복사하지 않는다. 동일 저장소 worker는 직렬 실행한다.
scope는 컨텍스트·결과 검수 경계이며 OS 파일 접근 격리라는 주장을 하지 않는다.
중단/복구는 기존 worker 종료 확인 뒤 lease를 갱신하고 변경사항을 검사한다.

### CLI-HARNESS-001-AC-02

중복 worker 차단, pause/cancel 프로세스 종료, stale lease, 비정상 종료 복구,
실제 임시 Git worktree 격리 및 범위 이탈 검출, 테스트 실패의 제한 재시도를 검증한다.

## CLI-HARNESS-001-REQ-03 Provider와 예산

기본 Codex, 별도 GMS 초안, 오프라인 Mock 인터페이스를 제공한다. 429 단독은 quota가 아니다.
quota/rate-limit/auth/network/permission/unknown을 구분하며 자동 전환은 명시 flag와 무변경 확인이 필요하다.
GMS는 기존 prepare_work/LocalGMSWork와 선택된 보관함·공통 원장·reserve_only 5,000 보존만 사용한다.
GMS는 shell/tool 실행기가 아니며 생성 초안은 검토 대상으로 보관한다. 자동 적용/성공 승격을 하지 않는다.
API 실패 후 자동 중복 GMS 호출은 금지하고 불확실 결과는 대기시킨다.

### CLI-HARNESS-001-AC-03

Codex fake-process JSONL, quota와 rate-limit 구분, opt-in Mock 전환, 변경 후 전환 차단,
GMS 기존 runner 위임과 draft 승인 게이트·오류 시 대기를 외부 호출 없이 검증한다.

## CLI-HARNESS-001-REQ-04 운영·보안

런타임은 ignored .local_runtime/harness-managed. DB 정본에서 JSONL/공유 요약을 파생한다.
최소 명시 코드 파일만 컨텍스트로 사용하며 data/raw/DB/키/로그/인증/런타임을 전송하지 않는다.
출력/오류는 비밀 패턴 제거·크기 제한, 검증은 shell=False의 허용 Python 테스트/Git diff 명령만 지원한다.
독립 worker는 앱 세션에 의존하지 않는다. 로그인·실제 모델·GMS 준비 미충족은 사실대로 기록한다.

### CLI-HARNESS-001-AC-04

관리 CLI subprocess E2E, 컨텍스트 경로/비밀 경계, 로그 정제, 운영 문서·환경 검사와 기존 하네스 회귀를 검증한다.
