# RENT-001 MVP 검증 기록 — 2026-10-13

2026-10-13 기록은 당시 구현의 이력이다. 현재 완료 증거와 남은 게이트는 아래 최종 재검증을 따른다.

## 실제 DB 준비 상태

기준 DB는 기존 canonical v2-growing 사본을 `mode=ro`로 열어 읽었다. serving projection은 새 출력 파일로 재생성했으며 canonical 입력은 수정하지 않았다.

| 항목 | 관측 |
| --- | --- |
| source batch / 기준일 | `7c74ac5fb53ce8fc28f86dc10c1687d52886d32151e7522df14f46117363bfc0` / 2026-10-12 |
| 전월세 관측 | 238,620 (전세 119,631, 월세 118,989) |
| 확정 단지 연결 전월세 관측 | 0 |
| 미확정 전월세 match candidates | 271,299, 전부 pending/unverified |
| 검수 좌표 / 검수 시설 | 없음 / 없음 |
| canonical 파일 크기 | 1,760,129,024 bytes |
| 새 serving projection 크기 | 135,847,936 bytes (canonical 대비 7.72%) |
| 결과 | `data_not_ready`; 미확정 후보를 추천하지 않음 |

실제 출처·적재 감사는 [CANONICAL 실제 검증](canonical-validation-20261013.md)과 [MOLIT 수집 검증](molit-validation-20261012.md)을 참고한다. serving DB는 ignored 재생성 산출물이며 Git에 넣지 않는다.

## 동작 검증

