# PLAN-RENT-001 — 서울 아파트 전월세 추천 전환

담당자: Codex(문서 적용), 후속 제품 Task의 기본 담당자: keulreobeu. 날짜: 2026-10-06.
계약: [RENT-001](../specs/10_rental_recommendation_spec.md). 결정: [ADR-003](../adr/ADR-003-rental-recommendation-first.md). 이번 실행: [TASK-RENT-DOC-001](../tasks/rental-spec-transition.md).

## 확정 근거

사용자는 최초 요청에서 전월세 중심 실거주 추천으로 기존 구상을 비교하고 SDD를 수정하도록 요청했다. 이후 아래 선택을 확정했고, 최종 `PLEASE IMPLEMENT THIS PLAN: 집담: 서울 아파트 전월세 실거주 추천으로 전환` 요청으로 문서 적용을 지시했다. 승인된 계획의 실행 범위는 **SDD 문서 수정**, 제품 코드는 후속 Task다.

| 결정 | 실제 답변 | 계약에 반영한 이유 |
| --- | --- | --- |
| D1 | 아파트 단지 후보 | 실거래 API와 현재 매물을 구분 |
| D2 | 서울 | 데이터 결합·검수의 첫 범위 제한 |
| D3 | 직장·역 거리부터 | 통근시간·도보거리로 잘못 표현하지 않음 |
| D4 | 최신 추천 우선 | 2023 연구 완료를 제품 선행 조건에서 제거 |
| D5 | 명세만 정리·보류 유지 | 실제 수집·매칭을 재개하지 않음 |
| D6 | 보증금·월세 각각 | 관리비·대출비용을 합친 총주거비를 주장하지 않음 |
| D7 | 새 Spec 중심으로 연결 | 기존 CURRENT·baseline·평가 이력 보존 |
| D8 | 필수·선호 구분 | 필수 통과와 추천 이유·포기할 조건을 분리 |
| D9 | office-hours 추가 | 첫 사용자 장면과 데모 접근 검토 |
| D10 | 팀 MVP·발표 데모 | 작은 완성 흐름 우선 |
| D11 | 추천 이유·포기할 조건 비교 | 근거를 확인할 수 있는 비교를 첫 가치로 선택 |
| D12 | 간단한 웹 입력·비교 화면 | 지도·대화 세션 없는 최소 UI |
| D13 | 백엔드 판단·LLM 설명 | 추천의 재현성, 모델 없는 실행 확보 |
| D14 | Python 단일 앱 | 기존 SQLite·CLI·평가기 재사용 |
| D15 | 마트·공원·병원 | 역 거리와 함께 첫 생활시설 범위 고정 |
| D16 | API 키 암호화 보관함 | 여러 공급자 키·키별 별칭·분류 폴더를 지원하고 폴더 삭제 시 포함 키도 삭제 |
| D17 | Windows Credential Manager | 암호화 키를 현재 Windows 사용자 계정에 묶고, 안전한 OS 저장소가 없으면 fail-closed |

12개월 관측 기간·최신 계약 우선·기본 5/최대 20·선호 충족 수/거리/날짜/ID 순위는 승인된 최종 계획에 포함된 기본값이다. 같은 날짜 관측 키·월말 경계·중복 조건 거부·명시적 오류는 그 동작을 재현하는 구현 규칙이며 신규 데이터 수집·비용을 승인하지 않는다. D16은 사용자의 API 키 보관함 요청, D17은 사용자의 Windows 계정 OS 자격 증명 저장소 선택으로 확정했다. 이번 추가도 SDD와 후속 Task를 갱신하며 보관함 제품 코드나 실제 API 호출을 실행하지 않는다.

## office-hours 결과와 접근 비교

문제 가설은 집을 찾는 사람이 여러 단지의 예산·직장 거리·생활시설을 일관된 기준으로 비교하기 어렵다는 것이다. 첫 대상은 신혼·첫집·사회초년생, 산출물은 발표 가능한 로컬 비교 데모다. 실제 사용자 수요·구매 의향·시장 성과를 검증했다고 주장하지 않는다.

