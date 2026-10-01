# 기존 저장소에서 가져온 범위

원본: [Real_estate_Chatbot_by_gemma4](https://github.com/keulreobeu/Real_estate_Chatbot_by_gemma4), `main`의 `f4ae6a9ce57b4c395df9355c1806197174ab9a4a` 커밋을 브라우저에서 확인하고 ZIP으로 읽었습니다.

| 이전 자산 | 이번 처리 | 이유 |
|---|---|---|
| `01_preprocessing/preprocess_apartment_pipeline.py`의 CSV 인코딩 fallback·주소 분리 | `src/budongi/legacy.py`로 축소·재구성 | 한국어 원본 접근에 필요한 작은 호환 기능 |
| `02_gemma4_generation/config/models.local.example.json` | 모델 ID/양자화를 코드에 고정하지 않고 CLI 인자로 받음 | 플랜에서 4B 후보를 실측 후 선정하도록 명시 |
| `02_gemma4_generation/inference/*` | 복사하지 않음 | 이전 인터페이스는 자유 텍스트 생성 중심이고 새 Tool Calling 계약과 다름 |
| `02_gemma4_generation/query_service.py` | 복사하지 않음 | 평면 CSV·규칙 기반 라우팅 대신 검증된 Tool 3개로 재설계 |
| `05_finetuning_prep`, `06_finetuning` | 복사하지 않음 | LoRA는 Data Tool과 기준선 평가 후의 단계 |
| 이전 보고서·웹 데모·실행 스크립트 | 복사하지 않음 | 현 단계의 실행 경로와 입력 계약을 혼동시키지 않기 위해 제외 |
| `data/original`, `data/qa`, `data/eval` | 실제 파일 없음 | GitHub ZIP에는 `.gitkeep`만 있으므로 데이터나 평가치를 재사용할 수 없음 |

새 DB 스키마·도구·오케스트레이터·평가기 코드는 첨부 플랜의 Phase 0~5 범위에 맞춰 새로 작성했습니다. `공급액(만원)`은 거래가격으로 승격하지 않았습니다.
