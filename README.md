# 집담 (Jipdam) — 팀 개발 워크스페이스

Python·SQLite 기반 부동산 정보 Tool Calling 프로젝트와 프로젝트 전용 Codex/gstack 작업 환경이다. 애플리케이션은 [`outputs/budongi_mvp_temp/`](outputs/budongi_mvp_temp/)에서 개발한다. `CURRENT`와 향후 도입할 `TARGET`은 [Project Spec](outputs/budongi_mvp_temp/docs/specs/00_project_spec.md)에서 구분한다.

## 처음 받은 팀원

다음 명령으로 clone한 뒤 **이 README가 있는 루트를 Codex 프로젝트로 연다**.

```powershell
git clone https://github.com/keulreobeu/jipdam.git
cd jipdam
```
 Codex 로그인은 각자의 계정으로 한다. API 키·로그인 정보·모델 파일을 저장소에 넣지 않는다.

| 작업 범위 | 필요한 도구 |
| --- | --- |
| 코드·테스트·합성 데이터 조회 | Python 3.11 이상 |
| 전체 gstack | 위 Python + Git + Bun 1.3.14 이상 + Node.js 22 이상 + Bash |
| Windows 전체 gstack | Git for Windows에 포함된 Git Bash 사용 |
| 컨테이너 실행 | Docker Engine/Desktop + Compose |
| 모델 답변 시험 | Ollama와 로컬 모델; 선택 사항 |

전체 설치 전 각 도구의 공식 설치 안내를 참고한다: [Python](https://www.python.org/downloads/), [Git](https://git-scm.com/downloads), [Bun](https://bun.sh/docs/installation), [Node.js](https://nodejs.org/en/download). 설치 스크립트는 누락된 도구와 지원 버전을 검사한다.

### 모델 없이 시작

루트에서 실행한다. 네트워크, API 키, 모델 다운로드 없이 제품 테스트·설치 도구 테스트·합성 스냅샷 조회를 확인한다.

```powershell
python -X utf8 scripts/bootstrap.py --app-only
```

Linux/macOS에서는 위 명령의 `python` 대신 `python3`를 사용한다. 개발용 가상 환경이 필요하면 `python -m venv .venv` 후 활성화하고 아래 명령으로 CLI를 설치할 수 있다.

```powershell
python -m pip install -e outputs/budongi_mvp_temp
jipdam --help
```

### Codex와 전체 gstack 설치

처음 설치하면 고정된 commit의 원본, Bun 의존성, Chromium을 다운로드한다. 개인의 전역 Codex 설정·스킬 대신 이 프로젝트에 등록한다.

```powershell
python -X utf8 scripts/bootstrap.py
# Windows에서 기존 진입점도 사용 가능
./scripts/setup-gstack.ps1
```

Linux/macOS:

```bash
bash scripts/setup-gstack.sh
```

설치가 끝나면 gstack 56개와 `jipdam-workflow` 1개가 등록된다. Codex의 다음 턴에서 사용하고 목록이 갱신되지 않으면 프로젝트를 다시 연다. 원본과 다른 host용 생성본은 스킬 탐색 경로 밖에 있으므로 테스트 fixture 스킬은 노출되지 않는다.

### 이후 검증

```powershell
python -X utf8 scripts/verify_environment.py
python -X utf8 scripts/verify_environment.py --gstack --browser
python -X utf8 scripts/register_gstack.py --check
```

첫 명령은 모델 없는 기본 검증, 두 번째는 고정 버전·57개 스킬·브라우저까지 확인한다. 브라우저 검사는 빈 테스트 화면에서만 실행하고 자체 서버를 종료한다.

## 개발할 때

- [루트 AGENTS.md](AGENTS.md)와 [제품 AGENTS.md](outputs/budongi_mvp_temp/AGENTS.md)를 따른다. 확정 Spec → 필요 시 ADR → Task → 구현 → 검사 → 문서 동기화 순서다.
- 집담 전용 스킬은 [jipdam-workflow](.agents/skills/jipdam-workflow/SKILL.md)에서 팀이 함께 개선한다. 생성된 gstack 스킬은 직접 편집하지 않는다.
- gstack은 [고정 버전](tooling/gstack.lock.json)에서 생성한다. 변경·업그레이드 절차는 [gstack 안내](docs/gstack.md)에 있다.
- 현재 실제 데이터 수집·단지 매칭은 보류 상태다. 합성 데이터 시험을 실제 부동산 정확도나 Phase 완료로 보고하지 않는다.
- 제품 실행·Ollama·Docker 사용법은 [애플리케이션 README](outputs/budongi_mvp_temp/README.md)에 있다. 모델 없는 기본 개발에는 GPU가 필요하지 않다.

## 저장소에 포함되는 것

코드·테스트·Spec·ADR·Task·Codex 지침·집담 전용 스킬·설치/검증 스크립트·gstack commit lock을 공유한다. `.local_runtime/`, `.venv/`, 모델·DB·원천 데이터·로그·API 키·생성된 gstack 설치본과 과거 source archive는 Git에서 제외한다.

GitHub 기본 CI는 Ubuntu와 Windows에서 Python 3.11/3.12의 모델 없는 검증을 실행한다. 전체 gstack, 모델, 실제 데이터 평가는 로컬 또는 별도 작업에서 확인한다. 현재 검증 범위는 [팀 환경 검증 기록](docs/team_environment_validation.md)에 기록한다.

## 이름과 저장소

서비스 이름은 **집담(Jipdam)**, GitHub 저장소는 [keulreobeu/jipdam](https://github.com/keulreobeu/jipdam)이다. 설치 패키지와 새 CLI 명령은 `jipdam`이다. 기존 코드의 `budongi` Python 모듈·CLI, `outputs/budongi_mvp_temp/` 경로와 데이터 ID는 호환성을 위해 유지한다.

공유 파일만 ZIP으로 준비하려면 `python -X utf8 scripts/export_team.py`를 실행한다. Git의 추적/제외 규칙을 적용해 `.local_runtime/team-share/jipdam-team-source.zip`을 생성한다.
