# TASK-RENT-REAL-001 — 실제 전월세 수집·매칭·사람 검수

```toml
kind = "task"
id = "TASK-RENT-REAL-001"
status = "in_progress"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/rental_review.py", "outputs/budongi_mvp_temp/src/budongi/collection_integrate.py", "outputs/budongi_mvp_temp/src/budongi/rental_readiness.py", "outputs/budongi_mvp_temp/scripts/", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md", "outputs/budongi_mvp_temp/docs/tasks/rental-real-data.md", "outputs/budongi_mvp_temp/docs/rental-review-package.md", "outputs/budongi_mvp_temp/docs/", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-07", "RENT-001-AC-10"]
[[verification]]
command = "manual: PLAN-RENT-001의 관련 제품 AC 시나리오를 실행하고 실제 결과를 기록"
result = "not_run"
evidence = "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md#product-verification-pending"
acs = ["RENT-001-AC-07", "RENT-001-AC-10"]

[[verification]]
command = "오프라인: 복원된 실제 MOLIT 전월세와 trade-detail aptSeq/name/sgg/dong/jibun 후보 대조"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/rental-identity-review-20261020.md"
acs = ["RENT-001-AC-07"]

[[verification]]
command = "복원된 전월세·trade-detail staging의 사용자 승인 5,156개 aptSeq 그룹/203,159관측을 canonical v3에 대사하고 검수 패키지로 serving 생성"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/rental-identity-review-20261020.md"
acs = ["RENT-001-AC-07"]
```

## 목표·범위

2026-10-20 사용자 요청은 기존에 승인·보존된 MOLIT 전월세 관측을 사람 검수해 실제 단지에 연결하도록 이 Task의 **기존 데이터 매칭 범위만** 재개한다. 새로운 수집/출처/좌표/시설은 승인하지 않았다. 요청월·수집일·페이지/행·해시·정규화 버전·한계를 추적하고 불명확한 매칭은 격리한다. 오래된 2023 연구의 완료를 선행 조건으로 삼지 않는다. 실제 추천 품질은 신규 실제 자료로 검수하고 합성 데모와 별도로 보고한다.

