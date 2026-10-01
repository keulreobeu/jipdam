# 집담 (Jipdam) 애플리케이션

**집담 고도화 및 LLM 평가 실행 계획**의 Phase 0~5를 위한 작은 출발점입니다. 팀 저장소는 [keulreobeu/jipdam](https://github.com/keulreobeu/jipdam)이며 기존 작업 폴더와 `budongi` Python 모듈·CLI는 호환성을 위해 유지합니다. 패키지 설치 후에는 `jipdam` 명령도 사용할 수 있습니다.

## 개발 문서와 작업 순서

새 기능은 요구사항 질문·Plan → 확정 Spec → 필요 시 ADR → Task → 구현 → 테스트·평가 → 문서 동기화 순서로 진행합니다. 워크스페이스에 설치된 gstack을 기본 개발 스킬로 사용하고, 집담 전용 `jipdam-workflow`로 기존 Spec·ADR·데이터·평가 계약에 연결합니다. 확정된 내용만 프로젝트 문서에 반영합니다. 작업 규칙은 [AGENTS.md](AGENTS.md), 설치·확장 방법은 [gstack 안내](../../docs/gstack.md)에 있습니다.

- [Project Spec](docs/specs/00_project_spec.md): 현재 구현, 목표, 공통 제약
- [Structured Search](docs/specs/03_structured_search_spec.md), [Router](docs/specs/04_router_spec.md), [RAG](docs/specs/05_rag_spec.md), [Agent Tools](docs/specs/06_agent_tools_spec.md): 기능별 현재 상태와 도입 조건
- [Data Model](docs/specs/02_data_model_spec.md), [Evaluation](docs/specs/08_evaluation_spec.md): 데이터·검증 계약
- [ADR](docs/adr/ADR-001-structured-tools-first.md): 중요한 설계 선택과 이유
- [Current Task](docs/tasks/current.md): 다음 구현 단위
- [Wiki](docs/wiki/README.md): 실험과 개발 과정 기록

Spec의 `CURRENT`는 확인된 구현, `TARGET`은 계획, `OPEN QUESTION`은 미결정 사항입니다. Router·RAG·Hybrid는 현재 구현 범위에 포함되지 않습니다.

## 현재 구현 범위

- 2023년 이하의 불변 스냅샷을 SQLite에 적재하는 정규화 CSV 계약
- `apartment`/`transaction`/`location`/`facility` 스키마와 원천 ID·날짜·파일 해시 기록
- 검증된 `search_apartments`, `search_transactions`, `get_apartment_detail` 함수
- 로컬 OpenAI 호환 채팅 엔드포인트의 Tool Calling 연결, 최대 5회 호출, 호출 로그
- Tool 선택·인자·반환 ID의 첫 결정적 평가기
- 기존 저장소의 주소 분리·CSV 인코딩 탐지 로직을 작은 호환 모듈로 재구성

기존 저장소의 [README](https://github.com/keulreobeu/Real_estate_Chatbot_by_gemma4)와 ZIP을 확인했습니다. GitHub 저장소에는 `data/original` 원본 CSV와 실제 평가 CSV가 들어 있지 않습니다. 따라서 여기에는 실거래 기록이나 200건 Golden을 임의로 만들지 않았습니다. 이전 파이프라인의 `공급액(만원)`은 분양/공급액이며 실거래가가 아닙니다.

## 빠른 시작

### Docker Compose

기본 구성은 현재 CLI와 SQLite를 컨테이너로 실행합니다. 데이터베이스와 로그는 프로젝트의 `data/`, `runs/`, `tool_runs/`, `reports/`에 남습니다. 모델 없이 초기화·조회부터 사용할 수 있습니다.

```powershell
docker compose build budongi
docker compose run --rm budongi init-db
docker compose run --rm budongi doctor
```

로컬 Ollama도 Docker로 실행하려면 선택형 `llm` 프로필을 켭니다. 모델 파일은 Docker named volume에 보존되고 Ollama 포트는 호스트에 공개되지 않습니다.

```powershell
docker compose --profile llm run --rm ollama pull qwen3.5:4b-q4_K_M
docker compose --profile llm run --rm budongi-llm ask `
  --snapshot-id <snapshot-id> --model qwen3.5:4b-q4_K_M `
  --question "강서구에서 10억 이하 전용 84㎡ 단지를 찾아줘"
```

CPU 실행을 기본으로 둡니다. GPU 전달은 개발 환경별 설정이 달라 별도 구성 대상입니다. Docker 환경의 `ollama` 서비스 연결은 Compose에서만 명시적으로 허용하며, 다른 외부 호스트는 계속 거부합니다. 전체 경계는 [Runtime and Container Spec](docs/specs/09_runtime_spec.md)에 있습니다.

### Python 직접 실행

이 폴더에서 Python 3.11 이상을 사용합니다. 표준 라이브러리만 필요합니다.

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python -m budongi.cli --db .\data\historical\serving.sqlite3 init-db
python -m budongi.cli --db .\data\historical\serving.sqlite3 doctor
python -m unittest discover -s tests -v
```

실제 2023 자료를 준비한 뒤 다음을 실행합니다. `snapshot_id`는 같은 파일·정제 규칙에 대해 고정하고, 수정 자료는 새 ID로 가져옵니다.

```powershell
python -m budongi.cli --db .\data\historical\serving.sqlite3 import-snapshot `
  --snapshot-id budongi_2023_v1 --snapshot-date 2023-12-31 `
  --apartments .\data\historical\apartments.csv `
  --transactions .\data\historical\transactions.csv

python -m budongi.cli --db .\data\historical\serving.sqlite3 tool `
  --snapshot-id budongi_2023_v1 --name search_apartments `
  --arguments '{"district":"강서구","max_price_krw":1000000000,"area_sqm":84}'
```

로컬에서 4B 모델의 OpenAI 호환 Tool Calling 엔드포인트를 실행한 후:

```powershell
python -m budongi.cli --db .\data\historical\serving.sqlite3 ask `
  --snapshot-id budongi_2023_v1 --model <실제-모델-ID> `
  --endpoint http://127.0.0.1:11434/v1/chat/completions `
  --question "강서구에서 10억 이하 전용 84㎡ 단지를 찾아줘"
```

엔드포인트는 예시이며, 해당 서버와 모델의 호환성·양자화·메모리 사용량은 실행 전에 확인해야 합니다. 외부 주소는 코드에서 거부합니다.

### 로컬 4B급 Tool Calling 시험 (가상 데이터)

사용자 지시에 따라 실제 데이터 수집·단지 매칭은 보류하고, 독립적인 모델 연결을 시험했습니다.
[Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B)의
[Ollama `qwen3.5:4b-q4_K_M`](https://ollama.com/library/qwen3.5:4b)를 사용했습니다.
시험한 서버는 Ollama `0.34.4`, 모델 다이제스트는
`2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`,
양자화는 `Q4_K_M`, 설정 컨텍스트는 8192 토큰입니다. GPU는 RTX 5060 Ti 16GB입니다.
포터블 실행 파일은 [공식 Ollama 릴리스](https://github.com/ollama/ollama/releases)에서
SHA-256 검증 후 `.local_runtime/`에 두며, 모델·시험 결과도 같은 무시된 폴더에 둡니다.

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python scripts/setup_ollama_portable.py
$env:OLLAMA_MODELS = (Resolve-Path .local_runtime).Path + '\models'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_CONTEXT_LENGTH = '8192'
$binary = (Resolve-Path .local_runtime\ollama-v0.34.4\ollama.exe).Path
Start-Process -FilePath $binary -ArgumentList 'serve' -WindowStyle Hidden
& $binary pull qwen3.5:4b-q4_K_M
python scripts/make_synthetic_smoke.py
python scripts/record_local_model.py
python -m scripts.run_synthetic_smoke --run-prefix smoke_recheck
```

Ollama는 Windows의 사용자 설정 폴더에도 파일을 생성합니다. 가상 스냅샷은 단지 2곳과 거래 3건만
담고 있으며, `doctor`는 이를 `synthetic_only`로 표시하고 실측 평가 준비 완료로 판정하지 않습니다.
FACT, FILTER, NO_MATCH, COMPARE 네 질문에서 모델의 도구 호출과 답변이 실행됐습니다.
첫 FILTER 실행은 도구 인자를 두 차례 잘못 제안했고, 프롬프트 수정 후 같은 질문은 한 번의 유효
호출로 끝났습니다. COMPARE에서 모델이 잘못된 차액을 생성한 사례는 당시 `price_claim_v1` 검사로
차단하고 도구 결과의 원래 금액·계약일·거래 출처로 대체했습니다. 현재 구현은 `answer_grounding_v2`로
가격·ISO 날짜·명시한 단지/거래 ID·출처 쌍도 검사하며, 실패한 원 답변은 안전 요약으로 대체합니다.
재현 로그와 환경 정보는
`.local_runtime/synthetic_smoke/`에 있습니다. 이는 실제 부동산 정확도나 Phase 0~5 완료 근거가 아닙니다.

## 입력 데이터 계약

### 공공 API에서 원본 받기

`scripts/fetch_public_data.py`는 [국토교통부 아파트 매매 실거래가 상세 자료](https://www.data.go.kr/data/15126468/openapi.do)와
[한국부동산원 청약홈 분양정보 조회 서비스](https://www.data.go.kr/data/15098547/openapi.do)를 조회합니다.
두 서비스 모두 공공데이터포털에서 **각각 활용신청**이 승인되어야 합니다. 인증키는
`DATA_GO_KR_SERVICE_KEY` 환경변수에서만 읽으며 파일과 출력에 남기지 않습니다.
공공데이터포털의 인코딩된 일반 인증키도 그대로 입력할 수 있습니다.

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
$env:DATA_GO_KR_SERVICE_KEY = Read-Host -MaskInput '일반 인증키'

# 지역코드 11110(종로구), 계약월 2023년 1월 아파트 매매
python scripts/fetch_public_data.py molit-trades --lawd-cd 11110 --deal-ymd 202301

# 모집공고일 기준 2023년 1월 APT 청약 공고
python scripts/fetch_public_data.py applyhome-apts `
  --start-date 2023-01-01 --end-date 2023-01-31

# 위 공고의 주택관리번호로 주택형별 정보 조회
python scripts/fetch_public_data.py applyhome-models --house-manage-no 2023820001
```

각 실행은 `data/provisional/api/` 아래 새 폴더에 응답 페이지 원본, `rows.jsonl`,
`manifest.json`을 저장합니다. 매니페스트에는 요청 범위·조회 시각·원본 해시가 포함됩니다.

### 임시 단지의 2023년 지역별 거래 수집

임시 카탈로그 주소를 [행정표준코드관리시스템 법정동 코드](https://www.code.go.kr/stdcode/regCodeL.do)에
연결해 지역별·월별 실거래 응답을 수집합니다. 코드 다운로드는 조회 시점 자료이며 생성·폐지일이
포함되지 않습니다. 2023년 이후 행정구역 변경으로 현재 API가 옛 구 코드에 0건을 반환하는 경우가
있어 [공식 코드 변경 공지](https://code.go.kr/bbsmng/dataBbsL.do)를 참고해 새 구 코드를 추가 조회합니다.

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
$env:DATA_GO_KR_SERVICE_KEY = Read-Host -MaskInput '일반 인증키'
python scripts/fetch_official_district_codes.py --output-dir data/provisional/legal_district_codes
python scripts/fetch_catalog_trades_2023.py             # 548단지·73지역·876요청 계획 확인
python scripts/fetch_catalog_trades_2023.py --execute   # 첫 범위 수집·원본 검증
python -m scripts.fetch_successor_trades_2023 --execute # 변경된 11지역·132요청
python -m scripts.report_catalog_trade_matches         # 사람 검수용 매칭 후보
```

기존 코드 원본이 달라지면 새 출력 폴더에서 다시 계획을 세웁니다. 수집 명령은 완료된 응답의
해시·행 수·지역코드·계약월을 재검증하고 다음 요청부터 재개합니다. 결과는
`data/provisional/api/molit_2023_catalog/`, `molit_2023_successors/`,
`data/provisional/matching_2023/report.json`에 있습니다. `candidates.csv`는 이름·동·지번의
일치 근거와 비교 대상 실거래 단지명을 담은 검수표입니다. 매칭 결과는 **후보**이며,
동일 지번에 이전 단지가 있을 수 있으므로 단지 식별자와 거래 이력의 검수가 필요합니다.

조회 연도가 2023년이어도 오늘 받은 응답이므로 **2023년 말 당시의 상태**로 간주하지 않습니다.
실거래 응답의 해제 여부와 청약 공고의 공급 정보는 서로 다른 자료이며, 원본 검수와 단지 ID
매칭 전에는 `data/historical/serving.sqlite3`에 적재하지 않습니다.
첨부된 국토교통부 기술문서에서 `dealAmount`는 **만원**, `aptSeq`는 **단지 일련번호**이며,
`cdealType`/`cdealDay`는 해제 정보입니다. 문서의 응답 필드에는 개별 거래의 고유 ID가 없으므로
동일 거래의 정정 버전을 자동 연결했다고 간주하지 않습니다.

### 정규화 입력

`apartments.csv` 필수 열: `apartment_id,name,source,source_id,valid_date`.
선택 열: `address,province,district,neighborhood,built_year,lat,lon,station_name,station_distance_m`.

`transactions.csv` 필수 열: `transaction_id,apartment_id,contract_date,price_krw,area_sqm,status,source,source_id,valid_date`.
선택 열: `reported_date,changed_date,floor`.

날짜는 `YYYY-MM-DD`, 금액은 **원 정수**, 면적은 **㎡**, 거리는 **m**입니다. `status`는 `valid/canceled/corrected` 중 하나입니다. 동일한 `source`와 `source_id`의 수정 이력은 최신 `valid_date`가 효력을 갖습니다. 취소된 최신 버전은 검색에서 빠집니다. 식별자와 정정 이력을 보존해야 하며, 결측 계약일이나 출처를 추정해서 채우면 안 됩니다.

`facilities` 테이블은 마련되어 있지만 시설 수집·적재 코드는 아직 없습니다. `get_apartment_detail`의 주변 정보도 현재는 위치와 역 거리까지만 제공합니다.

## 평가 파일

실제 데이터로 검수한 Golden을 `data/eval/dataset_v1.jsonl`에 둡니다. 기본 필드는 `id`, `split`, `task_type`, `question`, `expected_tool_calls`, `expected_entities`, `required_facts`, `source_ids`, `valid_date`, `snapshot_id`입니다. `expected_tool_calls`는 `[{"tool":"...","arguments":{...}}]` 형식입니다. CSV에는 구조화 claim guard와 Golden 필수 사실의 coverage가 따로 기록됩니다. coverage는 답변에 필수 정보가 빠졌는지 재며, 근거 없는 추가 주장 전체를 찾는 generation 정확도와는 구분합니다. 자세한 문자열·숫자·단위 비교 규칙은 [Evaluation Spec](docs/specs/08_evaluation_spec.md)을 따릅니다.

```powershell
python -m budongi.cli --db .\data\historical\serving.sqlite3 run-eval `
  --snapshot-id budongi_2023_v1 --golden .\data\eval\dataset_v1.jsonl `
  --model <실제-모델-ID> --run-id baseline_v1
```

결과는 `tool_runs/`, `runs/`, `reports/`에 저장됩니다. 실험의 모델 버전·데이터 해시·생성 설정을 보강하고, 답변 사실 추출 평가를 완성한 뒤에만 Phase 5 완료를 선언합니다.

## 다음 작업

사용자가 제공한 `apartment_20230905 - apartment_20230905.csv.csv`를 출처·기준일 미확인
**임시 단지 자료**로 `data/provisional/apartment_20230905/`에 복사했습니다. 재생성 명령과
제약은 [임시 자료 안내](data/provisional/README.md)에 있습니다. 이 자료는 단지·주소·좌표·역 거리
매핑 개발에 사용합니다. 현재 카탈로그는 실거래 기반 가격 조회나 실제 평가용 스냅샷이 아닙니다.

1. 검수 Golden의 `required_facts.entity_aliases`를 채우고 단지명·ID 별칭의 사람 검수 기준을 확정합니다.
2. 실제 자료 작업을 다시 시작할 때 임시 단지 자료의 원천·기준일과 거래 식별자·정정 이력을 검수합니다.
3. 검수된 실제 스냅샷을 만든 뒤 FACT/FILTER/COMPARE/NO_MATCH 약 200건을 사람 검수해 분할합니다.
4. 답변 전체의 근거 없는 추가 주장까지 재는 평가기를 확장해 실제 Tool 결과와 답변 사실을 단계별로 평가합니다.

의미 검색, 최신화, Judge, LoRA, Adapter/Model Routing은 초기 평가 이후에 도입합니다.
