# 집담 gstack 서브에이전트 사용 안내

집담 Codex 프로젝트에는 독립 작업을 명시적으로 요청할 때 사용할 수 있는 gstack 기반 서브에이전트 역할이 있다. 프로젝트가 신뢰된 상태에서 새 Codex 세션을 시작하면 프로젝트 설정에 등록된 역할을 사용할 수 있다. 각 역할은 집담 공통 지침과 지정 스킬을 읽는다.

| 역할 | 스킬 | 담당 범위 |
| --- | --- | --- |
| `gstack_planner` | `gstack-plan-eng-review` | 설계와 수용 기준 검토 |
| `gstack_reviewer` | `gstack-review` | 변경사항의 읽기 전용 리뷰 |
| `gstack_investigator` | `gstack-investigate` | 증상 재현과 원인 조사 |
| `gstack_qa` | `gstack-qa-only` | 읽기 전용 CLI/API 검증 |
| `gstack_docs` | `gstack-document-release` | 문서와 구현의 차이 조사 |

예: “`gstack_reviewer`에게 이번 변경을 읽기 전용으로 검토하게 하고, `gstack_qa`에게 관련 CLI 검증을 맡겨줘.” 부모 에이전트는 작업 범위, 수용 기준과 기대 결과를 명시하고 두 결과를 확인한다. 동시 실행 한도는 프로젝트 설정에 따른다. 기존 하네스 전용 `jipdam_*` 역할은 별도로 유지한다.

서브에이전트는 같은 작업공간을 공유한다. 독립된 파일시스템이나 숨은 테스트의 비밀성을 가정하지 않는다. 데이터·자격증명·원격 작업의 승인 범위와 프로젝트의 Spec, Task, 위키 계약은 그대로 적용된다. 스킬의 전체 절차와 작성 권한은 요청 범위와 충돌하지 않을 때만 실행한다.

2026-10-28 Windows 검증: 새 Codex 세션에서 위 다섯 역할의 생성 및 완료 이벤트를 확인했다. 이는 역할 생성 smoke이며 각 gstack 스킬의 전체 업무 절차를 검증한 결과는 아니다. 상세 및 기존 환경 검사 결과는 [TASK-GSTACK-AGENTS-001](tasks/gstack-subagents-20261028.md)을 따른다.
