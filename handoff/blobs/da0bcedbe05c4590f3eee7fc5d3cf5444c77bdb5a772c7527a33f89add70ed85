# TASK-META-INTEGRATE-001 — 팀 통합 메타데이터와 DB/PK 설계

```toml
kind = "task"
id = "TASK-META-INTEGRATE-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/31_metadata_integration_spec.md"]
scope = [".gitignore", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/docs/specs/31_metadata_integration_spec.md", "outputs/budongi_mvp_temp/docs/tasks/metadata-integration-20261030.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/plans/metadata-integration-20261030.md", "outputs/budongi_mvp_temp/docs/adr/ADR-028-apartment-identity.md", "outputs/budongi_mvp_temp/docs/metadata-db-design.md", "outputs/budongi_mvp_temp/docs/wiki/pages/"]
acs = ["META-INTEGRATE-001-AC-01", "META-INTEGRATE-001-AC-02", "META-INTEGRATE-001-AC-03", "META-INTEGRATE-001-AC-04"]

[[verification]]
command = "bundled Python -X utf8 .local_runtime/kan32_validate.py; artifact-tool inspect/render 22 sheets"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/metadata-integration-20261030.md#2026-11-02-재개검증"
acs = ["META-INTEGRATE-001-AC-01"]

[[verification]]
command = "official Atlassian getJiraIssue KAN-33 through KAN-38: assignee, scope, criteria and status read-back"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/metadata-integration-20261030.md#2026-11-02-재개검증"
acs = ["META-INTEGRATE-001-AC-02"]

[[verification]]
command = "catalog 75 item mapping and DB key design review; official building HUB and API documentation read-back"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/metadata-integration-20261030.md#2026-11-02-재개검증"
acs = ["META-INTEGRATE-001-AC-03"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py --base origin/main (KAN-32 isolated staging); Confluence 3178498 v1 full read-back"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/metadata-integration-20261030.md#2026-11-02-재개검증"
acs = ["META-INTEGRATE-001-AC-04"]
```

