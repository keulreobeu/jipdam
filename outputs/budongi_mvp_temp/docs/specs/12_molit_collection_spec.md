# MOLIT XML Collection Spec

```toml
kind = "spec"
id = "MOLIT-001"
status = "approved"
owner = "keulreobeu"
revision = 4
approved_by = "사용자"
approved_at = "2026-10-12"
approval_ref = "2026-10-12 서울 전월세·매매 원시 XML 수집과 오프라인 DB 생성 계획 검토·보완 후 진행 요청 및 원본·제외/실패 사유·무결성 증거 요구 Goal; 같은 날 사용자의 키 보관함 별칭 단일화 요청에 따라 키 선택을 명시적 ID로 통일"
change_approval = "2026-10-15 사용자 승인: 제공 통계의 거래량 기간(2024-01~2026-08)과 동일한 서울25구 MOLIT 매매·전월세 범위 확장. 기존 202510~202608 원본 재사용, 202401~202509 누락 query만 추가 수집. GitHub #7 예약."
```

## 범위·승인

서울 전월세·매매 일반·매매 상세의 원시 XML 보존, 재개·완료 재사용, 오프라인 DB와 ZIP 생성. 최초 승인은 서울25구 직전12개월(202510~202610)이었다. 2026-10-15 사용자의 추가 요청으로 거래량 통계와 맞춘 계약월202401~202608 범위를 추가 승인했다. 기존 #5의 202510~202608 원본은 재사용하고, 누락된 202401~202509만 GitHub #7로 예약하여 수집한다. 신규 plan은 `observation_from=2024-01-01`, `snapshot_date=2026-08-31`로 고정한다. 전체 목표는 서울25구×32개월×3서비스=2,400 query이며 기존 원본825 query를 재사용하고 최대1,575 query를 신규 수집한다. 매칭·좌표·시설·추천 연결·사람 Golden·Drive 자동 업로드는 포함하지 않는다.

## MOLIT-001-REQ-01 호출·키

공식 GET은 `https://apis.data.go.kr/1613000/` 아래 `RTMSDataSvcAptRent/getRTMSDataSvcAptRent`, `RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade`, `RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev`다. 각 서비스 키는 CRED-001의 자격증명 ID로 선택한다. 서비스 식별자는 `rental`, `trade`, `trade-detail`이며 서비스별 키 ID를 명시적으로 지정한다. 보관함 공급자 메타데이터나 별칭은 서비스 선택에 사용하지 않는다. 키 원문 인자·새 환경변수 fallback·키 포함 URL/헤더/오류 출력은 금지한다. 기존 역사 CLI는 유지한다. query는 LAWD_CD 5자리, DEAL_YMD 6자리, pageNo, numOfRows, serviceKey. 기본 numOfRows=1000, 직렬 1초 간격, timeout=20초, 일시 오류 최대 3회. 인증/일일 쿼터 실패는 해당 서비스를 중단한다. 서버 응답 pageNo/numOfRows/totalCount와 실제 행 수를 검증한다.

### MOLIT-001-AC-01 서비스·보안·회귀

세 서비스가 서비스별로 명시한 자격증명 ID의 키만 사용한다. 같은 ID를 여러 서비스에 지정할 수 있으며 별칭·폴더·기존 공급자 메타데이터에서 사용할 서비스를 추측하지 않는다. 오류·아카이브·ZIP에 키가 없고 기존 역사·보관함 동작이 유지된다.

## MOLIT-001-REQ-02 원본·재개·완료 검증

별도 배치 manifest와 서비스/지역/월별 manifest, 페이지별 요청·조회 시각·SHA-256·행 수를 보존한다. 파싱 전에 응답을 저장한다. 키가 반사된 응답은 저장하지 않고 안전한 오류만 남긴다. 시도별 파일을 추가하며 기존 원본을 덮어쓰지 않는다. 중단 후 남은 페이지를 받고 완료 페이지는 검증·재사용한다. 성공 0건/실패/부분 완료/불일치를 구분한다. 같은 시각의 원천 스냅샷 복구를 보장하지 않으며 조회 시점 복사본으로 표시한다. 갱신은 새 배치다. 전체 범위의 오래된 XML은 유지한다.

