# Observability v2.3 적용 계획 — KAN-30

1. 현재 checkout·제공 문서·공식 CLI 계약 대조, 원본 파일 hash와 차이를 기록한다.
2. 별도 append-only metrics, streaming Codex adapter, 기존 lifecycle hook을 순서대로 구현한다.
3. 봉인 suite와 독립 품질·승인 gate를 연결하고 실패/누락/분모를 노출한다.
4. 비과금 프로세스 fixture·재시도/승인 회귀·SDD·환경 검사, 위키 동기화를 수행한다.
5. 전담 Git agent가 이번 변경만 별도 publisher에서 검증·공유하고 원격 결과를 확인한다.

```text
managed Task → Run(profile hash) → Attempt → Invocation
                                     │          │
                                 validation   Codex JSONL
                                     │          │
                                     └── append-only metrics.sqlite3
                                                  │
                        frozen suite/item + independent outcome → report
```

기존 실행/승인 상태는 managed DB가 책임진다. metrics 저장 실패는 partial, 디스크 상한/초대형
줄은 collector health 경고로 처리한다. 기존 미저장 위키/파이프라인 변경은 Git 공유에서 제외한다.
실제 B0·O1 결과가 없으므로 토큰 절감률이나 공급자 우열을 만들지 않는다. 위험/실험 차단점은
운영 문서의 적용 표에 명시한다. 외부 리뷰 CLI는 현재 요청에 포함되지 않아 호출하지 않는다.
