# 위키 자동 관리 운영

[사용자 정책 v1.0](LIFECYCLE_POLICY.md), [Spec](../specs/25_wiki_lifecycle_spec.md),
[Task](../tasks/wiki-lifecycle.md), [Confluence 집담 개발 위키](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/360449).

## 실행 시점과 책임

Codex·Claude Code는 구현·수정 작업의 검증 완료 뒤, Jira 완료 이전에 문서화 판단·동기화를
수행한다. 별도 요청을 기다리지 않는다. CLI 하네스 run/validate 성공에는 판단 hook이
자동 실행되며 미완료 문서는 approve를 차단한다. worker는 시작 직후 및 매시간 유지관리를
수행한다. worker/agent가 실행되지 않는 동안 동작하는 원격 웹훅·OS 서비스는 설치하지 않았다.
PR merge·배포·장애 이벤트는 이를 확인한 agent가 CLI로 입력하고 관련 문서를 재검증한다.

## 문서화 판단

```powershell
python -m harness wiki maintenance
python -m harness wiki catalog
python -m harness wiki search --query "기능 또는 원인"
python -m harness wiki event --request .local_runtime/wiki-work/event.json
python -m harness wiki pending
python -m harness wiki metrics
```

catalog의 파일·관련 Spec/ADR/Task와 Confluence의 ID·모듈·원인·유사 제목을 검색한다.
CQL 오류 시 공간 content 목록을 끝까지 조회한다. 검색 누락·실패 시 신규 생성하지 않는다.
담당자가 근거·의미 중복을 확인한 뒤 현재 catalog.hash를 review.catalog_hash에 넣는다.
semantic_checked는 담당자의 실제 의미 검토 기록이며 vector 검색을 수행했다는 주장이 아니다.

```json
{
  "event_id": "TASK-EXAMPLE-VERIFIED-1",
  "event_type": "task_verified",
  "task_id": "TASK-EXAMPLE",
  "jira_key": "KAN-19",
  "verified": true,
  "validation_passed": true,
  "reasons": ["reusable_feature"],
  "knowledge": {
    "key": "STABLE-TOPIC-KEY",
    "title": "검증된 사용 절차",
    "project": "jipdam",
    "module": "해당 모듈",
    "owner": "실제 지정 소유자",
    "environment": "Windows / Python 3.12",
    "version": "적용 버전",
    "kind": "guide",
    "risk": "low",
    "sources": [{"path": "docs/실제원본.md", "sha256": "실제 파일 SHA-256"}],
    "sections": {
      "purpose": "목적·범위",
      "situation": "상황·증상",
      "cause": "확인된 원인과 미확인 사항",
      "procedure": "실행 가능한 절차",
      "cautions": "주의사항·예외",
      "verification": "실제 검사·결과",
      "references": "원본 경로 또는 확인된 링크"
    }
  },
  "review": {
    "reviewer": "agent-codex",
    "evidence_checked": true,
    "semantic_checked": true,
    "catalog_hash": "실제 catalog.hash"
  }
}
```

위 예시는 설명용이며 실제 해시·소유자·검증 결과로 채운다. reasons는 repeated_problem/
nonobvious_cause/operations_changed/contract_changed/high_impact/reusable_feature/explicit_request다.
제외 시 reasons 없이 exclude=typo/formatting/refactor_only/one_off/execution_log/
generated_reference/no_changes 중 하나를 기록한다. 미검증을 SKIP으로 위장하지 않는다.
반복 문제는 cause_key와 서로 다른 관측 이벤트가 필요하다. 동일 ID 재처리는 횟수를 늘리지 않는다.
갱신은 document_id·expected_revision을 넣으며 환경/버전이 다르면 병행 유지한다.
유사 제목이 독립 주제이면 실제 검토 뒤 review.independent_topic=true와 이유를 기록한다.