프로젝트 루트에서 실행:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -p 'test_canonical_rental.py' -v
node --check src/budongi/static/rental.js
python -m py_compile src/budongi/canonical_rental.py src/budongi/rental_server.py src/budongi/cli.py
```

결과: 전용 unittest 6개 통과. 확인 범위는 미연결 관측 배제와 read-only 연결, 확인 단지 최신 거래/예산 순서 및 계보, 명시적인 `coordinates_verified=1`의 WGS84 좌표만 지도 응답에 허용, 모델 draft allowlist·모킹된 구조화 응답, loopback 상태·대화 fallback·CSRF 차단이다. Node 문법 검사와 Python compile도 통과했다. 첫 sandbox 실행은 Windows loopback socket 권한으로 실패했고, 승인된 로컬 통합 테스트 재실행에서는 통과했다.

번들 Python 3.12 환경으로 애플리케이션 전체 테스트도 실행했다: `python -m unittest discover -s tests -v` 결과 **143개 통과**. `python -X utf8 -m budongi.cli rental-mvp --help` parser smoke도 통과했다. 시스템 Python에는 프로젝트 의존성 `openpyxl`이 없으므로 앱 실행 명령은 `pip install -e .` 또는 프로젝트 의존성을 포함한 Python 환경에서 실행해야 한다.

실제 serving DB를 대상으로 loopback 서버의 `/`·`/api/status`·POST `/api/recommendations` smoke를 실행했다. 화면 HTTP 200, 실제 관측 238,620건, API 결과 `data_not_ready`, 추천 0곳을 확인했다. 브라우저에서도 서울 자치구 기본값 누락으로 첫 제출이 입력 오류가 나는 것을 발견해 종로구 초기값을 지정했고, 재검증에서 니즈/전체 정보 탭 전환 및 실제 DB의 `data_not_ready` 안내를 확인했다. 이 브라우저 흐름은 실제 매칭 단지가 없는 상태에서 수행했다.

실제 로컬 LLM 모델은 현재 실행 중이지 않아 모델 질문 품질/실호출은 검증하지 않았다. LLM이 반환한 구조화 초안은 지원 키·타입·자치구·조건만 허용하고 좌표/SQL/추천 데이터는 폐기한다. 입력 초안은 검색 폼에 적용되지만 추천은 사용자가 조건을 확인해 제출하기 전 실행되지 않는다.

## 실제 DB 읽기 지연 및 쿼리 계획

측정은 Python 3.12, Windows local workspace, 동일한 persistent read-only SQLite connection, JSON 조건(월세, 종로구, 보증금 상한 5억, 월세 상한 100만원, 시설 조건 없음)을 사용했다. 처음 5회를 워밍업하고 같은 추천 API 함수 100회를 측정했다. 각 요청은 실제 DB의 준비 상태와 적격성 검사를 수행했다.

| 지표 | 값 |
| --- | ---: |
| 요청 수 / warm-up | 100 / 5 |
| p50 | 21.208 ms |
| p95 | 29.352 ms |
| max | 35.407 ms |
| 모든 응답 | `data_not_ready`, 0곳 |
| 준비된 12개월 후보 조회 CTE 단독 p50 / p95 / max | 0.289 / 0.357 / 0.453 ms |
| 후보 CTE 행 수 | 매회 0, confirmed 링크가 없어 실제 순위 집합 없음 |
| candidate SELECT 계획 | `rental_complex_latest` partial index 검색, `ROW_NUMBER()` 창으로 단지별 최신 거래 선택, 결과 정렬은 temp B-tree |

p95는 현재 실제 데이터 상태 응답 목표(500 ms)보다 낮다. 후보 선별은 단지별 과거 행을 Python에 전부 가져오는 대신 serving DB의 `ROW_NUMBER()` 창으로 최신 행을 구하고 예산을 적용하며, partial index는 단지 연결된 관측만 대상으로 한다. compact projection은 1.76 GB 원본보다 약 13배 작다. 현재 실제 확정 연결이 0건이라 후보가 있을 때의 실제 순위화와 실제 상세 거래 목록 지연은 측정할 수 없었다. 따라서 이 기록은 readiness 응답과 빈 적격 쿼리의 성능 근거이며 실제 추천 성공 경로 전체의 성능 완료로 확대 해석하지 않는다.

## 남은 검증 게이트

- 로컬 모델을 설정해 질문 → 조건 초안 → 사용자의 수정/확정 → 검색까지 브라우저에서 확인한다.
- 브라우저 UI에서 다중 자치구·필수/선호 거리·결과 탭을 확인한다.
- 승인된 공식 단지 연결이 들어온 뒤 실제 추천 비어 있지 않은 경로, 최신 계약/가격 필터/출처 표기·상세 지연을 같은 절차로 계측한다.
- 검수 좌표/시설 자료가 현재 없으므로 실제 위치 마커와 생활 시설 비교 품질은 미검증 상태다. 좌표가 허용될 때의 현재 UI는 사용자가 선택하면 OpenStreetMap을 새 탭으로 여는 click-through이며, 좌표 외부 전달 사실을 링크 근처에 알린다. 지도 타일/외부 지도 embedding 자동 요청은 포함하지 않았다. 자동 매칭·외부 데이터 수집·좌표 추정은 수행하지 않았다.
- `python -X utf8 scripts/verify_environment.py`는 실행했지만, MVP와 무관한 `outputs/budongi_mvp_temp/docs/team-collection-chat-summary.md` 변경이 업데이트된 `ready/in_progress/verified` Task에 포함되지 않았다는 SDD 검사에서 중단됐다. 전체 SDD/environment gate는 해당 문서 Task 연결 후 재실행해야 한다.

## 2026-10-14 구현 검증

승인된 T1~T6를 순차 구현했다. gstack helper는 Git for Windows MSYS NtCreateDirectoryObject 0xC0000022로 실행되지 않았다. Codex 내장 브라우저는 kernel assets 경로 오류로 초기화되지 않아 기존 gstack browse.exe/Chromium을 격리 state 파일로 사용했다. 외부 CLI 리뷰·자동 리뷰 로그 저장은 실행하지 않았다. 이 기록은 실제 실행한 unittest/브라우저/SQLite 계측의 증거다.

### 계약 및 회귀

- 전용 unittest 20개 통과: raw complex_id/verified bool 배제, pending/rejected 배제, 원본 불변/입출력 동일 파일/봉인·파일 해시, 검수·계보·좌표 오류, 버전, 최신 계약/동률/취소·정정, 필수/선호/커버리지/거리 경계, 최종 조건 이전 LIMIT 금지, 캐시 버전 격리, 상세/카탈로그, 대화 확인·수정·제거·모델 오류·만료·reset, Host/Origin/CSRF/로컬 모델 redirect 차단.
- 기존 합성 추천 15개 통과. 공통 distance/conditions/ranking 함수로 전환한 뒤 기존 CLI 출력과 승인된 동작을 유지했다.
- 전체 앱 회귀는 중간 변경에서 166개 통과했다. 최종 추가 변경 이후 전체 환경 검사는 아래 최종 결과로 대체하며 이 중간 통과를 최신 전체 증거로 사용하지 않는다.
- 실제 source 기본값은 canonical-v2-growing이며 PRAGMA user_version=2와 봉인 보고서/파일 해시가 일치한다. v3도 호환 투영으로 지원한다. 원본 해시는 prepare 시작/끝에 같아야 교체하며 이번 실제 생성에서 통과했다. serving은 schema2/catalog2, 확정 연결 0건/좌표·시설·커버리지 미제공을 유지했다.

### 브라우저 흐름

실제 DB `http://127.0.0.1:8766/`: 전세 선택 시 월세 0/disabled, 지도 보기 전 타일 0건. 검색 후 원본 238,620건·확정 0건과 data_not_ready를 표시하고 후보와 상세를 만들지 않았다.

