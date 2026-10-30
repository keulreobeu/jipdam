# TASK-KAN9-SOURCE-001 — 공원·교통·생활 기존 범위 확인

```toml
kind = "task"
id = "TASK-KAN9-SOURCE-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/16_team_collection_schema_spec.md"]
scope = ["outputs/budongi_mvp_temp/docs/tasks/kan9-source-review-20261028.md", "outputs/budongi_mvp_temp/scripts/build_seoul_parks_snapshot.py", "outputs/budongi_mvp_temp/scripts/build_seoul_metro_snapshot.py"]
acs = ["TEAM-DATA-001-AC-05"]
```

[KAN-9](https://kwulreobeu.atlassian.net/browse/KAN-9)의 기존 자료·중복 범위부터 확인한다. 새 외부 자료 수집, 좌표 검수, 단지 매칭, 추천 연결 및 업로드는 별도 승인 경계를 유지한다.

2026-10-28 GitHub `keulreobeu/jipdam`의 이슈에서 공원·운동시설·지하철·버스·TAGO·상가·소상공인·침수를 각각 검색했을 때 결과가 없었다. 이는 사용한 검색어·접근 가능한 이슈의 결과이며 자료 부재나 동시 예약 부재의 증명은 아니다. 공유 Drive `jipdam_db`의 반환된 직접 파일 목록에서 관련 이름의 공원·교통·침수 패키지는 확인되지 않았다. 이름 검색은 누락될 수 있다.

공원 후보: [서울시 주요 공원현황 OA-394](https://data.seoul.go.kr/dataList/OA-394/S/1/datasetView.do)의 2026년 하반기 XLSX는 2026-09-23 갱신·0.15MB로 표시되고, 출처표시 공공누리 제1유형이 표시된다. 주요 공원 대상이므로 서울 전체 공원·출입구·경계·운동시설 완전 자료로 간주하지 않는다. 파일은 다운로드하거나 내용을 확인하지 않았고, 수집 예약도 아직 하지 않았다.

별도 승인이 있으면 기존 [수집] Issue 전체 상태와 범위 및 동시 예약을 재확인한 후, 해당 파일 하나만 예약해 원본·해시·범위·스키마·정규화·검증을 기록한다. 실제 행 수·필드·현행성·좌표계는 원본을 검사하기 전 미확인이다. 원본 변경·좌표 승격·단지 연결·Drive 업로드는 이 후보에 포함하지 않는다. 나머지 교통·상권·침수 자료는 출처와 범위를 확정하지 않았다.

2026-10-28 사용자는 하반기 XLSX 한 건의 신규 수집을 승인했다. [GitHub #40](https://github.com/keulreobeu/jipdam/issues/40)에 예약하고 동시 예약을 재확인한 뒤 공식 파일을 수집했다. 원본 153,429바이트, SHA-256 `9a64b315997327f4d2d60519daeb5b0df044c781f9dc4d6d45626f94f8ecad28`, 수집시각 `2026-10-28T00:56:26.793482Z`. 시트 `공원현황`의 헤더 20개와 행 155개를 확인했다. 원천 수치·좌표는 미검수로 남긴다.

후속: [변환 스크립트](../../scripts/build_seoul_parks_snapshot.py)는 155행의 원본 20개 값을 시트 행 번호·원본 해시와 함께 보존하고 표준 좌표와 내부 ID를 NULL/pending으로 둔다. 원본 셀 대사 155×20 차이 0, 별도 재실행 전 행 비교(`staged_at_utc` 제외) 차이 0, 기존 출력 거부 및 source_unverified 상태를 확인했다. Python 3.12.14/openpyxl 3.1.5. 로컬 ZIP 266,316바이트, SHA-256 `f7e3855fb5091b6f707e31ecb490b852646bbaa50676122a994811ba54c7ca7b`; manifest payload 8개 크기·해시 및 ZIP CRC 통과. 페이지는 공공누리 1유형 표시이나 이 배치의 독립 사용권 검수는 pending이다. 원본은 `.local_runtime/kan9-park-20261028/`에 보존하고 결과·ZIP 해시를 #40에 기록했다. Drive 업로드·좌표 검수·단지/추천 연결은 미실행이다. 이 한 파일 완료는 KAN-9 전체 공원·교통·생활 범위의 완료가 아니다.

위키 판단: maintenance/catalog/search 후 `KAN9-PARK-SNAPSHOT-20261028` maintenance event는 SKIP/execution_log/DONE/nonblocking이다. 이 판단은 검증한 한 파일의 실행 기록을 #40과 Task에 남긴다는 뜻이며 전체 Task 완료로 처리하지 않는다. 새 위키 문서나 원격 문서 수정은 없다.


## 지하철 역사 좌표 후보 — 2026-10-28

[서울교통공사 1~8호선 역사 좌표 파일](https://www.data.go.kr/data/15099316/fileData.do)의 공개 메타데이터는 CSV, 276행, 파일 기준일 표기 2025-08-14, 페이지 수정 2026-09-17, 이용허락범위 제한 없음을 표시한다. 페이지는 좌표가 다른 기관 자료와 미세하게 다를 수 있으며 신설·이전·폐쇄 등 변경 시 갱신한다고 안내한다. 메타데이터만 확인했으므로 실제 파일 행·좌표계·최신성은 검증하지 않았고, 1~8호선 운영 역사 외 모든 철도나 출입구를 포괄한다고 보지 않는다.

GitHub에서 `15099316`, 지하철, 역사 좌표, 서울교통공사 검색 시 해당 파일의 명시적 수집 기록은 확인되지 않았다. 검색 결과만으로 모든 중복 또는 동시 예약이 없다고 단정하지 않는다. 단일 파일 수집 범위에 대한 사용자 답변을 기다리며 원본은 아직 받지 않았다. 승인 시 전체 수집 이슈 및 동시 예약을 다시 확인하고 예약 후에만 수집한다. 좌표 검수·단지 연결·Drive 업로드는 포함하지 않는다.


## 서울교통공사 역사 좌표 CSV — 2026-10-28

사용자가 공공데이터포털 15099316의 CSV 한 파일 신규 수집을 승인했다. 열림·닫힘 수집 이슈를 확인하고 [#41](https://github.com/keulreobeu/jipdam/issues/41)에 범위를 예약한 뒤 재검색 및 공식 파일 수집을 수행했다. 2026-10-28T06:36:56.300530Z HTTP 200, 원본 16,838바이트, SHA-256 `30e2eb633ac78904029b69fb0b9c48d3aee74b1493e93469af42837697421d08`. CP949 8열·276행, 작성기준일은 모두 2025-08-14다.

[재현 코드](../../scripts/build_seoul_metro_snapshot.py)는 원본 셀 문자열·행 번호와 해시를 보존한다. 원본 276×8셀 전수 대조 및 독립 재실행 결과 차이 0, 기존 출력 덮어쓰기 거부, ZIP CRC와 manifest 5개 파일의 크기·해시를 확인했다. 로컬 ZIP 18,385바이트, SHA-256 `b3d4124566626acb870fdda73942dc4ca7c294646c8b5e161fc859d329648dc5`; 원본·ZIP은 `.local_runtime/kan9-subway-20261028/`에 보관한다. `check_sdd.py --base origin/main` 통과.

원천 좌표는 문자열로만 보존하며 표준 좌표 NULL/pending, 원천 좌표계 unknown, quality `source_unverified`, 연결·coverage 미확정이다. 포털의 이용허락범위 제한 없음 표시를 확인했으나 배치별 사용권 검수는 pending이다. 이 파일은 서울교통공사 1~8호선 역사만 포함하므로 전체 노선·출입구·좌표 정확성 또는 운영 현황 검증을 뜻하지 않는다. Drive 업로드·단지 매칭·추천 연결은 하지 않았다. 상세와 최종 해시는 #41에 기록했다.

위키 `KAN9-SUBWAY-SNAPSHOT-20261028` 이벤트는 SKIP/execution_log/DONE/nonblocking이고 [Jira 기록](https://kwulreobeu.atlassian.net/browse/KAN-9?focusedCommentId=10123)의 receipt는 DONE이다. 이는 CSV 한 파일의 검증 범위이며 전체 KAN-9 완료가 아니다.

## 서울시 버스정류소 위치 파일 후보 — 2026-10-28

[서울시 버스정류소 위치정보 OA-15067](https://data.seoul.go.kr/dataList/OA-15067/S/1/datasetView.do)의 파일 목록에 `서울시버스정류소위치정보(20260902).xlsx`(0.72 MB, 2026-09-02 수정)가 있다. 제공 페이지는 공공누리 1유형을 표시한다. 페이지 설명의 `WGS84 (EPSG-5179)` 표기는 좌표계 판단에 모호함이 있어 출처 설명 그대로만 기록하고, 실제 파일의 좌표값이나 좌표계를 검증했다고 주장하지 않는다. 파일명 날짜와 게시 수정일만 확인했으며 실제 데이터 기준일·행 수·현행성은 미확인이다.

GitHub의 접근 가능한 이슈에서 `OA-15067`, `버스정류소`, `버스정류장`을 각각 검색한 결과는 없었다. 검색만으로 모든 과거 자료나 동시 예약이 없다고 판단하지 않는다. 이 파일은 사용자 별도 수집 승인 이전의 후보이며 아직 예약·다운로드하지 않았다. 승인 시 전체 수집 이슈 및 동시 예약을 다시 확인하고 단일 XLSX 범위를 예약한 뒤 원본·해시·행 대사·재현 결과를 로컬에 보관한다. 실시간 도착·노선 관계, 좌표 확정, 단지 연결 및 Drive 업로드는 이 후보 범위에 포함하지 않는다.
