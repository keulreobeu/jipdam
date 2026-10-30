# ADR-027 — One real feature, immutable experiment inputs

Accepted 2026-10-30 / 사용자 BENCH-FACILITY-001 실행·Objective 중복 제거 비교 요청 / KAN-31.

관측성 시스템을 다시 만들지 않고 managed Task/Orchestrator/MetricsStore를 재사용한다.
명세와 독립 acceptance를 구현 전에 봉인한 C_SHA로 모든 worker를 분리한다. 기존 dirty
checkout이나 앞선 trial의 구현을 다음 실행에 전달하지 않는다. 본문에는 실제 데이터가 없다.

Task scope 밖의 Spec을 context_files에 넣으면 현행 pack_context가 scope 오류를 내고,
team-data-contract.md는30,049B로24KB 한도를 넘는다. 이 실험에서는 고정된 bounded 명세를
objective에 넣고 context_files=[]로 둔다. context 로더/보안 경계는 바꾸지 않는다. 독립 tests는
시작 commit에 있고 읽을 수 있으나 구현 scope 밖이다. 숨겨진 평가라는 주장은 하지 않는다.

objective_mode=repeat를 기존 기본으로 보존하고 once를 opt-in으로 추가한다. 정확한 trusted
Task/objective prefix일 때만 중복을 제거해 직접 provider API가 목표를 잃지 않게 한다.
기존 CLI의 actual --model은 constructor가 결정하므로 runner에서 model과 Task metadata를
같게 고정한다. GMS provider 전환은 Codex 비교의 교란이므로 사용하지 않는다.

ABBA 4trial은 반복/캐시/순서 변동을 드러내는 작은 pilot이다. 제품 기능은 하나이며 trial4개를
작업4개 성과로 부풀리지 않는다. 완전한 공식 usage와 독립 품질·승인 조건이 없으면 절감률을
확정하지 않는다. provider-native Cloud/Claude/새 collector/DB/설비 연계는 추가하지 않는다.
