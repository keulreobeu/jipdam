---
name: jipdam-workflow
description: Apply this project's Spec, ADR, Task, data provenance, and evaluation contracts when using gstack to plan, implement, review, debug, test, or document the Jipdam Python and SQLite system.
---

# 집담에서 gstack 사용

워크스페이스 루트는 이 스킬 경로의 `.agents/skills/` 위 폴더다. 현재 구현은 `outputs/budongi_mvp_temp/`에 있다. 그 폴더의 `AGENTS.md`, `docs/specs/00_project_spec.md`, 관련 기능 Spec·ADR, `docs/tasks/current.md`를 먼저 읽는다. 과거 `work/source_archive/`의 모델·단계·성과를 현재 구현으로 상속하지 않는다.

요청에 맞는 `gstack-*` 스킬을 선택한다. 모호한 요청은 office-hours, 구조와 계약은 plan-eng-review, 변경 검토는 review, 버그는 investigate, 동작 확인은 qa/qa-only, 문서는 document-release/document-generate를 사용한다. 모든 요청에 전체 체인을 실행하지 않는다.

gstack 출력에서 확정된 입력·출력·오류·완료 조건은 기능 Spec에, 구조·데이터 모델·Router/RAG 전략의 채택 이유는 ADR에, 실제 구현 단위와 검사는 Task에 기록한다. 작은 버그나 리팩터링은 관련 Task와 검사로 충분하다. 스킬 내부의 계획·리뷰 상태 파일은 공식 Spec을 대체하지 않는다.

현재 프로젝트의 핵심 검토점:

- 불변 스냅샷, 원 정수·㎡·m, 원천 ID·날짜·파일 해시 보존. 공급액은 실거래가가 아니다.
- 2024년 이후 자료를 2023 역사 스냅샷이나 학습 입력에 섞지 않는다. 실제 데이터 수집·단지 매칭 보류를 유지한다.
- LLM은 SQL·DB 직접 접근·원천 수정 없이 허용된 세 Data Tool만 사용한다. 인자 검증, 호출 5회·결과 20행, 로컬 엔드포인트·타임아웃 경계를 검토한다.
- 현재는 단일 로컬 4B급 Tool Calling 경로다. Router·RAG·Hybrid·LoRA는 Spec의 도입 조건을 확인한 뒤 결정한다.
- 합성 시험, required-fact coverage, 전체 생성 사실 precision, 실제 Golden 평가는 서로 다른 결과다. 실제 검수 스냅샷·사람 검수 Golden이 없으면 실측 성능이나 Phase 완료를 보고하지 않는다.

QA는 현재 구현의 CLI/API부터 시작한다. 모델 없는 계약 변경은 관련 Python unittest를 실행하고, 모델 연결이 필요한 변경만 합성 smoke를 사용한다. 런타임 설정과 명령은 프로젝트 README를 확인한다. 없는 UI·Git 원격·배포 대상을 임의로 만들지 않는다.

외부 CLI 리뷰·유료 평가·원격 동기화·GitHub issue 등록·push/PR/merge/배포는 그 동작이 사용자 요청 범위에 있을 때만 실행한다. 필요한 도구나 인증이 없으면 가능한 로컬 검사와 그 한계를 보고한다.

완료 시 변경, 실제 검사 결과, 남은 조건과 다음 한 단계를 간결하게 보고한다. 이 스킬은 사용 중 발견한 구체적인 프로젝트 차이를 근거로 개선하고, 일반적인 gstack 변경은 원본 템플릿에 반영한다.