명시적 합성 `http://127.0.0.1:8767/`: 합성 배지, 후보 5개, 기본 니즈 20행/공원 선호 추가 후 25행, 첫 단지 120건 상세의 100행→20행 및 되돌아가기 버튼. 검수 좌표·근거·시설·커버리지·출처가 표시됐다. 지도 보기 전 타일 0건, 이후 마커 5개·OSM attribution·strict-origin-when-cross-origin. 실제 OSM 타일 12개가 naturalWidth256/complete로 로드됐다. 오류 주입 전 console errors 없음. 로컬 404 타일 오류를 주입한 뒤 실패 안내·마커5/거래20행 유지. 스크린샷: `.local_runtime/rental-browser-20261014/map.png` (합성 위치; 실제 추천 품질 증거 아님).

### 성능

같은 요청 5회 워밍업 후 100회, 연결+조회/판정+JSON 구성. LLM/지도 제외. 최초 부하 1회는 추천 약6380ms였으며 프로파일에서 반복 JSON/거리/날짜 처리가 병목이었다. 같은 serving·기준일·좌표·반경의 공간 근거만 캐시하고, 최신 계약은 좁은 ID window로 선별한 뒤 원본 행을 조인했다. 검색 covering index와 단지별 상세 index를 적용했다. 결과 자체를 캐시하거나 최종 필수 판정 전에 LIMIT하지 않는다. 첫 공간 스캔은 warm 경로보다 느릴 수 있다.

최종 수치와 쿼리 계획은 아래 자동 요약을 따른다. 인덱스 비교는 같은 파일의 사본에서만 제거한 대조군이며 인메모리 대조 수치는 최종 비교에 쓰지 않았다. 반복 결과·순위·계보 SHA가 같아야 한다. 실제 추천 성공/상세 성공은 확정 연결 0건 때문에 미실행이며 미준비/없는 후보 경로를 성공 경로로 표시하지 않는다.

### 데이터 준비 조건

사용자 답변: **아직 승인된 검수 패키지와 로컬 4B 모델이 없음 · 준비 조건으로 기록**. 새 원격 수집·자동 매칭·실제 좌표/시설 확정·배포를 수행하지 않았다. 실제 비어 있지 않은 추천·상세 p95≤500ms, 실모델 질문 시나리오는 자료 제공 후 재검증한다. Task와 전체 Goal의 해당 게이트는 미완료다.

### SDD 연결

기존 팀 요약·상세 문서가 해당 팀 Task scope에 없던 연결을 보완했다. 두 문서의 내용은 보존했으며 새 수집·제품 요구 승인으로 해석하지 않는다. 최종 전체 환경/SDD 검사는 아래 결과를 따른다.


## 2026-10-14 최종 재검증

### GMS 코드 작업

사용자의 재개 지시에 따라 저장된 선택 키·활성 정책을 사용하는 `gms-work --execute`로 `rental_review.py` 코드만 제공해 `tests/test_rental_review.py` 초안을 생성했다. 로컬에서 코드와 범위를 검토한 뒤 반영했다. Seoul 승인 날짜 경계, 시간대 없는 승인 거부, 잘못된/비정규 날짜 거부, 선택적 기준일, 합성 명시 승인 5개 테스트가 통과했다. DB·실거래·키·로그는 모델에 제공하지 않았다.

