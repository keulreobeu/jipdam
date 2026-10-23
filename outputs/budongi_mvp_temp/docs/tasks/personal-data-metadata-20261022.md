# TASK-PERSONAL-METADATA-001 — 본인 수집 데이터 메타데이터

```toml
kind = "task"
id = "TASK-PERSONAL-METADATA-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/26_data_catalog_spec.md"]
scope = ["outputs/budongi_mvp_temp/docs/tasks/personal-data-metadata-20261022.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json", ".gitignore"]
acs = ["DATA-CATALOG-001-AC-01", "DATA-CATALOG-001-AC-02", "DATA-CATALOG-001-AC-03"]

[[verification]]
command = "원본/통계DB 대사, XLSX 전체 값 및 비율 15474개 독립 대사, 4시트 렌더 및 SDD 검사"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/personal-data-metadata-20261022.md#산출물과-검증"
acs = ["DATA-CATALOG-001-AC-01", "DATA-CATALOG-001-AC-02", "DATA-CATALOG-001-AC-03"]
```

Jira: [KAN-21](https://kwulreobeu.atlassian.net/browse/KAN-21). 담당 실행: Codex. 2026-10-22.

요청: 본인 수집/제공 자료만 사용자 지정 4시트 Excel로 정리한다. 팀원/합성·가공 복제본을 신규 수집으로 세지 않는다.
관련 계약: MOLIT-001, STATS-001, LEGAL-CORPUS-001, COLLECT-001, ADR-007.

완료 기준:
- [x] DATA-CATALOG-001-AC-01 본인 수집 출처·배치·범위·현재 접근 여부를 확인하고 실측과 이력 건수를 구분했다.
- [x] DATA-CATALOG-001-AC-02 활용 목적·행단위·단위·중복/JOIN 제한을 표시했다.
- [x] DATA-CATALOG-001-AC-03 기준일·원본 위치·수집 기록과 검증 근거를 연결했다.
- 본인 귀속 및 원본/manifest/수집 이력 근거를 보존한다.
- 데이터셋과 컬럼을 전수 기술하고 실측값과 이력값/미확인을 구별한다.
- NULL/의미상 결측, 중복 분모, 단위, 행단위, JOIN 검증 여부를 명시한다.
- 4시트 XLSX를 생성하고 내용·계산·시각 검증을 수행한다.

원본은 읽기 전용. 새 수집·키 조회·원본 수정·추천 연결 없음. 실제 데이터는 GMS에 보내지 않는다.

## 산출물과 검증

- 산출물: `outputs/personal_metadata_20261022_01a162be/이진호_수집데이터_메타데이터_20261022.xlsx` (실제 대표값이 있어 Git 제외).
- 데이터셋/배치 목록 48행, 컬럼 메타데이터 3,918행, 품질/연계 48행, 이슈 27행. 팀원·합성·가공 DB·파생문/재포장 ZIP을 독립 수집으로 세지 않았다.
- 실제 원본: 기존 #5 XML 384,211행 및 최근 재조회 XML 248,075행, 정상 사용자 CSV 4개, 통계 원본 30개, 법령/기관 원문과 연혁 목록. 배치·서비스·CSV 간 중복을 합산하지 않는다.
- 기존 통계 공유 ZIP SHA-256 `83f0e40ac834bcb5a468fa51243913e7d73fc87d7d8eb15d279cca27dcdc32e1` 대조. 30개 원본 SHA 일치, 날짜셀 530,556 = 수치483,979 + 결측46,577을 원본/DB와 대사했다.
- XML은 각 query manifest 페이지 SHA/건수 전수 대조. 문서는 active manifest 원본 파일의 bytes/SHA를 대조했다. 손상 CSV 1개는 정상 행 통계에서 제외하고 NUL12,776,478바이트를 기록했다.
- 4시트 렌더 확인. 저장 XLSX의 전체 하드코딩 값/오류 셀 검사, 15,474개 비율 수식을 독립 계산과 대사, 테이블/고정창/ZIP CRC 확인. 실제 Excel 앱 실행은 하지 않았다.
- XLSX SHA-256: `b0e8eac9fe9c4acd7baac5dd0f1a09fe36a38b65f6bb542ec74786e7597e1130`.
- GMS 우선 초안 요청은 선택 키/예산 runner에서 로컬 credentials 서버 연결 불가로 blocked. 우회 호출/실데이터 전송 없이 로컬 작성·검증했다.

## 한계

M005~M007(2024-01~2026-08 확장 배치)은 완료 기록의 총수만 확인했다. 현재 PC에 원본 배치가 없어 컬럼 목록·NULL/고유값·파일 수를 추정하지 않고 미확인으로 남겼다. 전체 수집분의 모든 컬럼을 재측정했다고 주장하지 않는다. JOIN 성공률과 미연결건수는 이번 작업에서 실증하지 않았다.

## 위키 판단

정책상 자동 생성 가능한 상세 참조표의 스냅샷이므로 별도 위키 생성은 `SKIP/generated_reference`. 기존 데이터군 안내 `WIKI-E162D573DBB6F1CD` 및 지정 Confluence의 현행 페이지 589825를 검색해 확인했다. 본 Excel은 시점별 실측표로 보관하며 원본/DB/내부 runtime을 게시하지 않는다.

위키 이벤트 `TASK-PERSONAL-METADATA-001-VERIFIED-20261022`: SKIP/generated_reference, execution=DONE, blocking=false. Jira 결과 댓글 `10078`에 판단·근거·링크·한계를 기록했다. SDD features22/AC109/tasks45 및 대상 문서 diff whitespace 검사 통과.

상태: 메타데이터 산출물 검증 완료. 원본 미확보/미검증 JOIN은 산출물에 명시된 데이터 준비 이슈로 유지한다.
