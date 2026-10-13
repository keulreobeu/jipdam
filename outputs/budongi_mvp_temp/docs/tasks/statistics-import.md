# TASK-STATS-001 — 제공 통계 파일 별도 DB 수입

```toml
kind = "task"
id = "TASK-STATS-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/14_statistics_storage_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/statistics_storage.py", "outputs/budongi_mvp_temp/src/budongi/statistics_audit.py", "outputs/budongi_mvp_temp/src/budongi/statistics_cli.py", "outputs/budongi_mvp_temp/src/budongi/statistics_sources.json", "outputs/budongi_mvp_temp/src/budongi/cli.py", "outputs/budongi_mvp_temp/tests/test_statistics_storage.py", "outputs/budongi_mvp_temp/docs/specs/14_statistics_storage_spec.md", "outputs/budongi_mvp_temp/docs/plans/statistics-import-20261013.md", "outputs/budongi_mvp_temp/docs/adr/ADR-007-separate-statistics-store.md", "outputs/budongi_mvp_temp/docs/tasks/statistics-import.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/statistics-storage.md", "outputs/budongi_mvp_temp/docs/statistics-validation-20261013.md", "outputs/budongi_mvp_temp/README.md", "outputs/budongi_mvp_temp/.gitignore", "outputs/budongi_mvp_temp/pyproject.toml", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", "docs/sdd/traceability.json"]
acs = ["STATS-001-AC-01", "STATS-001-AC-02", "STATS-001-AC-03", "STATS-001-AC-04", "STATS-001-AC-05"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_statistics_storage.py -v"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/statistics-validation-20261013.md#contract-verification"
acs = ["STATS-001-AC-01", "STATS-001-AC-02", "STATS-001-AC-03", "STATS-001-AC-04", "STATS-001-AC-05"]

[[verification]]
command = "30개 원본 SHA-256/모든 날짜셀 XML 대사, DB 무결성, 동일 배치 재실행 SHA 확인"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/statistics-validation-20261013.md#actual-import-audit"
acs = ["STATS-001-AC-01", "STATS-001-AC-02", "STATS-001-AC-03", "STATS-001-AC-04"]

[[verification]]
command = "서울 심리 4쌍 2504셀 반올림 비교, 파일 기준 우선 지시에 따른 기준 검수 4건, 문서/SDD 검사"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/statistics-validation-20261013.md#metadata-distinction"
acs = ["STATS-001-AC-03", "STATS-001-AC-05"]
```

## 실행 범위

사용자가 이미 수집해 제공한 30개 파일만 오프라인으로 보존·적재한다. 새 외부 수집·업로드는 이번 작업 범위 밖이다.

## Acceptance Criteria

- [x] STATS-001-AC-01 원본/셀 계보·전체 건수 대사
- [x] STATS-001-AC-02 기간/지역/단위/결측/구조 검사
- [x] STATS-001-AC-03 재실행·개정·source_view 보존
- [x] STATS-001-AC-04 실제 30개 파일과 DB 격리
- [x] STATS-001-AC-05 CLI/manifest/사용자 메타데이터 후속

## Validation

통계 전용 8개 검사 및 실제 30개 원본/530,556셀 대사 통과. 동일 배치 재실행 신규 0, DB SHA 동일. 심리 요약 중복 4쌍 2,504셀 반올림 일치. 기준·중복 검수 이력 총 12건. 실제 결과는 위 검증 기록에 있다.

전체 verify_environment 실행은 기존 수집 경로의 Windows 디렉터리 rename 접근 오류로 실패했다. 재실행에서도 다른 기존 수집 테스트에서 같은 오류가 발생했으며 통계 검사 8개는 모두 통과했다. 이 Task의 검증 완료는 통계 범위에 한정하고 프로젝트 전체 검증 통과를 주장하지 않는다.
