# Drive 패키지 요청 시 다운로드 검증 — 2026-10-14

## 현재 제한

Drive connector 조회로 공유 폴더의 기존 패키지 ID/파일명/크기를 확인했다. 통계 패키지는 87,135,693 bytes, MOLIT ZIP은 210,915,139 bytes이며 MOLIT 조각 크기·해시는 Drive의 기존 parts manifest와 일치한다. 로컬 직접 요청 `HEAD https://drive.google.com/uc?export=download&id=1SQot8SCZXC-MdketgQPyoyROADwPWnbP`는 `drive.google.com` DNS 오류로 실패했다. 따라서 실제 CLI 다운로드, 최종 재조립, 재다운로드/기존 출력 보호는 아직 검증하지 않았다.

읽기 전용 로컬 용량 조사에서 `data/`는 9.81 GiB였다. `data/collection/`은 9.18 GiB이며 그중 복원 배치 폴더가 8.40 GiB다. 이 폴더에 각각 약 1.68 GiB인 canonical DB 4개와 1.11 GiB staging DB가 있다. 통계 DB는 0.38 GiB다. 따라서 로컬 사용량은 ZIP 원본만이 아니라 여러 재구성 버전의 DB가 주로 차지한다. 기존 로컬 자료는 삭제하지 않았다.

Drive metadata 조회에서 통계 ZIP의 `anyone` 권한이 `writer`로 표시됐다. 다운로드 도구는 읽기만 하지만 파일 권한은 변경하지 않았다. 다른 사람과 링크를 공유하기 전 Drive에서 최소 `reader` 권한으로 조정할 필요가 있다.

## 2026-10-14 로컬 중간 DB 정리

사용자 요청에 따라 검증이 끝난 중간 canonical v2 DB 세 개를 삭제했다: `canonical-v2-20261013/canonical.sqlite3`, `canonical-v2-growing-20261013/canonical.sqlite3`, `canonical-v2-incremental-20261013/canonical.sqlite3`. 최종 권장 `canonical-v3-20261013/canonical.sqlite3`, 제품 serving DB, 원본 폴더와 관측 DB는 남겼다. 삭제 뒤 `data/` 총 파일 용량은 4.89 GiB로 확인됐다. 세 파일은 Drive 포터블 패키지와 보존 원본에서 재구성할 수 있다.

`TASK-PORTABLE-DOWNLOAD-001` AC-05는 미완료이며, 실제 다운로드가 가능한 환경에서 실행 후 갱신한다. 기존 PORTABLE-001의 두 ZIP/DB 재구성 검증은 [2026-10-13 공유 검증](shared-data-validation-20261013.md)에 별도로 보존한다.

## 2026-10-14 다운로드 최종 확인

확인 폼의 uuid를 보존하도록 수정한 뒤 통계 87,135,693 bytes와 MOLIT 조각 3개 및 전체 ZIP 210,915,139 bytes를 실제 다운로드했다. 파일별/전체 SHA-256과 ZIP CRC가 일치했고, 같은 출력으로 재실행하면 다운로드 전 거부하며 기존 파일 해시가 유지됐다. 합성 다운로드 회귀 4개도 통과했다. TASK-PORTABLE-DOWNLOAD-001은 verified다. 상세 원인·명령·해시는 [후속 검증](continuation-validation-20261014.md)을 따른다. 위 DNS/미실행 문단은 초기 실패 기록으로 보존한다.
