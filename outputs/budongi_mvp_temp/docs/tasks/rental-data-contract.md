# TASK-RENT-DATA-001 — 전월세·위치·시설 적재 계약

```toml
kind = "task"
id = "TASK-RENT-DATA-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/public_data.py", "outputs/budongi_mvp_temp/src/budongi/rental_storage.py", "outputs/budongi_mvp_temp/scripts/", "outputs/budongi_mvp_temp/tests/", "outputs/budongi_mvp_temp/docs/specs/02_data_model_spec.md", "outputs/budongi_mvp_temp/docs/tasks/rental-data-contract.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-07"]

[[verification]]
command = "PowerShell: $env:PYTHONPATH='src'; python -X utf8 -m unittest discover -s tests -p test_rental_storage.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/rental-data-contract.md#검증남은-조건"
acs = ["RENT-001-AC-07"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/rental-data-contract.md#검증남은-조건"
acs = ["RENT-001-AC-07"]

[[verification]]
command = "manual: PLAN-RENT-001의 관련 제품 AC 시나리오를 실행하고 실제 결과를 기록"
result = "not_run"
evidence = "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md#product-verification-pending"
acs = ["RENT-001-AC-07"]
```

## 목표·범위

공식 전월세 기술문서의 실제 필드·단위·누락·ID/정정 제공 범위를 대조한다. 상세 필드표·단위표를 확인한 뒤에만 원천 값 매핑·변환을 구현한다. 키 비노출·원본 해시·페이지 검증을 재사용하고 최신 임대차를 별도 불변 DB에 적재하는 계약과 합성 fixture를 구현한다. 단지·직장·역·마트·공원·병원 좌표/커버리지·매칭 근거 입력을 검수한다. 같은 값을 가진 별개 거래를 잘못 병합하지 않는다. 추가 공급자의 기술문서·사용조건·기준일을 확인하고 확인된 계약만 Spec에 반영한다.

