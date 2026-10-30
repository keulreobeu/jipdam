# TASK-WIKI-RECOVERY-001 — 공유 위키 검토 대기 복구

```toml
kind = "task"
id = "TASK-WIKI-RECOVERY-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/25_wiki_lifecycle_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/jipdam_harness/wiki.py", "outputs/budongi_mvp_temp/src/jipdam_harness/wiki_cli.py", "outputs/budongi_mvp_temp/tests/test_wiki_lifecycle.py", "outputs/budongi_mvp_temp/docs/specs/25_wiki_lifecycle_spec.md", "outputs/budongi_mvp_temp/docs/wiki/AUTOMATION.md", "outputs/budongi_mvp_temp/docs/wiki/pages/WIKI-5BA57A2BFC7C9BCA.md", "outputs/budongi_mvp_temp/docs/wiki/pages/WIKI-E162D573DBB6F1CD.md", "outputs/budongi_mvp_temp/docs/tasks/wiki-review-recovery-20261028.md", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/docs/tasks/current.md"]
acs = ["WIKI-001-AC-03", "WIKI-001-AC-04"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py (project .venv, workspace TEMP, loopback enabled)"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/wiki-review-recovery-20261028.md#최종-검증"
acs = ["WIKI-001-AC-03", "WIKI-001-AC-04"]
```

- [x] WIKI-001-AC-03 검토 대기 복구와 수동 변경·이력·근거 보존
- [x] WIKI-001-AC-04 복구 CLI, 동기화 receipt 및 전체 환경 회귀

