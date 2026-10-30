# 집담 gstack 서브에이전트 역할 안내

```json
{"approval_ref":null,"content_hash":"4369034664a33802581d9bbd4e5eb8b1f90d166a4bd0c4714c4c56d32d501527","created_at":"2026-10-28T04:25:00+00:00","environment":"Windows / Codex CLI","id":"WIKI-6EFA6AB497CA1504","key":"GSTACK-AGENT-ROLES","kind":"guide","module":"developer-agent-roles","owner":"keulreobeu","project":"jipdam","publication_approved":false,"publication_approved_by":null,"replacement":null,"review_at":"2027-04-26T04:25:00+00:00","reviewer":"agent-codex","revision":1,"risk":"low","sources":[{"path":"docs/gstack-subagents.md","sha256":"f6bda4ec6e47fb119abcce622e29b419da286ca536e684f6d5344200d323bac9"}],"status":"ACTIVE","task_id":"TASK-GSTACK-AGENTS-001","title":"집담 gstack 서브에이전트 역할 안내","updated_at":"2026-10-28T04:25:00+00:00","verified_at":"2026-10-28T04:25:00+00:00","version":"2026-10-28"}
```

## 목적 및 적용 범위

집담 Codex의 gstack 역할과 사용 범위를 설명한다. 이 문서는 역할 선택을 돕는 안내이며 운영 및 보안 정책을 변경하지 않는다.

## 증상 또는 사용 상황

사용자가 독립적인 설계, 코드 리뷰, 원인 조사, QA 또는 문서 검토를 서브에이전트에 맡기려는 경우다.

## 원인과 미확인 사항

각 역할은 프로젝트 설정에서 정의되고 자신에게 할당된 gstack 스킬을 사용한다.

## 실행 절차

새 Codex 세션에서 원하는 역할과 검토 범위, 수용 기준을 명시한다. planner는 plan-eng-review, reviewer는 review, investigator는 investigate, qa는 qa-only, docs는 document-release 스킬을 사용한다.

## 주의사항 및 예외

공유 작업공간과 기존 프로젝트 데이터 및 외부 작업 승인 경계를 유지한다. 각 역할의 읽기 전용 업무 범위는 요청과 상위 지침을 따른다.

## 검증 방법 및 결과

2026-10-28 Codex 새 세션 원본 기록에서 다섯 역할의 생성과 완료 이벤트를 확인했다. 스킬 전체 업무 절차를 검증한 것은 아니다. 모델 없는 제품 323개와 팀 35개 검사 및 합성 CLI smoke가 통과했다.

## 관련 원본

저장소의 docs/gstack-subagents.md 및 docs/tasks/gstack-subagents-20261028.md를 참조한다.
