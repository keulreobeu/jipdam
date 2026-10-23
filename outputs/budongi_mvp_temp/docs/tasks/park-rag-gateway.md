# TASK-PARK-RAG-GATEWAY-001 — 공원 RAG용 보관함 API 경로

```toml
kind = "task"
id = "TASK-PARK-RAG-GATEWAY-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/23_park_rag_gateway_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/credential_server.py", "outputs/budongi_mvp_temp/src/budongi/gms_budget.py", "outputs/budongi_mvp_temp/src/budongi/park_gateway.py", "outputs/budongi_mvp_temp/tests/test_park_gateway.py", "outputs/budongi_mvp_temp/tests/test_gms_budget.py", "outputs/budongi_mvp_temp/docs/specs/23_park_rag_gateway_spec.md", "outputs/budongi_mvp_temp/docs/tasks/park-rag-gateway.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["PARK-RAG-GATEWAY-001-AC-01", "PARK-RAG-GATEWAY-001-AC-02"]
[[verification]]
command = "python -X utf8 -m unittest outputs.budongi_mvp_temp.tests.test_park_gateway outputs.budongi_mvp_temp.tests.test_gms_budget"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/park-rag-gateway.md#validation"
acs = ["PARK-RAG-GATEWAY-001-AC-01"]

[[verification]]
command = "python -X utf8 -m unittest outputs.budongi_mvp_temp.tests.test_park_gateway outputs.budongi_mvp_temp.tests.test_gms_budget"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/park-rag-gateway.md#validation"
acs = ["PARK-RAG-GATEWAY-001-AC-02"]
```

## 목표·근거

사용자의 공원 RAG 구현 요청에 따라 별도 집담 API route를 추가한다. 기존 GMS code-draft prompt, 계정 선택, 최소 잔액, 사전 입력 카운트, 비용 예약/정산, 키 노출 방지 경계를 유지한다.

## 완료 기준

- [x] PARK-RAG-GATEWAY-001-AC-01 견적/실행 가능한 RAG generation과 budget 계약 회귀.
- [x] PARK-RAG-GATEWAY-001-AC-02 Seoul API allowlist, provider 검증, 외부 응답/로그 비노출 회귀.

## validation

- outputs/budongi_mvp_temp/tests/test_park_gateway.py: 4 synthetic tests passed, including the official HTTP base URL contract.
- outputs/budongi_mvp_temp/tests/test_gms_budget.py: 45 tests passed, including RAG prompt mode through the existing quote, reserve and settlement ledger.
- RAG project scripts/validate.py: 52 tests passed.
- scripts.check_sdd.validate: 19 features, 100 acceptance criteria, 41 tasks, 9 changed paths passed before the transport correction; rerun after updating this Task/Spec.
- No live GMS generation was made. One OA-394 request was attempted through the vault proxy and failed without exposing the key or provider response. The user explicitly authorized HTTP after no HTTPS route was found.
