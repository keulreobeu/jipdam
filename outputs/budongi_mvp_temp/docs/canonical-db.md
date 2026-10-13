# 통합 DB 실행·조회·출처 확장

CANONICAL-001의 오프라인 통합 경로다. 실제 필수 수집 출처는 Source Registry의 세 MOLIT XML API다. CSV/JSON/XLSX 지원은 합성 시험으로 검증하며 신규 실제 자료 수집 완료를 뜻하지 않는다. 실제 해시·건수·검증 한계는 [검증 기록](canonical-validation-20261013.md), 승인 범위는 [Spec](specs/13_canonical_integration_spec.md)을 따른다.

## 보존 XML 통합과 증분

프로젝트 폴더에서 실행한다. 모든 출력은 새 경로를 사용한다. `--previous`는 이전 봉인 DB의 해시·무결성을 확인하여 새 사본에 적재한다. 원본·이전 DB·2023 역사 DB는 변경하지 않는다.

```powershell
python -m budongi.cli collection status --directory data/collection/BATCH
python -m budongi.cli collection build-db --directory data/collection/BATCH --output data/collection/BATCH/db-new
python -m budongi.cli collection integrate --directory data/collection/BATCH --db-directory data/collection/BATCH/db-new --output data/collection/BATCH/canonical-new
python -m budongi.cli collection integrate --directory data/collection/NEXT --previous data/collection/BATCH/canonical-new --output data/collection/NEXT/canonical-new
```

기본은 전체 조회 완료를 요구한다. `--allow-partial`은 완료 범위만 넣고 누락 범위를 남긴다. 오래된 계획·원본·DB의 조합은 거부한다. 재파싱/적재는 네트워크·키 보관함을 사용하지 않는다. 같은 배치/매핑 버전의 입력 변경은 새 배치 또는 새 버전을 요구한다. 같은 값의 다른 원본 행은 별도 관측이다. 매매 일반·상세를 동일 거래로 합치지 않는다.

## 공통 모델

| 테이블 | 역할 |
| --- | --- |
| sources, regions | 출처/데이터셋/형식/문서, 지역 코드 |
| batches, coverage | 배치/버전/기준일/기간/입력 서명, 출처·지역·월 범위/상태 |
| raw_blobs, raw_files, batch_files | SHA 콘텐츠, 출처별 파일 참조/행 수, 배치별 소속/수집 시각 |
| raw_items, staging_items | 전체 원문·섹션·행 위치, 배치별 valid/outside_period/rejected와 사유 |
| observations, batch_observations | 원본 행/버전 UNIQUE, typed 관측과 배치별 소속 |
| complexes, buildings, addresses | 공식 namespace/출처 ID, 검증된 주소 성분, 지역 FK |
| complex_address_evidence | 단지·주소·지원 관측 근거 |
| identity_conflicts | 공식 ID 충돌 사유/근거, 확정 연결 중단 |
| match_candidates | 지원 관측/근거, pending/unverified/점수 NULL |

공통 스키마는 canonical_real_estate_v3(user_version=3)이다. 여러 지역·월이 든 파일은 batch_files의 지역/월이 NULL이며 행별 관측과 coverage가 범위를 보존한다. v2는 새 사본에서 파일 범위 컬럼만 NULL 허용으로 변환한다. 기존 파일과 나머지 행 값은 유지한다. 출력은 INSERT/UPDATE/DELETE 차단 트리거로 봉인하며 PK/FK/UNIQUE/NOT NULL/CHECK를 사용한다. 형식과 엔터티 경계의 채택 이유는 [ADR-006](adr/ADR-006-canonical-batches-and-identity.md)을 따른다.

MOLIT aptSeq는 molit_apt_trade_detail:aptSeq namespace의 단지 ID다. 거래/건물 ID가 아니다. 실제 세 API에는 공식 건물 ID가 없으므로 buildings 0건, building_id NULL이다. 후보를 확정 FK로 자동 승격하지 않는다. 원천 품질 source_unverified는 사람 검수/추천 적합성을 뜻하지 않는다.

계약일은 observations.contract_date, 제공된 원천 유효기간은 source_effective_from/to, 수집 시각은 batch_files.retrieved_at_utc, 배치 기준일/기간은 batches.snapshot_date/observation_from, 현재 출력 적재 시각은 quality-report.json의 loaded_at_utc로 구분한다. 제공되지 않은 유효기간은 NULL이다. 과거 적재 시각은 보존된 해당 출력 보고를 따른다.

## 읽기 전용 조회

