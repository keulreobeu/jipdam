# 집담 통합 메타데이터와 DB·PK 설계

2026-10-30 / KAN-32. 현재 산출물은 **설계안과 업무 분담**이다. DB 생성·원본 재검증·매칭 확정은 실행하지 않았다.

## 아파트 표제부를 공통 키로 써도 되는가

**개별 건축물대장 연결 기준으로 사용하고, 단지 전체의 PK는 별도로 두는 것을 권고한다.** 단지는 여러 동·여러 필지·여러 대장을 가질 수 있다. 내부 complex_id / building_id / unit_id와 source register identifier를 분리한다. 현재 canonical v3는 출처별 엔터티이므로 기존 ID/FK를 보존하고 버전 있는 통합 마스터·검수 bridge를 후속 추가한다.

건축HUB는 종류 1 총괄표제부, 2 일반건축물, 3 표제부, 4 전유부를 구분한다. 관리건축물대장PK는 `(service_namespace,regstrKindCd,mgmBldrgstPk)`의 nonblank TEXT로 보존한다. 공식 안내에 구 시스템에서 건축HUB로 전환하며 PK가 변경됐다고 명시되어 있으므로 구·신 namespace를 섞지 않는다. 상위 대장키는 대상 종류·namespace·기준시점·근거가 검증될 때만 관계 후보로 연결한다. 총괄표제부도 서비스 단지와 1:1로 가정하지 않는다.

Kim D006/D007은 전유부·전유공용면적의 수집 중 스냅샷이다. 현재 목록에 표제부/총괄표제부 확보 항목이 있다는 증거가 없다. 전유공용면적은 대장 하나에 여러 행이므로 mgmBldrgstPk 단독 PK는 부적절하다. 표제부 확보 필요 여부는 KAN-37에서 확인하며 새 수집은 별도 승인 사항이다.

