# 팀 프로젝트의 gstack

원본: https://github.com/garrytan/gstack, MIT License. 정확한 repository/commit/version은 `tooling/gstack.lock.json`에서 관리한다. 최초 기준은 `1.91.9.0`, commit `96764e80a641e28141ec8297223768029f5bf483`다.

## 설치 구조

| 경로 | 역할 | Git 공유 |
| --- | --- | --- |
| `tooling/gstack.lock.json` | 원본 repository·commit·버전·필수 도구 범위 | 포함 |
| `.agents/skills/jipdam-workflow/` | 팀이 수정하는 집담 전용 스킬 | 포함 |
| `.agents/skills/gstack/` | Codex용 router manifest·metadata만 | 생성, 제외 |
| `.agents/skills/gstack-*/` | Codex용 manifest·section·metadata | 생성, 제외 |
| `.claude/skills/gstack*/` | Claude Code용 native skill과 보조 파일 | 생성, 제외 |
| `.local_runtime/tooling/.agents/skills/gstack/` | 원본 Git checkout·템플릿·helper·빌드 결과 | 제외 |
| `.local_runtime/gstack/` | gstack 프로젝트 상태·계획·브라우저 로그 | 제외 |
| `.local_runtime/playwright/` | Chromium | 제외 |

원본 checkout의 부모를 `.agents/skills/`로 두는 것은 공식 setup의 로컬 설치 탐지를 위한 것이다. 이 namespace 전체는 runtime 아래에 있어 루트 Codex 스킬 탐색 경로에 들어가지 않는다. upstream이 생성하는 다른 host용 스킬과 fixture도 그곳에 머문다.

## 팀원 설치와 검증

루트 README의 필수 도구를 설치한 뒤 현재 작업 host를 지정해 `python -X utf8 scripts/bootstrap.py --host codex` 또는 `--host claude`를 실행한다. Windows의 `scripts/setup-gstack.ps1`, Linux/macOS의 `bash scripts/setup-gstack.sh`도 인자를 그대로 bootstrap에 전달한다. Python만으로 확인하려면 `--app-only`를 추가한다.

bootstrap은 exact commit을 fetch하고 `VERSION`, 의존성 manifest, Bun lock을 확인한다. `bun install --frozen-lockfile` 뒤 선택한 host에 대해 upstream setup/render를 실행하고 그 host 스킬만 프로젝트 탐색 경로에 등록한다. Codex는 `.agents/skills/`, Claude Code는 `.claude/skills/`를 사용한다. 다른 host로 전환할 때 이 설치기가 만든 이전 gstack 등록본은 marker와 lock을 확인한 뒤 제거한다. 등록본은 전역 host 설정을 바꾸지 않으며 upstream 실행 파일·helper는 runtime checkout에 둔다. 원본·fixture·선택하지 않은 host용 스킬은 복사하지 않는다.

개인 전역 Codex 설정과 전역 스킬은 변경하지 않는다. 공식 setup 자체는 사용자 `~/.gstack/`에 설치 버전·welcome 표시 파일을 남길 수 있다. 프로젝트 상태는 telemetry off, auto-upgrade false, 외부 CLI 자동 리뷰 disabled로 시작한다. 전체 설치는 인터넷과 디스크 공간이 필요하다.

기본 실행 예:

```text
$gstack-office-hours 요구사항을 정리해줘
$gstack-plan-eng-review Tool 계약 변경 계획을 검토해줘
$gstack-review 이번 변경을 검토해줘
$gstack-investigate 테스트 실패 원인을 찾아줘
$gstack-qa CLI의 입력과 반환 결과를 검증해줘
$gstack-document-release 구현과 문서를 맞춰줘
```

등록된 Codex skill preamble은 working directory에서 상위 lock을 찾아 환경을 설정한다. Claude skill의 helper/state 경로는 프로젝트 `.local_runtime/`를 사용한다. helper를 직접 실행할 때는 PowerShell에서 `. ./scripts/enter-gstack.ps1`, Bash에서 `source scripts/enter-gstack.sh`를 사용한다.

설치 확인은 `python -X utf8 scripts/verify_environment.py --gstack --browser --host codex` 또는 host를 `claude`로 지정해 실행한다. Codex 재등록은 `python scripts/register_gstack.py`, Claude 재등록은 upstream renderer를 먼저 실행한 뒤 `python scripts/register_claude_gstack.py`를 사용한다. 형식·중복·nested fixture 검사는 각각 `register_gstack.py --check` 또는 `register_claude_gstack.py --check`로 실행한다. 필요하면 skill-creator의 `quick_validate.py`를 Python UTF-8 모드로 추가 실행한다.

## 팀에서 발전시키기

제품 계약은 Spec·ADR·Task에, 팀 공통 작업 규칙은 AGENTS.md에, 집담 전용 절차는 추적되는 `jipdam-workflow`에 기록한다. 생성된 gstack 스킬은 수정하지 않는다.

gstack 자체를 수정하려면 runtime checkout의 `SKILL.md.tmpl` 또는 section template를 수정한다. 해당 runtime 원본은 공유 대상이 아니므로 팀 배포에는 변경을 fork에 commit한 뒤 lock의 repository/commit/version을 갱신한다. adapter 자체 변경은 `scripts/register_gstack.py`에 남기고 root tests와 실제 등록·브라우저 검증을 수행한다.

업그레이드 전에 source checkout의 status와 diff를 확인해 로컬 수정과 template 변경을 commit/patch로 보존한다. 새 lock의 commit과 기존 source HEAD가 다르면 bootstrap은 자동 reset하지 않고 중단한다. 이전 checkout을 runtime 내 백업 경로로 옮긴 뒤 새 source를 설치하거나, 보존한 작업을 새 commit 위에 직접 이관한다. `/gstack-upgrade`도 이 팀 lock 절차를 따른다.

## 지원 범위

제품 코드·Spec·ADR·Task와 Python 검증 명령은 Codex·Claude Code·Antigravity에서 공통으로 사용한다. 도구별 시작 방법은 루트 README에 있다. Claude Code는 루트 `CLAUDE.md`에서 공통 `AGENTS.md`를 import하고, Antigravity는 공식 프로젝트 규칙의 `AGENTS.md`를 사용한다.

Codex는 `.agents/skills/`, Claude Code는 `.claude/skills/`의 host별 생성본을 사용한다. 두 형식의 소스는 GitHub에 함께 두지만 실제 설치는 명시한 한 host만 대상으로 한다. Claude용 skill은 upstream의 Claude host renderer에서 만들고, helper·state 경로를 프로젝트 runtime으로 연결한다. Anthropic Claude Code의 Git 권한·승인 정책은 host 설정이므로 이 등록은 우회하지 않는다. Antigravity의 생성 Codex manifest·preamble 실행 호환성은 검증하지 않았다.

Windows 전체 설치와 브라우저 smoke를 검증한다. Linux/macOS 진입점을 제공하되 해당 OS의 전체 설치 실행 결과는 별도 검증 대상이다. CSO 네이티브 실행에는 추가 C++ toolchain, iOS에는 기기와 관련 플랫폼, 외부 CLI 리뷰와 원격 동기화에는 별도 인증이 필요하다. 실제 모델·실데이터 정확도는 설치 검증에 포함하지 않는다.

현재 결과는 `docs/team_environment_validation.md`에 기록한다. 이 구성이 실제 모델·Golden·Phase 완료를 의미하지 않는다.
