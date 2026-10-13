# TASK-MOLIT-001 — 원시 XML 수집·오프라인 DB 구현

```toml
kind = "task"
id = "TASK-MOLIT-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/12_molit_collection_spec.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md", "docs/specs/data_collection_record_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/", "outputs/budongi_mvp_temp/tests/", "outputs/budongi_mvp_temp/docs/", "outputs/budongi_mvp_temp/README.md", "outputs/budongi_mvp_temp/.gitignore", "outputs/budongi_mvp_temp/pyproject.toml", "outputs/budongi_mvp_temp/AGENTS.md", "AGENTS.md", ".agents/skills/jipdam-workflow/SKILL.md", "docs/sdd/traceability.json", "docs/data-collection.md"]
acs = ["MOLIT-001-AC-01", "MOLIT-001-AC-02", "MOLIT-001-AC-03", "MOLIT-001-AC-04", "MOLIT-001-AC-05", "MOLIT-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/molit-validation-20261012.md#contract-tests"
acs = ["MOLIT-001-AC-01", "MOLIT-001-AC-02", "MOLIT-001-AC-03", "MOLIT-001-AC-04", "MOLIT-001-AC-05", "MOLIT-001-AC-06"]

[[verification]]
command = "collection fetch 및 네트워크/키 접근 차단하의 DB 재생성·SQL 대사·ZIP 복원 실제 검증"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/molit-validation-20261012.md#full-seoul-validation"
acs = ["MOLIT-001-AC-01", "MOLIT-001-AC-02", "MOLIT-001-AC-03", "MOLIT-001-AC-04", "MOLIT-001-AC-05"]

[[verification]]
command = "GitHub #5 본문/댓글 결과 기록 갱신"
result = "failed"
evidence = "outputs/budongi_mvp_temp/docs/molit-validation-20261012.md#github-record-limitation"
acs = ["MOLIT-001-AC-06"]

[[verification]]
command = "2026-10-13 검증된 원본 ZIP의 새 경로 복원·975query·세 DB 해시/행수/무결성 읽기 검사"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/molit-resume-validation-20261013.md#restored-archive-audit"
acs = ["MOLIT-001-AC-02", "MOLIT-001-AC-03", "MOLIT-001-AC-05"]

[[verification]]
command = "2026-10-13 GitHub #5 기존 본문/댓글 조회 후 연결앱 본문 결과 기록 갱신"
result = "failed"
evidence = "outputs/budongi_mvp_temp/docs/molit-resume-validation-20261013.md#github-result-record"
acs = ["MOLIT-001-AC-06"]

[[verification]]
command = "2026-10-13 사용자 승인된 로그인 GitHub CLI로 Issue #5 결과 본문 게시 후 로컬 기록문 전체 일치 확인"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/molit-resume-validation-20261013.md#github-cli-publication"
acs = ["MOLIT-001-AC-06"]
```

## 승인·범위

사용자가 2026-10-12 PLAN-MOLIT-001 전체 구현을 요청했다. 세 서비스 원본 수집/파싱의 보류만 해제하며 실제 단지 매칭·시설·추천/Golden은 계속 별도 작업이다. 환경 구성 Task의 미커밋 변경은 보존한다. GitHub 수집 Issue는 승인된 COLLECT-001 절차로 예약/결과를 작성하며 ZIP 업로드는 수동이다.

## 완료 기준

- [x] MOLIT-001-AC-01 키·호출·기존 회귀.
- [x] MOLIT-001-AC-02 원본·실패·재개.
- [x] MOLIT-001-AC-03 재사용·무결성.
- [x] MOLIT-001-AC-04 정규화·원문·식별.
- [x] MOLIT-001-AC-05 오프라인 두 DB·불변.
- [x] MOLIT-001-AC-06 CLI·요약·ZIP 검증과 필수 GitHub #5 결과 기록 게시·전체 본문 대조 통과.

## Validation

