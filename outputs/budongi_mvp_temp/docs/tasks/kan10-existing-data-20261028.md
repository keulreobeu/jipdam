# TASK-KAN10-EXISTING-001 — 기존 단지·보행 자료 확인

```toml
kind = "task"
id = "TASK-KAN10-EXISTING-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/16_team_collection_schema_spec.md"]
scope = ["outputs/budongi_mvp_temp/docs/tasks/kan10-existing-data-20261028.md"]
acs = ["TEAM-DATA-001-AC-05"]
```

[KAN-10](https://kwulreobeu.atlassian.net/browse/KAN-10)의 기존 수집·보관 범위를 확인한다. 신규 API 호출, 좌표 검수, 단지 매칭 확정과 Drive 업로드는 포함하지 않는다.

2026-10-28: [GitHub #29](https://github.com/keulreobeu/jipdam/issues/29)의 보행 네트워크 ZIP을 Drive에서 `.local_runtime/kan10-existing/osm-seoul.zip`에 다운로드했다. 크기 32,651,793바이트와 Issue의 SHA-256 `3a0d6935e0cd09408d793d7f00dc98deaced59286d960572a1ac213c25f6f7ff` 일치, ZIP 9개 항목 CRC 정상, manifest가 열거한 8개 payload의 크기·SHA-256 일치를 확인했다. 정규화 JSONL 127,140행은 manifest 행 수와 같다. 원본 PBF·경계·정규화·schema·validation·재현 코드가 들어 있다. 서울 전체 커버리지·보행 가능성·거리·좌표 및 단지 연결을 독립 검증한 것은 아니다.

K-apt 기본·시설 [#30](https://github.com/keulreobeu/jipdam/issues/30), 관리비 [#33](https://github.com/keulreobeu/jipdam/issues/33), 동물병원 [#31](https://github.com/keulreobeu/jipdam/issues/31), 반려동물 관광 [#32](https://github.com/keulreobeu/jipdam/issues/32)의 Drive ZIP을 내려받아 기록된 전체 SHA-256·크기와 ZIP CRC를 확인했다. manifest의 개별 payload는 각각 9/9·5/5·2/2·75/75가 일치했다. 내용 대사는 파일 행 수에 한정하며 실제 시설 상태·좌표·이용권을 검수하지 않았다.

- K-apt 기본: scoped raw·profile·amenities 각 3,340행. 전국 XLSX 전체는 공유 ZIP에 없고 scoped raw만 포함돼 최초 전국 원본의 전수 재처리는 아직 할 수 없다.
- K-apt 관리비: JSONL 24,657행. ZIP에 원본 XLSX와 재현 스크립트는 없으며 정규화 CSV/JSONL과 문서만 있다. 원본 170,978행의 독립 재대사에 필요한 원본과 코드 확인이 남았다.
- 동물병원: JSONL 985행. ZIP의 raw는 원본 전체가 아닌 필터된 CSV다. 원래 입력 2,241행에서의 필터 재현은 원본 미확보로 검증하지 않았다.
- 반려동물 관광: 관광목록 1,490행, 상세 41행, 동반 가능 확인 39행, 미확정/상세 없음 1,451행. 원본 상세 전체는 보관되지 않았고 ZIP에 재현 스크립트가 없어 전체 수집 재현은 미검증이다. 확인된 39건도 현장 조건이나 주거단지 규약을 검증한 것은 아니다.

건축HUB [#39](https://github.com/keulreobeu/jipdam/issues/39)는 이슈에 다른 담당자의 진행 중 수집으로 표시돼 있어 중복 호출·재예약하지 않는다. 이슈 문구만으로 실제 실행 프로세스가 현재 살아 있다고 주장하지 않는다. KAN-10은 나머지 원본·재현·이용조건 확인이 남아 진행 중이다.

관리비 정규화 CSV와 JSONL을 24,657행 전부 순서대로 읽어 단지코드·년월 문자열 및 나머지 숫자/NULL 필드를 비교했다. 필드 차이 0, 단지코드·년월 중복 0, 월 범위 202601~202609다. 두 파일은 같은 가공 결과이므로 원본 170,978행의 독립 재처리나 단위 검수 증거가 아니다. Drive에서 기록된 원본 파일명 세 가지를 검색했지만 정확한 이름의 파일은 검색 결과에서 찾지 못했다. 이는 저장소 전체 부재의 증거가 아니다.

K-apt 기본의 scoped raw·profile·amenities 3개 JSONL을 3,340행 전부 순서대로 대조한 결과 원본 행 번호와 K-apt 코드의 불일치 0건, 원본 행 번호 중복 0건이다. 고유 코드 3,194개와 반복 코드 123그룹을 재확인했으며 반복을 병합하지 않았다. 이 검사는 행 계보·코드에 한정하며 전국 원본의 검수나 다른 출처 단지와의 동일성 검증은 아니다.


## 보행망 JSONL 독립 대조 — 2026-10-28

기존 OSM ZIP의 `schema.json`과 정규화 JSONL 127,140행을 스트리밍으로 전수 대조했다. 20개 필드 순서, `osm-way/{source_way_id}` 식별자 형식, 중복 없는 ID, `tags_json`에서 12개 명시 필드로의 값·null 대응은 불일치 0건이었다. LineString 126,182행·MultiLineString 958행, 좌표 768,185개이며 두 좌표값이 유한하고 세계 경위도 범위 안에 있다. 이는 지오메트리의 행/좌표 형식 대조이며 원본 PBF와의 토폴로지, 경계 절단, 실제 접근성이나 전체 서울 커버리지 검증은 아니다.

**스키마 표기 불일치:** `oneway_foot`, `foot_forward`, `foot_backward`는 schema에서 `TEXT`로 기재되어 있지만 실제 JSONL의 각 필드가 127,140/127,140행 모두 null이다. 다른 nullable 텍스트 필드를 `TEXT/NULL`로 기재하고 null policy가 누락 태그를 null로 보존한다고 설명하므로, 스키마의 null 허용 여부가 모호하다. SQLite의 TEXT 타입 자체는 null을 금지하지 않지만 이 제출 계약의 명시 표기와 대조하면 strict 소비자가 거부할 수 있다. 데이터 null을 임의 값으로 채우지 않고 원본 ZIP을 변경하지 않았다. 패키지 소유자의 스키마 정정 또는 명시적 null 허용 계약과 재검증이 필요하며 KAN-10은 진행 중이다.


### 스키마 불일치 원인과 로컬 수정안

보관 추출기의 schema 생성 코드는 정규화 열 이름을 `TAG_FIELDS`와 비교하지만 세 원천 태그는 각각 `oneway:foot`, `foot:forward`, `foot:backward`이고 정규화 열은 콜론이 밑줄로 바뀌어 있다. 이 이름 차이로 세 필드가 일반 `TEXT`로 표시됐다. 코드의 태그명도 같은 방식으로 정규화해 비교하고 세 스키마 타입을 `TEXT/NULL`로 수정한 **로컬 제안**을 `.local_runtime/kan10-existing/osm-schema-proposal-20261028/`에 별도 저장했다. 원본 ZIP과 정규화 데이터는 수정하지 않았다.

제안 스키마로 보관 JSONL 127,140행의 TEXT 타입과 필수 텍스트 null 여부를 다시 대조해 오류 0건, 제안 추출 코드는 Python 컴파일을 통과했다. 제안 schema SHA-256 `b8d6ecacbed55248392233f8d76980c4e7dd43c3b280ebc30c6f647c3ec5f2da`, 제안 코드 SHA-256 `6d3cc0829825d3f49188f200694bb1e01ee9a6a7898d5c2223be8ee0ce766458`; 원본 ZIP 및 개별 코드/스키마 해시는 같은 폴더 receipt에 기록했다. `osmium-tool`, `pyosmium`, Shapely가 없어 추출 전체 재실행은 하지 않았으며, 소유자 승인이나 정정 패키지 배포도 없다. 실제 토폴로지·좌표 검수·추천 사용의 증거가 아니다.


### 보행망 경계 독립 재검사 — 2026-10-28

프로젝트 임시 의존성 `.local_runtime/kan10-deps/`에 Shapely 2.2.0과 pyosmium 4.3.2를 설치한 뒤 보관 ZIP의 경계와 기존 정규화 geometry 전체를 Shapely로 독립 검사했다. 경계 Polygon은 valid, 127,140개 선형은 empty/invalid 0건이다. 기하학적 정확한 `covers` 기준으로 643개는 경계 밖 잔여가 있었으나 `difference` 길이의 최댓값은 `5.638639191321732e-13` 좌표도이며, 기존 기록의 `1e-12`도 허용값 초과는 0건이다. 엄격한 경계 포함과 부동소수 오차를 고려한 허용값 통과를 구분한다. 이 검사는 기존 선형과 보관 경계만 비교했으며 원본 PBF 재추출, 단지 매칭, 보행 가능성 또는 커버리지의 검증이 아니다. Windows `osmium` CLI는 여전히 없어 제안 추출 코드의 전체 재생성은 미실행이다.


### OSM 원본 way 계보 독립 대조 — 2026-10-28

보관 ZIP의 PBF를 별도 임시 경로에 풀어 원본 SHA-256 `68a79665843d5ef7ad11049c5026e82cacf0feb5d125a28f44b2426495cbfa3c`를 재확인한 뒤 pyosmium 4.3.2로 원본 `highway` way를 읽고 정규화 JSONL의 원천 ID·첫/마지막 node ID·전체 태그를 대조했다. 원본 highway way 127,875개 중 정규화 127,140개 모두 원본에 있었고 첫/마지막 node 불일치 0건, 전체 태그 불일치 0건이다. 원본 중 출력에 없는 735개의 제외 이유나 공간 절단의 정확성은 이 검사만으로 독립 재현하지 않았다.

첫 실행은 대조 후 버전 출력에서 존재하지 않는 `osmium.version` 속성을 참조해 종료 코드 1로 실패했으며, 버전 조회를 `importlib.metadata`로 고친 별도 재실행이 종료 코드 0으로 통과했다. 이 검사는 모든 원본 노드 참조·좌표·길 연결성을 검증하거나 전체 추출기를 재실행한 것이 아니다.


### 원본 노드 기반 선형 재구성 대조 — 2026-10-28

pyosmium 4.3.2의 위치 인덱스로 PBF의 출력 대상 way에 속한 노드 좌표를 읽고 Shapely 2.2.0으로 원본 선형을 생성해 보관된 서울 경계와 교차했다. JSONL의 출력 대상 127,140건 모두 원천 way·노드 좌표를 찾았고, 재구성한 경계 내 선형과 보관 형상이 위상적으로 127,140/127,140 일치했다. Hausdorff 거리와 선 길이 차이의 최댓값은 모두 0 좌표도다. 결과 `.local_runtime/kan10-existing/osm-offline-check/geometry-comparison.json`, 종료 코드 0. 위상 일치는 선의 좌표 배열 순서까지 동일하다는 뜻은 아니다.

이 대조는 출력된 127,140개 way의 형상을 대상으로 한다. 원본 way 735개의 osmium export 제외 이유, 원래 추출기 전체의 재실행과 원본 서울 범위의 완전성·실제 보행 가능 여부는 여전히 별도 검증이다.


### 수정안 전체 오프라인 재현 — 2026-10-28

이전 `osmium` CLI 부재 기록 이후 conda-forge `osmium-tool 1.19.1`을 `.local_runtime/kan10-mamba/osmium/`에 격리 설치했다. 보관 ZIP에서 원본 PBF·경계를 별도 작업 폴더에 복사하고 기존 Python 라이브러리 pyosmium 4.3.2·Shapely 2.2.0과 수정 제안 추출 코드를 실행한 결과 종료 코드 0, 원본 highway way 127,875건, 내보내기에서 비선형 형상으로 제외 735건, 출력 127,140건을 재현했다. 제외 사유는 해당 osmium 1.19.1 선형 export의 분류에 한정되며 실제 보행 불가 판정이 아니다.

재생성 JSONL 127,140행은 기존 보관 JSONL과 순서대로 JSON 값이 모두 일치했고, 재생성 schema도 앞서 만든 수정 제안 schema와 동일하다. 재생성 ZIP은 9개 항목 CRC 정상, manifest 8개 파일의 bytes/SHA-256 대조 오류 0건이며 SHA-256 `006845ab58127bf30cf8dcc08f31244eaa2c847ae362472427226106bd48b4d1`이다. 재현 ZIP은 실행 시각 등 메타데이터를 포함한 로컬 검증 산출물로 원본과 별도이며 공유하거나 소유자 승인을 받은 정정본이 아니다. 기존 원본 ZIP은 변경하지 않았다. 전체 서울 커버리지, 실제 보행 가능성, 좌표 검수 및 단지 연결은 확인되지 않았다.

위키 maintenance/catalog/search 및 재현 범위 `KAN10-LOCAL-REPLAY-20261028`: SKIP/execution_log/DONE/nonblocking. 로컬 검증 실행 기록은 본 Task에 유지하며 전체 이슈 완료나 소유자 수락은 아니다. [Jira 판단 기록](https://kwulreobeu.atlassian.net/browse/KAN-10?focusedCommentId=10116)의 receipt는 DONE이다.
