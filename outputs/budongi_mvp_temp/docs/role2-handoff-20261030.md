# 2번 수집 인계 기록 — 2026-10-30 09:30 KST

[ROLE2-COLLECT-001](specs/27_role2_collection_spec.md) 작업을 새 세션이 이어받기 위한 기록이다. 키·원본·로그 내용은 넣지 않았다. 이 문서는 사실 기록이고, 확정 요구는 Spec, 결정 이유는 [ADR-025](adr/ADR-025-role2-collection-harness.md), 실행 단위는 [TASK-ROLE2-HARNESS-001](tasks/role2-collection-harness.md)·[TASK-ROLE2-COLLECT-001](tasks/role2-collection-run.md)을 따른다. 실행 증거는 [검증 기록](role2-collection-validation-20261029.md)에 남긴다.

## 1. 한눈에 보는 상태

| 영역 | 상태 |
|---|---|
| 거버넌스(승인문·Spec 27·ADR-025·Plan·Task 2·원장) | 완료, 커밋 `13bba6a` |
| W0 리드 코드(contract·base·_reuse·registry·filefetch·cli·credentials·secret_sweep·issues_net) | 완료, 테스트 15개 통과 |
| `tooling/role2_harness/`(role_guard·importer_oracle·ledger·merge_plan) | 완료, 루트 테스트 38개 통과, 수정 커밋 `148f1aa`·`33fb74c` |
| 외주 유닛 38개 테스트 감사 | **전부 Sonnet(claude-sonnet-5-5) 통과** |
| 외주 구현(agy gemini-3.8-flash) | **20/38 채택**, 2026-10-30 09:20에 안전 중지 |
| 1차 웨이브 예약 Issue | #42~#63(22건) 게시 완료(`gh`, 계정 cannedJean) |
| 원본 수집 | 키 없는 파일 10개 배치 raw 완료(49파일, 685.8MB), 패키징 전 |
| 나머지 | 리드 셸·어댑터 유닛·패키징·워크북·Issue 결과·키 레인 수집 미착수 |

브랜치는 `codex/role2-collection-20261029`(main `a7b1714` 기준)이다. 미커밋 변경 없음(이 인계 커밋 이후). push·merge는 하지 않았다.

## 2. 확정된 사용자 결정과 경계

2026-10-29 계획 승인(원문: `C:\Users\SSAFY\.claude\plans\c-users-ssafy-downloads-team-data-contr-purrfect-nautilus.md`, 저장소 밖):

1. 키 3종: data.go.kr·서울 열린데이터·생활안전지도(safemap). 사용자가 CRED-001 보관함에 등록했고 Claude는 credential ID만 쓴다. ID는 `src/budongi/team_collection/role2_sources.json`에 있다(datagokr `f1c6233d…`, seoul_open_data `25a5d5e2…`, safemap `ca4f8be2…`). 키 값은 수집기 프로세스 안에서만 읽는다.
2. #40(OA-394 주요공원)·#41(15099316 1~8호선 역 좌표)은 참조만 하고 재수집하지 않는다. 메타 `중복관계`에 표기한다.
3. 정적 데이터 우선 + 소량 실시간 표본: 버스 도착 약 300노선 × 하루 3회(07:30/12:30/18:30 KST) × 3일. 대기질은 파일 이력.
4. 담당 cannedJean, 데이터셋 ID 접두어 T(이슈 ID `T-I001~`). R·L 접두어는 제한/raw-only 출처용으로 이미 쓰고 있다.
5. 모델: Claude Code 중심 + agy 아웃소싱, **GMS 완전 제외**.
6. 공공누리3·4·비영리 출처: 원본+메타데이터만 공유하고 정리본은 보류.
7. 서울 열린데이터(:8088)·TOPIS(ws.bus.go.kr) HTTP 평문 키 전송 허용, 수집 후 키 재발급(사용자).

이후 대화의 추가 지시:

