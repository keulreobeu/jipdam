# SDD 도입 검증 기록

기준: 2026-10-01. TASK-SDD-001과 EVAL-001 baseline의 합성 검증을 실제 제품 평가와 구분한다.

## Local checks

2026-10-01 Windows/Python 3.12에서 `python -X utf8 scripts/bootstrap.py --app-only`를 실행했다. 제품 28개(기존 22 + 평가 집중 6), 팀 18개(기존 3 + SDD 15), 총 46개 테스트와 모델 없는 합성 CLI smoke가 통과했다. SDD 검사에 운영·평가 2개 기능, 12개 AC, 2개 Task를 등록했다.

Task 갱신 없는 코드 변경, 범위 누락, draft Spec에 대한 구현 진행, 중복 ID·깨진 문서/테스트/증거 참조, 미등록 메타데이터 문서, verified 근거 누락을 거부하는 회귀 검증을 포함한다. 설명 문서 면제와 계약 문서 면제 거부, PR/push/new-branch 및 rename의 실제 Git 변경 탐지도 확인했다. 독립 검토에서 찾은 CI 탐색 밖 테스트 참조와, 변경 경로의 저장소 밖 접근·마지막 실패 기록 누락을 재현했다. 추가 회귀 검사는 수정 전 실패하고 수정 후 통과했다. 로컬 통과가 GitHub CI·main 설정 완료를 의미하지는 않는다.

## GitHub CI

커밋 `0b4bc8f2bb5b145f4ae260b666f7e1e22a2f748b`의 [PR CI](https://github.com/keulreobeu/jipdam/actions/runs/36823087083)와 [push CI](https://github.com/keulreobeu/jipdam/actions/runs/36823044007)가 모두 성공했다. Windows/Linux × Python 3.11/3.12의 네 조합에서 SDD 검사·46개 테스트·합성 CLI를 실행했다. [PR #1](https://github.com/keulreobeu/jipdam/pull/1)에 변경과 검증을 공유한다.

## Main protection

2026-10-01 PR CI 성공 후 GitHub 보호 설정을 적용하고 `gh api repos/keulreobeu/jipdam/branches/main/protection`으로 다시 읽어 아래 값을 대조했다.

| 설정 | 확인한 값 |
| --- | --- |
| 필수 검사 | model-free-checks (ubuntu-latest, 3.11), (ubuntu-latest, 3.12), (windows-latest, 3.11), (windows-latest, 3.12) |
| 검사 제공 앱 | GitHub Actions, app_id 15368 |
| 최신 main 반영 | strict = true |
| 관리자 적용 | enforce_admins.enabled = true |
| 필수 승인 리뷰 수 | required_approving_review_count = 0 |
| Code Owner·마지막 push 승인 강제 | 둘 다 false |
| force push·브랜치 삭제 | 둘 다 false |

필수 검사 목록은 원격 응답과 정확히 일치했다. main 변경은 PR과 필수 CI를 따르고 사람 리뷰는 권장한다. [GitHub 보호 API](https://docs.github.com/en/rest/branches/branch-protection#update-branch-protection)의 `checks` 형식으로 앱 ID를 고정했다.

## Product evaluation

required-fact coverage의 공개 evaluate 경로에서 단위 환산·허용 오차 경계, 날짜/문자열 정규화, entity·alias·문장 경계, 미지원 입력과 prediction 누락, 미측정 분모 제외, CSV 근거·재현성, 기존 지표·generation 보류 상태를 검사했다. 6개 집중 테스트가 기존 평가 테스트와 함께 통과했다.

현재 `900,000,000원입니다`처럼 원 단위에 한글 서술을 붙인 형식이 missing이 되는 제한을 확인하고 baseline·회귀 테스트에 명시했다. `900,000,000원 입니다`는 환산된다. 기존 평가 코드는 변경하지 않았다. 검수된 실제 역사 snapshot, 사람 검수 Golden, 전체 claim precision 및 Phase 0~5 완료는 보류다.
