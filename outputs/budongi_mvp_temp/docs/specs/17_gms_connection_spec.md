# GMS Connection Spec

```toml
kind = "spec"
id = "GMS-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-14"
approval_ref = "GMS 3만 크레딧 사용을 위한 웹 키 등록/교체와 사용 가능 여부 확인, 대략적인 사용시간 요청; 사용자가 제공한 Responses endpoint/model/토큰별 요율"
```

## 목표·범위

기존 CRED-001 로컬 웹 보관함에서 키를 등록/교체하고 명시적으로 선택해 GMS 연결을 시험한다. 키 저장은 무통신이며 연결 확인만 고정 시험 문장을 한 번 전송한다. 실제 추천 채팅의 원격 전환, DB/질문 전송, 원격 수집, 자동 반복 호출, 자동 충전은 포함하지 않는다. 실제 GMS 잔액 조회 API는 제공되지 않았으므로 30,000은 사용자가 입력한 계산용 예산이다.

## GMS-001-REQ-01 키 선택과 유료 연결 시험

CRED-001의 암호화/교체/삭제/loopback Host·Origin·CSRF 계약을 재사용한다. 선택한 credential ID를 서버에서 복호화하고 HTTPS `https://gms.ssafy.io/gmsapi/api.openai.com/v1/responses`에 Bearer로만 보낸다. 모델은 `gpt-6.1-sol`, 고정 입력은 `Reply with OK.`, `store=false`, 출력 상한은 64토큰이다. 입력 비용을 포함한 예상 최대 비용은 약 7크레딧이며 실제 비용은 응답 usage로 계산한다. 비밀값을 환경변수·파일에 임시 복사하지 않는다. GMS 문서의 환경변수 예시는 curl 사용용이며 웹에서는 기존 보관함의 메모리 경계를 따른다.

등록/교체/목록 조회와 계산기는 외부 호출이 없다. 확인 버튼의 비용 표시와 POST의 `confirm=true`가 명시적 호출 의도다. 동시 시험은 한 개로 제한하고 자동 재시도·리다이렉트를 금지한다. 타임아웃 20초, 응답 상한 64KiB. 서버에 endpoint/model/input을 지정하는 일반 프록시를 만들지 않는다.

### GMS-001-AC-01 교체와 호출 경계

저장/교체/GET/확인 미동의/잘못된 Origin·CSRF/보관함 실패는 GMS 호출 0회다. 선택 ID만 사용하며 교체 뒤 다음 시험에는 새 키를 쓴다. 동시 요청은 busy 상태다.

### GMS-001-AC-02 상태와 비밀값 비노출

완료된 텍스트 응답은 available, 출력 상한에 의한 중단은 output_limited, 401은 unauthorized, 403은 forbidden, 402는 insufficient_credit, 429는 rate_or_quota_limited, 404는 model_unavailable, 기타 HTTP·네트워크·응답 오류는 구분해 표시한다. 429만으로 잔액 부족을 확정하지 않는다. 공급자 본문/모델 생성문/예외/키/암호문은 브라우저·로그에 반환하지 않는다. 실패에도 비용이 발생했을 수 있으며 usage 없는 오류에서 비용 0을 주장하지 않는다. 확인 결과는 현재 페이지에만 표시하고 키 변경/재조회/삭제 시 지운다. 과거 결과로 최신 키 상태나 향후 사용을 보장하지 않는다.

## GMS-001-REQ-02 사용량·시간 계산

제공 요율(입력 토큰당 0.02, 출력 토큰당 0.1)을 사용한다. 비용 = 입력×0.02 + 출력×0.1. 가능 호출 수 = floor(예산/비용), 예상 사용시간 = 가능 호출 수/시간당 호출 수. 입력/출력은 0 이상 정수이며 합계 비용은 양수, 예산/빈도는 양수 유한값이어야 한다. 문맥 재전송과 reasoning 토큰도 usage에 포함되므로 실제 사용량으로 계산하도록 안내한다. 캐시 할인·장문 할증·실제 잔액/만료/속도를 추정하지 않는다.

### GMS-001-AC-03 계산과 가정 표시

30,000 예산·1,000 입력·300 출력·시간당 10회이면 50크레딧/회·600회·60시간이다. 3,000/1,000이면 160/회·187회·18.7시간이다. 무효/0비용 값은 오류이며 계산은 무통신이다. UI에 토큰별 요율, 계산용 예산, 호출 빈도, 실제 잔액 미조회, reasoning/누적 문맥을 표시한다.

## 관련 문서

[Plan](../plans/gms-connection.md), [ADR-010](../adr/ADR-010-bounded-gms-probe.md), [Task/검증](../tasks/gms-connection.md), [CRED-001](11_api_credential_vault_spec.md). API usage/출력 상한 근거는 [OpenAI 공식 토큰 계산 문서](https://developers.openai.com/api/docs/guides/token-counting).
