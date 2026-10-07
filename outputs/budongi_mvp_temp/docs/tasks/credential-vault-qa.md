# TASK-CRED-QA-001 — 보관함 구현 검증과 수정

```toml
kind = "task"
id = "TASK-CRED-QA-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/credential_vault.py", "outputs/budongi_mvp_temp/src/budongi/credential_server.py", "outputs/budongi_mvp_temp/src/budongi/static/credentials.js", "outputs/budongi_mvp_temp/tests/", "outputs/budongi_mvp_temp/docs/tasks/", "outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md", "docs/sdd/traceability.json"]
acs = ["CRED-001-AC-01", "CRED-001-AC-03", "CRED-001-AC-04", "CRED-001-AC-05", "CRED-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-vault-qa.md#validation"
acs = ["CRED-001-AC-01", "CRED-001-AC-03", "CRED-001-AC-04", "CRED-001-AC-05", "CRED-001-AC-06"]

[[verification]]
command = "manual: gstack browse, 임시 DB·합성 키로 Escape·교체·마스킹·삭제 취소·오래된 확인·재확인 검증"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-vault-qa.md#validation"
acs = ["CRED-001-AC-01", "CRED-001-AC-03", "CRED-001-AC-04", "CRED-001-AC-05"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-vault-qa.md#validation"
acs = ["CRED-001-AC-06"]
```

사용자의 구현 검증·수정 요청으로 CRED-001 저장소·loopback API·설정 화면을 재검토한다. 실제 키·외부 공급자 호출·실데이터 수집·배포·커밋은 제외한다. 기존 TASK-CRED-001의 native Windows round-trip 미완료는 그대로 유지한다.

## validation

수정 전 새 회귀 테스트 8개에서 실패 6개·오류 2개로 모두 재현했다. 이전 키를 별칭에 넣으며 교체하면 평문 메타데이터가 되며, 폴더명에 같은 키를 넣는 경우도 등록이 허용됐다. idle TCP 연결은 다른 요청을 막았고, 비 ASCII CSRF는 연결을 종료했다. 잘못된 Unicode 이름은 500, 잘린 본문은 생성 성공, 미지원 메서드는 입력 반사 HTML, 오래된 폴더 확인은 새 키 삭제로 이어졌다.

브라우저 수정 전에는 합성 교체 키를 입력하고 Escape를 누르면 창이 닫혀도 입력 길이 25가 남았다. 임시 DB·메모리 키 저장소만 사용했다. 독립 in-host adversarial review에서 별칭·idle 연결·오래된 삭제 확인·Escape 경로를 지적했다. 외부 CLI 리뷰는 실행하지 않았다.

## 완료 기준

- [x] CRED-001-AC-01 기존 여러 키·별칭·교체 계약 유지
- [x] CRED-001-AC-03 메타데이터·오류 응답 비노출 및 닫기 입력 초기화
- [x] CRED-001-AC-04 최신 목록 확인·원자적 삭제·동시 조회 일관성
- [x] CRED-001-AC-05 외부 요청 없는 loopback 동작과 입력 오류 처리
- [x] CRED-001-AC-06 Spec·Task·원장 및 실제 검증 상태 동기화

## 수정·회귀 증거

새 테스트 파일은 `tests/test_credential_regressions.py`, 클래스는 `CredentialRegressionTests`다. 제품에 테스트 전용 API를 추가하지 않았다. 아래 메서드는 서로 다른 실패 경계·부작용을 보호한다.