- 2026-10-29 "github cli 활용해서 이슈 생성하고 직접 진행해": 승인 계획의 "Issue는 초안만"을 대체한다. Claude가 `gh`로 `[수집]` Issue를 만들고 본문을 갱신한다. **Drive 업로드는 여전히 배치별 사용자 승인 후 사용자가 한다.**
- 2026-10-29 "감사 계획은 haiku 보다 더 좋은 모델을 사용해야해": 모든 계획의 감사자를 Sonnet으로 했다. 심판(triage)은 Haiku.
- 리드가 Opus라서 Opus 감사는 `role_guard` R2와 outsource의 `require_distinct`가 막는다(사용자에게 설명함).
- 승인 범위 밖(변경 없음): 좌표 변환 확정·지오코딩·단지 매칭·추천/serving 연결·DB 적재·Drive 업로드(배치별 승인)·push/merge. 모델에 키·원본·DB·로그·.env를 보내지 않는다.

## 3. 모델 운용 사실

| 모델(경로) | 사실 |
|---|---|
| gemini-3.8-flash (agy) | 주 계약자. 정상 시도 1회 3~6분. 2026-10-29 13:27 할당량 소진 후 리셋됨 |
| gemini-4-argon (agy) | 이 계정에서 계속 429 |
| gpt-oss-120b-medium (agy) | 2026-11-02 제거 예정 |
| Fable 5.1 (`claude -p`) | usage credits 필요해 사용 불가 → r2-hard는 claude:sonnet 대신 agy gemini(effort high)로 바꿨다 |
| Sonnet 5.5 (`claude -p`) | 전 계획 감사자 |
| Haiku 5.5 (`claude -p`) | 심판(triage). 감사는 하지 않는다 |

`role_guard.py` 규칙: R1 계약자 ≠ 리드 계열(Opus), agy 경유 Opus 금지 / R2 감사자는 Anthropic이고 리드·계약자 계열이 아님 / R3 심판은 셋과 모두 다름 / R5 agy 입력에 hidden·키·data·raw·logs·.local_runtime 금지, 작업 폴더는 저장소 밖 / `gpt-6*`(GMS) 금지. `verify-run`은 실행 후 실제 모델을 agy 로그 `model=`에서 읽어 대조한다(위반 0, 미확인 0 확인).

## 4. 외주 빌드 상태(2026-10-30 09:20 중지 시점)

계획 위치: `.local_runtime/role2/outsource/r2-*/plan.json`(설계 요약 `UNIT_CATALOG.md`). 모든 계획: lead opus, auditor sonnet, 계약자 `agy:gemini-3.8-flash`, max_attempts 3. r2-hard만 effort high 고정, 나머지 medium.

| 계획 | 채택 | 미채택 |
|---|---|---|
| r2-core | C1~C10 전부(통합 테스트 passed) | – |
| r2-edge | E1·E3·E4·E5·E11 | E2(needs_attention) |
| r2-xcheck | X2 | X1(needs_attention), X3(X1 대기로 blocked) |
| r2-pack | P1·P4·P7 | P3·P5·P6(needs_attention), P2·P9·P10·P11(중지로 running 표시), P12(pending) |
| r2-hard | – | H1~H8 pending(미시작) |

**미채택 원인(확인함):** X1·E2·P3·P5·P6 모두 agy가 6분 안에 산출물과 `DELIVERY.json`을 쓰고 `DONE`을 출력했지만 `agy.exe`가 종료되지 않았다. X1·E2·P3은 30분 timeout으로 죽어 산출물이 버려졌고, P5·P6은 밤사이(PC 절전 추정) timeout이 동작하지 않아 21:06~08:58 약 12시간 멈췄다(리드가 프로세스를 종료). 코드 결함이 아니라 agy 종료 문제이므로 재실행하면 된다.

**중지 처리:** 백그라운드 실행을 멈추고 이 작업의 `outsource.py`·`agy_task.py`·`agy.exe -p "# Work order …"` 프로세스만 종료했다(사용자의 다른 agy 세션은 건드리지 않음). `sweep_hidden`으로 run 폴더의 숨김 테스트 평문 사본 0건 확인. `outsource run`은 accepted가 아닌 유닛(running 포함)을 다시 실행하므로 상태 파일을 손볼 필요 없다. 각 계획의 `report.md`를 `status`로 갱신했다.

