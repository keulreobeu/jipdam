# PLAN-ROLE2-COLLECT-001 — 2번 수집 하네스 실행 계획

| 항목 | 작성 내용 |
| --- | --- |
| ID | PLAN-ROLE2-COLLECT-001 |
| 담당자·날짜 | cannedJean, 2026-10-29 (Claude Code Opus 5.5 Ultracode로 작성, 사용자 승인) |
| 관련 문서 | [ROLE2-COLLECT-001](../specs/27_role2_collection_spec.md), [ADR-025](../adr/ADR-025-role2-collection-harness.md), [TASK-ROLE2-HARNESS-001](../tasks/role2-collection-harness.md), [TASK-ROLE2-COLLECT-001](../tasks/role2-collection-run.md) |
| 범위·제외 범위 | 2번 출처 수집·정규화·패키징·메타데이터·Issue 초안. 좌표 변환·매칭·DB 적재·자동 게시/업로드 제외 |

## 목표와 확정 근거

사용자 결정(2026-10-29): 키 3종(data.go.kr·서울 열린데이터·생활안전지도), #40·#41 참조만, 정적 우선+소량 실시간 샘플(버스 도착 약 300노선×하루 3회×3일), Issue·Drive는 초안만, 담당 cannedJean·접두어 T, Claude Code 중심+agy 아웃소싱·GMS 제외, 공공누리3·4·비영리는 원본+메타만 공유, HTTP 전용 키 허용 후 재발급.

## 변경과 실행 순서

1. **S0 준비:** 브랜치 `codex/role2-collection-20261029`, `.venv` + `pip install -e outputs/budongi_mvp_temp`, agy preflight.
2. **WF-0 출처 도시에:** 출처 약 35개의 파일·엔드포인트·열·CRS·라이선스·쿼터를 근거 인용과 함께 정리하고 Sonnet이 반박 검증. 결과는 `.local_runtime/role2/dossiers/`.
3. **거버넌스:** 이 Spec·ADR·Plan·Task 2개·원장, AGENTS 승인문, 레지스트리, 예약 팩(사전채움 Issue URL).
4. **W0 리드 코드:** `contract`·`base`·`_reuse`·`filefetch`·최소 `cli` → 예약된 키 없는 파일의 raw 수집 시작.
5. **유닛 스펙·테스트(WF-2/3):** 44개 유닛 조각, 공개/숨김 테스트, `check --red`, 감사.
6. **outsource 실행 W1→W5:** W1 고난도(claude:sonnet), W2~W5(agy gemini-3.8-flash). 리드 셸은 Sonnet 테스트 목록+Gemini 적대 테스트로 검증. 통합 후 제품 테스트.
7. **수집 웨이브:** 레인 A(파일) → B(data.go.kr) → D(서울 API) → C(TOPIS) → E(제한 라이선스). 배치별 stage → package → 검사기 4종·비밀 스윕 → profile → 결과 본문. 첫 3배치는 파일럿 go/no-go.
8. **메타데이터·마무리:** 워크북 조립과 3중 검증, 검증 문서, 로컬 커밋.

출처별 레인·record_type·요청 수·일정은 승인된 계획의 §9 웨이브 표를 따른다(T001~T027, R1~R6, L1~L4).

## 실패·호환성·데이터

- 예약·승인 없는 수집은 코드 게이트로 거부한다. 일일한도 코드(22 등)는 다음 날로 이월한다.
- 해시 불일치·총계 변동은 새 batch_id를 요구한다. 부분·실패는 complete_zero로 바꾸지 않는다.
- 키는 보관함 ID로만 받고, 프록시를 끄고, 저널에는 `{KEY}` 템플릿만 남긴다.
- 원본·ZIP·DB·워크북은 Git에 넣지 않는다(`data/collection/`, `.local_runtime/`, `outputs/team-share/`).

## 검증과 완료

- AC-01~06: `team_collection_tests` unittest(네트워크 없음, skip 없음).
- AC-07~08: [검증 문서](../role2-collection-validation-20261029.md).
- 공통: `scripts/check_sdd.py --base origin/main`, `scripts/verify_environment.py`.
- 현재 상태: not_run.
