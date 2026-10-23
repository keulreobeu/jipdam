# 집담 수집 데이터와 활용 가이드

```json
{"approval_ref":null,"content_hash":"f628c627c1d5f05fd4d3556740b14c19a3a177f6db60cf5c753ec889f2e6d731","created_at":"2026-10-22T04:52:32+00:00","environment":"Windows / Python 3.12","id":"WIKI-E162D573DBB6F1CD","key":"DATA-CATALOG","kind":"guide","module":"data-catalog","owner":"Codex","project":"jipdam","publication_approved":false,"publication_approved_by":null,"replacement":null,"review_at":"2027-04-20T04:52:32+00:00","reviewer":"agent-codex","revision":1,"risk":"low","sources":[{"path":"outputs/budongi_mvp_temp/docs/data-catalog.md","sha256":"a9d5239a8dc58f3c3df92db47a60d6be9c68e179b5f3ed6a174ef02a0dd1f99b"},{"path":"outputs/budongi_mvp_temp/docs/molit-statistics-history-validation-20261015.md","sha256":"f843ba6ef36b412d7691cee2074bc166f7a3b78eb5a5b566363fe951cfeeb32a"},{"path":"outputs/budongi_mvp_temp/docs/canonical-validation-20261013.md","sha256":"093159306440c82fe5304146b1cb888e87aa1f7e2f0c23590ca124fec58acc3e"},{"path":"outputs/budongi_mvp_temp/docs/statistics-validation-20261013.md","sha256":"48fd3e4e132d72503d5354d057dec6aca27d31f8df4b040a148bf2732fef2fed"},{"path":"outputs/budongi_mvp_temp/docs/tasks/legal-rag-source-snapshot-20261021.md","sha256":"5666802c2965c53a62aacbe0a012fbebb0828f0d6402e34976c7e7fda5ee754b"}],"status":"ACTIVE","task_id":"TASK-DATA-CATALOG-001","title":"집담 수집 데이터와 활용 가이드","updated_at":"2026-10-22T04:52:32+00:00","verified_at":"2026-10-22T04:52:32+00:00","version":"2026-10-22"}
```

## 목적 및 적용 범위

수집·통합·통계·법률 원문의 데이터별 용도와 준비 상태를 안내한다.

## 증상 또는 사용 상황

MOLIT 원본, KB 제공 통계, canonical 통합, 별도 법률 검색 후보 및 추천 serving 데이터가 보존되어 있다.

## 원인과 미확인 사항

각 데이터군은 권리·단위·검수·관계 연결 상태가 서로 다르다.

## 실행 절차

data-catalog.md의 항목별 현재 상태, 활용 방법, 제한과 연결 validation 자료를 확인한다.

## 주의사항 및 예외

source_unverified 및 pending_review 데이터를 확정 추천 근거로 사용하지 않는다. 미확정 단지·거래 상태·문서 권리를 추정하지 않는다.

## 검증 방법 및 결과

근거 문서를 대조하고 문서 diff whitespace 검사를 통과했다.

## 관련 원본

outputs/budongi_mvp_temp/docs/data-catalog.md 및 연결된 validation 기록
