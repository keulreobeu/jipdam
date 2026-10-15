# TASK-RENT-CONTINUE-001 — 1~5번 목적별 후속 준비와 검증

```toml
kind = "task"
id = "TASK-RENT-CONTINUE-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/15_data_portability_spec.md"]
scope = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/src/budongi/canonical_rental.py", "outputs/budongi_mvp_temp/src/budongi/rental_readiness.py", "outputs/budongi_mvp_temp/src/budongi/cli.py", "outputs/budongi_mvp_temp/tests/test_rental_readiness.py", "outputs/budongi_mvp_temp/tests/test_canonical_rental.py", "scripts/download_shared_data.py", "tests/test_download_shared_data.py", "outputs/budongi_mvp_temp/docs/tasks/continuation-parts-1to5.md", "outputs/budongi_mvp_temp/docs/plans/continuation-parts-1to5.md", "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/tasks/rental-web-demo.md", "outputs/budongi_mvp_temp/docs/tasks/rental-data-contract.md", "outputs/budongi_mvp_temp/docs/tasks/rental-real-data.md", "outputs/budongi_mvp_temp/docs/tasks/data-portability-download.md", "outputs/budongi_mvp_temp/docs/shared-data-download-validation-20261014.md", "outputs/budongi_mvp_temp/docs/rental-review-package.md", "outputs/budongi_mvp_temp/README.md", "README.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-15", "PORTABLE-001-AC-05"]

[[verification]]
command = "Actual default canonical-v3 prepare-rentals, read-only rental-readiness and statistics/MOLIT download/hash/CRC/existing-output audit"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md"
acs = ["RENT-001-AC-13", "PORTABLE-001-AC-05"]
```

## 목적과 범위

[Plan](../plans/continuation-parts-1to5.md)의 다섯 목적에 따라 기본 경로를 복구하고 검수/모델/성능 검증 준비와 실제 다운로드 확인, 문서·Git 정리를 수행한다. 사용자 미준비 답변을 준비 게이트로 유지하며 실제 매칭·좌표·시설을 생성하지 않는다.

## 완료 기준

- [x] RENT-001-AC-13 기본 canonical v3의 실제 prepare와 read-only 계보·미준비 상태 확인.
- [ ] RENT-001-AC-12 지정 모델/입력 준비 검사와 실행 절차; 실모델 검증은 미준비로 구분.
- [ ] RENT-001-AC-15 실제 후보가 있는 추천·상세 벤치마크 실행 절차와 데이터 준비 게이트.
- [x] PORTABLE-001-AC-05 통계/MOLIT 다운로드·전체 해시·기존 출력 보호 검증.

## 검증·남은 조건

[후속 검증](../continuation-validation-20261014.md)에 실제 명령과 결과를 기록한다. 준비 기능의 완료를 TASK-RENT-MVP-001 실제 모델/추천 품질 AC 완료로 표시하지 않는다.