Jira [KAN-32](https://kwulreobeu.atlassian.net/browse/KAN-32) / agent-codex / 진행 중. 이번 작업은 문서·워크북·팀별 검증 이슈 등록이며 실제 팀원 검증/관계 확정/DB 모델 구현은 후속이다.

## 완료 기준

- [x] META-INTEGRATE-001-AC-01 원문·75개 항목·컬럼·품질·이슈·보충 보존과 워크북 검증
- [x] META-INTEGRATE-001-AC-02 네 수집자의 명시적 검증 업무/Jira 배정
- [x] META-INTEGRATE-001-AC-03 단지/동/호/대장 분리와 전 항목 DB/테이블/PK안
- [x] META-INTEGRATE-001-AC-04 인계·SDD·위키·게시 상태

## 현재 결정

수집자 기재 상태는 원문으로 유지하며 이번 작업이 실데이터를 재측정했다고 표시하지 않는다. 파일 namespace는 lee/seo/kim/lsj다. 표제부는 대장 앵커 후보, 내부 단지 마스터와 기존 canonical source ID는 별개다. 원본 파일·DB는 변경하지 않는다.

KAN-28은 별도 진행 중이다. 사용자는 2026-10-29 통계 전체 worker 시간 20% 단축, 다른 세 유형의 지정 범위 시간과 네 유형의 최대 관측 RSS 10% 이내 회귀, 완전 동일 결과를 승인했다. 재승인 질문을 반복하지 않는다. 목표 평가의 승인 범위/기준선 고정 보강 후 계약 테스트 19개 통과. 최종 5회 성능·전체 출력 재검증과 위키 최신 반영은 계속 추적한다.

## 검증

실제 실행 결과를 여기에 추가한다. 후속 이슈는 데이터 소유자가 증거를 제출할 때까지 열린 상태로 유지한다.

## 2026-11-02 재개·검증

사용자가 원본 네 워크북을 현재 PC Downloads에 다시 제공했다. 원본은 읽기 전용으로 처리했고 통합본은 Git 제외 `outputs/metadata-integration-20261030-kan32/집담_4인_통합메타데이터_KAN32.xlsx`에 작성했다. 부속 `source-cell-ledger.json`, `catalog.json`, `validation.json`과 22개 시트의 렌더는 같은 로컬 폴더에 보존한다. 엑셀/원문 셀 원장은 Git·GMS/외부 CLI 모델 문맥에 넣지 않는다.

| namespace | 담당자 | 원본 SHA-256 | 등록항목 |
| --- | --- | --- | ---: |
| lee | 이진호 | b0e8eac9fe9c4acd7baac5dd0f1a09fe36a38b65f6bb542ec74786e7597e1130 | 48 |
| seo | 서지우 | d0a45fe5370323ee31012d5509dc9fca01c396dd877d454f595232df262a795f | 11 |
| kim | 김성현 | a9c613145ca302a2543524138ac3d2f31a75851993522990aac74a033a1cabd7 | 7 |
| lsj | 이성진 | f44fdcb495f5616db0c742d1c2637897a9e10773b3b3ce6e085b4237f1f0362e | 9 |

중단 원인은 원문 숫자를 float로 읽고 다시 XLSX 숫자로 내보내면서 표현/정밀도가 달라진 경로였다. 이번 통합본은 원문 16개 시트의 XML 값 표현을 텍스트로 보존하며 수식도 실행하지 않는 텍스트다. 명시적인 메타데이터 요약 수치(등록 수)는 별도 숫자형이다. source sheet·셀 좌표·원래 XML 타입·값을 원장에 기록해 표시 형식과 원문을 구별한다. 숫자형 대장키 최대값/PNU 최소·최대값 3셀은 정밀도검수 시트에 표시했다. 이는 원문 보존 조치이며 이미 손실됐을 수 있는 식별자 복원이나 키 검증 완료가 아니다.

독립 ZIP/XML 파서로 출력과 입력의 비어 있지 않은 138,653셀을 전수 대조해 불일치0, namespace ID75개/고유75개, 원본4파일 SHA 불변, 출력 실제 수식0을 확인했다. ID 없는 설명·보충 셀도 원문 위치에 남겼다. artifact-tool의 수식 오류 검색은0건이며 22개 시트 렌더를 확인했다. 실제 원천 DB/자료의 품질을 재측정한 결과로 표시하지 않는다.

공식 Jira read-back에서 KAN-33/이진호, KAN-34/서지우, KAN-35/김성현, KAN-36/이성진의 실배정과 범위·제출물·AC를 확인했다. KAN-37/김성현과 KAN-38/이진호도 기존 후속 이슈로 확인했다. 여섯 이슈 모두 해야 할 일 상태를 유지했으며 이 작업에서 실행하거나 종료하지 않았다.

건축HUB의 대장 종류1/2/3/4 및 공식 API의 PK 전환 안내를 2026-11-02 다시 확인했다. [공식 건축HUB](https://www.hub.go.kr/portal/opn/tyb/idx-bdrg.do), [공식 API 설명](https://www.data.go.kr/data/15134735/openapi.do?recommendDataYn=Y). 통합목록 75개 모두 제안 테이블·PK·grain과 원문 PK/JOIN/CRS·출처 위치를 구분했다. DB 생성·실제 관계 승격은 실행하지 않았다.

통합본 최종 SHA-256은 `58ce841d685a985a5bb196376dc53ead108210dc9553dec1dae8ea9768baf98d`다. `C:/Users/SSAFY/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8 .local_runtime/kan32_validate.py`를 실행해 위 XML 대사 결과를 확인했다. 22개 렌더의 전체 구성과 통합현황/목록/정밀도검수의 상세 가독성을 확인했다. 원문 수식을 실행하는 계산 워크북이 아니므로 실제 Excel 수식 재계산 완료로 주장하지 않는다.

위키 판단은 CREATE다. 지정 공간의 `메타데이터 OR KAN-32` CQL 검색 결과3개(시설 벤치마크, 파이프라인 CLI, 위키 정책)는 이번 출처별 키 설계/책임 분담과 다른 주제임을 확인했다. 기존 로컬 ACTIVE 페이지와도 대조했다. [통합 메타데이터·DB키 설계 위키](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/3178498) ID3178498/version1, 생성시각2026-11-02T00:34:11.844Z를 공식 연결로 full read-back 확인했다. 입력 파일·실데이터 예시는 업로드하지 않았다. 과거 PC의 wiki/Git 상태를 복원했다는 뜻은 아니다.

Git 전담 agent는 최신 main `a7061a6`을 기준으로 관리 CLI를 통해 `codex/metadata-integration-kan32`와 별도 publisher를 만들었다. main 기반 current/traceability에 KAN-32만 추가하며 다른 백업 계약과 KAN-31 source 변경을 보존한다. 이번 게시 대상은 KAN-32의 정확8개 문서/설정뿐이다. 스냅샷·최종 검증·PR·CI/병합은 실제 영수증에 따라 별도 기록한다.
