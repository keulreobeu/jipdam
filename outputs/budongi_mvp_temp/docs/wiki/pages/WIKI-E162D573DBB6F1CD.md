# 집담 수집 데이터와 활용 가이드

```json
{"approval_ref":null,"content_hash":"5c43c698a806e2dd3f72ffbe42b223326abd86cb314033f3cb1505999d6fd2fa","created_at":"2026-10-22T04:52:32+00:00","environment":"Windows / Python 3.12","id":"WIKI-E162D573DBB6F1CD","key":"DATA-CATALOG","kind":"guide","module":"data-catalog","owner":"Codex","project":"jipdam","publication_approved":false,"publication_approved_by":null,"replacement":null,"review_at":"2027-04-26T06:56:27+00:00","reviewer":"agent-codex","revision":2,"risk":"low","sources":[{"path":"outputs/budongi_mvp_temp/docs/data-catalog.md","sha256":"a9d5239a8dc58f3c3df92db47a60d6be9c68e179b5f3ed6a174ef02a0dd1f99b"},{"path":"outputs/budongi_mvp_temp/docs/molit-statistics-history-validation-20261015.md","sha256":"f843ba6ef36b412d7691cee2074bc166f7a3b78eb5a5b566363fe951cfeeb32a"},{"path":"outputs/budongi_mvp_temp/docs/canonical-validation-20261013.md","sha256":"093159306440c82fe5304146b1cb888e87aa1f7e2f0c23590ca124fec58acc3e"},{"path":"outputs/budongi_mvp_temp/docs/statistics-validation-20261013.md","sha256":"48fd3e4e132d72503d5354d057dec6aca27d31f8df4b040a148bf2732fef2fed"},{"path":"outputs/budongi_mvp_temp/docs/tasks/legal-rag-source-snapshot-20261021.md","sha256":"cf4d42ee98ddbcfd0a4de369c981e3a8526ec6b48d8023754836fc04421bc8bf"},{"path":"outputs/budongi_mvp_temp/docs/tasks/audit-personal-gms-20261021.md","sha256":"561a324fb8b69bd4f1f298f9a12ead96d9e277a48dd57ecb6cee148f284890c9"}],"status":"ACTIVE","task_id":"TASK-WIKI-RECOVERY-001","title":"집담 수집 데이터와 활용 가이드","updated_at":"2026-10-28T06:56:27+00:00","verified_at":"2026-10-28T06:56:27+00:00","version":"2026-10-22"}
```

## 목적 및 적용 범위

수집·통합·통계·법률 원문의 데이터별 용도와 준비 상태를 안내한다.

## 증상 또는 사용 상황

2026-10-22 기준 수집·검수 기록을 참조한다. 2026-10-28 이 PC에서 2026-10-13 MOLIT·통계 백업과 법률 원문 백업을 복원했으며, 2026-10-20 검수 serving과 검수 패키지는 이 PC에서 아직 확보하지 못했다.

## 원인과 미확인 사항

각 데이터군은 권리·단위·검수·관계 연결 상태가 서로 다르다.

## 실행 절차

data-catalog.md의 항목별 현재 상태, 활용 방법, 제한과 연결 validation 자료를 확인한다.

## 주의사항 및 예외

source_unverified 및 pending_review 데이터를 확정 추천 근거로 사용하지 않는다. 미확정 단지·거래 상태·문서 권리를 추정하지 않는다. 2026-10-20 승인 관계 수는 과거 검증 기록이며 현재 PC의 재측정이 아니다. 법령 원문은 보관 시점의 판본으로, 현재 효력은 별도 확인한다.

## 검증 방법 및 결과

2026-10-28 보관 패키지의 해시·복원 무결성 기록과 10월 22일 기준 카탈로그 및 validation을 대조했다. 실제 검수 serving·법률 효력·좌표·이용권의 최신 검증은 완료하지 않았다.

## 관련 원본

outputs/budongi_mvp_temp/docs/data-catalog.md 및 연결된 validation 기록
