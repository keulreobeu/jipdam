# 통합 DB 검증 — 2026-10-13

## Current scope

CANONICAL-001 승인 범위의 기존 서울 세 API 원본만 사용한다. 실제 새 API/키 접근/좌표시설/추천/Drive 업로드는 없다. 이전 Goal turn은GitHub #5 실제 게시·전체 본문 대조와수집Task verified전환으로 authoritative state를진행시켰다. 이번 실행은 배치/버전/관계·형식 확장 검증이다. 최종 판정은 아래 완료 감사와 verified Task를 따른다.

## Canonical model and synthetic contracts

canonical_real_estate_v2는원본콘텐츠/파일/행을배치소속과분리한다. staging검증상태는batch별,정규화관측은raw row/version별,유효관측소속은batch별이다. 이전봉인DB의해시/스키마/무결성을확인하여새출력에복사하고이전파일을변경하지않는다. 복사본에서만봉인trigger를해제하여적재한뒤새출력을다시봉인한다. 같은batch/version/입력에다른내용은거부하며새배치의동일원본은관측추가없이새소속만생긴다.

공식MOLIT매매상세aptSeq는출처namespace의단지ID이며거래/건물ID가아니다. 지역충돌은identity_conflicts에남기고해당확정연결을만들지않는다. 주소성분은검증/자리수표준화하고단지/주소근거를관계표로보관한다. building/source유효기간이없으면NULL/미연결이며임의생성하지않는다. 라벨후보는pending/unverified/score NULL이며자동확정하지않는다. 후보용공식엔터티증거를먼저요약하여거래행끼리조인하지않는다.

`test_collection_integration.py`는 초기10개, 최종12개 검사가 통과했다. 기존입력경계3개와반복/새배치/버전/충돌rollback/이전DB불변/공식주소/후보/충돌/CLI/규모회귀를포함한다. 기존collection15개검사도통과했다. 합성자료결과를실제수집자료로세지않는다.

## Actual pilot

기존전체XML의종로구11110/202609/세출처를검증하여`data/collection/canonical-pilot-20261013`에복사했다. fetch/build/integrate전체를네트워크/보관함차단guard에서실행했다. 새시점조회가아니라보존된원본의재사용이다.

실제137관측(전월세99/매매일반19/상세19),단지17,주소17,공식단지조인19,단지주소근거19,미확정후보49를확인했다. 전체lineage조인137,FK위반0,integrity_check=ok,building0/원천유효기간NULL. 최초pilotDBhash는`c909becf66ec3b3bd68c974504e8b888743e3267132883ba09dca53fc1a63425`이며원천품질source_unverified이다. 이는전체서울증거가아니다.

## Lineage performance regression

최초서울확대실행의원본행찾기SQL이`SEARCH s USING INDEX staging_state(batch_id=?)`를선택했다. 배치의전체staging행을읽은뒤legacy관측ID를검사하여유효관측마다반복검색했다. 실행중owned프로세스의명령/시작시각/PID를확인했다(2026-10-13KST09:47:32,실작업PID15380,launcher28576). 해당실작업만중단했고도구session28553은exit1로종료했다. 관측timeout을프로세스종료로간주하거나살아있는프로세스를중복재시작하지않았다.

현재입력의source/file reference/hash/row position에서결정적으로계산한raw_item_id를조건으로사용하도록수정했다. 동일조회EXPLAIN은`SEARCH s USING INDEX sqlite_autoindex_staging_items_1(batch_id=? AND raw_item_id=?)`및raw_items/raw_files의PK검색으로바뀌었다. source/원문/정규화필드의대사는그대로유지한다.

합성1000행의실제SQLiteVM작업량을500만명령으로제한하는회귀를추가했다. 수정전조회문을제품파일수정없이메모리에서재현했을때`sqlite3.OperationalError: interrupted`로예상실패했고수정후동일회귀가통과했다. 첫실행의미게시부분DB는보존했으며원본/완료pilot는삭제하지않았다. 잘못된실행계획을숨기거나성공으로기록하지않는다.

