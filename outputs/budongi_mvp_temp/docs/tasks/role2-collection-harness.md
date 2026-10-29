# TASK-ROLE2-HARNESS-001 — 2번 수집 런타임·패키저·워크북 구현

```toml
kind = "task"
id = "TASK-ROLE2-HARNESS-001"
status = "in_progress"
owner = "cannedJean"
specs = ["outputs/budongi_mvp_temp/docs/specs/27_role2_collection_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/team_collection/", "outputs/budongi_mvp_temp/tests/team_collection_tests/", "outputs/budongi_mvp_temp/pyproject.toml", "tooling/role2_harness/", "tests/test_role2_harness.py", "tests/test_role2_ledger.py", "tests/test_role2_merge_plan.py", "outputs/budongi_mvp_temp/docs/specs/27_role2_collection_spec.md", "outputs/budongi_mvp_temp/docs/adr/ADR-025-role2-collection-harness.md", "outputs/budongi_mvp_temp/docs/plans/role2-collection.md", "outputs/budongi_mvp_temp/docs/tasks/role2-collection-harness.md", "outputs/budongi_mvp_temp/docs/tasks/role2-collection-run.md", "outputs/budongi_mvp_temp/docs/role2-collection-validation-20261029.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["ROLE2-COLLECT-001-AC-01", "ROLE2-COLLECT-001-AC-02", "ROLE2-COLLECT-001-AC-03", "ROLE2-COLLECT-001-AC-04", "ROLE2-COLLECT-001-AC-05", "ROLE2-COLLECT-001-AC-06"]
```

## 목표·범위·제외 범위

새 기능. [ROLE2-COLLECT-001](../specs/27_role2_collection_spec.md)의 수집 런타임·정규화·패키저·프로파일러·워크북 작성기와 다중 LLM 빌드 도구(`tooling/role2_harness/`)를 구현한다. 근거: 2026-10-29 사용자 요청·계획 승인, [ADR-025](../adr/ADR-025-role2-collection-harness.md), [Plan](../plans/role2-collection.md).

제외: 실제 수집 실행 기록(→ [TASK-ROLE2-COLLECT-001](role2-collection-run.md)), 좌표 변환·매칭·DB 적재, 기존 MOLIT 수집기와 managed harness 변경.

## 완료 기준

- [ ] ROLE2-COLLECT-001-AC-01 미등록·미승인·record_url 없음·HTTP 미확인 요청 거부
- [ ] ROLE2-COLLECT-001-AC-02 저널 재개·쿼터 이월·상태 구분
- [ ] ROLE2-COLLECT-001-AC-03 키 비노출·반사 차단·비밀 스윕
- [ ] ROLE2-COLLECT-001-AC-04 record_type별 정규화·좌표·시각·재실행 결정성
- [ ] ROLE2-COLLECT-001-AC-05 패키지 게이트·거부 사례·결정적 ZIP
- [ ] ROLE2-COLLECT-001-AC-06 워크북 헤더·수식·캐시값·레이아웃 일치

## 결과·남은 조건

진행 중. 실행 결과는 [검증 기록](../role2-collection-validation-20261029.md)에 남긴다.
