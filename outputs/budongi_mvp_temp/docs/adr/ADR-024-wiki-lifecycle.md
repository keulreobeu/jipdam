# ADR-024 — Evidence bound local wiki and connector outbox

Status: Accepted, 2026-10-22 사용자 정책 실행 요청. WIKI-001 / TASK-WIKI-001 / KAN-19.

문서화 판단은 결정적 코드, 문장과 의미의 검토는 담당 agent로 분리한다. 별도 LLM agent나
상시 유료 모델을 필수화하지 않는다. 코드 정합성 확인에 필요한 source hash와 검토자를
기록하며 검색 결과가 불완전하면 새 문서를 생성하지 않는다.

SQLite transaction으로 ID/revision/event/decision/outbox를 관리한다. Markdown은 읽기 쉬운
공유 산출물이지만 저장 중 수동 수정은 content hash로 검사하고 충돌을 덮어쓰지 않는다.
DB와 파일 사이 장애는 복구 큐에서 재개한다. 검색은 현재 상태/근거/파일을 확인하므로
파생 인덱스가 남아 있어도 비활성 문서를 최신 지식으로 반환하지 않는다.

외부 서비스는 공식 host connector만 사용한다. Python에 OAuth/키나 임의 HTTP 게시를
추가하는 대신 outbox 요청과 실제 connector 결과 receipt를 연결한다. 외부 대상/권한이
미설정이면 초안·대기 상태를 명확히 보존한다. 원격 이벤트는 명시 CLI ingest이며
로컬 worker는 주기 유지관리를 수행한다. 웹훅/OS 서비스 자동 설치는 별개다.

대안인 매 작업 무조건 신규 위키 생성은 중복을 늘린다. 파일만을 상태 정본으로 사용하는
방식은 이벤트 멱등성/동시 편집/부분 성공 복구가 불명확하다. vector DB는 현 단계
불필요하며 ACTIVE 메타데이터 검색과 담당자의 의미 검토로 정책 경계를 지킨다.
