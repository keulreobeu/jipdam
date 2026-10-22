# Wiki lifecycle management

```toml
kind = "spec"
id = "WIKI-001"
status = "approved"
owner = "keulreobeu"
revision = 2
approved_by = "사용자"
approved_at = "2026-10-22"
approval_ref = "첨부 Agent Harness — Wiki 자동 생명주기 관리 정책 v1.0 기반 위키 자동갱신 및 관리 실행 요청"
```

## Scope

첨부 정책 원문은 [정책](../wiki/LIFECYCLE_POLICY.md)에 보존한다. 로컬 CLI 하네스와
Codex·Claude 공통 작업 루프에 적용한다. 저장소 문서가 정본이고 외부 Wiki/Jira 연동은
인증정보를 저장하지 않는 outbox와 공식 연결 도구로 처리한다. 외부 대상 미설정은
성공으로 간주하지 않는다. 원본 DB·제품 추천 RAG·수집·push/merge/deploy는 범위 밖이다.

## WIKI-001-REQ-01 Evidence based decisions

검증 완료·PR/계약/운영/의존성 변경·장애·명시 요청·정기 점검 이벤트를 명시 CLI로 입력한다.
CLI 하네스 검증 성공은 자동으로 문서화 판단을 기록한다. Task/Jira 종료 전 그 결과를 확인한다.
반복 원인은 90일 이력과 전체 기존 문서를 검색한다. 조건·제외·검색 검토·근거가 불완전하면
REVIEW_REQUIRED다. 기존 key/ID/환경·버전/내용 검색을 우선하고 의미 검토는 담당자가 수행한다.
의미 검토가 없는 신규 생성을 완전한 중복 검색으로 표시하지 않는다.

### WIKI-001-AC-01

오타 SKIP, 반복 문제 CREATE/UPDATE, 미검증 REVIEW_REQUIRED, 정확한 기존 문서
LINK_EXISTING, 계약/절차 UPDATE, 임시 조치 만료·소유자·검증과 버전별 병행을 검증한다.

## WIKI-001-REQ-02 Safe writing and publication

필수 메타데이터·본문·로컬 근거 해시·참조 링크·적용 환경/버전·담당자 검토를 검사한다.
자동 작성은 명시된 근거를 템플릿으로 정리하며 임의 명령 실행·LLM 호출을 하지 않는다.
안전한 내부 문서만 자동 ACTIVE, 핵심 운영/보안/개인정보/비용은 명시 담당자 승인 후 ACTIVE다.
외부 대상/권한이 없으면 외부 게시를 하지 않는다. 이벤트 ID와 입력 해시의 멱등성,
문서 revision CAS, 수동 편집/충돌 보존, 변경 이력 및 민감정보 즉시 검색 격리를 제공한다.

### WIKI-001-AC-02

비밀·개인정보/누락·근거 변경·경로 이탈·동시 편집·중복 이벤트·수동 내용 덮어쓰기·
승인 누락·외부 게시 권한 누락을 거부하고 버전 및 안전한 변경을 보존한다.
팀원도 같은 지정 공간을 사용한다. 권한 부족은 대상 링크·실패 동작·보기/작성/편집 권한 요청
안내를 반환하고 본인 OAuth와 DRAFT/SYNC_PENDING을 유지한다. 권한 부여·자동 요청 발송을
수행했다고 추정하지 않는다.

## WIKI-001-REQ-03 Lifecycle and retrieval

DRAFT/REVIEW_REQUIRED/ACTIVE/STALE/DEPRECATED/SUPERSEDED/ARCHIVED/TRASHED를 유지한다.
재검토 30/90/180/365일과 임시 최대30일, 변경 근거/링크 실패/만료로 STALE 처리한다.
폐기는 사유·소유자 승인·지원 버전·인바운드 참조·보존 정책을 확인하며 영구 삭제하지 않는다.
병합은 대표 문서로 유효 내용 포함 확인 후 승인하고 이전 ID와 대체 링크를 유지한다.
일반 검색은 ACTIVE만, 이력 검색은 명시 상태·환경·버전 범위만 반환한다.

### WIKI-001-AC-03

중복3개 통합, 제거 기능 비권장/보관, 지원 과거버전 보존, 검토 만료·참조 불일치,
민감정보 격리 및 비활성/삭제 문서 검색 제외를 검증한다.

## WIKI-001-REQ-04 Recovery and operations

SQLite 트랜잭션이 상태/이력/판단/outbox 정본이다. Markdown과 검색은 그 상태를 확인한다.
새 팀원은 공유 Markdown의 본문 hash/근거/ID/revision을 확인하여 로컬 목록을 복원한다.
검증되지 않은 수동 변경은 자동 ACTIVE로 복원하지 않는다. 원격 이력이 없으면 기존 ID를
먼저 조회하고 검토해 연결한다. 로컬 DB가 없다는 이유로 중복 문서를 만들지 않는다.
부분 export/외부 동기화 실패는 SYNC_PENDING, 제한 재시도·최신 버전 확인·수신 영수증으로
복구한다. 미확인 원격 링크는 검토 대기로 두며 네트워크로 임의 URL을 가져오지 않는다.
필수 문서 미완료는 하네스 완료를 차단한다. 일반 외부 동기화 예외는 명시 승인 기록이 필요하다.
worker는 주기 점검을 수행하고 독립 agent는 작업 종료 전 같은 CLI를 사용한다.
외부 webhook/스케줄러/Confluence 자동 인증이 설치되었다고 주장하지 않는다.

### WIKI-001-AC-04

CLI·하네스 검증 hook·완료 게이트·재시작·충돌·네트워크 실패 대기·제한 재시도·
구버전 동기화 거부·ACTIVE 검색 일관성 및 품질 지표를 오프라인 검증한다.
