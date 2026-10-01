# 집담 (Jipdam)

출처와 기준 시점을 추적하는 부동산 정보 질의 프로젝트다. Python·SQLite 기반의 스냅샷 적재, 검증된 Data Tool 3개, 로컬 모델 Tool Calling 경로를 개발한다. 현재 구현과 향후 계획은 [Project Spec](outputs/budongi_mvp_temp/docs/specs/00_project_spec.md)에서 구분한다.

팀원은 **Codex, Claude Code, Antigravity 중 익숙한 도구**로 작업할 수 있다. 같은 코드·Spec·ADR·Task·검증 명령을 공유한다. 전체 gstack의 자동 등록은 현재 Codex용으로 구성되어 있다.

## 1. 저장소 받기

```sh
git clone https://github.com/keulreobeu/jipdam.git
cd jipdam
```

선택한 AI 도구에서 **이 README가 있는 저장소 루트**를 작업 폴더로 연다. 애플리케이션은 `outputs/budongi_mvp_temp/`에 있다. 각자 AI 도구에 로그인하고 자신의 계정·실행 권한을 사용한다.

| 작업 | 필요한 도구 |
| --- | --- |
| clone·브랜치·커밋 | Git |
| 코드 수정·테스트·합성 데이터 조회 | Python 3.11 이상 |
| Codex용 전체 gstack | Python + Git + Bun 1.3.14 이상 + Node.js 22 이상 + Bash |
| Windows의 전체 gstack | Git for Windows에 포함된 Git Bash |
| 컨테이너 실행 | Docker Engine/Desktop + Compose, 선택 사항 |
| 로컬 모델 답변 시험 | Ollama와 모델, 선택 사항 |

