# MOLIT 계획 재검토·후속 검증 — 2026-10-12

Task: [TASK-MOLIT-001](tasks/molit-collection.md). 기존 XML·DB는 보존하고 새 출력으로 검증한다. 원본·실수집 상태·합성 검사·실제 DB 검증을 구분한다.

## 시작 상태

- 수집 Issue #5를 검색해 기존 예약을 확인했다. #3은 합성 배치이며 실제 범위를 차지하지 않는다. 새 예약 Issue는 만들지 않았다.
- 시범 `molit-pilot-20261012`: 전월세 99행, 매매 상세 19행 완료, 매매 일반 인증 실패. 전체 완료 아님.
- `molit-seoul-20261012`: 전월세 25구×13월 242,323행과 매매 상세 시범 19행 보존. 전체 975조합 중 326완료.
- `molit-seoul-20261012-v2`: 두 API 계획, 이번 확인 당시 전월세 242,323행과 매매 상세 4,487행 보존, 전체 650조합 중 376완료. 이번 세 API 계획의 전체 완료 증거가 아님.
- 보관함에서 ID/제공자 메타데이터만 읽었다. 사용자 2026-10-12 응답에 따라 연결 API 제거·별칭 통일·재등록 완료 통보 전 새 호출과 보관함 변경을 보류한다.
- 기존 수집 unittest 9개 통과. 실수집 완료로 승격하지 않는다.

## 후속 실행 결과

세 API 실제 수집·두 관측 DB·staging·오프라인 재생성·ZIP 복원 검증이 완료됐다. 아래 시작 상태·중단/수정 이력은 당시 기록으로 보존한다. 이후 GitHub 결과 게시와 후속 통합은 [최종 통합 검증](canonical-validation-20261013.md)·[통합 Task](tasks/canonical-integration.md)의 최신 판정을 따른다.

### Full Seoul validation

배치 `data/collection/molit-seoul-three-api-20261012`, 기준일2026-10-12, 관측2025-10-12~2026-10-12, 월별 조회202510~202610. 서울25구×13월×세 API **975/975 query 완료**, 실패/미조회0. 매매 일반/상세 각각 성공0건 query가2개이며 전월세는0개다. 원본은 실제 조회 시점 자료이고 동일 과거 상태/정정 완전성을 보증하지 않는다.

성공 페이지1,062개, 보존 시도1,063개(이전 인증 실패1개 포함). 성공 페이지의 조회 UTC는2026-10-12T07:08:50.146065+00:00~2026-10-12T08:13:50.395516+00:00이다. KST16:08:50~17:13:50이며 API 호출 시각과 관측 기간은 다른 값이다.

| 서비스 | 원본 관측 행 | 유효 적재 | 기간 제외 | 거부 |
| --- | --- | --- | --- | --- |
| 전월세 | 242,323 | 238,620 | 3,703 | 0 |
| 매매 일반 | 70,944 | 68,136 | 2,808 | 0 |
| 매매 상세 | 70,944 | 68,136 | 2,808 | 0 |
| 출처별 관측 합계 | 384,211 | 374,892 | 9,319 | 0 |

일반/상세는 독립 원천 관측이며 합계를 **중복 없는 실제 계약 건수**로 해석하지 않는다. 모든 원본 행은 staging에 남고 기간 밖 행의 원본/위치/날짜/제외 사유를 보존한다.

실제 실행: 완료 `collection fetch` 재실행은 자격증명0/네트워크0인 guard에서 `new_queries=0`으로 통과했다. 같은 guard에서 `build_databases`로 `db`와 `db-rebuild`를 새로 만들었다. 두 DB의 모든 관측 열(실제 적재 시각만 제외)의 정렬 행 digest가 같았고 staging.sqlite3는 파일 SHA-256까지 같았다. 첫/두 번째 생성 누적 시간은 각각265.91/506.80초, ZIP/복원 포함 검증은717.06초다. 이는 이 PC의 실행 기록이며 일반적인 성능 보장은 아니다.

SQL 원본 조인 전월세238,620행, 매매136,272행이 전체 적재 수와 일치했다. 세 DB 모두 `integrity_check=ok`, FK 위반0이며 PK/UNIQUE/CHECK 검사를 통과했다. 같은 관측 키·동일 값 여러 행 보존은 계약 테스트와 실제 재생성 정렬 비교로 검증했다.