임시 조치는 kind=temporary, 실제 owner, expires_at(시간대 포함, 최대30일)이 필요하다.
risk=operations/security/privacy/cost/recovery는 지정 담당자의 publication_approved=true가
있어야 ACTIVE다. publication_approved_by는 owner와 같아야 하고 approval_ref에 실제 승인 근거를 남긴다.
승인자를 추정하지 않는다. source 변경·누락·검증되지 않은 링크는 게시를 막는다.
원격 링크는 link_checks의 url/ok/reviewer/checked_at으로 실제 connector 확인을 기록한다.

수동 편집은 덮어쓰지 않는다. 편집 내용을 통합·검증한 후 현재 파일 SHA-256을 expected_file_hash로
지정하여 재개한다. 하네스 report.result.wiki의 미해결 판단은 새 event에 resolves=원래event_id와
같은 task_id를 넣어 해결한다. 미병합 worktree 코드를 원본에 적용된 것처럼 게시하지 않는다.

공유 Markdown의 본문은 정상이나 등록된 원본이 변경되어 import review에 남은 경우에는,
원본 변경분과 기존 문서의 의미를 실제 검토한 뒤 `wiki review-shared --request <JSON>`으로
복구한다. 요청에는 `document_id`, 현재 공유 파일의 `expected_file_hash`, 원래 `expected_revision`,
`reason`, `validation_passed=true`, 새 `knowledge` 전체와 실제 현재 `sources` 해시, 그리고
`review`의 `reviewer`, `evidence_checked=true`, `semantic_checked=true`, 현재 `catalog_hash`가 필요하다.
문서 key·project·environment·version·owner·module·kind·risk는 기존 값과 같아야 한다.
고위험 문서는 기존 승인 규칙을 추가로 따른다. 본문 위변조, 누락 원본, 미검증 링크, 변경된
파일·catalog·revision은 거부한다. 기존 revision과 검토 요청은 로컬 이력에 보존한다.
Markdown export가 실패하면 ACTIVE 검색에 노출하지 않고 기존 review를 유지한다. export 재시도
성공으로 로컬 review가 해소되어도 원격 outbox는 별도이며, stable ID 검색과 원격 수동 변경 확인,
실제 read-back receipt를 거쳐야 동기화 완료다. 이 명령은 원격 문서를 직접 덮어쓰지 않는다.

## Confluence와 Jira 동기화

[connection.json](connection.json)은 사용자가 지정한 공간·부모 ID·승인만 저장한다.
인증은 Codex 연결 Atlassian 또는 Claude 공식 MCP OAuth를 사용한다. Python에 키를 넣지 않는다.
Python은 outbox 요청을 만들며 현재 작업 agent가 공식 connector를 실행한다.

```powershell
python -m harness wiki pending
python -m harness wiki delivery --id DELIVERY_ID
python -m harness wiki receipt --request .local_runtime/wiki-work/receipt.json
python -m harness wiki decision --event EVENT_ID
```

delivery의 target.parentContentId 아래에서 stable document ID를 먼저 검색한다. 생성 전
space 지침/format guide를 확인한다. 기존 문서는 full HTML을 읽고 binding.remote_version/
remote_hash와 비교한다. 원격 수동 편집·ID 중복은 검토 대기다. snapshotToken으로 갱신하고
수동 내용·rich 요소를 보존한다. 저장 뒤 다시 읽은 실제 URL·버전·HTML SHA-256을 기록한다.
요청 HTML과 저장 HTML의 hash가 같다고 가정하지 않는다.

remote_hash는 실제 read-back 전체 HTML을 UTF-8/LF/끝 개행1개로 정규화한 SHA-256이다.
`python -m harness wiki remote-hash --file .local_runtime/wiki-work/readback.html`로 계산한다.