증거는 `.local_runtime/canonical-lineage-red-probe-20261013.json`, 수정 전 부분 보고 `.local_runtime/canonical-real-audit-20261013.json`, 수정 후 감사 `.local_runtime/canonical-real-audit-20261013-indexfix.json`이다. 수정 후 감사는 `audit_complete:true`, exit 0으로 완료됐다. 완료 증거를 보존한 뒤 작업자가 만든 실패 임시 DB와 재실행 비교용 DB 복사본만 정리했다. 원본과 주 통합 DB, 증분 DB는 유지한다.

## Actual full collection and replay — confirmed progress

2026-10-13 실제 서울 전체 감사가 완료됐다. 확정 범위 975개 지역·월·서비스 조합과 원본 XML 1,062개를 사용했다. 원본 384,211행 중 유효 관측 374,892행이 적재됐고, 기간 밖 9,319행은 제외 사유와 원본 추적 관계를 보존했다. 파싱 거부 행은 0이다. 매매 일반과 상세는 출처별 관측이며, 합계를 고유 거래 수로 해석하지 않는다.

공식 출처 ID 기준 단지 5,890개, 주소 5,839개를 보존했다. 공식 단지·주소·관측 조인 68,135행, 전체 원본 추적 조인 374,892행을 확인했다. SQLite 무결성 검사는 ok, FK 위반은 0이다. 후보 271,250건은 모두 pending/unverified이고 점수는 NULL이다. 공식 ID `11230-2029`의 지역 충돌 1건은 근거를 별도로 기록하고 확정 연결을 만들지 않았다. 해당 관측은 보존한다. 원천 품질 상태는 source_unverified다.

같은 배치 재적재 시 17개 테이블 모두 추가 행 0개였고, 정렬한 전체 행 값의 해시가 최초 DB와 일치했다. 전체 DB에 기존 종로구 배치를 추가하는 중복 범위 증분에서도 새 원본 행·관측은 0개, 새 배치 소속만 생성됐으며 원본과 이전 DB는 유지됐다.

종로구→서울 전체 범위 확대도 완료됐다. `.local_runtime/canonical-growing-audit-20261013.json`은 audit_complete:true이며 새 원본 행 384,074개와 새 관측 374,755개를 추가했다. 최종 고유 관측 374,892개, 전체 배치 원본 추적 조인 374,892개, 이전 DB 해시 불변을 확인했다. 새 시점 API 조회가 아니라 보존된 실제 범위 확대 검증이며 API/키 접근은 0회다.

주 통합 DB는 `data/collection/molit-seoul-three-api-20261012-restored-20261013/canonical-v2-20261013/canonical.sqlite3`이며 SHA-256은 `cc98e0711e05588b5d3db11c29b4f7a2bc19ee127384a4cff153f01a9b876e81`이다. 실제 감사 보고와 `.local_runtime/canonical-entity-sql-audit-20261013.json`에 조회 결과를 보존했다. 이 단계의 API 호출과 키 접근은 모두 0회다.

파일 canonical 연결과 실제 범위 확대를 구현·검증했다. v3 사본 변환의 실제 전체 행 대사와 최종 회귀·환경 검사가 완료됐다. 완료 판정은 아래 Goal 완료 감사와 Task의 AC별 근거를 따른다.

## File adapter preliminary validation

등록 CSV/JSON/XLSX의 원본/단위/날짜/공백/섹션 검증 8개가 통과했다. 중첩 JSON, 모든 XLSX 시트·빈 시트, 같은 값의 다른 행, 정확한 금액, 출처 계약/버전, 무관한 Registry 항목 추가 후 재사용, 봉인/변조 거부와 JSON 선택 경로 분리를 검증했다. 파일별 expected_rows와 섹션별 대사를 구분하며 거부 행은 canonical 공개를 막는다.

