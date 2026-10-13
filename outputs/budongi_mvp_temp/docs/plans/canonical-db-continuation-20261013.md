# 통합 DB 후속 실행 제안 — 2026-10-13

상태: **후속 범위 사용자 승인, 구현·실제 통합 검증 완료**. 최신 판정은 [Task](../tasks/canonical-integration.md)와 [Goal 완료 감사](../canonical-validation-20261013.md#goal-completion-audit)를 따른다. 아래 계획·사전 점검·리뷰는 실행 전 근거를 보존한 기록이다. 사용자가2026-10-13 “후속 통합 계획대로 진행 (추천)”을 선택했다. 원래 통합 DB Goal을 축소하거나 이번 문서 작성으로 완료하지 않는다. 관련 기존 실행 단위는 TASK-MOLIT-001이며 후속 구현은 독립 Spec·ADR·Task로 연결한다.

## 현재 확보한 기반

서울25구·202510~202610·세 API의975 query와 원본384,211행, 유효관측374,892행이 보존되었다. 원본 XML, 출처별 전월세/매매 DB, staging, manifest, 복원 ZIP을 입력으로 사용한다. 실제 추천·검수 단지·좌표·시설·새 데이터셋 수집·Drive 업로드는 현재 승인 범위 밖이다. 당초 GitHub 연결앱403은 사용자 CLI 로그인 후 해소했다. 2026-10-13 최종 수집 결과를 CLI로 게시하고 본문을 대조했다. 아래 미완료 점검은 구현 시작 전의 기록이며 최신 상태는 통합 Task와 검증 기록을 따른다.

현재 실행 계정에서 기존 `db/` 경로의 직접 읽기가 거부되어 원본 ZIP 해시를 먼저 검증하고 새 복원 경로에서 원본/DB 접근을 검증한다. 접근 실패를 데이터 손상이나 파일 삭제로 판정하지 않고 기존 파일·ACL을 변경하지 않는다. 복원 검증 결과는 별도 재개 감사 문서에 기록한다.

## 제안하는 다음 완료 범위

1. 기존 XML 세 출처의 유효관측 전부를 단일 관계형 canonical DB에서 조회한다. 전월세/매매 독립 관측 DB와 원본은 유지한다.
2. 공통 출처·배치·행정구역·원본·관측·단지·건물·주소 엔터티와 출처별 ID→내부 ID 매핑을 정의한다. 실제 공식 ID가 없는 건물/주소 연결은 미확인으로 두며 값을 생성하지 않는다.
3. 제공된 공식 출처 ID로 근거가 확인된 관계만 연결한다. `aptSeq`는 출처의 단지 ID로 보존하고 거래 ID로 사용하지 않는다. 식별자 유효 범위/지역 충돌을 검증한다. 이름·동·지번 조건은 후보 관계로만 보관하고 확정 FK에 자동 승격하지 않는다.
4. 동일 배치 재적재·다른 배치 증분 적재·정규화 버전 재적재의 규칙을 구현한다. 원본 콘텐츠와 배치에서의 관측 이력을 구분하고, 실제 서로 다른 계약을 값 유사성으로 합치지 않는다.
5. CSV·JSON·XLSX 어댑터가 동일한 원본/행위치/정규화/거부 사유 계약을 따르도록 연결한다. Source Registry에 승인된 출처만 실제 적재하며 현재 확정 출처는 XML 세 개다. 파일 어댑터의 합성 계약 테스트를 실제 신규 파일 데이터 수집 성공으로 보고하지 않는다.
6. 실제 서울 원본으로 DB 건수·무결성·조인·재실행·증분 동작을 검증하고 Goal9조건의 증거를 갱신한다.

이 범위의 실제 ID 연결·후보 관계 생성은2026-10-13 계획 승인으로 별도 해제되었다. 좌표·시설·추천·외부 수집으로 범위를 확대하지 않는다. 신규 파일 출처의 실제 적재는 Source Registry의 별도 출처 승인/범위 확정을 요구한다.

## 현재 코드에서 확인한 미완료 조건

이 항목은 읽기 기반 점검이며 실행으로 재현한 회귀 결과가 아니다. 검토 대상은 기존 미추적 `collection_integrate.py`, `source_files.py`, CLI의 integrate 진입점이다.

- `integrate_collection`은 새 출력만 생성하고 batch 한 개를 가정한다. 기존 canonical에 새 배치를 추가하는 경로·다중 배치 원본 소속 관계가 없다. 단일 observation/file PK로 재사용 원본의 배치별 이력을 표현할 규칙이 필요하다.
- 정규화 manifest의 배치/버전/DB 파일 해시만 검사한다. `plan_sha256`, 현재 완료 query 집합, `raw_input_hashes`의 대사를 통합 진입점에서도 공유해야 한다. 합계가 같아도 원본 범위가 바뀐 입력을 거부해야 한다.
- 단지/주소/후보 관계를 생성하는 기존 경로는 실제 매칭 보류 경계에 걸린다. 검증되지 않은 기존 코드가 CLI에 있다는 사실은 실행 승인이 아니다.
- 같은 이름·동·지번의 관측끼리 후보를 생성하는 SQL은 전체 거래 행끼리 조인한다. 단지별 증거를 먼저 요약하여 후보 생성량과 조인 비용을 제한해야 한다. 후보 근거의 손실이나 이름만으로 확정하는 동작은 허용하지 않는다.
- 파일 경로는 현재 staging만 생성하며 canonical 적재로 이어지지 않는다. JSON 중첩값, XLSX 시트/빈 시트·선택 제외, 정확한 날짜·원 단위·필수 공백·결측 정책을 계약화해야 한다.
- 파일 관측 키의 시트 이름을 슬래시 치환으로 만드는 규칙은 서로 다른 이름이 같은 문자열이 될 수 있다. 섹션의 원래 식별자와 행 위치를 구조적으로 보존해야 한다.
- 파일 expected_rows 불일치가 `complete=false`로만 남는 현재 동작과 일반 통합의 전체 완료 기본 정책을 연결해야 한다. 행 사유·섹션별 예상/실제 건수·공식 제외 조건을 기록한다.
- 공통 building 엔터티, 출처 유효기간과 수집 이력의 구분, 다중 출처의 식별자 충돌·모호성 정책과 테스트는 아직 없다.

## 제안 데이터 흐름·식별 규칙

```text
등록 출처 + 승인 범위 + 보존 XML/CSV/JSON/XLSX
  -> 콘텐츠 해시 검증 + 배치/기간/시트/페이지 커버리지
  -> 원본 콘텐츠 / 배치별 원본 소속 / 행별 staging
  -> 버전 명시 정규화 / 유효·제외·거부 및 건수 대사
  -> canonical 관측 + 배치 소속 + 출처·행정구역 FK
  -> 공식 출처 ID 근거의 엔터티 / 명시적인 관계 근거
  -> 미확정 후보는 별도 관계표(pending, confidence, evidence)
  -> 실제 SQL/무결성/반복·증분 검증 및 품질 보고
```

콘텐츠 SHA는 불변 원본의 식별자다. 출처별 관측 키는 출처·원본 참조·해시·행/섹션 위치와 정규화 버전을 명시한다. 기존 두 관측 DB의 ID는 원본 추적용으로 유지하고 새 통합 키와 매핑한다. 콘텐츠/동일 관측을 다른 배치에서 재사용할 때 배치 소속 이력을 별도 보관한다. 다른 행 위치의 동일 값은 다른 관측으로 유지한다. 다른 해시/수집 버전의 비슷한 관측은 실제 동일 계약의 수정으로 자동 연결하지 않는다.

계약일, 제공기관 기준일·유효기간, 실제 수집시각, 배치 기준일, 적재시각은 서로 다른 필드다. 원천이 제공하지 않는 유효기간/정정일은 NULL로 두고 수집일로 대체하지 않는다. 공식 ID가 같지만 지역/핵심 엔터티가 충돌하면 격리하고 확정 연결을 중단한다.

## 구조 선택 제안

권장: 기존 `collection_integrate.py`가 canonical 저장/조회/검증을, `source_files.py`가 파일 보존/행 읽기/매핑을 담당하고 `collection_cli.py`가 명령을 연결한다. 기존 `collection.py`, `collection_db.py`, rental 저장 계약의 검증/정규화는 재사용한다. 새 DB 서버·ORM·백그라운드 작업·외부 CLI 리뷰를 도입하지 않는다.

대안: 파일 읽기/매핑을 collection_integrate 한 모듈로 합쳐 모듈 수를 줄인다. 같은 기능·오류·검증 범위를 유지하지만 XML 통합과 파일 입력의 결합이 커진다. 확장 목표에는 기존 두 모듈의 책임을 나누는 권장 구조가 적절하다.

예상 변경: 구현/CLI3파일, 계약테스트2파일, Spec/ADR/Task/Plan/현재Task/traceability/사용문서7파일 이상. 새 기능 요구는 CANONICAL-001 초안으로, 결정은 ADR-006 초안으로, 실행은 TASK-CANONICAL-001 초안으로 연결한다. 확정하지 않은 이름/경로는 후속 리뷰에서 조정할 수 있다. gstack-plan-eng-review의 복잡도 선택/구조 질문은 이 실제 범위로 수행하고, 리뷰 완료와 승인 전에는 구현을 시작하지 않는다.

## 실행 순서·검증 증거

1. 사용자와 위 실제 ID 연결/미확정 후보 범위 및 구조를 확정한다. 승인 경계를 AGENTS·Spec·ADR·Task에 기록하고 gstack-plan-eng-review의 구조·코드품질·테스트·성능 검토를 완료한다.
2. 원본/정규화 manifest 공통 대사와 배치 소속 모델을 구현한다. 같은 batch/version/hash 재실행은 신규0, 같은 batch ID로 다른 입력은 거부, 새 배치는 별도 이력, 실패는 전체 rollback.
3. 관측/행정구역/공식 ID 관계와 미확정 후보를 구현한다. 이름만 같은 다른 단지, 공식 ID 충돌, NULL 주소, 서로 다른 동일 값 행, 일반/상세 거래 분리를 검증한다.
4. 등록 파일 소스→staging→canonical을 연결하고 CSV·JSON·전체 XLSX 시트, 잘못된 날짜/단위/공백/시트 식별 충돌/건수 불일치/원본 변조를 검증한다. 새 실제 파일 출처는 별도 등록 없이는 사용하지 않는다.
5. 종로구 기존 실제 입력으로 무네트워크/무키 시범을 통과한 뒤 전체 유효374,892행과 원본384,211행을 대사한다. 출처별 건수·SQL 조인·PK/FK/UNIQUE/NOT NULL/CHECK 검증과 재생성 결과를 기록한다.
6. 실제 보존 배치/시범 원본의 겹치는 범위를 이용해 재적재/증분 처리의 이력과 관측수를 검증한다. 기존 원본 재사용 시험과 실제 새 시점 API 갱신을 구분한다. 새 갱신 수집은 이번 단계의 필수 선행 작업으로 추가하지 않는다.
7. 환경·SDD 검사 및 AC별 증거, 사용법/매핑/확장 예제/품질 한계를 갱신한다. 승인/접근/자료가 부족한 조건은 미완료로 보고하고 Goal 전체 완료를 선언하지 않는다.

## 위험·대응

| 실패 조건 | 필요한 처리·검증 |
| --- | --- |
| 원본 변조/최신 manifest와 DB 불일치 | 적재/pack 거부, 기존 출력 보존 |
| 같은 batch ID에 다른 데이터/매핑 | 새 배치 또는 새 정규화 버전 요구 |
| 공식 ID의 지역·주소 충돌 | 확정 연결 중단, 근거/사유 격리 |
| 라벨 후보 여러 개/필드 미확인 | 모두 미확정 상태, 확정 FK 자동 승격 금지 |
| 시트·페이지·기간별 누락 | 커버리지 불완전, 기본 완료 거부 |
| 정규화 필수 값/단위 오류 | 원문/행 위치/사유 유지, 공개 DB rollback |
| 기존 경로 접근권한 실패 | 검증된 ZIP에서 새 복원, ACL·기존 파일 변경 금지 |
| GitHub 결과 기록 쓰기 거부 | 기록문 수동 게시/연결권한 해결; 승인 없는 Git 인증 조회 금지 |

## 승인·리뷰 상태

범위/구조/필수 회귀 검증은2026-10-13 사용자의 전체 계획 진행 답변을 근거로 확정했다. GitHub연결앱403이후사용자가로그인된CLI사용을지시하여기존#5의결과게시/본문대조를완료했다. 게시방법추가입력은없다. 기존DB경로의직접접근제한은수정완료로표시하지않고검증된새복원경로를사용한다. 아래engineering review는구현계획점검결과이며전체구현/검증통과주장이아니다.

## Engineering review target and scope

Target/report: 이 Plan. Scope accepted as-is, FULL_REVIEW. 선택한 구성은 기존 collection_integrate/source_files/collection_cli의3모듈, 함수 기반 구현, 새 클래스0이다. 원래 구성과 파일입력을 통합 모듈에 합치는 대안은 위 구조 선택 제안에 비교했다. 사용자 전체 계획 승인으로 명시된 권장 구성과 요구/회귀 검증을 재사용한다. 임의 기능 축소/새 서비스/의존성 추가는 없다. 문서를 포함한 예상12개 이상 변경 파일은 알려진 복잡도이며 순차로 구현한다.

Scope Challenge: 공통 검증/정규화·SQLite·openpyxl을 재사용하고 새 ORM/서버/외부 수집은 추가하지 않는다. 기존 Task/검증 보고와 실제 복원 입력을 조사했다. 새 TOD0나 별도 제품 요구는 제안하지 않는다. 배포/공유 자동화는 현재 요청 범위 밖이며 로컬 Python CLI/SQLite 배포를 유지한다.

## Architecture review

- A1 [P1, confidence8/10] collection_integrate.py:78 — 한 배치/새 출력 가정은 증분 통합 요구를 충족하지 않는다. batch membership과 정규화 버전을 분리한다. 현재 증분 오류를 실행으로 재현했다는 주장은 아니다.
- A2 [P1, confidence9/10] collection_integrate.py:84 — 현재 통합 경로가 plan hash/raw input scope 대사를 하지 않는다. 승인된 실행순서2의 공통 검증을 pack/integrate 두 경로에서 사용한다.
- A3 [P1, confidence9/10] collection_integrate.py:145 — aptSeq/주소 연결과 후보 생성은 출처 namespace/지역 충돌/미확인 상태를 명시해야 한다. 신규 실제 매칭 범위는 현재 승인된 공식 근거 관계/후보에 한정한다.

## Code quality review

- Q1 [P1, confidence9/10] source_files.py:175 — 섹션 이름의 슬래시 치환은 식별자 충돌 위험이 있다. 원래 섹션과 행 위치를 구조적으로 키에 포함한다.
- Q2 [P1, confidence9/10] source_files.py:101 — 날짜 문자열 자르기와 필수 공백 문자열은 정확한 검증 계약을 보장하지 않는다. 원문을 보존하고 정확한 필드별 검증/사유를 정의한다.

Shared-code decision: 기존 pack_collection(collection_db.py:322)과 integrate_collection(collection_integrate.py:78)은 동일 원본/derived manifest 신뢰 경계를 공유한다. pack은 기록URL/ZIP출력 검사를 유지하고 integrate는 DB출력/통합 검사를 유지한다. 검증 helper를 collection_db에 한 번 두고 두 호출자가 결과(plan/status/normalized)를 받는다. 공통 검증 약25~35줄 이동, 통합 중복검사 약10~15줄 제거, 통합 현재원본 검증 약15~25줄 증가를 예상한다. 총 테스트/문서까지는 순증가하며 코드절감보다 stale 입력 차단의 일관성을 목적으로 한다. 기존 normalized/pack 회귀와 새 integrate 경계 테스트를 동시에 검증한다.

## Test review

Framework: 기존 Python unittest와 SQLite 임시 출력, CLI 통합 테스트를 유지한다. 새 프레임워크/LLM 평가/브라우저 테스트는 필요하지 않다. collection tests의 mapping/source-separation/stale-pack/rollback이 기존 경로를 보호하지만 현재 integrate/source_files의 통합/증분 테스트는 없다.

```text
collection integrate / file import [proposed user flow]
  -> registered source / input selectors
     -> missing/unapproved/duplicate/version conflict [GAP T1/T4]
  -> validate_normalized_inputs [proposed shared boundary]
     -> invalid archive / incomplete default / stale plan or raw scope [GAP T1]
     -> modified DB hash / malformed manifest [GAP T1]
  -> source staging / normalization
     -> XML parse/period/value checks [existing collection tests]
     -> file CSV/JSON/XLSX all declared sections [GAP T4]
     -> null/date/unit/blank/header/section collision [GAP T4]
  -> canonical transaction
     -> first batch / replay / new batch / version [GAP T2]
     -> same batch changed input / row failure / rollback [GAP T2]
  -> official ID links / explicit uncertain candidates
     -> namespace/region conflict / absent codes / ambiguity [GAP T3]
  -> quality SQL / lineage joins / publish
     -> count mismatch / FK/UNIQUE/CHECK / original integrity [GAP T5]
     -> concurrent output/error JSON/exit [GAP T6, CLI integration]
```

신규 검증6개 범주는 승인된 완료 조건에서 도출했다. GAP은 구현 대기이며 기존 커버리지로 세지 않는다. 폐기할 테스트는 없다. 필수 회귀는 기존 XML/파생DB 불변, 전체 완료 기본값/명시적allow-partial, stale pack거부, 동일 값 다른 원본 행 보존, 역사2023격리와 키 접근0이다. 승인된 계획 실행순서와 MOLIT 테스트에 명시된 계약을 유지하며 새 제품 정책을 추가하지 않았다.

## Performance review

- P1 [P1, confidence8/10] collection_integrate.py:176 — 관측 행끼리 label join은 중간 행이 크게 늘 수 있다. 공식 엔터티/label별 증거를 먼저 요약한 뒤 후보를 생성하고 원본 근거는 관계표에 보존한다. 이는 코드/규모의 추론이며 실행 시간 증거는 아직 없다.
- P2 [P2, confidence8/10] collection_integrate.py:120 — 행별 반복 파싱/조회 비용을 출처별 처리와 인덱스로 제한한다. 스트리밍 원문/단일 트랜잭션과 출처ID/배치소속/행 추적 인덱스를 유지한다. 실제 대규모 실행 시간과 query plan을 기록하고 전체 배치JSON을 한 번에 메모리에 올리지 않는다.

## Decision ledger

| ID | 확정 동작 | 상태·실제 승인 |
| --- | --- | --- |
| R1 | canonical엔터티/공식ID/미확정 후보, 거래 자동 병합 금지 | accepted, 2026-10-13 “후속 통합 계획대로 진행 (추천)”, 완료범위1~3 |
| R2 | 배치/정규화 버전/동일배치 반복 및 충돌 정책 | accepted, 같은 답변, 완료범위4와 실행순서2/6 |
| R3 | 등록 파일 형식 입력과 필드/section 검증 | accepted, 같은 답변, 완료범위5와 실행순서4 |
| R4 | 두 진입점에서manifest/raw scope 검증 공유 | accepted, 같은 답변, 실행순서2와 구조선택 |
| R5 | 기존 회귀/실제SQL/전체/증분/CLI 검증 | accepted, 같은 답변, 실행순서5~7과 MOLIT계약 |
| R6 | 기존 모듈 책임 분리, 원본/역사데이터와 권한 보존 | accepted, 같은 답변, 구조선택과 위험표 |

Approval readiness: PASS, R1~R6의 승인된 동작을2026-10-13 실제 계획 승인에 연결했다. 새 미승인 보완 결정은 없다. GitHub인증방식은별도사용자지시로로그인된공식CLI를사용해기존기록을게시하는것으로해결했다. Git credential helper/원문인증값조회는수행하지않는다.

## What already exists and NOT in scope

collection의manifest/pagination/digest, collection_db의normalize_row와pack입력검사, rental_storage의출처키/격리규칙을 재사용한다. SQLite/openpyxl 기존 의존성을 유지한다. 검증된 실제975query복원 입력을 재사용하고 API를 다시 호출하지 않는다. 새 데이터셋 수집, 좌표시설, 추천, Drive업로드, 역사DB마이그레이션, PR/배포, 외부CLI리뷰는 범위 밖이다. building등 공식필드가 없으면NULL/미연결로 두고 테이블을 채우기 위한 데이터를 생성하지 않는다.

## Implementation Tasks

- [ ] T1 (P1, human약2h / agent약20min): manifest/raw scope공통검증과 잘못된입력거부회귀, 근거A2. collection_db/collection_integrate와collection테스트를 수정하고stale/완료/partial/오프라인CLI를 검증한다.
- [ ] T2 (P1, human약6h / agent약60min): 다중배치/버전/소속관계와 원자적canonical출력, 근거A1. collection_integrate와통합테스트를 수정하고동일배치신규0/충돌rollback/새배치독립소속을 검증한다.
- [ ] T3 (P1, human약4h / agent약40min): 공식IDnamespace/주소/미확정후보, 근거A3/P1. 충돌/다중후보/동명이단지/결측/FK를 검증하고 자동병합하지 않는다.
- [ ] T4 (P1, human약4h / agent약40min): 파일section/필드/완료검증을canonical로 연결, 근거Q1/Q2. source_files/CLI와파일계약테스트를 수정한다. 실제새출처는별도등록한다.
- [ ] T5 (P1, human약2h / agent약30min+실제DB실행): 실제전체/원문lineage/재생성증분대사, 근거Test review/P2. 복원입력에서새출력으로유효374892/제외9319/거부0과FK/인덱스를검증한다.
- [ ] T6 (P2, human약1h / agent약15min): CLI오류/문서/SDD와기존계약회귀, 근거Test review. 네트워크권한/인증접근을추가하지않는다.

시간은구조/테스트작업의추정이며외부대기/실제실행시간은제외한다. 단일agent/작업구역에서T1→T2→T3→T4→T5→T6순서로schema/호출자/테스트를수정한다. 공유파일을병렬편집하지않고추가agent승인이없어하위agent를실행하지않았다.

## Completion summary

Scope accepted as-is. Architecture3, Code quality2, Test review6개범주, Performance2로13개구현문제를기록했다. 각실패경로에명시적오류/rollback/검증을계획했고오류처리와테스트가모두누락된계획의silent critical gap은0이다. 기존코드수정완료를뜻하지않는다. 새TODO0, outside review실제설정disabled이므로외부CLI/대체agent없음. 원본복원은통과했으나canonical/실제엔터티·증분/Goal은미완료다.

이전review log를읽고현재계획의새기록을추가한다. 기존2026-10-12수집계획의GitHub기록대기는현재계획승인을대체하지않는다. 필수review log성공전에정식저장gate통과를주장하지않는다.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
| --- | --- | --- | --- | --- | --- |
| CEO Review | 미실행 | 승인목표유지 | 0 | not run | 범위축소없음 |
| Outside Review | codex_reviews설정확인 | 외부독립의견 | 1 | disabled | 실제설정disabled, 외부의견없음 |
| Eng Review | gstack-plan-eng-review | 데이터흐름/오류/테스트/성능 | 1 | ISSUES OPEN | 구현과제13, 미승인결정0, silent gap0 |
| Design Review | 미실행 | 제품UI변경없음 | 0 | not run | 해당없음 |
| DX Review | 미실행 | 기존CLI사용 | 0 | not run | CLI회귀테스트계획에포함 |

**OUTSIDE COVERAGE:** claude-code, plan-review, disabled, 미실행이며외부검토증거없음.
**VERDICT:** 사용자가후속전체범위/구조/회귀계약을승인했다. engineering issues_open은구현과제이며실제검증통과주장이아니다. 필수로그후승인된구현을진행하고Goal은active유지.
NO UNRESOLVED DECISIONS
