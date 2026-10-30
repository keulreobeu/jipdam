# TASK-WINDOWS-SNAPSHOT-001 — Windows 스냅샷 게시 접근 거부

```toml
kind = "task"
id = "TASK-WINDOWS-SNAPSHOT-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/13_canonical_integration_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/collection.py", "outputs/budongi_mvp_temp/src/budongi/collection_db.py", "outputs/budongi_mvp_temp/src/budongi/collection_integrate.py", "outputs/budongi_mvp_temp/src/budongi/source_files.py", "outputs/budongi_mvp_temp/tests/test_snapshot_publication.py", "outputs/budongi_mvp_temp/tests/test_file_canonical.py", "outputs/budongi_mvp_temp/docs/tasks/windows-snapshot-publication-20261028.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["CANONICAL-001-AC-04", "CANONICAL-001-AC-05", "CANONICAL-001-AC-07"]
```

[KAN-27](https://kwulreobeu.atlassian.net/browse/KAN-27). SQLite를 닫은 뒤에도 Windows 폴더 게시에서 WinError 5가 간헐적으로 발생한다. 제품 외 독립 실험에서 SQLite 생성·commit·close 후 100회 중 1회 재현했고 별도 600회에서는 재현되지 않았다. 잠금 주체는 미확인이다. 최신 전체 환경 검증은 329개 중 1오류였다.

대상은 수집 정규화·파일 staging·canonical 빌드의 새 디렉터리 원자적 게시다. Windows의 특정 일시적 접근 오류에 한해 제한적으로 재시도하고 다른 오류 및 재시도 소진은 그대로 실패한다. 기존 출력·원본을 덮어쓰지 않고 다른 OS의 기존 동작을 유지한다. 성공·지속 실패·다른 오류·게시 충돌의 합성 검증과 기존 전체 환경 검증을 수행한다. 실제 데이터 변경·수집·원격 전송은 포함하지 않는다. GMS 키는 만료되어 호출하지 않는다.

2026-10-28: 오류 코드 5/32/33은 최대 5회, 지수 간격 최대 총 0.75초 후에도 실패하면 원래 오류를 전달한다. 합성 게시 테스트 4개와 파일 canonical 테스트 10개, 전체 `scripts/verify_environment.py`의 제품·팀 검사 및 합성 CLI, SDD와 `git diff --check`가 통과했다. 최초 단위 검사는 sandbox 기본 TEMP에서 mkdir 권한 오류로 실패했으며 workspace TEMP로 재실행했다. 독립 재현을 포함해 잠금 주체는 아직 확인되지 않았으므로 근본 원인 조사는 열어 둔다.

위키 maintenance 및 catalog/search 검토 후 이벤트 KAN27-WINDOWS-PUBLISH-20261028은 SKIP/one_off/DONE/nonblocking이다. 잠금 주체나 사용자의 별도 조치를 확정할 근거가 없어 별도 원인 가이드를 만들지 않았다. [Jira 검증 기록](https://kwulreobeu.atlassian.net/browse/KAN-27?focusedCommentId=10129) 및 receipt DONE.

후속 조사: 합성 SQLite를 매번 생성·commit·close하고 그 폴더의 이름을 변경하는 별도 2,000회 실험을 실행했다. 이번 실험은 접근 거부 0건으로 끝나 Windows Restart Manager의 실패 시 소유자 조회 경로가 실제로 호출되지 않았고 잠금 주체에 관한 새 증거는 얻지 못했다. 이전 100회 중 1회 실패와 구분하며, 이것만으로 재발이 사라졌거나 특정 프로세스가 원인이라고 판단하지 않는다.

Windows 실제 잠금 합성 검증: 별도 자식 프로세스가 합성 SQLite 파일을 `FILE_SHARE_DELETE` 없이 열도록 제어했다. 0.25초 잠금에서 직접 rename은 실제 `PermissionError: WinError 5`였고 게시 함수는 0.344초 뒤 성공했으며 read-only 재조회 값이 일치했다. 1.3초 잠금에서는 게시 함수가 0.75초 뒤 같은 오류를 전달했고 helper 호출자의 합성 원본 폴더와 DB 값은 그대로, 목적지는 미생성이었다. 호출자의 기존 실패 정리 정책은 별도이며 이 helper 실험으로 임시 산출물의 영구 보존을 보장하지 않는다. 합성 잠금 원인은 의도적으로 만든 자식 프로세스이며 기존 간헐 오류의 잠금 주체를 특정하지 않는다.

2026-10-29: 위 실제 파일 공유 제한을 자동 회귀로 추가했다. 합성 SQLite의 연결을 닫은 후 Windows 파일 핸들에서 삭제 공유를 제외하고 직접 rename의 실제 WinError 5를 확인하며, 첫 재시도 대기 시 핸들을 결정적으로 닫아 게시 성공과 DB 행 보존을 검사한다. 프로젝트 `.venv`와 workspace TEMP의 `test_snapshot_publication.py` 5개가 통과했다. 테스트 추가 전 전체 환경 통과 이력은 그대로이며 이 테스트 추가 뒤 전체 환경을 다시 실행한 것은 아니다. 기존 간헐 오류의 외부 잠금 주체는 미확인이다.

위키 maintenance/catalog/search 후 `KAN27-REAL-LOCK-TEST-20261029`은 SKIP/execution_log/DONE/nonblocking이다. 자동 회귀 증거는 이 Task와 [Jira](https://kwulreobeu.atlassian.net/browse/KAN-27?focusedCommentId=10138)에 기록했고 Jira receipt는 DONE이다.

2026-10-29 추가된 실제 잠금 테스트를 포함한 `scripts/verify_environment.py` 전체 재실행이 종료 0으로 통과했다. 제품 335개, 팀 35개와 모델 없는 합성 CLI를 실행했고 SDD 22 features/109 AC/52 tasks도 통과했다. 이 결과는 실제 간헐 실패의 잠금 주체 확인이나 새 실데이터 검수를 뜻하지 않는다.
