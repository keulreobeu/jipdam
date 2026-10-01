# 임시 단지 자료

`apartment_20230905`는 사용자가 제공한 CSV의 출처와 기준일을 아직 확인하지 못한 개발용 자료입니다.
`source.csv`는 원본 바이트를 보존한 사본, `apartment_catalog.csv`는 단지명+주소로 묶은
임시 카탈로그, `profile.json`은 입력 해시·행 수·결측 요약입니다. 생성 파일은 Git에서 제외합니다.

`api/`에는 국토교통부 실거래와 청약홈 분양 API의 조회 시점 원본을 별도 폴더로 저장합니다.
각 폴더의 `manifest.json`에 조회 범위·시각·응답 해시가 기록됩니다. 계약 연도나 모집공고일이
2023년이어도 과거 시점 그대로 보존된 자료라는 뜻은 아닙니다.

`legal_district_codes/`는 행정표준코드관리시스템에서 내려받은 법정동 코드 ZIP과 해시입니다.
`api/molit_2023_catalog/`는 임시 카탈로그의 지역별·월별 조회,
`api/molit_2023_successors/`는 인천·부천·화성 행정구역 변경 후속 코드의 조회 원본입니다.
`matching_2023/report.json`은 단지명·동·지번을 비교한 **검수 후보**로, 동일 단지 확정이나
2023년 말 스냅샷이 아닙니다. 각 수집의 재현 명령은 루트 `README.md`에 있습니다.

프로젝트 루트에서 다음 명령으로 다시 생성합니다.

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python scripts/stage_legacy_apartments.py `
  'C:\Users\SSAFY\Downloads\apartment_20230905 - apartment_20230905.csv.csv' `
  --output-dir data/provisional/apartment_20230905
```

파일명에 있는 날짜는 검증된 데이터 기준일이 아닙니다. 이 파일의 `공급액(만원)`은 분양·공급액이며
실거래가가 아닙니다. `입주예정연도`도 준공연도가 아닙니다. 원천 거래 ID·계약일·정정/취소 이력이
없으므로 이 자료만으로 `data/historical/serving.sqlite3`의 역사 스냅샷이나 실측 평가를 만들지 않습니다.
