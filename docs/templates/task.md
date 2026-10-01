# Task 템플릿

영구 파일로 복사하고 원장의 tasks 배열에 등록한다. scope는 루트 상대 파일 또는 `/`로 끝나는 디렉터리다. verified 전 AC와 verification을 실제 근거로 채운다.

```toml
kind = "task"
id = "TASK-FEATURE-001"
status = "draft"
owner = "담당자"
specs = ["docs/specs/feature.md"]
scope = ["src/feature.py", "tests/test_feature.py", "docs/specs/feature.md", "docs/tasks/TASK-FEATURE-001.md", "docs/sdd/traceability.json"]
acs = ["FEATURE-001-AC-01"]
```

## 목표·범위·제외 범위

새 기능/버그/리팩터링/설정 중 변경 유형과 관련 계약·승인 근거를 기록한다. 담당자·의존 Task와 차단 이유를 기록한다.

## 완료 기준

- [ ] FEATURE-001-AC-01 관찰 가능한 완료 조건

## 검증 기록

완료 시 위 TOML 블록 안에 다음 table을 추가한다. failed/not_run은 완료 증거가 아니다. 로그 대신 공유 문서에 결과·실행 버전을 요약하거나 CI 링크를 연결한다.

```toml
[[verification]]
command = "실제로 실행한 명령"
result = "passed"
evidence = "docs/validation.md#result"
acs = ["FEATURE-001-AC-01"]
```

## 결과·남은 조건

실제 실행 결과, AC별 근거와 미완료 조건을 기록한다. 실제 평가나 후속 Task의 미완료를 이 Task의 완료와 구분한다.