```sql
SELECT source_id, COUNT(*) FROM observations GROUP BY source_id;

SELECT COUNT(*) AS lineage_rows
FROM batch_observations b
JOIN observations o USING(observation_id)
JOIN raw_items r USING(raw_item_id)
JOIN raw_files f USING(file_id)
JOIN sources s ON s.source_id=o.source_id
JOIN regions g ON g.sgg_cd=o.sgg_cd
JOIN batch_files m ON m.batch_id=b.batch_id AND m.file_id=f.file_id
WHERE b.batch_id=:batch_id;

SELECT COUNT(*) AS official_complex_address_rows
FROM batch_observations b JOIN observations o USING(observation_id)
JOIN complexes c USING(complex_id)
JOIN complex_address_evidence e ON e.observation_id=o.observation_id AND e.complex_id=c.complex_id
JOIN addresses a USING(address_id) WHERE b.batch_id=:batch_id;

PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

다중 배치의 소속 수 합계와 전체 고유 관측 수는 구분한다. 품질 보고는 전체 테이블 수와 해당 배치 raw/valid/staging/lineage 수를 구분한다. 원본은 batches.archive_root와 raw_files.file_ref로 추적한다. 이동 시 상대 참조와 manifest를 보존하고 archive_root는 역사 위치 기록으로 취급한다.

## 신규 파일 등록과 실행

실제 출처는 별도 승인 후 Source Registry에 source_id, dataset_id, documentation, status=approved, approval_ref, scope, format, record_type, mapping_version, expected_rows, field_mapping을 명시한다. 기본 지역은 서울 코드이며 regions의 코드→명칭 사전으로 범위를 선언할 수 있다. 예상 행 수가 없으면 complete=false다. 승인되지 않은 출처를 수집·적재하지 않는다.

현재 목표 record_type은 rental/sale이다. 필수 표준 필드와 매핑 타입은 sgg_cd(string), contract_date(date), apartment_name(string), area_sqm(number), rental의 deposit_krw/monthly_rent_krw 또는 sale의 price_krw(amount_krw)다. 모두 required=true를 선언한다. 금액 단위는 krw/manwon만 허용하며 64비트 원 정수로 변환한다. 결측 금액을 0으로 채우지 않는다. 면적>0/금액>=0과 종류·금액 일치를 검증한다. 큰 Excel 금액은 정확한 텍스트 셀로 제공하며 안전한 정수 범위를 넘는 부동소수 금액은 거부한다.

선택 필드는 legal_dong/jibun, floor/build_year(integer), source_record_id, source_effective_from/to(date), source_complex_id/source_building_id다. 공식 엔터티 ID에는 official_identifiers.complex/building의 namespace와 basis가 필요하다. 단지/건물 ID는 별도이며 건물 ID만으로 단지 소속을 추정하지 않는다. 주소의 legal_dong_code/main_number/sub_number/land_code는 address_basis와 함께 모두 제공한다. 지역·코드·4자리 번호·토지구분으로 표준화하며 좌표를 추정하지 않는다.

CSV는 encoding/delimiter, JSON은 items_path와 중첩 field_mapping.column 경로를 선언할 수 있다. JSON의 전체 원본 바이트/선택 경로를 보존하며 소수 숫자는 원문 숫자 문자열로 읽어 금액 정밀도를 유지한다. XLSX는 모든 시트를 파싱하며 sheets 선언은 실제 전체 집합과 일치해야 한다. 빈 시트와 expected_rows_by_section도 대사하고 수식을 실행하지 않는다.

```powershell
python -m budongi.cli collection stage-file --registry APPROVED_REGISTRY.json --source-id REGISTERED_ID --input ORIGINAL.csv --output data/collection/FILE_STAGE
python -m budongi.cli collection integrate-file --registry APPROVED_REGISTRY.json --directory data/collection/FILE_STAGE --batch-id UNIQUE_BATCH --snapshot-date 2026-10-12 --observation-from 2025-10-12 --record-url COLLECTION_RECORD_URL --output data/collection/FILE_CANONICAL
```

증분 파일 적재는 integrate-file에 --previous PREVIOUS_CANONICAL을 추가한다. source_files는 원본/섹션/매핑 검증, collection_integrate는 공통 적재, collection_cli는 명령을 담당한다. 현행 관측에 맞는 신규 출처는 등록·매핑으로 추가한다. 새 종류의 사실은 별도 Spec/ADR와 목표 레코드 계약을 확정해 어댑터를 추가한다.

## 오류·품질·검증

파일 원본을 바이트 보존하고 staging.sqlite3에 모든 행/정규화/거부 사유를 남긴다. 통합 전 원본을 다시 파싱해 staging 전체 값·행 위치·건수를 대사한다. 계약 변경·원본/DB 변조·불완전 수집·거부 행이 있으면 최종 DB를 게시하지 않는다. 파싱 실패 원본과 실패 manifest는 보존한다. 파일 단계 v4는 새 경로에서 생성하며 동일 정상 원본/계약은 재사용한다. 파일 전체/섹션 기대 수를 검증하지만 제공기관별 지역·월 총수가 없다면 coverage.expected_rows는 NULL로 표시한다.

정상 JSON 결과는 exit 0, 입력 계약 오류는 2, 처리 오류는 1이다. stage-file의 미완료/거부 행과 fetch의 미완료 범위는 결과를 남기고 exit 3이다. 같은 배치 재실행은 기존 관측·후보를 유지한다. synthetic과 source_unverified DB는 합치지 않는다. 키·원본·DB·ZIP은 Git에 넣지 않는다.

루트의 verify_environment.py와 check_sdd.py --base origin/main, [Task](tasks/canonical-integration.md)의 AC별 실제·합성 증거를 함께 확인한다. 수집/ZIP 공유는 COLLECT-001을 따르며 Drive 업로드는 이번 범위에 없다.
