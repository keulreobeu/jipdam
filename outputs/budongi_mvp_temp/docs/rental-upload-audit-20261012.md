# 2026-10-12 첨부 전월세 DB 점검

사용자가 제공한 `전월세 추천 데이터.zip`에는 `serving.sqlite3` 하나(77,824바이트)가 있다. 실제 수집 자료가 아닌 `synthetic_rental_demo`의 허구 예시이며, 이번 환경에 기존 봉인 스냅샷을 그대로 복원했다.

## 복원 위치·계보

- DB: `data/rental/synthetic-demo/serving.sqlite3`
- 원본 ZIP 보존: `data/rental/raw/20261012-upload/전월세 추천 데이터.zip`
- 기계 판독 점검·해시 기록: `data/rental/raw/20261012-upload/import-manifest.json`
- 로컬 진단용 합성 요청: `data/rental/synthetic-demo/request.json` (이번에 작성한 시험 입력)
- ZIP SHA-256: `6b7fe1637347bafc846a204fcae2825b7b2d0caee5b40cf81da8e7c6928fb8b7`
- DB SHA-256: `f53c0a1ffded8e7f2fe409793e5a73c8b7e74f8d6c99d07390d92d4095ac7a60`

현재 작업 폴더에는 복원 전 SQLite DB가 없었다. 별도 rental 경로를 사용했으며 역사 스냅샷을 생성하지 않았다. DB 파일의 바이트·품질 상태·생성 시각을 유지했다.

## 확인된 내용

| 항목 | 결과 |
| --- | --- |
| 스키마 | `rental_v1` |
| 스냅샷 | `synthetic_rental_demo_v1` 1개, 봉인됨 |
| 품질 | `synthetic_only`, 매니페스트 `fictional=true` |
| 기준일 | 2026-10-06 |
| DB 생성 시각 | 2026-10-07 11:36:51 KST |
| 데이터 출처 | `synthetic_rental_demo` |
| 지역 코드 | `11110` 종로구 — 합성 예시의 설정값 |
| 단지·좌표 | 합성 단지 3곳, 합성 좌표 3쌍 |
| 전월세 관측 | 월세 예시 3건, 전세 0건 |
| 계약일 범위 | 2026-09-15 하루 — 합성 예시의 설정값 |
| 보증금·월세 | 각각 1.1억/65만원, 1.2억/70만원, 1.3억/75만원 |
| 면적 | 모두 59.9㎡ |
| 매칭 | 합성 fixture의 confirmed 3건 |
| 역·마트·공원·병원 | 시설 0건, 커버리지 기록 0건 |
| 실제 수집 전월세 관측 | 이 첨부에서는 확인되지 않음 (0건) |

매니페스트가 참조하는 `synthetic-input.json`과 그 SHA-256은 DB에 남아 있지만 해당 원본 파일은 ZIP에 없다. 따라서 원본 파일 해시의 재검증은 불가능하다. DB의 `raw_payload_json`에 있는 허구 표시와 예시 값을 확인했다. 날짜·지역의 설정값으로 실제 수집 범위나 수집 완료 여부를 판단하지 않는다.

## Validation

Python 3.12.10, SQLite 3.49.1에서 검사했다. 프로젝트 로컬 `.venv`에 앱과 선언 의존성을 설치했다 (`cryptography` 50.0.2). 기본 셸의 Python에는 해당 의존성이 없었으므로 아래 CLI는 프로젝트 가상환경으로 실행한다.

- ZIP 내부 DB와 복원 DB의 SHA-256 일치. 조회·추천 검사 후에도 DB 해시 동일.
- `PRAGMA integrity_check`: `ok`; `PRAGMA foreign_key_check`: 위반 0건.
- 봉인 상태·합성 품질·월세 3건/전세 0건과 단지/시설/매칭 행 수 확인.
- `recommend_rentals`: 기본 합성 거부 확인; 명시적 합성 허용 시 시험 요청의 후보 2곳 반환. 역 선호는 `unknown`이며 실제 시설이 없다는 판정으로 바꾸지 않음.
- 아래 CLI 실행 성공 (종로구, 보증금 1.3억원/월세 75만원 상한, 합성 직장 직선거리 500m 필수, 역 500m 선호).
- 루트 `.venv/Scripts/python.exe -X utf8 scripts/verify_environment.py`: SDD 검사 통과, 앱 82개 테스트 중 81개 통과/1개 OS 자격증명 세션 관련 건너뜀, 팀 도구 18개 통과, 모델 없는 합성 CLI smoke 통과. OS 자격증명 검사는 이번 DB 복원 범위 밖이며 그 검증 완료를 주장하지 않는다.

프로젝트 루트에서 재조회:

```powershell
./.venv/Scripts/python.exe -X utf8 -m budongi.cli recommend --rental-db outputs/budongi_mvp_temp/data/rental/synthetic-demo/serving.sqlite3 --snapshot-id synthetic_rental_demo_v1 --request outputs/budongi_mvp_temp/data/rental/synthetic-demo/request.json --allow-synthetic
```

## 남은 조건

이 첨부로 확인되는 것은 합성 전월세 데모 준비까지다. 실제 수집 범위 점검에는 실제 원본 응답·요청 지역/월/페이지별 매니페스트 또는 실제 관측이 담긴 DB가 필요하다. 실제 시설·단지 매칭·전월세 추천 품질·Golden 평가는 완료되지 않았으며 새 외부 수집은 실행하지 않았다.

gstack QA 스킬과 runtime은 이 환경에 설치되지 않았고 Bun도 없어 사용하지 않았다. 루트 README의 공통 Python 검증 경로를 사용한다.
