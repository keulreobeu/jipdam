# 팀 환경 검증 기록

## Claude gstack 2026-10-20

See [TASK-CLAUDE-GSTACK-001](tasks/claude-gstack-support.md). The pinned source `96764e80a641e28141ec8297223768029f5bf483` rendered 56 Claude host skills. `register_claude_gstack.py` installed them under the ignored project `.claude/skills/` path; the discovery check confirmed 56 unique names matching their folders. Section links, helper commands, and state paths point into `.local_runtime/`.

Commands run:

```powershell
bun run scripts/gen-skill-docs.ts --host claude --out-dir .local_runtime/gstack/render/claude
python -X utf8 scripts/register_claude_gstack.py --render .local_runtime/gstack/render/claude
python -X utf8 scripts/register_claude_gstack.py --check
```

The registration code only writes `.claude/skills/gstack*` and does not open or modify Claude global settings. Existing skill names without this install's ownership marker or upstream generated banner are rejected. `CLAUDE.md` says to reopen the project before using `/gstack-*`. A live Claude Code session was not available for invocation smoke; this confirms registration and discovery, not host permissions. Git commits/pushes continue to follow the user's Claude Code permission settings and project approval rules.

기준: 2026-10-01. 제품 데이터·모델 평가와 설치 검증을 구분한다.

## 현재 확인

- Windows: Python 3.12, Bun 1.3.14, Node.js 24.18.0, Git for Windows.
- 제품 unittest 22개, 설치 도구 unittest 3개 통과.
- 모델 없는 합성 스냅샷 생성·doctor·Data Tool 조회 통과. 합성 스냅샷은 실제 평가 준비 완료로 표시하지 않는다.
- runtime 경로로 source를 이동하고 Codex용 57개 고유 manifest만 등록했다. 원본·fixture·다른 host용 스킬은 프로젝트 탐색 경로 밖에 있다.
- gstack browse의 빈 화면 탐색·클릭·DOM 조회·스크린샷·서버 종료를 확인했다.

## 새 checkout 검증

이름 변경 전 공유 파일만 export한 뒤 임시 Git 저장소에 baseline commit을 만들고 `clone with spaces`라는 새 경로에 clone했다. clone 시작 시에는 `.local_runtime/`이 없었고 프로젝트 스킬은 당시 `budongi-workflow` 1개뿐이었다. 현재 공유 스킬의 이름은 `jipdam-workflow`다.

그곳에서 `python -X utf8 scripts/bootstrap.py`를 실행해 다음을 확인했다.

- exact commit fetch·checkout과 `VERSION` 일치.
- Bun frozen lock 설치, 공식 전체 setup 완료, 설치 전후 Bun lock SHA-256 동일.
- 제품 테스트 22개와 등록 도구 테스트 3개 통과.
- 합성 스냅샷 생성, `doctor`의 synthetic-only/실측 준비 미완료 판정, `get_apartment_detail` 조회 통과.
- 57개의 고유하고 중첩되지 않은 프로젝트 스킬 manifest 확인.
- Chromium 시작, 빈 화면의 테스트 버튼 클릭, DOM 값 확인, 스크린샷 생성, 서버 종료 통과.
- bootstrap 최종 exit 0.

당시 소스 공유 대상은 70개 파일이며 원본 gstack checkout, 생성 스킬, node_modules, 모델, DB, 원천 데이터, 캐시, 로그, `.env`와 Git metadata를 제외했다. 검증 후 기록과 줄바꿈 속성을 갱신했으며, 실행 코드의 후속 변경은 초기 빈 Git 저장소의 불필요한 rev-parse 진단 출력을 억제한 것뿐이었다.

원본을 옮긴 현재 workspace에서도 같은 25개 테스트·합성 조회·57개 스킬·브라우저 smoke를 확인했다. 하위 애플리케이션 폴더에서 등록된 preamble의 runtime 경로 찾기를 파일로 실행해 확인했다. Windows Codex sandbox의 인라인 Bash probe는 멈춰 종료했고, 실제 설치와 동일한 실행 권한의 Git Bash 파일 실행은 통과했다.

