# ADR-028 — 단지·동·호와 건축물대장 식별자를 구분

Status: Proposed for future model implementation. 2026-10-30 / KAN-32 / META-INTEGRATE-001. 이번 변경은 설계 제안이며 기존 DB/ID 마이그레이션이 아니다.

단지 내부키 complex_id, 건물 내부키 building_id, 호 내부키 unit_id를 각각 두는 통합 마스터를 제안한다. 현재 canonical v3는 출처별 namespace/source ID 엔터티이며 기존 ID/FK를 보존한다. 새 통합 마스터로 연결할 때 별도 검수 관계를 추가한다.

표제부의 mgmBldrgstPk는 출처별 건축물대장 식별자이므로 `(source_namespace, regstrKindCd, mgmBldrgstPk)`로 보존한다. 종류 1 총괄표제부, 2 일반건축물, 3 표제부, 4 전유부를 구분한다. 총괄표제부를 단지와 일대일로 가정하지 않고 mgmUpBldrgstPk의 namespace·대상 종류·시점을 검증한다. 구·신 API의 PK 변경은 공식 대응이 확인되기 전 별개 namespace다.

K-apt 코드, 건축물대장PK, 공시가격 단지:동:호 코드, MOLIT aptSeq는 source identifier로 별도 보존한다. 이름/주소 일치로 단지를 병합하지 않는다. 현재 Kim D006/D007은 전유부/전유공용면적 수집 중 스냅샷이며 표제부 확보를 증명하지 않는다. 면적 행은 1:N 관측이므로 mgmBldrgstPk 단독 PK를 사용하지 않는다.

판단 근거와 공식 링크, 테이블별 키와 검증 조건은 metadata-db-design.md에 정리한다. 실제 적용은 수집자 검증·관계 검토와 별도 구현 Task 이후다.
