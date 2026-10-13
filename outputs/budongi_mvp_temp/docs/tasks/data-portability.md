# TASK-PORTABLE-001 — Drive 공유와 DB 재구성

```toml
kind = "task"
id = "TASK-PORTABLE-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/15_data_portability_spec.md", "docs/specs/data_collection_record_spec.md"]
scope = ["scripts/shared_data.py", "scripts/join_shared_parts.py", "tests/test_shared_data.py", "outputs/budongi_mvp_temp/docs/specs/15_data_portability_spec.md", "outputs/budongi_mvp_temp/docs/tasks/data-portability.md", "outputs/budongi_mvp_temp/docs/shared-data.md", "outputs/budongi_mvp_temp/docs/shared-data-validation-20261013.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/README.md", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", "docs/data-collection.md", "docs/sdd/traceability.json"]
acs = ["PORTABLE-001-AC-01", "PORTABLE-001-AC-02", "PORTABLE-001-AC-03", "PORTABLE-001-AC-04"]

[[verification]]
command = "최종 ZIP CRC/전체 파일 SHA, 분할 재조립 SHA, verify_environment 제품137/팀22/합성 CLI"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/shared-data-validation-20261013.md#package-integrity"
acs = ["PORTABLE-001-AC-01"]

[[verification]]
command = "통계 및 최종 MOLIT 패키지 독립 rebuild, 전체 논리 테이블 digest/무결성/FK 대사"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/shared-data-validation-20261013.md#actual-rebuild"
acs = ["PORTABLE-001-AC-02"]

[[verification]]
command = "Issue5/6 업로드 전 결과 기록 및 후속 개별 링크, Drive7개 파일 부모/크기/다운로드 SHA 확인"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/shared-data-validation-20261013.md#remote-state"
acs = ["PORTABLE-001-AC-03"]
```

- [x] PORTABLE-001-AC-01 원본/manifest/ZIP 해시
- [x] PORTABLE-001-AC-02 실제 새 폴더 재구성/논리 대사
- [x] PORTABLE-001-AC-03 Issue 기록/Drive 업로드/원격 확인
- [ ] PORTABLE-001-AC-04 새 원격 브랜치 코드/데이터 제외

## 승인과 현재 결과

사용자의 현재 요청과 구체적 GitHub 게시/ZIP·Drive 목적지 후속 명시 승인에 따라 작업했다. 두 실제 재구성·검증·Drive 공유/읽기 SHA 대사 완료. 원격 main/codex/data-collection-records 확인 후 codex/data-portability-20261013 생성, 최신 origin/main 병합 완료. 원본/DB/ZIP/키를 제외하고 코드 푸시와 원격 커밋 확인을 마무리한다.
