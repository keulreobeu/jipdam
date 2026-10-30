# 작업별 Git 자동 저장

계약: [GIT-AUTO-001](specs/git_lifecycle_spec.md), [Task / KAN-29](tasks/git-lifecycle.md).
정책: [tooling/git-lifecycle.json](../tooling/git-lifecycle.json).

## 누가 언제 실행하는가

로컬 정책은 활성화되어 있다. Codex·Claude는 구현/수정 작업 시작 시 Jira·Task와 exact scope를
확정하고 전담 Git 서브에이전트를 배정한다. 메인은 구현과 파일 버전 확정, 서브에이전트는
브랜치 생성·커밋·push·허용된 종료 처리를 맡는다. 별도 재요청 없이 의미 있는 단계마다 저장한다.
단순 질문·읽기 전용 검토·파일 변경 없음은 빈 커밋을 만들지 않는다.

Codex 새 세션의 역할 이름은 `gstack_committer`다. 역할 목록이 이미 고정된 현재 세션은 일반
worker 서브에이전트에 같은 지침과 정확한 scope를 전달한다. 역할 등록은 현재 실행 중인 세션의
목록을 즉시 바꾸지 않는다. 등록/도구가 없으면 직접 커밋으로 대체하지 않고 위임 대기로 알린다.
사용자는 터미널에서 같은 CLI를 직접 실행할 수 있다. 역할 이름은 보안 인증 수단이 아니다.

agent/worker가 실행 중일 때 단계 이벤트를 처리한다. 앱 종료 중 파일 변경을 감시하는
daemon·스케줄러·OS 서비스는 설치하지 않는다. 기존 managed task `run/approve/autocommit`의
고정 HEAD/완료 계약은 그대로며 이 Git 저장 명령과 별도 상태를 사용한다.

## 시작

루트에서 `.venv/Scripts/python.exe` 또는 의존성이 설치된 Python을 사용한다.
아래 JSON은 `.local_runtime/git-work/request.json`에 실제 작업 파일명으로 저장한다.
scope는 파일 경로 배열이다. 디렉터리/glob/원본 DB/키/raw/runtime은 넣지 않는다.

```json
{
  "task_id": "TASK-EXAMPLE-001",
  "branch": "codex/task-example-001",
  "completion_mode": "reviewed_merge",
  "scope": ["outputs/budongi_mvp_temp/src/example.py", "outputs/budongi_mvp_temp/tests/test_example.py"],
  "validation": [
    ["python", "-m", "unittest", "discover", "-s", "outputs/budongi_mvp_temp/tests", "-p", "test_example.py"],
    ["python", "-X", "utf8", "scripts/check_sdd.py", "--base", "origin/main"]
  ]
}
```

전담 서브에이전트가 시작한다.

```powershell
python -m harness git start --request .local_runtime/git-work/request.json
python -m harness git status --task TASK-EXAMPLE-001
```

start는 최신 origin/main에서 별도 publisher worktree와 codex/ 브랜치를 만들고 최초 branch를
push한다. 원본 checkout의 미커밋 변경과 index는 건드리지 않는다. 현재 작업폴더의 과거 커밋
전체를 새 branch에 포함하지 않는다. 따라서 기존 미공유 코드에 의존하는 기능은 필요한 의존
변경을 scope에 명시하고 검증해야 한다. 권한·네트워크·branch 충돌 시 범위를 넓혀 우회하지 않는다.

기존 공유 파일에 다른 작업의 미저장 수정이 같이 있으면 그대로 snapshot하지 않는다.
origin/main 파일에 이번 변경 부분만 합성한 별도 source_root를 만들고 담당자가 비교한다.
source_root는 같은 저장소 안의 작업 폴더만 허용한다. 이번 KAN-29도 이 방식으로 자동화만 전달한다.

## 단계별 저장과 병행 작업

메인은 단계의 exact scope 파일을 모두 저장한 다음 immutable snapshot을 만든다.
파일별 전후 해시를 비교하며 캡처 중 source가 바뀌면 다시 시도한다.

```powershell
python -m harness git snapshot --task TASK-EXAMPLE-001 --stage implementation
```

반환한 pending_snapshot을 전담 서브에이전트에 전달한다. 메인은 source에서 다음 편집을 계속할 수 있다.
서브에이전트는 고정 사본을 publisher에 적용하고 해당 snapshot만 commit/push한다.