**재개 순서(권장):**
1. 긴 실행 전 keep-awake 요청. `-j`는 4 이하, PC 전체에서 outsource 계획 1개씩.
2. 멈춤 대비 timeout을 짧게: medium 계획 `--timeout 15`, r2-hard `--timeout 25`. 실행 중 30분 이상 새 로그가 없으면 해당 `agy.exe -p "# Work order <유닛>"` 프로세스만 종료.
3. 순서: r2-pack(남은 8개) → r2-xcheck(X1, X3) → r2-edge(E2) → r2-hard(8개).
4. 실패가 남으면 `role_guard outsource triage <plan> --unit <U> --referee haiku --contractor agy:gemini-3.8-flash` → 스펙 보강/재감사(Sonnet) → 재실행.
5. 전부 채택되면 `outsource.py integrate <plan> --dest outputs/budongi_mvp_temp/src --dry-run` → 확인 후 실제 integrate, 테스트는 `outputs/budongi_mvp_temp/tests/team_collection_tests/`로 옮긴다(별도 `--with-tests` 결과를 검토해 배치).

## 5. 수집 상태

예약 매핑: `.local_runtime/role2/reservations.json`(source_id → t_id·record_url·제목). 예약 팩과 보류 28건 사유표: `outputs/team-share/role2/reservations-wave1.md`.

**raw 완료 10배치**(`outputs/budongi_mvp_temp/data/collection/role2/<T>-1/`, 목록 `batches.json`, Issue 상태 "수집 중"):

| T | Issue | 원본 |
|---|---|---|
| T001 | #46 | KRIC 전체 도시철도역사정보 XLSX(20260630) |
| T002 | #47 | 9호선 2·3단계 좌표 CSV(20260131) |
| T004 | #49 | 침수흔적도 연도별 ZIP 14개(6.5MB) |
| T005 | #50 | 버스정류소 XLSX(20260902)+컬럼정의 |
| T006 | #51 | 노선별정류소 XLSX(20260902) |
| T007 | #52 | 노선ID XLSX(20260902)+컬럼정의 |
| T011 | #55 | AIR_HOUR 2020~2022 CSV(115.4MB) |
| R1 | #43 | 생활인구 ZIP 202508~202607 12개(542.9MB) |
| R2 | #44 | 승하차 CSV 202510~202609 12개(14.5MB) |
| T021 | #63 | 상권영역 ZIP(2.1MB) |

**예약만 된 12건:** #42 L1(AirKorea 측정소, data.go.kr 키), #45 R3(첫·막차, 서울 키), #48 T003(역사마스터, 서울 키), #53 T008·#54 T009(표준데이터, 페이징 경로 미구현), #56 T013·#57 T014·#58 T015·#59 T016·#60 T017(서울 API), #61 T019(민방위, data.go.kr), #62 T020(SEMAS 상가정보, 10/31 신판 POST 다운로드).

**보류 28건:** probe·결정·키 필요(사유표는 예약 팩). safemap 키가 이제 등록됐으므로 L2a~L2c는 "키 미보유"가 해소돼 GetCapabilities probe 단계다. 2차 웨이브 Issue는 아직 없다.

수집 규칙: 매 배치 전 GitHub `[수집]` Issue 재검색(겹침 확인) → record_url 바인딩된 출처만 `cli fetch-files`가 허용 → 결과·건수·ZIP SHA-256을 Issue에 기록한 뒤에만 업로드 준비.

## 6. 남은 작업(순서)

