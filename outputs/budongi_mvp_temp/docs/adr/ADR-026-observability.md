# ADR-026 — Separate, append-only shadow metrics

Accepted 2026-10-30, 사용자 제공 문서 적용 요청 / OBS-001 / KAN-30.

managed state DB의 마지막 usage는 호환 출력으로 유지하되 측정의 정본으로 쓰지 않는다.
별도 metrics.sqlite3에 최소 허용 필드·불변 프로파일·턴별 Usage·lifecycle을 기록하고
리포트를 재생성한다. SQLite/WAL과 표준 라이브러리를 재사용해 외부 collector·새 의존성을
추가하지 않는다. Observer 장애는 기존 승인/재시도 흐름을 변경하지 않고 partial로 드러낸다.

프롬프트·응답·추론·MCP payload·키·원본 DB는 계측하지 않는다. context는 명시 코드 파일의
해시/byte만 기록하며 실제 모델 토큰 기여도로 환산하지 않는다. source identity가 없는
동일 수치 관측은 invocation 안의 수신 턴 순번으로 분리한다. 별도 원천은 자동 합산하지 않는다.

성공은 사전 고정된 원본 benchmark item의 독립 평가와 승인을 요구한다. 에이전트가 바꿀 수
있는 일반 회귀 테스트 통과를 독립 평가 성공으로 승격하지 않는다. 비용 추정/구독료/실청구/
GMS 크레딧은 후속 별도 계약이며 수치 합산하지 않는다. Claude와 Cloud는 호환 인터페이스만
예약하고 공식 연동·권한 확인 전 not_integrated다. Baseline 전 prompt 최적화는 보류한다.