승인 근거: 기존 자료 범위는 [PLAN-RENT-001](../plans/rental-recommendation-mvp.md#확정-근거), 매칭 재개는 2026-10-20 현재 사용자 요청이다. 후보 생성은 사람 검수·승인을 대체하지 않는다. 담당자는 기존 프로젝트 owner다.

## 의존·제외 범위

매칭 단계는 기존 `rental.sqlite3`와 대응하는 MOLIT trade-detail staging만 오프라인으로 사용한다. `aptSeq` 직접 일치와 구·이름·법정동·지번 대조를 후보로 기록하되, 사용자가 연결 규칙을 검수하기 전 confirmed 관계나 추천 반영을 만들지 않는다. 원천 취소/정정 상태가 미기록이면 임의로 valid로 채우지 않는다. 이 범위의 새 출처, 좌표, 시설, Drive/GitHub 파일 업로드, 외부 CLI 리뷰, push/PR/배포는 제외한다. 다만 2026-10-20 사용자 별도 승인에 따라 동일 MOLIT 전월세 API의 같은 지역·기간 1회 재조회는 아래 예약 기록에서 추적한다.

## 완료 기준

- [ ] RENT-001-AC-07 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.
- [ ] RENT-001-AC-10 [Spec](../specs/10_rental_recommendation_spec.md)의 해당 완료 기준과 Plan 시나리오를 충족한다.

## 검증·결과

2026-10-14: 기존 전월세 238,620건 수집·canonical은 별도 완료 Task로 보존한다. 실제 확정 관계·좌표·시설·커버리지와 사람 검수 Golden은 아직 없다.

2026-10-20: 사용자가 같은 `aptSeq`와 구·단지명·법정동·지번이 유일하게 일치하는 5,156개 그룹 203,159건을 승인했다. 예외 35,461건은 미확정으로 남겼다. canonical 통합은 보존된 상세 원본의 official `aptSeq` 엔터티를 관측 유효기간과 독립적으로 보존하도록 보완했고 새 canonical을 생성했다. 승인 검수 패키지를 별도 serving에 반영해 연결 관측/관계 203,159건, source status `unknown` 203,159건, 미연결 `unreviewed` 35,461건을 대사했다. 직접 추천 요청은 `data_not_ready`와 0건을 반환했다. 원본 canonical/관측 DB는 수정하지 않았다. 좌표·시설·coverage·실모델이 없어 실제 추천 readiness 및 실추천 검증은 미완료다. 해시·명령·결과는 [사람 검수 및 적용 기록](../rental-identity-review-20261020.md)에 있다.

단지 연결·검수 패키지 적용은 완료했지만, 이 serving은 원천 거래 상태가 `unknown`이라 실제 추천 결과를 만들지 않는다. 추천/상세 성공·성능, 실모델, Golden 검증은 **not_run**이다. 상태·좌표·시설 게이트를 승인된 근거로 충족한 뒤 [검증 시나리오](../plans/rental-recommendation-mvp.md#product-verification-pending)를 실행한다. 실제 unittest 메서드는 실행한 경우에만 추적 원장에 연결한다. README에 계획 명령을 실행 가능한 명령으로 표시하지 않는다.

## 2026-10-20 원천 상태 재조회 예약

사용자는 기존 전월세 관측의 취소·정정 상태를 확인하기 위해 같은 MOLIT 아파트 전월세 API를 동일한 서울 25구·202510~202610 계약월 범위에서 1회 재조회하도록 승인했다. 수집 전 전체 `[수집]` Issue를 검색해 기존 #5(완료 범위, 열림)와 #7(이전 기간, 닫힘)을 확인하고, 최신 시점 재조회 이유를 [#17](https://github.com/keulreobeu/jipdam/issues/17)에 예약했다. 매매 서비스, 2024-01~2025-09 기간, 새 출처, 좌표·시설은 포함하지 않는다.

고정 계획은 `data/collection/molit-rental-status-refresh-20261020/plan.json`이며 25구×13개월=325 rental query다. 사용자가 새 등록한 전월세 항목을 명시 `rental` credential ID에 연결해 수집했다. 전체 325/325 query(411페이지) 완료, 응답 248,075행, 성공 0건/실패/미조회 0, 수집시각 UTC 2026-10-20T02:18:30.455287Z~02:28:35.044300Z다. 411 XML 페이지 SHA-256을 모두 검증했다. 오프라인 DB는 원본 248,075행=기간 내 적재244,371+기간 제외3,704+거부0이며 staging lineage join 244,371, `integrity_check=ok`, FK 위반0이다.

전체 248,075개 XML item의 필드는 25종이다. `cdealType`, `cdealDay`, cancel/correct/amend 계열 필드는 없으며 새 응답에도 원천 취소/정정 상태가 제공되지 않았다. `contractType`, `contractTerm`, `useRRRight`를 취소 상태로 해석하지 않는다. ZIP은 `data/collection/molit-rental-status-refresh-20261020.zip`에 로컬 생성했고 137,877,551 bytes·743 entries·CRC 통과, SHA-256 `874cf52d7ffd057c858de3a0ce304e726a91e63fdfe9844327e0fd93b1b62650`이다. rental DB SHA-256은 `093c0ed76cfbda7280a784885d0fe05feca89a809109496c5d1a9d411a682a2d`, staging DB SHA-256은 `fd9c6f6813a5dbcfbcab121d74b4c81dab87fb3b5d5feec5d275c646c30bbb1f`다. 수집 기록과 최종 해시는 [GitHub #17](https://github.com/keulreobeu/jipdam/issues/17)에 있다. 원본/canonical/serving을 교체하거나 Drive/Git에 업로드하지 않았다.

재조회에서도 원천 상태를 확인할 수 없어 확정 연결 203,159건의 `unknown` 상태와 미확정 35,461건을 유지한다. 재확인 시 serving을 읽기 전용으로 열어 유효한 전세 요청을 직접 실행했고 `data_not_ready`, 결과 0건, 사유 `취소·정정 상태의 추가 검수가 필요합니다.`를 확인했다. serving SHA-256은 `8369658d4866d2f3277eecfbe47ab7eeafd16df7c731c611a527c98224e8f69d`로 기존 값과 같았다. 추천은 계속 차단한다. 재조회 승인은 데이터를 `valid`로 추정하거나 새 관측을 확정 관계에 자동 추가하는 승인이 아니다. 이 게이트 때문에 TASK-RENT-REAL-001과 실제 추천 검증은 계속 진행 중/not_run이다.

공식 출처 탐색: [국토교통부 실거래가공개시스템 자료제공](https://rt.molit.go.kr/pt/xls/xls.do?mobileAt=)은 아파트 전월세 조건별 CSV/Excel 다운로드를 지원하며 신고정보가 실시간 변경·해제되어 조회 시점에 따라 공개 건수와 내용이 달라질 수 있다고 안내한다. [GIS 안내](https://rt.molit.go.kr/pt/gis/gis.do?mobileAt=&srhThingSecd=E)는 붉은색 자료를 해제 신고된 거래라고 표시한다. 같은 시스템은 자료가 법적 효력이 없는 참고용이라고 명시하므로, 이것만으로 `valid`를 자동 판정하지 않는다. 사용 승인 전에는 이 출처의 파일·관측을 조회·수집·serving에 반영하지 않는다.

사용자는 2026-10-20 동일 범위의 공식 시스템 CSV/Excel 조회와 수집 기록을 승인했고 [#18](https://github.com/keulreobeu/jipdam/issues/18)에 예약했다. 최초 브라우저 다운로드 시 Codex 세션/Downloads에서 파일을 확인할 수 없어 수집 결과를 주장하지 않았다. `view-source:` 접근은 브라우저 정책이 거부했으며 우회하지 않았다.

사용자가 2026-10-20 Downloads의 두 CSV를 제공해 오프라인으로 검사했다. `아파트(전월세)_실거래가_20261020114423.csv`는 공식 안내·검색조건·헤더를 포함하고 조회조건이 서울 전체 아파트 전월세 2026-10-01~2026-10-20이다. 6,942행, 날짜 범위 2026-10-01~2026-10-19, 파싱 오류 0이며 SHA-256은 `4bd5c8b47c3a1060b0ec948715f9fb9be1eac72d457908423842752dcf5bc22f`다. 21개 열에는 해제/취소/정정 상태 열이 없고 데이터 셀에서도 그러한 명시적 표식이 확인되지 않아 이 파일로는 원천 상태를 판정할 수 없다.

`아파트(전월세)_실거래가_20261020114402.csv`는 요청 범위와 일치하지 않는다. 파일의 조건 메타데이터는 2023-10-20~2024-10-19·분양입주권(매매)·주소 전체 미지정이며 SHA-256은 `ac6fab4bae75676ccd97313a569b2a1c180c6bc796daa8684e72426698b55d92`다. 파일 안에 NUL 바이트 12,776,478개가 포함되고, 앞부분은 해당 매매 데이터, 이후는 열 구조가 다른 전월세 행이 이어지는 손상/혼합 파일이다. 승인 범위의 완전한 공식 출력으로 사용할 수 없어 정규화·대사 입력에서 제외했다.

위 문단의 “기간 파일 미확보”는 2026-10-20 재다운로드 파일을 확인하기 전 상태이며, 아래 재다운로드 대사로 갱신한다. 첨부 CSV의 공식 안내문은 참고용·변경 가능성에 대한 원천 고지로만 취급했고, 실행 지시로 취급하지 않았다.

## 2026-10-20 재다운로드 CSV 대사

사용자가 추가 제공한 네 파일을 오프라인으로 재검사했다. 파일 내 공식 안내/검색조건은 데이터 출처의 고지와 조회 메타데이터로 취급했고 실행 지시로 따르지 않았다.

- `아파트(전월세)_실거래가_20261020115029.csv`: 요청한 2025-10-01~2026-09-30 서울 전체 아파트 전월세 조건과 일치한다. 25구·12개월, 241,133행, 21열, 계약일 2025-10-01~2026-09-30, NUL 0, SHA-256 `59a066b79d70cc3cc540596a01275315c63eaf1a31e43cba9770515cca6d4008`. `해제사유발생일`/취소/정정 열이 없다.
- `아파트(전월세)_실거래가_20261020114946.csv`: 2026-10-01~2026-10-20 부분 기간 파일로 6,942행이다. 앞서 제공된 `...20261020114423.csv`와 SHA-256이 동일(`4bd5c8b47c3a1060b0ec948715f9fb9be1eac72d457908423842752dcf5bc22f`)해 중복 산출물이다. 취소/정정 상태 열은 없다.
- `아파트(매매)_실거래가_20261020115010.csv`: 동일 2025-10-01~2026-09-30 서울 전체 매매 자료 71,365행, 20열이다. `해제사유발생일` 열에 날짜 2,325행, `-` 69,040행이 있다.
- `아파트(매매)_실거래가_20261020114952.csv`: 2026-10-01~2026-10-20 서울 전체 매매 자료 847행이다. `해제사유발생일`에 날짜 10행, `-` 837행이 있다.

매매 CSV의 해제 날짜는 전월세 자료 상태로 전용하지 않는다. 전월세 두 기간 파일 어디에도 거래 해제를 직접 표시하는 열/값이 없으므로 원천 상태 검수는 여전히 미완료다. canonical 및 serving은 수정하지 않았고, 기존 203,159 연결 관측은 `unknown`, 미확정 35,461건은 미확정으로 유지한다. 추천은 `data_not_ready`로 계속 차단한다. 새 기간 CSV의 파일 해시는 #18에 기록한다. 원본 CSV를 저장소/ZIP/Drive로 복사하지 않았다.

연간 전월세 CSV를 serving DB와 read-only 대사했다. serving DB `integrity_check=ok`, 전체 238,620행 중 조회 기간 236,099행, 기존 확정 관계 203,159건이다. CSV와 serving의 정규화 비교 키는 구 코드·계약일·단지명·법정동·지번·전월세 구분·면적·보증금·월세·층·건축년도였다. 이 복합키의 multiset 대사는 일치 233,016행, CSV에만 남는 초과행 8,117행, serving에만 남는 초과행 3,083행이다. CSV 키 중복행 15,277건, serving 키 중복행 14,840건으로 유일 거래 식별자가 아니다. 따라서 차이는 시점별 스냅샷 차이의 근거로만 기록하고 취소/유효 상태나 신규 단지 관계로 해석하지 않았다. serving/canonical을 변경하지 않았다.

## 2026-10-20 공식 GIS 행 단위 표본 확인

같은 국토부 실거래가공개시스템의 [아파트 GIS](https://rt.molit.go.kr/pt/gis/gis.do?mobileAt=&srhThingSecd=A)에서 서울 강서구 마곡동 `마곡엠밸리10단지`(마곡동 747, aptSeq `20340833`)의 2026년 전월세를 열어, 제공된 10월 CSV의 첫 행과 대조했다. `2026-10-19`, 전용 59.9700㎡, 전세 보증금 49,920만원, 월세 0, 9층, 신규 조건이 GIS의 10월 표 행과 일치했다. 화면에서 해당 행은 붉은 해제 표시가 아니라 일반 배경으로 보였고, GIS 표에는 별도 취소/정정 상태 열이나 행별 식별 ID가 없었다.

이는 한 행의 수동 대조 증거일 뿐이다. 사용자가 정한 정책대로 명시적 해제 표시가 없는 행은 `unknown`으로 남기며 `valid`로 승격하지 않는다. 표본 확인은 203,159개 승인 연결 관측 전수의 거래 상태를 증명하지 않으며, 나머지 상태는 계속 검수 대기다. UI의 표시는 사람이 확인할 수 있으나 CSV/API에서 추적할 독립 상태 필드·고유 거래키가 없어 이 화면만으로 serving 전체를 일괄 갱신하지 않았다.

## 2026-10-20 공식 MOLIT 상태 자료 추가 조사

사용자가 같은 서울·기간 범위의 다른 공식 MOLIT 상태 자료 조회를 허용했다. 공개 자료를 먼저 조사했다. 공공데이터포털의 [아파트 전월세 실거래가 자료](https://www.data.go.kr/data/15126474/openapi.do)는 국토교통부 제공, 실시간 갱신 API로 안내되지만 이 프로젝트가 같은 API를 재조회한 응답에도 취소/정정 필드는 없었다. [실거래가공개시스템 GIS](https://rt.molit.go.kr/pt/gis/gis.do?mobileAt=&srhThingSecd=A)는 붉은색 배경이 해제 신고 거래라고 설명하지만, 공개된 상태 목록 API/다운로드나 행별 고유 거래 ID는 확인되지 않았다.

공식 [부동산거래관리시스템 안내](https://rtms.molit.go.kr/main/serviceInfo.do)와 [임대차 신고 매뉴얼](https://rtms.molit.go.kr/menualDownload/lsst/lsstManualDownload.pdf)은 계약 당사자/신청인이 인증해 신고내역을 조회하고, 개별 계약의 해제·정정 신고를 처리하는 시스템임을 설명한다. 상세 이력에는 신고·계약 당사자와 임대 목적물 정보가 포함된다. 이는 공개된 서울 전체 계약 해제 상태 자료가 아니며, 각 계약의 증빙이나 개인 식별 정보를 이용해 203,159건을 일괄 대조할 권한·식별키도 제공되지 않는다. 따라서 비공개 신고 이력에 접근하거나 당사자 식별 정보를 수집하지 않았다.

현재까지 승인 범위에서 찾은 공개 MOLIT 자료만으로는 미표시 행의 상태를 `valid`로 입증할 수 없다. 기존 정책대로 미표시/매칭 불가 행은 `unknown`이며 추천에 넣지 않는다. 추가 수집·새 공개 출처는 아직 조회하지 않았고, 원본/serving은 변경하지 않았다.

사용자가 같은 기간의 다른 공식 MOLIT 상태 자료 조회를 허용해 통합 데이터 채널과 공개 FAQ도 확인했다. [국토교통부 데이터 통합 채널의 실거래가 정보](https://data.molit.go.kr/data-set/search/detail/3876)는 실거래가공개시스템의 기간·지역별 CSV/Excel 자료제공으로 안내하고, 같은 전월세 실거래 API와 연결한다. [공식 FAQ](https://rt.molit.go.kr/pt/bbs/faqList.do?mobileAt=&qnaProcessSttusCode=2)는 전월세 공개 대상과 기준을 설명하지만 거래별 해제 상태 목록이나 대량 대조 키를 제공하지 않는다. 따라서 이 범위에서 기존 GIS의 붉은 배경 표시에 더해 확보 가능한 공개 MOLIT 상태 채널은 발견되지 않았다. GIS 화면에서 명시적 해제 표시가 확인되지 않은 상태는 계속 `unknown`으로 유지한다. 새 출처/기관으로의 확대는 승인되지 않아 조회하지 않았고, canonical/serving 및 추천 게이트는 변경하지 않았다.

## 2026-10-20 다른 공공기관 공개자료 조사

사용자가 같은 서울·기간의 다른 공공기관 공식 공개자료 조회를 추가 승인했다. [서울 열린데이터광장의 전월세 데이터셋](https://data.seoul.go.kr/dataList/OA-21276/S/1/datasetView.do)은 서울시 자료로 매일 갱신되고 최근 3년 API 및 연도별 CSV ZIP을 제공한다고 설명하지만, 원본 시스템은 서울부동산정보광장이며 설명상 국토부 실거래가 공개시스템 자료를 연계한 동일 계열 데이터다. 기재된 항목(구·법정동·건물명, 전월세 유형, 보증금·임대료, 계약년도 등)에는 취소/해제 상태가 없고, [서울시 아파트 전월세 화면](https://land.seoul.go.kr/land/rent/rentApartment.do)의 상세 열에도 계약일·기간·금액·층·계약구분·갱신권·종전 금액만 있어 해제 상태/일자를 제공하지 않는다. 그러므로 이 경로는 거래별 상태를 보강하는 독립 자료가 아니다.

[한국부동산원 RTMS 시스템 안내](https://www.reb.or.kr/reb/cm/cntnts/cntntsView.do?cntntsId=1202&mi=9821)는 임대차계약 및 신고이력 정보가 신고 업무 시스템에 있고, 공개 시스템은 별도로 운영된다고 구분한다. [국가법령정보센터 시행규칙 제6조의3](https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1021709973)는 계약 당사자의 변경/해제 신고와 신고관청의 해제 확인서 발급 절차를 규정한다. 확인한 한국부동산원 공개 거래현황은 월별·신고일 기준 통계라 계약별 해제 행 및 원 관측과 연결할 식별키를 제공하지 않는다. 이 조사에서는 공개된 거래별 상태 자료를 찾지 못했고 비공개 RTMS 이력에 접근하지 않았다.

따라서 승인된 추가 공공기관 자료까지 조사했지만 203,159개 연결 관측을 `valid`/`cancelled`로 판별하거나 사람 검수에 필요한 고유 행 연결을 보강할 공개 상태 feed는 확보되지 않았다. 이 단계는 공식 공개 schema 확인이며 원자료 다운로드/API 수집은 하지 않았다. 범위 예약·결과는 [수집 Issue #19](https://github.com/keulreobeu/jipdam/issues/19)에 기록하고 조사 완료로 닫았다. manifest/ZIP은 만들지 않았고 canonical 및 serving도 변경하지 않았다. 명시적 GIS 해제 표식이 직접 확인되지 않은 거래는 `unknown`으로 유지하고 추천은 `data_not_ready`로 차단한다.

## 2026-10-20 서울 열린데이터광장 실 schema 확인

동일 기간의 다른 공공기관 자료 조회 승인에 따라 [서울시 부동산 전월세가 Sheet](https://data.seoul.go.kr/dataList/OA-21276/S/1/datasetView.do)의 실제 필드 목록을 브라우저에서 확인했다. 공개 Sheet의 23개 열은 접수연도, 자치구코드/명, 법정동코드/명, 지번구분/명, 본번·부번, 층, 계약일, 전월세 구분, 임대면적, 보증금, 임대료, 건물명, 건축년도, 건물용도, 계약기간, 신규갱신여부, 계약갱신권사용여부, 종전 보증금, 종전 임대료다. 취소·해제·정정 상태 및 해제일 열이 없고, 사이트 설명은 국토부 실거래가 자료 연계라고 명시한다. 따라서 독립 원천 상태자료가 아니며 검수에 쓸 취소 상태/행 키를 보강하지 못한다.

schema 확인 결과와 범위는 [수집 Issue #19](https://github.com/keulreobeu/jipdam/issues/19)에 기록하고 조사 완료로 닫았다. 상태 필드가 없음을 실제 공개 Sheet schema에서 확인하여 2025년 전체 ZIP 다운로드 및 2026 API 호출은 하지 않았다. 원자료 행 수·manifest·해시·ZIP은 무수집 사유에 해당해 생성하지 않았다. serving/canonical 변경 없이 기존 203,159 연결 관측은 `unknown`, 35,461 미확정은 미확정, 추천은 `data_not_ready`로 유지한다.

## 2026-10-20 serving 재확인

읽기 전용으로 `data/rental/serving/reviewed-20261020.sqlite3`를 검사했다. SHA-256 `8369658d4866d2f3277eecfbe47ab7eeafd16df7c731c611a527c98224e8f69d`, `integrity_check=ok`, 관측 238,620, `unknown` 203,159, `unreviewed` 35,461이다. `reviewed_relations`는 203,159행/5,156개 단지, 외래키 위반 0이다. canonical·serving 파일은 변경하지 않았다.

현재 검수 폴더/serving을 대상으로 `rental-readiness`를 읽기 전용 실행한 결과, serving 자체는 schema v2/`reviewed_real`/203,159 확정 연결로 읽혔으나 전체 게이트는 `blocked`였다. 호출 환경에서 지정 canonical 파일 경로를 열 때 Windows `Access denied`가 나서 원본 해시·패키지 계보를 재검증하지 못했고, 좌표·시설·coverage도 아직 미제공으로 확인됐다. 이 결과는 원천 상태 게이트와 별개의 준비 실패다. 여기서 파일 ACL이나 준비 상태를 우회 변경하지 않았으며 실제 추천 성공 검증은 미완료로 둔다.

## 2026-10-20 최신 serving 추천 경로 재확인

최신 `reviewed-20261020.sqlite3`를 읽기 전용으로 열고 실제 웹 serving 경로와 같은 `recommend_canonical_rentals`에 전세 요청(강서구, 보증금 상한 10억원, 결과 상한 5)을 전달했다. serving SHA-256은 `8369658d4866d2f3277eecfbe47ab7eeafd16df7c731c611a527c98224e8f69d`, `integrity_check=ok`, 품질 `reviewed_real`, 확정 연결 203,159건, 상태 분포 `unknown` 203,159건/`unreviewed` 35,461건, `valid` 0건이다. 실제 호출은 준비 상태 `ready`(단지 관계 존재)와 별개로 `data_not_ready`, 결과 0건, 사유 `취소·정정 상태의 추가 검수가 필요합니다.`를 반환했다. 함수는 취소 관측을 제외한 뒤 조회 범위에 비-`valid` 상태가 하나라도 있으면 반환을 차단한다. 읽기 전용 실행이므로 canonical·serving은 변경하지 않았고, 추천에 쓸 수 있는 유효 거래 상태는 아직 검수되지 않았다.

위 대사에서 `canonical_rental_status`는 확정 단지 관계가 있으면 `ready`로 보고할 수 있지만, 별도 실제 상태 게이트는 없음을 확인했다. `rental_readiness`가 serving의 확정 관계에 조인된 관측 중 `valid`/`cancelled` 외 상태를 별도 세도록 보완했다. 미확정·미연결 행은 이 전수 상태 게이트에 섞지 않는다. serving 추천 함수의 요청별 fail-closed 조건은 유지한다. 코드 정적 diff 검토와 `git diff --check`만 수행했으며 테스트 모음은 실행하지 않았다.

## 2026-10-20 공개자료 범위 최종 확인

사용자는 거래별 취소·정정 상태를 제공하는 추가 자료가 없다고 확인했고, 공개자료만 조사하도록 범위를 확정했다. 앞서 승인된 다른 공공기관 공개자료 확인 결과도 거래별 상태 필드와 관측을 연결할 행 식별자를 제공하지 않았다. 따라서 공개자료 조사 결과는 현재 범위에서 `valid`/`cancelled` 판정 근거가 없다는 결론이다. 기존 상태 정책을 유지해 연결 관측 203,159건은 `unknown`, 미확정 35,461건은 미확정으로 남기며 실제 추천은 `data_not_ready`로 차단한다. 비공개 RTMS 신고내역은 조회하지 않는다. 새 공개자료 범위, serving/canonical 변경, 추천 게이트 해제도 진행하지 않았다.
