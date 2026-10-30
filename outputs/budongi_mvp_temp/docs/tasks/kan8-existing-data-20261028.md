# TASK-KAN8-EXISTING-001 — 기존 안전·교육·의료 패키지 대사

```toml
kind = "task"
id = "TASK-KAN8-EXISTING-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/16_team_collection_schema_spec.md"]
scope = ["outputs/budongi_mvp_temp/docs/tasks/kan8-existing-data-20261028.md"]
acs = ["TEAM-DATA-001-AC-05"]
```

Jira [KAN-8](https://kwulreobeu.atlassian.net/browse/KAN-8)의 기존 자료 재사용·중복 제외를 확인한다. 새 외부 데이터 수집, 좌표 검수, 단지 매칭, 추천 연결은 별도 승인 경계를 유지한다.

2026-10-28: GitHub 수집 기록과 Drive 메타데이터를 대조하고 네 ZIP을 `.local_runtime/kan8-existing/`에 내려받았다. 각 ZIP 전체 SHA-256이 수집 Issue의 최종값과 같고 ZIP CRC 검사를 통과했다. 네 패키지 모두 raw, normalized JSONL, schema, manifest, validation, 재현 코드가 들어 있다. JSONL 행 수는 패키지 validation의 records와 일치한다.

| 대상 | 기록 | JSONL 행 | 품질·한계 |
| --- | --- | ---: | --- |
| 공시가격 서울 | [#11](https://github.com/keulreobeu/jipdam/issues/11) | 2,782,147 | 원천 미검수; 공시가격 단지코드는 거래 단지 ID와 미연결 |
| 어린이집 서울 25구 | [#16](https://github.com/keulreobeu/jipdam/issues/16) | 4,078 | 원천 미검수; 좌표계 미확인, 비상업 이용 제한 기록 |
| NEIS 학교 전국 | [#12](https://github.com/keulreobeu/jipdam/issues/12) | 12,672 | 정상 12,554·제외 84·거부 34; 좌표 없음 |
| 심평원 병의원·약국 전국 | [#10](https://github.com/keulreobeu/jipdam/issues/10) | 105,532 | 원천 미검수; 좌표계 미확인 |

학교 통학구역 [#36](https://github.com/keulreobeu/jipdam/issues/36)과 교육환경보호구역 [#37](https://github.com/keulreobeu/jipdam/issues/37)도 Drive ZIP의 기록된 SHA-256·CRC, raw/normalized/schema/manifest/validation/코드를 확인했다. JSONL은 각각 629행·3,381행으로 validation과 일치한다. 통학구역의 유효하지 않은 도형 1개와 교육환경보호구역의 2개는 기록상 원본 보존 상태이며, 교육환경보호구역에는 비상업·변경금지 조건이 기록돼 있다. 도형을 독립 검수하거나 변환하지 않았다.

이 결과는 패키지 bytes·CRC·구성 및 행 수 확인이며 원본 전체 재처리나 좌표·이용조건의 독립 검수는 아니다. 잔여 범위와 기존 자료의 이용조건·재현 검증을 완료하기 전 KAN-8은 진행 중으로 유지한다.

추가 오프라인 재현: NEIS의 보관된 13개 원본 페이지로 `code/build_school.py`를 별도 작업 디렉터리에서 실행했다. 12,672행 전체를 원래 JSONL과 순서대로 비교해 `staged_at_utc`만 제외한 차이 0건, 원본 요청 로그 대비 페이지 불일치 0건이다. 12,554 정상·84 제외·34 거부도 재현했다. 이용조건의 독립 검수는 미완료다.

어린이집 XLS 25개는 `xlrd==2.0.1`을 별도 임시 의존성 폴더에 설치해 오프라인 재생성했다. 처음에는 작업 복사본에 `raw_files.json`을 빠뜨려 실패했고, 원본 ZIP에서 해당 메타데이터를 추가한 후 재실행했다. 4,078행 전체는 `staged_at_utc`를 제외하면 원본 정규화 결과와 차이 0건이다. 심평원 원본 ZIP도 별도 재생성해 105,532행 및 진료과목 434,777행 연결 집계를 재현했고, 정규화 105,532행의 같은 비교에서 차이 0건이다. 실제 좌표계·현행성·이용권이나 서비스 연결 검증을 뜻하지 않는다.

공시가격 원본 ZIP을 오프라인으로 재처리해 전국 15,851,336행 중 서울 2,782,147행을 재생성했다. 정규화 JSONL 전 행을 원래 패키지와 순서대로 대조한 차이는 0건이며 별도 constants의 차이는 재생성 `staged_at_utc`뿐이다. 이는 원본 스냅샷에 대한 재현이지 공시가격의 최신성·거래 가격·단지 관계 검수가 아니다. 통학구역과 교육환경보호구역의 원본 전체 재처리는 아직 하지 않았다.

여섯 ZIP의 manifest가 나열한 개별 payload 92개(어린이집33·교육환경10·심평원8·공시가격9·학교22·통학구역10)를 ZIP에서 직접 읽어 각 바이트 수와 SHA-256을 검증했고 불일치 0건이다. manifest에 열거되지 않은 파일의 별도 해시 검증이나 공간자료 재처리·좌표 검수를 주장하지 않는다.

## 공식 이용조건 확인 — 2026-10-28

- [어린이집 포털 이용약관](https://info.childcare.go.kr/info_html5/common/agreeUtili.jsp) 제14조 ④는 포털에서 얻은 정보의 복제·변경·제3자 제공 등에 사전 승낙을 요구한다. 보관 패키지는 Open API의 비상업 제한과 팀 합의를 기록하지만 포털 XLS에 대한 사전 승낙 근거는 없다. 서로 다른 자료·시점·서비스 조건의 적용 관계와 기존 공유/재현의 허용 여부는 기관 확인 전 미확정으로 둔다. 이 조항만으로 이미 허용된 사용이나 기존 권리를 단정하지 않는다.
- [공시가격 공식 파일](https://www.data.go.kr/data/3073746/fileData.do)은 2026-01-01 기준 호별 공시가격이며 현재 페이지는 이용허락범위 제한 없음을 표시한다. 해당 파일 페이지의 표시이며 다른 원천·거래가격까지 확장하지 않는다.
- [심평원 파일 현재 페이지](https://www.data.go.kr/data/15051059/fileData.do)는 2026-09-30판에 공공누리 제1유형을 표시한다. 우리 패키지는 2026-06판이므로 현재 페이지 표시만으로 과거판의 조건을 독립 확정하지 않는다. 보관 manifest의 당시 캡처 기록과 구분한다.
- [전국 통학구역 표준데이터 페이지](https://www.data.go.kr/data/15021149/standard.do)는 제공기관과 기준일을 보여주지만 이용허락 문구를 확인하지 못했다. 별도의 [안전원 SHP 2026-03-20판 페이지](https://www.data.go.kr/data/15159265/fileData.do)는 제한 없음을 표시하나 보관한 2026-09-20판에 그대로 적용하지 않는다. 패키지의 `license_review_status=verified`만으로 CSV·SHP 양쪽 이용권이 검증됐다고 보지 않는다.
- [NEIS 서비스 이용약관](https://open.neis.go.kr/portal/userAgreementPage.do)의 검색 색인에는 데이터의 저작자·출처 표시를 원칙으로 하고 제3자 권리는 별도 조건을 따른다고 표시된다. 다만 원문 직접 열기가 실패해 전체 문맥과 schoolInfo 개별 자료·과거 스냅샷의 적용은 미확정이다. 브이월드 해당 공간파일의 구체적인 현재 조건도 직접 확인하지 못했으며 교육환경보호구역의 기존 CC BY-NC-ND 기록은 유지한다.

위 조사로 신규 사용·재배포·상품 연결이 승인된 것은 아니다. 기관별 정확한 데이터·판본과 사용 목적에 맞는 이용조건 및 사전 승낙을 확인하기 전 KAN-8은 진행 중으로 남긴다.


## 통학구역 패키지 오프라인 재현 — 2026-10-28

보관된 원본 CSV/SHP ZIP과 패키지 코드를 격리 폴더에서 재실행했다. 첫 실행은 Windows에서 SHP reader가 임시 파일을 잡은 채 `TemporaryDirectory` 정리를 시도해 `WinError 32`로 종료 1이었다. 보관 ZIP은 유지하고 로컬 복사 코드에 reader의 `close()`를 임시 디렉터리 정리 전에 추가해 재실행한 결과 종료 0, 전국 CSV/SHP 각 7,132건·서울 출력 629건을 재현했다.

재생성 JSONL 629행은 보관본과 `staged_at_utc`를 제외한 차이 0건, validation은 실행시각과 수정된 parser SHA-256을 제외하면 동일하다. 원래 검증과 같이 전국 CSV/SHP 속성 불일치 668행과 원본 폴리곤 오류 1건이 남는다. 668은 전국 비교 수치로 서울 불일치 수나 동일 학교·단지의 매칭 수가 아니다. 코드 수정안 SHA-256 `96a7281d020dccdce231a7435b8dad5f4a8bac3a12019e5878f0768bf346df95`, 로컬 `.local_runtime/kan8-replay/school-district/`에만 보관했다. 이 결과는 과거 원본의 재현이며 도형 교정·서비스 적용·이용권 확정 또는 원 패키지 소유자 수락을 뜻하지 않는다.


통학구역의 재현 validation에서 전국 속성 차이 668행을 원본 CSV 행 번호·학구ID와 다시 대조했다. 668행 모두 CSV `시도코드`와 같은 공간객체의 SHP DBF `SD_CD` 차이이며, 확인된 쌍은 CSV `61` / SHP `12`로 동일하다. 서울 CSV 시도코드 `11`인 629행에는 이 속성 불일치가 0건이다. 두 코드의 의미·어느 쪽의 정확성·자료 제공 방식 차이는 이 값만으로 판정하지 않으며 변환이나 덮어쓰기를 하지 않았다. 기존 서울 원본의 invalid polygon 1건과 원천 검수 상태는 그대로다.

위 668행의 CSV·DBF 교육청명과 교육청코드도 각각 대조한 결과 모두 양쪽에 `전남광주통합특별시교육청` / `7140000`으로 동일하게 기록돼 있었다. 이는 보관 파일의 표기 확인일 뿐 해당 기관의 현재 실재·코드 체계나 시도코드의 정오를 검증한 결과는 아니다.


## 교육환경보호구역 오프라인 재현 — 2026-10-28

보관 원본 SHP ZIP과 추출기를 격리된 로컬 경로에서 재실행했다. 첫 실행은 Windows 임시 파일 정리 시 reader가 열려 있어 WinError 32/종료 1이었다. 원본 패키지는 보존하고 로컬 복사 코드에서 정리 전에 `r.close()`를 호출한 뒤 재실행해 종료 0, 전국 39,838개 중 서울 3,381개를 재현했다. 보관 JSONL과 `staged_at_utc` 제외 전 행 값 차이 0, validation은 실행시각과 수정 코드 해시 제외 동일이다. 기존 도형 유효성 오류 2건과 고시년도 범위 이상 102건은 그대로 재현됐으며 원본을 교정하지 않았다.

로컬 수정 코드 SHA-256 `58bf1008131b5d3db47c6569acada1bcdedd0dea0f9d13fd7c7dd1d6575735ed`; `.local_runtime/kan8-replay/education-zone/`에만 존재한다. 검산용 임시 좌표 계산 외 공간 도형 변환·저장·배포는 하지 않았다. 이용조건의 구체적 적용 및 패키지 소유자의 수정안 수락, 실제 지도·추천 사용은 여전히 미확정이다.

위키 maintenance/catalog/search 및 재현 범위 `KAN8-LOCAL-REPLAY-20261028`: SKIP/execution_log/DONE/nonblocking. 로컬 검증 실행 기록은 본 Task에 유지하며 전체 이슈 완료나 소유자 수락은 아니다. [Jira 판단 기록](https://kwulreobeu.atlassian.net/browse/KAN-8?focusedCommentId=10115)의 receipt는 DONE이다.
