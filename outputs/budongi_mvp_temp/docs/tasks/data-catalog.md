# TASK-DATA-CATALOG-001 — 수집 데이터와 활용 가이드

```toml
kind = "task"
id = "TASK-DATA-CATALOG-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/26_data_catalog_spec.md", "outputs/budongi_mvp_temp/docs/specs/12_molit_collection_spec.md", "outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md", "outputs/budongi_mvp_temp/docs/specs/14_statistics_storage_spec.md", "outputs/budongi_mvp_temp/docs/specs/24_legal_rag_corpus_spec.md"]
scope = ["outputs/budongi_mvp_temp/docs/data-catalog.md", "outputs/budongi_mvp_temp/docs/specs/26_data_catalog_spec.md", "outputs/budongi_mvp_temp/docs/tasks/data-catalog.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["DATA-CATALOG-001-AC-01", "DATA-CATALOG-001-AC-02", "DATA-CATALOG-001-AC-03"]

[[verification]]
command = "MOLIT/Canonical/Statistics/Legal RAG 원천·현황·기준일을 기존 승인 Spec 및 validation 기록과 대조"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/data-catalog.md"
acs = ["DATA-CATALOG-001-AC-01", "DATA-CATALOG-001-AC-02", "DATA-CATALOG-001-AC-03"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py 및 대상 문서 git diff --check"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/data-catalog.md"
acs = ["DATA-CATALOG-001-AC-01", "DATA-CATALOG-001-AC-02", "DATA-CATALOG-001-AC-03"]
```

## 목표·범위·제외 범위

실제로 보존된 원천·통계·통합 산출물을 그룹별로 요약하고 각 데이터의 현재 상태, 활용 방법과 사용 전 제한을 안내한다. 수집 승인·검증 기록·현재 제품 serving 상태를 서로 구분한다. 데이터 원본 수정, 새 수집, 추천 연결, 외부 게시/업로드는 범위에 포함하지 않는다.

## 완료 기준

- [x] DATA-CATALOG-001-AC-01 승인·보존된 데이터군, 범위, 수량, 상태를 근거 문서와 대조한다.
- [x] DATA-CATALOG-001-AC-02 데이터 항목마다 활용 예와 상태에 따른 제한을 표시한다.
- [x] DATA-CATALOG-001-AC-03 기준일과 확인용 수집·canonical·통계·RAG·추천 문서 링크를 제공한다.

## 위키 판단 및 결과

- Jira: KAN-20.
- 판단: CREATE (`verified_reusable_knowledge`). 활성 로컬 카탈로그와 지정 Confluence에서 데이터 카탈로그 중복 페이지를 찾지 못해 신규 등록했다.
- 위키 문서: `WIKI-E162D573DBB6F1CD`, [집담 수집 데이터와 활용 가이드](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/589825/WIKI-E162D573DBB6F1CD).
- 검증: Confluence에 표 본문을 게시하고 read-back 버전 `1`, remote hash `b40fc1e646299088546f0623c01404bea7765a4cb33456a31c8c2db1a9166a27`을 receipt로 기록했다. Jira 결과 댓글은 `10077`이며 두 outbox 전달 상태는 DONE이다. `python -X utf8 scripts/check_sdd.py`는 features 22, AC 109, tasks 44 검사에서 통과했다.
- 문서 근거 대조 및 변경 파일 `git diff --check` 통과. 제품 테스트는 추가하거나 실행하지 않았다.
