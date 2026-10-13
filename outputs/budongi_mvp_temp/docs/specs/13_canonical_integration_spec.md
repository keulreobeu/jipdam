# CANONICAL-001 — 출처·배치 이력을 보존하는 통합 관계형 DB

```toml
kind = "spec"
id = "CANONICAL-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-13"
approval_ref = "2026-10-13 저장된 canonical-db-continuation-20261013 계획에 대해 사용자가 '후속 통합 계획대로 진행 (추천)' 선택: 공통 엔터티·공식ID 관계·미확정 후보·반복/증분·CSV/JSON/XLSX 입력 계약 구현/검증 승인"
```

## 범위와 승인 경계

기존 서울 세 XML 출처의 원본을 재사용하여 단일 canonical DB에서 조회·조인·반복/증분 검증을 수행한다. 원래 전월세/매매 관측 DB와2023역사DB는 보존한다. 출처·배치·행정구역·관측·단지·건물·주소 모델을 정의하고 실제 제공된 공식 출처ID 근거만 확정 연결한다. 미확정 라벨 후보는 별도 보관하며 자동 확정/거래 병합을 하지 않는다.

파일 입력 어댑터는 등록된 CSV/JSON/XLSX 출처의 동일 보존/정규화/추적/적재 계약을 지원한다. 현재 실제 필수 수집 출처는 MOLIT-001의세 API이며 새 실제 출처는 별도 Source Registry 승인 없이 수집/적재하지 않는다. 좌표·시설·추천·Golden·Drive 업로드·새 API 호출·Git 자격증명 접근은 승인에 포함하지 않는다.

## CANONICAL-001-REQ-01 현재 입력과 원본 보존

통합은 네트워크/보관함 없이 보존 파일로만 동작한다. 전체 완료를 기본으로 요구하며 명시적 부분 입력은 완료 query만 사용하고 누락 범위를 남긴다. 원본 페이지/hash/query 범위, 계획hash와derived manifest·DBhash의 일치 여부를 검사한다. 패키징과 통합은 같은 현재 입력 검증을 공유한다. 기존 출력과 원본을 덮어쓰지 않는다.

### CANONICAL-001-AC-01 입력 무결성

현재 아카이브와 DB가 일치한 경우만 적재한다. 동일 건수지만 다른 원본, 계획 변경, 누락/변조/이전 partial DB는 거부한다. 기존 pack의 명시적allow-partial과stale거부 회귀를 유지한다.

## CANONICAL-001-REQ-02 공통 모델·식별·관계

출처와 내부ID를 구분하고 FK로 출처/행정구역/원본/관측·엔터티를 연결한다. 공통 모델에는 complex/building/address/region을 포함하되 원천에 식별 근거가 없는 엔터티는 미연결/NULL로 둔다. `aptSeq`는 MOLIT 출처namespace의 단지 ID이며 실제 거래ID가 아니다. 지역 등 근거가 충돌하면 확정 연결을 중단하고 사유를 격리한다. 주소는 확인된 행정/법정동·본번/부번·토지구분 등 출처 성분을 검증하며 명칭만으로 ID를 만들거나 지오코딩하지 않는다.

### CANONICAL-001-AC-02 관계 무결성과 조인

실제 전체 유효관측을 출처·행정구역·원본 및 확인된 공식 ID관계로 조인한다. PK/FK/UNIQUE/NOT NULL/CHECK를 정의하고 전체 검증을 통과한다. 연결 불가 엔터티는 실제 건수와 이유를 보고한다.

### CANONICAL-001-AC-03 불확실한 관계

동일 이름/동/지번은 근거를 가진pending 후보이며 확정 FK가 아니다. 후보별 신뢰 상태·근거·지원 관측을 추적한다. 여러 공식ID에 해당하면 모두 미확정으로 보존한다. 서로 다른 동일 값 행과 일반/상세 관측은 유지하고 자동 동일거래 연결/합산을 하지 않는다.

