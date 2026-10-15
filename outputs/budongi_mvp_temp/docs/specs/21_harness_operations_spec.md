# Harness operations — GMS reserve and automatic commits

```toml
kind = "spec"
id = "HARNESS-OPS-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-15"
approval_ref = "현재 대화: Codex CLI에서 GMS 가능하면 최대 사용·1,000크레딧 보존·새 브랜치와 오토커밋 추가"
```

## HARNESS-OPS-001-REQ-01 GMS 우선과 잔액

2026-10-15 추가 사용자 지시에 따라 현재 고정 보존액은 0이다. reserve_only로 가용 잔액 전부 사용을 허용한다.
실잔액·사전 count·최대 예약·공통 원장·active/uncertain hold·만료·기술 상한은 유지한다. 과거 1,000/5,000 정책과 uncertain 보류는 이력으로 남기고 원장을 초기화하지 않는다.
Codex CLI native GMS는 공식 Responses/gateway 호환성과 전체 요청 예산 검증이 있을 때만 활성화한다.
키를 CLI 환경변수나 전역 provider 설정에 직접 넣어 기존 예산을 우회하지 않는다.
미검증/예산 경계로 차단되면 기존 GMS draft adapter를 계속 우선 사용하고 사실과 이유를 기록한다.

### HARNESS-OPS-001-AC-01

0 보존 저장/가용 잔액 최대 사용/부족 잔액 거부/최대 예약·보류 보전·재시작 및 저장 정책 변경을 검증한다.
실제 native CLI gateway 요청의 가용성/프로토콜/한계를 명시하고 미지원 능력을 성공으로 보고하지 않는다.

## HARNESS-OPS-001-REQ-02 자동 커밋

전용 codex/ 브랜치에서 검증 통과 후 허용 scope의 변경만 로컬 commit한다.
승인 필요 작업은 approve 뒤 commit하며 승인 불필요 작업은 검증 성공 뒤 수행한다.
자동 push/merge/amend/force/reset은 하지 않는다. 사용자 기존 index와 범위 밖 변경은 보존한다.
민감 파일/DB/raw/log/runtime/키·Git 설정/외부 symlink·범위 밖 staged 변경은 거부한다.
commit 대상은 실제 검증한 hash/HEAD와 일치해야 한다. 실패는 상태·이벤트에 기록하고 검증 성공을 지우지 않는다.
자동 커밋은 명시 기능 스위치로 제어하고 재요청/재시작으로 같은 결과를 중복 커밋하지 않는다.

### HARNESS-OPS-001-AC-02

실제 임시 Git에서 범위 커밋·인덱스 보존·민감/해시 변경 거부·승인 게이트·멱등성을 검증한다.

## HARNESS-OPS-001-REQ-03 운영

CLI로 auto-commit 설정/상태/실행 결과를 관리하고 App은 같은 명시 명령을 사용한다.
현재 저장소의 기존 변경은 보존하며 새 브랜치에서 검토 가능한 작은 커밋으로 기록한다.

### HARNESS-OPS-001-AC-03

관리 CLI·회귀·SDD·운영 문서와 실제 브랜치/커밋 기록을 확인한다.
