# TASK-GMS-001 — 웹 GMS 연결 확인·크레딧 계산

```toml
kind = "task"
id = "TASK-GMS-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/17_gms_connection_spec.md", "outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/gms.py", "outputs/budongi_mvp_temp/src/budongi/credential_server.py", "outputs/budongi_mvp_temp/src/budongi/static/credentials.html", "outputs/budongi_mvp_temp/src/budongi/static/credentials.js", "outputs/budongi_mvp_temp/src/budongi/static/credentials.css", "outputs/budongi_mvp_temp/tests/test_gms.py", "outputs/budongi_mvp_temp/docs/specs/00_project_spec.md", "outputs/budongi_mvp_temp/docs/specs/17_gms_connection_spec.md", "outputs/budongi_mvp_temp/docs/plans/gms-connection.md", "outputs/budongi_mvp_temp/docs/adr/ADR-010-bounded-gms-probe.md", "outputs/budongi_mvp_temp/docs/tasks/gms-connection.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json"]
acs = ["GMS-001-AC-01", "GMS-001-AC-02", "GMS-001-AC-03"]

[[verification]]
command = "python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_gms.py -v (PYTHONPATH=product src; TEMP/TMP=workspace .local_runtime/gms-test-temp)"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/gms-connection.md#validation"
acs = ["GMS-001-AC-01", "GMS-001-AC-02", "GMS-001-AC-03"]

[[verification]]
command = "node --check outputs/budongi_mvp_temp/src/budongi/static/credentials.js"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/gms-connection.md#validation"
acs = ["GMS-001-AC-02", "GMS-001-AC-03"]

[[verification]]
command = "manual: Codex IAB http://127.0.0.1:8765/; GMS placeholder/disabled check, 1000/300 to 3000/1000 estimate, restore defaults, console warnings/errors"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/gms-connection.md#validation"
acs = ["GMS-001-AC-02", "GMS-001-AC-03"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/verify_environment.py (TEMP/TMP=workspace .local_runtime/gms-test-temp)"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/gms-connection.md#validation"
acs = ["GMS-001-AC-01", "GMS-001-AC-02", "GMS-001-AC-03"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/gms-connection.md#validation"
acs = ["GMS-001-AC-01", "GMS-001-AC-02", "GMS-001-AC-03"]
```

## 범위

사용자의 2026-10-14 GMS 요청에 따라 보관함의 등록/교체를 재사용하고 별도 선택 ID의 제한된 Responses 연결 시험과 무통신 비용 계산기를 추가한다. 신규 제품 기능. [Spec](../specs/17_gms_connection_spec.md), [Plan](../plans/gms-connection.md), [ADR](../adr/ADR-010-bounded-gms-probe.md). 추천 채팅 전환/실데이터 전송/수집/자동 충전은 범위 밖이다.

## 완료 기준

- [x] GMS-001-AC-01 교체와 호출 경계
- [x] GMS-001-AC-02 상태와 비밀값 비노출
- [x] GMS-001-AC-03 계산과 가정 표시

## validation

2026-10-14 Python 3.12 합성 테스트 12개와 JavaScript 문법 검사가 통과했다. 고정 endpoint/model/input/store=false/64토큰 상한, 선택 키와 교체 후 새 키, 동시 busy·잠금 해제, 미동의·보안 저장소 실패·Host/Origin/CSRF 차단, 등록/교체/삭제/GET/계산기의 GMS 무호출, 401/403/402/429/404/400/500·리다이렉트 분류, 타임아웃·네트워크·비 ASCII 키·초과/잘못된/불완전 응답, 공급자 생성문/비밀값 비노출, Decimal 비용·내림 호출 수·가정 시간·무효값을 검사했다. 모든 GMS transport는 가짜이며 실제 외부 요청은 0회다.

현재 사용자 프로필 보관함의 localhost:8765 서버를 실행하고 IAB에서 새 화면을 확인했다. GMS 키 미선택 시 확인 버튼은 비활성이며, 기본값은 50크레딧/600회/60시간이다. 입력 3,000·출력 1,000·시간당 10회로 바꿔 계산하자 160크레딧/187회/18.7시간이 표시됐다. 기본값을 복원했고 콘솔 경고/오류는 0개였다. 기존 저장 키는 복호화/교체/삭제하지 않았으며 실제 GMS 키를 입력하지 않았다. Windows 보안 저장소 사용 가능 배지를 확인했다.

첫 sandbox 실행은 Temp DB 권한과 localhost WinError 10013 때문에 실패했다. workspace의 무시된 TEMP/TMP와 승인된 sandbox 밖 localhost 검사로 해결했다. 첫 전체 검증은 시스템 Python의 openpyxl 부재 및 기존 non-ASCII CSRF 검사에서 일시적 WinError 10053으로 실패했다. 의존성이 설치된 프로젝트 .venv 재검사에서 제품 테스트 166개(67.349초), 팀·SDD 테스트 22개(1.601초), 모델 없는 합성 CLI smoke가 모두 통과했다. root/브랜치 SDD 검사는 11기능·67AC·26Task 참조와 기존 미커밋 변경을 포함해 통과했고 `git diff --check`도 통과했다. 실제 수집·GMS 호출은 실행하지 않았다.

실제 GMS 키는 제공되지 않았으며 외부 유료 시험은 실행하지 않았다. 사용자는 로컬 화면에서 키를 등록하고 비용이 표시된 확인 버튼을 눌러 실제 권한을 시험한다. 기능 AC의 합성 검증 완료는 실제 GMS 계정/모델 성공, 잔액 조회, 추천 LLM 원격 연결을 뜻하지 않는다.