```powershell
python -m harness git checkpoint --task TASK-EXAMPLE-001 --snapshot 실제반환ID
python -m harness git status --task TASK-EXAMPLE-001
```

다음 snapshot은 이전 pending 저장을 해결한 뒤 만든다. 소스 편집은 그동안 가능하다.
커밋·원격 read-back 영수증은 단계별로 보존한다. 실패하면 같은 snapshot ID로 재시도한다.
source의 새 버전을 이전 저장 요청에 덮어 넣지 않는다. push 성공 뒤 응답이 유실돼도 실제
원격 SHA를 읽어 중복 커밋을 피한다. force push/amend/reset/보호 규칙·hook 우회를 하지 않는다.
중간 저장은 최종 검증 합격 표시가 아니다. 민감정보·scope 검사는 모든 단계에 적용한다.

## 검증과 종료

```powershell
python -m harness git verify --task TASK-EXAMPLE-001
```

등록한 검증을 publisher의 실제 코드로 실행한다. HEAD·작업 내용이 바뀌면 합격하지 않으며
새 snapshot이 생기면 이전 검증은 무효다. diff --check만으로 최종 완료하지 않는다.
필수 위키는 병합 전에 해결한다. 문서 판단 근거를 실제 wiki decision/URL로 담는다.

```json
{"status": "SYNCED", "evidence": "실제 위키 decision ID 또는 read-back URL"}
```

```powershell
python -m harness git prepare-finish --task TASK-EXAMPLE-001 --documentation .local_runtime/git-work/documentation.json
```

이 명령은 병합 자체가 아니라 서브에이전트가 처리할 GitHub connector 요청을 만든다.
서브에이전트는 PR·필수 CI·최신 main 통합 상태를 확인하고 검증한 expected_head_sha로 병합한다.
main이 앞서가면 기존 합격을 재사용하지 않는다. 전담 서브에이전트가 아래 명령으로 충돌 없는
최신 main 통합 후보를 만들고 다시 verify한다. 충돌은 자동 해결하지 않고 원본과 branch를 보존한다.

```powershell
python -m harness git refresh-base --task TASK-EXAMPLE-001
python -m harness git verify --task TASK-EXAMPLE-001
```

통합 후 코드 추가 수정이 필요하면 source를 최신 후보와 대조해야 한다. 오래된 source snapshot을
그대로 재적용하지 않는다. 자동 충돌 해결이나 원격 병합 큐 서비스를 제공하는 것은 아니다.

실제 connector 응답과 main read-back으로 receipt를 기록한다. 상세 필드는 CLI의 finish_request와
구현된 receipt 계약을 따른다. 확인하지 않은 merged/check 성공을 JSON에 넣지 않는다.
원격 수동 변경·다른 PC의 경합은 조건부 병합과 서버 보호를 따른다. 로컬 잠금은 그 PC의
동일 Git common directory에서만 직렬화를 제공한다.

병합 뒤 위키 merge 이벤트 재검증·Jira 마감과 branch 정리를 진행한다. 원격 branch에 새 커밋,
다른 worktree 사용, publisher 미저장/ignored 산출물이 있으면 삭제하지 않는다. cleanup은
별도 재시도이며 이미 반영한 main을 자동 reset하지 않는다. source worktree와 스냅샷은 보존한다.

`completion_mode: branch_only`는 검증·push 뒤 branch를 남긴다. 이번 KAN-29는 사용자 확인용으로
이 모드를 적용하며 main 병합과 branch 삭제를 실행하지 않는다.

## 복구와 상태 보관

상태·스냅샷은 공통 저장소의 ignored `.local_runtime/git-managed/`에 저장한다.
토큰이나 Git 인증값을 JSON에 넣지 않는다. Git push 인증은 사용자의 기존 Git 설정,
PR/CI/병합은 공식 GitHub connector를 쓴다. `.gitignore`만으로 비밀 방지를 대신하지 않는다.
각 checkpoint의 실제 blob과 전송할 history를 검사한다.

PUSH_PENDING이면 로컬 커밋이 보존되어 있다. 원격 read-back 뒤 같은 snapshot을 checkpoint한다.
외부 HEAD 변경·scope 이탈·snapshot 변조는 자동 덮어쓰기 대신 조사한다.
검증 실패는 코드를 source에서 수정하고 새 snapshot으로 저장·재검증한다.
최종 완료, 원격 저장 완료, 병합 완료, 정리 완료를 구분해 보고한다.