### MOLIT-001-AC-02 원본·중단·재개

실패 XML을 보존하고 중단 후 완료 페이지를 다시 호출하지 않는다. 반사 키 응답은 저장되지 않는다.

manifest는 임시 파일 fsync 뒤 원자적으로 교체한다. Windows 읽기 핸들의 일시적 PermissionError는 파일 교체만 최대 5회(50/100/200/400ms 대기) 재시도한다. 영구 오류는 성공으로 숨기지 않는다. 응답 XML 저장 후 manifest 커밋이 중단돼도 received journal의 해시/페이지를 검증해 키·API 접근 없이 완료 페이지를 복구한다.

### MOLIT-001-AC-03 재사용·무결성

완료 범위 재실행은 키/네트워크 접근 없이 끝난다. 변조·페이지·조건·총건수 불일치를 완료로 취급하지 않는다. 외부 배치도 검증 후 원본을 재사용한다.

외부 배치의 유효한 일부 페이지와 received journal도 검증 후 재사용한다. 원본 제공 배치는 수정하지 않고 새 배치의 manifest에서 복구한다. HTTP 오류의 received 응답은 성공 페이지로 승격하지 않는다. 실제 파일이 없는 interrupted_write 시도는 기대 파일/해시만 메타데이터로 남기며 실제 확보 원본에 포함하지 않는다.

## MOLIT-001-REQ-03 오프라인 정규화·격리

파싱·build-db는 키/네트워크 접근을 하지 않는다. 금액은 Decimal로 만원→원 정수, 면적은 전용면적 수치, 날짜는 검증한 ISO 날짜다. 누락을 0으로 추정하지 않는다. 불명확한 종전 금액은 원문만 보존한다. 각 관측은 서비스·원본 파일 참조·해시·행 위치를 가진다. 동일 값의 다른 행은 유지한다. 매매 일반/상세를 자동 병합하지 않고 aptSeq는 단지 일련번호로만 둔다. 전월세 DB는 rental_v1/source_unverified, 매매 DB는 sale_observations_v1/source_unverified이며 기존 역사 DB를 건드리지 않는다. 관측 기간 밖/기준일 이후 행은 원본에 유지하고 기간별 제외 건수를 기록한다. 잘못된 필수 값은 행 위치와 함께 거부하고 DB 생성은 rollback한다.

### MOLIT-001-AC-04 필드·단위·식별

금액 쌍·날짜·결측·정정 미확인·동일 값 여러 행·서비스 구분과 전체 원문 보존을 검증한다.

### MOLIT-001-AC-05 오프라인 DB·불변

두 DB를 오프라인 재생성하고 정규화 결과·관측 키가 같다. 기존 출력을 덮어쓰지 않는다. 기본은 전체 완료만, allow-partial은 완료된 query만 포함하고 누락 범위를 표시한다.

완료된 query의 모든 원본 행은 `staging.sqlite3`에서 원본 파일/해시/행 위치·원문과 유효/기간 제외/거부 상태·사유로 추적한다. 원본 건수 = 유효 + 기간 제외 + 거부이며 유효 건수 = 정규화 DB 실제 건수와 원본 조인 건수여야 한다. 거부 행이 있으면 정규화 DB를 게시하지 않고 모든 발견 오류를 `normalization-errors.json`에 기록한다. 오류 보고의 `imported`는 게시 전 유효 후보 수이며 rollback된 행을 실제 적재 성공으로 보고하지 않는다. 같은 출력의 staging도 봉인한다.

## MOLIT-001-REQ-04 CLI·공유

