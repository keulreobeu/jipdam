# 제공 통계 엑셀 보존·조회

계약: [STATS-001](specs/14_statistics_storage_spec.md), [ADR-007](adr/ADR-007-separate-statistics-store.md), [Task](tasks/statistics-import.md). 실제 수입/중복/기간 검증은 [검증 기록](statistics-validation-20261013.md)을 따른다.

## 저장 위치와 의미

프로젝트 폴더 기준 `data/statistics/statistics.sqlite3`는 statistics_v1 SQLite 전용 DB다. 제공 파일 30개는 `data/statistics/raw/<SHA-256>.xlsx`에 bytes 그대로 보관한다. `provided-inputs-20261013.json`은 명시적 원본 입력목록, `manifests/kb-provided-20261013-v1.json`은 파일 해시/수록기간/관측/결측 수입 결과다. 원본 파일·DB·manifest는 Git 제외다. Downloads 원본은 수정하지 않는다.

통계 행은 거래나 매물이 아니다. 평균가격의 원본 단위는 잠정 만원, 수급/전망 등 설문은 응답비율과 지수, PIR은 월별 주택분위×소득분위별 배수다. 단위/라이선스/일반 기준월은 검수 대기이며 원문값을 다른 단위로 강제 환산하지 않는다.

## 실행

프로젝트 폴더에서 설치된 `jipdam` 또는 `python -X utf8 -m budongi.cli`로 실행한다. 루트 가상환경은 `../../.venv/Scripts/python.exe`이며 PYTHONPATH는 src다.

```powershell
jipdam statistics import --statistics-db data/statistics/statistics.sqlite3 --batch-id kb-provided-20261013-v1 --input-list data/statistics/provided-inputs-20261013.json
jipdam statistics status --statistics-db data/statistics/statistics.sqlite3
jipdam statistics audit --statistics-db data/statistics/statistics.sqlite3 --input-list data/statistics/provided-inputs-20261013.json --record-reviews
```

`--files`에 명시적 경로들을 줄 수도 있다. Downloads의 모든 엑셀을 자동 탐색하지 않는다. 등록한 30종 filename_stem과 날짜접미사만 수입할 수 있다. 새 통계 종류는 별도 범위·layout·단위 등록이 필요하다. 갱신은 새 batch ID로 수행한다. 같은 배치·같은 해시 재실행은 신규 0이고 DB bytes도 동일하다. 같은 batch ID의 다른 bytes/매핑은 오류다. 개정된 파일은 기존값을 보존하면서 새 file_id/관측으로 들어간다.

audit은 보존 원본의 모든 통계셀·XML numeric 원문을 SQL과 비교한다. input-list를 주면 제공 Downloads 파일의 현재 SHA도 대조한다. `--record-reviews`는 중복/100 기준점의 검수 근거만 metadata_reviews에 추가한다. 원래 수치를 변경하지 않는다.

## 스키마와 조회

| 테이블/뷰 | 내용 |
|---|---|
| datasets | 데이터셋·provider·source_view·주간/월간·표 구조 |
| source_files | 원본 SHA·bytes·보존경로·매핑버전·사용자 메타데이터/잠정 단위 |
| import_batches / batch_files | 배치·지문·적재 UTC·파일 소속·제공 파일명 |
| series | 지역/상위지역/권역·응답항목·PIR 두 분위 등의 JSON 차원과 단위 |
| stat_observations | 원문 헤더/값·정밀 Decimal·조회용 REAL·missing/numeric·시트/행/열 |
| latest_stat_observations | 같은 dataset/source_view/시리즈/기간의 최신 수입 배치 |
| metadata_reviews | 중복/기준시점/후속 사용자 검수 근거를 추가 보존할 공간 |

공식 지역코드는 추정하지 않는다. 예를 들어 전국에 반복되는 `중구`는 표의 서울/부산 등 상위문맥과 함께 보존한다. 거래규모·주택유형 파일은 숫자가 서울 통계와 같아도 헤더에 선택지역이 없으므로 selected_region은 미확정이다. 필요한 조회는 `dataset_id`와 차원을 명시한다.

```sql
SELECT o.period_key, o.value_decimal, o.value_numeric, o.value_status,
       o.file_id, o.sheet_name, o.source_row, o.source_column
FROM latest_stat_observations o JOIN series s USING(series_id)
WHERE s.dataset_id='kb_weekly_buyer_advantage'
  AND json_extract(s.dimensions_json, '$.지역')='서울'
  AND json_extract(s.dimensions_json, '$.구분')='매수우위지수'
ORDER BY o.period_key;
```

