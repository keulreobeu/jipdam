# 제공 통계 30개 오프라인 수입 Plan

요청: 이전 12개+신규 18개를 함께 보존하고 통계를 따로 저장. 승인 근거는 STATS-001이다.

구조: 기존 SQLite/openpyxl과 CLI를 재사용한다. statistics_storage.py는 등록 엑셀 검사·원본보존·cell 관측·SQLite 배치를 담당하고 statistics_cli.py는 import/status를 제공한다. 전용 statistics_sources.json에 명시적으로 허용된 30종과 source_view/frequency/layout/잠정 단위를 둔다. 기존 거래 source_registry와 거래모델은 재사용하지 않는다. 자료형과 기간/지역 구조가 거래행과 다르기 때문이다.

흐름: 명시적 파일목록 → registry/전체 시트 검사 → SHA 보존 → 단일 transaction → 파일/배치/series/관측/구조건수 → manifest/SQL 대사. 원본값·원본 셀 참조와 latest view를 모두 남긴다. 매핑지문이 바뀌면 같은 배치를 재사용할 수 없다.

실패: 입력 누락/미등록/수식/이상값/중복기간/같은 dataset의 복수 개정본/다른 DB 스키마는 전체 rollback 또는 게시 전 거부. 원본 아카이브는 실패 후에도 보존할 수 있지만 실패 수입을 성공으로 표시하지 않는다. 재실행은 입력값 파싱까지 확인한 뒤 같은 지문이면 DB 변경 0이다.

검토: 반올림 서울 dashboard와 전체지역 상세표를 dataset/source_view로 구분한다. 지역문맥은 원천 구조를 보존하며 공식 행정코드로 자동 승격하지 않는다. 평균가격의 원본 만원과 통계비율을 거래 원 정수로 섞지 않는다. PIR 파일의 월간/분위차원, 결측 `-`, 개정이력, 원본 변조, PK/FK, 원본 재확인 및 actual row audit을 검증한다. 입력→DB는 전부 오프라인이며 API/보관함 접속 경로가 없다.

순서: Spec/ADR/Task/원장 → registry/저장기/CLI → 의미 있는 계약검사 → 실제 30개 적재/셀대사 → 문서/환경/SDD 검사. 제품계약 승인 요구를 다시 묻지 않으며 세부 파일구조는 작업자가 결정한다. 별도 정식 gstack plan-eng-review 실행/외부 리뷰 완료를 주장하지 않는다.

실행 보완: statistics_audit.py에서 실제 원본 XML 정밀도/전체 셀/심리 반올림 중복을 대사하고 metadata_reviews에 근거를 추가한다. 신규 원본을 다운로드하지 않고 제공 파일과 보존 사본만 읽는다. 파일 헤더의 YYYY.MM.DD와 YYYY-MM-DD/주·월 표시를 각각 엄격 파싱한다. 사용자 업데이트 메모(2026.08~10)와 실제 수록기간·100 기준시점은 별도로 기록한다.