현재 runner의 승인된 모델/요율 계약은 `gpt-6.1-sol` 고정이므로 이 모델을 사용했다. 사용자가 허용한 LUNA는 이번에 호출하지 않았다. 난이도별 선택은 GMS 지원 모델과 요금 확인 및 모델별 사전 카운트·비용 예약 계약이 필요하다. 현재 앱의 추천용 로컬 LLM 경계와 별개의 개발 초안 경로다.

실행 2026-10-14 14:20 KST: 입력 1,690/출력 1,009토큰, 최대 예약 253.8크레딧, 조회 비용 20 + 생성 전후 계정 차이 135 = 원장 155크레딧. 누적 원장 310/500크레딧, 누적 모델 토큰 3,741/10,000, 보류 0. 확인된 실잔액 29,690크레딧이며 최소 보존 5,000을 유지했다. 계정 차이는 공급자의 개별 청구서로 해석하지 않는다. ignored 실행 결과 `.local_runtime/rental-gms-result-20261014.json`.

### 최종 성능

| 데이터·경로 | p50 (ms) | p95 (ms) | 결과 |
| --- | ---: | ---: | --- |
| 실제 관측 238,620건·추천 | 0.829 | 1.068 | data_not_ready·확정 연결 0 |
| 실제 DB·미존재 상세 ID | 1.102 | 1.253 | not_found·성공 상세가 아님 |
| 합성 1,001단지/20,102관측/2,000시설·추천 | 127.872 | 152.667 | ok |
| 합성·상세 100행 | 70.244 | 78.706 | ok |
| 합성 인덱스 제거 사본·추천 | 118.145 | 142.777 | 동일 결과·순위·계보 |
| 합성 인덱스 제거 사본·상세 | 86.144 | 99.950 | 동일 결과·순위·계보 |

각 경로 같은 요청 5회 워밍업/100회. DB 연결·판정·JSON 구성 합계이며 LLM/외부 지도는 제외한다. 성공 합성 추천에서 인덱스가 지연을 개선했다는 증거는 없다. 상세는 개선됐고, 추천 최적화는 좁은 최신 ID 선별과 공간 근거 캐시로 목표를 충족했다. 단일 반복 비교의 변동을 일반적인 속도 보장으로 해석하지 않는다. 실제 비어 있지 않은 두 경로는 미측정이다.

최신 계약 쿼리 계획: `rental_search` covering index(kind/sgg_cd/contract_date) → window 정렬 temp B-tree → 관측 ID/검수 관계/단지 ID index 조인. 시설은 RTree 가상 index `2:B0D1B2D3` → 시설 PK, 최종 거리는 원 좌표로 다시 계산한다. 인덱스 제거는 파일 사본에만 적용했고 응답 SHA가 일치했다.

재현 명령은 제품 폴더에서 `PYTHONPATH=src`와 번들 Python으로 실행한다:

```powershell
python -X utf8 scripts/benchmark_rentals.py --database data/rental/serving/canonical.sqlite3 --output ../../.local_runtime/rental-real-benchmark-final-20261014.json
python -X utf8 scripts/benchmark_rentals.py --database data/rental/synthetic-serving-final-20261014/serving.sqlite3 --allow-synthetic --candidate load-0000 --compare-indexes --output ../../.local_runtime/rental-synthetic-benchmark-20261014-v2.json
```

### 최신 UI와 환경

최신 실제 서버 8786 브라우저: 초기 채팅 draft는 빈 객체, 수동 보증금 변경 후 draft는 그 필드만 전달했다. 확인 전 추천 요청 0회, 확인 버튼 이후 전세 월세 0/disabled와 실제 238,620/확정 0 안내를 확인했다. 지도 타일 요청 0, 콘솔 오류 0. 캡처 `.local_runtime/rental-browser-final-result.json`. 합성 지도·거래 페이지·타일 실패 검증은 위 브라우저 흐름 기록을 따른다.

전체 환경 검증은 최신 코드/추적 원장으로 재실행했다. 시스템 Python의 sandbox 임시 폴더 오류는 제품 실패로 처리하지 않고 의존성이 포함된 번들 Python/허용된 로컬 실행에서 재검증했다. 아래 실행 결과가 최종 기준이다.