서로 다른 지표/출처/단위를 합산하지 않는다. 앞서 받은 서울 dashboard 4개는 동일 지표의 반올림 표현이고 전체지역 상세표와 별도 dataset_id다. 분석에는 위처럼 상세표를 선택한다. dashboard는 출처 증거로 보존하며 같은 지표를 두 번 집계하지 않는다.

## 기준기간·업데이트·기준시점

사용자 보고: PIR 업데이트 2026.08, 평균가격/월간 심리/전세가격비율/월간 지수·증감률 2026.09, 주간 심리/지수·증감률 2026-10-05. 일반 기준월 대부분 2026.06 및 2022년11월 개편 메모는 profile_json에 원문 의미로 남겼다.

파일 수록기간: 월별 헤더는 YYYY-MM, 주별은 YYYY-MM-DD로 저장한다. 원본의 `09:00:52` 등 시분초는 source_header_raw에 남기고 실제 수집/공표시간으로 해석하지 않는다. PIR은 제공 파일상 2026.06까지이며 업데이트 2026.08과 다른 필드다.

기준시점: 제공 가격지수 4개는 월간 2026.01/주간 2026-01-12에서 numeric 지역 278개의 값이 전부 100이다. KB 공식 안내도 월간 2026.1=100, 주간 2026.1.12=100을 표시한다. 사용자 파일 기준 우선 지시에 따라 metadata_reviews의 review_type=effective_base_period에 월간 2026-01, 주간 2026-01-12를 반영했다. 조회는 해당 검수 이력의 base_period를 사용한다. 원래 source_files.profile_json의 일반 2026.06 메모와 초기 NULL은 기록 당시 상태로 보존한다. 아직 확인되지 않은 다른 지표에 이 기준점을 일괄 적용하지 않는다. [KB 주간 안내](https://data.kbland.kr/share/kbstats/wmh?tIdx=HT01&tsIdx=weekAptSalePriceInx), [KB 월간 안내](https://data.kbland.kr/kbstats/wmh?tIdx=HT05&tsIdx=monthAptSmeuRentPriceInx).

## 추가로 확보할 통계

현재 30개 파일 저장은 추가 자료 없이 완료할 수 있다. 아래는 현재 묶음에 없는 아파트·전월세 관련 확장 후보다. 5년/전체 이력이 제공되면 원본과 함께 지표명·단위·100 기준시점·최신수록기간·표본/개편 안내를 보관한다. 정해진 주간/월간/분기 주기를 그대로 유지한다. 아래 항목 확보는 새 실제 수집기 실행 또는 기능 확대 승인이 아니다.

| 우선순위 | 추가 파일 후보 | 쓰임 |
|---|---|---|
| 우선 | 월간 아파트 월세가격지수, 전월세전환율 | 월세 시장·전세와 월세의 전환 지표 |
| 우선 | J-PIR | 전세가격과 소득 비교. 이번 월간 PIR과 구분 |
| 우선 | 아파트 전용면적별 매매·전세 가격지수 + 전용면적별 매매·전세 평균가격 | 예산·면적 조건에 맞춘 시장 비교 |
| 우선 | 아파트 ㎡당 매매·전세 평균가격, 매매·전세 중위가격 | 단위면적·평균/중앙값 비교 |
| 확장 | 아파트 5분위 매매·전세 평균가격, 아파트 ㎡당 5분위 매매·전세 평균가격 | 가격대별 격차 |
| 확장 | 주택구매력지수, KB주택구입잠재력지수, KB아파트주택담보대출 PIR | 구매력 연구. 담보대출 PIR의 분기자료를 현재 분위형 월간 PIR과 구분 |
| 확장 | KB선도아파트50 / 서울 시세총액 TOP30의 연도별 선정 단지 목록·선정 기준 | 현재 월간선도아파트 파일은 비교지수 4행이고 실제 단지목록은 없음 |
| 공공 | 아파트매매 거래주체별·매입자연령별 거래량 | 이미 받은 주택유형·면적규모 이외 거래 구성 |
| 공공 | 서울 주택공급(인허가·착공·준공), 미분양 현황 | 공급시장 배경 |
| 공공 | 서울 인구/연령·가구/1인가구·전입/전출 | 주거수요 배경 |

주택가격동향의 해당 지표/주기·수록 범위는 [KB통계 메뉴](https://data.kbland.kr/kbstats/wmh?tIdx=HT06&tsIdx=singleRentAvgPrice), 공공 거래량의 세부 항목은 [KB 공공통계 거래량](https://data.kbland.kr/publicdata/housing-trading-volume)에서 확인했다. 아파트 이외 단독/연립·오피스텔 및 전국 밖 연구는 별도 확장 목적이 있을 때 선택한다. 서울 심리 요약본 4개는 다시 받을 필요 없이 상세표에서 표시용 반올림으로 재현할 수 있다.
