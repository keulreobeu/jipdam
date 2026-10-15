# Portable Developer Harness

```toml
kind = "spec"
id = "HARNESS-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-14"
approval_ref = "현재 대화: Phase 0 분석 후 최소 Python 공통 하네스·선택적 역할·Mock GMS 구현 및 실제 테스트 요청"
```

개발 제어 계층이다. 제품 추천·SQL·키 보관함·기존 GMS-001/GMS-BUDGET-001과 분리한다.
제공 설계의 GMS-001 ID 재생성은 기존 계약과 충돌하므로 하지 않는다.
이번 범위는 오프라인 코어와 수동/native 호스트 인계다. 실 GMS는 키 조회 없이 차단한다.
30,000은 합성 예산 시나리오이며 실제 할당·크레딧·기존 10,000토큰 정책으로 해석하지 않는다.

## HARNESS-001-REQ-01 공통 상태

SQLite 트랜잭션에 Task/Run/event/checkpoint/artifact/result를 함께 기록한다.
Task는 queued → planning/implementing/reviewing/evaluating → queued 또는 verified,
실패는 failed/blocked/stopped다. 역할은 direct=Master→Evaluator,
bug=Engineer→Evaluator, feature=Planner→Engineer→Reviewer→Evaluator,
audit=Reviewer→Evaluator다. 자동 복잡도 추측 대신 Master가 kind를 명시한다.
동시 active claim 최대 2, 쓰기 역할의 겹치는 scope는 직렬화한다.
완료된 단계는 재실행하지 않는다. 중단된 현재 run_id는 유지하고 attempt/lease를 갱신한다.
running 복구는 운영자의 명시적 recover-running 선언이 필요하며 오래된 결과는 거부한다.
stop은 DB에 즉시 반영하고 새 배정/늦은 완료를 막는다. 이미 실행 중인 native 도구는
Master가 별도로 interrupt해야 한다. 외부 효과의 exactly-once 실행은 주장하지 않는다.

### HARNESS-001-AC-01 저장·재개·멱등성

역할 순서, 같은 Task/동시 claim 거부, stop fencing, 실제 프로세스 종료 후 동일 run 재개,
체크포인트 무결성·이벤트 커서, 완료 결과 중복 기록 방지와 AC 미검증 verified 차단을 검사한다.

## HARNESS-001-REQ-02 범위와 증거

작업은 명시 Task ID/목표/scope/AC만 허용한다. 결과는 run/task/host/role/status,
artifact SHA256, verification의 AC/command/exit_code/evidence SHA256,
errors/token_usage/provenance다. Master는 실제 증거 파일을 확인하고 결과를 제출한다.
Evaluator의 모든 AC passed와 실파일 해시가 필요하다. 검증 명령 문자열은 자동 실행하지 않는다.
수동 제출은 신뢰된 로컬 담당자의 증명이며 테스트가 실행됐다는 암호학적 보장은 아니다.
원문 키 패턴은 입력/출력에서 거부하고 provider 오류 원문은 저장하지 않는다.
하네스는 임의 셸·Git·SQL·키 조회를 실행하지 않는다. native Engineer의 실제 파일 접근은
host sandbox와 Master 검토가 강제해야 하며 scope 선언만으로 OS 격리를 주장하지 않는다.

### HARNESS-001-AC-02 보안·증거

경로 이탈·해시 변조·키 fixture·필수 AC 누락·stale lease를 거부하고 민감 원문이 DB/응답에 남지 않는다.

## HARNESS-001-REQ-03 호스트 인계

Codex를 우선으로 역할 TOML과 Master 절차를 제공한다. 실제 native tool은 호스트에서 호출하고
공통 JSON job/result로 기록한다. CLI는 수동 adapter이며 자동 agent subprocess를 만들지 않는다.
Claude/Antigravity는 같은 context/resume/result를 사용할 수 있지만 native 등록·hook은 미검증이다.
알 수 없는 host는 unsupported_host. 토큰 집계 미제공은 null이며 0으로 기록하지 않는다.

### HARNESS-001-AC-03 호스트 공통 계약

호스트를 바꿔 동일 task/run을 이어받고 역할·범위·결과를 검증한다. Codex 설정 정적 검사와
실제 native 위임 증거를 구분하며 다른 호스트의 미실행을 not_run으로 남긴다.

## HARNESS-001-REQ-04 Mock Provider Gateway

Provider capabilities/complete/usage, operation/model 명시 검증, 입력/출력/호출/카테고리 제한,
원자적 최대 토큰 예약·usage 정산·실패 uncertain 보류를 제공한다. 라이브 GMS는 항상 disabled다.
요청 ID는 영속 멱등 키이며 다른 payload 재사용은 거부한다. 캐시는 메모리 TTL만 유지하며
키는 provider/model/operation/prompt_version/snapshot/permissions/category/input/output 상한이다.
DB에는 prompt/응답 원문을 저장하지 않는다. 재시작 뒤 settled 요청은 already_completed로 반환하고
원격 호출을 반복하지 않는다. 명확한 무과금 429만 최대 1회 재시도한다. 500/timeout/usage 누락은
최대 예약을 유지하며 결정적 로컬 fallback을 반환한다. circuit/cooldown/호출 원장은 재시작 후 유지한다.
Mock 기본 전체 30,000/예비 3,000, development 10,000/quality 7,000/demo 10,000이며
실계정 할당이 아니다. 실제 Provider를 추가할 때 기존 GMSBudgetManager/보관함·실잔액·5,000크레딧
보존·유료 count 예약과 하나의 통제 경로로 연결해야 하며 별도 토큰 DB로 우회할 수 없다.

### HARNESS-001-AC-04 예산·장애·캐시

동시 10건의 예약이 일반 예산을 넘지 않고, 재시작/캐시/중복/429/500/timeout/usage 누락/
상한 위반/미지원 operation/model/키 fixture를 실제 오프라인 테스트한다. live 요청 0회다.

## HARNESS-001-REQ-05 기존 계약 보존

VQA archive는 정적 분석만 하고 라이선스 미확인으로 소스를 복사하지 않는다.
기존 미커밋 변경·제품·SDD·GMS 원장을 보존한다. 테스트의 환경 실패·기존 실패는 분리 기록한다.

### HARNESS-001-AC-05 분석·회귀·추적

파일별 재사용 결정/해시/출처·실제 에이전트·검사 결과·토큰 미확인을 기록하고 SDD와 제품 회귀를 실행한다.

[Plan](../plans/harness-integration.md) · [ADR](../adr/ADR-020-portable-harness.md) ·
[Task](../tasks/harness-integration.md) · [운영](../harness/README.md)
