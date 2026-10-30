# TASK-OBS-001 — 관측성 v2.3 적용

```toml
kind = "task"
id = "TASK-OBS-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/28_observability_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/jipdam_harness/execution.py", "outputs/budongi_mvp_temp/src/jipdam_harness/orchestrator.py", "outputs/budongi_mvp_temp/src/jipdam_harness/managed.py", "outputs/budongi_mvp_temp/src/jipdam_harness/managed_cli.py", "outputs/budongi_mvp_temp/src/jipdam_harness/observability.py", "outputs/budongi_mvp_temp/src/jipdam_harness/metrics_cli.py", "outputs/budongi_mvp_temp/tests/test_observability.py", "outputs/budongi_mvp_temp/docs/specs/28_observability_spec.md", "outputs/budongi_mvp_temp/docs/adr/ADR-026-observability.md", "outputs/budongi_mvp_temp/docs/plans/observability.md", "outputs/budongi_mvp_temp/docs/tasks/observability.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/harness/OBSERVABILITY.md", "outputs/budongi_mvp_temp/docs/wiki/pages/", "docs/sdd/traceability.json"]
acs = ["OBS-001-AC-01", "OBS-001-AC-02", "OBS-001-AC-03", "OBS-001-AC-04"]

[[verification]]
command = "python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_observability.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/observability.md#검증"
acs = ["OBS-001-AC-01", "OBS-001-AC-02", "OBS-001-AC-03", "OBS-001-AC-04"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/observability.md#검증"
acs = ["OBS-001-AC-04"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py (source checkout)"
result = "failed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/observability.md#검증"
acs = ["OBS-001-AC-04"]

[[verification]]
command = "python -m harness git verify --task TASK-OBS-001 (isolated publisher, snapshot 0001-9b66e5d5a3d2)"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/observability.md#격리-후보-검증"
acs = ["OBS-001-AC-01", "OBS-001-AC-02", "OBS-001-AC-03", "OBS-001-AC-04"]

[[verification]]
command = "python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_observability.py -k idle_pause (before correction)"
result = "failed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/observability.md#자동-리뷰-후속-수정"
acs = ["OBS-001-AC-02", "OBS-001-AC-03"]

[[verification]]
command = "python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_observability.py -k serialized (before serialization)"
result = "failed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/observability.md#자동-리뷰-후속-수정"
acs = ["OBS-001-AC-02"]

[[verification]]
command = "python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_observability.py; python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_managed_harness.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/observability.md#자동-리뷰-후속-수정"
acs = ["OBS-001-AC-01", "OBS-001-AC-02", "OBS-001-AC-03", "OBS-001-AC-04"]
```

