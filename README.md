# 집담 (Jipdam)

서울 아파트 전월세 단지 후보를 예산·직장 위치·생활시설 조건으로 추천하고 이유와 포기할 조건을 비교하는 프로젝트다. 승인된 [RENT-001](outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md)과 [전환 Plan](outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md)을 따른다. 기존 Python·SQLite 역사 조회·로컬 모델·합성 추천/평가와 키 보관함을 보존하면서, 실제 canonical DB read-only serving, 대화형 검색과 니즈/상세 화면을 추가했다. 실제 확정 단지 연결은 아직 없어 결과는 `data_not_ready`다. [MVP 실행 안내](outputs/budongi_mvp_temp/README.md#대화형-db-전월세-mvp)와 [검증 기록](outputs/budongi_mvp_temp/docs/rental-mvp-validation-20261013.md)을 참고한다.

팀원은 **Codex, Claude Code, Antigravity 중 익숙한 도구**로 작업할 수 있다. 같은 코드·Spec·ADR·Task·검증 명령을 공유한다. GitHub에는 Codex와 Claude Code용 gstack 지원을 함께 보관하지만, bootstrap에서는 작업 host 하나만 선택해 설치한다.

## 데이터 수집·공유

데이터 수집·공유는 [수집 현황](docs/data-collection.md)에서 확인한다. **수집 전 GitHub 범위 예약, Drive ZIP 업로드 전 결과 요약 기록은 필수**다. 기존 완료/예약 범위는 건너뛰고 미수집/실패분만 수집한다. 원본 ZIP은 [공유 Drive](https://drive.google.com/drive/folders/13AjoiYNCWcIB12GhSKyLiR1M2bR4Drkg)에 보관한다.

3인 분담은 [채팅 공유용 요약](outputs/budongi_mvp_temp/docs/team-collection-chat-summary.md)과 [상세 확보처·추가 데이터·제출 안내](outputs/budongi_mvp_temp/docs/team-collection-details.md)를 사용한다. 스키마의 공식 기준은 [팀 데이터 계약](outputs/budongi_mvp_temp/docs/team-data-contract.md)이다.

## 1. 저장소 받기

```sh
git clone https://github.com/keulreobeu/jipdam.git
cd jipdam
```

Windows에서는 저장소 루트 또는 `outputs/budongi_mvp_temp/`의 **`jipdam-server-v5.exe`**를 실행하면 터미널에 서버 출력과 시작 상태가 표시되고, 준비 후 브라우저가 열립니다. 기본 포트 8766이 사용 중이면 8767~8796에서 빈 포트를 찾아 실행합니다. `build_server_exe.ps1`로 다시 빌드할 수 있습니다. Python과 인터넷 연결이 필요하며 PyInstaller를 `.local_runtime/`에 설치합니다. 앱 코드와 로컬 데이터베이스는 기존 저장소 위치에서 사용합니다.

API 키 보관함 서버는 **`jipdam-credentials.exe`**를 실행합니다. 8765가 사용 중이면 8766~8796에서 사용 가능한 포트를 찾아 브라우저를 엽니다. 재빌드는 `build_credentials_exe.ps1`로 합니다.

선택한 AI 도구에서 **이 README가 있는 저장소 루트**를 작업 폴더로 연다. 애플리케이션은 `outputs/budongi_mvp_temp/`에 있다. 각자 AI 도구에 로그인하고 자신의 계정·실행 권한을 사용한다.

| 작업 | 필요한 도구 |
| --- | --- |
| clone·브랜치·커밋 | Git |
| 코드 수정·테스트·합성 데이터 조회 | Python 3.11 이상 |
| 선택한 host용 전체 gstack | Python + Git + Bun 1.3.14 이상 + Node.js 22 이상 + Bash |
| Windows의 전체 gstack | Git for Windows에 포함된 Git Bash |
| 컨테이너 실행 | Docker Engine/Desktop + Compose, 선택 사항 |
| 로컬 모델 답변 시험 | Ollama와 모델, 선택 사항 |

설치 안내: [Python](https://www.python.org/downloads/), [Git](https://git-scm.com/downloads), [Bun](https://bun.sh/docs/installation), [Node.js](https://nodejs.org/en/download).

## 2. 공통 환경 확인

AI 도구와 관계없이 저장소 루트의 터미널에서 실행한다.

```sh
python -m pip install -e outputs/budongi_mvp_temp
python -X utf8 scripts/bootstrap.py --app-only
```

Linux/macOS에서 `python` 명령이 없으면 `python3`를 사용한다. 첫 명령은 `cryptography`를 포함한 앱의 선언 의존성을 설치하며 패키지를 다운로드할 수 있다. `--app-only`는 gstack·브라우저 설치를 건너뛰고 제품·설치 도구 테스트와 합성 스냅샷 조회를 실행한다. 검증에는 외부 API 키, 모델, GPU가 필요하지 않다.

전역 Python 환경을 바꾸지 않고 의존성을 설치하려면 가상 환경을 사용한다.

Windows PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install -e outputs/budongi_mvp_temp
jipdam --help
python -X utf8 scripts/bootstrap.py --app-only
```

Linux/macOS Bash:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e outputs/budongi_mvp_temp
jipdam --help
python -X utf8 scripts/bootstrap.py --app-only
```

패키지 설치 시에는 빌드·앱 의존성을 다운로드할 수 있다. 제품 명령·Docker·Ollama 사용법은 [애플리케이션 README](outputs/budongi_mvp_temp/README.md)에 있다.

## 3. 사용하는 AI 도구 연결

| 도구 | 프로젝트 시작 | 공통 규칙 연결 | 현재 gstack 범위 |
| --- | --- | --- | --- |
| Codex | 저장소 루트를 프로젝트로 열기 | 루트·제품 `AGENTS.md` | 전체 설치 및 Codex 스킬 등록 검증 |
| Claude Code | 루트 터미널에서 `claude` 실행 | `CLAUDE.md`가 루트·제품 `AGENTS.md` import | bootstrap이 프로젝트 `.claude/skills/`에 upstream Claude host skills 등록 |
| Antigravity | 저장소 루트를 workspace로 열기 | `AGENTS.md`를 프로젝트 규칙으로 사용 | 공통 작업 절차 사용; 생성된 Codex용 gstack의 실행 호환성은 미검증 |

### Codex

[루트 AGENTS.md](AGENTS.md)와 [제품 AGENTS.md](outputs/budongi_mvp_temp/AGENTS.md)를 기준으로 작업한다. 전체 gstack을 사용할 때는 다음 절의 설치를 진행한다. 생성 스킬은 clone에 포함되지 않으므로 첫 설치가 필요하다.

### Claude Code

Claude Code를 설치하고 로그인한 뒤 저장소 루트에서 시작한다.

```sh
claude
```

저장소의 [CLAUDE.md](CLAUDE.md)는 공통 `AGENTS.md`를 import한다. 제품 규칙을 별도로 복사해 유지하지 않는다. 세션에서 `/memory`로 규칙이 로드됐는지 확인하고, 빠졌다면 아래 공통 첫 프롬프트로 파일을 직접 읽게 한다. import 방식은 [Claude Code 공식 안내](https://code.claude.com/docs/en/memory#import-additional-files)에 따른다.

Claude Code에서 전체 gstack을 설치할 때는 다음 host를 지정한다.

```powershell
python -X utf8 scripts/bootstrap.py --host claude
```

이 명령은 고정된 gstack commit에서 Claude host용 native skill만 생성해 프로젝트 `.claude/skills/`에 등록한다. Codex용 설치는 `--host codex`를 사용한다. host를 바꾸면 bootstrap이 자기 installer marker가 있는 이전 host의 gstack 등록본만 정리한다. 다른 host의 user-owned 파일은 그대로 둔다. gstack은 git/원격 작업 권한을 부여하거나 Claude Code의 권한 승인을 바꾸지 않는다. 일반 코드 작업·검증은 공통 명령으로 수행한다.

집담의 구현·수정·문서·설정·검증 요청은 Jira `KAN` 이슈로 자동 추적한다. Codex 사용자는 Atlassian Jira 앱을 연결하고, Claude Code는 저장소의 [`.mcp.json`](.mcp.json)에 등록된 Atlassian MCP 서버를 사용한다. Claude Code를 처음 열면 `/mcp`를 실행해 Atlassian에 OAuth 인증하고 연결을 승인한다. 연결 뒤 새 작업을 시작하면 에이전트가 이슈를 만들거나 기존 요청 이슈에 연결하고 `진행 중`으로 옮긴다. 검증까지 끝난 경우에만 닫는다. host label은 `agent-codex` 또는 `agent-claude`를 사용하며 담당자를 임의로 지정하지 않는다. 인증 토큰은 저장소에 저장하지 않는다. 자세한 규칙은 [Jira Task Lifecycle Spec](docs/specs/jira_task_lifecycle_spec.md)을 참고한다.

### Antigravity

저장소 루트를 workspace로 열고 Agent에서 작업한다. 공식 문서의 [프로젝트 규칙](https://www.antigravity.google/docs/rules/)은 `AGENTS.md`를 지원하며, [프로젝트 스킬](https://www.antigravity.google/docs/skills/)은 `.agents/skills/`를 사용한다. 도구 버전에 따라 규칙 인식 여부를 확인하고, 아래 첫 프롬프트로 동일한 파일을 직접 읽게 할 수도 있다.

추적되는 `jipdam-workflow`는 공통 프로젝트 절차다. 전체 bootstrap으로 생성하는 `gstack-*`는 Codex용 manifest·preamble을 사용하므로 Antigravity의 네이티브 실행을 검증했다고 보지 않는다. Antigravity만 사용하는 팀원은 `--app-only`로 시작하면 된다.

### 모든 도구에서 쓸 첫 프롬프트

다음을 붙여 넣은 뒤 실제 작업 요청을 이어서 적는다.

```text
이 저장소에서 작업하기 전에 다음 파일을 읽고 따라줘.
- AGENTS.md
- outputs/budongi_mvp_temp/AGENTS.md
- .agents/skills/jipdam-workflow/SKILL.md
- outputs/budongi_mvp_temp/docs/specs/00_project_spec.md
- outputs/budongi_mvp_temp/docs/tasks/current.md

현재 애플리케이션은 outputs/budongi_mvp_temp/에 있다.
관련 Spec·ADR·Task를 확인하고, 변경 후 필요한 검사와 문서를 갱신해줘.
실제 데이터 수집·단지 매칭 보류를 유지하고 합성 시험을 실측 성능으로 보고하지 마.
검증은 저장소 루트에서 python -X utf8 scripts/bootstrap.py --app-only로 할 수 있다.
설치되지 않은 스킬이나 다른 도구의 전용 명령을 사용할 수 있다고 가정하지 마.
```

## 4. 현재 host용 전체 gstack 설치

팀 공통 개발에 필요한 Python 검증과 별도로, 전체 기획·리뷰·QA 스킬을 Codex에 등록하는 선택 설치다.

```sh
python -X utf8 scripts/bootstrap.py --host codex
```

Windows에서는 `./scripts/setup-gstack.ps1 --host codex`, Linux/macOS에서는 `bash scripts/setup-gstack.sh --host codex`도 같은 설치를 실행한다. Claude Code 사용자는 host 값을 `claude`로 지정한다. 고정된 commit의 gstack, Bun 의존성, Chromium을 다운로드하며 개인의 전역 host 설정을 변경하지 않는다. 전체 bootstrap에서는 `--host`가 필수다.

Codex 선택 시 gstack 56개와 `jipdam-workflow` 1개가 Codex 탐색 경로에 등록된다. Claude Code 선택 시 gstack 56개가 `.claude/skills/`에 등록된다. 도구에서 목록이 갱신되지 않으면 프로젝트를 다시 연다. 단순 코드 수정 때 전체 설치를 반복할 필요는 없다.

```sh
python -X utf8 scripts/verify_environment.py --gstack --browser --host codex
python -X utf8 scripts/register_gstack.py --check
```

Claude Code 선택을 검증하려면 `--host claude`와 `python -X utf8 scripts/register_claude_gstack.py --check`를 사용한다. 브라우저 검증은 빈 테스트 화면에서 실행한다. 원본·fixture·선택하지 않은 host의 생성본은 스킬 탐색 경로 밖에 둔다. Antigravity용 gstack 연결은 미구현이다. 상세 설치·확장 방법은 [gstack 안내](docs/gstack.md)에 있다.

## 5. 함께 작업하는 규칙

- [SDD 작업 안내](docs/sdd.md)와 별도 [Spec](docs/templates/spec.md)·[Task](docs/templates/task.md)·[Plan](docs/templates/plan.md)·[ADR](docs/templates/adr.md) 템플릿을 사용한다. 제품 요구는 사용자가 확정하고 담당자가 AC별 검증 근거로 완료 처리한다.
- 작업마다 영구 Task ID를 만들고 코드·설정·계약 변경과 연결한다. 단순 설명·오탈자 수정은 면제한다. 기본 검증에 SDD 검사가 포함되며 브랜치 변경은 `python -X utf8 scripts/check_sdd.py --base origin/main`으로 확인한다.
- main은 네 가지 기본 CI가 필수이며 사람 리뷰는 권장한다. PR 양식에 Task·Spec·AC·검증 결과를 남긴다. 도입 상태와 실제 설정 근거는 [SDD 검증 기록](docs/sdd/validation.md)을 따른다.

- 확정 요구는 Spec, 중요한 결정 이유는 ADR, 실행 단위와 결과는 Task에 기록한다. AI의 계획·리뷰 결과는 초안이다.
- 각 팀원은 별도 clone 또는 브랜치에서 작업하고 PR로 변경을 공유한다. 다른 AI 도구끼리도 같은 파일의 동시 수정을 피한다.
- 모델에 SQL·DB 직접 접근 권한을 주지 않는다. 허용된 Data Tool·인자 검증·호출 제한·출처 추적을 유지한다.
- 현재 실제 데이터 수집·단지 매칭은 보류 중이다. 실제 검수 스냅샷·사람 검수 Golden 없이 정확도나 Phase 완료를 주장하지 않는다.
- 계정 정보·API 키·모델·DB·원천 데이터·로그·로컬 runtime은 Git에 넣지 않는다. 개인 AI 설정은 팀 공통 규칙과 분리한다.

기본 검증은 모든 도구에서 같다.

```sh
python -X utf8 scripts/verify_environment.py
```

GitHub CI는 Ubuntu/Windows × Python 3.11/3.12의 모델 없는 검증을 실행한다. [팀 환경 검증 기록](docs/team_environment_validation.md)은 Codex gstack의 Windows 검증, Claude skill 등록과 실제 Claude 세션 검증, 실제 모델·데이터 평가 범위를 구분한다.

## 문서와 저장소 구조

| 위치 | 용도 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 팀 공통 작업 규칙과 Codex용 gstack 연결 |
| [CLAUDE.md](CLAUDE.md) | Claude Code의 공통 규칙 import |
| [애플리케이션 README](outputs/budongi_mvp_temp/README.md) | 제품 CLI·데이터·모델·Docker 사용법 |
| [Spec](outputs/budongi_mvp_temp/docs/specs/00_project_spec.md) / [현재 Task](outputs/budongi_mvp_temp/docs/tasks/current.md) | 확정 계약과 진행 상태 |
| [jipdam-workflow](.agents/skills/jipdam-workflow/SKILL.md) | 팀이 개선하는 프로젝트 전용 절차 |
| [gstack 안내](docs/gstack.md) / [commit lock](tooling/gstack.lock.json) | 고정 설치와 확장 절차 |
| `scripts/` | 공통 설치·검증·공유 스크립트 |
| `.local_runtime/` | Git에서 제외하는 도구·캐시·검증 산출물 |

서비스·패키지·새 CLI 이름은 **집담(Jipdam)**·`jipdam`이다. 기존 `budongi` Python 모듈·CLI, 작업 폴더·데이터 ID는 호환성을 위해 유지한다. 저장소는 [keulreobeu/jipdam](https://github.com/keulreobeu/jipdam)이다.

공유 ZIP이 필요하면 `python -X utf8 scripts/export_team.py`를 실행한다. 공유 대상만 `.local_runtime/team-share/jipdam-team-source.zip`에 담는다.

### 대화형 전월세 MVP — 2026-10-14

채팅 초안 확인·수정, 실제 DB 추천, 후보별 니즈, 100행 거래 상세와 Leaflet+OSM 내장 지도를 구현했다. 2026-10-20 검수 serving `data/rental/serving/reviewed-20261020.sqlite3`에는 238,620건 중 203,159건(5,156개 단지)의 승인 관계가 반영됐다. 예외 35,461건은 미확정이며 연결 거래의 상태도 모두 `unknown`이라 실제 추천은 `data_not_ready`다. 보존한 이전 canonical의 0건 연결과 이 검수 serving을 구분한다. 검수 자료·실모델은 준비 조건이다. [실행·검수 패키지·성능 재현 안내](outputs/budongi_mvp_temp/docs/rental-review-package.md)를 따른다.

2026-10-15 후속 준비: [1~5번 목적별 계획](outputs/budongi_mvp_temp/docs/plans/continuation-parts-1to5.md)과 [실제 검증](outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md)을 따릅니다. canonical v3 기본 경로·검수/로컬 모델 readiness CLI·Drive 패키지 다운로드·SOL/LUNA 난이도 선택을 연결했습니다. GMS는 최신 사용자 지시에 따라 누적을 차단 기준으로 쓰지 않고 선택한 개인 키의 실잔액 1,000을 보존합니다(이전 5,000은 이력). 두 모델의 최신 설정 UI 호출·정산 검증도 완료했습니다. 실제 검수 자료/모델의 남은 게이트는 Task 기록을 따릅니다.

### CLI-First 개발 하네스

현재 구현과 Codex CLI·Claude Code CLI·Antigravity별 지원 상태는 [팀 공유 하네스 요약](outputs/budongi_mvp_temp/docs/harness/TEAM_GUIDE.md)에서 확인한다.

저장소 루트에서 `python -m harness status`, `python -m harness providers`로 자동 작업을 관리합니다.
[작업 등록·worker·복구·검토·승인 명령](outputs/budongi_mvp_temp/docs/harness/CLI_OPERATIONS.md)과
[구현·검증 결과](outputs/budongi_mvp_temp/docs/harness/CLI_IMPLEMENTATION_REPORT.md)를 참고하세요.

현재 GMS 최소 보존은1,000이고 검증·승인 후 로컬 오토커밋이 활성화됐습니다.
[최신 GMS·자동커밋 운영/호환성](outputs/budongi_mvp_temp/docs/harness/OPERATIONS_UPDATE_20261015.md)을 따릅니다.

## 작업별 Git 자동 저장

[Git 자동 저장 운영](docs/git-lifecycle.md)을 따른다. 작업 시작 시 전용 branch를 만들고,
메인이 확정한 단계의 snapshot은 Git 전담 서브에이전트가 별도 작업 공간에서 commit/push한다.
로컬 진입점은 `python -m harness git --help`다. 정책은 `tooling/git-lifecycle.json`이며
현재 KAN-29 전달은 main 병합 없이 자동화 전용 branch를 남긴다.