## CANONICAL-001-REQ-03 시간·배치·버전·증분

계약일, 제공기관 기준일/유효기간, 실제수집시각, 배치기준일, 적재시각을 구분한다. 제공되지 않은 시간은NULL이다. 콘텐츠 식별과 배치별 파일/관측 소속은 별도로 보존한다. 같은batch/version/input의재실행은새관측/소속0이다. 같은batch/version에다른입력은거부한다. 새로운배치와새정규화버전은기존불변기록을유지한다. 비슷한내용을실제정정거래로자동연결하지않는다.

### CANONICAL-001-AC-04 반복·증분 일관성

같은배치반복, 겹치는새배치, 새정규화버전, 같은batch입력충돌, 실패rollback을검증한다. 콘텐츠재사용과새로운배치소속이력을구분하고전체관측/대사결과를기록한다.

## CANONICAL-001-REQ-04 파일/새 출처 확장

Source Registry에source ID·출처종류·승인/범위·format·mapping version·단위·section/시트/JSON선택·목표record type과필드매핑을명시한다. 원본파일을바이트보존하고보존복사본만파싱한다. 모든시트/선택대상·예상/실제수·제외조건을추적한다. 원본row/section과정규화payload는서로구분한다. 정확한금액/날짜/코드/NULL/필수공백/중복헤더를검증하고거부사유를남긴다. 기본공개DB는필수값오류/완료대사실패시전체rollback하며유효행을누락하지않는다.

### CANONICAL-001-AC-05 형식 확장과 추적

CSV/JSON/XLSX가공통raw→staging→validation→canonical계약을따른다. 시트/section키충돌,필수공백,잘못된날짜/금액단위,원본변조,등록없는입력,건수불일치를검증한다. 합성입력검증과실제출처수집완료는별도로표시한다.

## CANONICAL-001-REQ-05 원본·정규화 대사와 실제 실행

모든완료query의원본행은valid/outside_period/rejected상태와원본위치/사유로보존한다. raw=valid+excluded+rejected,valid=실제canonical관측수=전체lineagejoin수를대사한다. 오류중간출력을최종성공으로게시하지않는다. 출력DB/품질보고에는입력hash/스키마·매핑버전·범위/완료/출처품질이있다.

### CANONICAL-001-AC-06 실제 전체 검증

보존된실제975query의384211원본/374892유효/9319기간제외/0거부를통합DB에서확인하고재생성·중복적재/증분·SQL조인/제약/정렬digest를검증한다. 실제엔터티연결과미확인범위를과장하지않는다.

## CANONICAL-001-REQ-06 운영·문서·기존 경계

CLI조회/적재/검증/오류종료를명시하고출처/스키마/매핑/확장방법/실행/품질보고를문서화한다. 원본·DB·ZIP·키는Git에넣지않는다. 기존2023명령/전월세추천의source_unverified차단과키비노출을유지한다. 원격GitHub결과게시/Drive업로드는별도권한과COLLECT-001을따른다.

### CANONICAL-001-AC-07 운영·회귀·문서

CLI/기존회귀/환경·SDD검사를통과하고모든AC의합성/실제증거와미완료조건을Task에기록한다. 통합Goal9조건을실제확인하기전Goal완료로표시하지않는다.

## 관련 문서·검증 상태

[Plan](../plans/canonical-db-continuation-20261013.md), [ADR-006](../adr/ADR-006-canonical-batches-and-identity.md), [Task](../tasks/canonical-integration.md), [재개 실제입력](../molit-resume-validation-20261013.md). 승인된 범위의 구현·실제 전체/증분/복사 변환·등록 파일 계약 검증은 완료했다. 완료의 원본은 verified Task와 실제 SQL/테스트 및 Goal 완료 감사 증거다. 추천 서비스·좌표·시설·신규 실제 출처·Drive 업로드의 완료를 뜻하지 않는다.