검증에서 CollectionError가 ValueError 하위 형식이라 날짜/숫자 사유가 일반 오류로 덮이는 것을 확인하고 사유를 보존하도록 수정했다. 최신 파일 단계는 v4이며 JSON 선택 경로를 해시 원본 참조와 원래 pointer 섹션으로 구분한다. v3 출력을 덮어쓰지 않는다.

파일→canonical 합성 통합 9개가 통과했다. 세 형식의 원본/정확한 17자리 원 정수/행 추적, 여러 지역·월과 기간 제외, 빈 시트, 동일 배치/새 배치/새 버전, 입력 충돌 rollback, 공식 단지·건물·주소 성분, 지역 충돌 격리, 합성/실제 품질 혼합 거부, CLI 실행을 검증했다. 신규 엔터티 배치 추가 뒤 과거 배치 재실행은 과거 후보를 바꾸지 않는다. 원본 전체를 다시 파싱해 모든 staging 행을 대사한 뒤 같은 공통 스키마로 적재한다. 이는 실제 신규 파일 출처 수집 증거가 아니다.

CLI 시험의 최초 실패는 테스트가 존재하지 않는 budongi.__main__ 진입점을 사용한 원인이며 실제 budongi.cli 진입점으로 수정해 통과했다. v2→v3 시험은 모든 행 대사를 통과했으나 테스트가 SQLite 연결을 닫지 않아 Windows 임시 폴더 정리에서 실패했다. 명시적 close를 추가했고 최종 12개 통합 회귀와 전체 환경 검사에서 통과했다. 실패를 제품 통과로 숨기지 않는다. 사용법과 스키마·확장 계약은 [canonical-db.md](canonical-db.md)를 따른다.


## Final canonical v3 and checks

최종 권장 DB는 `data/collection/molit-seoul-three-api-20261012-restored-20261013/canonical-v3-20261013/canonical.sqlite3`다. SHA-256은 `e08d0cd38cceba3d425f453edc807bf4a14fdc587db1806a2136a25e6912b8f2`다. 실제 변환 감사 `.local_runtime/canonical-v3-actual-audit-20261013.json`과 출력 폴더의 `full-audit-report.json`은 audit_complete:true, 이전 DB 해시 불변, 17개 테이블 전체 정렬 행 digest 일치, 서울 전체 lineage 374,892, integrity ok/FK 위반 0을 기록한다. 관측 digest는 `e28f999e79e22a30922625229b464de4c40e8c452c98229885224fb1b97b008b`로 최초 전체 DB와 같다.

최종 DB는 전체 서울 배치와 종로구 보존 배치의 이력을 함께 담는다. 고유 원본 384,211행·관측 374,892행은 한 번만 저장하지만 배치 관측 소속은 375,029건, coverage는 978건이다. 서울 전체 배치 후보 271,250건과 종로구 당시 후보 49건을 보존하므로 전체 후보는 271,299건이다. 재실행이 과거 후보를 다시 계산하지 않는다. quality-report.json은 현재 재실행한 종로구 배치와 전체 테이블 수를 보고하며, full-audit-report.json은 서울 전체 배치 감사를 별도로 제공한다.

최종 `scripts/verify_environment.py`는 제품 unittest 129개·팀 계약 18개와 모델 없는 합성 CLI smoke를 통과했다. 로그는 `.local_runtime/canonical-environment-completion-20261013.log`다. 통합 입력/관계/재실행/버전/rollback/제약/복사 변환 12개, 파일 보존 8개, 파일→canonical 9개가 포함된다. 같은 건수의 변경 입력, DB 체크섬을 다시 계산한 잘못된 정규화 값, 등록/승인 없는 출처, 선택 JSON 배열의 서로 다른 행, 17자리 원 정밀도를 검증한다. `check_sdd.py --base origin/main`도 최종 Task/문서 갱신 후 다시 확인한다.

