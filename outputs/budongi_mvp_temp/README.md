# 집담 (Jipdam) 애플리케이션

승인된 목표는 **서울 아파트 전월세 단지 후보의 조건별 추천·비교 웹 데모**입니다. 채팅과 선택적 로컬 LLM 후속 질문, 실제 canonical DB의 read-only 추천 API, 니즈 비교·전체 거래 상세/지도 화면의 첫 구현을 제공합니다. 현재 canonical에는 전월세 관측 238,620건이 있지만 확정 단지 연결이 0건이므로 제품은 `data_not_ready`를 표시합니다. 보존된 역사 스냅샷·세 Data Tool·로컬 모델·합성 평가, 합성 전월세 CLI와 Windows 계정 기반 암호화 API 키 보관함은 기존 경로로 유지됩니다. 팀 저장소는 [keulreobeu/jipdam](https://github.com/keulreobeu/jipdam)이며 `budongi` Python 모듈·CLI 호환성을 유지합니다.

2026-10-13 추가 구현: 서울 세 API의 확정된 원본 수집과 오프라인 통합 DB, 공식 ID 관계·미확정 후보·반복/증분 적재 및 등록 파일 입력을 구현·검증했습니다. [실행 문서](docs/canonical-db.md)와 [실제 검증](docs/canonical-validation-20261013.md)을 따릅니다. 후속 대화형 전월세 MVP의 첫 웹/실 DB 경로는 [실행 안내](#대화형-db-전월세-mvp), 검증 범위·현재 데이터 미준비 상태는 [검증 기록](docs/rental-mvp-validation-20261013.md)을 참고하세요.

사용자가 제공한 통계 엑셀 30개는 별도 `data/statistics/statistics.sqlite3`에 오프라인 보존·적재했습니다. `jipdam statistics import/status/audit`는 원본 셀 계보·기간·결측·재실행·심리 반올림 중복과 후속 메타데이터 근거를 관리합니다. [사용·조회·추가 자료 후보](docs/statistics-storage.md)와 [실제 수입 검증](docs/statistics-validation-20261013.md)을 따릅니다.

## 개발 문서와 작업 순서

다른 PC에서 필요할 때 Drive의 [공유 패키지](docs/shared-data.md)를 내려받아 원본으로 DB를 재구성할 수 있습니다. 다운로드 CLI는 파일별 크기와 SHA-256을 확인하며 ZIP/DB/원본은 Drive에, 코드·설정·수집 기록은 GitHub에 보관합니다. 재구성은 실제 검증 기록을 참고하세요.

새 기능은 요구사항 질문·Plan → 확정 Spec → 필요 시 ADR → Task → 구현 → 테스트·평가 → 문서 동기화 순서로 진행합니다. 워크스페이스에 설치된 gstack을 기본 개발 스킬로 사용하고, 집담 전용 `jipdam-workflow`로 기존 Spec·ADR·데이터·평가 계약에 연결합니다. 확정된 내용만 프로젝트 문서에 반영합니다. 작업 규칙은 [AGENTS.md](AGENTS.md), 설치·확장 방법은 [gstack 안내](../../docs/gstack.md)에 있습니다.

- [Project Spec](docs/specs/00_project_spec.md): 현재 구현, 목표, 공통 제약
- [전월세 추천 RENT-001](docs/specs/10_rental_recommendation_spec.md) / [전환 Plan](docs/plans/rental-recommendation-mvp.md) / [전환 ADR](docs/adr/ADR-003-rental-recommendation-first.md): 승인된 추천 계약·제품 순서·결정 이유
- [대화형 MVP 실행](#대화형-db-전월세-mvp) / [TASK-RENT-MVP-001](docs/tasks/rental-mvp.md) / [실제 DB·성능 검증](docs/rental-mvp-validation-20261013.md): 확정 연결만 추천, 미준비 상태와 지연 계측
- [API 키 보관함 CRED-001](docs/specs/11_api_credential_vault_spec.md) / [ADR-004](docs/adr/ADR-004-local-api-credential-vault.md) / [구현 Task](docs/tasks/api-credential-vault.md): Windows 보호 키·암호화 저장·검증 상태
- [통합 DB 실행·조회·출처 확장](docs/canonical-db.md) / [검증 기록](docs/canonical-validation-20261013.md) / [Task](docs/tasks/canonical-integration.md): 보존 XML과 등록 CSV/JSON/XLSX의 오프라인 적재·재실행·증분 계약
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
- Windows Credential Manager가 보호하는 암호화 키와 별도 사용자 로컬 SQLite를 사용하는 API 키 보관함·loopback 설정 화면

기존 저장소의 [README](https://github.com/keulreobeu/Real_estate_Chatbot_by_gemma4)와 ZIP을 확인했습니다. GitHub 저장소에는 `data/original` 원본 CSV와 실제 평가 CSV가 들어 있지 않습니다. 따라서 여기에는 실거래 기록이나 200건 Golden을 임의로 만들지 않았습니다. 이전 파이프라인의 `공급액(만원)`은 분양/공급액이며 실거래가가 아닙니다.

## 빠른 시작

### 대화형 DB 전월세 MVP

첫 실행이나 canonical DB 갱신 뒤 실제 통합 DB에서 compact serving projection을 재생성하고 loopback 웹 화면을 시작합니다.

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python -X utf8 -m budongi.cli prepare-rentals
python -X utf8 -m budongi.cli rental-readiness
python -X utf8 -m budongi.cli rental-mvp --no-browser
```

브라우저에서 출력된 `http://127.0.0.1:8766/`을 엽니다. 로컬 OpenAI 호환 모델을 연결할 때만 `JIPDAM_RENTAL_MODEL`과 `OLLAMA_ENDPOINT`를 설정합니다. 모델이 없으면 질문 안내와 직접 조건 입력을 사용할 수 있습니다. 대화 draft는 폼에 반영되며, 사용자가 확인·수정한 뒤 검색 버튼을 눌러야 DB를 조회합니다. 현재 실제 단지 연결은 0건이므로 `data_not_ready`가 정상 상태입니다. 확정 연결·검수 좌표·시설 데이터를 자동으로 만들지 않습니다. 실제 사용 범위와 제약은 [검증 기록](docs/rental-mvp-validation-20261013.md)을 따릅니다.

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

이 폴더에서 Python 3.11 이상을 사용합니다. API 키 암호화에는 `cryptography` 패키지가 필요합니다.

```powershell
python -m pip install -e .
$env:PYTHONPATH = (Resolve-Path .\src).Path
python -m budongi.cli --db .\data\historical\serving.sqlite3 init-db
python -m budongi.cli --db .\data\historical\serving.sqlite3 doctor
python -m unittest discover -s tests -v
```

### 합성 전월세 추천 CLI

실제 키 없이 모델과 외부 호출 없이 실행합니다. 이 폴더에서 다음을 실행하세요.

```powershell
python -X utf8 -m budongi.cli rental-demo
python -X utf8 -m budongi.cli recommend --rental-db data/rental/synthetic-demo/serving.sqlite3 --snapshot-id synthetic_rental_demo_v1 --request data/rental/synthetic-demo/request.json --allow-synthetic
```

첫 명령은 허구 단지 3개와 요청 JSON을 만듭니다. 둘째 명령은 예산·직장 직선거리 필수 조건으로 2곳을 반환합니다. 역 선호는 확인되지 않은 조건으로 표시합니다. 데모가 이미 있으면 첫 명령을 다시 실행하지 않고 둘째 명령만 실행하거나 `rental-demo --directory 다른폴더`를 사용하세요.

`request.json`에서 원 정수 예산·면적·자치구·확인한 직장 좌표·필수/선호를 바꿀 수 있습니다. 실제 데이터로 받아들이지 않도록 합성 허용 옵션을 명시해야 합니다. 실데이터 조회 웹은 별도 [대화형 MVP](#대화형-db-전월세-mvp)에 있고, 이 CLI 설명은 합성 snapshot 경로에 한정됩니다. [추천 Task](docs/tasks/rental-recommendation-cli.md#validation)에서 검증과 한계를 확인할 수 있습니다.

### GMS 실잔액·사용 한도·코드 작업

`jipdam credentials`로 [로컬 보관함](http://127.0.0.1:8765/)을 엽니다. 등록한 GMS 키를 직접 선택하고 **잔여 크레딧 조회**를 누르면 공식 key-info의 전체/사용/잔여 크레딧과 KST 만료 시각을 표시합니다. 키 교체는 저장한 키의 **수정 → 새 API 키 → 변경 저장**을 사용합니다.

**실행 예산 기준**은 현재 사용자 지시에 따라 `reserve_only`입니다. 실잔액에서 진행 중 예약과 이번 최대 비용을 제외한 뒤 **5,000크레딧 이상 보존**하는지만 비용 기준으로 관리합니다. 누적/호출 크레딧·누적 토큰 한도는 실행을 차단하지 않고 사용 이력은 기록으로 유지합니다. 500크레딧/10,000토큰은 초기 운영 이력입니다. 입력/출력의 기술적 상한·키 만료·유료 입력 카운트·최대 예약·정산은 유지합니다. 이전 `cumulative` 모드는 호환용입니다.

모든 생성 전에 공식 잔액/만료와 전체 입력 토큰을 확인합니다. GMS의 입력 카운트 프록시에도 실제 관측상 요금이 붙으므로 조회 비용부터 예약합니다. 모델별 견적은 조회 비용 + 입력×입력 요율 + 예상 출력×출력 요율이며 최대 생성 예약은 정수 크레딧까지 올려 계정 반올림을 포함합니다. SOL 요율은 0.02/0.1, LUNA는 0.001/0.005크레딧/토큰입니다. 120초 동안 model/input을 동결하고 카운트를 재사용합니다. 실제 usage와 계정 차감을 대사하며, 팀의 다른 차감이 섞일 때는 보수적으로 계산합니다. 사용량 없는 실패는 최대 비용/토큰을 보류하고 재시도하지 않습니다. 조회 요금의 공식 상한은 제공되지 않았으므로 관측 상한을 넘으면 다음 실행을 중지합니다.

웹의 **명확한 코드 작업 · 사전 견적**에 Task ID, 목표/AC, 필요한 코드 부분을 입력하면 견적을 볼 수 있습니다. 견적 조회에도 크레딧이 사용될 수 있으며 별도 실행 버튼만 모델 생성합니다. 코드 초안은 자동 적용하지 않습니다.

CLI용 `request.json` 예시는 다음과 같습니다. files는 이 제품 폴더 기준 src/tests/docs의 코드·문서만 지정합니다.

```json
{
  "task_id": "TASK-EXAMPLE-001",
  "objective": "금액 검증 함수의 경계값 테스트 초안을 작성한다",
  "acceptance_criteria": ["음수·bool·소수점 초과 입력을 거부한다"],
  "files": ["src/budongi/gms_budget.py"],
  "difficulty": "simple",
  "max_output_tokens": 1000,
  "expected_output_tokens": 700
}
```

```powershell
python -X utf8 -m budongi.cli gms-work --request request.json
python -X utf8 -m budongi.cli gms-work --request request.json --execute
```

`difficulty=simple`은 `gpt-6-luna`, `complex`는 `gpt-6.1-sol`을 사용합니다. 누락은 기존 SOL이며 두 ID만 직접 지정할 수 있습니다. 작업 출력 상한은 저장 정책 이내로만 줄입니다. 현재 검증 서버는 `credentials --no-browser --port 8785`로 실행하며 CLI에도 `--port 8785`를 지정합니다. 기본 포트 8765의 기존 서버는 최신 코드로 재시작한 뒤 사용하세요.

첫 명령은 사전 견적만, 둘째는 저장된 정책 안에서 1회 생성합니다. 가능한 한 둘째 명령 한 번으로 견적/실행을 수행해 불필요한 카운트 조회를 줄이세요. 필요한 코드 부분만 선택하며 큰 문맥은 입력 상한에서 차단합니다. 실제 데이터/DB/raw·키/.env·다른 자격증명·로그/런타임을 보내지 않습니다. 명확한 코드/테스트/기계적 문서 초안은 이 runner를 우선 사용하고 담당자가 검토·적용·테스트합니다. 현재 Codex 채팅 모델 자체를 GMS로 전환한 것은 아닙니다. [계약](docs/specs/18_gms_budget_spec.md)·[Plan](docs/plans/gms-budget-work.md)·[검증 Task](docs/tasks/gms-budget-work.md).

### API 키 보관함 (Windows)

패키지 설치 후 다음 명령으로 로컬 설정 화면을 엽니다. 기본 주소는 `http://127.0.0.1:8765/`이며, 종료할 때는 실행한 터미널에서 `Ctrl+C`를 누릅니다.

```powershell
jipdam credentials
# 또는
python -m budongi.cli credentials
```

화면에서 폴더, 키 별칭과 키 원문을 입력합니다. 별칭은 `공공데이터포털 공통 인증키`처럼 알아볼 수 있는 이름으로 정하고, 수정 창에서 별칭 변경·폴더 이동·키 교체를 할 수 있습니다. 연결 API 선택 목록은 사용하지 않습니다. API 사용 작업에서는 API 종류와 저장된 키 ID를 명시적으로 지정하며 별칭·폴더명으로 API 종류를 추측하지 않습니다. 기존 키도 재등록 없이 그대로 사용할 수 있습니다. 원문은 등록 응답·목록에 다시 나타나지 않으며, `%LOCALAPPDATA%\Jipdam\credentials.sqlite3`에 AES-256-GCM 암호문으로 저장됩니다. 암호화 키는 Windows 자격 증명 관리자에 사용자 계정 범위로 저장합니다. Windows 보안 저장소를 쓸 수 없는 실행 세션에서는 키 등록이 차단됩니다. 설정의 저장·수정·삭제는 외부 API를 호출하지 않습니다.

아래는 보존된 역사 조회 경로의 사용 예시입니다. 새 전월세 추천의 선행 조건이 아니며, 실제 자료 수집·매칭은 보류 중입니다. 검수된 실제 2023 자료를 준비한 뒤 다음을 실행합니다. `snapshot_id`는 같은 파일·정제 규칙에 대해 고정하고, 수정 자료는 새 ID로 가져옵니다.

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

### 기존 매매·청약 API 명령 (현재 수집 보류)

아래 명령은 기존 코드의 참고 사용법이며 지금 실행하라는 안내가 아닙니다. 전월세는 XML 원문 태그 파서와 합성 정규화 입력을 위한 분리 저장 기반만 구현됐습니다. 공식 응답 필드·단위 확인, 원천 필드 매핑·환산, 실제 API 수집은 아직 구현하지 않았습니다. 진행 상태는 [데이터 Task](docs/tasks/rental-data-contract.md)를 따릅니다. [실제 수집 Task](docs/tasks/rental-real-data.md)는 사용자 보류 해제까지 blocked입니다.

`scripts/fetch_public_data.py`는 [국토교통부 아파트 매매 실거래가 상세 자료](https://www.data.go.kr/data/15126468/openapi.do)와
[한국부동산원 청약홈 분양정보 조회 서비스](https://www.data.go.kr/data/15098547/openapi.do)를 조회합니다.
두 서비스 모두 공공데이터포털에서 **각각 활용신청**이 승인되어야 합니다. 이 기존 역사
수집 명령은 `DATA_GO_KR_SERVICE_KEY` 환경변수에서만 키를 읽으며 파일과 출력에 남기지 않습니다.
신규 전월세 연동용 키 보관함은 [CRED-001](docs/specs/11_api_credential_vault_spec.md)에
따르며 위의 Windows 로컬 설정 화면에서 관리합니다. 이 기능은 API 키를 보관하지만 실제 공급자 API 호출은 아직 연결하지 않았습니다.
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

## 보존된 자료와 후속 제품 작업

사용자가 제공한 `apartment_20230905 - apartment_20230905.csv.csv`를 출처·기준일 미확인
**임시 단지 자료**로 `data/provisional/apartment_20230905/`에 복사했습니다. 재생성 명령과
제약은 [임시 자료 안내](data/provisional/README.md)에 있습니다. 이 자료는 단지·주소·좌표·역 거리
매핑 개발에 사용합니다. 현재 카탈로그는 실거래 기반 가격 조회나 실제 평가용 스냅샷이 아닙니다.

### 원시 MOLIT 수집과 오프라인 DB

[MOLIT-001](docs/specs/12_molit_collection_spec.md)·[실행 Task](docs/tasks/molit-collection.md)는 서울 전월세·매매 일반·매매 상세의 최근 12개월 원본 수집을 다룹니다. 단지 매칭·시설·추천 연결의 보류는 유지합니다. API 키는 보관함에서 등록하고 서비스별 자격증명 ID를 명시적으로 선택합니다. 별칭·폴더에서 API 종류를 추측하지 않습니다.

다음 명령은 제품 폴더에서 실행합니다. 배치 시작 시 기준일을 고정하며 새 기준일의 갱신은 새 디렉터리를 사용합니다. 수집 전 GitHub의 완료·닫힌·예약 범위를 검색하고 담당자·범위를 예약해야 합니다.

```powershell
python -m budongi.cli collection plan --directory data/collection/my-batch --batch-id my-batch --snapshot-date 2026-10-12 --services rental trade trade-detail --record-url https://github.com/keulreobeu/jipdam/issues/5
python -m budongi.cli collection fetch --directory data/collection/my-batch --credential rental=<전월세-자격증명-ID> --credential trade=<매매일반-자격증명-ID> --credential trade-detail=<매매상세-자격증명-ID>
python -m budongi.cli collection status --directory data/collection/my-batch
python -m budongi.cli collection build-db --directory data/collection/my-batch --output data/collection/my-batch/db
python -m budongi.cli collection pack --directory data/collection/my-batch --db-directory data/collection/my-batch/db --output data/collection/my-batch/my-batch.zip
```

`plan/status/build-db/pack`은 키·네트워크를 사용하지 않습니다. `fetch`도 검증된 완료 범위는 키 접근·추가 호출 없이 재사용합니다. 다른 배치의 완료 원본은 `--cache-dir <배치폴더>`로 검증해 재사용합니다. 월별 조회는 관측 기간의 경계 월을 포함하며 기간 밖 행도 원본/staging에 남깁니다.

출력은 `rental.sqlite3`, `sales.sqlite3`, `staging.sqlite3`, `normalized-manifest.json`입니다. `staging_items`와 `raw_files`로 원본 파일·해시·행 위치·기간 제외 사유를 조회합니다. 매니페스트는 원본/유효/기간 제외/거부 건수와 실제 원본 조인·무결성 검사 결과를 기록합니다. 잘못된 필수 값이 있으면 DB를 게시하지 않고 `normalization-errors.json`에 모든 발견 오류를 남깁니다. 완료된 DB와 staging은 불변이며 기존 출력은 덮어쓰지 않습니다.

기본 DB 생성·pack은 전체 완료를 요구합니다. `--allow-partial`은 검증된 완료 query만 대상으로 하며 미조회·실패 범위를 명시합니다. 부분 성공을 전체 수집/Goal 완료로 표시하지 않습니다. 부분 DB 생성 뒤 수집이 추가되면 새 출력으로 DB를 재생성해야 pack이 허용됩니다. ZIP에는 XML까지 포함하며 최종 해시와 결과를 같은 수집 Issue에 기록합니다. Drive 자동 업로드는 없습니다.

실제 실행 결과와 미완료 조건은 [2026-10-12 검증 기록](docs/molit-validation-20261012.md)을 참조합니다. 금액은 원 정수, 면적은 ㎡이며 일반·상세 매매 건수는 출처별 관측입니다. 같은 실제 계약이라고 자동 연결하거나 합산하지 않습니다. 최신 DB는 `source_unverified`이고 기존 역사 DB의 2023 cutoff·추천 검수 경계를 유지합니다.

### 제품 실행 순서

[현재 Task](docs/tasks/current.md)와 [Plan](docs/plans/rental-recommendation-mvp.md)을 따른다. 문서 전환·합성 추천 CLI·[암호화 API 키 보관함](docs/tasks/api-credential-vault.md)에 더해, [대화형 DB 전월세 MVP](#대화형-db-전월세-mvp)의 loopback 웹/API, 실제 serving projection 및 니즈/상세 화면 첫 구현을 진행 중이다. 실제 확정 매칭, 좌표·시설은 별도 승인·검수 게이트이며 현재 추천 상태는 `data_not_ready`다. 성공 경로와 실제 모델/browser QA는 추가 검증이 필요하다. 추천은 현재 매물이 아닌 단지 후보이며, 직선거리와 보증금/월세 각각의 상한을 사용하고 관리비·대출비용은 포함하지 않는다.

### 선택형 역사 평가 연구 (제품 선행 조건 아님)

1. 검수 Golden의 `required_facts.entity_aliases`를 채우고 단지명·ID 별칭의 사람 검수 기준을 확정합니다.
2. 실제 자료 작업을 다시 시작할 때 임시 단지 자료의 원천·기준일과 거래 식별자·정정 이력을 검수합니다.
3. 검수된 실제 스냅샷을 만든 뒤 FACT/FILTER/COMPARE/NO_MATCH 약 200건을 사람 검수해 분할합니다.
4. 답변 전체의 근거 없는 추가 주장까지 재는 평가기를 확장해 실제 Tool 결과와 답변 사실을 단계별로 평가합니다.

최신 임대차 데이터 계약은 제품 첫 단계로 앞당깁니다. 의미 검색·Judge·LoRA·Adapter/Model Routing은 제품 평가에서 필요성이 확인된 경우 별도 계약으로 검토할 후속 연구입니다. 기존 2023 역사 자료·평가 미완료 기록은 보존합니다.

### 대화형 전월세 MVP — 2026-10-14

채팅 초안 확인·수정, 실제 DB 추천, 후보별 니즈, 100행 거래 상세와 Leaflet+OSM 내장 지도를 구현했다. 현재 실제 확정 연결은 0건이므로 data_not_ready로 표시한다. 검수 자료·실모델은 준비 조건이다. [실행·검수 패키지·성능 재현 안내](docs/rental-review-package.md)를 따른다.


## 개발 에이전트 하네스

선택적 역할 배정·공통 SQLite 상태·체크포인트·Mock GMS 예산은 [하네스 운영](docs/harness/README.md)을 따릅니다. 루트에서 `python -X utf8 scripts/agent_harness.py doctor`로 확인합니다. 실제 GMS 호출은 새 하네스에서 차단되며 기존 GMS·제품 경로를 보존합니다.
