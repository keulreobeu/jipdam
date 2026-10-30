# Controlled facility benchmark and objective-once context

```toml
kind = "spec"
id = "BENCH-CONTEXT-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-30"
approval_ref = "현재 대화: BENCH-FACILITY-001 실제 Baseline/원상태 반복 후 Objective 중복 제거 한 변수 비교"
```

## BENCH-CONTEXT-001-REQ-01 사전 봉인과 계측 확인

OBS-001을 재사용한다. 먼저 비과금32개·CLI0.164.0/ChatGPT 인증·공식 Usage smoke를 확인한다.
키를 읽거나 API 요금 경로로 전환하지 않는다. 현재 구성의 gpt-6.1-terra/high를 고정한다.
모델은 provider constructor와 Task.execution.model에 같게 명시한다. CLI가 실제 모델을
보고하지 않으면 observed_model=null로 남기고 configured model만 확인됐다고 명시한다.
두 조건 모두 native multi_agent/multi_agent_v2와 memory를 비활성화한 단일 구현자 조건으로
고정한다. 현재 user 설정의 multi_agent=true를 그대로 대표하는 무통제 운영 baseline이 아니라,
이 고정 조건에서의 첫 baseline이다. 부모의 Git 전담 역할은 별도이며 CLI 모델 토큰에 합산하지 않는다.

공통 시작 C_SHA는 main b29d2d4 기반의 명세/독립 평가/runner/opt-in option 준비 commit이다.
시설 구현 파일은 C_SHA에 존재하지 않아야 한다. 모든 worker는 C_SHA에서 새 detached
worktree·세션으로 시작한다. 과제/AC/evaluator/schema/hash/CLI/model/reasoning/sandbox/허용
도구/파일/context를 실행 전에 봉인하고 첫 실행 뒤 바꾸지 않는다. 관측 수정이 필요하면
사전 검증부터 별도 새 실험으로 시작하고 실패 비용을 삭제하지 않는다.

### BENCH-CONTEXT-001-AC-01

실제 smoke의 공식 Usage·complete 또는 미완전 원인과 봉인 manifest SHA를 기록한다.
미완전 실측을0이나 synthetic으로 채우지 않는다.

## BENCH-CONTEXT-001-REQ-02 Objective 한 변수

Task execution.objective_mode는 repeat(기존 기본) 또는 once다. repeat는 기존
`objective + '\n\n' + pack_context`를 보존한다. once는 context가 trusted pack_context의
정확한 첫 Task/objective section으로 시작할 때만 prepended objective를 생략한다.
직접 provider 호출 등 objective가 context에 없으면 repeat로 fallback해 목표가 사라지지 않는다.
컨텍스트/툴/모델/추론/재시도/승인/보안 정책은 두 조건에서 같다. 다른 문맥 최적화는 하지 않는다.
옵션은 명시 opt-in이며 기본을 바꾸지 않는다. 실제 비교 없이 전역 기본으로 승격하지 않는다.

### BENCH-CONTEXT-001-AC-02

미지원 모드 거부, repeat의 byte 호환, once의 objective 보존/중복만 제거, 직접 호출 fallback을
검사한다. 실제 전달 prompt는 저장하지 않고 byte/hash/전략만 기록한다.

## BENCH-CONTEXT-001-REQ-03 독립 품질·반복

파일 쓰기 scope는 새 team_package.py와 public test_team_package.py 두 개다. 사전 봉인한
test_team_package_acceptance.py/Spec/runner는 구현 agent의 수정 scope 밖이며 전후 hash를
확인한다. 독립 검사는 agent의 테스트 자기 선언과 구별한다. 평가 테스트가 repository에서
읽힐 수 있음을 밝히며 완전히 숨겨진 평가라고 부르지 않는다. 테스트/정책 수정으로 통과시키지 않는다.

고정 pilot 순서는 A1(repeat)→B1(once)→B2(once)→A2(repeat), fresh session, 각 max_attempts=2다.
첫 baseline 전에 objective-once 실험 결과를 보지 않는다. 각 성공 후보는 동일 독립 AC·회귀·범위·
보안 검사를 통과한 뒤 명시 approve한다. worker 실행 중 부모가 worktree를 편집하지 않는다.
검증 실패 후 수동 수정이 필요하면 measured run의 성공으로 세지 않고 별도 local repair로 기록한다.

### BENCH-CONTEXT-001-AC-03

모든 시도의 결과/토큰/오류를 보존하고 original item=1, repeat/trial=4를 구별한다. 합성 입력을
사용한 실제 모델 개발 비용 실측이며 실제 시설 자료 품질 평가라고 부르지 않는다.

## BENCH-CONTEXT-001-REQ-04 비교와 전달

보고서는 Run/Attempt input/output/cache/known/complete·실패 토큰·AC·승인·wall time를 표시한다.
단계는 직접 관측한 implementation/validation만 귀속하고 이 App의 수동 기획/Jira/Git 작업은
측정 범위 밖이다. 사람 활동은 unknown이다. 각 trial의 suite/item 성공당 토큰과 고정 조건의
paired 차이·원시값을 보고한다. 반복 trial 수를 독립 제품 기능 수로 합산하지 않는다.
성공0 또는 incomplete/conflict면 확정 효율비는 null이며 품질 실패의 적은 토큰을 절감으로
발표하지 않는다. 1M 지표·달러 추정·구독 한도 환산은 제외한다. N=2 pilot은 통계적/인과적
우위 증명이 아니며 캐시·순서·비결정성 차이를 한계로 남긴다.

### BENCH-CONTEXT-001-AC-04

동일 C_SHA/모델/명세/평가와 모드만 다른 receipt를 대조하고 기존 baseline을 보존한다.
품질 검증된 구현 하나를 부모가 읽고 적용·전체 검증·위키·Git 절차로 전달한다. GMS는 이번
Codex 비교에 섞지 않는다. 일반 GMS 정책/1,000 보존·공통 원장은 변경하지 않는다.
