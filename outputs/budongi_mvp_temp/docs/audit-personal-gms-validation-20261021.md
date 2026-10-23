# 상태 재검증·개인 GMS 검증 — 2026-10-21

관련: TASK-AUDIT-GMS-001 / Jira KAN-6. 구현·집중 검증 완료, 전체 환경 검증 실패로 진행 중.

초기 재현: `python -X utf8 scripts/check_sdd.py`가 rental-real-data.md의 invalid verification result로 실패했다. readiness 기존 4개 테스트는 workspace TEMP/TMP에서 통과했다. 시스템 sandbox TEMP는 WinError 5였으며 제품 오류와 구분했다. GMS 기존 로컬 서버 8786/8765는 연결할 수 없어 실잔액/만료 조회와 GMS 초안을 실행하지 않았다. 과거 2026-10-16 만료 기록으로 현재 키 상태를 단정하지 않는다.

근본 원인: 최신 승인 연결을 오래된 canonical 상태 요약에 반영하지 않은 문서, enum 위치에 설명을 넣은 Task, 상태 게이트 변경에 대한 회귀 누락, 단일 policy와 전체 calls 합계로 여러 개인 키를 함께 계산한 GMS 구조다.

## 지적 사항 재검증

| 항목 | 결과 |
| --- | --- |
| 연결 0건 문서 | 이전 canonical과 2026-10-20 검수 serving을 구분하도록 Project/RENT Spec·MVP Task·README·AGENTS를 수정. 실제 serving 238,620관측/203,159관계/35,461미확정을 재확인 |
| SDD result 형식 | 설명문 두 곳을 `passed`로 정정. 근거/설명과 실제 제품 AC 미완료는 보존. `check_sdd.py` 및 `--base origin/main` 통과(18기능/98AC/38Task) |
| readiness 회귀 | 8개 통과. 확정 관계의 unknown/correction_pending 차단, 미연결 unknown 제외, valid/cancelled 처리, DB/집계 오류의 거짓 ready 방지 |
| GMS 기준/만료 | 현재 1,000·개인 키별 원장으로 문서/화면을 동기화. 2026-10-16 만료는 과거 키 관측값으로만 보존. 기존 설정 서버 부재로 현재 키 실잔액/만료는 미확인 |

readiness에 상태 집계를 추가했던 기존 변경은 쿼리 실패 후 읽어 둔 `state`를 남겨 일부 게이트를 ready로 표시할 수 있었다. 예외 때 상태를 초기화하고 상태 집계 수와 확정 관계 메타데이터가 다르면 blocked로 처리했다. 실제 추천 게이트는 완화하지 않았다.

## 실제 DB 읽기 전용 감사

`data/rental/serving/reviewed-20261020.sqlite3`의 SHA-256은 검사 전후 모두 `8369658d4866d2f3277eecfbe47ab7eeafd16df7c731c611a527c98224e8f69d`였다. `integrity_check=ok`, FK 위반0, 관측238,620/관계203,159, 상태 unknown203,159/unreviewed35,461을 확인했다. 전세/강서구11500/보증금10억원/limit5의 정상 스키마 요청은 `data_not_ready`, 결과0, 취소·정정 상태 추가 검수 사유를 반환했다. 첫 probe는 잘못된 입력 키 kind/regions로 거부됐고 올바른 rental_type/districts로 재실행했다. 첫 입력 오류를 제품 결함이나 성공 근거로 세지 않았다.

`data/rental/review_build/canonical-v3-20261020-reviewed-ids/`는 sandbox 밖 읽기에서도 Windows 접근 거부였다. ACL 변경/원본 재생성 없이 중단했다. 원본 해시·패키지 계보 전체 재검증은 blocked, 거래 상태는 needs_input, 실제 추천 품질/실모델/좌표·시설/Golden 미완료다. 기본 serving 경로와 검수 serving 별도 실행 명령을 README에 명시했다.

## GMS 개인 키 자동 기록

