# 팀 환경 검증 기록

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
