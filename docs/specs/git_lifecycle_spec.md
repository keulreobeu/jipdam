# Git lifecycle — delegated stage publication

```toml
kind = "spec"
id = "GIT-AUTO-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-29"
approval_ref = "현재 대화: 로컬 즉시 적용·자동화만 별도 브랜치 업로드·commit은 메인 대신 서브에이전트 수행"
```

## 범위

Codex의 작업 진행과 Git 저장을 분리한다. 메인은 구현·범위·문서·검증 판단을 맡고,
전담 committer 서브에이전트는 확정한 스냅샷을 별도 publisher worktree에서 커밋·push한다.
기존 managed task의 COMPLETED, 최종 로컬 autocommit, 사용자 index와 미저장 변경은 유지한다.
현재 KAN-29 전달은 branch_only다. main 병합·브랜치 삭제·배포·실데이터 업로드는 이번 전달에 포함하지 않는다.

## GIT-AUTO-001-REQ-01 격리된 작업 시작과 스냅샷

입력은 task_id, 정확한 파일 scope 배열, 검증 argv 배열, codex/ branch 및 completion_mode다.
Git common directory 기준의 공유 상태/OS 잠금을 사용한다. origin/main을 갱신하고 해당 커밋에서
publisher를 생성한다. dirty source의 전체 HEAD 이력이나 다른 파일을 자동 가져오지 않는다.
단계 handoff는 파일 bytes/삭제·해시를 고정한다. 새 작업은 시작 전에 branch를 만들며 재개는
저장 상태·branch·HEAD가 일치할 때만 허용한다. 등록 경로의 symlink·탈출·민감파일을 거부한다.

### GIT-AUTO-001-AC-01

임시 실제 Git 저장소에서 source/index 보존, scope만 전달, 스냅샷 뒤 source 추가 편집과
다른 worktree controller의 공통 잠금 충돌을 확인한다.

## GIT-AUTO-001-REQ-02 단계별 커밋과 원격 저장

메인은 스냅샷을 요청하고 서브에이전트가 고정 사본만 commit/push한다. 처리 중 source 편집은
다음 단계에 남는다. 각 단계에 고유 ID·commit SHA·원격 read-back을 기록한다. 이전 단계의
committed가 새 단계 저장을 건너뛰게 하지 않는다. 순서 역전/재전송/변조를 거부한다.
민감 경로·본문·원격에 전송할 커밋 범위를 검사한다. Git hooks와 저장소 보호를 우회하지 않는다.
push 실패/응답 유실은 로컬 커밋을 보존하고 실제 원격 SHA를 대사한 뒤 같은 결과를 재시도한다.

### GIT-AUTO-001-AC-02

로컬 bare 원격을 사용해 여러 단계 저장, 중복 호출, push 실패/재시도, 스냅샷 변조와
민감파일 및 범위 밖 history 차단을 검증한다. 실원격 branch push는 별도 전달 증거로 남긴다.

## GIT-AUTO-001-REQ-03 검증과 완료 게이트

중간 저장은 최종 검증 완료와 다르다. 최종 verify는 publisher의 실제 코드와 명시 테스트를
실행하고 HEAD/작업 내용 일치를 재확인한다. 새 단계는 기존 검증을 무효화한다.
검증 명령은 제한 argv·shell=False·publisher 소스 경로를 사용한다. diff check만으로 최종 합격하지 않는다.
COMPLETED를 원격 저장/병합 상태로 재해석하지 않고 별도 Git 단계 상태를 기록한다.

### GIT-AUTO-001-AC-03

중간 커밋 후 재검증, 검증 실패·중간 변경·새 단계의 검증 무효화와 허용 명령 경계를 확인한다.

## GIT-AUTO-001-REQ-04 PR·병합과 복구

branch_only는 원격 브랜치에 보존한다. reviewed_merge의 prepare-finish는 검증한 최신 SHA,
미저장 scope 변경 부재, 필수 위키 완료 근거를 확인한 뒤 connector 요청을 만든다.
전담 서브에이전트는 실제 PR과 필수 CI·최신 main을 확인하고 expected_head_sha를 지정해 병합한다.
명령·네트워크 성공 코드만으로 병합 완료라 하지 않는다. 실제 read-back·URL·SHA를 receipt로 남긴다.
다른 PC와의 경합은 원격 조건부 병합/보호 규칙으로 처리하며 로컬 잠금만으로 해결했다고 주장하지 않는다.
병합 후 위키 재검증·Jira 종료와 브랜치 정리를 별도 기록한다. 정리 실패는 병합을 되돌리지 않는다.
브랜치 추가 커밋·다른 worktree 사용·미저장/ignored 파일이 있으면 강제 삭제하지 않는다.

### GIT-AUTO-001-AC-04

미검증/소스 변경/위키 대기에서는 finish 요청을 거부하고, branch_only에서 자동 병합을 하지 않는다.
실제 connector 근거가 없는 receipt와 다른 SHA를 거부한다. 현재 전달은 실 main 병합을 시험하지 않는다.

## GIT-AUTO-001-REQ-05 로컬 활성화와 서브에이전트 책임

tooling/git-lifecycle.json과 공통 AGENTS 규칙을 활성화하고 Codex 역할 gstack_committer를 등록한다.
새 역할 등록은 새 세션부터 발견될 수 있어 현재 세션에서는 명시 worker 서브에이전트에 같은
책임을 배정한다. 역할 이름/JSON의 actor는 보안 인증이나 OS 격리를 제공하지 않는다.
agent/worker가 실행되지 않는 동안 저장하는 OS 서비스나 원격 webhook을 설치했다고 주장하지 않는다.
기존 미저장 설정을 보존하면서 공유 branch에는 이번 변경 부분만 포함한다.

### GIT-AUTO-001-AC-05

현재 로컬 CLI 진입, 역할 TOML·공통 규칙·SDD, subagent의 실제 commit/push 및
자동화 전용 branch diff/read-back을 검증한다. [운영](../git-lifecycle.md), [Task](../tasks/git-lifecycle.md).
