---
name: jipdam-workflow
description: Apply this project's Spec, ADR, Task, data provenance, and evaluation contracts when using gstack to plan, implement, review, debug, test, or document the Jipdam Python and SQLite system.
---

# 집담에서 gstack 사용

SDD 운영은 루트 `docs/sdd.md`와 별도 Spec·Task·Plan·ADR 템플릿을 따른다. 코드·설정·계약 변경은 같은 변경에서 갱신한 영구 Task와 연결한다. 등록된 요구·AC·테스트 연결과 TOML 상태를 유지하고 `python -X utf8 scripts/verify_environment.py` 및 브랜치의 `scripts/check_sdd.py --base origin/main`으로 검증한다. 제품 요구는 사용자, 세부 구현과 AC별 증거 기반 완료는 담당자가 책임진다. baseline을 소급 승인하거나 합성 검증을 실제 평가 완료로 표시하지 않는다.

워크스페이스 루트는 이 스킬 경로의 `.agents/skills/` 위 폴더다. 현재 구현은 `outputs/budongi_mvp_temp/`에 있다. 그 폴더의 `AGENTS.md`, `docs/specs/00_project_spec.md`, `docs/specs/10_rental_recommendation_spec.md`, 관련 기능 Spec·ADR, `docs/plans/rental-recommendation-mvp.md`, `docs/tasks/current.md`를 먼저 읽는다. 과거 `work/source_archive/`의 모델·단계·성과를 현재 구현으로 상속하지 않는다.

요청에 맞는 `gstack-*` 스킬을 선택한다. 모호한 요청은 office-hours, 구조와 계약은 plan-eng-review, 변경 검토는 review, 버그는 investigate, 동작 확인은 qa/qa-only, 문서는 document-release/document-generate를 사용한다. 모든 요청에 전체 체인을 실행하지 않는다.

gstack 출력에서 확정된 입력·출력·오류·완료 조건은 기능 Spec에, 구조·데이터 모델·Router/RAG 전략의 채택 이유는 ADR에, 실제 구현 단위와 검사는 Task에 기록한다. 작은 버그나 리팩터링은 관련 Task와 검사로 충분하다. 스킬 내부의 계획·리뷰 상태 파일은 공식 Spec을 대체하지 않는다.

현재 프로젝트의 핵심 검토점:

- 불변 스냅샷, 원 정수·㎡·m, 원천 ID·날짜·파일 해시 보존. 공급액은 실거래가가 아니다.
- 2024년 이후 자료를 2023 역사 스냅샷이나 학습 입력에 섞지 않는다. 실제 데이터 수집·단지 매칭 보류를 유지한다.
- 신규 전월세 API 키는 [CRED-001](../../../outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md)의 로컬 암호화 보관함을 사용한다. Windows Credential Manager가 없으면 평문 fallback 없이 fail-closed한다. 별칭·폴더는 보관 메타데이터이고 폴더 삭제는 포함 키 삭제다. 기존 역사 CLI 환경변수는 유지하며, 키 등록·삭제는 외부 API 호출을 일으키지 않는다.
- CURRENT의 LLM은 SQL·DB 직접 접근·원천 수정 없이 허용된 세 Data Tool만 사용한다. CURRENT의 recommend_rentals는 합성 스냅샷용 별도 읽기 전용 백엔드 허용 목록에 있으며 기존 LLM 세 Tool에는 아직 연결하지 않았다. 전월세 LLM 연결은 후속 Task다. 인자 검증, 호출 5회·결과 20행, 로컬 엔드포인트·타임아웃 경계를 유지한다.
- 현재는 단일 로컬 4B Tool Calling 경로다. 새 제품은 서울 아파트 전월세 단지 후보를 결정적 백엔드로 추천하고 직장/역/마트/공원/병원 직선거리와 필수/선호를 비교한다. LLM은 선택형 설명이며 추천·순위를 바꾸지 않는다. 최신 rental 데이터는 역사/학습과 분리하고 2023 Golden 완료를 제품 선행 조건으로 요구하지 않는다. 합성 추천·CLI는 구현됐고 실제 검수 데이터 추천·웹 비교는 미완료이며 Router·RAG·Hybrid·LoRA는 후속 연구다.
- 합성 시험, required-fact coverage, 전체 생성 사실 precision, 실제 Golden 평가는 서로 다른 결과다. 실제 검수 스냅샷·사람 검수 Golden이 없으면 실측 성능이나 Phase 완료를 보고하지 않는다.

QA는 현재 구현의 CLI/API부터 시작한다. 모델 없는 계약 변경은 관련 Python unittest를 실행하고, 모델 연결이 필요한 변경만 합성 smoke를 사용한다. 런타임 설정과 명령은 프로젝트 README를 확인한다. 없는 UI·Git 원격·배포 대상을 임의로 만들지 않는다.

외부 CLI 리뷰·유료 평가·원격 동기화·GitHub issue 등록·push/PR/merge/배포는 그 동작이 사용자 요청 범위에 있을 때만 실행한다. 필요한 도구나 인증이 없으면 가능한 로컬 검사와 그 한계를 보고한다.

완료 시 변경, 실제 검사 결과, 남은 조건과 다음 한 단계를 간결하게 보고한다. 이 스킬은 사용 중 발견한 구체적인 프로젝트 차이를 근거로 개선하고, 일반적인 gstack 변경은 원본 템플릿에 반영한다.