결과: **앱 199개 + 팀 22개 모두 통과**, SDD 12개 기능/71개 AC/28개 Task/64개 변경 경로 통과, 모델 없는 합성 CLI smoke 통과. JS 문법 검사 통과. 전체 실행 로그는 `.local_runtime/rental-environment-final-20261014.log`에 있다. 이전 SDD/동시 GMS 변경 중 실패 기록을 이 최신 검증으로 대체한다.

최신 합성 모바일 회귀: 후보 5곳/니즈 20행, 첫 단지 상세 100행. 표의 최소 콘텐츠 폭이 grid 카드의 자동 최소 폭을 키워 페이지가 668px까지 넘치는 원인을 확인했다. 카드 `min-width:0`, 스크롤 컨테이너 `max-width:100%`로 수정한 뒤 화면/문서 폭 모두 375px, 표는 내부 스크롤 600px로 검증했다. 상세 거래 열에도 최소 폭을 지정해 긴 계보가 한 글자씩 감기지 않게 했다. 콘솔 오류 0. 화면 증거 `.local_runtime/rental-browser-20261014/mobile-detail-final.png` (합성).

기능 구현과 모델 없는 계약/합성 성공 경로 검증은 완료했다. 실제 검수 연결/좌표/시설/커버리지 패키지와 실모델, 실제 비어 있지 않은 두 조회 경로 성능은 여전히 준비 조건이다. Task의 AC-12·AC-15 및 전체 Goal은 완료로 전환하지 않는다.

### 목표 항목별 완료 감사

현재 파일·실행 상태를 다시 확인했다. 준비 상태 함수는 schema2/catalog2, 실제 전월세 238,620/확정 0, 좌표·시설·커버리지 false를 반환했다. 현재 설정으로 생성한 로컬 서버의 모델은 미설정이다. 사용자가 미제공으로 답한 검수 패키지/실모델을 임의로 만들거나 대체하지 않았다.

| 목표 | 현재 증거 | 판정·남은 조건 |
| --- | --- | --- |
| 1 채팅 조건·추가 질문·사용자 확인 | rental_server의 로컬 구조화 응답/초안 검증, chat 테스트와 UI 확인 전 추천 0회 | 기능 검증 완료. 실제 지정 4B 모델로 누락·단위·수정 시나리오 확인 필요 |
| 2 실제 DB 추천 | canonical read-only serving, 확정 검수 관계 적격성·최신 계약·예산·순위 테스트, 현재 상태 조회 | 미준비 반환 검증 완료. 승인된 실제 확정 관계가 있어야 실제 후보/계보 검증 가능 |
| 3 실제 위치 | Leaflet 로컬 자산·검수 좌표 전용 마커·합성 연결/타일 실패 검증 | 실제 검수 좌표 미제공. 실제 단지의 지도 위치 확인 필요 |
| 4 두 화면 | 후보별 니즈·등록 전체 필드·100행 상세·지도·페이지 이동·375px 내부 스크롤 | 기능 검증 완료. 실제 거래/시설/커버리지 내용 확인은 실제 패키지 제공 후 수행 |
| 5 추가 데이터 확장 | schema2/catalog2, 카탈로그 필드/단위/출처/유효기간, 미지원 필드·버전 오류 테스트 | 현재 확장 계약 검증 완료 |
| 6 속도·최적화 | 5warmup/100회 실제 미준비와 합성 성공의 추천·상세 p50/p95, 쿼리 계획·파일 사본 인덱스 대조 | 합성 목표 통과. 실제 비어 있지 않은 두 경로 p95≤500ms 미측정 |
| 7 문서·Task·검증 | RENT-001/Runtime/Plan/Task/원장, 앱199·팀22, 최신 SDD 재검사 | 이전 REQ-06의 HTTP 상태·웹 미구현 설명과 프로젝트/현재 Task의 후속 표시를 현재 계약으로 동기화. 초기 Plan 표는 승인 이력으로 구분 |

문서 동기화 후 `python -X utf8 scripts/check_sdd.py`는 기능12/AC71/Task28/변경64 통과했다. 이 감사에서는 제품 코드·데이터를 변경하지 않았고 실모델/실데이터 미측정을 완료로 바꾸지 않았다. 남은 실행에 필요한 입력은 (1) 이미 승인된 검수 패키지 경로, (2) 사용자가 지정한 로컬 모델명·loopback 엔드포인트다. 제공 후 기존 prepare/API/benchmark 경로로 재검증한다.
