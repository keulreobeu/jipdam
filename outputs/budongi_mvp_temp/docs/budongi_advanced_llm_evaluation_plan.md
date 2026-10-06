# 집담 고도화 및 LLM 평가 실행 계획

## 문서 상태 — 선택형 연구 계획

2026-10-06 사용자가 서울 아파트 전월세 추천 전환을 승인했다. 현재 제품 계약·실행 순서는 [RENT-001](specs/10_rental_recommendation_spec.md)·[PLAN-RENT-001](plans/rental-recommendation-mvp.md)·[현재 Task](tasks/current.md)를 따른다. 아래 Phase 0~17·2023 cutoff·학습/평가 프롬프트는 기존 연구 계획과 이력으로 보존한다. 2023 스냅샷·약 200건 역사 Golden 완료를 새 추천의 선행 조건으로 요구하지 않으며 최신 임대차 데이터 계약은 제품 첫 단계로 앞당긴다. 실제 수집·단지 매칭은 계속 보류다. 아래 연구 목표를 CURRENT 구현 또는 이번에 승인/완료된 제품 기능으로 취급하지 않는다.

> 이 문서는 「프로젝트 진행 정리」 대화의 계획과 후속 데이터 엔지니어 관점 피드백을 합친 실행 기준이다. 수치 예시는 목표 성능이나 실측 결과가 아니다. 모델명·메모리 사용량·Colab 가용성은 실제 실행 전에 확인하고 기록한다.

## 1. 핵심 가설과 성공 기준

**연구 질문:** Ryzen 5 5600, RAM 16GB, RTX 3060 Ti 8GB 환경에서 **검증된 Data Tool을 사용하는 로컬 4B LLM**을 기준으로 Hybrid RAG, LoRA Adapter Routing, Model Routing을 순차 결합하면 단일 4B 모델보다 얼마나 좋아지고, Colab의 20~30B급 대형 오픈 모델 및 GPT 참조 모델과의 품질 격차를 얼마나 줄일 수 있는가?

실험의 결론은 단일 정확도 대신 **사실성·근거 충실도·최신 정보 활용·지연·메모리·비용의 동시 비교**로 내린다. 특히 완성 시스템과 Colab 대형 오픈 모델의 비교가 주 비교이고, GPT는 외부 참조점이다. 실측 전에는 어느 쪽이 우세하다고 가정하지 않는다. 개발은 작은 기준 시스템을 먼저 완성하고, 평가에서 가장 큰 실패 원인을 하나씩 해결하는 순서로 진행한다.

