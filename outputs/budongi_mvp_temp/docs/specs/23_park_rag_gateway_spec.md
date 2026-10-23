# 서울 공원 RAG 게이트웨이 Spec

```toml
kind = "spec"
id = "PARK-RAG-GATEWAY-001"
status = "approved"
owner = "keulreobeu"
revision = 2
approved_by = "사용자 요청: 서울 공원 RAG 전체 명세 구현, LLM은 API 키 보관함의 GMS 키 사용"
approved_at = "2026-10-21"
approval_ref = "KAN-18 / 서울 공원 RAG 구현 요청; 2026-10-21 사용자 지시: 안전한 HTTPS 경로가 없으면 HTTP 진행"
```

## 범위

서울 공원 실험 클라이언트가 집담의 기존 로컬 암호화 보관함에 저장된 Seoul Open Data 키와 GMS 키를 사용한다. 키는 클라이언트/UI 응답으로 반환하거나 로그에 기록하지 않으며 서울 API 인증을 위해 서버에서 공급자에 전달한다. 서울 공식 API 샘플은 HTTP만 안내했고 공개 HTTPS 검사에서 :8088 TLS 오류와 443 연결 시간 초과가 확인됐다. 사용자는 안전한 HTTPS 경로가 없으면 평문으로 진행하도록 명시했다. 따라서 allowlist 제한 호출에서 키가 URL 경로로 평문 전송되는 위험을 인지하고 승인한 상태다. 기존 `/api/gms/quote`의 코드 작성 전용 프롬프트와 예산·원장 정책을 보존한다. 새 RAG 경로는 `GMSBudgetManager`의 선택 키·개인 원장·최소 잔액 보존·만료·사전 카운트·최대 예약·실행 재검증·정산을 통과한다.

## PARK-RAG-GATEWAY-001-REQ-01 RAG generation

루프백 Origin/CSRF 보호를 그대로 적용한다. `GET /api/rag/capabilities`는 배포된 기능과 예산 보장을 보고한다. `POST /api/rag/quote`는 공원 답변 또는 후보 선별에 필요한 RAG 입력을 제한된 JSON으로 견적하고, 실행 가능 여부·최대 비용만 반환한다. `POST /api/rag/execute`는 일회성 견적만 실행하고 JSON 구조화 답변을 반환한다. 요청의 키 ID는 받지 않고 현재 저장 정책이 선택한 GMS 키만 사용한다. 입력 크기, 출력 토큰, 인용 수, API 호출 수를 제한한다. 키·공급자 응답 원문·내부 경로는 응답이나 로그에 기록하지 않는다.

### PARK-RAG-GATEWAY-001-AC-01

기능 미배포, 키 미선택, 정책 비활성, 보존 한도 부족, 입력/출력 초과, 만료·재사용 quote는 생성 전에 거절한다. 일반 RAG 입력이 기존 code-draft system prompt에 들어가지 않는다. 정상·usage 누락·공급자 오류는 기존 예약/정산 규칙을 사용한다.

## PARK-RAG-GATEWAY-001-REQ-02 Seoul API proxy

정적 allowlist의 dataset ID→service→허용 parameters에서만 호출한다. `credential_id`는 명시 선택된 `seoul_open_data` provider 키여야 하며 키 원문을 반환하지 않는다. 페이지당 최대 1,000행, 전체 요청 상한, timeout, redirect 차단, 응답 크기와 JSON 구조 검증을 적용한다. OA-23053의 `MOSQUITO_DATE` 외 사용자 parameter는 허용하지 않는다. 원문 오류/요청 URL을 애플리케이션 로그/응답에 넣지 않는다.

### PARK-RAG-GATEWAY-001-AC-02

비허용 dataset·서비스명 위조·타 provider key·잘못된 날짜·과도한 범위·redirect·실패 응답은 거부되고 요청 키/응답 본문/공급자 URL은 노출되지 않는다. 샘플 API fixture와 mock transport로 allowlist 계약을 검사한다.

## 제한 및 완료 표현

API 연결 완료는 로컬 mock 검증과 분리한다. 실제 GMS 호출은 기존 키 선택·정책·예산 원장을 거치고, 실제 서울 호출은 사용자가 승인한 HTTP 경로를 사용하되 allowlist·응답 제한을 유지한다. 외부 실데이터 적재는 별도 검증한다. 기존 rent/DB/recommendation 경계를 변경하지 않는다.
