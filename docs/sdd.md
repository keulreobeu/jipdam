# 집담 SDD 작업 안내

계약은 [SDD Spec](specs/sdd_workflow_spec.md), 결정 이유는 [ADR](adr/ADR-003-sdd-workflow.md), 현재 도입 작업은 [Task](tasks/sdd-adoption.md)에 있다. Codex·Claude Code·Antigravity가 동일한 문서와 명령을 사용한다.

## 작업 순서와 책임

```text
요청 → 기존 계약 확인 → 필요하면 사용자와 요구 확정 → Spec/Plan/ADR
     → 영구 Task → 구현 → AC별 검증 → 담당자 완료 기록 → CI → PR 병합
```

| 변경 | 필요한 기록 |
| --- | --- |
| 새 기능·Tool·계약 변경 | 사용자 확정 Spec + Task |
| 중요한 구조·데이터 모델 변경 | Spec + Plan + ADR + Task |
| 기존 계약 내 버그·리팩터링·설정 변경 | Task + 기존 계약 참조 + 관련 검증 |
| 계약을 바꾸지 않는 README 설명·오탈자 | Task 면제, PR에 사유와 확인 결과 |

실행하는 구현·수정·문서·설정·검증 작업은 Jira `KAN` 이슈로 추적한다. 시작 전에 사용자 지정 티켓을 연결하거나 진행 중인 티켓이 없으면 작업 이슈를 만든다. 단순 질문·설명·실행하지 않는 계획·읽기 전용 검토는 제외한다. 생성·연결·종료 규칙은 [Jira Task Lifecycle](specs/jira_task_lifecycle_spec.md)을 따른다.

제품 요구·비용·데이터·보안·호환성의 주요 결정은 사용자가 확정한다. 담당자는 세부 구현을 판단하고 AC별 증거로 완료 처리한다. AI 계획·리뷰는 초안이다. 현재 요청에 이미 확정된 요구는 다시 승인받지 않고 요청 근거를 기록한다.

## 상태와 문서

Spec 상태는 `draft`, `approved`, `baseline`, `superseded`다. `baseline`은 확인된 기존 구현을 기술하며 과거 승인을 소급하지 않는다. 새 계약은 사용자 확정 근거를 남겨 `approved`로 바꾼다. 폐기한 문서는 `superseded`로 보존하고 대체 문서를 연결한다.

Task 상태는 `draft → ready → in_progress → verified`이고, 외부 조건을 기다리면 `blocked`로 이유를 기록한다. 등록 Spec이 draft 또는 superseded이면 Task를 ready·in_progress·verified로 진행할 수 없다. 요구가 이미 확정된 버그·리팩터링 Task는 담당자가 ready로 만들 수 있다. `verified`는 해당 Task 범위의 AC를 검증했다는 뜻이며 제품 전체나 실제 데이터 평가의 완료를 뜻하지 않는다.

| 템플릿 | 사용 |
| --- | --- |
| [Spec](templates/spec.md) | 범위, 요구·AC, 오류·입출력 계약 |
| [Task](templates/task.md) | 담당자, 범위 경로, AC와 실행 결과 |
| [Plan](templates/plan.md) | 영향·순서·의존성·실패 처리 |
| [ADR](templates/adr.md) | 중요한 결정의 이유와 대안 |

기존 문서 위치는 유지한다. Task를 덮어쓰지 않고 고유 파일·ID로 보존하며 `current.md`에서는 활성 Task를 연결한다. Issue는 필수가 아니다. 같은 문서의 동시 수정은 피하고 파일·Task 담당자를 정한다.

## 기계 판독 계약

시범 Spec/Task의 첫 `toml` 코드 블록을 메타데이터로 사용한다. Spec 필수 필드는 `kind, id, status, owner, revision`이며 approved에는 `approved_by, approved_at, approval_ref`도 필요하다. Task 필수 필드는 `kind, id, status, owner, specs, scope, acs`다. owner는 담당자의 이름 또는 GitHub 계정이다.

ID는 대문자·숫자·하이픈을 사용한다. 기능 `EVAL-001`, 요구 `EVAL-001-REQ-01`, AC `EVAL-001-AC-01`, Task `TASK-SDD-001`처럼 안정적으로 유지한다. Spec의 요구·AC는 해당 ID로 시작하는 Markdown 제목을 만든다. Task AC는 `- [ ] ID 설명` 형식이고 검증 후 `[x]`로 바꾼다.

[추적 원장](sdd/traceability.json)의 `schema_version`은 1이다. `features`에는 `id, spec, requirements`를, 각 requirement에는 `id, acs`를 기록한다. AC의 `tests`는 `{file, class, method}` 배열이고, 수동 검증은 `manual`의 `{command, evidence}` 배열이다. `tasks`는 등록 Task 파일 경로 배열이다. 계약 본문은 Markdown이 원본이며 JSON은 ID·참조·검증 연결만 보관한다.

