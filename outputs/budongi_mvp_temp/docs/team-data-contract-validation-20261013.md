# 팀 수집 계약 검증 — 2026-10-13

계약: [TEAM-DATA-001](specs/16_team_collection_schema_spec.md). 실행: [TASK-TEAM-DATA-001](tasks/team-data-contract.md). 제출 기준: [가이드](team-data-contract.md).

## db-inspection

루트 `.venv/Scripts/python.exe -X utf8 -`의 Python/SQLite 읽기 전용 probe로 아래 실제 파일을 열었다. `mode=ro`와 `PRAGMA query_only=ON`을 사용했다. 원본·DB·출처 registry를 수정하지 않았다. canonical/통계 코드의 SCHEMA를 in-memory DB에 실행하고 실제 DB의 모든 table_info(열/타입/NULL/PK)와 foreign_key_list를 대조하여 두 DB 모두 일치했다. 후속 읽기 전용 probe에서 sqlite_master의 전체 table DDL도 공백/말미 세미콜론만 정규화하여 대조했고 두 DB 모두 UNIQUE/NOT NULL/CHECK를 포함해 일치했다. 현행 구조 근거는 collection_integrate.py, statistics_storage.py, rental_storage.py, source_files.py다.

| 실제 경로 (제품 폴더 기준) | 확인 결과 |
|---|---|
| `data/collection/molit-seoul-three-api-20261012-restored-20261013/canonical-v3-20261013/canonical.sqlite3` | user_version=3, 무결성 ok/FK 오류 0. raw_items 384,211; observations 374,892; complexes 5,890; addresses 5,839; buildings 0; identity_conflicts 1 |
| 같은 배치 `db/rental.sqlite3` | 무결성 ok/FK 오류 0. 전월세 238,620; complexes/facilities/observation_matches 각각 0. snapshots 325개 source_unverified |
| `data/statistics/statistics.sqlite3` | user_version=1, 무결성 ok/FK 오류 0. files/datasets 30; series 3,832; observations 530,556 = numeric 483,979 + missing 46,577; metadata_reviews 12 |
| `data/rental/synthetic-demo/serving.sqlite3` | 무결성 ok/FK 오류 0. observations/complexes/matches 각각 3; facilities 0; synthetic_only snapshot 1 |

canonical: jeonse 119,631와 wolse 118,989 모두 complex_id NULL. sale 136,272 중 NULL 68,137. match_candidates 271,299 모두 pending/unverified. 이는 후보 **관계 행 수**이며 단지 수나 확정 관측 수가 아니다. confidence_score의 값을 검수 점수라고 보고하지 않는다.

전체 staging의 valid 375,029·outside_period 9,319는 여러 배치의 소속을 포함한다. observations의 전체 고유행 374,892와 단순 비교하지 않는다. 배치별 대사는 아래 batch-inspection에 기록한다.

처음 시스템 Python probe는 openpyxl이 없어 import 단계에서 실패했으며 DB 검사 전이었다. 프로젝트 가상환경에서 다시 실행해 위 검사를 완료했다. 새 의존성 설치나 환경 변경은 하지 않았다.

재현 시 루트에서 아래 읽기 전용 SQL을 사용한다. 파일 경로는 위 표의 기존 파일을 명시하고 없으면 새 DB를 생성하지 않는다.

```python
import sqlite3
from pathlib import Path
p = Path("outputs/budongi_mvp_temp/data/collection/molit-seoul-three-api-20261012-restored-20261013/canonical-v3-20261013/canonical.sqlite3")
with sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True) as c:
    c.execute("PRAGMA query_only=ON")
    print(c.execute("PRAGMA integrity_check").fetchall())
    print(c.execute("PRAGMA foreign_key_check").fetchall())
    print(c.execute("SELECT kind,COUNT(*),SUM(complex_id IS NULL) FROM observations GROUP BY kind").fetchall())
    print(c.execute("SELECT review_status,confidence,COUNT(*) FROM match_candidates GROUP BY 1,2").fetchall())
    print(c.execute("SELECT batch_id,validation_status,COUNT(*) FROM staging_items GROUP BY 1,2").fetchall())
```

## batch-inspection

읽기 전용 batch별 SQL 실행 결과: `canonical-pilot-20261013`의 valid/관측 소속은 137건, `molit-seoul-three-api-20261012`의 valid/관측 소속은 374,892건·outside_period 9,319건이다. 서울 배치 원본 384,211 = 374,892 + 9,319 + 거부 0으로 대사한다. 파일 콘텐츠/원본행 재사용과 배치 소속의 차이를 가이드 §7에 반영했다.

## contract-review

