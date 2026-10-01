# SDD 운영 Spec

```toml
kind = "spec"
id = "SDD-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "keulreobeu"
approved_at = "2026-10-01"
approval_ref = "사용자의 PLEASE IMPLEMENT THIS PLAN 요청과 D1~D8 선택"
```

## 범위

팀 공통 SDD 운영·템플릿·검사·PR와 required-fact 평가 시범 적용. 세 AI 도구에 같은 계약을 제공한다. 제품 동작·CLI·평가 형식·실데이터 상태는 변경하지 않는다.

## SDD-001-REQ-01 계약과 영구 작업 기록

입력은 Markdown Spec/Task와 TOML 메타데이터, JSON 추적 원장이다. 출력은 운영 규약·네 템플릿과 추적 가능한 Task다. 제품 요구는 사용자가 확정하며 담당자는 구현·검증·완료 기록을 책임진다.

### SDD-001-AC-01 상태·ID·메타데이터

중복 ID, 미지원 상태, 필수 필드 누락·오류를 거부한다. baseline과 실제 데이터 평가 미완료를 구분한다.

## SDD-001-REQ-02 요구와 검증의 추적

원장은 요구→AC→실제 테스트 또는 수동 검증을 연결한다. 검사는 네트워크·추가 패키지 없이 Python 3.11 이상에서 실행한다.

### SDD-001-AC-02 참조와 검증 연결

없는 문서·요구·AC·테스트 클래스/메서드, 빈 AC 검증 연결, 저장소 밖 경로를 거부한다.

## SDD-001-REQ-03 변경과 완료 증거

코드·설정·계약 변경은 같은 변경에서 갱신한 Task의 scope에 포함되어야 한다. 단순 설명 문서는 면제한다. 검증 실패는 종료 코드 1과 원인을 반환한다.

### SDD-001-AC-03 Task 연결과 면제

Task 누락·범위 누락·미갱신 Task를 거부한다. README 설명 수정은 허용하고 규칙·Spec·템플릿 문서에는 면제를 적용하지 않는다.

### SDD-001-AC-04 verified 증거

미체크 AC, 명령·passed 결과·증거·AC 연결 누락을 거부한다. 실패 기록만으로 verified가 되지 않는다.

## SDD-001-REQ-04 재현 가능한 팀 검증과 병합

기본 검증에 SDD 검사를 통합하고 GitHub PR/push 변경 범위를 확인한다. 현 CI matrix를 유지하고 사람 승인 리뷰 수는 강제하지 않는다.

### SDD-001-AC-05 기본 검증과 시범 기능

Windows/Linux CI에서 SDD 검사·기존 테스트·보완 테스트·합성 CLI가 성공하고 required-fact AC가 실제 테스트에 연결된다.

### SDD-001-AC-06 main 필수 검사

네 가지 `model-free-checks` 조합을 main 필수 검사로 적용한 뒤 실제 설정을 읽어 확인한다. 리뷰 승인 수는 0이고 관리자도 필수 검사를 따른다.
