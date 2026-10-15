# TASK-GMS-BUDGET-001 — 잔액·예산·GMS 코드 작업

```toml
kind = "task"
id = "TASK-GMS-BUDGET-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/gms_budget.py", "outputs/budongi_mvp_temp/src/budongi/gms_work.py", "outputs/budongi_mvp_temp/src/budongi/credential_server.py", "outputs/budongi_mvp_temp/src/budongi/static/credentials.html", "outputs/budongi_mvp_temp/src/budongi/static/credentials.js", "outputs/budongi_mvp_temp/src/budongi/static/credentials.css", "outputs/budongi_mvp_temp/src/budongi/cli.py", "outputs/budongi_mvp_temp/tests/test_gms_budget.py", "outputs/budongi_mvp_temp/tests/test_gms.py", "outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md", "outputs/budongi_mvp_temp/docs/specs/00_project_spec.md", "outputs/budongi_mvp_temp/docs/plans/gms-budget-work.md", "outputs/budongi_mvp_temp/docs/adr/ADR-011-gms-budgeted-work.md", "outputs/budongi_mvp_temp/docs/tasks/gms-budget-work.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/README.md", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", "docs/sdd/traceability.json"]
acs = ["GMS-BUDGET-001-AC-01", "GMS-BUDGET-001-AC-02", "GMS-BUDGET-001-AC-03"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/verify_environment.py (TEMP/TMP=workspace .local_runtime/gms-test-temp)"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/gms-budget-work.md#validation"
acs = ["GMS-BUDGET-001-AC-01", "GMS-BUDGET-001-AC-02", "GMS-BUDGET-001-AC-03"]

[[verification]]
command = "node --check outputs/budongi_mvp_temp/src/budongi/static/credentials.js"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/gms-budget-work.md#validation"
acs = ["GMS-BUDGET-001-AC-03"]

[[verification]]
command = "manual: selected credential key-info GET; GMS input_tokens; gms-work quote/execute for TASK-GMS-BUDGET-001; IAB actual balance/5000 reserve/policy/counter fee/ledger and console"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/gms-budget-work.md#validation"
acs = ["GMS-BUDGET-001-AC-01", "GMS-BUDGET-001-AC-02", "GMS-BUDGET-001-AC-03"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/gms-budget-work.md#validation"
acs = ["GMS-BUDGET-001-AC-01", "GMS-BUDGET-001-AC-02", "GMS-BUDGET-001-AC-03"]
```

## 목표·근거

2026-10-14 사용자 요청과 제공 key-info 가이드에 따라 [Plan](../plans/gms-budget-work.md)을 구현한다. Goal은 이 기능의 구현/검증이며 실제 유료 코드 작업 성공은 한도 설정 뒤 별도 증거로 남긴다.

## 완료 기준

- [x] GMS-BUDGET-001-AC-01 실제 잔액 adapter·비노출
- [x] GMS-BUDGET-001-AC-02 정책·견적·예약·정산·재시작
- [x] GMS-BUDGET-001-AC-03 웹·코드 CLI 경로·예산 진입점

## validation

2026-10-14 구현/검증. 제공 key-info 가이드를 확인했다. 최초 GMS root 방문은 유효하지 않은 경로 화면이었으며 사용자가 로그인 및 공식 가이드를 추가 제공했다. 사용자는 현재 작업의 실제 GMS 실행도 승인하고 최소 5,000크레딧 보존을 지정했다. 현재 작업은 담당자가 보수적으로 전체 500크레딧/10,000토큰, 호출당 입력 4,000/최대 출력 2,000토큰/280크레딧, 카운트 조회 상한 20크레딧을 적용했다. 이 초기 상한을 사용자가 직접 지정한 값이라고 소급하지 않는다.

### 실제 GMS 증거

사용자가 로컬 화면에서 명시적으로 선택한 키 ID를 사용했다. 원문은 출력/로그/프롬프트/Git에 넣지 않았다. key-info GET이 전체 30,000·사용 0·잔여 30,000과 `2026-10-16 18:00:00.000 KST` 만료일을 반환했다. 실제 KST 접미사 형식을 지원했다.

GMS 경유 input_tokens의 실제 입력 계산은 359토큰이었다. 승인된 만료일 파서의 모순된 KST/UTC offset 처리 코드 작업을 한 번 실행했다. 예상 출력 700토큰의 요율 견적은 77.18크레딧, 출력 상한 2,000의 생성 최대 예약은 207.18이었다. 응답은 completed 텍스트, 실제 입력 359/출력 683토큰이며 요율 기반 비용은 75.48이었다. GMS가 작성한 함수의 timezone 충돌 검사를 검토해 반영했다. GMS가 제시한 테스트 정규식의 과도한 escape는 로컬 검토에서 정확한 오류 문자열 검사로 수정하고 KST 충돌/일치 테스트를 적용했다. 모델에 로컬 파일/명령 실행 권한을 주지 않았다.

