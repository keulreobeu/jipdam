# 위키 자동 관리 운영

```json
{"content_hash":"6b43def3c70a99a21e6982d882c325ab8440b77401371773f6dfdb2164238e34","created_at":"2026-10-22T00:26:53+00:00","environment":"Windows / Python 3.12 / official Atlassian connector","id":"WIKI-5BA57A2BFC7C9BCA","key":"WIKI-AUTOMATION","kind":"guide","module":"developer-wiki","owner":"keulreobeu","project":"jipdam","publication_approved":false,"replacement":null,"review_at":"2027-04-20T00:29:49+00:00","reviewer":"agent-codex","revision":2,"risk":"low","sources":[{"path":"outputs/budongi_mvp_temp/docs/wiki/AUTOMATION.md","sha256":"55518d3a62c8f3a04c41948a462f7a19a8af1e196c6a83b0f11cec50657648f1"}],"status":"ACTIVE","task_id":"TASK-WIKI-001","title":"위키 자동 관리 운영","updated_at":"2026-10-22T00:29:49+00:00","verified_at":"2026-10-22T00:29:49+00:00","version":"WIKI-001-v1"}
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

## 주의사항 및 예외

자동 판단은 무조건 신규 생성하지 않는다. 근거 해시·revision·수동 내용을 확인한다. 보안/개인정보/비용/핵심 운영 게시에는 실제 소유자 승인 근거가 필요하다. 영구삭제하지 않는다. 기존 실험 기록과 제품 부동산 RAG를 자동 승격하지 않는다. agent/worker가 멈추면 그동안 원격 사건을 자동 감지하지 않는다.

## 검증 방법 및 결과

2026-10-22 제품 회귀320개·팀 도구27개·최종 위키 검사24개 통과. 정책·운영·팀원 권한 안내를 Confluence에 게시하고 실제 저장본을 다시 읽었다. 전체 verify_environment 진입점은 다른 작업의 tmp/pdfs 임시 파일 SDD 미연결로 중단됐다. 이번 작업의 SDD 정합성은 별도로 검사한다.

## 관련 원본

저장소 원본: outputs/budongi_mvp_temp/docs/wiki/AUTOMATION.md
정책: https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/131074
작업: https://kwulreobeu.atlassian.net/browse/KAN-19
