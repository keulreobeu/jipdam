# TASK-AUDIT-GMS-001 — 상태 재검증과 개인 키별 GMS 관리

```toml
kind = "task"
id = "TASK-AUDIT-GMS-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/gms_budget.py", "outputs/budongi_mvp_temp/src/budongi/gms_accounts.py", "outputs/budongi_mvp_temp/src/budongi/credential_server.py", "outputs/budongi_mvp_temp/src/budongi/static/credentials.js", "outputs/budongi_mvp_temp/src/budongi/static/credentials.html", "outputs/budongi_mvp_temp/src/budongi/rental_readiness.py", "outputs/budongi_mvp_temp/tests/test_gms_budget.py", "outputs/budongi_mvp_temp/tests/test_rental_readiness.py", "outputs/budongi_mvp_temp/docs/specs/00_project_spec.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md", "outputs/budongi_mvp_temp/docs/tasks/rental-real-data.md", "outputs/budongi_mvp_temp/docs/tasks/rental-mvp.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/tasks/audit-personal-gms-20261021.md", "outputs/budongi_mvp_temp/docs/adr/ADR-023-personal-gms-ledger.md", "outputs/budongi_mvp_temp/docs/audit-personal-gms-validation-20261021.md", "outputs/budongi_mvp_temp/README.md", "outputs/budongi_mvp_temp/AGENTS.md", "AGENTS.md", "README.md", "docs/sdd/traceability.json"]
acs = ["GMS-BUDGET-001-AC-06", "RENT-001-AC-11"]

[[verification]]
command = "workspace TEMP/TMP: GMS budget44 + GMS12 + readiness8 + team27 unittest; node --check credentials.js; check_sdd.py --base origin/main; git diff --check; synthetic IAB A-B-A; real serving read-only audit"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/audit-personal-gms-validation-20261021.md"
acs = ["GMS-BUDGET-001-AC-06", "RENT-001-AC-11"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "failed"
evidence = "outputs/budongi_mvp_temp/docs/audit-personal-gms-validation-20261021.md"
acs = ["GMS-BUDGET-001-AC-06", "RENT-001-AC-11"]
```

Jira: [KAN-6](https://kwulreobeu.atlassian.net/browse/KAN-6).
승인: 2026-10-21 현재 사용자 요청. 문서 불일치·SDD 결과 형식·readiness 회귀를 검증하고 개인 할당 GMS 키별 정책/예약/자동 호출 내역을 구현한다.

- [ ] GMS-BUDGET-001-AC-06 키별 독립 정책·사용·보류·자동 정산, 재시작/동일 키 중복 등록/교체/이전 원장 보존, 비밀 비노출을 검증한다. 집중 검증 통과, 전체 검사 완료 대기.
- [ ] RENT-001-AC-11 기준 DB/날짜별 상태를 맞추고 SDD와 readiness 회귀·실제 읽기 전용 검증 증거를 남긴다. 문서/serving 재검증 통과, 원본 접근·전체 검사 대기.

전체 환경292개 중 수집 DB 임시 폴더 rename WinError5 1건으로 공식 검증은 failed다. canonical 원본 접근과 현재 실키 확인도 미완료이므로 Jira/Task는 진행 중을 유지한다. 기능별 검증을 제품/실키 전체 완료로 표시하지 않는다.

기존 사용자 변경은 유지한다. 새 수집·매칭·추천 차단 해제·키 자동 선택·push/merge는 포함하지 않는다.

## 2026-10-28 재검증 및 복원 진행 (KAN-6)

현재 PC에서 `check_sdd.py --base origin/main`은 통과했고, 프로젝트 내부 임시 디렉터리와 로컬 소켓 접근을 허용한 환경에서 `verify_environment.py`는 제품 323개·팀/SDD 35개와 합성 CLI smoke를 통과했다. 별도 readiness 8개와 GMS 예산 45개도 통과했다. 제한된 샌드박스에서는 로컬 소켓 WinError 10013으로 전체 검사가 실패했으며 이를 제품 오류나 통과로 기록하지 않는다.

사용자 확인: 기존 GMS 키가 만료돼 현재 사용할 키가 없다. 새 키의 선택·정책·잔액·만료 검증은 미실행이며 키/원장을 추측하거나 초기화하지 않는다. 현재 PC의 기존 검수 serving과 canonical 검수 원본은 해당 경로에 없다. Drive의 2026-10-13 국토부와 제공 통계 패키지는 기존 기록의 SHA-256 및 내부 manifest를 검증했다. 통계는 별도 로컬 경로에 오프라인 재구성해 30개 파일·530,556 관측의 논리 대사 결과 `verified`를 확인했다. 국토부 재구성 및 2026-10-20 검수 패키지·serving의 복구와 계보 재검증은 아직 진행/미확인이다. 당시 203,159 관계 수는 이 PC의 최신 실측이 아니라 2026-10-21의 보존된 검증 이력이다.

국토부 재구성 후속 결과: 네트워크를 차단한 패키지 `shared_data.py rebuild`가 `verified`로 종료했다. 원본과 전 논리 테이블 digest를 비교하고 SQLite 무결성·외래키를 검사했다. 재구성 canonical의 관측은 374,892건, 원본 행 384,211건, 미확정 후보 271,299건이고 전월세 관측 238,620건의 연결은 0건이다. 이는 10월 13일 이전 상태를 복원한 것으로 10월 20일 검수 serving의 203,159건과 다른 스냅샷이다. 로컬 산출물: `.local_runtime/kan6-restore/molit-rebuilt/` 및 `statistics-rebuilt/`의 `rebuild-verification.json`. 10월 20일 승인 검수 패키지와 serving은 여전히 미확보이며 사용자는 백업 위치를 모른다고 확인했다. 기존 완료 기준과 이슈 상태는 유지한다.
