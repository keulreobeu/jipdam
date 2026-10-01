# Golden 데이터 자리

`dataset_v1.jsonl`은 실제 스냅샷으로 도구 실행 결과를 확인한 뒤 사람 검수해 만듭니다.
현재 예시 정답이나 실측 점수는 포함하지 않습니다. Test 분할은 개발 중 설정 선택에 쓰지 마세요.

`required_facts`는 원자 사실 배열로 작성합니다. 각 항목은 `entity`, `field`, `value`가 필요합니다.
`entity_aliases`에는 답변에서 해당 대상을 부를 수 있는 단지명과 ID를 적습니다. 생략하면
canonical `entity` ID가 답변에 있어야 합니다. Alias와 값은 같은 문장에 있어야 채점됩니다.
숫자는 반드시 `unit`을 지정하고, 허용오차가 필요하면 `tolerance`를 함께 적습니다.
지원 단위는 `m`, `㎡`, `원`, `만원`, `년`과 문서화된 표기 alias입니다. 원화 금액은 `원`,
`만원`, `억 원` 표현 사이를 환산합니다. 날짜 문자열은
`YYYY-MM-DD`를 기본으로 하며 답변에서 `YYYY년 M월 D일`, `YYYY.M.D` 형식도 인식합니다.

예시 구조:

```json
{"entity":"APT_A","entity_aliases":["APT_A","마곡 테스트 단지"],"field":"station_distance",
 "value":350,"unit":"m","tolerance":5}
```

지원하지 않는 unit/value, null 값, 누락된 prediction은 `not_measured`입니다. 실제 snapshot이나
검수 Golden을 추가하기 전에는 coverage를 실제 부동산 성능으로 해석하지 않습니다.

로컬 모델 연결 확인용 가상 자료와 실행 로그는 `.local_runtime/synthetic_smoke/`에 따로 둡니다.
그 결과는 실제 Golden이나 부동산 성능 지표에 포함하지 않습니다.
