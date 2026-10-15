# TASK-PORTABLE-DOWNLOAD-001 — Drive 원본 패키지 요청 시 다운로드

```toml
kind = "task"
id = "TASK-PORTABLE-DOWNLOAD-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/15_data_portability_spec.md"]
scope = ["scripts/download_shared_data.py", "outputs/budongi_mvp_temp/docs/specs/15_data_portability_spec.md", "outputs/budongi_mvp_temp/docs/tasks/data-portability-download.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/shared-data.md", "outputs/budongi_mvp_temp/docs/shared-data-download-validation-20261014.md", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json"]
acs = ["PORTABLE-001-AC-05"]

[[verification]]
command = "Drive에서 통계/MOLIT 각 패키지를 다운로드하고 파일별·전체 SHA-256, 재실행 시 기존 출력 보존을 확인"
result = "not_run"
evidence = "outputs/budongi_mvp_temp/docs/shared-data-download-validation-20261014.md"
acs = ["PORTABLE-001-AC-05"]

[[verification]]
command = "Actual statistics/MOLIT download, each file and assembled ZIP SHA-256/size, CRC, repeat existing-output rejection and unchanged digests; 4 synthetic download tests"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md"
acs = ["PORTABLE-001-AC-05"]
```

- [x] PORTABLE-001-AC-05 요청한 패키지만 내려받고 파일별 해시, MOLIT 전체 ZIP 해시 및 기존 출력 보존 확인

## 구현 상태

루트의 `scripts/download_shared_data.py`가 승인된 두 Drive 패키지와 파일 ID/크기/SHA-256을 고정해 사용한다. MOLIT은 검증된 조각을 내려받고 전체 ZIP을 재조립한 뒤에만 결과 폴더를 게시한다. 다운로드 네트워크는 재구성 스크립트와 별도이며, 다운로드 후 `shared_data.py verify/rebuild`는 오프라인으로 동작한다.

초기 sandbox DNS 오류와 Drive 확인 폼 uuid 누락을 구분해 기록하고 수정했다. 실제 두 패키지 다운로드·조각/전체 SHA·크기·CRC·기존 출력 보호를 확인해 verified로 갱신했다. [후속 검증](../continuation-validation-20261014.md)을 따른다. 실제 다운로드와 기존 오프라인 재구성 검증은 구분한다.