Jira: [KAN-30](https://kwulreobeu.atlassian.net/browse/KAN-30), agent-codex. 검증·위키·Git receipt를 확인해 종료한다.
요청: 두 제공 문서의 적용 가능성 확인 및 적용. Git completion_mode=reviewed_merge(기본 계약),
공유 범위는 이번 변경 hunk만, commit/push는 전담 gstack_committer가 수행한다.

- [x] OBS-001-AC-01 공식 Usage·streaming·정규화/정정
- [x] OBS-001-AC-02 불변 원장·재시도/fallback·기존 승인 보존
- [x] OBS-001-AC-03 원본 benchmark item·독립 평가·실패 포함 집계
- [x] OBS-001-AC-04 CLI·SDD·환경·운영/위키 동기화

## 검토와 현재 증거

제공 문서의 마지막 턴 overwrite·stdout 절단·재시도 overwrite 지적은 현재 코드에서 확인됐다.
문서의 Jira 미병합/과거 SHA는 조사 당시의 기록이며 현재 checkout의 Jira/위키/Git 계약을
덮어쓰지 않는다. 설치 Codex CLI 0.164.0의 help/version과 공식 JSONL 문서를 확인했다.
GMS providers 결과는 local_server_unavailable. 기존 선택 키/예산 runner를 우회하지 않고
로컬 구현한다. gstack preamble은 Windows Bash 객체 생성 권한 오류로 degraded이며
프로젝트 계약과 로컬 코드 검토를 계속한다. 유료 외부 리뷰는 수행하지 않는다.

## 검증

Windows 정상 권한에서 신규 관측성29개·기존 공급자15개·managed 하네스13개 검사 통과.
SDD 기본/main 비교는 features25·AC123·tasks55로 통과했다. 제한된 실행 환경에서는 임시 Git
초기화/WinCred 경계로 실패해 정상 권한으로 재검증했다. 코드 문제로 남긴 실패가 아니다.
전체 source 환경 검사399개 중398개 통과, 이번 scope 밖의 미공유 pipeline
`test_target_assessment_requires_distinct_anchored_runs_and_exact_outputs` 1개가
`targets_status: not_met != verified`로 실패했다. pipeline은 관측성 모듈을 import하지 않으며
이번 exact scope/Git 전달에 포함하지 않는다. 별도 origin/main 기반 publisher에서 이번 변경만
분리한 전체 검증은 아래와 같이 통과했다. 실제 Baseline/최적화·Cloud/Claude 실측은 미실행이다.

같은 pipeline 실패 메서드의 단독 비변경 재실행은1개PASS였다. 전체 실행 중 실패를 지우거나
전체 통과로 바꾸지 않는다. 후속 팀 검사35개 및 합성 doctor/get_apartment_detail smoke는
별도PASS이며 실제 평가 준비로 승격하지 않았다. 소스의 이번 작업 외 변경은 보존했다.

독립 읽기 전용 reviewer가 실제 worktree provenance, 중복 완료, usage 누락을 재현했고 수정했다.
후속 probe/정규화4개 PASS와 추가 P0 결함 없음 보고를 받았다. 독립 평가 artifact hash·현재
subject 확인 및 operator_attestation 표시도 반영했다. 전체 회귀 결과와 reviewer probe는 구분한다.

## 격리 후보 검증

origin/main `a7b17141a52e37b0ad4ee43afb4fb35fe5b2ad61`에서 분리한14개 exact 파일만
전담 gstack_committer가 저장했다. snapshot `0001-9b66e5d5a3d2`, 구현 커밋/원격 read-back
`7b6a31ed8eca3b763876d63c9b3341c2773fdf63`, branch `codex/observability-kan30`.
publisher의 관측성29개(exit0), 기존 managed13개(exit0), 전체 `verify_environment.py`(exit0),
`check_sdd.py --base origin/main`(exit0)이 모두 통과했다. helper가 전체 환경 출력의 상세 개수를
보존하지 않아 개수를 추정하지 않았다. 기존 미공유 wiki hook/pipeline과 사용자 index는 전달하지
않았다. 원래 source의 전체 검사 실패 이력도 위에 보존했다. 이 Task의 verified는 현재 범위의
오프라인 구현·검증이며 실제 모델/Cloud/멀티프로바이더·효율 개선 완료를 뜻하지 않는다.

위 검증 결과를 추가한 문서 snapshot도 같은 Git 절차로 재검증하며 PR/CI/최종 병합/정리 상태는
TASK-OBS-001의 Git lifecycle receipt와 Jira에 실제 결과로 별도 기록한다.

## 자동 리뷰 후속 수정

[PR64 리뷰](https://github.com/keulreobeu/jipdam/pull/64#discussion_r4419358269)의 P2를 병합 전에
재현했다. worker가 없는 상태에서 control(pause/cancel)·ready가 managed DB만 바꾸고 기존
finish lifecycle hook을 지나지 않아 측정 원장과 suite 상태가 낡는 원인이었다. 신규 회귀가
수정 전 `WAITING_FOR_PROVIDER != PAUSED`로 실패했고, managed DB transaction 이후 lease가
없는 경우에만 실제 idle 상태를 append하도록 두 경로를 보강했다. 실행 중 control은 그대로
worker 종료에 맡긴다. idle pause→ready→cancel과 suite의 failed1/blocked0을 검증했다.
동시 관리 검토에서 read→append 사이에 다른 ready/claim이 끼어드는 TOCTOU도 발견해,
threading 회귀로 수정 전 실제 추월을 재현했다. 현재 row 재조회와 append를 managed write
transaction 안에서 직렬화하고, 관측 장애 경고는 같은 connection에 기록해 중첩 잠금을 피했다.
finish/approve도 최신 상태 재조회 경로를 사용하며, 늦은 attempt 종료가 authoritative lifecycle
상태를 되돌리지 않게 했다. reviewer가 후속 잠금 순서·경합 해결을 읽기 전용 확인했다.
최종 수정 후 관측성32개 및 managed13개 PASS. 자동 리뷰로 발견한 실패 이력도 보존하며, 이 후보를
격리 전체 검증·새 head의4개 CI·리뷰 확인까지 통과한 후에만 병합한다.

## 위키 판단

maintenance/catalog/ACTIVE 검색과 Confluence CQL 제목/안정ID 검색을 수행했다. 관측성 기존
문서가 없어 CREATE / verified_reusable_knowledge. 문서 ID `WIKI-444E9C9A3DB049D9`, revision1.
[실제 read-back v1](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/2293762).
허용 원본 OBSERVABILITY.md hash `b814e98f49e3056562410c922ca00e86e9e6e7eeff2436b2150a4b55e0363ecb`,
실제 HTML hash `76377a0e284a0010cb87e5ad311b0c37c6abd905d38d7a5f4def248acef41b7b`.
Confluence outbox receipt DONE. Jira comment10146에 같은 판단·범위·검증을 기록했다.
다른 작업의 pipeline STALE/pending은 이번 완료로 처리하지 않는다.