| 산출물 | SHA-256 |
| --- | --- |
| rental.sqlite3 | `aedd99bf8f4c11eb71ad13615f4be738fe6bbf9f28ef7a03dec81fbaf5c51e53` |
| sales.sqlite3 | `a87f996341be738fc63e228a53d1ef22ea4b4a1866a279b6cfcd89da8e6ef572` |
| staging.sqlite3 | `95a60415c7844f20c2dcacb9532cff2dafe5a1714a3314dc70b13bb6f368f211` |
| 전체 XML/manifest/DB ZIP | `de4df7bf6558f2c78cedfabc2c1160aafd11f4c997b0bdf56166071f36ad4739` |

ZIP은210,802,677바이트(약211MB)다. 별도 `restore-check`에 풀어 모든 원본/파생 파일 해시와 ZIP CRC를 검증하고 복원 아카이브의975 query를 다시 검사했다. 원본·DB·ZIP은 Git 제외를 확인했다. 실제 상세 보고는 배치의 `full-audit-report.json`, 원본·DB 입력/대사는 `db/normalized-manifest.json`, 요청/시각/페이지는 각 query manifest에 있다. Drive 업로드는 하지 않았다.

복원 가능한 입력은 불변 XML/manifest/버전이며 적재 시각/SQLite 물리 배치가 달라 DB 파일 해시까지 항상 같다는 주장은 하지 않는다. 전월세 모든 관측 열 행 digest `a5509aec06b1fddc5650d12dba0db33b0216e7667c2b011b099d894fccbdd8e4`, 매매 `f0abf22d90155a2220a264a9350875d36d15adadf508a6f6cf983162d5c2552f`.

### Contract tests

`python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_collection.py -v`: 최종 수집 검사 15개 통과. 완료 무호출·캐시 검증·페이지 실패/재개·반사 키 차단·일시 오류 3회·성공 0건/변조·필수 값 rollback/모든 오류 보고·경계 기간 제외 추적·부분/stale DB pack 거부·CLI·원자적 manifest 교체 재시도·received journal 무호출 복구·외부 일부 페이지/received 재사용·HTTP 오류 journal 성공 승격 거부를 검증했다. 모두 합성 계약 테스트다.

최종 `python -X utf8 scripts/verify_environment.py`: 제품100개 중99통과/Windows OS 계정 세션 검사1skip, 팀18개 통과, 모델 없는 합성 CLI 통과. `python -X utf8 scripts/check_sdd.py --base origin/main`: features6/AC38/tasks20, 변경 연결 검사 통과. OS 검사의 skip을 성공으로 세지 않으며 실제 세 API 호출은 별도 사용자 세션의 보관함 경로로 성공했다.

### Pilot validation

사용자가 세 API 등록 완료를 통보한 뒤 `molit-pilot-20261012`의 매매 일반 11110/202609 누락 query만 1회 성공적으로 수집했다. 기존 전월세/상세 원본을 재호출하지 않았다. 이후 `collection fetch`는 자격증명 없이 세 query 완료, `new_queries=0`을 반환했다.

| 서비스 | 원본 | 적재 | 기간 제외 | 거부 |
| --- | --- | --- | --- | --- |
| 전월세 | 99 | 99 | 0 | 0 |
| 매매 일반 | 19 | 19 | 0 | 0 |
| 매매 상세 | 19 | 19 | 0 | 0 |

`db-three-api-v3`/`db-three-api-v4`를 새 출력으로 오프라인 생성했다. 실제 SQL 원본 조인은 전월세99/매매38, 세 DB의 integrity_check=ok, FK 위반0이다. 적재 시각을 제외한 **모든 관측 열**을 관측 키 순서로 직렬화해 SHA-256을 비교했고 재생성 결과가 같았다. 전월세 행 digest `25d3f61c0fa11fc48d9689193773bc49cfd39322a738fa6ec56460fb99273ffc`, 매매 `b811814c489b8dffdc7926bfee42dc3761eb5d5f5db29893ff620fc6370bf1d1`. 적재 시각/파일 물리 배치의 차이로 DB 파일 자체 해시 일치까지 주장하지 않는다.

세 서비스 시범 ZIP `pilot-three-api-v4.zip`: SHA-256 `3c8d68602e55e6da07437007d6dae0e5d8b87fbc213fde230a73ba0846dad550`. 로컬 생성만 했으며 업로드하지 않았다. 일부 두 서비스만 담은 이전 감사 ZIP은 전체 완료 증거로 사용하지 않는다.

### Performance and Windows recovery

