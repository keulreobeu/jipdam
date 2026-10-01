# Task — 집담 이름과 GitHub 게시

Status: Complete. 첫 커밋 `85faaf4`를 `main`에 게시했고 GitHub CI의 4개 조합이 모두 통과했다.

사용자가 집담(Jipdam)을 선택하고 `https://github.com/keulreobeu/jipdam.git`에 첫 게시를 요청했다.

- 서비스와 문서의 이름은 집담(Jipdam), Python 배포 패키지·새 CLI는 `jipdam`으로 정한다.
- 프로젝트 전용 스킬은 `jipdam-workflow`로 통일한다.
- 기존 `budongi` Python 모듈·CLI, 작업 폴더·데이터 ID는 호환성을 위해 유지한다.
- 고정 gstack 설치와 모델 없는 검증을 확인하고 공유 대상만 첫 커밋에 포함한다.
- 기존 원격 커밋을 덮어쓰지 않고 `main`에 일반 push한다. 모델·DB·API 키·로컬 runtime은 제외한다.
- GitHub의 Ubuntu/Windows CI 결과를 확인한다. 실제 데이터·Golden 평가 보류는 유지한다.

관련 계약: `outputs/budongi_mvp_temp/docs/specs/00_project_spec.md`, `docs/team_environment_spec.md`.

로컬 검증: 제품 테스트 22개·설치 도구 테스트 3개, 합성 조회, 고정 gstack과 스킬 57개, 문서 상대 링크, 별도 환경의 `jipdam` 패키지 설치 및 두 CLI `--help` 확인이 통과했다.

원격 검증: [첫 게시 CI](https://github.com/keulreobeu/jipdam/actions/runs/36810256416)에서 Ubuntu/Windows × Python 3.11/3.12의 모델 없는 검증이 모두 성공했다. 실제 모델·데이터 평가는 포함하지 않는다.
