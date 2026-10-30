# TASK-META-INTEGRATE-001 — 팀 통합 메타데이터와 DB/PK 설계

```toml
kind = "task"
id = "TASK-META-INTEGRATE-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/31_metadata_integration_spec.md"]
scope = [".gitignore", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/docs/specs/31_metadata_integration_spec.md", "outputs/budongi_mvp_temp/docs/tasks/metadata-integration-20261030.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/plans/metadata-integration-20261030.md", "outputs/budongi_mvp_temp/docs/adr/ADR-028-apartment-identity.md", "outputs/budongi_mvp_temp/docs/metadata-db-design.md", "outputs/budongi_mvp_temp/docs/wiki/pages/"]
acs = ["META-INTEGRATE-001-AC-01", "META-INTEGRATE-001-AC-02", "META-INTEGRATE-001-AC-03", "META-INTEGRATE-001-AC-04"]
```

Jira [KAN-32](https://kwulreobeu.atlassian.net/browse/KAN-32) / agent-codex / 진행 중. 이번 작업은 문서·워크북·팀별 검증 이슈 등록이며 실제 팀원 검증/관계 확정/DB 모델 구현은 후속이다.

## 완료 기준

- [ ] META-INTEGRATE-001-AC-01 원문·75개 항목·컬럼·품질·이슈·보충 보존과 워크북 검증
- [ ] META-INTEGRATE-001-AC-02 네 수집자의 명시적 검증 업무/Jira 배정
- [ ] META-INTEGRATE-001-AC-03 단지/동/호/대장 분리와 전 항목 DB/테이블/PK안
- [ ] META-INTEGRATE-001-AC-04 인계·SDD·위키·게시 상태

## 현재 결정

수집자 기재 상태는 원문으로 유지하며 이번 작업이 실데이터를 재측정했다고 표시하지 않는다. 파일 namespace는 lee/seo/kim/lsj다. 표제부는 대장 앵커 후보, 내부 단지 마스터와 기존 canonical source ID는 별개다. 원본 파일·DB는 변경하지 않는다.

KAN-28은 별도 진행 중이다. 사용자는 2026-10-29 통계 전체 worker 시간 20% 단축, 다른 세 유형의 지정 범위 시간과 네 유형의 최대 관측 RSS 10% 이내 회귀, 완전 동일 결과를 승인했다. 재승인 질문을 반복하지 않는다. 목표 평가의 승인 범위/기준선 고정 보강 후 계약 테스트 19개 통과. 최종 5회 성능·전체 출력 재검증과 위키 최신 반영은 계속 추적한다.

## 검증

실제 실행 결과를 여기에 추가한다. 후속 이슈는 데이터 소유자가 증거를 제출할 때까지 열린 상태로 유지한다.