1. 외주 유닛 나머지 18개 완료·통합(§4).
2. 리드 셸 작성(Opus): `transport`·`supervisor`·`stage`·`package_build`·`profile_run`, cli 나머지(`stage`, `package`, `profile`, `issues draft`). 셸 검증은 Sonnet 블랙박스 테스트 목록 + Gemini 적대 테스트.
3. 어댑터 유닛 E6 classify·E7 seoul·E8 datagokr·E9 topis·E10 filedata·E12 wms: WF-0 도시에(`.local_runtime/role2/dossiers/g0*.json`, `critic.json`)로 작업지시·공개/숨김 테스트 작성 → `check --red` → Sonnet 감사 → agy 실행.
4. 필드 매핑(raw 도착분): 값 없는 헤더 형상만으로 A안(Gemini)·B안(Opus) 독립 작성 → 결정적 diff → 불일치는 `unmapped`+T-I 이슈.
5. 파일럿 T001·T002(+T003은 서울 키 수집 후) 패키징 → 12개 게이트·검사기 4종(builder·selfcheck+record_check·importer oracle·recount)·비밀 스윕 → go/no-go → 나머지 8배치. R1·R2는 raw-only, 95MB 이상은 `jipdam_zip_parts_v1` 분할.
6. 프로파일 → `outputs/team-share/role2/cannedJean_수집데이터_메타데이터_YYYYMMDD.xlsx`(4시트, 헤더 29/30/29/11열, 제목2·메모3·헤더5·데이터6행, 표 MetadataTable1..4, 틀 고정 C6) → 3중 검증(data_only 재읽기, X3 readback, Excel COM 재계산).
7. Issue 결과 본문(`gh issue edit`): 상태·완료/0건/실패 요청·건수·방법·mapping_version·ZIP명·전체/조각 SHA·조회 시각·manifest.
8. 키 레인 수집(예약 12건): 서울 :8088 → data.go.kr → TOPIS(하루 1,000회) → 도착 표본 3일. 상가정보는 10/31 이후.
9. 2차 웨이브: 보류 28건 probe·사용자 결정 → 예약 Issue.
10. 배치별 Drive 업로드 승인 요청 → 사용자가 업로드 → 파일 링크를 Issue·워크북에 기록.
11. 마무리: 검증 기록 AC-01~08 갱신, `scripts/check_sdd.py --base origin/main`, `scripts/verify_environment.py`, 로컬 커밋. 사용자에게 서울·TOPIS(data.go.kr) 키 재발급 안내.

## 7. 주의할 사실

- Python은 `.venv\Scripts\python.exe -X utf8`(openpyxl·cryptography는 venv에만 있음). PowerShell 5.1이라 `utf8NoBOM`·`&&`가 없다. 파일은 Python이나 Write 도구로 쓴다.
- 팀 importer는 미병합 백업 브랜치 blob `f84e2010c23ee7acf36a04155899ccce06bc77f0`(origin/codex/workspace-backup-20261023)를 `tooling/role2_harness/importer_oracle.py`가 로드한다. 팀원 ZIP은 한글 멤버명을 UTF-8 플래그 없이 저장한다(오라클이 재해석).
- 팀원 참조: `.local_runtime/role2/reference/std-library/STD_std-library-national-20261014-v1.zip`(SHA `1e15a13c…`), 양식 엑셀 3개와 계약 문서는 `C:\Users\SSAFY\Downloads\`(서지우·이진호·김성현 메타데이터 xlsx, `team-data-contract.md`, `team-collection-details.md`; 저장소 사본 `outputs/budongi_mvp_temp/docs/team-data-contract.md`·`team-collection-details.md`).
- 서울 버스는 TAGO에 없다 → TOPIS·서울 열린데이터만 쓴다.
- 판정 원장 `.local_runtime/role2/xval/verdicts.jsonl`(append-only 해시 체인, 현재 2건).
- 런타임 산출물(`.local_runtime/`, `data/collection/`, `outputs/team-share/`)은 Git에 넣지 않는다.
- 메모리의 "Issue는 초안만"은 §2의 gh 지시로 대체됐다.

## 8. 다음 세션 킥오프 프롬프트

새 세션(작업 폴더 `C:\Users\SSAFY\Desktop\jipdam`)에 그대로 붙여 넣는다.

```text
너는 집담 프로젝트에서 팀 2번(재난·대중교통·생활 인프라) 데이터 수집을 맡은 cannedJean의 리드 엔지니어다(Claude Code Opus 리드). 이전 세션이 2026-10-30 09:20 KST에 작업을 안전하게 중지하고 인계했다. 그 지점부터 이어서 진행해.

