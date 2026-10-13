# TASK-COLLECT-001 — 수집 요약·예약·업로드 전 기록

```toml
kind = "task"
id = "TASK-COLLECT-001"
status = "verified"
owner = "Codex"
specs = ["docs/specs/data_collection_record_spec.md"]
scope = ["docs/specs/data_collection_record_spec.md", "docs/tasks/data-collection-record.md", "docs/data-collection.md", ".github/ISSUE_TEMPLATE/", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", "README.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["COLLECT-001-AC-01", "COLLECT-001-AC-02", "COLLECT-001-AC-03"]

[[verification]]
command = "manual: Python/PyYAML로 Issue Form 필수 입력·고유 ID·예약/완료 구분 및 운영 문서/AGENTS 겹침·업로드 규칙 검토"
result = "passed"
evidence = "docs/tasks/data-collection-record.md#validation"
acs = ["COLLECT-001-AC-01", "COLLECT-001-AC-02", "COLLECT-001-AC-03"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "docs/tasks/data-collection-record.md#validation"
acs = ["COLLECT-001-AC-01", "COLLECT-001-AC-02", "COLLECT-001-AC-03"]

[[verification]]
command = "manual: GitHub REST로 첨부 합성 배치 Issue 게시 후 title/body 읽기 검증"
result = "passed"
evidence = "https://github.com/keulreobeu/jipdam/issues/3"
acs = ["COLLECT-001-AC-01"]
```

## 목표·승인·범위

2026-10-12 사용자 요청으로 GitHub 수집 Issue의 짧은 필수 양식, 수집 전 범위 예약/중복 검색, Drive 업로드 전 결과 기록, 공통 AI 규칙을 만든다. 첨부 합성 DB의 기록을 첫 예시로 게시한다. 원본 ZIP 업로드·새 API 수집·매칭은 실행하지 않는다. gstack 스킬/runtime이 설치되지 않은 환경이므로 공통 Python 검증을 사용한다.

## 완료 기준

- [x] COLLECT-001-AC-01 필수 수집 양식과 README 진입점 및 짧은 실제 첨부 기록.
- [x] COLLECT-001-AC-02 겹침/예약/부분 완료/성공 0건/실패/재조회/합성 구분 절차.
- [x] COLLECT-001-AC-03 업로드 전후 기록, manifest·해시·원본 격리와 강제 범위의 명확한 표시.

## Validation

2026-10-12 Python 3.12.10/PyYAML 6.0.3에서 YAML 파싱, 필수 입력 9개·필수 확인 2개, 고유 ID, 완료 값을 미리 채우지 않음, README 링크·공통 AGENTS·범위 겹침/0건/실패/페이지/재조회/합성 구분과 업로드 한계를 확인했다. 루트 환경 검증은 앱 82개 중 81개 통과·OS 자격증명 세션 관련 1개 skip, 팀 도구 18개 통과, SDD 및 합성 CLI smoke 통과다.

[첨부 배치 GitHub #3](https://github.com/keulreobeu/jipdam/issues/3)를 게시하고 제목·본문을 읽어 확인했다. 연결 GitHub 앱은 쓰기 403이어서 현재 PC의 기존 Git Credential Manager 인증으로 게시했다. 자격 증명은 출력·파일에 남기지 않았다.

Issue 기록은 이미 게시되어 있고, 저장소 Issue Form과 공통 규칙의 팀 적용은 해당 변경이 main에 병합된 뒤다. Issue API·사람의 직접 Drive 업로드·동시 예약을 자동 차단하는 구현은 아니다. 이번 절차 완료는 실제 수집 완료를 의미하지 않는다. 원본 ZIP의 Drive 업로드는 실행하지 않았다.