모든 경로는 저장소 루트 기준 `/` 구분 상대 경로다. Task `scope`는 정확한 파일 경로 또는 `/`로 끝나는 디렉터리 경로다. Spec과 테스트 참조에 glob, 절대 경로, `..`, 저장소 밖 symlink는 허용하지 않는다. 테스트 참조는 실제 unittest TestCase의 `test_` 메서드여야 한다. 기본 CI와 검사기가 공유하는 TEST_ROOTS 아래의 `test*.py` 파일만 인정하며 하위 디렉터리는 `__init__.py`가 있는 패키지여야 한다. skip·expectedFailure 테스트는 AC 검증 근거로 인정하지 않는다.

Task `[[verification]]`에는 `command, result, evidence, acs`를 기록한다. result는 `passed / failed / not_run`이다. verified Task는 모든 AC가 체크되고 각 AC의 마지막 검증 기록이 passed여야 한다. 이후 failed·not_run 기록을 과거 passed 기록으로 덮을 수 없다. evidence는 존재하는 저장소 파일·제목 anchor 또는 HTTPS 결과 링크다. 실행 로그·DB·비밀값을 Git에 넣지 않고 공유 문서에 필요한 결과와 실행 버전을 요약한다.

## 검증과 PR

```sh
python -X utf8 scripts/verify_environment.py
python -X utf8 scripts/check_sdd.py
python -X utf8 scripts/check_sdd.py --base origin/main
```

첫 명령은 SDD 구조·현재 작업 변경 연결, 제품·팀 테스트, 합성 CLI를 실행한다. 마지막 명령은 브랜치의 main 대비 변경과 미커밋 변경을 함께 검사한다. 새 Task는 원장에 등록하고 변경 범위를 선언한다. 코드·설정·계약 변경을 덮는 Task 문서도 같은 변경에서 갱신해야 한다. 기존 Task가 존재한다는 이유만으로 후속 코드 변경을 자동 인정하지 않는다.

설명 문서 면제는 README 및 일반 docs Markdown에 적용한다. `specs/adr/tasks/templates/plans/sdd` 아래 문서, `*_spec.md`, `sdd.md`, AGENTS·CLAUDE·GEMINI 규칙, 스킬·설정·워크플로는 계약이므로 면제하지 않는다. 새 기능의 새 Spec은 원장에 등록한다. 원장에 없는 기존 Spec은 전환 범위 밖으로 유지하지만 변경 시 Task 연결이 필요하다.

CI는 PR base/head 또는 push before/after의 실제 파일 차이를 검사한다. PR은 Task·변경 유형·관련 Spec·AC·실행 결과를 기록한다. 문서 사유나 PR 양식만으로 검사 면제를 받을 수 없다. 사람 리뷰는 권장이며 main은 네 가지 기본 CI 성공을 필수로 한다.

자동 검사는 문법·참조·범위·증거의 존재와 테스트 실행을 확인한다. 테스트가 요구를 충분히 증명하는지, 면제한 설명이 실제 계약을 바꾸지 않는지, 결과의 의미는 담당자와 리뷰어가 확인한다. 가짜 링크나 형식적인 Task 갱신은 완료 근거가 아니다.

## 현재 적용 경계

2026-10-22 이후 위키는 [WIKI-001](../outputs/budongi_mvp_temp/docs/specs/25_wiki_lifecycle_spec.md)과
[운영](../outputs/budongi_mvp_temp/docs/wiki/AUTOMATION.md)을 따른다. 작업 검증 뒤 Jira 완료 전에
문서화 판단(SKIP/LINK_EXISTING/CREATE/UPDATE 등), 사유, 문서 ID/링크, 검증·동기화 상태를
Task/Jira에 기록한다. Spec/ADR/Task의 원본 책임을 유지하며 실제 문서 정합성 검토를 생략하지 않는다.

운영 체계(SDD-001)와 required-fact coverage(EVAL-001)의 기존 등록을 유지하고, 2026-10-06 사용자 승인에 따라 [전월세 추천 RENT-001](../outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md)·[API 키 보관함 CRED-001](../outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md)과 관련 영구 Task를 등록한다. 현재 CRED-001 보관함 구현은 별도 Task에서 추적하며, 전월세 추천·실데이터 수집·단지 매칭·실제 Golden 구성·Router/RAG 확장은 이번 기능 범위에 포함하지 않는다. 문서 완료·합성 데모·실제 성능을 구분하고 데이터 수집 보류를 유지한다.

## Git 단계 저장과 종료

[Git 생명주기](git-lifecycle.md)·[GIT-AUTO-001](specs/git_lifecycle_spec.md)을 따른다.
작업 시작에 branch를 생성하고 메인이 확정한 snapshot의 commit/push는 전담 서브에이전트가 수행한다.
최종 검증과 필수 위키를 해결한 뒤 최신 PR CI·main 반영을 확인하며, Git 저장/병합/정리 상태를 분리한다.
branch_only 요청은 branch를 남긴다. 메인 source/index 및 다른 작업의 미저장 내용은 자동 포함하지 않는다.