먼저 읽기(순서대로):
1. outputs/budongi_mvp_temp/docs/role2-handoff-20261030.md — 현재 상태·결정·재개 절차의 기준 문서
2. AGENTS.md, outputs/budongi_mvp_temp/AGENTS.md의 "2026-10-29 2번 … 수집 한정 승인" 문단
3. outputs/budongi_mvp_temp/docs/specs/27_role2_collection_spec.md, docs/adr/ADR-025-role2-collection-harness.md, docs/plans/role2-collection.md, docs/tasks/role2-collection-harness.md, docs/tasks/role2-collection-run.md, docs/role2-collection-validation-20261029.md
4. 승인된 상세 계획(저장소 밖): C:\Users\SSAFY\.claude\plans\c-users-ssafy-downloads-team-data-contr-purrfect-nautilus.md — §4 런타임, §5 패키징 12게이트, §6 워크북, §7 유닛 구성, §9 웨이브 표
5. .local_runtime/role2/outsource/UNIT_CATALOG.md와 각 r2-*/report.md

지켜야 할 경계:
- 브랜치 codex/role2-collection-20261029에서 검증 후 로컬 커밋만. push·merge·amend·reset 금지.
- GMS 사용 금지. 코드는 Claude Code 중심 + agy 아웃소싱. 모든 outsource/agy 호출은 tooling/role2_harness/role_guard.py를 거친다(계약자 agy:gemini-3.8-flash, 감사 sonnet, 심판 haiku; Opus 감사는 리드와 같은 계열이라 불가).
- 모델(agy·claude -p 포함)에 키·원본·DB·로그·.env·숨김 테스트를 보내지 않는다. 키는 role2_sources.json의 credential ID로 수집기 프로세스 안에서만 읽는다.
- 수집은 role2_sources.json에 approved이고 [수집] Issue가 예약된 범위만. 매 배치 전 GitHub Issue 재검색. Issue 생성·본문 갱신은 gh(계정 cannedJean)로 직접 한다. Drive 업로드는 배치 목록을 내가 채팅으로 승인한 뒤 내가 한다.
- 좌표 변환 확정·지오코딩·단지 매칭·추천/serving 연결·DB 적재 금지. #40·#41 재수집 금지. 원본·ZIP·DB·워크북은 Git에 넣지 않는다.
- Python은 .venv\Scripts\python.exe -X utf8. 셸은 Windows PowerShell 5.1.

바로 할 일:
1. 상태 확인: git log -3, 각 계획 status(outsource.py status), 남은 agy 프로세스 없는지.
2. 긴 실행 전 keep-awake를 요청하고, outsource를 백그라운드로 재개: r2-pack → r2-xcheck → r2-edge(E2) → r2-hard. medium 계획은 --timeout 15, r2-hard는 --timeout 25, -j 4 이하, 한 번에 계획 1개. 실행 후 role_guard verify-run으로 위반 0·미확인 0 확인.
3. agy가 DONE 후 종료하지 않는 문제가 있다: 30분 넘게 로그가 멈춘 유닛은 그 `agy.exe -p "# Work order <유닛>"` 프로세스만 종료한다. 다른 agy 세션은 사용자 것이니 건드리지 마.
4. 실패가 남으면 haiku triage → 스펙 보강 → sonnet 재감사 → 재실행. 전부 채택되면 integrate --dry-run 후 통합하고 제품 테스트(team_collection_tests)와 루트 tests/test_role2_*를 돌린다.
5. 그다음 인계 기록 §6 순서대로: 리드 셸(transport·supervisor·stage·package_build·profile_run) → 어댑터 유닛 E6~E10·E12 → 매핑 A/B → 파일럿 패키징(T001·T002) go/no-go → 나머지 배치 → 워크북 → Issue 결과 본문 → 키 레인 수집 → 2차 웨이브.

진행 방식:
- 각 단계 결과를 검증 기록(role2-collection-validation-20261029.md)에 사실대로 남기고, 확인하지 않은 것은 완료로 쓰지 않는다.
- 사용자 결정이 필요한 것(보류 28건의 범위·라이선스·새 키, Drive 업로드 승인)만 묻고 나머지는 판단해서 진행한다.
- 진행 상황을 물으면 단계별 채택 수·남은 일·예상 시간을 한국어로 짧게 답한다.
```
