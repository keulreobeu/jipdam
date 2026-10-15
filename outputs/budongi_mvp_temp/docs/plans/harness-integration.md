# Harness integration — bounded implementation plan

대상: 제공 `Jipdam_Harness_Integration_Plan.md`와 현재 사용자의 Phase 0→최소 코어 구현 요청.
기존 미커밋 변경은 사용자 소유이며 새 패키지/테스트/스크립트를 추가한다.

```text
Master(kind/scope/AC) → Store.claim → JSON job → native host/manual CLI
                                           → trusted Master checks artifacts
Store.complete ← result(JSON/hash/AC/evidence) ← Reviewer/Evaluator
        ↓
SQLite task/run/event/checkpoint    Mock Gateway → reserve → call → settle/uncertain
```

| 단계 | 담당·파일 | 검증·완료 조건 |
| --- | --- | --- |
| 0 | Master + read-only source_assessment | 기존 계약/현황/ZIP hash/라이선스·충돌·재사용 표 |
| 1 | Master Engineer; src/jipdam_harness, scripts/agent_harness.py | 상태·claim·중단·재시작·hash·AC 테스트 |
| 2 | Master; Mock gateway | 동시 예산·재시도·unknown spend·캐시·키·live 차단 |
| 3 | Master; Codex 역할·공통 운영 문서 | native 위임 증거와 정적 설정 검증을 분리 |
| 4 | 독립 Reviewer/Evaluator + Master | 실제 검사·문제 수정·SDD/회귀·검증 문서 |

구조 검토: 표준 SQLite를 재사용하고 코어 4개 모듈(contracts/state/gateway/cli)과 진입 스크립트로 구성한다.
호스트 실행 API·제품 추론·보관함과는 경계를 둔다. 상태/이벤트의 이중 쓰기는 같은 DB 트랜잭션으로 제거한다.
성능은 작은 개발 작업 큐/최대 active 2를 기준으로 하고 원격 분산 실행·GPU·웹 dashboard는 범위 밖이다.
오류는 DB lock timeout→busy, 오래된 lease→stale_run, 불명확 provider 소비→예약 보류,
검증 누락→verified 거부, 손상 checkpoint→명시 오류다. 중단은 진행 worker에 별도 interrupt를 요구한다.
검증은 unittest 합성 fixture + 별도 Python 프로세스 + 기존 제품 suite/SDD다. 데이터/유료 API 호출은 없다.

gstack plan-eng-review 시작 도우미는 Git Bash NtCreateDirectoryObject 0xC0000022로 실행 실패했다.
로컬 Architecture/Code quality/Tests/Performance 검토는 본문 설계에 반영하며 정식 gstack 로그·
외부 CLI voice·완료 인증은 not_run이다. 사용자의 명시적 최소 구현 지시에 따라 가역 구현을 계속한다.
추가 구조 승인·유료 호출 승인으로 해석하지 않는다.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
| --- | --- | --- | --- | --- | --- |
| Eng | 현재 구현 요청 | portable core/GMS 경계 | 1 | PARTIAL | native 로컬 검토, Bash helper 실패 |
| Outside voice | 정식 리뷰 | 별도 외부 CLI 요청 없음 | 0 | NOT_RUN | native 독립 source/review는 별도 기록 |
| VERDICT | 게이트 | 정식 로그 없음 | 1 | NOT CLEARED | 구현/테스트 결과와 별개 |

NO UNRESOLVED DECISIONS