Jira: [KAN-26](https://kwulreobeu.atlassian.net/browse/KAN-26). 변경된 근거를 가진 공유 위키는 검토 대기로 유지하며 문서 ID·원격 수동 내용·이력·근거 해시와 충돌 검사를 보존한다. 안전하게 검증된 공유 문서를 재가져온 뒤 이전 import 검토 항목이 영구 대기에 남는지 재현하고, 정상 복구 경로와 실패·재시작 회귀를 검증한다. 실제 검토되지 않은 문서를 자동 승인하거나 외부 문서를 덮어쓰지 않는다. 현재 실제 review 항목과 전체 Jira 목표는 별도 검증이 끝날 때까지 열린 상태다.


2026-10-28 재현: 팀원 checkout에서 공유 문서의 근거 해시가 변경되면 import를 거부하고 review 대기를 만든다. 원래 검증된 바이트를 되돌려 재시작하면 정상 import되지만 기존 대기가 남는 것을 회귀 테스트의 수정 전 실패로 확인했다. 변경 후 정상 import와 같은 트랜잭션에서 정확히 같은 파일/사유의 import review만 완료 및 파일 해시·revision receipt를 기록한다. 다른 사유의 review는 남기며 변경된 근거는 계속 import 거부한다.

Python 시스템 환경의 전체 wiki 테스트는 `cryptography` 미설치로 27개 중 1 오류였다. 프로젝트 `.venv`와 workspace TEMP를 사용한 동일 테스트 27개는 통과했다. 실제 `WIKI-E162D573DBB6F1CD`는 여전히 변경된 근거를 검토해야 하므로 이 변경으로 자동 복구되거나 원격에 반영되지 않는다. 변경된 근거를 명시적으로 검토한 후 안전하게 재가져오는 전체 경로와 실제 대기 복구는 계속 미완료다.

프로젝트 `.venv`·workspace TEMP 및 로컬 소켓 허용으로 `scripts/verify_environment.py` 전체 제품/팀 검사와 합성 CLI smoke가 종료 코드 0으로 통과했다. `scripts/check_sdd.py --base origin/main`은 22 features / 109 AC / 51 tasks로 통과했고 `git diff --check`도 통과했다. 이 검증은 실제 변경 근거에 대한 수동 리뷰나 원격 위키 복구가 아니다.

위키 maintenance/catalog/search와 부분 검증 이벤트 `KAN26-VERIFIED-IMPORT-20261028`은 SKIP/execution_log/DONE/nonblocking이며 [Jira 기록](https://kwulreobeu.atlassian.net/browse/KAN-26?focusedCommentId=10121)의 receipt는 DONE이다. 전체 Task는 미완료다.


후속 작업 중간 기록: 변경된 근거의 명시적 검토를 위한 `wiki review-shared --request` 초안을 구현했다. 검토자·근거/의미 검토·catalog hash·원본 파일 hash·기존 revision 및 새 source hash를 확인하고 원본 문서 ID/기존 revision을 보존한다. 내보내기 실패 시 ACTIVE 검색을 막고 review를 유지하며, 재시도 성공 후 대기를 처리하는 합성 테스트를 포함해 위키 테스트 28개가 통과했다. 이 변경은 아직 추가 보안 검토·전체 회귀·운영 문서·실제 원격과의 충돌 검증을 끝내지 않았으므로 실제 공유 문서에 적용하지 않았고 KAN-26은 진행 중이다.


2026-10-28 후속 구현: `wiki review-shared`는 기존 공유 문서 본문 무결성·ID/revision·현재 파일 해시, 명시된 검토자/근거·의미 검토·catalog hash, 동일 문서 범위와 갱신된 근거 해시를 확인한다. 이전 revision 및 검토 요청(사유와 근거 해시 포함)을 이력에 보존한다. export 실패 시 ACTIVE 검색과 review 완료를 보류하고 성공적인 재시도 후 해당 review만 해소한다. 고위험 소유자 승인과 원격 outbox 보류를 유지하며 원격 전송 완료를 추정하지 않는다. 운영 문서와 Spec에 반영했다.

검증: `.venv` 위키 테스트 30개 통과(거부 조건, 내보내기 실패/재시도, CLI 원격 대기, 고위험 승인 포함); SDD와 diff whitespace 통과. 전체 환경 첫 실행은 제품 326개 중 수집 DB 디렉터리 rename `WinError 5` 1오류였고 해당 단독 재실행은 통과했다. 동일 전체 환경 재실행은 당시 제품 326개·팀 35개·합성 CLI 통과했다. 실행 시작 후 추가한 고위험 위키 테스트는 별도 30개 위키 묶음에서 통과했다. 실제 WIKI-E162D573DBB6F1CD의 원격 표와 로컬 근거의 합산 리뷰·적용 및 전체 Task 완료는 아직 하지 않았다.


위키 maintenance/catalog/search 후 운영 안내 `WIKI-5BA57A2BFC7C9BCA`를 동일 ID revision 4로 UPDATE했다. 로컬 Markdown과 source 검증은 완료했으나 Confluence outbox는 `SYNC_PENDING`/blocking이다. 원격 기존 문서 65959 revision 2를 읽어 기존 내용을 확인했지만 로컬 binding의 remote_version/hash가 없으므로 수동 변경을 덮어쓰지 않았다. 원격 이력의 안전한 연결·read-back receipt가 필요하다. 이벤트 `KAN26-WIKI-GUIDE-20261028`의 [Jira 기록](https://kwulreobeu.atlassian.net/browse/KAN-26?focusedCommentId=10125)은 receipt DONE이며 원격 위키 receipt가 아니다. 실제 카탈로그 문서 `WIKI-E162D573DBB6F1CD` review도 남아 KAN-26은 진행 중이다.


## 기존 원격 기준점 연결과 운영 안내 동기화 — 2026-10-28

기존 문서의 실제 read-back·stable ID·원격 버전/해시 및 담당자의 수동 내용/의미 검토를 근거로 연결만 수행하는 `wiki bind-existing`을 추가했다. 정확한 delivery/revision·catalog·readback 파일·호스트·문서 ID를 확인하며 기존 다른 binding은 덮어쓰지 않는다. 연결과 원격 전송 완료를 구분하고 검토 요청을 이력에 기록한다. 위키 테스트 31개, `check_sdd.py --base origin/main`, `git diff --check`, 프로젝트 전체 환경 검사 및 합성 CLI가 통과했다.

기존 운영 안내 Confluence 65959의 공개 revision 2와 편집 초안 내용이 동일했고 이전 로컬 revision 2의 모든 절·source hash를 포함함을 확인했다. 실제 read-back 해시 `d410f19f3dacd4cbd528f26d8fe586303c888176ef65da36028b33c492d827b3`로 기준 binding을 설정했다. 갱신 직전 공개 버전/본문·초안 snapshot을 재확인하고 기존 노드를 유지하며 검증된 운영 변경 부분만 수정했다. 공개 read-back revision 3, 실제 HTML 해시 `27ee4a77530dd60ca9ec1ae31e2b430259d8a8502324b21f77f8adcaff2c4361`, 변경하지 않은 5개 본문 노드와 문서 ID·새 절차·원본 해시를 대조했다. [원격 문서](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/65959/WIKI-5BA57A2BFC7C9BCA), 이벤트 `KAN26-REMOTE-BASELINE-GUIDE-20261028` UPDATE/DONE/nonblocking, 위키 및 [Jira](https://kwulreobeu.atlassian.net/browse/KAN-26?focusedCommentId=10126) 실제 receipt DONE. 기존 데이터 카탈로그 review는 별도이고 아직 미완료다.


## 데이터 카탈로그 검토 복구 — 2026-10-28

변경된 legal Task와 기존 카탈로그·validation을 검토하고 10월 13일 백업 복원, 10월 20일 검수 serving의 현 PC 미확보, 과거 법령 판본/권리 재확인을 명시했다. `review-shared`로 같은 `WIKI-E162D573DBB6F1CD` revision 2를 복구하고 6개 현재 근거 해시 및 담당자 검토 이력을 보존했다. 원격 문서의 stable ID가 본문 대신 제목에 있는 사례는 공식 read-back 제목이 정확히 `[ID] 제목`으로 일치할 때도 연결되도록 보완했고 잘못된 제목 거부 회귀를 확인했다.

공식 Confluence 589825 공개 revision 1과 편집 초안 본문을 비교해 기존 수동 표를 확인하고 원격 기준점 hash `b40fc1e646299088546f0623c01404bea7765a4cb33456a31c8c2db1a9166a27`를 연결했다. 기존 표를 유지하고 현 PC의 복원·미확보·판본 확인 상태와 근거만 추가했다. 공개 read-back revision 2에서 표 28개 셀 텍스트·local ID 전부 동일, 실제 HTML SHA-256 `c2b0c6b79c3eedd69b8cb37b84738ec85fa0b06944c14fb7951391de729aea01`, 위키 receipt DONE. [원격 문서](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/589825/WIKI-E162D573DBB6F1CD), [Jira 기록](https://kwulreobeu.atlassian.net/browse/KAN-26?focusedCommentId=10127). 과거 검수 수치는 현 PC의 재측정이 아니며, 법령 현행 효력이나 권리 검수 완료를 뜻하지 않는다.

## 제목 기반 식별과 최신 회귀 결과 — 2026-10-28

운영 안내 WIKI-5BA57A2BFC7C9BCA 로컬 revision 8을 갱신하고 Confluence 65959 공개 revision 4를 실제 read-back했다. 변경 범위 밖 본문 5개 노드를 보존했으며 HTML SHA-256은 `11f9417bb3487542675ebf382e0f050cb638feca8dc41af31d56f1011d572edd`다. 이벤트 KAN26-TITLE-ID-GUIDE-20261028은 UPDATE/DONE/nonblocking이며 위키와 [Jira](https://kwulreobeu.atlassian.net/browse/KAN-26?focusedCommentId=10128) receipt 모두 DONE이다.

제목 기반 식별 추가 후 위키 32개 테스트와 SDD는 통과했다. 최신 전체 환경 검사는 제품 329개 중 디렉터리 rename에서 Windows `WinError 5` 2건으로 실패했고, 관련 모듈 9개 재실행에서도 같은 유형 1건이 발생했다. 이전 전체 환경 통과는 이 최신 변경에 대한 전체 통과를 뜻하지 않는다. 확인한 두 경로는 SQLite 연결을 닫은 후 rename을 시도하지만 접근 거부의 구체적 원인은 아직 확인되지 않았다. 전체 검증을 통과할 때까지 KAN-26은 진행 중이다.
별도 workspace TEMP에서도 `test_file_canonical.py` 9개 중 1개가 canonical 디렉터리 rename의 동일한 WinError 5로 실패했다. 임시 경로 변경만으로는 해결되지 않았으며 원인은 계속 조사 대상이다.

## 최종 검증

2026-10-28 KAN-27의 Windows 게시 재시도 보완 후 `.venv`·workspace TEMP·로컬 루프백에서 `scripts/verify_environment.py`는 제품 전체 테스트, 팀 테스트 35개 및 모델 없는 합성 CLI를 모두 통과했다. SDD 22 features/109 AC/52 tasks 및 `git diff --check`도 통과했다. 위키 검토 복구의 실제 Confluence read-back과 Jira receipt는 위 각 기록에 보존하며 원격 대기 항목은 없다. 이 결과는 10월 20일 검수 serving DB의 실자료 복구를 뜻하지 않는다. 간헐적 Windows 접근 거부의 잠금 주체는 KAN-27에서 계속 조사한다.