설치 안내: [Python](https://www.python.org/downloads/), [Git](https://git-scm.com/downloads), [Bun](https://bun.sh/docs/installation), [Node.js](https://nodejs.org/en/download).

## 2. 공통 환경 확인

AI 도구와 관계없이 저장소 루트의 터미널에서 실행한다.

```sh
python -X utf8 scripts/bootstrap.py --app-only
```

Linux/macOS에서 `python` 명령이 없으면 `python3`를 사용한다. 이 검증은 Python 표준 라이브러리만 사용하며 네트워크·API 키·모델·GPU 없이 제품 테스트, 설치 도구 테스트, 합성 스냅샷 조회를 확인한다.

CLI를 설치해서 개발하려면 가상 환경을 만든다.

Windows PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install -e outputs/budongi_mvp_temp
jipdam --help
```

Linux/macOS Bash:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e outputs/budongi_mvp_temp
jipdam --help
```

패키지 설치 시에는 빌드 의존성을 다운로드할 수 있다. 모델 없이 개발할 때는 첫 번째 `--app-only` 검증만으로도 시작할 수 있다. 제품 명령·Docker·Ollama 사용법은 [애플리케이션 README](outputs/budongi_mvp_temp/README.md)에 있다.

## 3. 사용하는 AI 도구 연결

| 도구 | 프로젝트 시작 | 공통 규칙 연결 | 현재 gstack 범위 |
| --- | --- | --- | --- |
| Codex | 저장소 루트를 프로젝트로 열기 | 루트·제품 `AGENTS.md` | 전체 설치 및 Codex 스킬 등록 검증 |
| Claude Code | 루트 터미널에서 `claude` 실행 | `CLAUDE.md`가 루트·제품 `AGENTS.md` import | 공통 작업 절차 사용; Claude 네이티브 gstack 등록은 제공하지 않음 |
| Antigravity | 저장소 루트를 workspace로 열기 | `AGENTS.md`를 프로젝트 규칙으로 사용 | 공통 작업 절차 사용; 생성된 Codex용 gstack의 실행 호환성은 미검증 |

### Codex

[루트 AGENTS.md](AGENTS.md)와 [제품 AGENTS.md](outputs/budongi_mvp_temp/AGENTS.md)를 기준으로 작업한다. 전체 gstack을 사용할 때는 다음 절의 설치를 진행한다. 생성 스킬은 clone에 포함되지 않으므로 첫 설치가 필요하다.

### Claude Code

Claude Code를 설치하고 로그인한 뒤 저장소 루트에서 시작한다.

```sh
claude
```

저장소의 [CLAUDE.md](CLAUDE.md)는 공통 `AGENTS.md`를 import한다. 제품 규칙을 별도로 복사해 유지하지 않는다. 세션에서 `/memory`로 규칙이 로드됐는지 확인하고, 빠졌다면 아래 공통 첫 프롬프트로 파일을 직접 읽게 한다. import 방식은 [Claude Code 공식 안내](https://code.claude.com/docs/en/memory#import-additional-files)에 따른다.

이 저장소의 bootstrap은 `.claude/skills/`에 gstack을 등록하지 않는다. Codex의 `$gstack-*` 호출을 Claude Code의 slash command로 가정하지 않는다. 일반 코드 작업·검증은 공통 명령으로 수행한다.

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

## 4. Codex용 전체 gstack 설치

팀 공통 개발에 필요한 Python 검증과 별도로, 전체 기획·리뷰·QA 스킬을 Codex에 등록하는 선택 설치다.

```sh
python -X utf8 scripts/bootstrap.py
```

Windows에서는 `./scripts/setup-gstack.ps1`, Linux/macOS에서는 `bash scripts/setup-gstack.sh`도 같은 설치를 실행한다. 고정된 commit의 gstack, Bun 의존성, Chromium을 다운로드하며 개인의 전역 Codex 설정을 변경하지 않는다.

설치가 끝나면 gstack 56개와 `jipdam-workflow` 1개가 등록된다. Codex에서 목록이 갱신되지 않으면 프로젝트를 다시 연다. 단순 코드 수정 때 전체 설치를 반복할 필요는 없다.

```sh
python -X utf8 scripts/verify_environment.py --gstack --browser
python -X utf8 scripts/register_gstack.py --check
```

브라우저 검증은 빈 테스트 화면에서 실행한다. 원본·fixture·다른 host용 생성본은 스킬 탐색 경로 밖에 둔다. Claude Code·Antigravity용 네이티브 gstack 연결을 추가할 때는 host별 등록·runtime·동작 검증을 함께 구현한다. 현재 설치 스크립트에 없는 `--host` 옵션을 임의로 붙이지 않는다. 상세 설치·확장 방법은 [gstack 안내](docs/gstack.md)에 있다.

## 5. 함께 작업하는 규칙

- 확정 요구는 Spec, 중요한 결정 이유는 ADR, 실행 단위와 결과는 Task에 기록한다. AI의 계획·리뷰 결과는 초안이다.
- 각 팀원은 별도 clone 또는 브랜치에서 작업하고 PR로 변경을 공유한다. 다른 AI 도구끼리도 같은 파일의 동시 수정을 피한다.
- 모델에 SQL·DB 직접 접근 권한을 주지 않는다. 허용된 Data Tool·인자 검증·호출 제한·출처 추적을 유지한다.
- 현재 실제 데이터 수집·단지 매칭은 보류 중이다. 실제 검수 스냅샷·사람 검수 Golden 없이 정확도나 Phase 완료를 주장하지 않는다.
- 계정 정보·API 키·모델·DB·원천 데이터·로그·로컬 runtime은 Git에 넣지 않는다. 개인 AI 설정은 팀 공통 규칙과 분리한다.

기본 검증은 모든 도구에서 같다.

```sh
python -X utf8 scripts/verify_environment.py
```

GitHub CI는 Ubuntu/Windows × Python 3.11/3.12의 모델 없는 검증을 실행한다. [팀 환경 검증 기록](docs/team_environment_validation.md)은 전체 gstack의 Windows 검증과 실제 모델·데이터 평가의 미완료 범위를 구분한다. Claude Code·Antigravity의 실제 세션 동작은 이 PC에서 검증하지 않았다.

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
