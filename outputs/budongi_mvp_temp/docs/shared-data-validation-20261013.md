# 공유 패키지 검증 — 2026-10-13

## Package integrity

두 ZIP 생성/CRC/전체 포함 파일 SHA 검증 완료. 통계87,135,693 bytes/59 entries, MOLIT210,915,139 bytes/36 entries. 최종 해시는 [공유 안내](shared-data.md)에 있다. MOLIT 내부 기존 ZIP SHA는 de4df7bf6558f2c78cedfabc2c1160aafd11f4c997b0bdf56166071f36ad4739 그대로다. 통계 보관DB/원본30개도 원래 bytes와 일치한다. 코드/registry/의존성 버전 포함. 100MB 도구 제한 때문에 국토부 ZIP을 세 조각으로 나눴고 재조립한 전체 SHA가 e9eeb0c1057e16f11066c42e704ffd38d88e93bc59dda797a3b250c7366cc013로 일치했다.

## Actual rebuild

통계 ZIP을 새 relocated-statistics 폴더에 풀고 원본30개로 rebuilt-statistics DB를 생성했다. 네트워크 차단 상태에서 전체 논리 테이블 값/건수(530,556셀)/검수12건이 원래 DB와 일치하며 integrity/FK 검사 통과. import_batches.imported_at_utc만 새 실행시각으로 구분했다. Git 제외 .local_runtime/shared-data-20261013/rebuilt-statistics/rebuild-verification.json에 근거가 있다.

최종 MOLIT ZIP을 D의 final-relocated 폴더에 새로 풀고 패키지의 shared_data.py rebuild --output D:/jipdam-portability-20261013-01a1331f/final-rebuilt 명령을 독립 실행했다. 네트워크 차단 상태에서 관측DB/종로구→서울 전체 canonical v3 생성·모든 논리 테이블 digest 대사·SQLite 무결성/FK까지 exit0/verified로 통과했다. 관측374,892·원본384,211·배치2·배치관측소속375,029·후보271,299·단지5,890·주소5,839·충돌1이 원래 DB와 같다. 기존 DB는 변경하지 않았다. archive_root 및 rental_snapshots.created_at_utc/rental_observations.ingested_at_utc만 새 환경/적재시각으로 구분했다. 원본 수집시각/계약일/금액 등 모든 나머지 필드를 비교했다.

초기 실패도 보존 기록으로 구분한다. 첫 압축해제는 C 여유0/Errno28, 두 번째 전체 대사는 SQLite 정렬 임시 공간 부족이었다. D로 임시 공간을 지정한 대사에서 rental 두 적재시각 차이와 후보41건 차이를 확인했다. 원래 pilot→full 이력 순서로 복원 코드를 수정하고 최종 ZIP/manifest/기대 사실/코드를 다시 생성한 뒤 위의 전체 명령을 처음부터 끝까지 재실행했다. 실패/이전 해시 패키지는 공유 완료 증거로 사용하지 않는다. 최종 근거는 .local_runtime/final-molit-rebuild-20261013.log와 D 출력의 rebuild-verification.json이다.

## Branch and checks

fetch/ls-remote에서 main=f5c356c0773af136d160b245cc548cb784d8d075 및 codex/data-collection-records=8d70e41ac23898d4e4aea1c0ec4633cd8a1de9fb 확인. 기존 브랜치에서 codex/data-portability-20261013 생성, origin/main 병합 완료. Git 명령에만 Codex/codex@openai.com 작성자를 사용했고 전역 설정은 변경하지 않았다. 사용자가 새 브랜치의 코드·완료 기록 push를 명시 승인한 뒤 일반 push를 수행했다. ls-remote의 원격 커밋 618f9c7fdbf68d08ab5176d5eb3b5ccb2401a7fd가 로컬과 같고 변경64개 파일에 원본/DB/ZIP/XML/키 파일이0개임을 확인했다. 워킹 트리는 clean이다. [제출 브랜치](https://github.com/keulreobeu/jipdam/tree/codex/data-portability-20261013)에 구현·복원 명령·Spec/Task/검증 기록을 보존한다.

최종 코드의 verify_environment에서 제품137개·팀22개·합성 CLI 통과(.local_runtime/ship-environment-parts-final-20261013.log). 패키지 검사4개는 변조/경로 탈출, ZIP CRC/기존 출력 보존, 논리 값 변경 탐지/환경경로 구분, 실제 분할 ZIP 재조립/변조 거부를 다룬다. SDD 기본/--base origin/main 통과(features9/AC54/tasks23), git diff --check 통과.

gstack-ship의 내부 읽기 전용 adversarial review 완료, 구체적 P1/P2 발견0. 외부 CLI/릴리스/PR는 브랜치 푸시 요청과 별도이며 실행하지 않았다. 실제 두 패키지 복원 대사와 최종 검사 완료를 제출 조건으로 권고했다.

## Remote state

Drive 계정 kwulreobeu@gmail.com/기존 jipdam_db를 조회해 기존 합성 ZIP1개를 보존했다. 통계 ZIP1개와 국토부 3조각/parts.json/재조립 코드/안내6개 업로드 완료. 각각의 부모 폴더/크기를 확인하고 Drive에서 다시 스트리밍 다운로드한 모든 파일 SHA가 로컬 원본과 일치했다. 통계 readback87,135,693 bytes/SHA83f0e40a...; 국토부 조각과 보조 파일6개는 .local_runtime/molit-drive-readback-proof-20261013.json으로 증명한다. 제공자 임시 다운로드 파일명에 붙는 .bin은 원래 Drive 파일명과 연결해 대사했다. 전체 ZIP 해시는 조각별 동일성과 로컬 재조립 검증으로 확인했다.

처음 GitHub/Drive 쓰기는 자동 검토가 구체적 게시 내용/ZIP/목적지 승인을 요구했고 사용자가 각각 명시 승인했다. GitHub API403은 사용자가 설치 권한을 갱신한 뒤 정상화됐다. 브라우저 우회는 하지 않았다. 업로드 전 #5/새 #6에 결과/해시를 게시했고 업로드 후 두 Issue 본문을 개별 Drive 링크/원격 검증/재구성 결과로 갱신했다. [MOLIT #5](https://github.com/keulreobeu/jipdam/issues/5), [통계 #6](https://github.com/keulreobeu/jipdam/issues/6).
