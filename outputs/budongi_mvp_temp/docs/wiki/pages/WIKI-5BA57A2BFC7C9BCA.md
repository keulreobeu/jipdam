# 위키 자동 관리 운영

```json
{"approval_ref":null,"content_hash":"c87f088a318c62d438086586f2e836eaca78499d221ef0f128b87263b24bf34f","created_at":"2026-10-22T00:26:53+00:00","environment":"Windows / Python 3.12 / official Atlassian connector","id":"WIKI-5BA57A2BFC7C9BCA","key":"WIKI-AUTOMATION","kind":"guide","link_checks":[{"checked_at":"2026-10-28T07:01:58+00:00","ok":true,"reviewer":"agent-codex","url":"https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/131074"},{"checked_at":"2026-10-28T07:01:58+00:00","ok":true,"reviewer":"agent-codex","url":"https://kwulreobeu.atlassian.net/browse/KAN-19"}],"module":"developer-wiki","owner":"keulreobeu","project":"jipdam","publication_approved":false,"publication_approved_by":null,"replacement":null,"review_at":"2027-04-26T07:01:58+00:00","reviewer":"agent-codex","revision":8,"risk":"low","sources":[{"path":"outputs/budongi_mvp_temp/docs/wiki/AUTOMATION.md","sha256":"d2b1a91b2d8189a18e42a8297c3efc2eb44d0bad79584e5e41704b857643d76d"}],"status":"ACTIVE","task_id":"TASK-WIKI-RECOVERY-001","title":"위키 자동 관리 운영","updated_at":"2026-10-28T07:01:58+00:00","verified_at":"2026-10-28T07:01:58+00:00","version":"WIKI-001-v1"}
```

## 목적 및 적용 범위

검증된 지식을 기존 문서 중심으로 유지하고 중복·노후·충돌·게시 실패를 관리한다. 적용 범위는 집담 개발 위키와 CLI 하네스다.

## 증상 또는 사용 상황

작업 검증 완료, API/CLI/설정/운영/의존성 변경, 장애 해결, PR 병합·배포 확인, 명시 문서화 요청 및 정기 유지관리 때 실행한다.

## 원인과 미확인 사항

기존 위키는 수동 기록 폴더였으며 검증·문서 ID·재검토·외부 게시 복구가 연결되지 않았다. 원격 웹훅과 OS 상시 서비스는 설치하지 않았다.

## 실행 절차

저장소 루트에서 실행:
python -m harness wiki maintenance
python -m harness wiki catalog
python -m harness wiki search --query 기능또는원인
관련 파일과 Confluence의 기존 문서를 실제로 검색·검토한다.
python -m harness wiki event --request .local_runtime/wiki-work/event.json
python -m harness wiki pending
python -m harness wiki delivery --id DELIVERY_ID
공식 Atlassian 도구로 대상 ID를 조회·게시한 뒤 실제 저장 결과를 다시 읽는다.
python -m harness wiki receipt --request .local_runtime/wiki-work/receipt.json
python -m harness wiki decision --event EVENT_ID
판단·사유·문서 ID/링크·검증·동기화 상태를 Task/Jira에 기록한 뒤 완료한다.
원격 read-back 전체 HTML 해시 확인:
python -m harness wiki remote-hash --file .local_runtime/wiki-work/readback.html
UTF-8/LF/끝 개행1개로 정규화한 값을 remote_hash로 사용한다.
공유 문서의 근거 변경 검토가 필요한 경우 wiki review-shared --request로 변경 전 파일 hash·revision과 검토 결과를 확인한다. Markdown 실패와 원격 동기화는 각각 대기로 보존한다.
기존 원격 binding이 없으면 공식 read-back을 검토하여 wiki bind-existing --request로 기준점만 연결한다. 이후 버전·해시를 다시 비교하고 실제 수정/read-back receipt를 기록한다.
원격 본문에 ID가 없으면 공식 read-back의 정확한 [문서 ID] 제목을 remote_title로 전달한다.

## 주의사항 및 예외

자동 판단은 무조건 신규 생성하지 않는다. 근거 해시·revision·수동 내용을 확인한다. 보안/개인정보/비용/핵심 운영 게시에는 실제 소유자 승인 근거가 필요하다. 영구삭제하지 않는다. 기존 실험 기록과 제품 부동산 RAG를 자동 승격하지 않는다. agent/worker가 멈추면 그동안 원격 사건을 자동 감지하지 않는다.

## 검증 방법 및 결과

2026-10-22 제품 회귀320개·팀 도구27개·최종 위키 검사24개 통과. 정책·운영·팀원 권한 안내를 Confluence에 게시하고 실제 저장본을 다시 읽었다. 전체 verify_environment 진입점은 다른 작업의 tmp/pdfs 임시 파일 SDD 미연결로 중단됐다. 이번 작업의 SDD 정합성은 별도로 검사한다.
2026-10-28 위키 복구 회귀 30개와 전체 환경 재실행 통과. 변경 근거 검토·내보내기 실패/재시도·고위험 승인·원격 대기를 합성 환경에서 확인했다.
원격 기준점 연결의 검토 누락·해시/호스트/버전 충돌 거부와 전송 대기 보존을 합성 테스트로 확인했다.
제목 기반 ID 일치 및 다른 제목 거부를 포함한 위키 테스트 32개가 통과했다. 전체 환경 검사는 Windows 디렉터리 rename 오류로 별도 재검증이 남았다.

## 관련 원본

저장소 원본: outputs/budongi_mvp_temp/docs/wiki/AUTOMATION.md
정책: https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/131074
작업: https://kwulreobeu.atlassian.net/browse/KAN-19
