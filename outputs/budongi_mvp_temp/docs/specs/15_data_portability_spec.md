# PORTABLE-001 — 원본 공유와 오프라인 DB 재구성

```toml
kind = "spec"
id = "PORTABLE-001"
status = "approved"
owner = "Codex"
revision = 2
approved_by = "사용자"
approved_at = "2026-10-14"
approval_ref = "2026-10-13 포터블 패키지 승인에 더해 2026-10-14 사용자가 '원본을 드라이브에 저장해두고 필요하면 드라이브에서 받아서 쓸 수 있게 만들어' 요청"
```

## 범위

기존 MOLIT 서울 세 API 전체 원본·종로구 증분 이력 및 제공 통계 30개를 대상으로 한다. 원본/설정/변환 코드/해시/복원 명령을 ZIP으로 보관한다. 복원은 API 호출·키 없이 새 출력 경로에 수행한다. 현재 사용자 요청은 이 자료의 GitHub 기록·Drive 업로드와 구현 코드의 새 브랜치 푸시를 승인한다. 원본/DB/API 키는 Git에 넣지 않는다. 기존 합성·역사 자료는 이번 실제 원본 패키지와 구분한다.

## PORTABLE-001-REQ-01 원본과 재현 입력

MOLIT 기존 ZIP의 원본/manifest/DB를 그대로 포함하고, 주 통합 DB의 종로구 배치 원본/계획도 포함한다. 통계는 30개 원본 bytes·기존 DB·검수 이력을 보존한다. 각 패키지에 필요한 Python 코드·registry·의존성 안내와 모든 포함 파일 SHA-256 manifest를 넣는다. archive_root/적재 시각은 환경별 기록이며 논리 데이터 대사에서는 구분한다.

### PORTABLE-001-AC-01

원본 해시·ZIP CRC·전체 포함 파일 해시가 일치하고 manifest에 실제 범위/건수/단위/품질/미확정 사항이 있다.

## PORTABLE-001-REQ-02 안전한 재구성

복원 스크립트는 해시 검증 후에만 수행하며 경로 탈출/기존 출력 덮어쓰기를 거부한다. MOLIT 관측 DB를 원본에서 다시 생성하고 최초 보관 순서인 종로구→서울 전체로 canonical v3를 생성하여 과거 후보 근거를 보존한다. 통계는 원래 제공 파일명으로 입력해 동일 mapping/source_view/정밀도를 복원하고 검수 이력을 연결한다. 네트워크/키 접근을 차단한 실행에서도 동작해야 한다. 임시 폴더도 충분한 공간이 있는 드라이브를 사용한다.

### PORTABLE-001-AC-02

새 폴더에서 실제 거래·통합·통계 DB를 재생성해 원본 DB의 모든 논리 테이블 값/건수와 대사하고 SQLite 무결성/FK를 확인한다. 환경별 batches.archive_root, rental_snapshots.created_at_utc, rental_observations.ingested_at_utc, 통계 import_batches.imported_at_utc만 재구성 위치/적재시각으로 명시적으로 제외한다. 원본 수집시각·계약일·수치·기타 모든 필드는 대사 대상이다.

## PORTABLE-001-REQ-03 공유 기록

기존 수집 Issue의 완료/예약과 Drive 동일 파일을 먼저 확인한다. 기존 MOLIT #5를 재사용하고 제공 통계는 별도 수집 기록을 만든다. 업로드 전 최종 ZIP SHA-256/manifest/결과를 게시하고 업로드 후 개별 파일 링크·크기/내용 해시를 확인한다.

### PORTABLE-001-AC-03

공유 폴더의 두 ZIP을 원격 메타데이터 또는 다운로드 SHA로 확인하고 해당 수집 Issue에서 개별 파일 링크/해시가 일치한다.

## PORTABLE-001-REQ-04 구현 공유

원격 브랜치 확인 결과 다른 작업 브랜치가 있으므로 기존 브랜치에서 새 codex 브랜치를 만든다. 최신 main을 통합하고 변경/필수 검사/문서/원본 제외를 확인한 뒤 일반 push한다. 강제 push하지 않는다. 이번 요청의 다른 브랜치 조건은 main 직접 병합을 요구하지 않는다.

### PORTABLE-001-AC-04

원격 새 브랜치의 SHA가 로컬 제출 커밋과 같고 재구성 스크립트/관련 구현이 있으며 원본/DB/ZIP/키는 없다.

## PORTABLE-001-REQ-05 요청 시 Drive 패키지 다운로드

명시한 `statistics` 또는 `molit` 패키지만 Google Drive에서 내려받는다. 내려받을 파일은 고정 Drive 파일 ID에 연결하고 파일별 크기·SHA-256을 확인한다. MOLIT 조각은 조각별 검증 뒤 기존 전체 ZIP 크기·SHA-256과 대조해 재조립한다. 성공한 새 출력 폴더만 게시하며 기존 경로를 덮어쓰지 않는다. 다운로드된 ZIP은 기존 오프라인 `shared_data.py verify/rebuild` 절차로 사용한다. 자동 다운로드/압축해제/재구성은 하지 않는다.

### PORTABLE-001-AC-05

요청한 패키지만 Drive에서 내려받고 원본 Drive 링크에 접근할 수 없거나 파일이 바뀌면 실패한다. 각 다운로드 파일의 크기/해시, MOLIT 전체 ZIP 해시를 확인하고 기존 출력 보존을 검증한다. 다운로드 후 재구성은 네트워크 없이 기존 PORTABLE-001-AC-02를 따른다.
