# TASK-TEAM-REF-001 — 팀 제공 reference 데이터 수입

```toml
kind = "task"
id = "TASK-TEAM-REF-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/22_team_reference_import_spec.md"]
scope = ["outputs/budongi_mvp_temp/scripts/import_team_reference_packages.py", "outputs/budongi_mvp_temp/docs/specs/22_team_reference_import_spec.md", "outputs/budongi_mvp_temp/docs/tasks/team-reference-import-20261020.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/team-reference-import-validation-20261020.md", "docs/sdd/traceability.json"]
acs = ["TEAM-REF-001-AC-01", "TEAM-REF-001-AC-02", "TEAM-REF-001-AC-03", "TEAM-REF-001-AC-04"]

[[verification]]
command = "python -X utf8 outputs/budongi_mvp_temp/scripts/import_team_reference_packages.py --package-root outputs/budongi_mvp_temp/data/collection/team_import_20261020 --database outputs/budongi_mvp_temp/data/collection/team_import_20261020/team_reference.sqlite3"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/team-reference-import-validation-20261020.md#result"
acs = ["TEAM-REF-001-AC-01", "TEAM-REF-001-AC-02", "TEAM-REF-001-AC-03"]

[[verification]]
command = "Read-only SQLite source/batch/status counts, PRAGMA integrity_check, and PRAGMA foreign_key_check"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/team-reference-import-validation-20261020.md#commands"
acs = ["TEAM-REF-001-AC-03", "TEAM-REF-001-AC-04"]
```

2026-10-20: 사용자가 요청한 네 ZIP을 Drive에서 받아 GitHub Issue 해시와 대조했다. 패키지의 받은 원본과 manifest가 검증된 뒤 별도 reference DB를 만들었다. ZIP과 SQLite 산출물은 ignored `outputs/budongi_mvp_temp/data/collection/team_import_20261020/`에 둔다.

- [x] TEAM-REF-001-AC-01 Drive ZIP SHA-256이 #9/#13/#14/#15 값과 각각 일치; ZIP CRC, manifest 및 모든 파일 SHA/bytes 검증 통과.
- [x] TEAM-REF-001-AC-02 `source_unverified` normalized JSONL 157,602 accepted행 적재: HUG 828, 학원 138,523, 도서관 3,597, 어린이보호구역 14,654. 학원 rejected 1행도 DB에 `rejected` 상태로 보존했다.
- [x] TEAM-REF-001-AC-03 SQLite integrity/FK 검사 및 출처·배치별 SQL count 대사 통과.
- [x] TEAM-REF-001-AC-04 전월세 canonical/serving DB는 건드리지 않았다. 이 데이터는 미검수 별도 reference DB이며 추천·좌표 활용을 하지 않는다.

검증 명령: `python -X utf8 outputs/budongi_mvp_temp/scripts/import_team_reference_packages.py --package-root outputs/budongi_mvp_temp/data/collection/team_import_20261020 --database outputs/budongi_mvp_temp/data/collection/team_import_20261020/team_reference.sqlite3`

Drive SHA-256: HUG `9ebf178b…c0dcda`, 학원 `8da8dd9a…f2eda`, 도서관 `1e15a13c…46dbb`, 어린이보호구역 `38651cf6…985a63`. 네 Issue의 manifest/라이선스 확인 기록과 ZIP을 보존했다. 행 단위 원천 품질은 여전히 미검수이며, 시설 좌표계와 기관별 기준일은 미확인이다.
