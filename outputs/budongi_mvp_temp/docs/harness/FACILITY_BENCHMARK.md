# 시설 검증기·첫 Codex 실측·다른 환경 인계

2026-10-30 / [KAN-31](https://kwulreobeu.atlassian.net/browse/KAN-31) /
[기능 Spec](../specs/29_facility_package_validation_spec.md),
[실험 Spec](../specs/30_context_benchmark_spec.md), [영구 Task](../tasks/facility-benchmark.md).
실제 제품 기능은 하나, 반복 trial은4개다.

## 구현과 사용

manifest·SHA-256/bytes/rows·시설/계보 필수값·건수·구조화 오류·결정성/원본 불변을 검사하는
stdlib 오프라인 API `budongi.team_package.validate_package(Path | str)`와 JSON CLI다.
첫 지원 범위는 Spec29의 `facility_all_status_rows_v1`이다. 전체 team_collection_v1의 모든
합법 레이아웃을 지원하지 않는다. validation.json에만 rejected 위치가 있는 제출은
unsupported_layout이고 rejected 수를0으로 만들지 않는다. 수집/좌표 변환/매칭/DB 적재/
Snowflake/업로드는 하지 않는다. 통과는 사실성·사용권·추천 적격성 승인이 아니다.

```powershell
python -m budongi.team_package C:/path/to/package
python -m unittest discover -s outputs/budongi_mvp_temp/tests -p "test_team_package*.py" -v
```

루트 README대로 환경을 설치한다. CLI는 정상0/잘못된 패키지2, stdout JSON 한 개다.

## 고정 조건과 실제 결과

시작 C_SHA=`d6cc4badb2c52dea0a6f72f70fb5c9085c77491e`는 main b29d2d4 기반의 준비
커밋이며 시설 구현은 없었다. A1→B1→B2→A2 모두 fresh Codex 세션/별도 worktree,
CLI0.164.0·ChatGPT 인증·configured gpt-6.1-terra/high·openai다. observed model은 CLI에서
확인되지 않아 null이다. memory/native multi-agent/fallback/resume은 두 조건 모두 비활성,
max_attempts2다. 이 고정 조건의 baseline이며 App 전체 사용량을 대표하지 않는다.

| 실행 | Objective | 입력 | 출력 | 캐시 읽기 | 미캐시 입력 | 총 토큰 | 작업 초 | 검토 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A1 | repeat | 285,978 | 7,559 | 251,008 | 34,970 | 293,537 | 88.708 | 거부 |
| B1 | once | 310,108 | 6,827 | 269,952 | 40,156 | 316,935 | 80.686 | 거부 |
| B2 | once | 229,822 | 6,716 | 197,632 | 32,190 | 236,538 | 78.991 | 거부 |
| A2 | repeat | 232,305 | 6,468 | 194,304 | 38,001 | 238,773 | 80.005 | 거부 |

모두 공식 turn Usage coverage=complete/collector_health=ok, attempt1/retry0/cache_write0다.
reasoning output은 차례로452/589/253/248이며 출력의 하위 항목이다. 입력에는 캐시가 포함된다.
총 토큰=입력+출력으로 캐시를 다시 더하지 않는다. feature trial 합계 **1,085,783토큰**.
별도 smoke는 입력23,395/출력9/캐시7,296/총23,404토큰으로 feature trial에 합산하지 않았다.
구독 한도·달러 비용으로 환산하지 않는다. 모델 내부 도구 반복을 harness retry로 추정하지 않았다.

모델 실행 초는83.438/74.828/73.750/74.750, validation 초는4.781/4.828/4.765/4.797이다.
wall time에 단계 시간을 다시 더하지 않는다. 사람 활동 시간, App 기획/검토/Jira/Git/위키,
숨겨진 provider 호출은 계측 밖이다. 1M 토큰당 작업량은 계산하지 않았다.

## 품질 판정과 실패 비용

모든 trial은 봉인 acceptance19·worker public test·provider17을 통과했다. 그러나 독립 코드
검토/추가 합성 재현에서 A1은 추가 files.path=null 무시, B1은0건 manifest 버전=null 허용,
네 trial 모두 CSV source_row_number의5,000자리 숫자→int 변환 중 ValueError를 확인했다.
세 경계 사례를 모든 trial에 동일 적용했다. native 리뷰는 B2의 schema.json=null 허용과
refresh_token query 누락도 재현했다. 고정 평가 자체의 coverage가 부족했던 결과다.

**verified success=0/4, 성공당 토큰=null, paired 절감률=null.** REVIEW_REQUIRED와 별도
review/approval=false outcome을 보존했고 성공 approve를 호출하지 않았다. harness 실패
attempt 토큰 필드는 null(해당 실패 attempt 관측 없음)이다. 검토 탈락 비용은 각 trial의
총 토큰 전부이며 합계1,085,783이다. 실패 비용을0으로 만들거나 원장을 지우지 않았다.

실제 전달 prompt는21,711→11,143bytes로 중복10,568bytes를 제거했다. 이는 **byte 감소**이며
총 토큰 절감 증거가 아니다. 토큰 변동 방향도 일치하지 않는다. N=2 조건별 pilot,
캐시/순서/비결정성과 평가 coverage 한계를 남긴다. once는 opt-in, 기존 기본 repeat는 유지한다.

## 측정 뒤 보완과 절차 이탈

B2를 원본 worker 밖의 개발 폴더로 복사한 뒤 긴 CSV 숫자를 int 변환 없이 검사하고,
refresh_token을 거부하며 존재하는 schema.json=null을 invalid_type으로 처리했다. 최종 native
리뷰에서 재현한 깊은 JSON의 RecursionError도 invalid_json으로 보고한다. 결함 검사를 먼저
실패시키고 수정했다. public9+봉인19=28 PASS. 이 로컬 보완/검토 비용은 위
실측 밖이며 trial을 소급 성공으로 바꾸지 않는다.

봉인 driver는 이전 COMPLETED만 허용해 실패 뒤 진행을 막았다. 원본 driver/worker/evaluator는
수정하지 않고 runtime adapter가 부정 outcome을 기록한 뒤 후속 실행했다. 모델 입력과 평가
hash는 그대로였다. 최종 driver에는 `reject --trial A1 --reviewer agent-codex-evaluator
--reason quality_failure`가 추가됐다. 현재 subject/revision/evidence hash가 일치하는 거부만
다음 실행을 허용하며 성공 승인이 아니다. approve는 담당자의 실제 코드 검토를 전제로 한
명시 attestation이다. 최종 제어 검사10개 PASS.

## 다른 환경에서 이어하기

1. 이번 브랜치/PR을 가져오고 루트 README대로 환경을 설치한다. AGENTS·Task·두 Spec과 이
   보고서를 읽는다. 원래 dirty source의 다른 작업은 이번 전달 대상이 아니다.
2. 과거 시작점은 위 C_SHA다. 최종 구현이 있는 HEAD를 baseline으로 쓰지 않는다. Git 담당
   절차로 C_SHA의 별도 깨끗한 worktree를 만든다. merge commit으로 C_SHA 이력을 보존한다.
3. 사용자의 마무리 요청에 따라 추가 실측은 중단했다. 다음 실험은 새 study/task/state-dir로
   만들고 이번 결함을 잡는 평가부터 봉인한다. 이전 원장을 reset/retry해 덮어쓰지 않는다.
   평가/driver 변경 후 재측정은 새 baseline이며 같은 실험이라고 부르지 않는다.
4. actual 실행 전에 preflight/smoke로 CLI·인증·모델·Usage를 확인한다. 다른 OS/CLI/model/
   cache 정책은 별도 조건이다. API 키/GMS로 자동 fallback하지 않는다.
5. .local_runtime의 원장/세션은 Git에 넣지 않아 자동 전송되지 않는다. 원장 없는 환경에서
   과거 metrics report를 재생성했다고 주장하지 않는다. 인증/키/raw/DB/runtime 전체를 복사하지
   않는다. 영구 보고서의 실제 수치·해시·Run ID로 과거 결과와 새 결과를 구별한다.

이 환경 원장: `.local_runtime/bench-facility-work/experiment/.local_runtime/facility-benchmark/`.
sealed-manifest.json/comparison.json/results/prompt-receipts와 managed metrics/state를 보존했다.
Git/위키/최종 환경 검증의 실제 완료 여부는 영구 Task 영수증을 따른다.

### 병합 전 추가 검토 보완

PR `9f3d3e72`의 최종 자동 검토에서 `str.splitlines()`가 JSON 문자열 내부의 합법적인
U+2028/U+2029/U+0085를 JSONL 행 경계로 처리하는 결함을 발견했다. 검토 재현은
[PR comment 4422070758](https://github.com/keulreobeu/jipdam/pull/65#discussion_r4422070758)이다.
파서를 LF 기준으로 분할하고 CRLF의 CR만 제거하도록 수정했다. 공개 테스트에 세 문자를
포함한 합성 시설명을 추가했으며 public10 및 봉인 acceptance19가 통과했다. 이 보완은
실측 밖이고 기존 4개 trial의 거부/토큰·비용 결과를 바꾸지 않는다. 수정 후 publisher
snapshot, 최신 필수 CI 및 C_SHA 조상 확인이 끝나기 전까지 PR은 병합 완료가 아니다.

| 증거 | 값 |
| --- | --- |
| manifest SHA-256 | fa08475c47e9996bdb3172b826fd6b72386dccccb12e71935771dddb67ba3ccc |
| frozen evaluator SHA-256 | 0e1f9872680219b9edf1e14ea291262440353f6156d6b6436b308c3e09a0ef0c |
| original runner SHA-256 | ec570684e07df14553c7173ab380dac71057839ca2fa901c46b17f05c2bf3004 |
| repeat prompt SHA-256 | 5cc80f0f006a997259cbe2ee3e4c698757bad36be72c9752bfef8b27fef53be1 |
| once prompt SHA-256 | 2c3b4f15eadf357c44fcf70b5e455630e9457cb2e40f1d5a673c9cd0e6c05846 |
| smoke Run ID | cf8f9491fe41410ba09eb0d7a9e47bf5 |
| A1 Run ID / result SHA-256 | ccdb749287fb42fb953f5ab3d44a8498 / 89382371ff1f552b1fb0adebcc651e8ae8261de6f4541b5b6eb9882309de9493 |
| B1 Run ID / result SHA-256 | 720d8b326d9f4c6db948b250e37905f4 / d3f0c0a80517d9ff306f9ee543c3b7918ed6fbfe68e8ade57933fe2b21d7a919 |
| B2 Run ID / result SHA-256 | a43d270a2eea44d198dc8931b46e526e / b246d08c185af93f8650c20d0f522772d059ad50297718c831aa418a125acc67 |
| A2 Run ID / result SHA-256 | 625c0be80d7b4016b8f7c9f6f7b6fd53 / 52d2aed3ea0e345ab7c20cefceebe54290772bfc3d1c12036fb22b8feb851ce5 |
