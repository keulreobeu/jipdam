# STATS-001 — 제공된 통계 엑셀의 별도 보존·적재

```toml
kind = "spec"
id = "STATS-001"
status = "approved"
owner = "Codex"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-13"
approval_ref = "2026-10-13 이전 12개와 신규 18개 제공 엑셀을 함께 저장하고 통계 전용 DB 공간을 만들라는 사용자 요청. 기준월/추가 메타데이터는 사용자가 후속 정리."
```

## 범위

사용자가 이미 수집해 Downloads에 제공한 30개 파일을 오프라인으로 보존·적재한다. 전용 SQLite `data/statistics/statistics.sqlite3`와 SHA-256 주소의 raw 아카이브를 사용한다. 기준기간은 셀에서 읽으며 전체 제공 이력을 보존한다. 외부 수집/API 호출·키 접근·GitHub 게시·Drive 업로드·추천 연결은 이번 요구에 포함하지 않는다. 기존 거래 canonical, historical, rental DB는 통계 DB로 변경하지 않는다.

## STATS-001-REQ-01 원본과 계보

등록된 파일명/매핑만 받고 원본 bytes·SHA-256·파일명·수입 배치·적재 UTC를 보존한다. 관측마다 시트·행·열·원문 날짜헤더·원문값과 원본 파일 관계를 남긴다. Excel numeric XML 원문은 Decimal 문자열로 저장하고 REAL은 조회 보조다. 외부 다운로드 시각·공표일은 제공되지 않으면 NULL이다. 적재일을 출처 기준일로 대체하지 않는다.

### STATS-001-AC-01

모든 입력 해시와 보존본이 같고 모든 날짜셀을 numeric/missing 상태로 대사하며 각 관측을 원본 셀로 역추적한다.

## STATS-001-REQ-02 기간·지역·차원·단위

주간/월간 기간을 명시적 registry로 선택한다. 날짜헤더의 시분초는 원문에 남기고 월은 YYYY-MM, 주는 YYYY-MM-DD로 조회한다. PIR 제공 파일은 월간 소득분위×주택분위이며 담보대출 PIR로 바꾸지 않는다. 지역명만으로 공식 행정코드를 추정하지 않고 표의 상위지역/권역 문맥을 보존한다. 원천 `-`/빈 셀은 missing, 숫자 0은 numeric이다. bool/비유한/미등록 텍스트/수식/중복기간/잘못된 표 구조는 전체 적재를 거부한다.

가격은 원본의 만원 단위 평균 수치(정수가 아닐 수 있음), 지수/비율/건수/배수는 각 registry 단위를 보존하며 거래 금액으로 환산하지 않는다. 확인되지 않은 단위 정의·지수 기준시점·출처 기준일은 provisional/NULL이다. 사용자의 파일 기준 우선 지시에 따라 가격지수 4개는 파일의 100 기준점과 공식 안내를 대조해 월간 2026-01, 주간 2026-01-12를 effective_base_period 검수 이력으로 추가한다. 이전 일반 기준월 메모는 보존한다. 서울 dashboard 반올림, 전체 통계표, 선도 dashboard 등의 source_view를 구분한다.

### STATS-001-AC-02

월/주·PIR 분위·동명이인 지역문맥·missing/0·정밀도·구조 오류의 검증과 rollback이 재현된다.

## STATS-001-REQ-03 재실행·개정 보존

같은 배치 ID와 같은 파일/registry 지문 재실행은 신규 0이고 DB를 바꾸지 않는다. 같은 배치에 바뀐 입력은 거부한다. 새 배치의 동일파일은 사실을 재사용하고 배치소속만 기록한다. 다른 bytes의 개정본은 이전 관측을 보존한다. 같은 배치에 같은 dataset의 서로 다른 개정본은 거부해 우선순위를 추정하지 않는다. latest view는 dataset/source_view/series/period별 가장 나중의 명시적 수입 배치를 선택한다. 대시보드 반올림본과 상세표는 서로 덮어쓰지 않는다.

### STATS-001-AC-03

반복·새 배치·개정본·변경배치 거부와 다른 source_view 보존을 확인한다.

## STATS-001-REQ-04 격리와 실제 데이터

statistics 전용 application_id/schema만 쓴다. 다른 SQLite를 대상 경로로 지정하면 변경 전에 거부한다. raw 파일은 콘텐츠 해시로 복사하며 Downloads는 수정하지 않는다. source_status는 user_supplied_pending_review다. 지금 허용된 것은 제공 원본의 별도 적재이며 KB/공공통계의 사용권·통계 메타데이터 검수 또는 실제 추천 완료를 뜻하지 않는다.

### STATS-001-AC-04

30개 실제 입력·파일별 기간/행/관측/결측 건수·PK/FK/무결성·원본 셀 대사와 기존 DB 경로 격리를 확인한다.

## STATS-001-REQ-05 실행과 후속 검수

statistics import/status/audit CLI, source registry, 수입 요약/manifest 및 사용 문서를 제공한다. 일별/월별 헤더의 기준기간과 파일명 다운로드날짜를 구분한다. 사용자 후속 정리의 출처·단위·기준시점은 별도 검수 이력으로 연결하며 파일·공식 안내로 확인한 항목만 근거와 함께 추가한다.

### STATS-001-AC-05

CLI로 등록 파일만 적재·읽기상태 조회·오류 종료가 재현되고 사용자 보완 항목·추가 통계 후보가 문서로 남는다.