| 문제 → 수정 | 회귀 메서드·실패 조건 |
| --- | --- |
| 이전 키 별칭 노출 → 이전/새 키 모두 검사·롤백 | `test_rotation_rejects_old_secret_in_alias_and_rolls_back`: 이전 키가 별칭에 들어가거나 키 교체가 부분 적용되면 실패 |
| 폴더명 키 노출 → 등록·교체 때 해당 폴더 검사 | `test_folder_name_cannot_echo_key`: 키와 같은 폴더명에 등록되면 실패 |
| Unicode 이름 500 → 안전한 입력 오류 | `test_invalid_unicode_label_is_input_error`: 400이 아니거나 행이 추가되면 실패 |
| 비 ASCII CSRF 연결 종료 → 403 | `test_non_ascii_csrf_is_rejected_without_disconnect`: 응답 없는 종료나 부작용 발생 시 실패 |
| 기본 HTTP 오류 입력 반사 → 공통 JSON·보안 헤더 | `test_unsupported_method_does_not_echo_input_and_has_security_headers`: 메서드 반사·no-store 누락이면 실패 |
| idle 연결의 전체 차단 → 독립 요청 처리·5초 읽기 제한 | `test_idle_connection_does_not_block_other_requests`: 실제 idle 연결이 수락된 뒤 다른 GET이 지연되면 실패 |
| 잘린 본문 적용 → 선언 길이 검사 | `test_truncated_body_is_rejected_without_mutation`: half-close 후 부분 본문이 적용되면 실패 |
| 읽기 제한·삭제 목록의 새 계약 | `test_incomplete_body_times_out_without_mutation`, `test_folder_delete_requires_explicit_key_list`: 408/400 대신 적용되면 실패. 앞선 재현 뒤 추가한 경계 검증 |
| 오래된 삭제 확인 → 트랜잭션 내 정확한 키 ID 대조·409 | `test_stale_folder_confirmation_preserves_all_keys_even_with_same_count`: 개수가 같아도 ID가 바뀐 키가 삭제되면 실패 |
| 동시 조회의 개수/목록 불일치 → 단일 읽기 트랜잭션 | `test_folder_counts_and_key_ids_share_one_snapshot_during_concurrent_add`: 실제 SQLite reader/writer를 교차 실행하여 불일치 시 실패. SQLite trace callback으로 기존 DB 경계에서만 스케줄을 제어 |

독립 재검토에서 마지막 동시 조회 문제를 발견했다. 추가 회귀 테스트는 수정 전 개수 0·목록 1로 실패했고 수정 후 통과했다. 수정 소스의 마지막 독립 검토에서 추가 지적이 없었다.

## 최종 실행 결과

- 새 회귀 테스트 11개 통과. 제품 전체 65개 중 64개 통과·native WinCred 1개 skip. 루트 18개 통과. `verify_environment.py`의 합성 CLI smoke도 통과.
- `check_sdd.py --base origin/main`: 4개 기능·29개 AC·12개 Task·46개 변경 경로 검사 통과. `git diff --check`, `node --check outputs/budongi_mvp_temp/src/budongi/static/credentials.js` 통과.
- 브라우저: Escape 이후 교체 키 입력 길이 25 → 0, 교체·새로고침 후 별칭 `QA updated`와 마스킹만 표시. 다른 요청에서 키를 추가한 뒤 오래된 화면의 삭제 확인은 409와 재확인 안내로 처리하고 2개 모두 유지. 삭제 취소는 유지, 새 목록의 재확인은 폴더·2개 키 삭제 성공.
- 1280px 데스크톱·390px 모바일 화면 캡처와 육안 확인 완료. 모바일 전체 페이지 너비는 390px이며 표는 자체 가로 스크롤을 사용한다. 콘솔에는 의도적으로 검증한 409 HTTP 실패만 있었으며 JavaScript 예외는 없었다. 로컬 캡처는 `.local_runtime/gstack/qa-reports/credential-vault-20261006/screenshots/`에 있으며 합성 저장소 배지는 실제 OS 검증 증거가 아니다.
- 기존 최초 캡처 실패는 Windows 경로 인자 해석 문제였으며 절대 `/` 경로로 캡처했다. 공식 gstack review binding 및 Bun 기반 QA 영수증은 helper 실행 제약으로 미저장이다. 공식 gstack 완료 판정 대신 위 네이티브 검사·브라우저 관측을 증거로 사용한다.

이 Task의 `verified`는 위 수정 범위의 검증이다. [TASK-CRED-001](api-credential-vault.md)의 AC-02는 Windows 로그온 Credential Manager 세션 부재(오류 1312)로 계속 미완료다. 사용자 인터랙티브 Windows 세션에서 `test_native_credential_manager_round_trip_uses_synthetic_key`를 실행해야 한다. 실제 공급자 호출과 데이터 수집 보류도 그대로 유지한다.