- 기존 사용자 프로필의 보관함 경계를 유지하고 선택 키별 정책/누적/예약/잔액/전체 호출 페이지를 분리했다. 관리 이름은 직접 입력하며 별칭·폴더로 소유자를 추측하지 않는다.
- 동일 키 중복 등록은 원장을 공유하고, credential ID가 같아도 실제 키가 바뀌면 기존 견적을 무통신 거부하고 새 비활성 정책으로 시작한다.
- 카운트/생성/연결 시험마다 Task·모델·시각·정산 상태·계산 입력/실사용 토큰·요율 비용·계정 관측 차감·보류를 자동 기록한다. CLI/하네스도 같은 runner다. 실패/usage 누락을 사용량0으로 처리하지 않는다.
- 기존 calls/model 행은 변경/삭제하지 않으며 귀속 미확인은 legacy_unattributed로 남긴다. 불확실 과거 예약은 검수 전 유료 차단한다. 실제 사용자 보관함의 이관·키 선택/정책 변경은 이번 실행에서 하지 않았다.

합성 GMS/budget HTTP·CLI **44개**, 기존 GMS **12개**, readiness **8개**(합계64개) 통과. 팀/SDD unittest **27개** 통과. `node --check .../credentials.js`, `git diff --check` 통과. 실제 GMS 유료 count/생성은0회이며 실키 성공은 주장하지 않는다.

임시 합성 서버와 IAB로 A→B→A를 실제 선택했다. A의4크레딧/120토큰/2내역, B의0/0/0내역, A복원 후 동일 내역을 확인했다. 원격 provider는 FakeClient만 사용했다. 합성 화면 증거는 ignored `.local_runtime/audit-20261021/personal-gms-ui.png`; 탭/합성 서버는 종료했다.

## 전체 검사와 남은 실패

공식 `python -X utf8 scripts/verify_environment.py` 첫 실행은 제품290개 중 기존 canonical 폴더 교체2오류와 변경한 화면 제목의 문자열 검사1실패였다. 제목은 기존 GMS 연결 확인 문구를 보존해 관련12개 검사를 통과했다. canonical2개만 재실행한 결과 첫 테스트는 통과했지만 두 번째는 다른 format(json)에서 같은 WinError5가 재현됐다.

최종 전체 재실행은 제품 **292개 중291개 통과/1오류**다. `test_collection_integration.CanonicalSnapshotTests.test_row_lineage_lookup_does_not_scan_entire_batch_for_each_observation`가 `collection_db.py:284`의 합성 `.molit-build-*`→`db` 디렉터리 `os.rename`에서 WinError5로 실패했다. 이번에 수정하지 않은 수집 DB 게시 경로이며 실패 위치가 실행마다 달랐다. 전체 통과로 보고하거나 임의 재시도로 숨기지 않는다. 공식 검사 후속 합성 CLI smoke는 이 실패로 실행되지 않았다. 팀27개는 별도 실행해 통과했다. 로그는 ignored `.local_runtime/audit-20261021/environment-final.log`와 `canonical-rerun.log`에 있다.

전체 환경 검사·원본 접근·현재 실키 확인이 미완료여서 Jira KAN-6 및 Task는 진행 중으로 유지하고 오토커밋하지 않았다. 다음 범위는 디렉터리 게시 WinError5 원인과 원본 접근 권한을 별도로 조사하고, 사용자가 선택한 개인 GMS 설정 서버가 준비되면 잔액/만료와 기존 귀속 미확인 예약을 검수하는 것이다. 새 수집·관계 승격·원본 변경·외부 업로드는 하지 않았다.

운영 학습: Windows sandbox의 시스템 TEMP와 loopback 제한은 제품 실패와 분리해 workspace TEMP 및 허용된 로컬 테스트로 재검증한다. 그 이후에도 남은 원본 폴더 ACL/디렉터리 rename 실패는 별도 환경 게이트로 보존한다. 전역 합계와 트랜잭션 내 call count를 함께 키별로 바꿔야 개인 키 전환이 동작한다.