첨부 분담안·기존 Spec/ADR·코드와 수동 대조했다. 가이드 §1/5가 현재 적재 지원·기존 DB 재사용, §2가 namespace/계층/법정동 10자리↔현행 뒤5자리/NULL, §3/4가 필드 타입·단위·시각·좌표, §6/7이 패키지·대사·검수상태·재실행, §8이 후속 판단의 증거/담당/그 전 저장 상태다. 이번 새 문서 5개의 상대 파일 링크 19개가 실제 파일로 연결됨을 Python probe로 확인했다.

특히 현재 JSON 파일 어댑터와 제출 JSONL의 차이, source_files의 복사 시각과 실제 조회 시각의 차이, 통계 Decimal/주기/원문 셀과 거래 원 정수/행의 차이, canonical pending CHECK와 미래 confirmed의 차이를 확인했다. 새 typed 도메인 필드를 기존 JSON payload로만 우회 적재하지 않도록 명시했다.

수집 후 수락/실제 매칭/좌표·시설·공간 변환은 실행하지 않았다. 신규 API 응답 필드나 제공 범위·사용권을 실제 확인했다고 주장하지 않는다. 좌표 교환의 GeoJSON 축 순서는 [RFC 7946](https://www.rfc-editor.org/rfc/rfc7946)의 WGS84/longitude·latitude 정의를 확인했다.

gstack 시작 명령은 Git Bash의 NtCreateDirectoryObject 접근 오류(0xC0000022)로 실패했다. 자동 review/외부 CLI/서브에이전트 완료 로그는 없다. 스킬의 구조·코드·검증·성능 검토 관점만 수동 계약 검토에 적용했다.

## sdd-validation

이번 변경 7개 경로만 지정하여 check_sdd.validate를 실행: features 10 / AC 64 / tasks 25 / changed_paths 7 / passed. 전체 브랜치 검사 `.venv/Scripts/python.exe -X utf8 scripts/check_sdd.py --base origin/main`: 같은 feature/AC/Task 수, changed_paths 73 / passed. 이번 변경 외 기존 미커밋/동시 작업은 별도로 보존하고 이 Task의 구현으로 귀속하지 않는다.

전체 환경 검사의 기본 TEMP는 Windows sandbox AppData 경로에서 WinError 5로 실패했다. 137개 제품 테스트의 생성/rename/정리 접근 오류가 누적된 실행이며 제품 계약 실패로 단정하지 않는다. 동일 셸 프로세스의 TEMP/TMP만 작업 폴더 `.local_runtime/team-contract-temp`로 바꾸어 재검사했다. 영구 환경/제품 코드는 변경하지 않았다.

| 검사 | 결과 |
|---|---|
| 기본 sandbox `verify_environment.py` | 제품 137 tests, errors 259(하나의 테스트에 중복 오류 가능), TEMP 접근 오류; 실패 |
| 작업 폴더 TEMP/TMP의 동일 검사 | 제품 137 tests / 89.942s, errors 18; loopback 소켓 WinError 10013와 OS Credential Manager 접근 오류 5; 실패 |
| 정상 사용자 권한·작업 폴더 TEMP/TMP의 동일 검사 | 제품 137 tests / 60.831s, errors 3; 아래 기존 rename 경로 WinError 5; 실패 |

정상 권한 검사에서 남은 테스트는 `CanonicalSnapshotTests.test_changed_same_batch_rolls_back_and_previous_snapshot_hash_is_preserved`(collection_db.py의 os.rename), `FileCanonicalTests.test_different_json_selections_reuse_blob_but_keep_distinct_file_views_and_rows`(collection_integrate.py의 os.rename), `FileSourceTests.test_distinct_json_array_selections_have_distinct_raw_row_identity`(source_files.py의 os.rename)다. 모두 기존 fixture 임시 디렉터리 게시 단계이며 해당 코드/테스트는 이번 Task에서 변경하지 않았다. 이 오류의 잠금 원인은 이번 문서 검증에서 추가 조사하지 않았으며 전체 환경 검사를 passed로 표시하지 않는다. verify_environment는 제품 테스트 오류로 중단되어 뒤의 팀 테스트/합성 CLI smoke까지 완료하지 못했다.

문서 Task AC-06은 SDD/이번 scope 연결과 위 실패·제한의 정확한 기록을 검증한다. 전체 회귀 통과나 실제 수집/매칭 완료를 이 문서 Task의 완료로 대체하지 않는다. 별도 코드 수정은 해당 원인 조사/Task에서 다룬다.

루트 SDD 단위 검사 `.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_sdd.py -v`는 작업 폴더 TEMP/TMP로 실행하여 15 tests / 3.396s / OK다. 새 Spec/Task 등록·scope·완료 메타데이터 검사기의 기본 회귀는 통과했다.

Task verified 기록 후 최종 SDD 재검사: 이번 7개 경로는 passed, 전체 `--base origin/main`은 동시 작업을 포함한 changed_paths 78 / passed. `git diff --check`도 exit 0이다. 이 숫자는 전체 작업 폴더 변경 수이며 이번 Task의 변경은 7개 경로다.
