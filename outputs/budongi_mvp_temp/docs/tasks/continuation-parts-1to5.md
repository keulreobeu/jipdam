# TASK-RENT-CONTINUE-001 — 1~5번 목적별 후속 준비와 검증

```toml
kind = "task"
id = "TASK-RENT-CONTINUE-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/15_data_portability_spec.md"]
scope = [".gitignore", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/src/budongi/canonical_rental.py", "outputs/budongi_mvp_temp/src/budongi/rental_readiness.py", "outputs/budongi_mvp_temp/src/budongi/cli.py", "outputs/budongi_mvp_temp/src/budongi/rental_candidate_export.py", "outputs/budongi_mvp_temp/tests/test_rental_readiness.py", "outputs/budongi_mvp_temp/tests/test_canonical_rental.py", "outputs/budongi_mvp_temp/tests/test_rental_candidate_export.py", "scripts/download_shared_data.py", "tests/test_download_shared_data.py", "outputs/budongi_mvp_temp/docs/tasks/continuation-parts-1to5.md", "outputs/budongi_mvp_temp/docs/tasks/rental-candidate-review-export.md", "outputs/budongi_mvp_temp/docs/plans/continuation-parts-1to5.md", "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/tasks/rental-web-demo.md", "outputs/budongi_mvp_temp/docs/tasks/rental-data-contract.md", "outputs/budongi_mvp_temp/docs/tasks/rental-real-data.md", "outputs/budongi_mvp_temp/docs/tasks/data-portability-download.md", "outputs/budongi_mvp_temp/docs/shared-data-download-validation-20261014.md", "outputs/budongi_mvp_temp/docs/rental-review-package.md", "outputs/budongi_mvp_temp/docs/harness/CLI_OPERATIONS.md", "outputs/budongi_mvp_temp/README.md", "README.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-07", "RENT-001-AC-08", "RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-15", "PORTABLE-001-AC-05"]

[[verification]]
command = "Actual default canonical-v3 prepare-rentals, read-only rental-readiness and statistics/MOLIT download/hash/CRC/existing-output audit"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md"
acs = ["RENT-001-AC-13", "PORTABLE-001-AC-05"]

[[verification]]
command = "Synthetic-only benchmark_rentals --create-synthetic --allow-synthetic --compare-indexes (5 warmups + 100 runs per path)"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md"
acs = ["RENT-001-AC-15"]

[[verification]]
command = "manual loopback UI check against an existing synthetic serving and the default actual serving database; synthetic results/zero-match/detail and actual data_not_ready"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md#actual-and-synthetic-browser-gates"
acs = ["RENT-001-AC-08"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py; python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md"
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-15", "PORTABLE-001-AC-05"]
```

## 목적과 범위

[Plan](../plans/continuation-parts-1to5.md)의 다섯 목적에 따라 기본 경로를 복구하고 검수/모델/성능 검증 준비와 실제 다운로드 확인, 문서·Git 정리를 수행한다. 사용자 미준비 답변을 준비 게이트로 유지하며 실제 매칭·좌표·시설을 생성하지 않는다.

## 완료 기준

- [x] RENT-001-AC-13 기본 canonical v3의 실제 prepare와 read-only 계보·미준비 상태 확인.
- [x] Part 2 / RENT-001-AC-12 준비 항목: 승인 패키지 readiness 검사와 실행 순서를 검증했다. 실제 검수 패키지와 로컬 모델은 사용자 결정대로 준비를 미뤄 실제 모델 검증은 대기 중.
- [x] Part 3 / RENT-001-AC-15 준비 항목: 실제 후보 벤치마크 명령·입력 gate를 확인하고 synthetic-only 5+100회 비교를 실행했다. 실제 추천 후보·모델 기반 결과는 대기 중.
- [x] PORTABLE-001-AC-05 통계/MOLIT 다운로드·전체 해시·기존 출력 보호 검증.
- [x] Part 5 준비·제출: 관련 웹/데이터 Task와 최신 MVP 검증 연결, 원본/bundle Git 제외, GMS 현재 예산 설명의 README 정합성, 전체 회귀·SDD·공백 검사 및 범위 한정 로컬 커밋을 확인했다.

## 검증·남은 조건

[후속 검증](../continuation-validation-20261014.md)에 실제 명령과 결과를 기록한다. 준비 기능의 완료를 TASK-RENT-MVP-001 실제 모델/추천 품질 AC 완료로 표시하지 않는다.

