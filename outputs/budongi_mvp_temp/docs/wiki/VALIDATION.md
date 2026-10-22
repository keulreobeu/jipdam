# WIKI-001 검증 — 2026-10-22

Task: TASK-WIKI-001 / Jira KAN-19. 사용자 정책 v1.0 및 팀원 접근 요청 추가 지시를 기준으로 검증했다.

## 실행 결과

| 검사 | 실제 결과 |
|---|---|
| 위키 정책 acceptance | 최종26개 통과. 첨부15개 시나리오, 실제 Git worktree hook/완료 차단, 경로/수동 편집/버전 충돌, 권한 요청, 원격 해시 정규화, 팀원 clone 복원 및 미검증 수동 변경 차단 포함 |
| 제품 전체 회귀 | 제한 밖 실행320개 통과. 합성 HTTP·Windows 보관함 검증 포함 |
| 팀 도구 회귀 | 27개 통과 |
| 기존 managed 하네스 | 13개 통과 |
| 기존 로컬 자동커밋 | 9개 통과 |
| SDD 구조/브랜치 | 구현 중 전체 구조 및 origin/main 비교 통과. 마지막 관련 범위 검사는 아래 완료 기록에 기재 |
| 전체 verify_environment 진입점 | 최초 sandbox 실행은 로컬 socket/OS 저장소 권한 제한. 제한 밖 재시도는 다른 작업의 tmp/pdfs/sgi_tail_20261022/tail-17.png에 Task 연결이 없어 SDD 단계 중단. 해당 파일을 수정/삭제하거나 검사 규칙을 완화하지 않았다 |
| GMS 초안 | 기존 runner의 로컬8786 설정 서버 미연결로 차단. 유료 생성/키 우회 없음 |

명령: `python -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -p test_wiki_lifecycle.py -q`.
제품 전체는 제품 폴더에서 `python -X utf8 -m unittest discover -s tests -q`, 팀 검사는 루트에서 같은 명령이다.
샌드박스 임시 폴더 ACL 제한을 피하기 위해 TEMP/TMP를 작업의 Git 제외 임시 경로로 지정했다.

## 실제 위키 생명주기

- 사용자 지정 Confluence space65816/homepage65913을 공식 도구로 조회했다. 별도 공간 지침은 없었다.
- 기존 페이지 목록 전체(2개)를 확인한 뒤 집담 부모360449와 정책 원문131074를 만들었다.
- 운영 WIKI-5BA57A2BFC7C9BCA와 권한 안내 WIKI-B6B7A1FAAA4FA55B를 CREATE하여
  로컬 ACTIVE/외부 SYNC_PENDING을 확인했다. 실제 Confluence65959/425985 게시 후 full HTML을
  다시 읽고 URL·버전·정규화 SHA-256 receipt를 기록했다.
- read-back 해시 절차 추가로 원본 운영 문서가 바뀌자 같은 운영 ID를 UPDATE하여 revision2를
  게시했다. 원격 기존 HTML과 버전이 이전 read-back과 같은지 확인하고 snapshotToken을 사용했다.
- root index360449는 policy/operation/team-access 링크 및 권한 요청 안내를 포함하는 version2다.
- 팀원 실제 접근 권한을 부여했다고 주장하지 않는다. 권한이 없으면 본인 계정으로 보기/작성/편집을
  공간 관리자에게 요청하도록 안내하며 초안과 SYNC_PENDING을 유지한다.
- 팀원이 runtime DB 없이 저장소의 공유 Markdown만 받아도 무결성/근거 검사를 통과한 기존
  문서 ID를 복원하고 LINK_EXISTING으로 연결했다. 수동 변경된 복사본은 ACTIVE에서 제외했다.
- 저장소 source/문서 ID/내용/버전과 정제된 근거만 게시했다. 원본 DB·실데이터·키는 보내지 않았다.

## 운영 경계

로컬 worker 시작/매시간 점검과 작업 검증 hook, Codex·Claude의 작업 완료 절차를 연결했다.
외부 전송은 공식 host connector를 쓰는 agent가 outbox를 처리한다. agent/worker가 미실행인 동안
자동으로 원격 이벤트를 관찰하는 OS 서비스·웹훅을 설치한 것은 아니다. 제품 부동산 RAG에는 연결하지 않았다.
문서화 정확도·실제 문제 해결 성공률 등 라벨이 없는 지표는 unmeasured로 유지한다.

## 완료 기록

관련 변경25개에 대한 SDD 검사 통과:21 features/106 AC/43 tasks. 다른 작업 변경99개는
이 작업의 검증 범위에 포함하지 않았다. Jira KAN-19 댓글10043에 CREATE2/UPDATE1과
검증·게시 URL·전체 검사 한계를 기록했고 각 outbox에 실제 댓글 receipt를 연결한다.
최종 검색에서 ACTIVE2개(운영revision2/권한안내revision2)를 확인했다. 외부 동기화 대기는
성공 receipt 처리 후0건이다. local codex/wiki-lifecycle-20261022 브랜치에서 변경을 관리한다.
