# 전월세 단지 연결 사람 검수·적용 — 2026-10-20

상태: 사용자 검수 승인(203,159건) 및 격리 serving 적용 완료. 추천은 원천 거래 상태 확인 전까지 차단한다.

## 입력과 범위

- 기존 승인 자료만 사용했다. 새 API 호출, 새 데이터셋 적재, 좌표/시설 수집은 없다.
- 전월세 입력: 복원된 `rental.sqlite3` (238,620 observations).
- 대조 입력: 같은 보존 배치의 `staging.sqlite3`에서 `raw/trade-detail/` 아래 매매 상세 원본 행.
- 전월세 DB SHA-256: `aedd99bf8f4c11eb71ad13615f4be738fe6bbf9f28ef7a03dec81fbaf5c51e53`.
- staging DB SHA-256: `95a60415c7844f20c2dcacb9532cff2dafe5a1714a3314dc70b13bb6f368f211`.

## 대조 결과

전월세 원본의 `aptSeq`를 매매 상세 출처의 `aptSeq`와 비교했다. 이름만으로 연결하지 않았다. 유일 일치 판정은 자치구 코드, 아파트명, 법정동, 지번 네 값이 일치하고 그 네 값에 해당하는 매매 상세 `aptSeq` 후보가 하나인 경우다.

| 결과 | 건수 |
| --- | ---: |
| 전월세 관측 | 238,620 |
| 전월세 관측 중 `aptSeq` 누락 | 0 |
| 전월세 `aptSeq` 그룹 | 7,453 |
| 매매 상세에서 관측된 고유 `aptSeq` | 5,937 |
| 네 속성과 같은 `aptSeq`가 유일한 관측 (5,156개 그룹) | 203,159 |
| 속성 일치는 있으나 `aptSeq` 후보가 복수인 관측 (2개 그룹) | 72 |
| 이름·지역·동·지번 후보가 다른 `aptSeq` 하나를 가리킨 관측 (2개 그룹) | 5 |
| 매매 상세에서 네 속성과 일치하는 후보를 찾지 못한 관측 (2,293개 그룹) | 35,384 |

사전 대조 결과 203,159건(5,156개 단지 ID 그룹)이 승인 기준을 만족했고 35,461건은 예외다. 사용자가 승인 기준과 수량을 확인한 뒤 앞의 부분집합만 확정 연결했다. 매매 상세 자료에서 확인할 수 없던 예외 단지 ID는 자동 생성하지 않았다.

## 사람 검수 자료

검수용 후보 파일은 무시 규칙이 적용된 `data/rental/review_candidates/`에 있다.

- `aptseq-match-candidates.csv`: 전월세 `aptSeq`별 7,453행. 승인한 5,156개 그룹만 `confirmed`/`approved`와 검수자·시각·근거를 기록하고 나머지는 pending이다.
- `aptseq-match-exceptions.csv`: 예외 관측 35,461행과 가능한 다른 `aptSeq` 후보 및 두 출처의 행 위치. 모두 미확정으로 남겼다.
- `summary.json`: 입력 DB 해시, 검수 결과 건수와 산출물 SHA-256.

승인 기록이 반영된 후보 CSV SHA-256은 `a01a3803f0515b4db90b20f17848c04c9cdee190b12d3df68534b4fc1766cc32`, 예외 CSV SHA-256은 `fdd0b5ab14be9627c9056db559d0d403700f78938809d04c0c3e6a15e449f746`이다.

관계 후보의 namespace는 프로젝트의 공식 단지 키 계약 `molit_apt_trade_detail:aptSeq`를 사용했다. 사용자는 2026-10-20에 아래 기준과 수량을 승인했다.

- 같은 `aptSeq`이며 자치구 코드·단지명·법정동·지번이 모두 일치하고 해당 속성 후보가 하나인 5,156개 ID 그룹, 전월세 관측 203,159건만 `confirmed` 관계로 적용한다.
- 예외 35,461건(속성 중복 ID 72건, 다른 ID를 가리키는 5건, 상세 후보 없음 35,384건)은 미확정으로 남긴다.
- 원천 거래 취소·정정 상태는 확인 전까지 차단한다. 238,620건의 상태는 `unknown`으로 보존하고 `valid`로 추정하지 않는다.
- 승인 시각: `2026-10-20T01:48:58Z`, 검수자 표기: 사용자. 이는 채팅의 명시적 승인 기록이며 서명 기반 인증은 아니다.