2026-10-15 추가: RENT-001-AC-08의 canonical HTTP API와 CLI 실행 경로가 같은 추천 서비스/결과를 사용하도록 `recommend-canonical`을 추가했고, 두 경로의 JSON 결과 및 source/serving DB 불변성을 synthetic serving fixture로 대조했다. 신규 회귀 2개와 canonical rental 22개, legacy rental 15개가 통과했다. 실제 브라우저 시나리오, 승인 검수 패키지와 로컬 모델 검증은 이 결과에 포함되지 않는다.

## Verification

2026-10-15 재구성: 기존 승인 Drive MOLIT 패키지를 지정 CLI로 내려받아 파일별 SHA-256/크기, 전체 ZIP SHA-256 `e9eeb0c1057e16f11066c42e704ffd38d88e93bc59dda797a3b250c7366cc013`, ZIP CRC를 확인했다. 패키지 manifest 검증 후 네트워크 차단 재구성에서 관측·정규화·canonical 논리 테이블이 모두 패키지 기대값과 일치했고 `rebuild-verification.json`은 verified다. 출력은 새 경로에 만들고 생성된 canonical 폴더를 기본 경로 `canonical-v3-20261013`에 정렬했다.

실제 기본 경로 `prepare-rentals`는 exit 0, source v3/serving v2와 관측 238,620건을 반환했다. canonical 원본 SHA-256은 prepare 전후 `04f7e4da5e52884878c957757699c4e1cd44213839a0df2fc9273e911e46b20f`로 동일하다. Readiness는 기대한 exit 2 / `needs_input`: Part 1 ready, Part 2 승인 검수 패키지 없음, Part 3 확정 관계/좌표/시설/커버리지와 실제 후보 없음, 추천용 로컬 모델은 사용자 요청에 따라 준비하지 않았다. `data_not_ready`, 확정 관계 0을 유지한다.

Part 3 synthetic-only 비교 benchmark는 각 경로 5회 warmup/100회 실행, 인덱스 on/off의 결과 signature 일치를 확인했다. 추천 p95 145.243/152.562 ms, 상세 p95 82.065/90.655 ms다. 실제 후보의 p95나 실모델 품질로 간주하지 않는다. 통계 다운로드는 선행 Task 증거로 유지하고, 이번 MOLIT 재다운로드 SHA/CRC도 통과했다.

Part 5에서 저장소 `.gitignore`에 로컬 제품 data 디렉터리와 기존 `jipdam-branches-pre-delete-20261015.bundle`의 정확한 경로를 추가해 raw/DB/ZIP과 사용자 bundle이 Git 변경 목록·스테이징에서 제외되도록 했다. bundle 자체는 변경하지 않는다. GMS 현재 고정 보존액은 0이며 이전 5,000/1,000 기록을 현재 지시로 취급하지 않는다. LUNA 문구 작업은 두 번 `output_limited`; 세 번째 generation은 ledger에서 settled/852 tokens로 확인했지만 command output text가 노출되지 않아 draft를 적용하지 않았다. 전체 hold 380 credits와 active_calls 0은 유지됐고 재시도하지 않았다.

후속 freshness check: `python -X utf8 -m budongi.cli rental-readiness`에서 `$LASTEXITCODE=2`, canonical v3 ready와 Part 2·3 needs_input, serving 238,620건/확정 연결 0/`data_not_ready`를 재확인했다. `benchmark_rentals.py --help`에는 실제 `--candidate`와 합성 인덱스 비교 인자가 표시된다. 해당 결과와 SDD/환경검증 기록은 [후속 검증](../continuation-validation-20261014.md)에 연결했다.

Part 5 Task-link audit: `TASK-RENT-WEB-001`은 최신 구현/브라우저 evidence를 `TASK-RENT-MVP-001`에 연결하고, `TASK-RENT-DATA-001`은 MOLIT·canonical 적재 완료와 MVP 검수 serving 계약 및 위치/시설 입력 미확보를 구분한다. `TASK-RENT-REAL-001`은 검수 패키지와 별도 수집·매칭 승인 전 보류를 유지하며, `TASK-PORTABLE-DOWNLOAD-001`은 두 승인 패키지 다운로드·해시/CRC/기존 출력 보호의 passed evidence를 연결한다. 이 연결은 Task 현황을 추적하기 위한 것이고 미완료 제품 AC를 완료로 승격하지 않는다.

2026-10-15: 모델·승인 검수 패키지 없이 진행 가능한 Part 2 준비로, 기존 canonical의 전월세 pending/unverified 후보를 사람이 검토할 수 있는 로컬 CSV 요약·상세 내보내기를 추가한다. 이는 확정 연결·추천 serving 입력·`rental_review_v1` 패키지가 아니며 `TASK-RENT-REAL-001`은 계속 blocked다.
