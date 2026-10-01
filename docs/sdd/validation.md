# SDD 도입 검증 기록

기준: 2026-10-01. TASK-SDD-001과 EVAL-001 baseline의 합성 검증을 실제 제품 평가와 구분한다.

## Local checks

2026-10-01 Windows/Python 3.12에서 `python -X utf8 scripts/bootstrap.py --app-only`를 실행했다. 제품 28개(기존 22 + 평가 집중 6), 팀 18개(기존 3 + SDD 15), 총 46개 테스트와 모델 없는 합성 CLI smoke가 통과했다. SDD 검사에 운영·평가 2개 기능, 12개 AC, 2개 Task를 등록했다.

Task 갱신 없는 코드 변경, 범위 누락, draft Spec에 대한 구현 진행, 중복 ID·깨진 문서/테스트/증거 참조, 미등록 메타데이터 문서, verified 근거 누락을 거부하는 회귀 검증을 포함한다. 설명 문서 면제와 계약 문서 면제 거부, PR/push/new-branch 및 rename의 실제 Git 변경 탐지도 확인했다. 독립 검토에서 찾은 CI 탐색 밖 테스트 참조와, 변경 경로의 저장소 밖 접근·마지막 실패 기록 누락을 재현했다. 추가 회귀 검사는 수정 전 실패하고 수정 후 통과했다. 로컬 통과가 GitHub CI·main 설정 완료를 의미하지는 않는다.

## GitHub CI

PR CI·Windows/Linux 실행 결과는 확인 후 기록한다.

## Main protection

CI 성공 후 필수 검사·리뷰 권장 설정을 적용하고 읽은 결과를 기록한다.

## Product evaluation

required-fact coverage의 공개 evaluate 경로에서 단위 환산·허용 오차 경계, 날짜/문자열 정규화, entity·alias·문장 경계, 미지원 입력과 prediction 누락, 미측정 분모 제외, CSV 근거·재현성, 기존 지표·generation 보류 상태를 검사했다. 6개 집중 테스트가 기존 평가 테스트와 함께 통과했다.

현재 `900,000,000원입니다`처럼 원 단위에 한글 서술을 붙인 형식이 missing이 되는 제한을 확인하고 baseline·회귀 테스트에 명시했다. `900,000,000원 입니다`는 환산된다. 기존 평가 코드는 변경하지 않았다. 검수된 실제 역사 snapshot, 사람 검수 Golden, 전체 claim precision 및 Phase 0~5 완료는 보류다.
