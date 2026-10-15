# GMS 웹 연결 확인

2026-10-14 사용자 요청. 계약: [GMS-001](../specs/17_gms_connection_spec.md), 실행: [TASK-GMS-001](../tasks/gms-connection.md).

1. 기존 보관함 화면에 GMS 키 선택·비용이 표시된 확인 버튼·예산 계산기를 추가한다. 등록/교체는 CRED-001을 재사용한다.
2. 서버의 별도 GMS adapter는 고정 endpoint/model/문장과 출력 상한으로 한 번 호출한다. Origin/CSRF와 동시 실행 잠금, 비밀값 비노출·오류 분류를 적용한다.
3. 합성 transport로 인증/쿼터/리다이렉트/타임아웃/불완전 응답과 키 교체를 검사한다. 실제 키/크레딧은 사용자 화면에서만 시험한다.
4. 비용·시간 계산과 무통신 경계를 검사하고 SDD/기존 보관함 회귀검사를 실행한다.

기존 미커밋 rental MVP 변경을 보존한다. GMS를 로컬 LLM endpoint 허용 목록에 추가하지 않으며 추천/수집/DB 경계는 기존 계약을 따른다.