재통합 대사에서 승인 대상 중 200건의 공식 ID 32개가 종전 canonical에 없었다. 이들은 보존된 trade-detail 원본에는 있었지만 거래 관측 유효기간 밖이라 관측 행만 정규화된 경우였다. 승인 범위의 official `aptSeq` entity를 모든 보존 상세 원본 행에서 추출하도록 canonical 통합을 보완했다. 기간 밖 거래 관측을 추가하거나 임대 관측에 자동 연결하지는 않는다. 새 canonical 스냅샷과 serving은 기존 스냅샷을 수정하지 않고 별도 경로에 생성한다. 적용 후의 입력/출력 해시, 연결 건수와 준비 상태는 아래 적용 기록에 기록한다.

## 남은 데이터 게이트

- 원천 전월세 238,620행 모두 정규화 `source_status`가 기록되지 않았다. 저장된 25개 응답 키에는 `cdealType`과 `cdealDay`가 없다. 취소/정정 상태를 추측해 `valid`로 채우지 않았다. [공식 API 페이지](https://www.data.go.kr/data/15126474/openapi.do)는 이 조회가 REST/XML이고 기술문서(HWP)를 제공한다고 설명하지만, 페이지에 표시된 정적 필드 목록만으로 현재 저장 응답의 누락 상태를 보충할 수는 없다.
- 현재 serving 추천은 관계 승인 외에도 원천 상태 검수가 필요한 경우 `data_not_ready`를 반환한다. 좌표와 시설 자료도 별도로 없으므로 위치·시설 조건을 확인할 수 없다.
- 이 후보 자료만으로 실제 추천 가능 상태나 데이터 품질 완료를 선언하지 않는다.

## 적용 기록

2026-10-20 사용자 승인 부분집합을 별도 패키지와 serving 경로에 적용했다. 원본 canonical 및 보존된 전월세·staging DB는 수정하지 않았다.

| 산출물 | 결과 |
| --- | --- |
| 확정 연결 | 203,159 observations / 5,156 `aptSeq` groups |
| 예외 | 35,461 observations remain unconfirmed |
| 원천 상태 | 확정 연결 203,159건 모두 `unknown`; 연결되지 않은 35,461건은 `unreviewed` |
| canonical v3 complexes | 5,937; 47개는 기간 제외 상세 원본에서 official ID만 보존. 거래 관측은 새로 포함하지 않음 |
| canonical SHA-256 | `e1ec30431188cf0942a20bca52a797bc952c0d7da4a1fd861da3685e256e0574` |
| review package | `data/rental/review_packages/reviewed_20261020`; manifest SHA-256 `eccbde13c34c4b890bd6204e41ba560e4eb25252f5ca191f85ff45441d7fd270` |
| candidate CSV SHA-256 | `a01a3803f0515b4db90b20f17848c04c9cdee190b12d3df68534b4fc1766cc32` |
| exceptions CSV SHA-256 | `fdd0b5ab14be9627c9056db559d0d403700f78938809d04c0c3e6a15e449f746` |
| serving DB | `data/rental/serving/reviewed-20261020.sqlite3`; SHA-256 `8369658d4866d2f3277eecfbe47ab7eeafd16df7c731c611a527c98224e8f69d` |

적용한 serving은 총 238,620건 중 전세 119,631건(연결 112,278), 월세 118,989건(연결 90,881)이며 `PRAGMA integrity_check=ok`, FK 위반 0이다. 직접 추천 함수에 유효한 전세 요청을 넣어 `data_not_ready`, 결과 0건을 확인했다. 알려지지 않은 취소·정정 상태가 `valid`로 승격되지 않았다.

`rental-readiness --canonical-db <canonical> --database <serving> --review-package <package>`는 원본/패키지 검증을 통과했고 전체 readiness는 `needs_input`이다. 좌표·시설·coverage가 없고, 사용자 지정 로컬 모델도 없다. 따라서 전월세 관측은 단지 연결 완료지만 현재 추천 자격을 갖춘 건은 0이며 실추천 품질 검증도 미완료다. 준비/추천 검증 커맨드와 구체 응답은 이 Task의 로컬 실행 기록에 연결한다.

## 검수 후 단계

다음 단계는 원천 상태를 확인할 수 있는 승인된 출처 자료를 확보하는 것이다. 새 수집·추가 출처·좌표·시설은 기존 범위에 포함되지 않는다. 승인된 후에도 새 패키지의 원본 해시·행 계보 대사를 거쳐 serving을 재생성하며, 원본 canonical/거래 DB는 수정하지 않는다.