## 한계

Windows 이외 플랫폼의 전체 gstack 설치와 실제 모델/데이터 평가는 이 기록의 통과 범위에 포함하지 않는다. CSO 네이티브 helper는 현재 Windows C++ Build Tools가 없어 사용할 수 없다.

## 집담 이름 변경 후 검증

2026-10-01, 서비스 이름을 집담(Jipdam)으로 확정했다. 배포 패키지와 새 CLI는 `jipdam`, 프로젝트 스킬은 `jipdam-workflow`다. 기존 Python 모듈·CLI·작업 폴더·데이터 ID는 유지한다.

제품 테스트 22개·설치 도구 테스트 3개, 모델 없는 합성 조회, 고정 gstack·고유 스킬 57개, 문서 상대 링크 검사를 통과했다. 별도 Python 환경에서 패키지 설치와 `jipdam --help`, `budongi --help`를 모두 확인했다. 집담 첫 게시의 공유 대상은 71개 파일이었다.

공개 게시 전 소스 검사에서 HIGH 항목은 0개였다. 나머지 탐지 항목은 직접 확인한 gstack 버전, 금액·공공 식별번호, 기본 로컬 모델 endpoint, 예시 파일명과 SHA-256 계산 코드였다. 실제 인증키나 개인 연락처는 포함하지 않는다. GitHub 게시와 Actions 결과는 저장소에서 확인한다.

## GitHub 게시와 CI