실제 세 API 서울975 query 원본384,211행 수집, 유효374,892행 적재·기간 제외9,319행의 staging 추적·거부0을 검증했다. 원본 조인/무결성·무호출 재실행·오프라인 재생성·ZIP 복원975 query 검증은 [증거](../molit-validation-20261012.md#full-seoul-validation)를 따른다. 2026-10-13 사용자 승인된 GitHub CLI로 [#5](https://github.com/keulreobeu/jipdam/issues/5)에 최종 결과와 ZIP 해시를 게시하고 로컬 기록문과 전체 본문 일치를 확인했다. 모든 수집 Task AC가 통과하여 verified로 변경한다. 후속 통합 DB Goal 전체·추천·Drive 업로드의 완료는 의미하지 않는다.

## 2026-10-12 계획 재검토·후속 실행

현재 채팅의 사용자가 세 API 계획을 검토·보완 후 실행하도록 요청했다. 기존 구현·원본을 재사용하고 Source Registry의 매매 일반 제외와 계획의 세 API 범위 불일치를 명시한다. API 키 보관함의 연결 API 제거·별칭 통일과 재등록은 다른 작업에서 진행 중이며 사용자 완료 통보 전까지 새 호출·보관함 연결 변경을 하지 않는다.

이번 후속 구현은 원본 레코드별 staging·유효/기간 제외/거부 사유, 전체 건수 대사, 최신 원본과 파생 DB의 패키지 일치 검증과 오프라인 재생성 증거를 보완한다. 잘못된 필수 값이 있으면 공개할 정규화 DB 전체를 rollback하고 모든 발견 오류의 행 위치를 별도 보고한다. 기존 DB·XML을 덮어쓰지 않는다. 단지·주소·시설 매칭과 추천 연결은 실행하지 않는다.

검토/증거: [Plan](../plans/molit-xml-offline-db.md), [후속 검증](../molit-validation-20261012.md). 실제 완료는 세 API 전체 범위와 원본·DB 검증이 모두 통과한 뒤 기록한다. 이 단계 완료는 통합 DB Goal 전체 완료가 아니다.

후속 실제 실행에서 드러난 두 원인을 수정했다. 원본 조인에 관측 키 단독 인덱스가 없어 서울 규모에서 반복 전체 검색이 발생했고, 기존 composite PK를 유지한 채 별도 인덱스를 추가했다. Windows의 열린 읽기 핸들은 manifest 원자 교체를 WinError 5로 거부하는 것을 재현했으며, 교체만 제한적으로 재시도하고 received journal을 무호출 복구한다. 기존 XML과 공개된 DB를 수정하지 않았다. GitHub 연결의 수정·댓글 403과 대체 Git 자격증명 사용에 대한 자동 승인 거부 때문에 기록 갱신은 별도 승인/수동 게시가 필요하다.

## 2026-10-13 재개

사용자가 Goal을 재개했다. 직접 DB 경로 접근 거부를 데이터 손상으로 판단하지 않고, 원본 ZIP 해시를 먼저 대조한 뒤 새 경로에 복원하여975query와 전체 원본/DB hash·건수·무결성을 다시 확인했다. 추가 API/키 접근0, 기존 파일/ACL 변경0. [재개 증거](../molit-resume-validation-20261013.md)를 따른다. GitHub #5 결과 갱신은 연결앱403으로 다시 실패했고 완료로 표시하지 않는다.

사용자가 [후속 통합 계획](../plans/canonical-db-continuation-20261013.md)을 승인했다. 후속 canonical 구현은 독립 Spec/ADR/Task로 연결하며 이 수집 Task의 완료를 통합 Goal 완료로 간주하지 않는다.

2026-10-13 사용자가 남은 입력 요청 해소와 로그인된 GitHub CLI 사용을 지시했다. 기존 연결앱403 실패 이력은 보존하며 Git credential helper를 조회하지 않고 공식CLI의 기존 로그인으로 기록을 게시했다. 게시 방식 질문은 해결되었고 추가 답변을 요구하지 않는다.
