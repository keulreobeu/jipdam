# 팀원 위키 작성과 권한 요청

```json
{"approval_ref":null,"content_hash":"4e4c0e5efe057c0138957f4cf97734e7ecfde7ff52cb5ef117bc89e096dec78c","created_at":"2026-10-22T00:26:54+00:00","environment":"Windows / Python 3.12 / official Atlassian connector","id":"WIKI-B6B7A1FAAA4FA55B","key":"WIKI-TEAM-ACCESS","kind":"guide","module":"developer-wiki","owner":"keulreobeu","project":"jipdam","publication_approved":false,"publication_approved_by":null,"replacement":null,"review_at":"2027-04-20T00:36:32+00:00","reviewer":"agent-codex","revision":2,"risk":"low","sources":[{"path":"outputs/budongi_mvp_temp/docs/wiki/TEAM_ACCESS.md","sha256":"146aa7d53c0f0242ee94c1268a5022c6c2414247250cffca2283c6112e418590"}],"status":"ACTIVE","task_id":"TASK-WIKI-001","title":"팀원 위키 작성과 권한 요청","updated_at":"2026-10-22T00:36:32+00:00","verified_at":"2026-10-22T00:36:32+00:00","version":"WIKI-001-v1"}
```

## 목적 및 적용 범위

팀원이 같은 집담 개발 위키를 사용하고 권한 부족 시 적절한 접근 요청을 할 수 있도록 안내한다.

## 증상 또는 사용 상황

새 팀원의 첫 접근, 기존 문서 조회 실패, 페이지 작성·편집 권한 오류 또는 공식 Atlassian 연결 인증 실패 때 적용한다.

## 원인과 미확인 사항

공유 대상 설정은 Confluence 권한을 부여하지 않는다. 각 팀원의 개인 계정이 실제 보기·작성·편집 권한을 가져야 한다. 현재 개별 팀원의 권한 보유 여부는 확인하지 않았다.

## 실행 절차

1. 본인 Atlassian 계정으로 아래 대상 위키를 연다.
2. 보기/페이지 작성/편집 중 실패한 동작과 대상 링크를 확인한다.
3. 접근 요청 기능이 표시되면 사용하거나 공간 관리자에게 아래 문구로 요청한다.

집담 개발 위키에 검증된 작업 지식을 기록하려고 합니다. 제 Atlassian 계정에 이 공간/페이지의 보기 및 페이지 작성·편집 권한을 요청합니다. 현재 [실패한 동작]에서 권한 오류가 발생했습니다.
대상: https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/360449

4. 로컬 초안은 DRAFT, 게시 요청은 SYNC_PENDING으로 보존한다.
5. 권한 부여 뒤 실제 접근을 확인하고 동일 문서 ID로 동기화를 재개한다.
새로 받은 저장소에서는 공유 pages/의 ID·본문 hash·근거를 확인하여 기존 목록을 복원한다. runtime DB를 공유하지 않는다. 원격 binding이 없으면 같은 ID의 실제 Confluence 내용을 먼저 검토하고 snapshotToken으로 갱신한다.

## 주의사항 및 예외

본인 OAuth를 사용하고 다른 사람의 인증·토큰·키를 공유하지 않는다. 관리자 권한을 기본 요청하지 않는다. 접근 실패를 검색 결과0건으로 보고 중복 문서를 만들지 않는다. 권한 부여나 요청 메시지 자동 전송을 수행했다는 뜻이 아니다. 필수 문서가 막히면 Task/Jira를 미완료로 유지한다.

## 검증 방법 및 결과

2026-10-22 지정 공간65816/부모360449 및 실제 게시425985를 확인했다. 위키 검사26개가 통과했으며 권한 부족 안내, runtime DB 없는 팀원 clone의 기존 ID 복원, 미검증 수동 변경 복사본의 ACTIVE 차단을 포함한다. 팀원별 실제 권한은 본인의 접근 성공으로 확인해야 한다.

## 관련 원본

저장소 원본: outputs/budongi_mvp_temp/docs/wiki/TEAM_ACCESS.md
공통 작업 규칙: AGENTS.md 및 outputs/budongi_mvp_temp/AGENTS.md
대상: https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/360449