2026-10-01, `85faaf4`를 [keulreobeu/jipdam](https://github.com/keulreobeu/jipdam)의 `main`에 일반 push하고 로컬·원격 SHA 일치를 확인했다. [첫 CI 실행](https://github.com/keulreobeu/jipdam/actions/runs/36810256416)은 Ubuntu/Windows × Python 3.11/3.12의 4개 job이 모두 성공했다. 각 job은 `python -X utf8 scripts/bootstrap.py --app-only`로 제품·설치 도구 테스트 및 합성 CLI 검증을 수행한다. 전체 gstack·브라우저·모델·실데이터 검증은 이 CI의 범위가 아니다.

## Environment repair 2026-10-06

[TASK-ENV-001](tasks/environment-repair-20261006.md)의 로컬 환경 후속 검증이다. 이전 검수는 새 Windows PATH와 일반 Git Bash에서 bunx가 없음을 확인했다. Bun 1.4.2는 있었고 Chromium은 별도 Playwright CLI로 설치되어 있었다.

### 변경과 재현

저장된 Windows Machine/User PATH를 읽은 셸에서 기존 Bun의 `bun completions` 설치 마무리 명령을 실행했다. 공식 [Windows 설치 스크립트](https://bun.com/install.ps1)는 이 명령으로 bunx 연결을 생성한다. 이번 실행은 `BUN_NO_INSTALL_COMPLETIONS=1`, `IS_BUN_AUTO_UPDATE=1`을 해당 프로세스에만 설정했고, 기존 설치 폴더에 bunx.exe가 생성된 뒤 두 환경 변수를 제거했다. 전역 Codex 설정이나 PowerShell 프로필은 편집하지 않았다. PowerShell 자동완성 미지원 안내가 출력됐으나 명령은 exit 0이고 bunx 연결과 실행은 확인됐다.

- 원래 실패했던 새 Windows PATH의 bunx 확인: 수정 전 exit 127, 수정 후 `bunx --version`이 1.4.2와 exit 0을 반환했다.
- 저장된 PATH를 읽은 일반 Git Bash에서도 bunx 경로와 1.4.2 실행을 확인했다.
- 프로젝트 runtime 원본 폴더에서 `bunx playwright install chromium`이 exit 0, `bunx --no-install playwright --version`이 1.62.1을 반환했다. 기존 프로젝트-local Chromium을 사용했다.

### 가상환경과 CLI

루트에서 `python -m venv .venv`, `.venv/Scripts/python.exe -m pip install --no-cache-dir -e outputs/budongi_mvp_temp`를 실행했다. Python은 3.12.10, 설치된 jipdam은 0.1.0이다. 패키지 빌드 의존성은 가상환경 설치 절차에서 내려받았다.

`.venv/Scripts/jipdam.exe --help`, `.venv/Scripts/budongi.exe --help`가 정상 help와 exit 0을 반환했고 `.venv/Scripts/python.exe -m pip check`도 `No broken requirements found`와 exit 0이었다. 새 Git Bash에서 `.venv/Scripts/activate`를 source한 뒤 두 CLI가 `.venv/Scripts/`에서 선택되어 실행되는 것도 확인했다.

PowerShell에서 활성화 없이도 다음 명령으로 설치한 CLI를 사용할 수 있다.

```powershell
.venv/Scripts/jipdam.exe --help
```

### 최종 로컬 검증

`.venv/Scripts/python.exe -X utf8 scripts/verify_environment.py --gstack --browser`가 exit 0이었다.

- SDD 구조·변경 경로 Task 연결 통과: 등록 Task 3개.
- 제품 테스트 28개 및 SDD·설치 테스트 18개 통과.
- 합성 스냅샷 doctor·Data Tool 조회 통과; 실측 평가 준비 완료로 판정하지 않았다.
- 고정 gstack commit 및 고유·중첩 없는 manifest 57개 확인.
- Chromium 빈 화면 탐색·클릭·DOM 조회·스크린샷·서버 종료 통과.

원본 capture 001~003은 Git 제외 `.local_runtime/gstack/qa-reports/environment-repair-20261006T045305Z/`에 보존한다. 사용자별 환경·원본 로그는 공유 Git 대상에 포함하지 않는다.

이 기록은 현재 Windows의 기본 개발·설치형 CLI·Codex gstack 실행 범위다. CSO C++ 도구 체인, Docker daemon·Ollama·모델 및 실제 데이터·Golden 평가를 완료했다고 판정하지 않는다.

## 모델 없는 CI 앱 의존성 보완 — 2026-10-07

전월세·자격증명 기능 PR #2의 최초 CI에서 Ubuntu/Windows 및 Python 3.11/3.12 job이 제품 모듈을 가져올 때 `cryptography` 누락으로 실패했다. 원인은 `pyproject.toml`에는 앱 의존성이 선언됐지만 CI workflow가 editable 앱 패키지를 설치하지 않은 것이었다. [TASK-CI-DEPS-001](tasks/ci-python-dependencies.md)에서 추적한다.

workflow에 `python -m pip install -e outputs/budongi_mvp_temp` 단계를 추가해 검증 전에 앱 런타임 의존성을 설치한다. 루트 README도 새 checkout에서 패키지를 설치한 뒤 `--app-only`를 실행하도록 고쳤다.

저장소 `.local_runtime/` 아래 임시 가상환경을 새로 만들고 workflow와 같은 editable 설치를 실행했다. `cryptography 50.0.2`와 그 의존성이 설치된 뒤 `python -X utf8 scripts/bootstrap.py --app-only`가 통과했다. 제품 테스트 82개, 팀/SDD 테스트 18개, 합성 CLI smoke가 모두 성공했다. `python -X utf8 scripts/check_sdd.py --base origin/main`도 통과했다. PR #2 수정 후 [GitHub Actions run 37599609319](https://github.com/keulreobeu/jipdam/actions/runs/37599609319)에서 네 OS/Python 조합이 모두 성공했다.

## Environment setup 2026-10-12

[TASK-ENV-002](tasks/environment-setup-20261012.md)의 현재 PC 구성 결과다. Python 3.12.10, Node.js 24.18.0, Git 2.55.0.windows.2 및 기존 `.venv`의 editable jipdam 0.1.0·cryptography 50.0.2를 확인했다. `pip check`와 두 CLI help가 정상이다.

공식 Bun 1.3.14 Windows x64 ZIP과 같은 release의 SHASUMS256.txt를 내려받아 SHA-256 `0a0620930b6675d7ba440e81f4e0e00d3cfbe096c4b140d3fff02205e9e18922` 일치를 확인했다. `.local_runtime/bun/bin/`에 bun.exe와 bunx.exe hard link를 설치하고 둘 다 1.3.14 실행을 확인했다. 사용자 전역 PATH·PowerShell 프로필·Codex 설정은 편집하지 않았다.

고정 gstack commit `96764e80a641e28141ec8297223768029f5bf483`의 전체 bootstrap이 exit 0이었다. frozen Bun lock 설치·setup 전후 lock 해시 확인과 고유 스킬 57개 등록을 통과했다. Chromium/Headless Shell 151.0.7922.34, Playwright browser revision 1234를 프로젝트 로컬에 설치했다. setup은 일부 대형 스킬의 토큰 상한 경고를 출력했지만 설치·manifest·실행 검증은 성공했다.

최종 검증 결과:

- 제품 unittest 82개, 팀/SDD unittest 18개 모두 통과. 첫 sandbox의 app-only 검증에서는 native WinCred round-trip 1개가 로그온 세션 부재로 skipped였으나, 최종 전체 설치 실행에서는 같은 합성 테스트도 통과했다.
- 합성 역사 스냅샷 doctor·Data Tool 조회 통과. 실제 평가 준비 완료로 판정하지 않는다.
- Chromium 빈 화면 탐색·버튼 클릭·DOM 값·스크린샷·서버 종료 통과.
- `register_gstack.py --check`: 고유·중첩 없는 스킬 57개.
- 별도 합성 rental-demo CLI: 후보 2곳, status ok. 추천 전후 DB SHA-256 동일. 없는 DB는 exit 3·data_unavailable이며 DB 파일을 만들지 않는다.
- `check_sdd.py --base origin/main` 통과. GitHub CI를 새로 실행하거나 원격 게시하지 않았다.

현재 PC의 PowerShell에서는 저장소 루트에서 다음을 실행하면 Python·jipdam·budongi와 Bun·bunx가 로컬 설치 경로로 선택된다. UTF-8 출력과 gstack runtime 환경도 함께 설정한다. 이 스크립트는 개인 runtime 산출물이므로 Git에 포함하지 않는다.

```powershell
. ./.local_runtime/activate.ps1
jipdam --help
python -X utf8 scripts/verify_environment.py
```

추가 `gstack-qa-only` 보고서의 첫 직접 CLI 증거 캡처는 stdout이 UTF-8이 아니어서 incomplete였다. 해당 report-only 실행을 종료한 뒤 환경 작업에서 활성화 스크립트에 `PYTHONUTF8=1`을 추가했다. 동일 추천 명령을 같은 봉인 DB로 다시 실행해 complete 캡처, UTF-8 JSON·후보 2곳 및 DB 불변을 확인했다. 원래 실패와 후속 복구 증거는 분리해 보존했다. 보고서: `.local_runtime/gstack/qa-reports/environment-setup-20261012/`, 복구 capture: `.local_runtime/gstack/qa-reports/environment-setup-20261012-repair/`.

Git Bash의 `--noprofile --norc` helper 호출은 셸 내부 PATH에 Unix 도구 경로가 있어야 한다. 단순 Windows PATH 전달에서는 dirname/tr/sed를 찾지 못했으며, 다음 방식으로 skill-start/end가 정상 동작했다.

```powershell
. ./.local_runtime/activate.ps1
& 'C:/Program Files/Git/bin/bash.exe' --noprofile --norc -c 'export PATH="/usr/bin:/bin:$PATH"; "$GSTACK_ROOT/bin/gstack-config" get telemetry'
```

전체 설치 로그는 `.local_runtime/environment-setup-20261012-full.log`, 화면은 `.local_runtime/team-browser-smoke.png`에 있다. telemetry·auto_upgrade·update_check·원격 자동 리뷰는 꺼져 있다. Docker 실행 환경·Ollama·모델·CSO C++ toolchain은 이번 구성 범위 밖이다. 실제 수집·단지 매칭 보류와 GitHub 수집 범위 예약·결과 기록 계약을 유지한다. 합성 검증을 실제 데이터 수집·추천 품질 완료로 해석하지 않는다.

## Host-specific gstack bootstrap 2026-10-20

요청에 따라 GitHub 공유 소스는 Codex·Claude Code 지원을 모두 유지하고, 로컬 전체 설치는 `scripts/bootstrap.py --host codex|claude` 중 하나를 명시하도록 변경했다. 선택 host만 upstream setup/render 및 프로젝트 등록에 사용하고, 다른 host 등록은 현재 lock과 installer marker가 일치할 때만 제거한다. `verify_environment.py --gstack/--browser`도 동일한 `--host`를 받아 선택 host 등록과 반대 host 부재를 확인한다. README·CLAUDE.md·공통 작업 규칙에 host별 명령을 추가했다.

현재 Codex 작업공간은 Codex 전용 등록 상태다. `register_gstack.py`로 고정 source의 Codex skill 56개를 등록하고, marker 검증을 통과한 Claude 등록본 56개를 제거했다. `register_gstack.py --check`와 Codex 전용 `verify_gstack('codex')`에서 프로젝트 skill 58개가 확인됐고, `.claude/skills/`에 gstack 등록이 없음을 확인했다. Python compile, traceability JSON 파싱, `git diff --check`도 통과했다.

전체 bootstrap 재실행은 이 PC의 Bun 1.3.14가 `bun install --frozen-lockfile` 도중 자체 crash해 완료하지 못했다. 첫 호출은 `.local_runtime` Bun 경로가 PATH에 없어 중단됐고, 로컬 Bun 경로를 PATH에 추가한 재시도는 Bun panic으로 종료됐다. 따라서 전체 `bootstrap.py --host codex|claude` 전환은 end-to-end로 확인되지 않았으며, `CLAUDE-GSTACK-001-AC-03`은 pending이다. 이전 검증에서 Claude host renderer와 56개 Claude manifest 등록 자체는 확인했지만, Claude 선택 bootstrap은 다시 실행되지 않았다. 이 작업에서 제품 unittest/전체 verify는 실행하지 않았다.

## Jira task lifecycle 2026-10-20

See [TASK-JIRA-AUTO-001](tasks/jira-task-lifecycle.md) and [JIRA-AUTO-001](specs/jira_task_lifecycle_spec.md). The user approved tracking implementation work in Jira for Codex and Claude Code. Created `KAN-4` before implementing this workflow, added the `agent-codex` label, and moved it to `진행 중`. Codex Atlassian Jira tools were available for issue creation and transition. Claude Code receives the official project-scoped remote MCP endpoint in `.mcp.json`; its first session must run `/mcp` and complete the Atlassian OAuth approval. No token or API key is stored in the repository. Shared AGENTS/Claude instructions and `jipdam-workflow` define create/link-before-edit, in-progress host labeling, verified-only close, unassigned-by-default, and leave-open-on-block/failure behavior.

Focused validation parsed `.mcp.json` and `docs/sdd/traceability.json`, confirmed task scope paths exist and the feature's four AC IDs match the Task, and checked Codex/Claude instructions. `git diff --check` passed (Git noted a line-ending normalization warning on an unrelated dirty file). The full `python -X utf8 scripts/check_sdd.py` check was attempted but reports an unrelated pre-existing invalid verification result in `outputs/budongi_mvp_temp/docs/tasks/rental-real-data.md`; this work did not modify that file. Claude's interactive OAuth has not been performed in this Codex session and is required at first Claude Code use.
