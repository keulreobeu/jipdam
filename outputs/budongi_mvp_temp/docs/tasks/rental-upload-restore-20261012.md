# TASK-RENT-RESTORE-001 — 첨부 전월세 DB 복원·수집 범위 점검

```toml
kind = "task"
id = "TASK-RENT-RESTORE-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["outputs/budongi_mvp_temp/.gitignore", "outputs/budongi_mvp_temp/data/rental/", "outputs/budongi_mvp_temp/docs/tasks/rental-upload-restore-20261012.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/rental-upload-audit-20261012.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-07"]

[[verification]]
command = "manual: Python sqlite3/zipfile/hashlib로 첨부·복원 DB 해시, integrity_check, foreign_key_check, 행 수, 합성 기본 거부와 명시 허용 추천을 검사"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/rental-upload-audit-20261012.md#validation"
acs = ["RENT-001-AC-07"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/rental-upload-audit-20261012.md#validation"
acs = ["RENT-001-AC-07"]
```

## 목표·승인 근거·범위

2026-10-12 사용자 요청: “저번주에 수집한 데이터인데 지금 이 환경 db에 적제해주고, 어디까지 수집했는지 확인”. 제공 ZIP의 기존 SQLite 스냅샷을 별도 rental 경로에 복원하고 실제 내용·계보·수집 범위를 확인한다. 새 API 수집·자동 단지 매칭·역사 DB 변경은 요청 범위에 포함하지 않는다.

첨부 DB는 `rental_v1`, `synthetic_only`, `fictional=true`인 기존 봉인 합성 스냅샷이다. 합성 품질 표시·스냅샷 ID·생성 시각·원본 DB 바이트를 유지한다. 실제 데이터 Task의 수집·매칭 보류와 제품 평가 미완료 상태는 유지한다. AC-07의 이번 검증 범위는 첨부 DB 복원 시 계보·합성 구분·역사 격리이며, 실제 원천 행까지의 검수 완료를 주장하지 않는다.

## 완료 기준

- [x] RENT-001-AC-07 ZIP·DB 해시와 내용을 보존해 분리 복원하고, 합성 표시·무결성·외래키·행 수·지역·기간·원천 파일 누락 및 추천 경로를 확인한다.

## 검증 기록

최종 실행 결과와 한계는 [첨부 점검 보고서](../rental-upload-audit-20261012.md)에 기록한다. 로컬 원본·DB·JSON은 `data/rental/`에서 Git에 포함하지 않는다.

## 남은 조건

ZIP에는 실제 수집 원본과 `synthetic-input.json`이 없다. 실제 전월세 수집 범위를 판단하려면 실제 API 응답·매니페스트 또는 실제 DB가 필요하다. 합성 매칭 3건은 실제 단지에 대한 사람 검수가 아니다.
