# TASK-RENT-CANDIDATE-EXPORT-001 — 미확정 전월세 후보 검토표 내보내기

```toml
kind = "task"
id = "TASK-RENT-CANDIDATE-EXPORT-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/rental_candidate_export.py", "outputs/budongi_mvp_temp/src/budongi/cli.py", "outputs/budongi_mvp_temp/tests/test_rental_candidate_export.py", "outputs/budongi_mvp_temp/docs/tasks/rental-candidate-review-export.md", "outputs/budongi_mvp_temp/docs/tasks/continuation-parts-1to5.md", "outputs/budongi_mvp_temp/docs/tasks/rental-real-data.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/rental-review-package.md", "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-07"]

[[verification]]
command = "python -X utf8 -m unittest discover -s tests -p test_rental_candidate_export.py -v"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md#2026-10-15-review-only-candidate-export"
acs = ["RENT-001-AC-07"]

[[verification]]
command = "python -X utf8 -m budongi.cli export-rental-review-candidates --canonical-db data/collection/molit-seoul-three-api-20261012-restored-20261013/canonical-v3-20261013/canonical.sqlite3 --output-dir .local_runtime/rental-candidate-review-20261015"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md#2026-10-15-review-only-candidate-export"
acs = ["RENT-001-AC-07"]
```

## 목표와 경계

기존 canonical에서 전월세(`jeonse`, `wolse`) pending/unverified 후보 관계만 읽어 오프라인 사람 검토용 CSV를 만든다. 등록된 공식 단지 식별자, 관측 식별자, 배치·출처 계보, 원래 라벨과 후보 다중성은 검토 문맥으로 보존한다.

이 도구는 어떤 관계도 확인·거절하지 않는다. 출력은 추천 serving이나 `rental_review_v1` importer에 입력할 수 없다. 거래 금액·정규화 원문 payload·raw 파일은 내보내지 않으며 canonical을 SQLite read-only로 연다. 출력은 사용자가 명시한 새 `.local_runtime/` 하위 폴더에만 허용한다. 기존 폴더를 덮어쓰지 않는다.

프로젝트 디렉터리에서 `python -m budongi.cli export-rental-review-candidates --canonical-db <canonical.sqlite3> --output-dir .local_runtime/<new-folder>`를 실행한다. 결과는 `candidate_pairs.csv`, `candidate_groups.csv`, `README.txt` 세 파일이다. 출력에 `manifest.json`/`records.json`을 만들지 않으며 엑셀 수식으로 해석될 수 있는 셀 접두를 무력화한다.

## 완료 기준

- [x] 필수 `--canonical-db`, `.local_runtime/` 하위의 새 `--output-dir`만 허용하고 canonical DB의 해시가 실행 전후 같다.
- [x] 전월세 pending/unverified 후보 관계를 관측-후보 단지 쌍으로 내보내며 매매와 확정 관계는 제외한다. supporting observation, batch, 날짜, 지역·동·지번·단지 라벨 및 공식 단지 ID 계보를 포함한다.
- [x] 별도 그룹 CSV에서 같은 라벨에 복수 후보 단지가 있는 모호성을 표시하고, 모든 행은 검토 전 상태로 남는다.
- [x] 요약은 출력이 검수 승인·import 패키지가 아님을 밝히며 manifest/records JSON 등 importer 입력물을 만들지 않는다. 수식 주입을 안전하게 처리하고 기존 출력 디렉터리를 보존한다.
- [x] 합성 SQLite 회귀검사에서 매매 제외, 중복 배치 쌍 집계, ambiguity, read-only, formula safety와 출력 보호를 확인한다.

## 검증 상태

이 작업을 수행해도 실제 사람 검수는 발생하지 않는다. 사용자가 직접 라벨 기반 후보를 판정해 승인 근거를 준비하고, 별도 보류 해제와 검수 패키지가 생기기 전까지 `TASK-RENT-REAL-001` 및 추천의 `data_not_ready`를 그대로 유지한다.

검증 결과: 전용 회귀 3개 통과. 실제 canonical export는 candidate pair 203,108행·group 9,080행·모호 라벨 그룹 2개를 기록했다. 원본 SHA-256은 export 전후 `04f7e4da5e52884878c957757699c4e1cd44213839a0df2fc9273e911e46b20f`로 기존 계보 기록과 일치한다. 실제 파일별 크기와 SHA는 사용자 로컬의 ignored `.local_runtime/rental-candidate-review-20261015/README.txt`에 있다. 원본 거래 payload/금액은 출력하지 않았다.

코드·검토표 생성 경로는 검증됐지만 RENT-001-AC-07의 실제 사람 검수는 아직 수행되지 않았다. 이 Task는 전체 AC 완료로 표시하지 않으며, 사용자가 검토하고 승인 근거가 생길 때까지 `in_progress`를 유지한다.
