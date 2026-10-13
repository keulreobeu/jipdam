# TASK-CANONICAL-001 — 실제 원본 기반 통합 DB와 증분 검증

```toml
kind = "task"
id = "TASK-CANONICAL-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md", "outputs/budongi_mvp_temp/docs/specs/12_molit_collection_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/collection_integrate.py", "outputs/budongi_mvp_temp/src/budongi/source_files.py", "outputs/budongi_mvp_temp/src/budongi/collection_db.py", "outputs/budongi_mvp_temp/src/budongi/collection_cli.py", "outputs/budongi_mvp_temp/tests/", "outputs/budongi_mvp_temp/docs/", "outputs/budongi_mvp_temp/README.md", "outputs/budongi_mvp_temp/AGENTS.md", "AGENTS.md", "docs/sdd/traceability.json"]
acs = ["CANONICAL-001-AC-01", "CANONICAL-001-AC-02", "CANONICAL-001-AC-03", "CANONICAL-001-AC-04", "CANONICAL-001-AC-05", "CANONICAL-001-AC-06", "CANONICAL-001-AC-07"]

[[verification]]
command = "기존 수집15개 및 입력 경계3개 오류 계약 회귀; 실제975query 복원 입력의 네트워크/키 차단 검증"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/molit-resume-validation-20261013.md#canonical-input-validation"
acs = ["CANONICAL-001-AC-01"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py; scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/molit-resume-validation-20261013.md#canonical-input-validation"
acs = ["CANONICAL-001-AC-01"]

[[verification]]
command = "실제 서울 전체 canonical SQL/원본 대사/동일 배치 재적재/겹치는 범위와 확대 증분/이전 DB 불변/17개 테이블 digest 및 v2→v3 사본 변환 감사"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/canonical-validation-20261013.md#goal-completion-audit"
acs = ["CANONICAL-001-AC-02", "CANONICAL-001-AC-03", "CANONICAL-001-AC-04", "CANONICAL-001-AC-06"]

[[verification]]
command = "최종 제품 unittest129개/팀18개/합성 CLI smoke/verify_environment.py/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/canonical-validation-20261013.md#final-canonical-v3-and-checks"
acs = ["CANONICAL-001-AC-01", "CANONICAL-001-AC-02", "CANONICAL-001-AC-03", "CANONICAL-001-AC-04", "CANONICAL-001-AC-05", "CANONICAL-001-AC-06", "CANONICAL-001-AC-07"]

```

사용자2026-10-13전체후속계획승인으로실행한다. Spec/ADR/Plan의근거를유지하며실제수집975query와복원경로를입력으로사용한다. 새API호출/키접근/원격업로드/역사DB수정은하지않는다.

## 완료 기준

- [x] CANONICAL-001-AC-01 현재 원본/계획/DB 무결성과 기본 완료 정책.
- [x] CANONICAL-001-AC-02 공통 모델·실제 공식 관계·제약/전체 조인.
- [x] CANONICAL-001-AC-03 미확정 후보와 출처별 관측 보존.
- [x] CANONICAL-001-AC-04 반복·증분·버전·충돌·rollback.
- [x] CANONICAL-001-AC-05 등록 파일 형식의 보존부터canonical까지.
- [x] CANONICAL-001-AC-06 실제 전체 DB·원본·조인·재생성·증분 대사.
- [x] CANONICAL-001-AC-07 CLI·문서·기존 회귀·환경/SDD.

## Validation

2026-10-13 승인된 후속 범위를 실제 실행과 합성 계약 시험으로 검증했다. 현재 권장 DB는 canonical_real_estate_v3이며 기존 v2는 원본을 변경하지 않고 새 사본에서 변환한다. 실제 서울 원본 384,211행, 유효 관측 374,892행, 기간 밖 9,319행과 사유를 대사했다. 전체 원본 추적 조인 374,892행·공식 단지/주소 조인 68,135행·무결성 ok/FK 위반 0을 확인했다.

동일 배치 재적재의 17개 테이블 추가 행은 0개이며 전체 값이 일치한다. 겹치는 범위는 기존 관측을 재사용하고 종로구→서울 확대는 새 관측 374,755행을 추가했다. 이전 DB 해시는 유지했다. v2→v3 실제 사본의 17개 테이블 전체 정렬 digest도 일치한다. 출처별 관측은 자동 거래 병합하지 않는다. 미확정 후보와 공식 ID 지역 충돌 1건은 원문·근거와 함께 보존한다.

CSV/JSON/XLSX는 원본 바이트·모든 선언 섹션·정확한 원 정수·날짜·NULL·행 위치를 보존하고 원본 재파싱으로 staging 전체를 대사한 뒤 같은 canonical 스키마에 적재한다. 원본/정규화 변조·등록/승인 부재·완료 건수 불일치·거부 행은 공개 출력을 막는다. 반복/새 배치/새 버전/rollback·합성 품질 혼합 거부·JSON 선택 분리·공식 ID/주소·CLI를 시험했다. 실제 신규 파일 출처 수집으로 보고하지 않는다.

최종 환경 검사는 제품129개·팀18개와 모델 없는 합성 CLI smoke를 통과했다. 통합 회귀12개, 파일 보존8개, 파일 canonical9개가 포함된다. source_unverified 차단·기존 역사2023 cutoff·키 비노출 회귀를 유지한다. 최초 성능 회귀, CLI 테스트 진입점과 연결 정리 오류 및 수정 증거는 보존했다.

[검증 기록](../canonical-validation-20261013.md)의 실제 전체/증분/v3/Goal 9조건 표와 [실행 문서](../canonical-db.md)를 최종 근거로 삼는다. 신규 수집·좌표·시설·추천·Drive 업로드·코드 push/PR/merge는 포함하지 않는다. 추가 사용자 입력은 없다. 이 Task의7개 AC는 verified이며 추천 제품/Golden의 별도 미완료 상태는 유지한다.