당시 실제 usedCredit는 135, remainCredit는 29,865였다. input_tokens 프록시 조회에도 요금이 붙는 차이를 확인해, 조회 비용부터 예약·usedCredit 전후 차이 대사·조회 실패 최대 보류·상한 초과 중지로 수정했다. 최초 미추적 차액은 135−75.48=59.52를 키 없는 보수적 대사 레코드로 추가했다. 이 차액을 개별 공급자 청구서나 순수 모델 비용이라고 주장하지 않는다.

보완 후 실제 웹에서 입력 110토큰의 견적 조회를 한 번 실행했다. 조회 전 usedCredit 135, 조회 후 155로 20크레딧 차감을 확인했고 원장에 반영했다. 예상 출력 1,000이면 조회 포함 예상 122.2, 전체 최대 222.2(생성 예약 202.2)크레딧을 표시했다. 이 추가 견적은 실행하지 않았다. 최종 공식 잔여 29,845/사용 155, 원장 155크레딧/모델 1,042토큰/보류 0을 확인했다. key-info GET만 반복해도 잔액은 유지됐다. 카운트 요금의 공식 상한은 미제공이며 관측값 20을 초과하면 후속 실행을 중지한다. 계정 차이에 팀의 다른 사용이 섞일 수 있어 보수적으로 계산한다.

### 로컬 검증

GMS 테스트 35개가 첫 최종 실행에서 통과했다. 이후 계정 차감이 작은 usage보다 큰 경우와 생성 후 잔액 조회 실패의 최대 비용 보류를 추가했다. 전체 검사 첫 실행은 제품 193개 중 HTTP guard 경로에서 일시적인 Windows WinError 10053 한 건으로 실패했다. 최신 코드의 전체 재검사는 제품 194개(72.599초), 팀/SDD 22개(1.565초), 모델 없는 합성 CLI smoke가 모두 통과했다. 이 제품 검사에는 기존 GMS 12개+새 잔액/예산/CLI 25개가 포함된다. JS 문법/브랜치 SDD/공백 검사도 통과했다. 테스트 transport는 합성이며 위의 실제 GMS 생성과 분리한다.

IAB localhost:8765에서 공식 잔액·5,000 보존·초기 한도 저장·조회 요금 포함 견적·누적 원장을 확인했다. 새로고침 뒤 정책/누적 사용량이 유지됐고 실행 버튼은 새 견적 없이는 비활성이었다. 최종 콘솔 경고/오류는 0개다. 외부 GMS 확인 탭에서 키를 복사하지 않았고 비밀값을 브라우저 영속 저장소에 넣지 않았다. 실제 원본 데이터/DB/다른 키는 전송하지 않았다.

### 결과·다음 작업

명확한 코드 작업은 `gms-work --request <승인된 Task JSON> --execute`를 우선 사용하는 공통 AGENTS 지침을 추가했다. 현재 채팅 모델 자체의 공급자를 교체하지 않았다. 실제 키 정보·count 경유·코드 초안 생성·로컬 반영/테스트를 확인했고 미래 작업은 저장된 한도/실잔액/만료/카운트/예약을 매번 통과해야 한다. 보존 크레딧에도 2026-10-16 18:00 KST 만료가 적용된다. 사용자 변경 전 현재 전체 사용 상한은 500크레딧이다.

### Goal 완료 감사

| 요구 | 현재 증거 |
| --- | --- |
| 실제 잔여량/만료 조회 | key-info 실제 GET 및 최종 웹 29,845/155·KST 만료 표시 |
| 사용자가 남길 5,000 보존 | 저장 정책·예산 경계 테스트·새로고침 영속성 |
| 호출/작업 단위 입력·출력·누적 토큰 한도 | 작업 runner는 한 번의 동결 생성에 호출 한도를 적용; 모든 작업의 누적에는 전체 토큰 한도 적용; 입력/출력/누적·초과·키/정책 변경 테스트 |
| 생성 전 입력 카운트·출력 예상 비용 | 실제 count 359/110토큰; 조회 비용 포함 견적; 출력 예상/최대 구분; 매 생성 전에 일치하는 고정 input/model의 카운트 확인 |
| 조회·최대 생성 비용 예약/usage 대사 | 실제 카운트 차감 20 및 원장155; 정상 차액 반환·미확인 최대 보류·provider 초과 중지·누적·동시·재시작 테스트 |
| Plan/Spec/Task/Goal | 해당 영구 문서·SDD 원장·이 채팅 Goal의 구현/검증 목적 연결 |
| 명확한 코드 작업 GMS 우선 | 실제 GMS가 파서 함수/테스트 초안 작성; 로컬 검토/수정/적용/테스트; 공통 AGENTS의 runner 우선 지침 |
| 비밀값/데이터/현재 모델 경계 | 허용된 서버 HTTPS만 선택 키 사용; prompt/키 없는 원장; 문맥 경로/비밀 탐지 테스트; 현재 Codex 공급자 및 원본 DB/추천 경계 유지 |
