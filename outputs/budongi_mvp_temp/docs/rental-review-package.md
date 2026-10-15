# 전월세 MVP 실행과 검수 패키지

관련 계약: [RENT-001](specs/10_rental_recommendation_spec.md), [ADR-009](adr/ADR-009-reviewed-rental-serving.md), [Task](tasks/rental-mvp.md).

## 로컬 실행

루트 README의 환경 설치 후 프로젝트 폴더에서 실행한다.

```powershell
Set-Location outputs/budongi_mvp_temp
$env:PYTHONPATH='src'
python -m budongi.cli prepare-rentals
python -m budongi.cli rental-readiness
python -m budongi.cli rental-mvp --no-browser
```

브라우저에서 `http://127.0.0.1:8766/`을 연다. 모델이 없어도 조건을 직접 확인·검색할 수 있다. 현재 실제 관측은 238,620건, 확정 연결은 0건이다. `data_not_ready`는 정상이며 미확정 후보를 보여주지 않는다. 원본 canonical은 수정하지 않고 serving v2를 재생성한다. 실행 중인 상세 조회가 Windows 파일 교체를 막으면 조회가 끝난 뒤 prepare를 다시 실행한다. 기존 serving은 실패 시 유지된다.

로컬 4B 모델을 별도로 실행한 경우 실제 설치된 모델명·주소를 지정한다. 예시 이름은 설치 여부를 의미하지 않는다.

```powershell
python -m budongi.cli rental-mvp --model qwen3.5:4b-q4_K_M --endpoint http://127.0.0.1:11434/v1/chat/completions
```

모델이 없거나 응답이 잘못되면 대화와 입력을 유지하고 직접 입력으로 이어간다. 초안은 검색을 실행하지 않는다. 검색 버튼이 사용자 확인이다. 직장 위치는 사용자 확인 좌표를 폼에 넣으며 모델이 회사명을 좌표로 바꾸지 않는다. 새 대화는 서버 메모리 세션을 지운다. 대화는 30분 만료·최대 20메시지다.

## 승인된 오프라인 검수 패키지

`rental-readiness`는 canonical/serving의 원본 해시 일치, 검수 패키지 입력, 실제 확정 관계/좌표/시설/커버리지, 지정 모델·loopback 주소를 읽기 전용으로 확인한다. 파일 생성·수집·모델 호출은 없다. 미준비/오류이면 종료 코드 2, 설정 확인이면 0이며 실제 검증 완료를 의미하지 않는다. 현재 기본 canonical은 보존된 `canonical-v3-20261013/canonical.sqlite3`다.

자료가 준비되면 아래 순서로 실행한다. `APPROVED_PACKAGE`, `LOCAL_MODEL`, `ACTUAL_CANDIDATE_ID`는 실제 승인/설치/추천 결과 값으로 바꾼다.

```powershell
python -m budongi.cli prepare-rentals --review-package APPROVED_PACKAGE
python -m budongi.cli rental-readiness --review-package APPROVED_PACKAGE --model LOCAL_MODEL
python -m budongi.cli rental-mvp --model LOCAL_MODEL --no-browser
python -m budongi.cli recommend-canonical --request REQUEST_UTF8_JSON
python scripts/benchmark_rentals.py --database data/rental/serving/canonical.sqlite3 --candidate ACTUAL_CANDIDATE_ID --output ../../.local_runtime/real-ready-benchmark.json
```

실모델은 누락 조건 질문·단위·수정/제거·사용자 확인 전 추천 0회·응답 오류 시 입력 보존을 검증한다. 실제 추천/상세는 반환 후보의 계보·조건·검수 좌표/시설 내용을 확인하고 각각 p95≤500ms를 검사한다. `data_not_ready`/`not_found` 계측으로 이 성공 조건을 완료 처리하지 않는다.

importer는 승인된 자료를 읽으며 검수나 승인을 만들어 주지 않는다. `approval_ref`는 운영자가 확인한 승인 기록이며 전자서명이 아니다. 신규 수집·단지 매칭 확정·좌표 검수는 기존 승인 절차를 먼저 따른다. 팀 제출 `team_collection_v1`을 자동 확정 패키지로 승격하지 않는다.

```powershell
python -m budongi.cli prepare-rentals --canonical-db PATH_TO_CANONICAL --output-db PATH_TO_SERVING --review-package PATH_TO_APPROVED_PACKAGE
```

패키지 디렉터리에 `manifest.json`, 정규화 `records.json`, 검수 근거 파일을 둔다. 모든 파일 경로는 패키지 내부 상대 경로다. 파일마다 최대 50MiB이며 manifest에 SHA-256을 기록한다. 원본 DB의 전체 SHA-256을 `source_db_sha256`으로 대사한다. 누락·충돌·좌표 오류·해시 불일치는 출력 교체 전에 거부한다.

| manifest 필드 | 계약 |
|---|---|
| `schema_version` | `rental_review_v1` |
| `source_db_sha256` | 입력 canonical 파일 SHA-256 |
| `quality_status` | `reviewed_real` 또는 `synthetic_only` |
| `approval_ref`, `approved_by`, `approved_at_utc` | 이미 승인된 기록·담당·timezone 포함 시각 |
| `records_file` | 정규화 레코드 JSON 상대 경로 |
| `snapshot_date` (선택) | 추가 검수 자료를 함께 비교할 통합 기준일. 원본 배치일 이후이며 승인일(서울 날짜)을 넘지 않음. 생략 시 원본 배치일 |
| `files` | `{path, sha256}` 목록. 레코드 파일과 모든 근거 파일 포함 |

`records.json`의 지원 목록은 `relations`, `coordinates`, `facilities`, `coverage`다. 각 행은 다음 공통 계보를 가진다.

