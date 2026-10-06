# ADR-004 — 로컬 전월세 API 자격증명 보관함

Status: Accepted. 담당자: keulreobeu. 날짜: 2026-10-06.

관련 계약: [CRED-001](../specs/11_api_credential_vault_spec.md), [RENT-001](../specs/10_rental_recommendation_spec.md), [PLAN-RENT-001](../plans/rental-recommendation-mvp.md), [TASK-CRED-001](../tasks/api-credential-vault.md). 사용자 결정: API 키는 암호화해 저장하고, 키별 별칭·폴더를 제공하며 폴더 삭제 시 포함 키도 삭제한다. 암호화 키 보호 방식으로 Windows 계정에 묶인 OS 자격 증명 저장소를 선택했다.

## Context

전월세 추천은 공공데이터포털, Kakao Local, 서울 열린데이터광장 등 서로 다른 API 자격증명을 사용할 수 있다. 환경변수만 허용하면 여러 키의 별칭·폴더 관리와 로컬 데모 설정 화면을 제공하기 어렵다. 기존 역사 CLI는 이미 환경변수를 사용하므로 그 동작을 깨지 않고 새 전월세 경로를 분리해야 한다.

## Decision

- 신규 전월세 API 키는 역사·임대차 데이터 DB와 별도인 사용자 로컬 보관함에서 관리한다. SQLite에는 메타데이터와 암호문만 두고 API 키 원문은 저장하지 않는다.
- API 키 값은 AES-256-GCM으로 암호화한다. 256-bit 암호화 키는 Windows Credential Manager에 저장해 현재 Windows 사용자 계정에 묶는다. 키 저장소가 없거나 사용할 수 없으면 fail-closed이며 평문 대체는 금지한다.
- 사용자는 평면 폴더로 키를 분류하고 각 키에 별칭을 붙인다. 같은 공급자용 키를 여러 개 허용한다. 런타임 공급자 adapter에는 명시된 credential ID를 전달하며 임의 별칭을 자동 선택하지 않는다.
- 폴더 삭제는 명시적 확인 뒤 트랜잭션으로 폴더와 모든 자식 키를 삭제한다. SQLite의 WAL/저장매체까지 포렌식 복구 불가능하다고 보장하지 않고 앱 보관함에서의 영구 삭제로 정의한다.
- 키는 로컬 server-side adapter만 사용한다. 웹 화면은 입력 원문을 등록/교체 POST로 한 번 보내고 다시 받지 않는다. 키를 URL·브라우저 영속 저장소·LLM·로그·오류 응답에 넣지 않는다.
- 키 등록과 키 사용을 분리한다. 데이터 수집 보류가 해제되기 전까지 저장한 키로 외부 API를 호출하지 않으며 유료 쿼터를 자동 활성화하지 않는다.

## Alternatives

| 대안 | 판단 |
| --- | --- |
| 환경변수만 계속 사용 | 기존 CLI와 호환되지만 여러 키의 사용자 별칭·폴더·앱 설정 화면 요구를 충족하지 못해 신규 전월세 경로에는 채택하지 않음 |
| 평문 SQLite 또는 `.env` 파일 보관 | 저장소 유출·백업·프로젝트 폴더 노출 시 키가 그대로 노출되어 금지 |
| 앱 잠금 암호를 매번 입력 | 사용자가 암호 입력을 피하고 Windows 계정에 묶인 보호를 선택했으므로 채택하지 않음 |
| 외부 secret manager / 클라우드 동기화 | 외부 서비스·네트워크·운영 비용이 필요하며 로컬 데모 범위에서 제외 |

## Consequences

첫 구현은 Windows native local app과 Credential Manager를 지원한다. 다른 운영체제에서는 OS 보안 저장소 adapter가 별도로 구성되기 전까지 vault 작업을 fail-closed로 처리한다. 암호화 의존성과 키 저장소 상태 검사를 설치·실행 문서와 테스트에 추가한다. 자격증명 보관 파일은 사용자 프로필에 두고 Git 저장소·역사 DB·rental snapshot·원장과 분리한다.

현재 `DATA_GO_KR_SERVICE_KEY`를 읽는 2023 역사 CLI·수집 스크립트의 계약은 이번 전환에서 바꾸지 않는다. 새 임대차 adapter와 앱 UI는 CRED-001을 사용한다. 실제 수집·시설 매칭은 [실데이터 Task](../tasks/rental-real-data.md)가 보류된 상태를 유지한다.

## Verification

CRED-001-AC-01~05 제품 검증은 [vault Task](../tasks/api-credential-vault.md#validation)에 수동 시나리오로 연결한다. 문서 전환 검증은 [문서 Task](../tasks/credential-vault-sdd.md#doc-validation)에 기록한다. 이 ADR은 구현 또는 실제 API 호출 완료 증거가 아니다.