**보존된 연구의 시작 범위(제품 선행 조건 아님):** 2023 데이터 스냅샷과 기본 조회를 재현하고, 검증된 `search_apartments`/`search_transactions`/`get_apartment_detail` Tool을 만든다. 4B 한 모델이 FACT/FILTER/COMPARE에서 Tool을 선택해 끝까지 답하게 한다. 약 200건의 Golden으로 **Tool 선택·인자·조회 결과·답변**을 기계 평가한 뒤에만 검색 확장·최신화·Judge·LoRA·라우팅을 검토한다. 단계별 상세 완료 조건은 [10절](#10-단계별-실행-순서와-완료-조건)에 있다.

```
2023 데이터 스냅샷 → Data Serving/Tool Layer → 4B Tool Calling MVP
→ 소형 Golden/단계별 자동 평가 → 검색 개선 → 최신화/Temporal Eval → AI Judge/사람 보정
→ Prompt/LoRA → Adapter Routing → Model Routing/Persona
→ Colab 대형 모델/GPT 비교 → 운영 지표/대시보드
```

## 2. 환경 제약과 역할 분리

| 자원 | 제약과 설계 원칙 |
|---|---|
| CPU | Ryzen 5 5600. 구조화 검색·라우팅·전처리·일부 후처리를 맡긴다. 동시 실행 시 지연을 측정한다. |
| 시스템 RAM | 16GB. 모델, 벡터 인덱스, 검색기, OS가 함께 사용하므로 피크 RSS와 스왑 여부를 기록한다. |
| GPU | RTX 3060 Ti 8GB. 양자화 및 순차 로딩을 기본 가설로 두고 실제 VRAM과 지연을 측정한다. 8B 상시 GPU 적재는 전제하지 않는다. |
| 외부 실행 | Colab은 대형 오픈 모델 비교용, GPT는 API 참조 비교용. 로컬 배포 가능성 평가는 별도 축이다. |

**로컬 후보와 역할(확정 모델이 아니라 측정할 후보군):**

| 역할 | 후보 | 선택 기준 |
|---|---|---|
| 후속 분류/라우팅 | 처음에는 4B의 Tool 선택, 이후 필요할 때 규칙·경량 분류기 또는 2B급 모델 | task/난도/어댑터 분류 정확도 대비 지연·메모리. 별도 Router는 Tool 선택 오류가 지속될 때만 실험한다. |
| 기본 생성 | Qwen 계열 4B 중심, Gemma 계열의 비교 가능한 소형 모델도 후보 | 한국어 응답 품질, 구조화 출력, 8GB 내 추론 가능성, 라이선스와 실행 환경. 한 베이스를 고른 뒤 LoRA 비교에서는 고정한다. |
| 선택적 Expert | 8B급 양자화 모델 후보 | 어려운 비교·설명에서 얻는 품질 이득이 로딩 시간과 메모리 비용을 정당화하는지. 필요 시 CPU 오프로딩/순차 로딩을 측정한다. |
| 검색/재정렬 | 구조화 DB + 벡터 검색, 필요하면 다국어 reranker(예: bge-reranker-v2-m3 후보) | Recall@K/MRR, 지연, 메모리. |

모델 크기 표기는 역할을 뜻하며 특정 버전의 성능·VRAM 사용량을 보증하지 않는다. 모델 ID, 버전, 양자화, 컨텍스트 길이, 프롬프트, 생성 설정, 드라이버와 실행 라이브러리 버전을 실험 로그에 고정한다.

### Model Routing

**첫 MVP에는 별도 Router 모델을 두지 않는다.** 4B가 허용된 Tool 중 하나를 고르고 인자를 제안하며, 백엔드가 인자를 검증하고 실제 조회를 수행한다. FACT/FILTER의 결과는 Tool에서 확정하고 4B는 설명을 만든다. 후속 단계에서 단순 Tool 파싱은 2B, 일반 설명은 4B, 복잡한 비교·낮은 신뢰도는 8B Expert를 후보로 시험한다. 4B의 Tool Selection Accuracy와 오류 분포가 충분하면 별도 Router를 추가하지 않는다. 추가한다면 사전에 고정한 조건으로 호출하며 오라우팅 손실, Expert 호출률, p95 지연과 피크 메모리를 측정한다.

### LoRA Adapter Routing

같은 4B 베이스에 업무별 행동 양식을 학습한다. **첫 실험은 `response_lora_v1` 하나**로 COMPARE/RECOMMEND/SUMMARY의 답변 구조·정보 부족 표현을 익히게 하고 `Base ↔ Base+Prompt ↔ Base+Response LoRA`를 비교한다. 의미 있는 이득이 확인될 때만 `structured_adapter`(Tool 인자용 JSON/조건 추출)와 `response_adapter`(응답)의 2개 어댑터로 라우팅을 실험한다. Compare/Recommend 개별 어댑터나 상담형·분석형·JSON형 세분화는 분리 이득이 검증된 뒤의 확장안이다. 어댑터의 대상은 **행동 방식**이며, 바뀌는 가격 등 최신 사실은 Data Tool 결과에서 제공한다. 라우팅 오류, 버전·데이터셋·호환성·서빙 비용, 전환 지연과 품질 이득을 함께 비교한다. Persona는 먼저 Prompt로 평가하고 별도 LoRA는 추가 이득이 입증될 때만 검토한다.

### 제한된 Orchestrator 아키텍처

```text
사용자 → 4B LLM Orchestrator → 허용된 Tool 선택·인자 제안
                              ↓
               Tool Layer: schema 검증·쿼리 실행·계산·결과 제한
                              ↓
           Data Serving Layer → PostgreSQL/Vector Index
                              ↓
                      Curated → Raw/API
                              ↓
                Tool 결과 → 4B의 근거 기반 답변
```

LLM은 **의도를 해석하고 허용된 Tool을 호출하는 클라이언트**다. 실제 SQL 작성·실행과 숫자 계산은 백엔드가 한다. LLM에 DB 접근 권한이나 자유 SQL 실행 기능을 주지 않는다. Tool 호출 횟수, 허용 목록, JSON 인자 스키마, 타임아웃, 결과 행 수를 제한한다(초기 상한 예: `max_tool_calls = 5`). 중복 호출·타임아웃·빈 결과도 응답 및 평가 로그로 남긴다. 처음에는 Python 함수로 시작하고 별도 서비스가 필요해질 때 API로 분리한다.

| Tool | 입력과 책임 | 도입 |
|---|---|---|
| `search_apartments` | 지역·가격·면적·입주년도 등 검증된 조건으로 단지 후보 검색 | MVP |
| `search_transactions` | 단지·기간·가격·면적과 유효 거래 상태로 실거래 조회 | MVP |
| `get_apartment_detail` | 특정 단지의 기본정보·위치·제공 가능한 주변 정보 | MVP |
| `calculate_metrics` | 가격 변화율·예산 비율·거리 등 결정적 계산; 필요하면 목적별 함수로 분리 | Tool 평가 뒤 |
| `semantic_search` | 청약 제도·용어·공공 문서 등 비정형 자료 검색 | Structured 안정화 뒤 |

초기 호출 예: `search_apartments({"district":"강서구","max_price":1000000000,"area":84})`. 백엔드는 타입/범위/허용 필드를 검증한 뒤 파라미터화된 SQL을 실행해 ID·수치·기준일·출처가 담긴 구조화 결과를 반환한다. COMPARE는 두 단지의 상세 Tool 결과를 같은 기준으로 읽고 설명한다. 여러 Tool을 조합하는 제한된 Agent는 Hybrid 단계에서만 도입한다.

## 3. 사실 데이터 수집과 Hybrid RAG

| 원천 | 용도 | 관리할 원본 키/시점 |
|---|---|---|
| 국토교통부 아파트 실거래 자료 | 거래가격·거래일·면적 | 원천 거래 식별자, 계약일, 수집 시점 |
| 청약홈 분양 정보 | 공고·분양·청약 | 공고 식별자, 공고/접수 기간 |
| 공동주택 기본정보 | 세대수·난방·관리 및 제공되는 주변 정보 | 단지 식별자, 정보 기준일 |
| 서울 열린데이터 등 지역·교통 정보 | 역·교통·지역 정보 | 시설 식별자, 좌표, 갱신일 |
| 파생 계산값 | 역거리·생활시설 거리 등 | 계산식, 좌표계, 입력 데이터 버전 |

최소 데이터 실체는 `apartment`, `transaction`, `location`, `facility`다. 예를 들어 단지에는 `apartment_id/name/address/district/lat/lon/built_year`, 거래에는 `transaction_id/apartment_id/contract_date/price/area/floor/status/source`를 둔다. 원본 수집, 정제, 파생 특성, 모델 출력을 구별한다.

| 계층 | 예 | 필요한 추적 정보 |
|---|---|---|
| `raw_fact` | 원천 거래 가격·계약일 | `source`, `source_id`, 원본 payload, `ingested_at` |
| `clean_fact` | 정정·취소 상태를 반영한 거래 | 원본 ID, 정제 규칙/버전, 상태 |
| `derived_feature` | 역거리, 교통 점수 | 입력 데이터 ID, 계산식/좌표계, 변환 버전 |
| `model_output` | 추천 설명, 요약 | 사용한 context ID, 모델·Prompt·run ID |

사실 레코드에는 최소 `source`, `source_id`, `retrieved_at` 또는 `ingested_at`, `valid_date`, `snapshot_id`를 둔다. 거래는 **계약일(`event_time`), 신고일, 수정/취소일, 수집일(`ingestion_time`)을 분리**하고 `status = valid/canceled/corrected`를 관리한다. ‘최신 거래’는 단순 `max(date)`가 아니라 질문의 기준 시점에 유효한 거래 중 계약일과 정정 상태로 선택한다. 가격 단위는 원화 정수, 거리 단위는 m 등으로 정규화하고 원본값도 추적한다. 단지명 유사성, 거래 취소/정정, 중복, 면적 차이, 기준일 누락을 정제 단계에서 검사한다.

`원천 API → raw → clean → serving/derived feature/index → Tool result → answer`의 **data lineage**를 각 단계의 입력 ID와 `pipeline_version`/`transformation_version`으로 연결한다. 최종 답변의 가격 한 건을 원천 거래 레코드까지 거슬러 올라갈 수 있어야 한다. Tool 호출·검색 산출물과 답변 산출물도 따로 저장해 오류의 책임 단계를 구분한다. 최신화 때는 `API → incremental ingestion → raw → validation → clean → upsert → serving → index update`로 진행하며 재수집/정정의 멱등성을 확인한다.

**검색 선택 원칙:** `10억 이하`, `84㎡`, `강서구`, 특정 거래 시점 같은 명시 조건은 구조화 Tool로 처리한다. 설명·의미 검색은 `semantic_search`가 키워드/BM25·벡터 자료를 사용하고, 둘 다 필요하면 구조화 Tool로 후보를 좁힌 뒤 의미 검색·reranker를 결합한다. 예를 들어 “강서구 10억 이하 역세권”은 지역/가격으로 후보를 좁힌 다음 역 접근성 파생값을 조회·정렬한다. “예산 10억, 여의도 출퇴근”은 후보 검색 → 통근/거리 계산 → 상세 조회 → 필요시 의미 검색의 순서로 처리한다. 최소 MVP는 구조화 검색만으로 시작한다. 확장 실험은 `R0 Structured only → R1 Vector only → R2 Structured + Vector → R3 Structured + Vector + reranker`로 한다. 검색 결과에는 단지/거래 ID, 문서 점수·순위, 날짜, 출처를 유지한다.

평가는 세 층으로 나눈다. **조건 해석**은 `district/price_max/area/date` 필드 정확도, **후보 집합**은 Entity Precision/Recall/F1, **문서 검색**은 Recall@1/3/5·MRR·nDCG로 본다. FILTER의 정답이 여러 단지의 집합인 경우 문서 Recall만으로 평가하지 않는다. 생성기 비교에서는 저장된 동일 Top-5 컨텍스트를 사용한다.

## 4. 2023 cutoff와 최신화의 동시 활용

기존 데이터는 **2023년까지의 불변 스냅샷**으로 고정한다. 예: `snapshot_id = budongi_2023_v1`, `snapshot_date = 2023-12-31`. 이후 수집분도 연도/월별 스냅샷 ID와 생성 시각, 원천 파일 목록·해시를 남긴다. `knowledge_cutoff = 2023-12-31`을 선언하고 2024년 이후 사실이 SFT/LoRA 학습 데이터, 예시 답변, Prompt 선택용 메모에 섞이지 않도록 provenance를 검사한다. 최신화 수집은 2024~2026년 자료에 대해 별도 수행한다. 최종적으로 서비스 검색 DB에는 최신 자료를 제공하되, 평가 정답 파일과 접근 권한은 별도로 관리한다. Eval-C에서 필요한 최신 사실은 **추론 시 검색 컨텍스트로만** 제공한다.

| 기간 | 사용 |
|---|---|
| ≤2023 | 기존 DB 스냅샷, 학습용 사실, LoRA 학습 |
| 2024 | Temporal 개발/오류 분석 |
| 2025 | Temporal 검증 및 Prompt/설정 선택 |
| 2026 | 최종 Temporal Test. 확정 후에는 재튜닝에 사용하지 않음 |

이는 권장 분할이며 실제 자료의 밀도에 따라 조정할 수 있다. 최종 분할 전에 단지 ID·거래 ID·동일 질문의 재표현·같은 사건의 파생 문제를 묶어 누출을 막는다. **질문 생성 과정의 누출**도 관리한다: Train은 synthetic generator A를 사용하더라도 Validation에는 사람 변형을 섞고, Test는 다른 생성 지시문·사람 작성·대조적 질문을 사용한다. 최종 Temporal Test는 가능한 만큼 사람 검수한다. 같은 생성기·같은 프롬프트 패턴으로 Train/Test를 만들면 사실이 달라도 표현 분포가 비슷해져 성능이 부풀 수 있다. 2026 자료를 한 번 확인하고 모델을 고친다면 그 세트는 더 이상 최종 Test가 아니므로 별도 잠금 세트를 마련한다.

```
data/historical/  ≤2023 동결 스냅샷
data/current/     2024~2026 수집·정제 자료
data/eval/        Golden 및 temporal holdout (서비스 DB와 별도 관리)
```

## 5. Task taxonomy, 답변 템플릿, Golden Dataset

| Task | 예시 | 핵심 판정 |
|---|---|---|
| FACT | “A단지 최근 실거래가는?” | 대상·거래일·금액·출처 |
| FILTER | “강서구 10억 이하 전용 84㎡” | 조건 추출과 결과 집합 |
| COMPARE | “A와 B를 가격·교통으로 비교” | 동일 기준, 두 대상, 우선순위 |
| RECOMMEND | “여의도 직장, 예산 8억” | 조건 충족, 근거, 유보 사항 |
| EXPLAIN | “청약 경쟁률 10대 1의 의미” | 정확하고 이해하기 쉬운 설명 |
| SUMMARY | “단지 장단점 요약” | 정보 누락/과장 없는 압축 |
| NO_MATCH | 존재하지 않는 정보나 검색 결과 0건 | 지어내지 않고 결과 없음 표기 |
| AMBIGUOUS | “마곡에서 좋은 집” | 필요한 조건 확인 또는 제한된 범위만 답변 |

답변 템플릿은 내용 평가 전에 버전을 고정한다.

```text
FACT_V1
[답변] {핵심 사실}
기준일: {date}
출처: {source}

FILTER_V1
조건에 맞는 단지는 {N}곳입니다.
1. {단지}: 가격 {price}, 면적 {area}, 위치 {location}, 교통 {transport}
...
기준일: {date}

COMPARE_V1
두 단지를 동일 기준으로 비교합니다.
| 항목 | A | B |
| 가격 | ... | ... |
| 교통 | ... | ... |
| 입주년도 | ... | ... |
| 생활환경 | ... | ... |
사용자의 {priority}를 기준으로 본 A/B의 강점: ...
제공된 데이터로 확인할 수 없는 점: ...

RECOMMEND_V1
사용자 조건: 예산 / 지역 / 우선순위
조건을 충족하는 후보: ...
추천 근거: ...
추가로 확인할 점: ...

UNKNOWN_V1
현재 제공된 데이터만으로는 해당 내용을 확인할 수 없습니다.
확인 가능한 정보: ...
필요한 추가 조건 또는 자료: ...
```

**Golden Dataset 공통 레코드(예시):** 필수 항목과 task별 선택 항목을 함께 표현한다. `reference_answer`는 유일한 정답 문장으로 채점하지 않고 답변 요건과 근거를 읽는 참고 자료로 사용한다.

```json
{
  "id": "compare_0001",
  "split": "train",
  "eval_group": null,
  "task_type": "COMPARE",
  "difficulty": "MEDIUM",
  "persona": {"type": "직장인", "budget": 1000000000, "priority": ["교통", "가격"]},
  "question": "A단지랑 B단지 중 출퇴근하기에는 어디가 나아?",
  "context_ids": ["APT_A", "APT_B"],
  "context_version": "historical_2023_v1",
  "expected_tool_calls": [
    {"tool": "get_apartment_detail", "arguments": {"apartment_id": "APT_A"}},
    {"tool": "get_apartment_detail", "arguments": {"apartment_id": "APT_B"}}
  ],
  "expected_filters": {},
  "expected_entities": ["APT_A", "APT_B"],
  "required_facts": [
    {"entity": "APT_A", "field": "station_distance", "value": 350, "unit": "m", "tolerance": 0},
    {"entity": "APT_B", "field": "station_distance", "value": 820, "unit": "m", "tolerance": 0}
  ],
  "forbidden_claims": ["근거 없는 학군 평가", "미래 가격 상승 보장"],
  "answer_requirements": ["두 단지를 모두 언급", "교통 차이를 수치로 설명", "가격 조건 확인"],
  "answer_template": "COMPARE_V1",
  "reference_answer": "...",
  "answerable": true,
  "expected_behavior": "ANSWER",
  "deterministic_checks": ["required_fact_match", "entity_coverage"],
  "judge_checks": ["persona_alignment", "faithfulness"],
  "source_ids": ["..."],
  "valid_date": "2023-12-31"
}
```

`split`은 train/validation/test/persona/human_calibration 중 하나로 관리하고, `eval_group`은 Eval-A/B/C 및 C1~C4를 가리킨다. 복수 평가군에 쓰더라도 ID와 버전은 고정한다. 숫자 tolerance와 날짜 비교 규칙은 데이터 생성 후 평가 전에 확정한다.

Tool Calling Golden에는 단일 호출이면 `expected_tool`/`expected_arguments`, 여러 호출이면 위처럼 순서를 가진 `expected_tool_calls`를 둔다. 일부 task는 여러 호출 순서가 동등할 수 있으므로 순서 필수 여부와 허용 호출 집합을 명시한다. `expected_entities`는 실제 Tool 반환 집합을 검증하고, `required_facts`는 최종 답변을 검증한다. Golden에 적힌 Tool 호출은 생성 모델의 제안일 뿐, 백엔드 계약과 사람 검수로 확정한다.

## 6. 데이터 구성과 평가군

**최소 MVP 평가셋은 약 200건**부터 시작한다. 예시 구성은 FACT 50, FILTER 60, COMPARE 60, NO_MATCH 30이며 개발용 100, Validation 50, 봉인 Test 50으로 배분할 수 있다. 이는 Tool 호출과 평가기를 검증하는 소형 세트다. 확장 목표인 **Train 2,000 / Validation 300 / Test 300 / Persona Eval 200 / Human calibration 50**은 최소 시스템과 채점기가 안정된 뒤 단계적으로 만든다. 숫자는 고정 할당량이 아니며 task별 결함을 보고 추가한다(예: COMPARE 실패가 크면 COMPARE 증강). Train과 평가 데이터를 랜덤 문장 단위로 섞지 않는다. 단지, 거래, 사건, 유사 질문 묶음 단위로 분리한다. Persona Eval은 핵심 Test와 겹치는 경우 동일 사실의 Persona별 일관성 검사로 표시하고, 독립 일반화 수치를 낼 때는 별도 entity 묶음을 사용한다.

| 평가군 | 대상 | 검증하려는 능력 |
|---|---|---|
| Eval-A | 학습에서 본 단지, 보지 못한 질문 표현 | 지시와 표현의 일반화 |
| Eval-B | 학습에서 보지 못한 단지 | 검색된 새 대상에 대한 일반화 |
| Eval-C | 2023 cutoff 이후 자료 | 암기한 과거 사실보다 제공된 최신 컨텍스트를 활용하는지 |

보고서에는 전체 평균과 별도로 **Seen Entity / Unseen Entity / Temporal** 성능을 제시한다. 최소 MVP는 Eval-A와 간단한 미등장 단지 사례만 포함해도 되지만, 본 실험에서는 세 split을 독립적으로 고정한다.

### Eval-C 세부 항목

| 구분 | 문제 구성 | 기계 판정과 주요 지표 |
|---|---|---|
| C1 Unseen Fresh Fact | 학습 이후 처음 등장한 거래·가격·분양 사실 | 최신 사실 값과 날짜의 일치, **Fresh Fact Accuracy** |
| C2 Old vs New Conflict | 과거 값과 최신 값이 함께 있는 컨텍스트 | 최신값 선택, 옛 값을 현재값으로 말했는지, **Freshness Preference Accuracy / Stale Fact Error Rate** |
| C3 Latest Selection | 여러 날짜의 거래 레코드 | 질문에 맞는 최신 `contract_date` 및 레코드 선택, **Latest Record Accuracy / Date Citation Accuracy** |
| C4 Temporal Comparison | 2023 기준과 이후 동일 기준의 값 | `absolute_change = new - old`, `rate = (new-old)/old × 100`(old≠0), **변화량·변화율 정확도** |

Temporal Eval 첫 구현은 **C1/C2**로 제한하고, 최신 레코드 선택과 변화 계산이 필요해질 때 **C3/C4**를 확장한다. 예를 들어 2023년 8.0억과 2026년 10.0억이면 2.0억 및 25% 상승이다. 서로 다른 전용면적·거래유형·기간을 무심코 비교하지 않도록 비교 가능성 규칙을 먼저 정한다. 최신 데이터가 없으면 값을 만들어내지 않고 확인 불가로 답해야 한다. 계약일과 신고일이 엇갈리거나 거래가 정정·취소된 edge case도 포함한다. 시간 평가에는 날짜 명시 여부도 포함한다.

## 7. 평가 체계

### 7.1 결정적 평가를 우선한다

**질문 → Tool Selection → Argument Extraction → Tool 실행/조회 → Generation**을 각각 채점한다. MVP의 핵심 지표는 Tool Selection Accuracy, 인자 Exact Match/필드별 F1(`district/max_price/area/date`), Tool 반환 Entity Precision/Recall/F1, 최종 Fact Accuracy/Required Fact Coverage, NO_MATCH Accuracy다. 숫자 계산 Tool은 입력 인자와 백엔드 결과를 별도로 검증한다. 후속 Model/Adapter Router를 도입했을 때만 별도 Router Accuracy/Macro F1을 추가한다. 문서 검색 단계에서는 Retrieval Recall@K/MRR/nDCG를 기록한다. 금액의 ‘9.8억’과 `980000000`처럼 표현이 달라도 정규화한 원화 값으로 비교한다. 허용 오차는 측정 단위와 반올림 정책에 맞춰 사전 등록한다. 단순 문자열 포함 여부만으로 사실성을 단정하지 않는다.

자유 형식 답변의 사실도 `답변 → 사실 추출(대상·필드·값·날짜·출처) → 정규화 → Golden 비교`로 평가한다. 추출 실패율을 별도로 기록하고, 추출기의 오류가 모델 오류로 오인되는 샘플은 사람 검수에 보낸다. 평가 레코드별 pass/fail뿐 아니라 실패 이유를 저장한다.

### 7.2 AI Judge는 의미 판단에 한정한다

Judge는 근거 충실도, 완전성, 관련성, Persona 적합성, 설명 품질, 근거 없는 주장, 불확실성 처리만 평가한다. 도입 첫 단계는 **Faithfulness, Completeness, Unsupported Claim** 세 항목으로 시작한다. 질문·고정 컨텍스트·답변·rubric을 제공하고 모델 이름은 가린다. 항목별 0~4점(4 우수, 3 경미한 문제, 2 명확한 문제, 1 심각한 문제, 0 실패)과 근거/누락/문제 문장을 구조화 JSON으로 남긴다. 가격·필터·정답 ID처럼 규칙으로 판정 가능한 항목은 Judge에 위임하지 않는다. Judge 버전과 Prompt도 고정한다.

```json
{
  "faithfulness": {"score": 4, "issues": []},
  "completeness": {"score": 3, "missing": ["예산 조건 설명"]},
  "persona_alignment": {"score": 4, "issues": []},
  "unsupported_claims": ["향후 가격 상승 가능성이 높다"]
}
```

모델 간 생성 답변은 별도 **pairwise Judge**로 A/B/동률을 블라인드 판정하고 Win/Tie/Loss 비율을 보고한다. 답변 위치를 뒤집은 재평가로 순서 편향을 확인한다. 점수형 Judge와 pairwise 결과가 충돌하면 사람 검수 대상에 넣는다.

### 7.3 Human calibration

Judge가 채점한 300개 중 대표성과 실패 유형을 고려해 50개를 사람에게 블라인드 평가받는다. 사람 평가자는 같은 0~4 rubric과 근거 자료를 사용한다. **Exact score agreement, ±1 agreement, Spearman correlation, Cohen's kappa**를 보고, 불일치 사례를 읽어 Judge rubric을 수정한다. rubric을 바꾼 뒤에는 변경 이력과 이전 결과를 보존한다. 가능하면 경계 사례 일부를 둘 이상의 사람에게 맡겨 사람 간 일치도도 확인한다.

## 8. 동일 컨텍스트 비교와 ablation

비교는 두 트랙으로 분리한다. **온라인 종단 평가**에서는 로컬 시스템이 실제 Tool을 선택·호출하므로 Tool Selection/인자/조회/생성의 전체 성능과 비용을 잰다. **고정 결과 생성기 평가**에서는 같은 질문, System Instruction/답변 형식, 동일한 Tool 결과와 필요시 동일한 검색 Top-5 문서·순서, 같은 컨텍스트 길이·생성 조건을 4B·대형 오픈 모델·GPT에 제공한다. 이를 `eval_context_v1.jsonl`로 저장한다. 이 트랙은 Tool 선택 능력이 아니라 **제공된 사실을 읽고 답하는 능력**을 비교한다. 대형 모델의 Tool 사용 능력을 평가하려면 동일한 Tool 명세와 백엔드를 제공하는 별도 실험으로 표시한다. Zero-shot은 추가 예시 없이 답하게 한다는 뜻이다. 플랫폼별 샘플러 구현 차이는 설정값과 함께 기록한다.

| ID | 구성 | 확인할 효과 |
|---|---|---|
| B0 | 로컬 4B Base zero-shot | 기본 기준선 |
| B1 | 4B + 고정 Prompt | 지시문 효과 |
| B2 | 4B + 구조화 Data Tool 3개 | Tool Calling 기준 시스템 |
| B3 | B2 + semantic_search/Hybrid Retrieval | 검색·Tool 조합 효과 |
| B4 | B3 + 단일 Response LoRA | 학습 효과 |
| B5 | B3 + Adapter Routing | 업무별 어댑터 선택 효과 |
| B6 | 2B/4B/8B Model Routing + Adapter Routing + Data Tools/Hybrid RAG | 완성 시스템의 추가 이득과 자원 비용 |
| L1 | Colab 20~30B급 대형 오픈 모델 zero-shot + 동일 Tool 결과/컨텍스트 | 주 대형 모델 생성기 비교군 |
| L2 | GPT 계열 zero-shot + 동일 Tool 결과/컨텍스트 | 외부 생성기 참조점 |

B0/B1/L1/L2의 **생성기 비교 점수**는 고정 Tool 결과가 제공된 조건으로 표시한다. B2~B6의 **종단 점수**는 실제 Tool 선택·조회 오류까지 포함하므로 같은 열에 섞지 않고 별도 표로 표시한다. 필요하면 모든 모델에 동일 Tool 스키마를 제공한 종단 비교를 추가한다.

B2→B3에서 `Structured Tool only / semantic_search / 조합 / 조합+reranker`를 동일 Golden에서 평가한다. LoRA는 먼저 COMPARE/RECOMMEND/SUMMARY에 대해 `4B Base ↔ 4B+Prompt ↔ 4B+response_lora_v1`을 **같은 Tool 결과**로 비교한다. 그 후 어댑터 라우팅, 마지막으로 Expert 선택 호출을 붙인다. **Tool 계약과 평가 → Retrieval → 베이스 모델/Prompt → LoRA → Routing** 순서로 후보를 좁혀 조합 폭발을 피한다. 각 단계의 품질 차이뿐 아니라 신뢰구간 또는 문제별 승패, Tool/Expert 호출률, 지연·VRAM·RAM 증가량을 함께 보여준다.

대형 모델 예시 점수(예: 4B 89%, 27B 96%, GPT 97%)는 앞선 대화의 **설명용 가상 수치**이므로 보고서의 실측 표에 넣지 않는다. Colab GPU 종류·가용 메모리·할당 시간과 대형 모델 버전/양자화도 기록한다. 대형 모델을 로컬 8GB 시스템의 배포 대안인 것처럼 제시하지 않는다.

### 실험 재현성: Experiment Registry

각 결과는 `run_id`로 묶고 최소 `model_version`, `adapter_version`, `tool_schema_version`, `retriever_version`, `dataset_snapshot`, `eval_version`, `prompt_version`을 저장한다. 함께 실행 환경, 양자화, seed, 생성 설정, Tool 호출 한도·검색 Top-K, 데이터/코드 해시, 실행 시간과 지연·메모리 측정 방법을 남긴다. 같은 `run_id`에서 **질문 → Tool 선택 → 인자 검증 → Tool 반환 ID/값 → 고정 context → 답변 → 채점**을 재현할 수 있어야 한다.

```json
{
  "run_id": "run_20260928_001",
  "model_version": "local_4b_quant_v1",
  "adapter_version": "response_lora_v1",
  "tool_schema_version": "tools_v1",
  "retriever_version": "hybrid_v3",
  "dataset_snapshot": "budongi_2026_09_v1",
  "eval_version": "eval_c_v2",
  "prompt_version": "compare_prompt_v4"
}
```

각 Tool Call은 `request_id`, `tool`, 검증된 `arguments`, `started_at`, `duration_ms`, `row_count`, `status`, `snapshot_id`, 반환 레코드 ID를 기록한다. 전체 데이터 payload를 로그에 무조건 복제하지 않고 ID와 버전으로 원천 조회가 가능하게 한다. 반복 호출·실패·타임아웃도 남겨 Tool 선택과 데이터 품질 문제를 구분한다.

### Failure Taxonomy와 다음 작업 선택

| 코드 | 실패 유형 | 우선 살필 단계 |
|---|---|---|
| E01 | Retrieval Miss | 인덱스·검색·재정렬 |
| E02 | Wrong Entity | 단지 식별·entity 연결 |
| E03 | Filter Parsing Error | 조건 파서 |
| E04 | Numeric Error | 단위 변환·계산·생성 |
| E05 | Temporal Error | 시간 필터·거래 상태·날짜 선택 |
| E06 | Unsupported Claim | 컨텍스트 충실도·Prompt |
| E07 | Missing Constraint | 조건 반영·답변 템플릿 |
| E08 | Persona Misalignment | 우선순위 반영 |
| E09 | Format Failure | 구조화 출력·템플릿 |
| E10 | Routing Failure | 모델/어댑터 선택 규칙 |
| E11 | Stale Fact Preference | 최신 정보 우선 규칙 |
| E12 | Hallucination | 근거 없는 사실 생성 |
| E13 | Wrong Tool Selection | Tool 목록·선택 지시·4B 능력 |
| E14 | Invalid Tool Arguments | JSON/schema·단위·누락 인자 |
| E15 | Tool Execution Failure | 백엔드 검증·SQL·타임아웃·데이터 서비스 |

문제마다 복수 코드와 첫 번째 원인 단계(`tool_selection/argument/tool_execution/retrieval/generation/routing/evaluation`)를 남긴다. 오답을 건수와 비율로 집계하고 **가장 큰 수정 가능한 실패 유형 하나**를 다음 개발 과제로 선택한다. 예를 들어 Retrieval Miss가 크면 LoRA 학습보다 검색기 개선을 먼저 실험한다.

## 9. 지표·대시보드·판정 기준

| 영역 | 지표 |
|---|---|
| Tool/라우터 | Tool Selection Accuracy, 인자 Exact/F1, Tool 호출 수·실패율; 후속 Model/Adapter Accuracy·Macro F1·Expert 호출률 |
| Data Tool/파이프라인 | Tool p50/p95·타임아웃·빈 결과율, 수집 지연, 검증 실패율, 스냅샷 최신성, 취소/정정 반영률 |
| 검색 | Query Parsing 필드 정확도, 문서 Recall@1/3/5·MRR·nDCG, Entity Precision/Recall/F1, 검색 지연 |
| 필터/사실 | Filter Exact Match/F1, Entity Precision/Recall, Fact Accuracy, Required Fact Coverage |
| 생성 | Faithfulness, Completeness, Relevance, Unsupported Claim Rate, Format Compliance, pairwise Win/Tie/Loss |
| 예외/Persona | NO_MATCH/UNKNOWN Accuracy, Clarify 적절성, Persona Alignment, 동일 사실 유지율 |
| 시간 | C1~C4 정확도, Latest Record Accuracy, Stale Fact Error Rate, Date Citation Accuracy |
| 시스템 | mean/p50/p95/p99 지연, 초당 토큰, 피크 VRAM/RAM, 모델 로딩·어댑터 전환 시간, 실패율, API 비용 |
| 평가 신뢰도 | 사람-Judge 일치도, 평가 항목별 샘플 수, 추출 실패율 |

대시보드는 B0~B6/L1/L2를 같은 고정 Test 기준으로 비교하고, Eval-A/B/C와 task/persona/난도별로 분해한다. **Quality / Freshness / Faithfulness / Retrieval / Latency / Resource** 축을 나란히 제시하며 하나의 종합점수로 결론을 대체하지 않는다. 품질 대 자원 사용량 Pareto 산점도 및 95% 신뢰구간을 제시한다. **개선 판정은 사전 선택한 주요 지표**(예: Fact Accuracy와 Unsupported Claim Rate)와 허용 지연/메모리 한도를 함께 만족하는지로 한다. 라우팅은 평균 지연이 괜찮아도 p95/p99가 악화될 수 있으므로 꼬리 지연을 별도 확인한다. 최종 Test를 본 뒤 성공 기준을 바꾸지 않는다.

## 10. 단계별 실행 순서와 완료 조건

**보존된 연구 순서(제품 우선순위 아님):** ① 2023 스냅샷과 Data Serving(Phase 0~1) → ② Tool Calling MVP와 단계별 평가(2~5) → ③ 계산·검색 Tool 및 제한된 조합(6~10) → ④ 최신화·Temporal Eval(11) → ⑤ Judge·LoRA·라우팅·Persona(12~16) → ⑥ 대형 모델 비교·운영 검증(17). 각 단계의 완료 조건을 충족한 뒤 다음으로 간다. 앞 단계 결과가 충분하면 뒷단의 복잡한 구성은 생략할 수 있다.

| Phase | 핵심 질문과 최소 구현 | 완료 조건/다음 결정 |
|---|---|---|
| **0 데이터 복구** | 2023 `apartment/transaction/location/facility`의 Raw→Clean→Serving 및 `budongi_2023_v1` 스냅샷 | 단지 ID로 기본정보·거래·시설·위치를 코드만으로 동일 스냅샷에서 조회. |
| **1 Data Serving** | 검증된 Python 함수 `search_apartments`, `search_transactions`, `get_apartment_detail`와 파라미터화된 SQL | LLM 없이도 인자 검증·조회·구조화 반환 및 원천 ID 추적이 가능. |
| **2 Tool Calling MVP** | **4B 하나**가 허용 Tool을 선택·호출하고 결과로 답변; 별도 Router 없음 | Tool 선택→실행→결과→답변이 종단 실행되고 호출 로그가 남음. |
| **3 첫 질문 범위** | FACT/FILTER/COMPARE와 FACT_V1/FILTER_V1/COMPARE_V1만 지원 | 각 task와 NO_MATCH에서 근거 있는 답변 또는 적절한 결과 없음 처리. **첫 E2E MVP 완료 지점.** |
| **4 단계별 평가기** | Tool Selection, Argument, Entity Retrieval, Generation의 결정적 평가 | 각 실패가 어느 단계에서 발생했는지 자동 분리. |
| **5 Eval v1** | FACT 50/FILTER 60/COMPARE 60/NO_MATCH 30의 약 200건과 분할 | 한 명령으로 Tool/인자/Entity/Fact 지표와 `run_id`별 오류 파일 재현. **평가 가능한 MVP 완료 지점.** |
| **6 계산 Tool** | 가격 변화율·예산 비율·거리 등 결정적 백엔드 계산 | LLM 수치 계산 대신 검증된 결과를 설명하고 입력·결과를 채점. |
| **7 의미 검색 Tool** | 청약 제도·용어·비정형 공공 문서용 `semantic_search` | 구조화 조건을 의미 검색에 떠넘기지 않고 문서 Recall/MRR 측정. |
| **8 Hybrid Tool 조합** | 구조화 후보 검색→거리/시설 계산→필요한 문서 검색·재정렬 | 단일 Tool 대비 품질·지연 이득을 고정 평가셋으로 확인. |
| **9 제한된 Agent** | 허용 Tool·인자 schema·호출 횟수·타임아웃·결과 수 상한 | 무한 재호출 없이 오류·빈 결과·타임아웃을 처리. |
| **10 Tool 관측성** | request ID별 호출/인자/시간/행 수/상태/snapshot/반환 ID 로그 | 답변의 사실에서 Tool과 원천 레코드까지 계보 추적. |
| **11 최신화/Temporal** | 증분 수집·검증·upsert·index 갱신과 C1/C2 우선 구현 | 2023 스냅샷 유지, 정정/취소 반영, 최신값·과거값 충돌 평가. 이후 C3/C4 확장. |
| **12 AI Judge 보정** | Faithfulness/Completeness/Unsupported Claim과 사람 50건 | 사람-Judge 일치도·불일치 분석. Pairwise는 모델 비교에 추가. |
| **13 Prompt vs LoRA** | Base 4B ↔ Prompt ↔ `response_lora_v1` | 동일 Tool 결과에서 답변 품질 이득이 학습·서빙 비용을 정당화하는지 결정. |
| **14 Adapter Routing** | 이득이 입증되면 `structured_adapter`/`response_adapter` 두 개 | Tool 호출 결과와 task 기반 선택 정확도·전환 시간·메모리·품질 확인. |
| **15 Model Routing** | 단순 Tool 파싱→2B, 일반 설명→4B, 복잡·낮은 신뢰도→8B 후보 | 4B 단독 Tool 선택 성능이 충분하면 별도 Router 생략. 품질·p95·피크 메모리로 채택 결정. |
| **16 Persona** | 같은 Tool 결과를 Persona별 우선순위로 설명; Prompt부터 비교 | Fact Consistency/Persona Alignment/Constraint Satisfaction. |
| **17 대형 모델·운영 검증** | Local Base/Full/LoRA/Routing, Colab 20~30B zero-shot, GPT reference 비교와 자원 대시보드 | 동일 질문·Tool 결과/컨텍스트로 생성기 비교; 로컬 종단 성능은 별도 표시. p50/p95/p99·RAM/VRAM·비용·한계 보고. |

Phase 0~5의 최소 산출물은 `eval/dataset_v1.jsonl`, `tool_runs/*.jsonl`, `runs/baseline_v1.json`, `reports/baseline_v1.csv`처럼 재실행 가능하게 저장한다. 이후 실패 유형을 보고 평가셋을 2,000/300/300/Persona 200 규모로 확장한다. **기능 추가 → 평가 → 실패 분류 → 가장 큰 원인 한 가지 수정 → 재평가**를 매 단계의 반복 루프로 삼는다. 최신화는 Phase 11에서 Eval-C 제작과 함께 진행한다. 최종 2026 holdout과 대형 모델 비교는 설정을 확정한 뒤 수행한다.

## 11. 실행 체크리스트

- [ ] 2023 스냅샷과 cutoff를 버전으로 고정했다.
- [ ] Data Serving 함수 3개가 인자를 검증하고 파라미터화된 조회 결과를 반환한다.
- [ ] 4B 하나가 허용 Tool을 호출해 FACT/FILTER/COMPARE 답변을 끝까지 만든다.
- [ ] LLM에 직접 DB 접근 또는 자유 SQL 실행 권한이 없다.
- [ ] 약 200건 소형 Golden에서 Tool 선택·인자·조회·답변을 단계별 채점한다.
- [ ] Tool 호출 횟수·허용 목록·인자 schema·타임아웃·결과 수 상한을 정했다.
- [ ] 2024~2026 수집 자료의 원천·식별자·기준일·수집일을 보존했다.
- [ ] `raw_fact / clean_fact / derived_feature / model_output`을 분리하고 답변을 원천까지 추적할 수 있다.
- [ ] 가격/면적/거리의 단위와 거래 정정·취소 처리 규칙을 정했다.
- [ ] 계약일·신고일·수정/취소일·수집일을 별도 저장하고 최신값 선택 규칙을 고정했다.
- [ ] 최신 서비스 DB와 Eval-C 정답 파일을 분리했다.
- [ ] Train/Validation/Test 사이에 단지·거래·질문 변형 누출이 없다.
- [ ] Train과 Test의 질문 생성 방식도 분리하고 최종 Temporal Test를 봉인했다.
- [ ] Eval-A/B/C 및 C1~C4별 충분한 샘플과 정답 근거가 있다.
- [ ] NO_MATCH/AMBIGUOUS/오류 전제/상충 조건을 포함했다.
- [ ] Golden Dataset에 필수 사실, 금지 주장, 답변 요건, 템플릿 버전이 있다.
- [ ] 결정적 검사와 의미 평가를 나눴고 사실 추출 오류를 따로 측정한다.
- [ ] Query Parsing, Entity 검색, 문서 검색, 생성 결과의 중간 산출물을 각각 저장했다.
- [ ] request ID별 Tool 호출 로그에 인자·시간·상태·snapshot·반환 ID가 남는다.
- [ ] 숫자 변화율·거리·예산 비율은 백엔드 계산 Tool로 검증한다.
- [ ] 실험마다 model/adapter/tool schema/retriever/dataset/eval/prompt 버전과 run ID를 기록했다.
- [ ] E01~E15 실패 유형으로 분류해 다음 개선 대상을 결정했다.
- [ ] Judge는 모델명을 모른 채 채점하고 사람 50건과 보정했다.
- [ ] 검색기/Tool 종단 실험과 생성기 실험을 분리하고 동일 Tool 결과·Top-5를 저장했다.
- [ ] 4B Base/Prompt/RAG/LoRA/Adapter/Model Routing ablation을 같은 분할로 돌렸다.
- [ ] 단일 Response LoRA의 Prompt 대비 이득을 확인한 뒤 Adapter 확장 여부를 결정했다.
- [ ] Colab 대형 모델 및 GPT에 동일 질문·Tool 결과/컨텍스트·형식·평가 기준을 적용했다.
- [ ] 실측 VRAM/RAM, mean/p50/p95/p99 지연, 모델 로딩·Adapter 전환, 토큰속도/API 비용을 기록했다.
- [ ] 최종 Test는 설정을 확정한 뒤 한 번 실행하고 실패 사례와 한계를 남겼다.

## 12. 데이터 생성 프롬프트 전문

아래 세 프롬프트는 앞선 대화에서 제시된 전문이다. `{{CONTEXT}}`에는 출처·ID·날짜가 붙은 검증된 구조화 사실만 넣는다. 출력은 자동 검증과 사람 검수를 거쳐 Golden으로 승격한다. 검증용 프롬프트는 학습용과 별도 실행하고, holdout 자료를 학습 생성 단계에 노출하지 않는다.

### 12.1 LoRA 학습 데이터 생성 프롬프트

```text
당신은 부동산 RAG 시스템의 SFT/LoRA 학습 데이터를 설계하는 데이터 엔지니어입니다.

목표는 아래에 제공되는 STRUCTURED_CONTEXT의 사실만 사용하여, 한국어 부동산 질의응답 모델을 학습시키기 위한 고품질 instruction-response 데이터를 생성하는 것입니다.

중요 원칙:

1. STRUCTURED_CONTEXT에 존재하지 않는 사실을 절대로 추가하지 않습니다.
2. 미래 가격, 투자수익, 학군 수준, 지역 전망 등 근거가 없는 추측은 하지 않습니다.
3. 가격, 면적, 거리, 날짜 등 수치 정보는 원본 값을 정확히 유지합니다.
4. 동일한 사실을 묻더라도 사용자의 표현은 다양하게 생성합니다.
5. 지나치게 정형화된 질문만 만들지 말고 실제 사용자가 입력할 법한 자연스러운 표현도 포함합니다.
6. 모델이 Context를 활용하는 방법과 답변 형식을 학습하는 것이 목적이며 최신 부동산 지식을 암기시키는 것이 목적이 아닙니다.

생성할 TASK_TYPE:

- FACT
- FILTER
- COMPARE
- RECOMMEND
- EXPLAIN
- SUMMARY
- NO_MATCH
- AMBIGUOUS

각 Task마다 쉬운 문제, 일반 문제, 복합 조건 문제를 섞습니다.

질문의 난이도:

EASY
- 단일 사실 확인
- 단일 조건 검색

MEDIUM
- 조건 2~3개 결합
- 두 단지 비교
- 여러 사실 종합

HARD
- 여러 조건 우선순위
- 일부 조건 충족/불충족
- 사용자의 요구사항을 종합하여 설명해야 하는 경우

출력 답변은 다음 원칙을 지킵니다.

FACT:
핵심 사실을 먼저 제시하고 필요하면 기준일과 출처를 제공합니다.

FILTER:
검색 조건을 명확히 밝히고 조건을 만족하는 후보만 제공합니다.

COMPARE:
동일한 기준으로 두 대상을 비교하고, 사용자가 지정한 우선순위가 있다면 그 기준으로 차이를 설명합니다.

RECOMMEND:
먼저 사용자의 조건을 확인하고, 조건을 만족하는 후보와 그 근거를 Context의 사실을 이용해 설명합니다.
근거가 부족하면 단정하지 않습니다.

NO_MATCH:
정보가 존재하지 않는 경우 추측하지 않고 확인할 수 없다고 답합니다.

AMBIGUOUS:
질문 조건만으로 판단이 어려운 경우 부족한 조건을 명확하게 설명합니다.

각 데이터는 다음 JSON 형식으로 출력합니다.

{
  "task_type": "",
  "difficulty": "",
  "question": "",
  "context_ids": [],
  "required_facts": [
    {
      "entity": "",
      "field": "",
      "value": null
    }
  ],
  "forbidden_claims": [],
  "answer_requirements": [],
  "answer_template": "",
  "reference_answer": ""
}

reference_answer는 자연스럽고 실제 서비스에서 바로 사용할 수 있는 한국어 답변이어야 합니다.

같은 Context에서 여러 데이터를 생성할 경우 질문 표현, 조건 조합, 문체를 반복하지 마십시오.

정답을 생성한 뒤 스스로 다음을 검증하십시오.

- 질문에 답하는 데 필요한 모든 정보가 Context에 있는가?
- 답변의 모든 사실이 Context로 검증 가능한가?
- 숫자가 원본과 일치하는가?
- Context에 없는 평가나 추측을 추가하지 않았는가?
- 질문과 정답 사이에 모순이 없는가?

검증을 통과한 데이터만 최종 출력하십시오.

STRUCTURED_CONTEXT:

{{CONTEXT}}

생성 개수:

{{N}}
```

### 12.2 검증·평가 데이터 생성 프롬프트

```text
당신은 부동산 AI 시스템을 검증하는 Red-Team QA 데이터 설계자입니다.

목표는 모델에게 친절한 문제를 만드는 것이 아니라, 실제 서비스에서 발생할 수 있는 실패를 발견할 수 있는 평가 문제를 만드는 것입니다.

제공되는 STRUCTURED_CONTEXT만 사용합니다.

평가 데이터 생성 시 다음 유형을 균형 있게 포함하십시오.

1. 단순 사실 질문
2. 여러 조건이 결합된 필터 질문
3. 두 개 이상의 단지를 비교하는 질문
4. 사용자 조건 기반 추천 질문
5. Context에 답이 없는 질문
6. 일부 정보만 존재하는 질문
7. 모호한 질문
8. 비슷한 단지명 또는 지역명으로 혼동하기 쉬운 질문
9. 날짜 기준이 중요한 질문
10. 가격·면적·거리 단위 변환이 필요한 질문
11. 조건이 서로 충돌하는 질문
12. 사용자가 잘못된 전제를 포함한 질문
13. 검색 결과가 0건이어야 정상인 질문
14. 여러 후보 중 일부만 조건을 만족하는 질문

중요한 평가 원칙:

- 학습 데이터의 질문을 단순 재표현하지 않습니다.
- 가능한 경우 처음 보는 Entity 조합을 사용합니다.
- 정답을 맞히기 위해 사전 지식이 아니라 제공 Context를 사용해야 하도록 구성합니다.
- 근거 없는 추천이나 미래 전망을 유도하는 질문도 일부 포함하여 hallucination을 검사합니다.
- 질문 속에 잘못된 사실이 있으면 모델이 그대로 동의하는 것이 아니라 정정하거나 불확실성을 표현해야 합니다.

각 항목은 다음 JSON 구조로 반환합니다.

{
  "id": "",
  "task_type": "",
  "difficulty": "",
  "question": "",

  "expected_filters": {},

  "expected_entities": [],

  "required_facts": [
    {
      "entity": "",
      "field": "",
      "value": null,
      "tolerance": null
    }
  ],

  "forbidden_claims": [],

  "answer_requirements": [],

  "answerable": true,

  "expected_behavior": "ANSWER | NO_MATCH | UNKNOWN | CLARIFY",

  "reference_answer": "",

  "deterministic_checks": [
    ""
  ],

  "judge_checks": [
    ""
  ]
}

deterministic_checks에는 코드로 직접 검사할 수 있는 사항만 기록합니다.

예:
- price == 980000000
- station_distance == 420
- returned_entity_ids == ["APT001", "APT007"]
- answerable == false

judge_checks에는 의미 기반 평가가 필요한 사항만 기록합니다.

예:
- 사용자 조건을 빠뜨리지 않았는가
- 두 단지의 차이를 이해하기 쉽게 설명했는가
- 근거 없는 투자 판단을 추가하지 않았는가
- 정보 부족 상황을 적절하게 표현했는가

검증셋은 좋은 답변을 쉽게 생성할 수 있는 데이터보다 시스템의 약점을 드러낼 수 있는 데이터가 더 가치 있습니다.

STRUCTURED_CONTEXT:

{{CONTEXT}}

HOLDOUT 조건:

{{HOLDOUT_RULE}}

생성 개수:

{{N}}
```

### 12.3 Persona 기반 질문 생성 프롬프트

```text
당신은 실제 부동산 상담 서비스의 사용자 행동을 모사하는 Persona QA 데이터 설계자입니다.

제공되는 부동산 STRUCTURED_CONTEXT를 바탕으로 동일한 데이터를 서로 다른 사용자 Persona가 질문하도록 만드십시오.

중요 원칙:

- Persona에 따라 질문의 우선순위와 표현은 달라질 수 있습니다.
- 그러나 부동산 사실 자체를 Persona에 맞게 변경해서는 안 됩니다.
- Persona가 제공하지 않은 개인정보를 임의로 추가하지 않습니다.
- 단순히 Persona 이름만 바꾼 동일한 질문을 반복하지 않습니다.
- 실제 서비스 사용자가 입력할 법한 자연스러운 표현을 사용합니다.

Persona 후보:

1. 사회초년생
2. 신혼부부
3. 어린 자녀가 있는 가족
4. 중고등학생 자녀가 있는 가족
5. 1인 가구
6. 고령자
7. 서울 도심 직장인
8. 자차 출퇴근 사용자
9. 대중교통 중심 사용자
10. 예산을 가장 중요하게 보는 사용자
11. 주거 쾌적성을 중요하게 보는 사용자
12. 생활편의시설 접근성을 중요하게 보는 사용자

각 Persona에는 다음을 설정합니다.

{
  "persona_id": "",
  "household": "",
  "budget": null,
  "work_location": null,
  "transport_preference": "",
  "priorities": [],
  "constraints": []
}

Persona 질문은 다음 종류를 포함합니다.

- 후보 검색
- 조건 비교
- 추천
- 장단점
- 조건 충돌
- 예산 초과 판단
- 통근 관점
- 생활편의 관점

예:

같은 두 단지에 대해

사회초년생:
"회사까지 지하철로 다녀야 하는데 둘 중 어디가 더 현실적이야?"

어린 자녀 가족:
"아이 키우면서 살기에는 두 단지 중 어디를 먼저 검토할 만해?"

예산 우선 사용자:
"둘 중 9억 예산 안에서 현실적으로 가능한 쪽이 어디야?"

단, Context가 학군, 안전, 미래가격 등 특정 판단에 필요한 정보를 제공하지 않는다면 그 사실을 인정하도록 정답을 설계하십시오.

출력 형식:

{
  "persona": {},
  "task_type": "",
  "question": "",
  "context_ids": [],
  "persona_priorities": [],
  "required_facts": [],
  "required_considerations": [],
  "forbidden_claims": [],
  "reference_answer": "",
  "judge_rubric": {
    "fact_correctness": "",
    "persona_alignment": "",
    "constraint_satisfaction": "",
    "faithfulness": ""
  }
}

각 Persona별로 동일한 Context를 사용한 질문과 서로 다른 Context를 사용한 질문을 섞어 생성하십시오.

특히 동일 Context에 대해 여러 Persona 질문을 생성하여 모델이 사실을 바꾸지 않으면서 설명의 관점만 적절하게 변경하는지 평가할 수 있도록 하십시오.

STRUCTURED_CONTEXT:

{{CONTEXT}}

Persona 수:

{{PERSONA_COUNT}}

Persona당 질문 수:

{{QUESTIONS_PER_PERSONA}}
```

### 12.4 Tool Calling 평가 라벨 생성 프롬프트(추가)

앞의 세 프롬프트 전문은 유지한다. 아래 프롬프트는 **추가로 전달된 Tool 중심 설계**에 맞춰 생성된 질문에 정답 Tool/인자/반환 집합을 주석으로 붙이는 용도다. 이 출력은 자동 확정하지 않고 실제 Data Serving 함수 실행 결과와 대조해 Golden으로 승격한다.

```text
당신은 부동산 Tool Calling 평가 데이터의 라벨러입니다.

입력으로 주어진 QUESTION, STRUCTURED_CONTEXT, TOOL_SCHEMAS, SNAPSHOT_ID만 사용하십시오.
허용된 Tool은 TOOL_SCHEMAS에 있는 것뿐입니다. LLM에게 자유 SQL을 작성하게 하거나
Tool 결과, 단지, 거래, 가격, 날짜를 지어내지 마십시오.

해야 할 일:
1. 질문에 답하기 위해 필요한 최소 Tool 호출을 고릅니다.
2. 각 Tool의 인자를 schema에 맞춰 추출합니다. 단위는 원화 정수, 면적 ㎡, 거리 m로 정규화합니다.
3. 호출 순서가 필수인지, 순서를 바꿔도 같은 결과인지 표시합니다.
4. 질문에 답할 수 없거나 조건이 부족하면 expected_behavior를 NO_MATCH/UNKNOWN/CLARIFY로 둡니다.
5. Tool의 예상 반환 entity/거래 ID와 답변 필수 사실은 제공 사실에서만 채웁니다.
6. 기계적으로 채점할 수 있는 검사와 의미 평가가 필요한 검사를 분리합니다.

JSON 하나로만 출력하십시오:
{
  "question_id": "",
  "snapshot_id": "",
  "task_type": "FACT | FILTER | COMPARE | RECOMMEND | EXPLAIN | SUMMARY | NO_MATCH | AMBIGUOUS",
  "expected_tool_calls": [
    {"tool": "", "arguments": {}, "order_required": true}
  ],
  "expected_entities": [],
  "required_facts": [],
  "forbidden_claims": [],
  "answerable": true,
  "expected_behavior": "ANSWER | NO_MATCH | UNKNOWN | CLARIFY",
  "deterministic_checks": [],
  "judge_checks": [],
  "label_evidence_source_ids": []
}

출력 전 확인하십시오:
- 모든 Tool 이름과 인자 키가 TOOL_SCHEMAS에 존재하는가?
- 모든 ID·수치·날짜가 STRUCTURED_CONTEXT에 존재하는가?
- 정정·취소 거래를 유효 거래로 오인하지 않았는가?
- 최종 답변 필수 사실과 Tool 반환 근거가 연결되는가?

QUESTION:
{{QUESTION}}

STRUCTURED_CONTEXT:
{{CONTEXT}}

TOOL_SCHEMAS:
{{TOOL_SCHEMAS}}

SNAPSHOT_ID:
{{SNAPSHOT_ID}}
```
