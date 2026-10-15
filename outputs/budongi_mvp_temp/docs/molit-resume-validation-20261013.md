# MOLIT 재개·복원 확인 — 2026-10-13

## Restored archive audit

저장된 checkpoint와 현재 branch `codex/data-collection-records`, HEAD `8d70e41` 및 미커밋 상태를 대조했다. 새 API 수집은 하지 않았다.

현재 실행 환경에서 기존 배치의 `db/` 파일 열기와 ACL 읽기가 접근 거부로 실패했다. 일반 실행과 승인된 읽기 전용 실행 모두 같은 결과였다. 파일 부재·손상으로 판정하지 않았다. 기존 ZIP은 접근 가능하고210,802,677바이트이며 SHA-256이 저장된 `de4df7bf6558f2c78cedfabc2c1160aafd11f4c997b0bdf56166071f36ad4739`와 일치했다.

검증된 ZIP을 새 경로 `data/collection/molit-seoul-three-api-20261012-restored-20261013`에 복원했다. 기존 원본/DB/ZIP/ACL은 변경하지 않았다.2045 ZIP member를 읽으며 CRC를 검사하고 manifest의2038 원본/계획/query 파일 해시 및 세 DB 해시를 대조했다. `collection_status`로975/975query 완료를 다시 확인했다.

| 복원 DB | 실제 행 수 | integrity_check | FK 위반 |
| --- | ---: | --- | ---: |
| rental.sqlite3 | 238620 | ok | 0 |
| sales.sqlite3 | 136272 | ok | 0 |
| staging.sqlite3 | 384211 | ok | 0 |

staging valid374892 + outside_period9319 = 전체384211, 거부0이다. 매매136272는 일반/상세 독립 관측의 합계이며 중복 없는 계약 건수로 표현하지 않는다. XML과 DB hash는2026-10-12 결과와 같고 현재 복원은 새 시점 자료 수집이 아니다.

실행 증거: `.local_runtime/molit-restore-audit-20261013.py` 및 `.local_runtime/molit-restore-audit-20261013.json`. 실행은 네트워크·보관함 접근 없이 ZIP 읽기/새 경로 쓰기/SQL 읽기만 수행했다. 이후 통합의 입력은 이 검증된 복원 경로를 사용한다. 기존 `db/` 접근권한의 세부 원인은 미확정이며 접근권한을 고쳤다고 주장하지 않는다.

## GitHub result record

2026-10-13 연결앱으로 GitHub #5와 댓글을 다시 읽었다. 본문은 기존 예약·수집0건 상태, 댓글0개였다. 준비된 `collection-issue-5-result-20261012.md`를 본문 갱신으로 요청했지만403 `Resource not accessible by integration`으로 실패했다. 별도 Git 인증은 조회하지 않았다. 게시 방법에 대한 사용자 답변을 기다리고 결과 기록/AC06을 미완료로 유지한다.

## Approved continuation

사용자가2026-10-13 “후속 통합 계획대로 진행 (추천)”을 선택했다. [후속 계획](plans/canonical-db-continuation-20261013.md)의 기존 세 API 원본 기반 공통 엔터티·공식 ID 관계·미확정 후보·반복/증분 적재·CSV/JSON/XLSX입력 계약 구현/검증을 승인했다. 새 데이터 수집·좌표·시설·추천·Drive 업로드는 제외한다. 본 문서의 복원 검증은 통합 엔터티 조인이나 증분 처리 구현 완료의 증거가 아니다.

## Operational learning

기존 출력 경로를 직접 읽을 수 없더라도 접근 가능한 보존 ZIP의 저장 해시를 먼저 확인한 뒤 새 경로에서 원본/DB를 복원·검증할 수 있다. 기존 디렉터리의 ACL을 변경하거나 완료 API를 재호출할 필요가 없다. gstack Bash는 현재 일반 실행에서 Windows named-object 접근 오류가 발생했지만 승인된 로컬 helper 실행은 성공했다. 외부 CLI 검토는 실제 설정값 disabled, telemetry와 artifact sync는off를 유지했다.

## Canonical input validation