서울 보존 원본의 첫 DB 생성에서 관측 키 단독 조인은 SQLite EXPLAIN에서 `SEARCH s ...; SEARCH f ...; SCAN o`였다. composite(snapshot_id,observation_id) PK의 선두 키가 없어 전체 관측을 반복 검색했다. 이 채팅이 시작한 해당 오프라인 프로세스만 이름/시작 시각으로 확인해 중단했고, 그 프로세스의 게시되지 않은 `.molit-build-eaeifshn`만 절대 경로·워크스페이스 포함 여부를 검증하여 정리했다. 원본/기존 공개 DB는 보존했다.

관측 키 단독 인덱스를 추가한 새 출력은 `SEARCH o USING COVERING INDEX collection_lineage_id (observation_id=?)`를 확인했다. 기존 두 서비스 서울 아카이브에서 원본246,810 = 유효242,890 + 기간 제외3,920, 거부0을 검증했다. 실제 FK 위반0/세 DB integrity_check=ok/원본 조인 전월세238,620·상세매매4,270. 이 아카이브의 범위는 650조합 중376완료인 부분 배치이며 전체 서울 세 API 완료로 세지 않는다.

실수집은 매매 상세11530/202603의 manifest 교체에서 WinError5로 중단됐다. Windows에서 JSON 읽기 핸들을 연 채 교체하면 같은 오류가 발생하고 핸들을 닫으면 성공하는 것을 별도 임시 파일로 재현했다. 제한적인 원자 교체 재시도와 received journal 검증으로 기존 XML을 재사용해 재개한다. 추가 API 호출 대신 저장된 응답을 복구하는 회귀 테스트가 통과했다. scope helper는 보호된 사용자 홈 쓰기 제한으로 경계를 생성하지 못했으므로 획득한 freeze owner는 없다. 수정은 제품 수집 모듈/테스트/계약으로 수동 제한했다.

기존 v2 donor의11200/202610에는 received journal과 유효3행 XML이 있었지만 기존 캐시 경로가 complete만 받으므로 첫 전체 실행에서 한 query를 다시 호출했다. 두 응답 바이트가 같음을 확인했고 각 원본 배치를 보존했다. 이후 외부 partial/received도 제공 배치의 기록을 수정하지 않고 검증·재사용하도록 수정했다. 두 페이지 외부 부분 배치의 누락 페이지만 요청하고, 외부 received 완료는 호출0/키0으로 복구하는 계약 테스트가 통과했다. 이 수정 전의 중복 호출을 없었던 것으로 보고하지 않는다. 최종 DB에는 해당 query의 관측을 한 번만 적재했다.

### Overall goal boundary

현재 Source Registry의 확정 세 XML API 범위에 대해 원본 확보/복원·관측 적재·행 대사·PK/FK/제약·원본 조인·동일 입력 재생성은 실제 증거로 확인했다. 이 결과는 첫 수집/관측 DB 단계다. 공통 단지/건물/주소/행정구역 엔터티의 통합 명세·출처 간 관계와 증분 통합 검증, 신규 파일/API의 canonical 적재 계약은 후속이며 완료하지 않았다. 단지 매칭/시설/추천 연결의 보류는 유지한다. 실제 검수 추천·Golden·제품 평가 또는 Goal 전체 완료를 선언하지 않는다.

### GitHub record limitation

예약 #5를 검색·재확인했다. 연결 도구의 Issue 본문 수정과 댓글 작성은 GitHub 403 `Resource not accessible by integration`으로 실패했다. 다른 기존 Git 인증으로 기록을 쓰려는 실행은 자동 승인 검토에서 **별도 승인 없는 Git 자격증명 조회와 거부된 Issue 수정의 재실행**이라는 이유로 거부됐다. 그 인증 조회/원격 쓰기는 실행하지 않았고 우회하지 않는다. 완성된 기록문을 로컬에 준비해 명시적 추가 승인 또는 사용자의 수동 게시를 요청한다. 예약은 이미 있으므로 해당 예약의 누락 수집을 수행하되 결과 기록 없이 Drive 업로드는 하지 않는다.

2026-10-13 후속 해결: 사용자가 로그인된GitHub CLI사용과남은입력요청해소를명시했다. 공식CLI의로그인으로 [#5](https://github.com/keulreobeu/jipdam/issues/5)에최종기록을게시하고전체본문일치를확인했다. 이전거부실행/실패이력은보존한다. 현재기록문제는해결되었으며증거는 [재개·게시검증](molit-resume-validation-20261013.md#github-cli-publication)을따른다. Drive업로드와통합Goal완료는수행하지않았다.
