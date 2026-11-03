# KAN-42 검증 기록

2026-11-03, source base70f7408b316ddf5e3d5bdd8f4c59eff8311069c9.
현재 구현/전체 회귀 후 독립 검토·최종 게시 전이다. 로컬 AC는 통과했지만 전체 완료로 승격하지 않는다.
기존 사용자 DB/GMS 원장은 열거나 재설정하지 않는다.
실제 모델/API 호출·새 벤치마크는 없고 fixture 숫자는 합성이다. 개발/검토의 공식 usage는
관측되지 않았으면 unknown이며 Python 기능의 invoke0과 혼동하지 않는다.
위키 판단/최종 검증·동기화 상태는 실제 실행 후 같은 Task/Jira에 기록한다.

## 개별 실행

- `unittest discover -s outputs/budongi_mvp_temp/tests -p test_input_check.py -q`:18개/5.724초 OK.
- `... -p test_lean_metrics.py -q`:10개/4.044초 OK(후속 fixture 표현 변경은 전체 검증으로 재확인).
- `... -p test_observability.py -q`:32개/20.090초 OK.
- `... -p test_harness_operations.py -q`:9개/7.309초 OK(후속 URL token 검사는 전체 회귀로 재확인).
- `scripts/check_sdd.py --base origin/main`:22feature/126AC/45Task passed.
- 실제 `harness input-check`의 source syntax/registry JSON smoke:PASS, approval_granted=false,
  checker가 시작한 provider invocation0.

고정 offline fixture version=`input-check-boundaries-v1`, 정의(test_input_check.py) SHA256
`ad93dc6173b1e6504a108b77467b7fa8ab3554f98b3802da4024a176d9175749`.
이는 새로운 경계 fixture의 식별자이며 실제 생성 모델 benchmark를 실행/봉인했다는 뜻이 아니다.
과거 다섯 결함 유형은 긴 CSV 숫자의 text 보존/JSON 정수 제한, null request 거부,
refresh token URL 차단, 깊은 JSON, JSONL U+2028 보존으로 재현했다.

처음 0건 unittest는 로컬 Python에서 종료코드5/NO TESTS RAN으로 나타났다. 코드0만 검사하지 않고
관측 test count를 먼저 분류하도록 수정해 UNKNOWN을 검증했다. repair→수동재개 시험은 처음에
기존 max_attempts2 한도에 막혔다. 실제 한도는 유지하고 별도 합성 작업을3회로 선언해 검증했다.
이 중간 실패를 최종 PASS로 소급하지 않는다.

## 전체 회귀

`python -X utf8 scripts/verify_environment.py`: exit0, 제품411개227.322초/팀35개1.930초 OK,
합성 doctor/tool CLI passed. 기존 HANDOFF23/OBS32/GMS·managed·index 보존 회귀를 포함한다.
고정 scope39 파일 scanner passed, SDD22feature/126AC/45Task와 git diff --check passed.
원문 로그는 ignored `.local_runtime/kan42-git/full-verification.log`에만 남기고 Git에 넣지 않는다.
최종 고정 SHA의 독립 검토와 해당 SHA publisher 검증 전에는 이 결과를 원격 최종 합격으로 표시하지 않는다.

Git 전담 helper의 읽기 전용 조합도 검증했다: 기존 root git_lifecycle/git_cli만 fallback load하고
scanner/contracts/isolation은 검증한 KAN-42 source를 사용한다. 130KB 일반 파일 허용,
LLM safe(payload)128KB 거부, annotated secret 차단을 확인했다. 함수 monkeypatch/guard skip은 없다.
원본 root 파일/index와 KAN-41의 source·publisher·승인 WIP artifact를 보존한다.

검토 목적 신규 장문 산출물은0이며 이 기록은 필수 Task/AC 증거다. 로컬 파일 scanner5MB와
LLM safe(payload)128KB를 분리했고 후자는 불변이다. 이 변경의 공개 범위는 고정 source 검사로 확인한다.
위키 판단은 SKIP(기존 Spec/Task/운영 자료 재사용, 별도 장문 게시 요청 없음)이며 원격 sync 성공은 주장하지 않는다.