collection_db의 `validate_normalized_inputs`를pack과integrate가 공유하도록 구현했다. 현재계획hash·완료query의원본hash/파일위치·완료상태·정규화버전·필수DB목록·파일hash를 대조한다. 기본통합은불완전입력을거부한다. 기존pack의명시적부분입력/출력불변/기록URL계약을유지했다.

신규합성회귀3개는동일건수의변경원본을통합/pack양쪽에서거부,계획변경/partial정책,필수DB목록/잘못된manifest/DB변조거부를검증했다. 최초추가assertion은기존JSON형식오류코드를잘못기대하여실패했고 `invalid_manifest` 계약으로수정한뒤3개통과했다. 기존collection15개와신규3개의검사도통과했다. 일반임시디렉터리권한문제로test준비가실패한실행은성공으로세지않으며승인된정상로컬실행의결과를사용한다.

실제검증스크립트 `.local_runtime/canonical-input-audit-20261013.py`는네트워크/보관함차단guard에서검증된복원경로를새helper에입력했다. UTC2026-10-13T00:23:25.238750+00:00,975query전체완료·1062완료XML입력·세DBhash·출처별건수가2026-10-12결과와일치했다. 새API0/키접근0. 상세출력 `.local_runtime/canonical-input-audit-20261013.json`. 이는CANONICAL-001-AC-01의실제입력경계증거이며엔터티/배치증분DB구현완료의증거가아니다.

SDD검사 `scripts/check_sdd.py --base origin/main`은features7/AC45/tasks21/변경경로47로통과했다. 나머지canonicalAC는미완료이며추후실제증거로갱신한다.

최종표준검사 `scripts/verify_environment.py`는제품103개/팀18개모두통과했고모델없는합성CLI도통과했다. 이번정상로컬계정실행에서는Windows Credential Manager의합성round-trip테스트도통과했으며이전제한실행의skip과구분한다. 실제보관함키등록/사용상태를새로조회한것은아니다. 문서업데이트후 `check_sdd.py --base origin/main`을다시읽기검사하여features7/AC45/tasks21/변경경로47통과를확인했다.

다음선택작업은Plan T2의배치/버전/원본·관측소속구조구현이다. 기존단일배치canonical초안은아직이단계요구를충족하지않는다. source_files의단독staging을지원형식의canonical완료라고보지않는다. 전체Goal은active/미완료다. GitHub게시방식질문은아래실제CLI게시로해결되었다.

## GitHub CLI publication

사용자가 “저 입력 필요 제거해주고 github cli 로그인 해둠”이라고 지시했다. 이를 로그인된 공식 GitHub CLI로 이 기존 수집 기록을 게시하도록 허용한 답변으로 처리했다. `C:/Program Files/GitHub CLI/gh.exe`의 계정은keulreobeu, 대상은기존예약Issue #5였다. CLI가현재셸PATH에는없어실제설치경로를사용했다. 제한환경의외부연결실패후승인된네트워크실행으로기록했다. Git credential helper/인증값원문은조회·출력하지않았다.

`gh issue edit 5 --repo keulreobeu/jipdam --body-file .../collection-issue-5-result-20261012.md`가성공했다. 다시조회한원격본문을줄바꿈/마지막공백만정규화하여검토한로컬기록문전체와비교했고일치했다. 원격updatedAt은UTC2026-10-13T00:29:39Z다. 975/975범위·실제행수·단위/미검수한계·수집시각·원본/manifest·ZIP SHA-256·Drive업로드대기가모두게시되었다. [GitHub #5](https://github.com/keulreobeu/jipdam/issues/5). 검증요약 `.local_runtime/github-issue-5-published-20261013.json`.

TASK-MOLIT-001-AC06의필수결과기록조건은충족되어수집Task를verified로변경했다. 전체통합Goal과canonicalTask는미완료다. GitHub게시방법의추가입력은없으며다시요청하지않는다. 입력카드를직접삭제하는앱도구는현재제공되지않아UI삭제성공은주장하지않는다. 실제Drive업로드/Issue닫기/코드push는수행하지않았다.