```json
{
  "review_status": "confirmed",
  "evidence": "검수 근거를 식별하는 기록",
  "reviewed_by": "검수자",
  "reviewed_at_utc": "2026-10-12T00:00:00Z",
  "source_id": "등록 출처",
  "source_date": "2026-10-12",
  "source_file_ref": "evidence.json",
  "source_content_sha256": "실제 근거 파일의 SHA-256",
  "source_row_number": 1
}
```

위는 형식 설명이며 승인된 실데이터가 아니다. `pending`/`rejected`도 명시할 수 있으나 추천에 사용하지 않는다.

| 목록 | 추가 필드·제약 |
|---|---|
| relations | `observation_id`, `complex_id`, `source_status`(`valid`/`cancelled`/`correction_pending`). 관측·단지의 canonical 존재와 지역 일치 확인, 관측당 확정 관계 1개 |
| coordinates | `complex_id`, `latitude`, `longitude`, `crs=EPSG:4326`, `method`. 추천 자격 단지마다 검수 좌표 1개, WGS84 범위·출처·변환 방법·근거 필수 |
| facilities | `facility_id`, `category`(station/supermarket/park/hospital), `name`, 위경도·crs·method. 검수된 행만 적재 |
| coverage | category, `sgg_cd`, `coverage_status`(complete/partial/unknown), `checked_at_utc`, `coverage_area={latitude,longitude,radius_m}`. 원과 기준일을 보존 |

필수 시설 판정은 완전한 검수 원이 요청 반경 전체를 포함하고 출처·검수 기준일이 스냅샷의 12개월 이내일 때만 가능하다. 범위 내 오래된 시설도 `unknown`을 유발한다. 선호 미확인은 점수에 넣지 않는다. RTree 경계는 탐색용이며 최종 거리는 실제 좌표로 계산한다.

새 시설·커버리지의 기준일이 기존 거래 배치보다 늦으면 승인된 패키지의 `snapshot_date`를 명시한다. 거래 원본 `snapshot_date`와 상태의 `source_snapshot_date`는 그대로 보존하며 통합 기준일과 구분한다. 승인일을 넘는 미래 기준일은 거부한다.

## 필드 확장과 API

serving `schema_version=2`, `catalog_version=2`. `field_catalog()`에서 지원 필드의 key/label/type/unit/section/source/validity를 등록한다. 추가 정규화 필드의 투영·타입 검사와 카탈로그/스키마 버전을 함께 바꾸고 serving을 재생성한다. 미등록 원본 필드는 상세 `unsupported_fields`로 보고한다. 런타임에서 SQL 열 이름을 사용자 입력으로 만들지 않는다.

| API | 동작 |
|---|---|
| GET /api/status | 배치·카탈로그·serving 버전, 관측/확정 연결·좌표/시설/커버리지 준비 상태 |
| POST /api/chat | `{message,session_id?,draft?}` → 질문·초안·draft_patch·missing_fields·mode. `{reset:true,session_id}`는 삭제 |
| POST /api/recommendations | `{request}` → 상태·후보·니즈/순위·좌표 검수·원본 계보 |
| GET /api/candidates/{id}/{offset} | offset 0/100/200…, 등록 항목·100행 거래·시설/커버리지·검수 근거 |

입력 오류 400, DB 이용 불가 503, 준비된 DB의 자료 부족 200 `data_not_ready`, 존재하지 않는 후보 404. 존재하는 후보의 끝 이후 페이지는 200과 빈 거래 목록이다. 상세와 추천의 `serving_version`이 달라지면 다시 검색한다. Host/Origin/CSRF는 loopback 화면으로 제한한다. 모델은 로컬 HTTP만 허용하고 proxy·redirect를 사용하지 않는다.

지도는 Leaflet 1.9.4 자산·라이선스가 패키지에 포함되어 있으며 버튼을 눌러야 배경을 불러온다. [OSM 정책](https://operations.osmfoundation.org/policies/tiles/)에 따라 출처·Referer·브라우저 HTTP 캐시를 유지하며 화면 밖 사전 수집·오프라인 타일 다운로드를 제공하지 않는다. 허용 타일 도메인은 `tile.openstreetmap.org` 하나다. 직장 좌표는 타일 요청에 넣지 않는다. Leaflet 위치 배치에 필요한 인라인 style은 CSP에 허용하고 스크립트는 로컬만 허용한다.

## 재현 가능한 합성 성능 검증

루트에서 다음을 실행한다. 실제 추천 데이터와 분리하며 fixture 디렉터리는 새 경로 또는 빈 폴더여야 한다.

```powershell
python outputs/budongi_mvp_temp/scripts/benchmark_rentals.py --create-synthetic outputs/budongi_mvp_temp/data/rental/NEW_SYNTHETIC_DIRECTORY --allow-synthetic --candidate load-0000 --compare-indexes --output .local_runtime/rental-benchmark.json
```

20,102개 합성 관측·1,001개 검수 관계 단지·2,000개 시설로 5회 워밍업/100회 추천·상세를 측정한다. 연결·DB 조회와 판정·응답 JSON 시간을 분리한다. 인덱스 비교는 같은 파일의 사본에서만 인덱스를 제거하며 원본은 보존한다. 결과·순위·계보의 SHA-256이 같아야 한다. 공간 근거 캐시는 2,048개로 제한하고 serving 해시/카탈로그/기준일/좌표/반경별로 격리한다. 후보와 필수 판정은 매 요청 실행한다. 실모델·지도 로딩은 DB 계측에서 제외한다.

현재 실제 추천 성공/상세 성공과 실모델 검증은 사용자 답변대로 자료 준비 후 수행한다. [최신 검증 기록](rental-mvp-validation-20261013.md#2026-10-14-구현-검증)을 따른다.
