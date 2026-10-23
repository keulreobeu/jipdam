# TEAM-REF-001 — 팀 제공 통계·시설 패키지 별도 적재

```toml
kind = "spec"
id = "TEAM-REF-001"
status = "approved"
owner = "Codex"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-20"
approval_ref = "2026-10-20 사용자 요청: GitHub #9~#15와 Drive jipdam_db의 ZIP을 확인하고 1번 HUG 및 추가 학원·도서관·어린이보호구역 자료를 DB에 합치기"
```

## 범위와 분리

이번 수입 배치는 HUG 전세보증 사고(#9), NEIS 학원(#13), 전국 도서관(#14), 어린이보호구역(#15) 네 출처다. 공시가격·병의원·약국·학교는 이 배치에 포함하지 않는다. 원본 ZIP과 패키지 파일은 ignored `data/collection/`에 보존한다.

전월세 canonical 거래 DB 및 rental serving DB는 수정하지 않는다. 서로 다른 `regional_statistic`/`facility` 사실을 별도 `team_reference.sqlite3`에 출처·배치·타입·원문 JSON·품질 상태와 함께 저장한다. 입력은 `team_collection_v1` 패키지의 검증된 정규화 JSONL이며 원본 파일은 manifest의 크기와 SHA-256으로 대사한다. `source_unverified` 상태를 그대로 보존한다. 이 적재는 품질 검수, 좌표 검수, 시설 매칭, 지도/추천 연결을 승인하거나 수행하지 않는다.

## TEAM-REF-001-REQ-01 입력 계보 및 패키지 검증

### TEAM-REF-001-AC-01 ZIP 해시가 Issue #9/#13/#14/#15와 일치하고 CRC·manifest·모든 manifest 파일 크기/hash가 통과한다.

## TEAM-REF-001-REQ-02 통합 행 대사

### TEAM-REF-001-AC-02 출처·배치·record type 및 normalized JSONL 건수가 일치한다. 저장 accepted 행은 HUG 828, 학원 138,523, 도서관 3,597, 어린이보호구역 14,654로 총 157,602건이고 학원 rejected 1건도 상태와 함께 보존한다.

## TEAM-REF-001-REQ-03 별도 DB와 품질 상태

### TEAM-REF-001-AC-03 DB는 별도 파일로 생성되고 SQLite integrity/FK 검사를 통과하며 각 레코드가 source/batch/record type/`source_unverified` 및 payload를 보존한다.

## TEAM-REF-001-REQ-04 기존 서비스 데이터 격리

### TEAM-REF-001-AC-04 기존 canonical/serving DB, 미검수 품질 상태, 좌표·시설 매칭·추천 보류 경계를 보존한다. 기존 출력 DB를 덮어쓰지 않는다.

실제 수입 증거는 [TASK-TEAM-REF-001](../tasks/team-reference-import-20261020.md)에 기록한다.