GitHub #5는 2026-10-13 최종 조회에서도 원본 384,211행과 원본 포함 ZIP SHA-256이 유지됐다. 새 원격 게시·Drive 업로드·코드 push/PR/merge는 수행하지 않았다. 확인된 범위만 완료 처리한다.

## Goal completion audit

독립 구성 결과 대사도 완료했다. 최초 서울 전체 단일 적재와 종로구→서울 XML 기반 확대 적재 후 v3 변환 결과를 서울 배치 범위로 맞춰 비교했다. 17개 테이블의 전체 정렬 행 수와 SHA-256이 모두 일치했다. 배치별 테이블은 서울 batch_id로 필터하고 콘텐츠·원본 행·관측·공통 엔터티는 전체 값으로 비교했다. `.local_runtime/canonical-independent-derivation-audit-20261013.json`과 최종 DB 폴더의 `independent-derivation-audit.json`은 audit_complete:true/17개 일치를 보존한다. 물리적 DB 파일 해시 일치와 의미상 전체 행 일치를 혼동하지 않는다.

| 성공 조건 | 실제 근거와 판정 |
| --- | --- |
| 1. 확정 원본 확보 | Source Registry의 필수 세 XML 출처, 25구×13월×3=975/975 조회 완료, 1,062 성공 XML. MOLIT 전체 감사·복원 감사·최종 입력 재검증 통과 |
| 2. 복원 가능한 원본/이력 | 응답 바이트·페이지/시도 manifest·수집 시각·파일 해시·원본 포함 ZIP 보존. ZIP 해시/CRC/파일·DB 해시 확인 및 새 경로 실제 복원 통과 |
| 3. 전체 파이프라인 | 기존 XML→오프라인 두 관측 DB/staging→공통 v3 DB 실제 실행. 등록 CSV/JSON/XLSX는 원본→staging→원본 전체 대사→같은 canonical 적재의 합성 시험 통과 |
| 4. 유효 행/사유 | 실제 raw 384,211=valid 374,892+outside 9,319+rejected 0. 모든 유효 행의 canonical/원본 추적 조인 일치, 기간 제외 원문·사유 보존 |
| 5. 무결성 | 실제 전체 integrity_check=ok/FK 위반 0, PK/UNIQUE/NOT NULL/CHECK의 오류 강제 시험 통과, 최종 출력 봉인 |
| 6. 실제 조인 | 전체 관측→출처/지역/원본 374,892행, 공식 단지→주소→지원 관측 68,135행. 단지 5,890/주소 5,839, 건물 0과 사유·공식 ID 충돌 1건 명시 |
| 7. 기존/신규 통합 규칙 | Spec/ADR/실행 문서의 출처 namespace·원본/행/버전·배치 소속·불확실성 규칙, 여러 출처·새 파일 배치·새 매핑 버전·공식 ID 충돌 시험 통과 |
| 8. 반복/증분 | 동일 실제 배치 신규 0·17개 전체 행 digest 일치, 겹치는 범위 재사용과 종로구→서울 신규 관측 374,755 추가, 이전 DB 불변. 실제 v2→v3 복사 변환 전체 행 일치 |
| 9. 문서/실행/품질 | Source Registry, MOLIT/CANONICAL Spec, ADR, Task, 공식 매핑과 canonical-db.md, 실제/합성 감사·환경/SDD·GitHub 수집 기록 보존 |

현재 확정 수집 범위와 승인된 후속 통합 계약에서 9개 성공 조건의 증거를 확인했다. 미확정 후보와 충돌은 요구한 격리 정책의 결과이며 사람 검수 완료로 표시하지 않는다. 새 실제 파일 출처·좌표·시설·추천 서비스·Golden·Drive 업로드는 현재 승인/수집 범위에 포함되지 않는다. 이 문서는 이후 추천에 활용할 통합 데이터 기반 완료를 입증하며 추천 제품 완료를 뜻하지 않는다.