`collection plan/fetch/status/build-db/pack`을 제공한다. plan/status/build-db/pack은 네트워크와 키가 필요 없다. fetch에 GitHub 기록 URL을 요구하고 COLLECT-001의 예약 절차를 따른다. 같은 서비스·지역·월·페이지 크기의 외부 완료 XML도 지정한 cache 디렉터리에서 재사용할 수 있다. pack에는 XML, manifest, DB, 짧은 summary.md를 넣고 최종 ZIP SHA-256을 출력한다. GitHub 기록·예약은 별도 수행하며 URL만으로 원격 예약의 진실성이나 동시 담당 충돌을 자동 판정하지 않는다. Drive 업로드는 수동이다. 데이터·DB·ZIP·키는 Git 제외.

### MOLIT-001-AC-06 CLI·요약·ZIP

CLI 전체 흐름·원본 포함 ZIP·해시·누락 요약·오류 종료를 검증하고 실제 수집 결과는 합성 검증과 분리 보고한다.

ZIP의 DB는 현재 계획 해시·완료 query 원본 해시/파일 위치·전체 완료 상태와 일치해야 한다. 부분 DB 생성 뒤 수집이 추가된 경우 기존 DB 해시가 정상이어도 pack을 거부하고 새 출력으로 재생성한다. 키 보관함 연결 계약은 사용자가 별칭 통일/재등록 완료를 알린 뒤 확인하며 그 전 새 API 호출은 보류한다.

## MOLIT-001-REQ-05 명시 기간

계획 생성은 기존 기본값(기준일 직전 12개월)을 유지하되 사용자가 승인한 역사 통계 정합 수집을 위해 `--observation-from`의 inclusive ISO 날짜를 받을 수 있다. 시작일은 기준일보다 늦을 수 없고 plan에 저장되어 load/rebuild 시 동일하게 검증한다. 월별 query와 관측 기간은 구분한다. 캐시된 완료 query는 동일 서비스·구·월·페이지 크기일 때 검증 후 재사용한다.

### MOLIT-001-AC-07 기간 선택·재현

CLI가 2024-01-01~2026-08-31 관측 기간과 202401~202608 월별 query를 하나의 고정 plan으로 보존하고, 오프라인 재생성·pack에서 같은 기간 및 원본 계보를 확인한다. 잘못된 시작일은 저장 전 거부한다. 승인 범위 밖 데이터·원본은 수정하지 않는다.

## 공식 필드 근거

[전월세 15126474](https://www.data.go.kr/data/15126474/openapi.do), [매매 일반 15126469](https://www.data.go.kr/data/15126469/openapi.do), [매매 상세 15126468](https://www.data.go.kr/data/15126468/openapi.do)의 페이지 내 Swagger를 2026-10-12 읽어 대조했다. 전월세 HWP의 페이지 파라미터도 확인했다 (SHA-256 `361aa2da577550a820e3c82800c47512c5b6c56a33d76931104a0cfa88f5cc27`). 실제 응답 계약 변경은 원본을 유지하고 새 정규화 버전으로 처리한다.

| 원천 | 정규화 | 근거·한계 |
| --- | --- | --- |
| sggCd, umdNm, aptNm, jibun | 지역·동·이름·지번 | 단지 자동 식별 아님 |
| dealYear/dealMonth/dealDay | contract_date | 유효 날짜만 |
| deposit/monthlyRent | deposit_krw/monthly_rent_krw | 공식 명세의 만원 × 10000; 월세 0은 전세 |
| dealAmount | price_krw | 만원 × 10000 |
| excluUseAr, floor, buildYear | 면적·층·건축연도 | 필수 면적 양수; 원문 유지 |
| aptSeq | source_complex_id | 매매 상세의 단지 일련번호, 거래 고유 ID 아님 |
| cdealType/cdealDay | 원천 취소 표시·일자 | 매매에만 제공, 버전 자동 연결 없음 |
| preDeposit/preMonthlyRent | raw_payload만 | 명세에 단위 명시 부족; 추정하지 않음 |
| 나머지·새 필드 | raw_payload | 누락 없이 보존 |