승인 근거: [PLAN-RENT-001](../plans/rental-recommendation-mvp.md#확정-근거)의 최종 사용자 적용 요청. 이번 착수에서 합성 입력에 대한 저장·계보 기반을 구현한다. 실제 API 호출·실데이터 수집·단지 매칭은 계속 보류한다. 담당자는 Codex다.

## 의존·제외 범위

선행 조건: TASK-RENT-DOC-001. 실수집/매칭은 별도 보류 해제까지 금지하며 합성 입력으로 가능한 구현과 구분한다. 외부 CLI 리뷰·push/PR/배포는 이 Task의 자동 권한이 아니다.

## 완료 기준

- [ ] RENT-001-AC-07 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.

## 조사·구현 결과

- [공공데이터포털의 공식 API 페이지](https://www.data.go.kr/data/15126474/openapi.do)는 법정동 앞 5자리와 계약년월 6자리 기준 조회, REST/XML 형식, 아파트 동·호 비공개를 설명한다. 같은 페이지가 `아파트 전월세 실거래가 자료 기술문서.hwp`를 참고문서로 열거한다.
- 이 실행 환경에서 포털의 정적 API 명세에는 응답 21개 모델 항목 이름·단위표가 노출되지 않았고, HWP 본문을 열람하지 못했다. 따라서 원천 필드·금액 단위·누락·개별 거래 ID·취소/정정 상태를 확인했다고 주장하지 않는다.
- `parse_molit_rental_response`는 XML 태그와 빈 문자열을 그대로 돌려주는 순수 파서다. 네트워크 요청·필드 별칭·단위 변환을 하지 않는다.
- `rental_v1` 저장기는 기존 역사 DB와 분리되고, source manifest의 파일 경로·SHA-256·행 수와 각 행 출처가 일치해야 한다. 관측 ID는 원천 ID가 아닌 파일 해시·행 번호 기반 내부 키다. 적재가 끝나면 스냅샷을 봉인하며 SQLite trigger가 후속 행 추가·수정·삭제를 거부한다.
- 합성 검증은 동등한 값의 개별 행 보존, source ID/상태 미발명, 시설 커버리지 unknown, 매칭 근거, 원본 바인딩, 인증값 거부, 기존 DB 격리, 스냅샷 불변성과 실패 rollback을 다룬다.

## MVP API 신청 우선순위

| 우선 | 서비스 | 신청·키 | 추천 범위와 한계 |
|---|---|---|---|
| 필수 | [국토교통부 아파트 전월세 실거래가](https://www.data.go.kr/data/15126474/openapi.do) | 공공데이터포털에서 해당 서비스 활용신청·승인을 받는다. 신규 전월세 adapter는 [CRED-001](../specs/11_api_credential_vault_spec.md)의 별도 암호화 보관함에서 공급자 `data_go_kr`와 사용자가 정한 별칭/폴더로 선택한다. 기존 역사 수집 스크립트의 `DATA_GO_KR_SERVICE_KEY` 환경변수 계약은 유지한다. | 서울 법정동 5자리·계약년월 6자리, REST/XML. 실거래 이력 조회이며 현재 매물이 아니다. 발급·승인 준비와 실제 호출은 별개이고 실제 수집은 보류 상태다. |
| 권장 | [Kakao Local API](https://developers.kakao.com/docs/ko/local/dev-guide) | 카카오디벨로퍼스에서 앱을 만들고 플랫폼 키의 REST API 키를 준비한다. 신규 전월세 adapter에서는 공급자 `kakao_local`과 키별 별칭/폴더로 보관한다. | 주소→좌표 변환과 장소 검색은 API 호출이며 좌표 간 직선거리 계산은 로컬 연산이다. 문서의 그룹 코드는 지하철역 `SW8`, 대형마트 `MT1`, 병원 `HP8`이다. `MT1`은 모든 동네 슈퍼를 뜻하지 않으며, 일반 마트 키워드 검색의 부재를 시설 부재로 해석하지 않는다. 공원 그룹 코드는 없어 별도 출처가 필요하다. 실제 호출 전 장소 결과의 보관·재사용 약관도 확인한다. |
| 공원 조건을 MVP에 넣을 때 | [서울시 주요 공원현황](https://data.seoul.go.kr/dataList/OA-394/S/1/datasetView.do?tab=A) | 서울 열린데이터광장에서 인증키 신청. 신규 adapter에서는 공급자 `seoul_open_data`와 키별 별칭/폴더로 등록한다. | 공원명·주소·WGS84 좌표(`XCRD`, `YCRD`)를 제공하는 주요 공원 범위다. 전체 소공원 목록으로 간주하지 않고 갱신은 비정기다. 공개 샘플은 `http://...:8088/.../(인증키)/...` 형태로 키를 경로에 넣으므로, 키 신청은 가능하나 실제 호출 전 HTTPS 지원을 확인한다. 미확인이면 파일 내려받기나 HTTPS가 확인된 대체 출처를 쓴다. |

카카오맵 REST의 공개 문서에는 주소·장소 검색 일일 무료 쿼터가 각각 100,000건으로 표시되지만, 개발자 계정의 첫 활성 앱만 무료 쿼터를 받고 추가 사용은 유료일 수 있다. 지금은 유료 쿼터·비즈월렛을 켜지 않는다. [공식 쿼터](https://developers.kakao.com/docs/ko/getting-started/quota)

현재 신청할 항목은 위 필수 1개와 권장 1개, 공원 조건을 첫 데모에서 살릴 경우에만 3번째다. 지도 JavaScript SDK, 대중교통·도보 경로, 현재 매물, 대출·금리, 청약 API는 현 MVP에서 신청하지 않는다. 실거래 수집 보류가 해제될 때까지 어떤 신규 키로도 실제 전월세·장소 데이터를 호출하지 않는다. 신규 키는 Windows Credential Manager가 보호하는 암호화 보관함에서 관리하며 채팅·저장소·브라우저 영속 저장소·로그에 원문을 넣지 않는다. 현재 역사 CLI의 환경변수 흐름은 유지한다.

## 검증·남은 조건

위 unittest 명령은 저장·파서 foundation에 대해 실행했고 통과했다. 이 결과는 `RENT-001-AC-07` 전체를 통과한 기록이 아니다. 공식 상세 기술문서의 응답 항목·단위·식별/정정 한계를 확인하고 원천→정규화 매핑 및 그 fixture를 추가하기 전까지 AC는 체크하지 않고 Task를 `in_progress`로 둔다. 실데이터 수집·사람 검수 단지 매칭·제품 추천 시나리오는 **not_run**이며 [후속 검증 시나리오](../plans/rental-recommendation-mvp.md#product-verification-pending)를 따른다.