원격 문서가 이미 있으나 로컬 binding이 없으면 stable ID로 문서를 검색하고 공식 connector로
전체 HTML·URL·버전을 직접 읽어 수동 변경과 의미를 검토한 뒤 `wiki bind-existing --request <JSON>`을
사용할 수 있다. 요청에는 대상 `delivery_id`, 현재 `expected_revision`, 실제 `url`·문자열
`remote_version`, `.local_runtime/` 아래 `readback_file`, 정규화한 `remote_hash`, 검토자
`reviewer`, `identity_checked=true`, `semantic_checked=true`, `manual_changes_reviewed=true`,
현재 `catalog_hash`가 필요하다. 연결은 기준점을 기록할 뿐 대기 전송을 성공 처리하지 않는다.
본문에 stable ID가 없으면 공식 connector에서 읽은 정확한 `[문서 ID] 제목`을 `remote_title`로
함께 제공한다. 제목만으로 본문·수동 변경 검토를 생략하지 않는다.
이미 다른 binding이 있으면 충돌로 보류한다. 이후 갱신 직전 원격 버전·해시를 다시 비교하고
수동 편집을 보존해 snapshotToken으로 변경한 다음 실제 read-back receipt를 남긴다.

```json
{
  "delivery_id": "실제 대기 ID",
  "success": true,
  "reviewer": "agent-codex",
  "url": "https://kwulreobeu.atlassian.net/wiki/실제페이지",
  "remote_version": "실제 버전",
  "remote_hash": "실제 저장된 HTML SHA-256"
}
```

Jira channel은 지정 이슈에 판단·사유·대상ID/링크·검증·상태를 댓글로 남기고 댓글 URL/ID를
receipt로 기록한다. Task에도 결과를 연결하고 이슈를 완료한다. 실패는 success=false이며
최대3회 재시도한다. 복구 후 실제 성공 receipt로 대기를 해제한다. 영수증은 담당자의
실제 connector 결과 확인 기록이다. 상시 전송에는 공식 도구를 쓸 agent가 실행 중이어야 한다.
비활성 문서는 원격 본문 재게시 대신 접근 제한·보관·대체 링크를 처리한다. 민감정보 노출은
일반 큐보다 먼저 접근 제한/게시 중단하고, 권한이 없으면 차단 완료로 표시하지 않는다.

## 재검토·병합·보관

```powershell
python -m harness wiki maintenance --changed-path outputs/budongi_mvp_temp/src/해당파일.py
python -m harness wiki history --document DOCUMENT_ID
python -m harness wiki transition --request .local_runtime/wiki-work/transition.json
python -m harness wiki merge --request .local_runtime/wiki-work/merge.json
python -m harness wiki search --status SUPERSEDED --environment ENV --version VERSION
python -m harness wiki retry
```

runbook30일, interface90일, guide/troubleshooting180일, stable365일이다. 기간 경과는 STALE이며
임의 재작성·삭제하지 않는다. ACTIVE라도 만료·근거 변경·수동 편집·링크 실패면 검색에서 제외한다.
transition: document_id/expected_revision/status/reason/reviewer, 폐기에는 approved_by=owner,
support_checked=true/still_supported=false/retention_checked=true가 필요하다.
DEPRECATED/SUPERSEDED → ARCHIVED → TRASHED를 지키며 참조가 있으면 대체 문서가 필요하다.
merge: 대표 document_id/duplicates/revisions/catalog_hash/reviewer/approved_by/
all_valid_content_preserved=true. 같은 환경·버전의 유효 내용 통합을 소유자가 확인한다.
과거 지원 버전·문서 ID·대체 링크를 보존하며 영구 삭제 명령은 제공하지 않는다.

## 보관과 측정

SQLite 상태·이력·outbox는 ignored `.local_runtime/wiki-managed/`, 공유 문서는 `pages/`다.
실행 이력·원격 binding 복구에는 로컬 상태도 보존해야 한다. 제품 부동산 RAG에는 연결하지 않는다.
ACTIVE 메타데이터 검색을 제공하며 metrics의 정확도·해결 성공률·의미 중복률·승인 지연은
측정 근거가 없으면 unmeasured다. 이 엔진의 자동 모델 호출은 0회다.
