# 팀 메타데이터 통합·DB 설계 실행 및 인계

고정 범위: KAN-32 / META-INTEGRATE-001. 네 워크북으로 통합 메타데이터, 수집자별 검증 Jira, DB/테이블/키 제안을 제공한다. 원본 검증을 대신 수행하거나 실제 DB를 마이그레이션하지 않는다.

| 단계 | 담당/스킬 | 시작 조건 | 완료 근거 |
| --- | --- | --- | --- |
| 1 통합 목록 | Codex, spreadsheets | 최신 네 파일·해시 | 75개 namespace 항목/원문·보충 보존·렌더·독립 대사 |
| 2 키·저장 모델 | Codex, gstack-plan-eng-review | 원문 grain·현행 계약·공식 문서 | 출처 관측/실체·버전·PK·미확보·현재/목표 구분 |
| 3 수집자 자체 검증 | 각 소유자, jipdam-workflow + gstack-qa-only | 본인 보존 원본·manifest | 해시·입출력 대사·키/NULL/CRS/기준일·미완료 보고 |
| 4 오류 수정 | 각 소유자, gstack-investigate → gstack-qa | 재현된 결함 | 원인·매핑 버전·회귀·봉인 패키지 |
| 5 내부키·관계 검토 | 건축 파트 주도, gstack-plan-eng-review + gstack-review | 자체 검증 결과·대장 종류/서비스 키 | 불일치/미연결/1:N·근거·검수 후보표. 실제 확정은 별도 승인 |
| 6 통합 적재 | 이진호 조정, KAN-28/후속 구현 Task, gstack-plan-eng-review → gstack-qa → gstack-review | 봉인 입력·합의한 교환 계약 | 원본별 typed 모델·동일 결과·중복/복구·계보 |
| 7 위키·인계·Git | gstack-document-release + gstack-context-save, Git 전담 agent | 검증된 문서·고정 scope | 위키 read-back·Task/Jira·게시 영수증. 새 채팅은 gstack-context-restore |

팀 검증 이슈는 이번 워크북 작성 완료와 함께 닫지 않는다. 문서에 기록된 수집자 검증 완료와 중앙 수용을 혼동하지 않는다. 이번 논리 DB안의 물리 생성, Snowflake 예산/적재, Airflow 운영은 후속 구현이다.

## 재개

루트/제품 AGENTS → jipdam-workflow → TASK-META-INTEGRATE-001 → metadata-db-design.md → Jira KAN-32의 팀 이슈를 읽는다. 실제 워크북은 outputs/metadata-integration-20261030-kan32/에 있고 원본은 Downloads다. 다른 PC에서는 원본 네 파일과 SHA를 확인한다. 작업 파일/실데이터를 GMS 문맥에 보내지 않는다.

기존 KAN-28의 확정 성능 목표와 단계별 gstack 배정은 pipeline-m1 Plan/Task에 남아 있다. 해당 미완료를 이 설계 작성으로 종료하지 않는다. 기존 사용자 미커밋 변경을 유지하고 Git 전담 agent가 허용된 고정 문서만 별도 publisher에서 저장한다.

## GSTACK REVIEW REPORT

구조 검토 범위는 이 메타데이터 설계다. native 읽기 전용 검토에서 현행 canonical의 출처별 ID 보존, 대장 종류를 포함한 식별자, source file+section+row와 1:N component 계보, 상위 관계의 타입/시점, 수집자 검증과 중앙 수용 분리를 반영했다. 외부 모델 검토·실데이터 관계/좌표 검수는 수행하지 않았다. 정식 저장형 review log와 최종 근거는 Task를 따른다.
