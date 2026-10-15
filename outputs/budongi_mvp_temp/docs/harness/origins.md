# Phase 0 — 출처·재사용·충돌 평가

2026-10-14 Master와 실제 read-only native subagent `/root/source_assessment`가 조사했다.
VQA ZIP: `ssafy16-vqa-harness.zip`, 827 entries, SHA256 `1197d211548df90d2914748ccf6b2ec9ca7fbbd65ae03dab23af1b57d4f0016c`.
참고 패키지: `Jipdam_Harness_Implementation_Package.zip`, SHA256 `0aa63e2114216f7c78cb4113be30516e8f289f4281a2e876d9ace42011714363`.
제공된 Plan/Implementation Prompt/reuse manifest를 읽었고 starter 코드는 복사하지 않았다.

명시적 LICENSE/COPYING/NOTICE/저작권 파일이나 관련 후보의 재배포 허가문은 확인되지 않았다.
사용 권한/원본 commit은 **unverified**이며, 소스/상태/데이터/키/.git은 복사·실행하지 않았다.
아래는 동작 개념을 바탕으로 새로 구현한 결정표다. 라이선스 부재를 허가로 해석하지 않는다.

| 원본 경로 | SHA256 | 결정 | 집담 대상 | 차이·충돌 처리 |
| --- | --- | --- | --- | --- |
| `scripts/autopilot.py` | `49e8f9b5c7e29d29e65b86636e0789b7b5b80e8f9a1816311b4938faacfd119a` | reimplement | state.py | 상태 전이/원자적 claim/제한 재시도; 대회/자동 push 제외 |
| `scripts/wait_signal.py` | `a67ec3be4cf9ebeef945737ec2a92c473bcf2ce7e2cd7a7d0a9863d6da83ffb3` | reimplement | state.py events | event id cursor; Colab/ADC 제외 |
| `scripts/hooks/precompact_checkpoint.py` | `42232217a57ee0b4d2f0f4b9de03db19cf7e2a3cb1a068177d299c36ffd6a7a0` | reimplement | state.py checkpoint | DB snapshot/hash; Claude hook 미설치 |
| `scripts/hooks/session_start_inject.py` | `1c55232f9e9585941c1b002a5e4c21781612d12820a4c8e4eedaecb20f609791` | reimplement | state.py context + CLI | 명시적 resume; 자동 hook 제외 |
| `src/lockfile.py` | `84871d55620ed59c3fd2c415cae017d8353c8aaf8beb08c0a29edf5e3e634651` | reject code / reimplement behavior | state.py transaction | SQLite BEGIN IMMEDIATE; 잠금 실패 무시 제거 |
| `_workspace/ledger/ledger.jsonl` | `20b3e4b4c2ce9809cf0845a5e20ef9435b84726800a23667e76100b79055dfdd` | schema reference only | runs/events/artifacts tables | 과거 원장/점수/데이터 미이식 |
| `_workspace/decisions/pipeline_queue.yaml` | `3eebed805b172c1d496e7f8ee8506423ed846090b1d86e35452bc28d7253b1ae` | schema reference only | tasks/runs tables | 선택적 역할 큐; Colab 고정3병렬 제외 |
| `.claude/skills/vqa-experiment-loop/SKILL.md` | `de6ae6aa530d07f44ff68516b68d29f4c91a69e1608f0378a198ec1e2483c16f` | rewrite | Master workflow + Codex roles | 모델 고정/Claude team API 제외 |
| `scripts/git_txn.py` | `5468656976f38bdeb9318bf4ccd6c6c31d19c0ffb1d0aa46c965f33d57a45d41` | reject | 없음 | 자동 commit/push 미도입 |
| `scripts/submit_cycle.py` | `0770062fb44e865b49ef31cabfd049f5463f2463ed75542e7ea8c90b0d78ff9e` | reject | 없음 | Kaggle 제출/자동 publish 제외 |
| `scripts/colab_guarded.py` | `a24a48bc6f60f66744fd2380ee23aebf52089b6cec06f730c6027b4d9f068065` | reject | 없음 | GPU/Colab/자격증명/학습 제외 |
| `.claude/agents/code-engineer.md` | `7568f89c1630862bd59ada22e3e96aad4a110dc6b85d8e4a40c0b9aad6c9b86a` | rewrite role concept; no copy | `.codex/agents/` | 호스트·모델 고정 제거; Claude native 미검증 |
| `.claude/agents/evaluator.md` | `bba0a79f80b6b3e078a0e4250d956acf8872c72d925311153f65e6737aca887a` | rewrite role concept; no copy | `.codex/agents/` | 호스트·모델 고정 제거; Claude native 미검증 |
| `.claude/agents/experiment-planner.md` | `4cc6ab3a36afe715bd24bdc28b42f458c5508ebe93983313ac6e524df1f1847d` | rewrite role concept; no copy | `.codex/agents/` | 호스트·모델 고정 제거; Claude native 미검증 |

기존 코드와 충돌: `budongi/gms_budget.py`는 실크레딧·토큰 예약/uncertain/유료 count를 이미 구현했다.
`gms_work.py`는 견적만으로도 count 통신이 생길 수 있다. 이번에는 두 경로/보관함을 인스턴스화하지 않는다.
새 Mock 원장은 합성30,000/예비3,000이고 기존500크레딧/10,000토큰/5,000크레딧 보존을 덮어쓰지 않는다.
참고 설계의 GMS-001 재등록은 기존 ID와 충돌하므로 HARNESS-001로 분리했다.
기존 SDD/gstack/제품 코드·로컬 추천·역사평가를 보존했다. 고정 gstack 수 검사는 새 프로젝트 스킬을
허용하되 생성된 gstack 수/중복/fixture guard를 계속 검사하도록 수정하고 회귀 테스트했다.

원본 autopilot의 파일 상태+별도 event 이중 쓰기와 lock fallback은 채택하지 않았다.
SQLite 트랜잭션으로 task/run/event를 함께 기록한다. Windows 대소문자·후행점/공백 aliases를 검사한다.
실험 결과/attempt/증거를 이벤트에 보존하고 VQA 점수를 제품 평가로 상속하지 않는다.

검증 범위: ZIP metadata/source 정적 점검만 했다. VQA test/스크립트/외부 호출은 실행하지 않았다.
소스 분석 agent 토큰은 도구 미제공으로 unknown, GMS live 호출은 0회/0토큰이다.
