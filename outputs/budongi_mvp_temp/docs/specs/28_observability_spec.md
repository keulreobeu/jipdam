# Harness observability — Codex-first shadow measurement

```toml
kind = "spec"
id = "OBS-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-30"
approval_ref = "제공 관측성 v2.3·구축 이력 v2: 이 내용을 프로젝트에 적용 가능한지 확인하고 적용"
```

## 범위

현재 checkout의 managed CLI에 별도 SQLite shadow observer를 추가한다. 제공 문서의
23장 P0 우선순위와 단계 게이트를 적용한다. 문서 안의 명령·전문가 PASS·가격·역사적
PR 상태는 현재 실행 지시나 실측 증거가 아니다. 구독 구매·클라우드 전송·Claude 실행은
포함하지 않는다. 실제 Baseline 전에는 objective 중복 등 최적화 후보를 바꾸지 않는다.

## OBS-001-REQ-01 공식 Usage와 스트리밍

Codex stdout을 제한 길이 줄 단위로 즉시 파싱한다. 각 완료 턴을 별도 내구성 관측으로
남기며 기존 bounded stdout 진단과 분리한다. 입력은 cache 포함, reasoning은 output의
부분집합이다. bool/음수/범위 모순은 invalid, 누락은 NULL이다. Claude 정규화는 오프라인
계약만 제공하며 CLI/OTel을 실행하지 않는다. 검증되지 않은 공급자·버전/누적 의미는
확정 합산하지 않는다. 동일 수치의 서로 다른 턴을 합치지 않는다.

### OBS-001-AC-01

단일/다중 턴, 캐시·추론, 128KiB 초과 출력, 잘못된 JSON·초대형 줄·중단·누락·버전
미확인, 동일 이벤트 재전송/충돌/명시 정정 fixture를 검증한다(M-01~03/06~08/12~15/21).

## OBS-001-REQ-02 불변 원장과 실행 연결

Run/Attempt/Invocation ID를 호출 전에 만들고 모든 재시도/fallback을 보존한다.
실행 프로파일은 코드 SHA/dirty, Task/AC·검증/명시 context 해시, 실행 설정을 봉인한다.
Usage와 lifecycle만 append하며 원문·키·stdout·stderr·tool 인수는 metrics DB에 넣지 않는다.
관측 장애는 기존 실행을 바꾸지 않되 report에서 partial과 정적 오류 코드를 노출한다.
완전성은 공급자가 노출한 턴 범위의 완전성이지 숨은 호출·청구액 보장이 아니다.

### OBS-001-AC-02

실패→재시도·fallback·재시작·승인 전후·DB 장애·불변 행·원천 충돌·프로파일 분리와
기존 상태 전이 회귀를 검증한다(M-04/05/16/18/20/22/24/25).

## OBS-001-REQ-03 품질과 원본 과제 집계

사전 등록·봉인한 suite/item/required task/AC hash/evaluation hash를 사용한다. 분할 Task는
하나의 원본 item으로 센다. 모든 실패 Run/Attempt 토큰을 포함하고, partial/unavailable/
conflict 또는 성공 0건이면 성공당 확정 토큰은 NULL과 이유를 반환한다. 독립 평가의
AC/회귀/보안/scope/review와 실제 승인 모두 필요하며 managed 테스트만으로 성공하지 않는다.
독립 평가 근거는 현재 Run revision에 고정하고 재시도 뒤 재평가한다. 사람 활동은 unknown,
단계별 monotonic duration과 전체 UTC 경과는 구별한다. 비용 회계·1M 지표는 P0 밖이다.

### OBS-001-AC-03

실패 비용 포함·원본 과제 분할 방지·성공0·미시도/blocked 분모·Cloud Usage 결측·작은
단일 과제 및 평가 revision 무효화를 검증한다(M-17/28/31/42~48).

## OBS-001-REQ-04 운영과 후속 게이트

`python -m harness metrics`로 로컬 coverage/report/suite/outcome을 관리한다. 독립 App/Cloud,
Claude/GMS는 미연동 범위를 명시한다. 과거 토큰을 복원·추정하지 않는다. B0 실제 Baseline,
O1 paired 최적화, 네이티브 Cloud 실험, Claude 유료 도입은 각각 실제 증거/추가 권한 게이트다.

### OBS-001-AC-04

CLI·SDD·환경/기존 하네스 회귀와 적용/보류 표·운영 절차·위키 판단을 기록한다. 합성
fixture 결과를 실제 토큰 절감/멀티프로바이더 완성으로 보고하지 않는다.
