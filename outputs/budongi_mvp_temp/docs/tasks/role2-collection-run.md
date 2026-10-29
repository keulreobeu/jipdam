# TASK-ROLE2-COLLECT-001 — 2번 실제 수집·기록·교차검증

```toml
kind = "task"
id = "TASK-ROLE2-COLLECT-001"
status = "in_progress"
owner = "cannedJean"
specs = ["outputs/budongi_mvp_temp/docs/specs/27_role2_collection_spec.md"]
scope = ["AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", "outputs/budongi_mvp_temp/docs/role2-collection-validation-20261029.md", "docs/data-collection.md", "outputs/budongi_mvp_temp/docs/tasks/role2-collection-run.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["ROLE2-COLLECT-001-AC-07", "ROLE2-COLLECT-001-AC-08"]
```

## 목표·범위·제외 범위

실행 Task. 2026-10-29 사용자 승인 범위(두 AGENTS.md의 승인문)에서 2번 출처를 COLLECT-001 절차로 수집하고, 배치별 패키지·Issue 초안·메타데이터 워크북·다중 LLM 검증 기록을 남긴다. Issue 게시와 Drive 업로드는 사용자가 한다.

제외: 자동 게시·업로드, 좌표 변환·매칭·DB 적재, #40·#41 재수집.

## 완료 기준

- [ ] ROLE2-COLLECT-001-AC-07 배치별 Issue·상태·건수·ZIP·SHA-256·검사기 일치 기록
- [ ] ROLE2-COLLECT-001-AC-08 유닛별 생산자·감사자·심판 모델, role_guard 위반 0건, 판정 원장 요약

## 결과·남은 조건

진행 중. [검증 기록](../role2-collection-validation-20261029.md)을 따른다.
