# BENCH-FACILITY-001 실행 계획 — KAN-31

1. 기존 facility 계약/계측 중복 검사, CLI·ChatGPT 인증·비과금 회귀를 확인한다.
2. 두 Spec·독립 acceptance·명시 objective-mode·runner를 먼저 준비해 C_SHA를 고정한다.
3. 깨끗한 C_SHA source에서 Usage smoke를 실행하고 공식 필드·완전성을 확인한다.
4. 모델/추론/평가/context/scope·실행 ABBA 순서·각 Task/Run ID를 사전 manifest와 suite에 등록한다.
5. A1→B1→B2→A2를 순차 실행한다. 각 worker가 끝난 뒤 immutable evaluator/변경 범위와
   실제 코드를 부모가 검토하고 승인한다. 모든 재시도와 실패를 포함한다.
6. trial별 원시 지표·pair 차이·성공당 토큰과 coverage를 보고하고 pilot 한계를 명시한다.
7. 검증된 시설 구현 하나를 source에 적용한다. 원본·다른 작업은 보존하고 전체 검증/위키/
   별도 publisher CI·PR/merge로 마무리한다.

```text
명세/독립 평가 봉인 → C_SHA (시설 구현 없음)
   ├─ A1 repeat → independent AC → approval → metrics
   ├─ B1 once   → independent AC → approval → metrics
   ├─ B2 once   → independent AC → approval → metrics
   └─ A2 repeat → independent AC → approval → metrics
                         ↓
               1개 실제 기능 + pilot 비교 보고
```

Architecture: 기존 provider·worktree·budget·approval를 재사용하고 모델 실행과 독립 검증의
수정 scope를 분리한다. Code quality: stdlib parser/JSON report, 별도 서버/ORM 없음.
Tests: hash/bytes/rows, 필수 envelope/facility, 잘못된 JSON/경로/좌표/건수, 결정성/read-only,
prompt의 목표 보존과 한 변수만 변경을 사전 검사한다. Performance: 실제 공식 토큰과
monotonic/UTC 시간을 수집하며 파일 byte 수를 모델 token으로 환산하지 않는다.

실패 처리: CLI 미인증/API 요금 환경/버전 미지원은 actual run 차단; partial usage는 효율비
미정의; 구현 scope 이탈·평가 변조는 실패; timeout/quality 실패는 원장에 남긴다. 별도 actual
구독 한도 병목은 fallback 과금 없이 보고한다. 역할은 부모 Spec/평가, CLI 단일 구현자,
Git 전담 committer다. 실행 중 같은 worktree를 부모가 수정하지 않는다.