실거래·단지 정보는 [네이버 부동산](https://land.naver.com/)과 [호갱노노](https://www.hogengnono.com/recommend/apt)에서도 제공한다. 집담의 데모 가치는 입력한 조건의 충족·포기·미확인을 거래 근거까지 확인하는 흐름에 둔다. 이는 기능 방향에 대한 판단이며 경쟁 우위를 실증한 결과는 아니다.

| 접근 | 규모·위험 | 재사용·장단점 | 결정 |
| --- | --- | --- | --- |
| Python 단일 앱 + 정적 웹 | 작은 변경, 로컬 운영 | SQLite·CLI·검증 재사용, 프런트 빌드 불필요. 대규모 배포 구조는 별도 필요 | 채택(D14) |
| Python API + 별도 프런트 | 추가 빌드·의존성·운영 | UI 확장은 쉬우나 같은 발표 범위에 절차가 늘어남 | 후속 선택지 |

설계 전제: 실거래를 매물로 부르지 않는다(D1); LLM이 조건·순위를 결정하지 않는다(D13); 최신 서비스 데이터와 2023 연구를 분리한다(D4·승인된 최종 계획). 첫 화면은 조건 입력, 다음 화면은 후보 비교와 추천 이유다. 샘플은 합성 여부를 명확히 표시하며 실제 단지·거래·시설을 만들어내지 않는다.

## 2026-10-06 초기 계획의 유지·추가·중단

이 표는 초기 승인 이력이다. 지도·대화의 현재 범위는 아래 2026-10-14 사용자 승인 실행 계획에서 확장됐다.

| 분류 | 대상 | 처리 |
| --- | --- | --- |
| 유지 | Python/SQLite, 불변 스냅샷, 정규화 단위·출처·해시, 제한된 Tool·평가기 | 기존 코드·CURRENT·SDD-001/EVAL-001 이력 보존 |
| 추가 | 전월세 적재·검수, 단지/좌표/시설 연결, 필수·선호, 순위·비교표 | RENT-001과 후속 Task에 기록 |
| 추가 | Windows 계정 보호 API 키 보관함·키별 별칭·폴더 연쇄 삭제 | CRED-001·ADR-004·후속 제품 Task에 기록; 키 등록은 외부 호출을 시작하지 않음 |
| 앞당김 | 최신 데이터 계약과 최신성 검사 | 제품 첫 데이터 단계에서 다룸 |
| 개발 후순위 | 매매·청약 확대, RAG·Hybrid | 첫 전월세 MVP의 선행 작업에서 제외 |
| 연구 보류 | LoRA·Adapter/Model Router·Judge·대형 모델 비교 | 제품 실패 증거·별도 계약을 갖추면 재검토 |
| 필수 순서에서 제거 | 실제 2023 스냅샷·기존 약 200건 Golden 완료 | 기존 미완료 상태를 보존하고 별도 연구로 관리 |
| 첫 범위 밖 | 현재 매물, 아파트 외/서울 외, 통근시간, 총주거비, 청약·공공주택, 치안·소음·전세안전, 지도·대화·배포 | 미지원 표시, 무근거 답변 금지 |

[기존 LLM 실행 계획](../budongi_advanced_llm_evaluation_plan.md)의 Phase 0~17은 보존된 선택형 연구 계획이다. 새 제품 로드맵은 아래 표이며 역사 Phase 완료를 제품 완료와 혼용하지 않는다.

## 문서 적용과 후속 실행 순서

| 단계 | Task | 모듈·영향 범위 | 의존·시작 조건 |
| --- | --- | --- | --- |
| 문서 적용 | [TASK-RENT-DOC-001](../tasks/rental-spec-transition.md) | Spec·ADR·Plan·Task·원장·작업 규칙·README | 이번 사용자 요청 |
| 데이터 계약 | [TASK-RENT-DATA-001](../tasks/rental-data-contract.md) | 전월세 adapter·별도 rental storage·검수 위치/시설 입력·합성 fixture | 문서 적용; 원천 기술문서·단위·사용조건 검토, 실수집 없이 가능 |
| 추천·CLI | [TASK-RENT-REC-001](../tasks/rental-recommendation-cli.md) | 추천 validation/선택/필터/순위·CLI·Tool | 합성 rental 스냅샷과 데이터 계약 |
| 암호화 API 키 보관함 | [TASK-CRED-001](../tasks/api-credential-vault.md) | loopback 설정 UI/API·암호문 저장·Windows Credential Manager·폴더 cascade | 추천·CLI 계약; 키 저장소 오류·비노출·삭제 검증, 외부 호출 없음 |
| 로컬 웹 | [TASK-RENT-WEB-001](../tasks/rental-web-demo.md) | HTTP 진입점·정적 화면·README | 공통 추천 인터페이스와 CRED-001 설정 앱 기반 |
| 설명·평가 | [TASK-RENT-LLM-001](../tasks/rental-explanation-evaluation.md) | 선택형 로컬 설명·근거 검증·제품 평가 | 모델 없는 추천·웹 비교 |
| 실데이터 | [TASK-RENT-REAL-001](../tasks/rental-real-data.md) | 승인된 수집·단지/좌표/시설 매칭·사람 검수 Golden | 사용자 보류 해제·API 활용 승인·자료 사용조건·데이터 계약 |

현재 보관함 제품 코드는 구현했고, Task 상태는 in_progress다. 암호화·관리 API·폴더 삭제·비밀값 비노출 테스트는 통과했으며, 자동 실행 환경에 Windows 로그온 Credential Manager 저장 세션이 없어 native key round-trip 확인이 남았다. 나머지 합성 구현 Task는 draft, 실제 자료 Task는 blocked다. 동일 storage/Tool/CLI 경계를 공유하므로 순서대로 실행한다. 외부 CLI 리뷰·issue·push·PR·merge·배포·원격 동기화·전체 gstack 재설치는 이번 범위 밖이다. 기존 작업 파일의 변경을 되돌리거나 대신 완료하지 않는다.

## TARGET 데이터·사용자 흐름과 실패 처리

```text
사용자가 API 키·별칭·폴더 입력
  → Windows Credential Manager 보호 키 + 별도 사용자 로컬 SQLite 암호문
      ├ 보안 저장소 불가/암호화 실패 → fail-closed; 평문 fallback·외부 호출 없음
      └ 저장 → 별칭·폴더만 UI에 재표시; 키 등록만으로 외부 API를 호출하지 않음

원천 기술문서 + 승인된 원본 / 합성 fixture
  → 원본·단위·기간·매칭·커버리지 검수
      ├ 실패/미확인 → 격리·원인 기록; 추천 스냅샷 승격 금지
      └ 통과 → 별도 불변 rental 스냅샷

웹 입력 / CLI / 허용 recommend_rentals
  → 타입·위치·지원 조건 검증
      ├ 오류 → 명시적 오류; 후보 생성 금지
      └ 통과 → 유형·면적·12개월 → 단지별 최신 계약 → 같은 계약의 두 예산
          → 필수 met만 통과 → 선호 met/unmet/unknown → 정해진 순위·기본 설명
              ├ 0건 → no_match; 조건 자동 완화 금지
              ├ 1~2건 → 있는 후보만 비교
              └ 후보 → 출처·거리 종류·관측일·누락 비용과 비교표
                  └ 선택형 로컬 LLM 설명
                      ├ 오류/무근거/변경 → 기본 설명
                      └ 검증 통과 → 같은 후보·순위의 설명
```

| 실패 경로 | 사용자 동작·처리 | 검증 연결 |
| --- | --- | --- |
| 최근 계약이 예산 초과, 과거 계약만 저렴 | 제외; 과거 가격을 현재 가능한 가격으로 제시하지 않음 | AC-02/03 |
| 좌표·시설 커버리지·매칭 부족 | 필수 제외·선호 미확인, 자료 없는 상태 표시 | AC-04/05/07 |
| 없는/미검수 스냅샷·DB 오류 | 준비 안 됨/오류; 정상 0건과 구분 | AC-08 |
| 원천 ID·취소/정정 정보 없음 | 관측 키·미확인 표시; 자동 버전 연결 주장 금지 | AC-07 |
| 모델 오류·수치/조건/출처 변경 | 기본 설명; 추천 자체는 실행 | AC-09 |
| 오래된 스냅샷·합성 자료 | 기준일·수집일·관측 기간·합성 표시; 실시간/실측 주장 금지 | AC-07/10 |
| OS 키 저장소 잠김·없음·복호화 실패 | 키 저장·사용 요청을 fail-closed 처리; 평문 저장·fallback·API 호출 금지 | CRED-001-AC-02/03/05 |
| API 키 폴더 삭제·DB 오류 | 확인 후 전체 cascade 삭제하거나 트랜잭션 전체 rollback | CRED-001-AC-04 |

재사용은 기존 원본 수집의 키 비노출·페이지/해시 기록, SQLite·파라미터 SQL·인자 검증·CLI·평가다. 전월세 필드 매핑, 시설 importer, 거리·조건·순위, 웹, 설명 검증은 신규이며 구현된 것으로 표시하지 않는다.

성능은 유형·기간·면적의 SQL 필터와 단지별 대표 선택 후 거리·선호 계산을 수행한다. 내부 후보 검색에 현재 Tool의 20행 출력 상한을 먼저 적용해 전체 순위를 왜곡하지 않는다. 최종 결과만 20행으로 제한한다. 개별 후보마다 외부 API를 호출하는 방식은 피하고 검수 스냅샷을 사용한다. 실제 p95·메모리·커버리지는 후속 구현에서 측정한다.

## product-verification-pending

추천 AC-01~06은 합성 스냅샷의 결정적 추천·CLI에서 검증했으며 [TASK-RENT-REC-001](../tasks/rental-recommendation-cli.md#validation)에 실제 결과를 기록했다. 아래 표는 해당 시나리오와 아직 남은 실제 원천·웹·모델 검증 계획이다. CRED-001은 별도 Task에서 구현·테스트 중이고, native Credential Manager round-trip 확인만 남았다. 보관함 완료를 추천 품질이나 실데이터 평가로 승격하지 않는다.

| AC | 수동 검증 절차·예상 결과 | 잡아낼 회귀·검증 경계 |
| --- | --- | --- |
| RENT-001-AC-01 | 서울/외 지역·0/1/2/5/20 후보 fixture; 부족하면 그대로, 매물 보장·총주거비 표현 없음 | 후보 생성/완화·상한 초과; 공통 추천·CLI, 웹 parity는 AC-08 |
| RENT-001-AC-02 | 예산 같음/1원 초과·0·누락·bool 및 서로 다른 계약의 각 최저 금액 fixture | 단위·상한·가짜 계약 쌍; 추천 공개 경계 단위 검사 |
| RENT-001-AC-03 | 최신 고가/과거 저가·유형/면적/기간 불일치·미래·월말·동일 날짜 fixture | 예산 필터 후 과거 선택/동률 흔들림; storage+추천 통합 |
| RENT-001-AC-04 | 반경 같음/초과·필수 unknown/unmet·미확정 직장/좌표 fixture | 미확인 통과·직선거리를 시간으로 변환; 계산·입력 검사 |
| RENT-001-AC-05 | 시설 커버리지 부족·선호 unknown·미지원 필수/선호 fixture | 없음과 미확인 혼동·조용한 조건 무시; 구조화 추천·CLI, 웹 표시는 AC-08 |
| RENT-001-AC-06 | 선호/거리/날짜/ID 동률·직장 unknown·중복 조건으로 같은 요청 반복 | 비결정적 순위·중복 점수; 추천 공개 경계 |
| RENT-001-AC-07 | 원본 행 역추적·동일 값의 별개 관측·누락 원천 ID/상태/날짜·최신/역사 격리 검사 | 원천 사실 위조·역사 오염; 적재 통합 및 수동 검수 |
| RENT-001-AC-08 | 같은 CLI/POST 요청·잘못된 입력·없는 데이터·DB 오류·로딩/0건/부분 비교 | 각 진입점 계약 차이·오류를 정상 빈 결과로 변환; E2E |
| RENT-001-AC-09 | 모델 없음/장애/타임아웃·금액 역할/거리/조건/순위/출처 조작 응답 | 모델 의존 추천·무근거 설명; fake 응답 계약+실제 모델 별도 eval |
| RENT-001-AC-10 | 기존 46개 검사·역사 CLI와 cutoff 재실행, 합성/실데이터 결과·미측정 상태 확인 | 역사 회귀·합성 성능 승격; 회귀+사람 Golden 별도 |

미검증 수집 스냅샷은 화면에 내보내지 않는다. 실제 Golden은 후보 적합성·필수 충족·순위·가격 쌍·날짜·거리 종류·누락·출처를 사람이 검수한다. 기존 약 200건 매매 Golden 수량을 새 전월세 평가의 승인된 수량으로 상속하지 않는다.

## 문서 검증·발견성과 완료

문서 AC-11과 CRED-001-AC-06은 README/AGENTS에서 신규 Spec·Plan·ADR·Task를 찾을 수 있고 CURRENT/TARGET·보류·원장 연결이 일치해야 한다. 검사:

```sh
python -X utf8 scripts/check_sdd.py
python -X utf8 scripts/verify_environment.py
python -X utf8 scripts/check_sdd.py --base origin/main
```

실행 결과는 [문서 Task](../tasks/rental-spec-transition.md#doc-validation)에 기록한다. 문서 완료와 신규 제품 구현·모델 품질·실데이터 평가 완료는 분리한다. 실제 적용·검증 이전에는 완료로 표시하지 않는다. 배포 채널은 팀의 기존 로컬 Python 환경이며 외부 서비스·CI 배포는 만들지 않는다.

## 자격증명 보관함 추가 기록 — 2026-10-06

사용자가 API 키 등록 시 암호화 저장, 공급자별 복수 키와 키별 별칭, 분류 폴더 및 폴더 삭제 시 포함 키 연쇄 삭제를 추가 요청했다. 암호화 키 보관 대안에서는 Windows 계정에 묶인 OS 자격 증명 저장소를 선택했다. 이를 CRED-001과 ADR-004로 분리해 RENT-001의 추천·거래 데이터 계약과 책임을 섞지 않는다. 인증값은 Windows Credential Manager로 보호되는 키로 AES-256-GCM 암호화해 사용자 프로필 아래 별도 SQLite에 둔다. 등록·수정·삭제는 외부 호출과 결제 설정을 일으키지 않고, 실수집 보류도 유지한다.

## 보관함 구현 업데이트 — 2026-10-06

`jipdam credentials`가 Windows loopback 설정 화면을 띄우고, 공급자별 키 여러 개·별칭·폴더·교체·개별 삭제·확인형 폴더 cascade를 제공한다. AES-256-GCM 암호문은 `%LOCALAPPDATA%\Jipdam\credentials.sqlite3`에 저장하며 master key는 Windows Credential Manager에 둔다. 관리 서버는 loopback Host·Origin·CSRF를 확인하고, 키 원문은 목록·HTTP 응답·브라우저 영속 저장소에 넣지 않는다. 테스트 자동 실행 세션은 Credential Manager `CredWriteW`에서 오류 1312를 반환했으므로, 사용자 로그온 세션에서 합성 키 저장·읽기·삭제를 확인할 때까지 CRED-001-AC-02를 미완료로 유지한다. 실제 공급자 API 호출·쿼터 활성화·실데이터 수집은 수행하지 않았다.

## 리뷰와 결정 기록

범위는 사용자가 승인한 전환 문서와 후속 Task다. 구조 축소는 D7의 새 Spec 중심 연결, D14의 Python 단일 앱으로 결정했다. 모든 제품 요구는 확정 답변/최종 적용 요청에 연결했고 추가 공급자·실수집·외부 비용은 승인하지 않았다. Approval readiness: PASS — D1~D15와 최종 적용 요청의 문서 범위.

Architecture: 2023 선행 순서·최신/역사 혼합·실거래/매물 혼동을 새 계약과 경계로 보완. Code quality: 기존 helpers·CURRENT 재사용, 금액 쌍·관측 키·오류 의미를 명시. Tests: 위 경로별 시나리오를 정의하고 기존 검사와 신규 미실행 제품 검증을 분리. Performance: DB 필터 선행, 최종 출력 상한과 내부 후보 수 구분, 후보별 외부 호출 없이 스냅샷 재사용. 모두 계획 검토이며 미래 코드 성능·품질을 측정한 결과가 아니다.

이전 office-hours 내부 독립 검토는 SDD 적용 범위, 최신 계약 우선, 관측/취소 상태 구분, 결과 부족·미지원 조건, 문서/제품 검증 분리를 지적했고 계약에 반영했다. 적용 문서 독립 검토에서는 REC Task가 후속 웹 E2E를 완료 조건으로 요구하는 P2 1건을 찾았다. AC-05는 구조화 결과의 조건 상태, AC-08은 WEB Task의 HTTP·화면 검증으로 정리해 순차 실행을 가능하게 했다. 수정 후 같은 검토자의 읽기 전용 재확인에서 추가 이슈는 없었다. 외부 CLI 리뷰는 실행하지 않았다.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
| --- | --- | --- | --- | --- | --- |
| CEO Review | — | 제품 전략 | — | 별도 미실행 | office-hours에서 팀 발표 데모와 범위를 확인 |
| Outside Review | office-hours/적용 문서의 내부 독립 검토 | 계약·작업 순서 일관성 | 계획 1회, 적용 1회와 재확인 1회 | 내부 검토 완료; 외부 CLI skipped | 계획 경계 보완, Task 순환 의존 P2 1건 수정·재확인 |
| Eng Review | `/plan-eng-review`와 승인 문서 적용 검토 | 구조·데이터·테스트 계획 | 1, CRED 추가 전 | 기존 RENT 계획만 검토; CRED-001 추가는 미검토 | 최신 계약·예산 쌍·미확인·결정적 순위·역사 격리; 이번 보관함 추가의 독립 Eng Review는 수행하지 않음 |
| Design Review | — | UI 상세 설계 | — | 후속 | 최소 입력·후보 비교, 오류·빈 결과·부분 결과의 범위만 확정 |
| DX Review | — | 개발 경험 | — | 별도 미실행 | 기존 CLI·검증 진입점 재사용 |

**OUTSIDE COVERAGE:** host=codex, source=in-host, outside_provider=claude-code, outside_status=skipped, phase=plan-review. 내부 독립 검토이며 외부 CLI 완료나 외부 coverage를 주장하지 않는다.

**VERDICT:** 기존 RENT 계획 검토는 CRED-001 추가 전 기준이며 이번 보관함 추가를 검토하지 않았다. 이번 변경은 사용자가 결정한 보안 요구를 Spec·ADR·Task로 반영하며 신규 제품 구현·실제 API 호출·실데이터 추천 품질 완료를 뜻하지 않는다. 이번 문서 검증은 [보관함 SDD Task](../tasks/credential-vault-sdd.md#doc-validation)에 기록한다.

NO UNRESOLVED DECISIONS

## 2026-10-13 MVP 범위 확장 및 실행 계획

이번 사용자의 확정 요구는 채팅형 조건 수집, LLM 추가 질문, 실제 로컬 DB 기반 추천, 후보 목록과 두 개의 상세 페이지(니즈 비교 / 전체 데이터), 좌표가 있을 때의 지도, 측정 가능한 DB 성능 기준이다. 기존 D12의 간단한 입력·비교 화면과 “지도·대화 제외”는 이 날짜의 확정 요구로 대체한다. 기존 RENT-001 검증·단위·출처·미확인 규칙, Python 단일 앱, SQLite, loopback 보안 경계는 유지한다.

### 데이터 준비 상태 감사와 확정 정책

읽기 전용 감사 기준 DB: `data/collection/molit-seoul-three-api-20261012-restored-20261013/canonical-v2-growing-20261013/canonical.sqlite3`.

| 항목 | 2026-10-13 관측 | 제품 처리 |
| --- | ---: | --- |
| 전체 canonical observations | 374,892 | 성능 고정 기준 |
| 전월세 observations | 238,620 (전세 119,631 / 월세 118,989) | 실제 데이터 조회 대상 |
| `pending` 전월세 match candidates | 271,299 | 추천 후보로 쓰지 않음 |
| `observations.complex_id`가 연결된 전월세 | 0 | 승인된 실제 추천 결과 현재 0개 |
| 실제 canonical 좌표 필드/단지 시설 행 | 없음 | 지도/시설은 미제공 상태 표기 |
| `data/rental/.../serving.sqlite3` | 합성 거래 3, 단지 3, 시설 0 | 실제 데이터로 자동 대체 금지 |

사용자는 **확정 매칭된 단지만 추천**하도록 선택했다. 현재 실제 DB의 결과는 빈 추천 성공이 아니라 `data_not_ready`이며, 격리된 관측·pending 후보는 별도 데이터 준비 상태로 설명한다. 후보 자동 확정·문자열 유사도 매칭·거래 병합은 실행하지 않는다. 실제 좌표가 새로 제공되어도 검수 승인 전에는 지도에 올리지 않는다. 이 초기 계획에서는 외부 타일을 별도 승인으로 두었다. 이후 사용자 D1/D2와 실행 요청으로 Leaflet+OSM 내장 지도·지도 보기에서의 타일 요청을 승인했으며 2026-10-14 실행 계약이 적용된다.

### 아키텍처와 작업 순서

```text
채팅 UI
  → loopback 대화 endpoint
      → 로컬 LLM: 다음 확인 질문과 구조화 초안만 생성
      → 사용자 확인 + 기존 rental request validator
          → 설정된 실제 canonical DB read-only query
              → confirmed complex links만 선별
                  → deterministic ranking + query evidence
                      ├ 후보 결과 → 니즈 비교 페이지
                      └ 후보 상세 ID → 전체 DB 데이터/출처 페이지 + 좌표 있으면 지도
```

1. `TASK-RENT-MVP-001`에서 1.76 GB canonical 원본 DB를 읽기 전용으로 열고, 추천에 필요한 실제 전월세 typed 필드·출처 계보만 담은 별도 인덱스 serving DB를 생성한다. 원본 canonical 파일은 수정하지 않는다. serving DB 경로를 설정화하고 confirmed link 전용 쿼리 및 `data_not_ready`/`no_match` 구분을 API 계약에 넣는다. 합성 데이터는 명시적 demo 설정에서만 사용한다.
2. 사용자 메시지·assistant 질문·확정 구조화 조건으로 구성된 메모리 내 대화 세션을 구현한다. 기존 로컬 Ollama 런타임만 호출하고 4B 모델은 누락 슬롯 질문과 JSON 초안을 제공한다. 서버가 타입/범위/좌표를 검증하고 사용자 확인 전에는 추천을 실행하지 않는다. 모델 장애 때 입력을 유지하며 정적 확인 양식으로 전환한다.
3. 기존 loopback 서버 경계를 재사용해 chat, recommendations, candidate-detail endpoint를 추가한다. DB는 `mode=ro`로 열고 SQL은 파라미터화한다. 후보 상세는 명시적인 필드 카탈로그와 출처·기준일을 반환하고, 행/거래 provenance 링크를 제공한다.
4. 정적 화면을 채팅, 결과/니즈 비교, 전체 데이터 상세(지도 포함)로 연결한다. 지도는 로컬 렌더러에 검수 WGS84 좌표만 전달한다. 현재 DB에는 좌표/시설이 없으므로 빈 지도와 데이터 준비 메시지가 실제 동작이다.
5. 실제 canonical DB를 변경 없이 읽으며 성능 계측을 100회 수행한다. 대표 request, 평균/중앙값/p95, DB 크기·행 수·SQLite 버전·query plan을 기록한다. 목표는 warmed backend read p95 ≤ 500ms다. 미달 query에만 좁은 인덱스를 설계하고, 기존 불변 DB를 수정하지 않고 별도 재생성/serving 사본에 적용한다.
6. HTTP/API contract, 대화 질문, confirmed-only/data-not-ready, 상세 필드 계보, 지도 좌표/좌표 없음, 기존 역사·credentials 호환과 성능 목표를 검증한다. 성능 AC는 actual query 결과와 함께 기록하며 model latency를 DB latency에 섞지 않는다.

### 데이터 계약과 실패 동작

- 기본 경로는 실제 canonical에서 재생성된 compact serving DB다. canonical 입력과 serving 출력 경로를 명시하고 원본은 read-only로만 연다. serving 파일이 없거나 schema/source batch가 다르면 fail-closed하고, 합성 DB로 조용히 대체하지 않는다. 정상적으로 열린 DB에 confirmed 전월세 링크가 0건이면 `data_not_ready`; 입력은 유효하지만 확정 후보가 없으면 `no_match`다.
- 매칭은 `review_status='confirmed'` 및 근거를 가진 링크만 사용한다. 한 원본 거래를 두 단지에 중복 연결하지 않는다. query 결과는 원본 `observation_id`의 계약 금액·면적·날짜 및 dataset/batch provenance를 반환한다. 집계가 필요해도 원본 관측은 병합/덮어쓰기하지 않고 결과 화면에서 그룹 출처를 모두 열거한다.
- canonical DB schema에는 단지 위경도와 시설 테이블이 없으므로 이 DB에서 역/공원/병원 조건은 `unknown`이다. 필수 거리 조건은 후보를 무리하게 통과시키지 않고 `data_not_ready` 또는 확인 요청이 된다. 외부 지오코딩·시설 조회는 실행하지 않는다.
- detail field catalogue는 `dataset_id`, `kind`, typed columns, unit, label, source/validity and provenance keys를 매핑한다. 임의 원문 payload를 브라우저로 반환하지 않는다. 새 데이터는 catalogue에 명시 추가하고 version을 남긴다.
- 대화는 현재 로컬 프로세스 메모리에서만 유지한다. 로컬 LLM에 DB 조회 권한이나 사용자 키를 보내지 않는다. 이름/직장 입력은 로그·SQLite 대화영속 저장에 남기지 않는다.
- 조회 성능은 SQL 선별 시간, 응답 구성 시간, 전체 endpoint DB 소요시간을 분리한다. serving DB에 `kind/region/date/area` 검색 인덱스와 `complex_id/contract_date` 최신 거래 인덱스를 추가하고 query plan을 기록한다. 100회 동일 payload, 첫 5회 워밍 후 다음 100회를 보고하며 p50/p95를 기록한다. 데이터 적격성 0건도 빠른 응답으로 별도 보고하고 그 사실을 추천 완료로 취급하지 않는다.

### 미완료 게이트

현재 실제 DB에는 confirmed 전월세 링크가 없다. 따라서 실제 추천 콘텐츠·지도 표식·생활시설 비교의 제품 유효성은 사람 검수 매칭, 좌표·시설 자료의 승인된 입력 후 검증해야 한다. 이번 코드는 실제 추천 경로와 올바른 `data_not_ready` 상태를 구현할 수 있으나 현재 DB로 실제 추천 품질을 주장할 수 없다. 실수집·새 출처·좌표/시설 확보·외부 지도 타일·자동 매칭은 이 계획의 범위에 포함하지 않는다.

### 2026-10-13 구현 진행 및 실제 계측

`TASK-RENT-MVP-001`에서 루프백 UI/API, allowlist draft, confirmed-only read-only serving query, 명시적 verified 좌표 게이트, 확장 가능한 상세 필드 카탈로그를 구현했다. 단지별 최신 관측 선택은 SQL `ROW_NUMBER()`로 수행하고, budget은 최신 관측 선택 후 적용한다. Python에 후보 전체 행을 로드하지 않고 serving partial index를 사용한다. 상세 관측은 100행 페이지로 읽는다.

실제 238,620건 전월세 projection을 읽어 readiness endpoint 100회 p95 29.352ms, confirmed-only CTE 후보 조회 100회 p95 0.357ms를 계측했다. CTE의 실제 반환 건수는 매회 0이며 EXPLAIN은 `rental_complex_latest` 검색을 보였다. 이 수치는 현재 DB 상태의 성능 검증이지, 후보가 존재할 때의 실제 추천 성공/결과 정렬·상세 지연 검증은 아니다. 자세한 측정값, 환경, 테스트와 남은 게이트는 [검증 기록](../rental-mvp-validation-20261013.md)에 있다. 실모델과 브라우저 QA, verified match·좌표·시설 자료는 아직 없다.

## 2026-10-14 사용자 승인 실행 계획

사용자의 PLEASE IMPLEMENT THIS PLAN을 실행한다. D1 내장 지도, D2 Leaflet 1.9.4+OpenStreetMap, D3 별도 어댑터·공통 순수 판정. T1 검수 관계/좌표/시설/커버리지·manifest·해시·카탈로그를 포함하는 선택형 review package와 serving v2 → T2 latest-before-budget·필수/선호·순위·RTree → T3 로컬 모델 초안/확인/수정/제거/복구 → T4 후보별 니즈·100행 상세·내장 지도 → T5 5회 워밍업/100회 추천·상세와 회귀 → T6 Runtime/Spec/Task/원장 동기화.

필수 met만 통과하며 선호 unknown은 유지한다. 최신 계약은 날짜/관측ID 내림차순, 순위는 선호 충족/직장거리/계약일/단지ID. 최종 조건 판정 이전 LIMIT 금지. HTTP 400 입력, 503 DB 오류, 200 data_not_ready, 404 존재하지 않는 후보만. 원본 불변·검수 근거 필수·합성 명시·지도 보기에서만 타일 요청. 기능 검증과 실제 데이터 검증을 별도 기록하고 실제 확정 연결 0건의 빠른 응답만으로 Goal을 완료하지 않는다. 상세 계약과 이유는 RENT-001 revision5와 ADR-009를 따른다.

현재 T1~T6 구현·회귀·합성 지도/성능 증거는 TASK-RENT-MVP-001에 기록했다. 실제 확정 자료/좌표/시설 및 실모델은 사용자 답변대로 준비 조건이며 실제 성공 경로 p95를 별도 검증한다.

2026-10-14 재개 지시로 GMS budgeted runner를 사용해 검수 패키지 날짜 경계 테스트 초안을 만들고 로컬 검토·검증 후 적용했다. 개발 초안만 GMS에 제공하며 실제 추천용 로컬 모델은 기존 계약을 유지한다. 현재 runner는 승인된 `gpt-6.1-sol` 고정 모델/요율을 사용했다. 사용자가 허용한 난이도별 LUNA 선택은 지원 모델·요금 확인 후 사전 카운트·최대 비용 예약까지 모델별로 연결해야 한다. 실제 사용·잔액·최종 검증은 [검증 기록](../rental-mvp-validation-20261013.md#2026-10-14-최종-재검증)에 남겼다.
