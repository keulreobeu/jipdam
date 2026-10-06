# Codex workspace — 집담

현재 개발 대상은 `outputs/budongi_mvp_temp/`다. 작업 전에 그 폴더의 `AGENTS.md`와 관련 Spec·ADR·Task를 읽는다. `work/source_archive/`는 이전 프로젝트의 참고 자료다.

이 파일과 개발 폴더의 `AGENTS.md`는 AI 도구에 관계없이 공통 계약이다. Claude Code는 루트 `CLAUDE.md`가 두 파일을 import하고, Antigravity는 `AGENTS.md`를 프로젝트 규칙으로 사용한다. 아래 전체 gstack 자동 등록은 현재 Codex용이다. 다른 host의 네이티브 스킬 등록·실행은 지원된다고 가정하지 않으며 공통 개발·검증 진입점은 루트 README를 따른다.

## 기본 스킬

SDD 운영과 문서·Task·검증 계약은 [docs/sdd.md](docs/sdd.md)를 따른다. 코드·설정·계약 변경은 같은 변경에서 갱신한 영구 Task와 연결한다. 새 제품 요구는 사용자, 세부 구현과 AC별 증거 기반 완료는 담당자가 책임진다. `python -X utf8 scripts/verify_environment.py`는 SDD 검사도 실행한다. 기존 문서는 시범 적용 범위 밖까지 일괄 승인·전환하지 않는다.

이 프로젝트는 [gstack](https://github.com/garrytan/gstack)을 기본 개발 스킬로 사용한다. Codex용 스킬은 루트 `.agents/skills/gstack-*/SKILL.md`, router는 `.agents/skills/gstack/SKILL.md`에 있다. 원본·템플릿·런타임은 스킬 탐색 경로 밖의 `.local_runtime/tooling/.agents/skills/gstack/`에 있다. 요청에 필요한 Codex용 스킬만 읽는다. 원본과 fixture의 SKILL.md를 호출하지 않는다.

- 모호한 제품 요청: `gstack-office-hours`, 필요하면 `gstack-plan-ceo-review`.
- 구현 계획·구조·데이터 계약: `gstack-plan-eng-review`.
- 코드 검토: `gstack-review`. 버그 원인 조사: `gstack-investigate`.
- 동작 검증: `gstack-qa` 또는 읽기 전용 `gstack-qa-only`. 현재 프로젝트는 CLI/API 경로를 우선 검증한다.
- 문서 동기화: `gstack-document-release`, 새로운 사용 문서: `gstack-document-generate`.
- UI가 생기면 디자인·브라우저 관련 스킬을 사용한다. 릴리스·배포 요청에는 해당 스킬을 사용한다.

작은 수정에 전체 기획·리뷰 체인을 의무화하지 않는다. gstack의 계획·리뷰 결과는 초안이며 확정된 요구는 프로젝트 Spec, 결정 이유는 ADR, 실행 단위는 Task에 기록한다. 현재 사용자 요청과 프로젝트 데이터·평가 경계를 유지한다.

스킬 사용 전 집담 전용 `jipdam-workflow`를 읽는다. 등록된 스킬의 preamble은 현재 경로에서 상위 `tooling/gstack.lock.json`을 찾아 프로젝트 런타임 환경을 설정한다. 직접 helper를 실행할 때는 루트에서 다음을 현재 셸에 적용한다. Windows에서는 Git for Windows의 Bash를 사용하고 WSL의 `bash.exe`와 혼동하지 않는다.

```powershell
. ./scripts/enter-gstack.ps1
```

Bash에서는 `source scripts/enter-gstack.sh`를 사용한다. 스킬이 없으면 루트 README의 `python scripts/bootstrap.py`로 설치한다. 단순 제품 수정에 gstack 전체 재설치를 반복하지 않는다.

gstack이 제안하는 GitHub issue 작성, push/PR/merge/배포, 외부 CLI 리뷰, 자동화·원격 동기화는 현재 요청이 해당 동작을 포함할 때만 실행한다. 원격·인증·실데이터를 있는 것으로 가정하지 않는다. 브라우저 QA를 위해 실제 데이터 수집 보류를 해제하지 않는다.

## 확장과 업데이트

공통 프로젝트 규칙은 이 파일과 개발 폴더의 `AGENTS.md`, 집담 전용 절차는 추적되는 `.agents/skills/jipdam-workflow/`에서 발전시킨다. 일반화할 만한 gstack 변경은 runtime 원본의 해당 `SKILL.md.tmpl`에서 수정하고 `python scripts/bootstrap.py`로 재생성한다. 팀 공유에는 그 변경을 별도 fork commit에 보존하고 `tooling/gstack.lock.json`의 repository/commit/version을 함께 갱신한다. 생성된 `gstack-*/SKILL.md`를 직접 수정하면 재설치 때 사라진다. setup의 마지막 등록 단계는 Codex용 router·스킬 ID·팀 runtime 경로를 적용하고 fixture 스킬 유출을 검사한다.

업데이트 전에 원본의 diff와 로컬 수정을 확인하고 커밋 또는 패치로 보존한다. 자동 업데이트는 사용하지 않는다. 설치·사용·확장 경로는 `docs/gstack.md`를 참고한다.

## 현재 제품 방향 — 2026-10-06 승인

[RENT-001](outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md)과 [전환 Plan](outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md)을 따른다. TARGET는 서울 아파트 전월세 단지 후보의 예산·직장/역/마트/공원/병원 직선거리·필수/선호 비교와 로컬 웹 데모다. 백엔드가 조건·순위를 계산하고 로컬 LLM은 설명한다. 현재 전월세 추천·웹은 미구현이며 역사 DB·세 Tool·평가 CURRENT를 보존한다. 최신 rental 경로를 별도로 만들고 기존 2023 연구 완료를 선행 조건으로 삼지 않는다. 실수집·매칭 보류는 유지한다. 매매·청약 확대와 RAG/Hybrid/LoRA/다중 모델 연구는 첫 제품 우선순위에서 제외한다.