공식 근거: [건축HUB 대장 종류](https://www.hub.go.kr/portal/opn/tyb/idx-bdrg.do), [국토부 건축물대장 API·PK 변경 안내](https://www.data.go.kr/data/15134735/openapi.do?recommendDataYn=Y), [표제부 제공 항목](https://www.data.go.kr/data/15044720/fileData.do), [K-apt 목록 범위](https://www.data.go.kr/data/15057332/openapi.do?recommendDataYn=Y). 이는 키 설계의 근거이며 실제 관계 검수 결과가 아니다.

## 공통 키와 저장 영역

원본 파일 SHA는 콘텐츠 식별자, 저장 경로는 위치, collection_batch_id는 수집 시점/범위다. 같은 원본이 여러 배치에 속하는 관계를 별도로 둔다. raw_item_id=H(file_sha,section/sheet,row); 정규화 관측 obs_id=H(dataset_id,collection_batch_id,raw_item_id,mapping_version,component_type/원순번). H는 타입·경계를 보존하는 canonical JSON tuple SHA-256이며 문자열을 단순 연결하지 않는다. 통계는 source_column과 source_view를 추가한다. 성능 실험의 run_id를 새 수집 배치로 취급하지 않는다.

원본/ZIP은 파일 보관, Catalog는 기존 SQLite, 통합 identity master는 별도 SQLite 확장 제안, 분석 fact는 Parquet와 DuckDB SQL, 클라우드는 향후 JIPDAM_ANALYTICS의 LANDING/SILVER/GOLD로 나눈다. 현재 canonical/statistics/추천 DB는 읽기 전용 입력으로 유지한다. Snowflake 계정/리전/예산·이전 조건 확정 전 클라우드를 만들지 않는다. Snowflake 표준 테이블 PK/FK 선언만으로 유일성/관계를 검증한 것으로 처리하지 않고 dbt/대사 검사를 둔다. Airflow 운영 PostgreSQL은 업무 데이터베이스와 분리하는 후속 운영 영역이다.

## 테이블과 키

모든 신규 테이블은 후속 구현 제안이다. 기존 M1 Catalog와 Parquet 실행 기반의 존재를 모든 표의 구현 완료로 확대하지 않는다.

| DB/영역 | 테이블 | 행 단위 | PK | 주요 필드·후보 제약 | 주의 |
| --- | --- | --- | --- | --- | --- |
| Catalog SQLite | metadata_snapshot / metadata_entry | 워크북 / 등록항목 | snapshot_sha / (snapshot_sha,namespace,entry_id) | 원문 시트·셀·수집자·수입시각 | 75개는 등록항목 수. 논리 데이터셋·배치와 별도 |
| Catalog SQLite | dataset / collection_batch | 논리 출처 / 수집 배치 | dataset_id / collection_batch_id | 기간·범위·manifest_sha·봉인상태 | 성능 반복 run_id를 새 수집 배치로 만들지 않음 |
| Catalog SQLite | artifact / location / batch_file | 콘텐츠 / 위치 / 배치 소속 | file_sha256 / location_id / (collection_batch_id,file_sha256,role) | 크기·원래 경로·해시 | 사본 경로와 중복 콘텐츠를 구분 |
| Catalog SQLite | raw_item / normalized_lineage | 원본행·셀 / 출력 계보 | raw_item_id=H(file_sha,section,row) / (obs_id,raw_item_id,source_column) | 매핑 버전·component_type/sequence | 1:N 출력·한 파일의 다중 배치 소속 보존 |
| Catalog SQLite | validation_report | 수집자 검증 보고서 판본 | validation_id | dataset/batch/hash,검증자·시각·방법·결과 | 자체검증/통합수용/관계검수 별도 상태 |
| Identity SQLite (신규 제안) | apartment_complex / building / unit | 단지 / 동 / 호 실체 | complex_id / building_id / unit_id (발급 후 고정 UUID TEXT) | 명칭·주소 이력. 검수 관계로만 소속 연결 | 현행 canonical 출처별 ID/FK 재계산 금지 |
| Identity SQLite (신규 제안) | source_identifier / entity_binding | 출처 식별자 / 내부 실체 연결 | source_identifier_id / binding_id | UNIQUE(namespace,entity_level,source_key);유효시점·근거·검수자 | 미확정 연결은 NULL/후보. Kapt/aptSeq/대장키 별개 |
| Identity SQLite (신규 제안) | register_identifier / register_relation | 대장 식별자 / 상하위 관계 | (service_namespace,regstrKindCd,mgmBldrgstPk) / relation_id | 모두 nonblank TEXT;상위키의 대상종류·namespace·기준일 | 구·신 서비스 별도. 상위키만으로 조인/단지 확정 금지 |
| Identity SQLite (신규 제안) | entity_membership / coordinate_review | 단지-동-호 소속 / 검수 좌표 | membership_id / coordinate_review_id | 유효시점·관계 근거;CRS/축순서/변환·검수자 | WGS84 값 범위만으로 공식 CRS 확인을 대체하지 않음 |
| DuckDB SILVER / Snowflake SILVER | molit_rental_observation / molit_sale_observation | 출처 서비스의 거래 관측 | obs_id | 원 정수·면적·계약일·취소정정·service·source IDs | 배치·일반/상세·CSV 중복은 보존. 고유 거래 수 아님 |
| DuckDB SILVER / Snowflake SILVER | housing_stat_cell | 원본 셀 1개 | H(collection_batch_id,file_sha,sheet,row,column,mapping_version,source_view) | series·기간/주기·차원·단위·value_decimal·결측 | 판본·표현·주간/월간 구분. 원본 행은 여러 셀 출력 |
| DuckDB SILVER / Snowflake SILVER | guarantee_incident_observation / population_observation | 지역×기간×지표 / 지역×기준일×성별×연령 | obs_id | 출처별 지역코드·지표·단위·시점 | HUG 자체코드·행정동·법정동 코드 체계 구분 |
| DuckDB SILVER / Snowflake SILVER | assessed_unit_price_observation | 공시가격의 호별 기준일 관측 | obs_id | 출처단지:동:호·기준일·대장PK·원 정수·면적 | 후보 UK=(source namespace,단지,동,호,기준일,판본). 내부 unit FK 검수 후 |
| DuckDB SILVER / Snowflake SILVER | kapt_basic_observation / kapt_monthly_fee_observation | 기본정보 원본행 / 단지×월 관측 | obs_id | kaptCode·기준일·비용항목·단위·판본 | 반복 코드 원본행 보존. 월 비용항목 세로화 시 component 추가 |
| DuckDB SILVER / Snowflake SILVER | building_register_observation | 총괄/표제/전유 등 대장 응답행 | obs_id | register_identifier FK·상위키·동/호·면적·기준일 | 현재 D006=전유부 수집 중. 표제부/총괄은 확보 확인 필요 |
| DuckDB SILVER / Snowflake SILVER | building_area_component_observation | 전유/공용 면적 구성요소 1행 | H(collection_batch_id,raw_item_id,mapping_version,component_type,original_sequence) | 대장키·전유공용구분·층·구조·용도·면적 | mgmBldrgstPk 단독 PK/UNIQUE 금지. 원본 순번 유지 |
| DuckDB SILVER / Snowflake SILVER | facility_observation / facility_attribute_observation | 학교·학원·의료·도서관·어린이집·보호대상시설 관측 | obs_id / (obs_id,attribute_code,original_sequence) | source namespace/id·종류·주소·원좌표·운영상태 | 학교 SD_SCHUL_CODE; 학원 교육청+지정번호; 의료 출처요양기호. 없으면 계보키 |
| DuckDB SILVER / Snowflake SILVER | rail_station_observation | 운영기관·노선별 역 관측 | obs_id | 기관·노선·역번호·원명·출처판본 | T001 복합키도 중복. T002와 역번호 체계가 달라 관계 검수 필요 |
| DuckDB SILVER / Snowflake SILVER | rail_ridership_day | 사용일×노선×역 관측 | obs_id | 일자·출처노선명/역명·승차/하차·조회판본 | 후보 UK=source+일자+노선+역+판본. 표준 station FK는 매핑 검수 후 |
| DuckDB SILVER / Snowflake SILVER | bus_stop_observation / bus_route_observation | 정류소 / 노선 관측 | obs_id | source NODE_ID/ARS_ID / ROUTEID·기준일 | 지역/운영기관 namespace 필요. 이름을 PK로 쓰지 않음 |
| DuckDB SILVER / Snowflake SILVER | bus_route_stop_observation | 노선×방향/변형×경유순번×판본 | obs_id | ROUTE_ID·NODE_ID·original_sequence·direction_raw | 노선+정류소만으로 유일성 가정 금지. 미제공 방향은 unknown |
| DuckDB SILVER / Snowflake SILVER | air_quality_hour | 측정소×시간×항목×정정/수집판본 | obs_id | 측정소 namespace·원시시각/타임존·항목·값·단위·정정상태 | 측정소-자치구 매핑 검증 전 지역값 부여 금지 |
| DuckDB SILVER / Snowflake SILVER | spatial_feature_observation | 침수·상권·학구·교육환경 구역 feature | H(collection_batch_id,file_sha,layer,feature_id_or_original_sequence,mapping_version) | 레이어/연도·source feature id·원형상/CRS·변환버전 | 소스의 동명 OBJT_ID 등은 namespace/레이어/판본 포함 |
| DuckDB SILVER / Snowflake SILVER | osm_way_observation | OSM Way·버전 관측 | obs_id | osm_type+osm_id+version·태그·형상·source_file | Way는 보행 그래프 edge 아님. 노드/연결성은 별도 파생 검증 |
| DuckDB SILVER / Snowflake SILVER | tourism_content_observation / tourism_code_observation | 관광 콘텐츠 / 코드표 항목 | obs_id / H(source,code_system,code_version,code) | contentid·콘텐츠유형·반려동물정보·원시코드 | 코드표를 콘텐츠와 합산하지 않음. 정보 없음은 동반 불가 아님 |
| DuckDB SILVER / Snowflake SILVER | document_version / document_fragment / legal_history_index | 문서 판본 / 페이지·조문·청크 / 연혁 목록 | document_version_id / (document_version_id,parser_version,locator,chunk_seq) / obs_id | 기관·문서ID·판본·원문SHA·시행/조회일·이용조건 | HTML/PDF 사본/캡처와 법령 본문·연혁 목록 구분. 자동 법률판정 금지 |
| DuckDB SILVER / Snowflake SILVER | region_code_version / region_crosswalk / period_dim | 코드 판본 / 검수 대응 / 기간 | (code_system,version,code) / crosswalk_id / (calendar,frequency,period_key) | 유효기간·코드길이·계층·매핑근거;기간시작/끝 | 법정/행정/기관자체코드 이름이 같아도 자동 조인 금지 |
| DuckDB GOLD / Snowflake GOLD | region_period_mart / complex_context_mart | 출처/지표/지역/기간 / 단지/기준시점/모델 | (model_version,region_version,period,metric,source_view) / (model_version,complex_id,as_of) | 집계 기준·미연결/미검수·관측 수/고유 실체 수 | 검수된 관계만 이용. 지표중복/결측을0으로 집계하지 않음 |
| 기존 serving SQLite | 현행 canonical / 추천 projection | 현행 계약 유지 | 기존 ID/FK 유지 | 통합 마스터는 별도 확장·검수 bridge 후 연결 | 이번 설계로 실제 추천·관계·좌표 승격하지 않음 |

## 타입·중복·품질 규칙

- 모든 출처 ID·법정/행정 코드·단지/동/호·대장키는 문자열이다. Excel 숫자 정밀도 손실은 추정 복원하지 않는다. 없는 source ID는 NULL이며 원본 계보로 관측만 구분한다.
- 원 단위 금액은 범위 검증한 정수, 면적/통계는 정확한 Decimal 원문을 보존한다. 손실 없는 범위를 측정한 후에만 DuckDB/Snowflake DECIMAL/NUMBER(p,s)로 변환한다. 소수·미측정·이상값을0으로 바꾸지 않는다.
- 수집/기준/유효/계약/조회 시점, 주기, 출처 시각/타임존을 구분한다. 늦게 도착한 거래와 정정·기관 수정 판본을 덮어쓰지 않는다.
- batch overlap, CSV/JSONL 사본, 통계 source_view와 법령 HTML/PDF·캡처를 명시 관계로 기록한다. 값·이름이 같은 것만으로 원본 관측을 삭제하거나 같은 실체로 승격하지 않는다.
- 코드체계와 유효기간이 검수된 경우에만 region FK를 연결한다. CRS/축순서가 미확인인 점은 source_x/y를 유지한다. 시설점과 구역 경계는 서로 다른 테이블/grain이다.
- 각 수집자의 자체 검증과 통합 수용, 관계·좌표 검수·이용조건 확인을 별도 상태로 둔다. 승인 관계에는 검수자·시각·원본해시·근거·유효기간을 기록하고 상충/순환/중복 accepted 관계를 차단한다.

## 담당별 작업

- 이진호: [KAN-33](https://kwulreobeu.atlassian.net/browse/KAN-33) — 거래·주택통계·문서 48항목 자체 검증
- 서지우: [KAN-34](https://kwulreobeu.atlassian.net/browse/KAN-34) — 보증·의료·공시가격·교육·인구·공간 11항목 자체 검증
- 김성현: [KAN-35](https://kwulreobeu.atlassian.net/browse/KAN-35) — K-apt·건축HUB·보행·반려동물 7항목 자체 검증
- 이성진: [KAN-36](https://kwulreobeu.atlassian.net/browse/KAN-36) — 교통·침수·대기·상권 9항목 자체 검증
- 김성현: [KAN-37](https://kwulreobeu.atlassian.net/browse/KAN-37) — [키 설계 후속] 표제부·전유부·공시가격·K-apt 식별자 관계 검토
- 이진호: [KAN-38](https://kwulreobeu.atlassian.net/browse/KAN-38) — [통합 인수 후속] 수집자 검증 패키지 인수와 출처별 적재 계약 확정

각 수집자는 자기 자료의 검증과 도메인 필드·키 제안을 먼저 제출한다. Kim은 건축/단지 키, Seo는 공시가격/의료·교육/인구, LSJ는 교통·환경·공간, Lee는 거래/통계/문서와 공통 인수·계보를 맡는다. workload는 파일/등록 항목 수가 아닌 유형·볼륨·예외로 조정한다. 다른 사람의 데이터 검증을 완료했다고 대신 서명하지 않는다.

즉시 제출물: 원본 manifest/hash, input/accepted/excluded/rejected/output 대사, 후보키 NULL/중복/1:N, 단위/기준일/CRS·이용조건, 재현 명령과 검증자/시각, 실패/보류 목록. 수집 중 자료는 봉인 범위와 누락을 별도 기록한다. 기존 패키지의 기재 검증 완료는 이번 통합 작업의 재측정으로 표시하지 않았다.

## 다음 환경에서 재개

우선 docs/plans/metadata-integration-20261030.md와 docs/tasks/metadata-integration-20261030.md, Jira KAN-32 및 KAN-33~KAN-38을 읽는다. 통합 워크북의 입력출처 시트에 네 원본 SHA와 파일명/위치가 있다. 원본 네 워크북과 실제 데이터 패키지는 Git 코드와 별도 전달·해시 확인이 필요하다. 현재 PC의 Downloads/복원 경로를 다른 PC의 경로로 추정하지 않는다.

코드 환경은 프로젝트 README/bootstrap을 따른다. 이번 워크북은 파일 산출물이며 재사용 코드 설치를 요구하지 않는다. 현재 M1 파이프라인 의존성은 선택 pipeline extra다. 성능/키/DB/raw/런타임은 GMS 문맥에 보내지 않는다. 사용자가 요청한 정리는 여기까지이며 다음 단계의 수집자 검증·물리 DB 생성·관계 확정은 시작하지 않았다.
