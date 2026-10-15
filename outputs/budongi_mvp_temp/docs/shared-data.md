# 원본 공유와 DB 재구성

계약: [PORTABLE-001](specs/15_data_portability_spec.md), [Task](tasks/data-portability.md).

공유 대상은 [jipdam_db](https://drive.google.com/drive/folders/13AjoiYNCWcIB12GhSKyLiR1M2bR4Drkg)다. 원본 ZIP·DB·키는 Git에 넣지 않는다.

| 패키지 | 내용 | bytes / SHA-256 |
|---|---|---|
| kb-statistics-provided-20261013-portable-v1.zip | 엑셀30개·통계DB 보관본·검수12건·코드/registry/manifest/복원 명령 | 87,135,693 / `83f0e40ac834bcb5a468fa51243913e7d73fc87d7d8eb15d279cca27dcdc32e1` |
| molit-seoul-three-api-20261012-portable-v2.zip | 기존 서울 XML/관측DB ZIP·종로구 이력 원본·코드/manifest/복원 명령 | 210,915,139 / `e9eeb0c1057e16f11066c42e704ffd38d88e93bc59dda797a3b250c7366cc013` |

통계 ZIP: [Drive 파일](https://drive.google.com/file/d/1SQot8SCZXC-MdketgQPyoyROADwPWnbP/view?usp=drivesdk) · [수집 기록 #6](https://github.com/keulreobeu/jipdam/issues/6). 다운로드 SHA도 원본과 일치했다.

국토부 ZIP은 도구의 파일당100MB 제한 때문에 동일 bytes를 3조각으로 저장했다. 아래 6개를 같은 폴더에 내려받는다. 기록은 [#5](https://github.com/keulreobeu/jipdam/issues/5)다.

- [part001](https://drive.google.com/file/d/1wvA1exd635p1lVZzfrojvlCUGASK4-Ph/view?usp=drivesdk)
- [part002](https://drive.google.com/file/d/1oqJiUgFFRM18OsL_MPT7M6elDVIsx6A5/view?usp=drivesdk)
- [part003](https://drive.google.com/file/d/15RprzVeERz5x9SwH1p6toYTCUJVmXs_V/view?usp=drivesdk)
- [조각별/전체 해시 manifest](https://drive.google.com/file/d/1_Gt7M7zFx7jjxE_BrEYnN_Ahkx0xLdO0/view?usp=drivesdk)
- [재조립 스크립트](https://drive.google.com/file/d/1QxLCDO0srDI-iD9dWA6ayN00simSreYp/view?usp=drivesdk)
- [복원 안내](https://drive.google.com/file/d/1jy7JkCYd_1n3KynE1G_0bXgUltnaLVa9/view?usp=drivesdk)

```sh
python join_shared_parts.py molit-seoul-three-api-20261012-portable-v2.zip.parts.json --output molit-seoul-three-api-20261012-portable-v2.zip
```

재조립은 각 조각과 전체 ZIP의 크기/SHA를 검사하고 기존 출력을 거부한다. 파일명은 그대로 유지한다. 통계 ZIP은 재조립이 필요 없다.

## 다른 PC에서 실행

필요한 데이터만 Drive에서 다시 받으려면 저장소 루트에서 아래 명령을 사용한다. `--output`은 아직 없는 폴더로 지정한다. 이 명령은 ZIP을 내려받고 파일별 크기/SHA-256을 검증한다. MOLIT은 세 조각도 검증한 다음 전체 ZIP을 재조립한다.

```powershell
python scripts/download_shared_data.py statistics --output D:/jipdam-downloads/statistics
python scripts/download_shared_data.py molit --output D:/jipdam-downloads/molit
```

필요한 묶음 하나만 실행한다. 인터넷 연결과 Drive 파일 다운로드 권한이 필요하다. 내려받은 결과의 ZIP을 새 폴더에 풀고 아래 재구성 명령을 실행한다. 재구성에는 12GB 이상의 여유 공간이 필요하며 압축 해제·DB 출력 경로는 공간이 충분한 드라이브를 선택한다. 다운로드 폴더와 이전 출력은 덮어쓰지 않는다.

Python3.11 이상과 12GB 이상 여유 공간을 준비한다. ZIP 전체 SHA를 위 기록과 대조한 뒤 새 폴더에 풀고 독립 Python 프로세스로 실행한다.

```sh
python -m pip install -r requirements.txt
python shared_data.py verify
python shared_data.py rebuild --output ../rebuilt-new
```

API 키 없이 네트워크를 차단한 상태에서 원본만 읽어 생성한다. 기존 출력은 덮어쓰지 않는다. 실패했으면 새 출력 이름을 선택한다. manifest는 모든 파일 해시/크기·범위/건수/단위/품질·기대 DB의 전체 논리 테이블 digest를 담는다. 외부 ZIP SHA가 패키지 전체의 신뢰 기준이다.

통계 출력은 statistics.sqlite3/raw/manifests/rebuild-verification.json이다. 원문 XML 숫자 정밀도·결측·지역차원/source_view/검수 이력을 복원하고 import_batches.imported_at_utc만 새 적재시각으로 구분해 모든 논리 값을 대사한다. snapshot/statistics.sqlite3는 기존 DB 자체의 보관본이다.

MOLIT 출력 observations에는 전월세/매매/staging DB, canonical에는 종로구→서울 전체 순서로 과거 후보 이력까지 보존한 canonical v3가 있다. batches.archive_root와 rental_snapshots.created_at_utc/rental_observations.ingested_at_utc만 새 환경 위치/적재시각으로 구분하며 나머지 모든 논리 값을 대사한다. 스크립트는 임시 정렬 파일도 출력 드라이브에 둔다. 원본 raw/manifest를 함께 보존해야 역추적이 가능하다. 일반/상세는 별도 관측이고 후보는 pending/unverified다.

## 공유 승인과 기록

초기 자동 승인 검토는 구체적 GitHub 게시 내용과 Drive 원본/DB ZIP·목적지 승인 증거를 요구해 거절했다. 사용자가 각각 명시 승인했고 GitHub App 쓰기 권한도 갱신한 뒤 정상 경로로 게시/업로드했다. 브라우저 우회 게시·자격증명 추출은 하지 않았다.

게시 대상은 통계 #6와 기존 MOLIT #5다. 출처/범위/건수/단위/검수/최종 ZIP 및 조각 SHA/복원 방법/개별 링크를 기록한다. 원본/DB/API 키/자격증명 값은 GitHub에 게시하지 않는다.
