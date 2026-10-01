# Codex 작업 프로토콜 — 집담

이 폴더는 진행 중인 임시 프로젝트다. 이전 저장소 `work/source_archive`는 참고 자료이며 그곳의 활성 단계·모델·성과를 이 프로젝트에 상속하지 않는다.

## 시작 순서

1. 현재 요청과 이 파일을 읽는다.
2. `docs/specs/00_project_spec.md`와 관련 기능 Spec을 읽는다.
3. 관련 `docs/adr/` 및 `docs/tasks/current.md`를 읽는다.
4. 관련 코드·테스트와 `README.md`의 실제 실행 상태를 확인한다.

우선순위는 **현재 사용자의 명시적 지시 → 확정된 Spec → Accepted ADR → 검증 가능한 Acceptance Criteria/테스트 → 현재 Task → 코드 → Wiki/README**다. 충돌을 발견하면 어느 쪽이 현재 의도인지 확인하고 문서와 코드를 동기화한다. `CURRENT`는 확인된 구현, `TARGET`은 계획, `OPEN QUESTION`은 미결정 사항이다.

## 작업 루프

팀 SDD 운영은 루트 `docs/sdd.md`와 별도 템플릿을 따른다. 새 작업은 고유 Task 파일·ID로 보존하고 `current.md`에서 연결한다. 시범 등록된 Spec·Task는 TOML 메타데이터와 루트 추적 원장을 유지한다. 기본 검증은 루트 `python -X utf8 scripts/verify_environment.py`, 브랜치 변경 검사는 `python -X utf8 scripts/check_sdd.py --base origin/main`이다. baseline은 소급 승인이 아니며 verified Task도 실제 제품 평가 완료를 의미하지 않는다.

요청 → 필요한 질문·Plan → Spec 확인/갱신 → 중요한 결정이면 ADR → Task → 구현 → 관련 테스트·평가 → Acceptance Criteria 확인 → Spec과 코드의 차이 확인 → 문서 갱신.

- 워크스페이스 루트의 `.agents/skills/`에 설치된 gstack을 기본 개발 스킬로 사용한다. 먼저 `jipdam-workflow`를 읽고 요청에 맞는 기획·설계·리뷰·디버깅·QA·문서 스킬을 선택한다. 작은 수정에 전체 체인을 실행하지 않는다. gstack 결과 자체는 공식 요구사항이 아니다. 확정된 변경점만 저장소 Spec/ADR에 반영한다. 설치·확장 방법은 워크스페이스의 `docs/gstack.md`에 있다.
- 작은 버그·리팩터링은 Task와 관련 검사로 충분하다. 새 기능·Tool·계약은 Spec과 Task를, 구조·데이터 모델·Router/RAG 전략 변경은 Plan·Spec·ADR·Task를 먼저 다룬다.
- 사용자 경험, 외부 서비스·비용, 보안·개인정보, 호환성 없는 API/스키마 변경, 데이터 삭제, 되돌리기 어려운 설계 선택은 사용자와 결정한다. 함수명·내부 구조·테스트 fixture 같은 되돌리기 쉬운 구현은 작업자가 판단한다.
- 구현 중 새 제품·구조 결정이 드러나면 해당 Spec/ADR부터 갱신한다. 범위 밖 기능을 임의로 추가하지 않는다.
- 완료 보고에는 변경 사항, 실제 실행한 검사와 결과, 미완료 조건 및 다음 한 단계를 명시한다. 확인하지 않은 결과나 단계를 완료로 표시하지 않는다.

## 이 프로젝트의 필수 경계

- 현재 MVP는 2023년 이하 스냅샷의 적재 계약, 허용된 세 Data Tool, 단일 로컬 4B급 Tool Calling 경로다. 검수된 실제 스냅샷은 아직 없다. Router·RAG·Hybrid·LoRA는 평가 후 결정할 확장안이다.
- LLM에 SQL·DB 직접 접근·원천 수정 권한을 주지 않는다. Tool 허용 목록, 인자 검증, 호출 5회, 결과 20행, 로컬 엔드포인트 및 타임아웃 제한을 유지한다.
- `공급액(만원)`은 실거래가가 아니다. 근거 없는 가격·거리·시설·학군·전망을 생성하지 않는다. 원 단위 가격, ㎡ 면적, m 거리를 쓰고 출처 ID·기준일을 추적한다.
- 2024년 이후 자료를 2023 역사 스냅샷이나 학습 자료에 섞지 않는다. 데이터 수집·단지 매칭은 사용자의 보류 지시가 유지되는 동안 재개하지 않는다.
- 실제 역사 스냅샷, 사람 검수 Golden, 전체 생성 사실 평가가 없으면 Phase 0~5 완료 또는 실측 성능으로 보고하지 않는다.

상세 데이터 계약과 단계별 완료 조건은 `docs/specs/` 및 `docs/budongi_advanced_llm_evaluation_plan.md`에 둔다.
