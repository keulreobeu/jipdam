# ADR-020 — Offline portable developer control plane

Status: Accepted (2026-10-14 현재 사용자 구현 요청).

기존 GMSBudgetManager는 크레딧/실잔액/count까지 통제한다. 이를 새 토큰 가정으로 교체하지 않는다.
독립 `jipdam_harness` 패키지에 표준 라이브러리 SQLite와 버전 1 JSON 계약을 두고 제품 경로를 보존한다.
DB가 상태/이벤트/체크포인트의 정본이며 Markdown/JSONL은 파생 출력이다. 별도 파일 잠금 대신
SQLite BEGIN IMMEDIATE로 Windows에서도 실패를 숨기지 않고 직렬화한다.

원본 ZIP에 명시적 라이선스가 확인되지 않아 소스 복제 없이 운영 패턴을 독립 구현한다.
호스트 SDK를 코어에 종속시키지 않는다. CLI는 job을 내보내고 Master가 native agent를 실행한 뒤
실파일 증거와 결과를 제출한다. 자동 subprocess 실행/권한 확대/자동 Git은 없다.
호스트 전환 시 같은 run을 lease fencing으로 보호하고 완료 단계는 보존한다.

Mock만 구현해 라이브 전환 스위치 자체를 제공하지 않는다. 향후 GMS는 기존 보관함/예산 통제를
통합한 별도 Task가 필요하다. 프롬프트/응답을 DB 캐시에 보관하는 대신 프로세스 메모리 TTL을 택한다.
재시작 멱등성은 응답 재생보다 중복 호출 방지를 우선해 already_completed로 보고한다.

[Spec](../specs/19_harness_spec.md) · [Plan](../plans/harness-integration.md)
