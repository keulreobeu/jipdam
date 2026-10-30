# TASK-LEGAL-RAG-CORPUS-001 — 별도 RAG 실험용 공식 원문 패키지

```toml
kind = "task"
id = "TASK-LEGAL-RAG-CORPUS-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/24_legal_rag_corpus_spec.md"]
scope = ["outputs/budongi_mvp_temp/.gitignore", "outputs/budongi_mvp_temp/data/raw/legal_rag/", "outputs/budongi_mvp_temp/docs/specs/24_legal_rag_corpus_spec.md", "outputs/budongi_mvp_temp/docs/tasks/legal-rag-source-snapshot-20261021.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/rag-readiness-assessment-20261021.md", "outputs/budongi_mvp_temp/docs/legal-api-access-guide-20261021.md", "docs/sdd/traceability.json"]
acs = ["LEGAL-CORPUS-001-AC-01", "LEGAL-CORPUS-001-AC-02"]
```

## 목적

사용자 요청에 따라 별도 프로젝트에서 RAG를 시험할 수 있도록 법률·표준계약서·보증기관의 공식 원문 자료와 출처 기록을 수집한다. 현행 집담 canonical/serving DB나 제품 인덱스에 연결하지 않는다. Jira 추적은 [KAN-13](https://kwulreobeu.atlassian.net/browse/KAN-13), 출처별 예약·결과 기록은 GitHub [수집 #24](https://github.com/keulreobeu/jipdam/issues/24)~[수집 #28](https://github.com/keulreobeu/jipdam/issues/28)을 사용한다.

## 범위와 경계

- Law.go 공개 현행 법령, 법무부 표준임대차계약서, HUG/HF/SGI 기본 반환보증 안내 자료를 별도 `data/raw/legal_rag/` 아래에 보존한다. HUG 다상품 공공데이터 묶음을 다룰 때는 사용자 승인 범위인 `전세보증금반환보증` 약관만 분리 보존하고 다른 상품 약관은 코퍼스에 넣지 않는다.
- 법제처 공식 공개 연혁 탭에서 주택임대차보호법 29개, 시행령 32개 항목(현행본 포함)의 순번·시행일·공포번호/일자·개정구분을 확인해 [연혁 인벤토리](../../data/raw/legal_rag/law_20261021_v1/history_inventory.md)에 보존했다. 이 인벤토리는 버전 식별 메타데이터이며 과거 시행본 원문 본문은 아직 수집하지 않았다. 법률 API/OC 호출도 하지 않았다. [수집 #24](https://github.com/keulreobeu/jipdam/issues/24)에 출처·범위·패키지 해시를 기록했다.
- 각 파일의 출처 URL, 문서/상품 버전, 확보 시각·방식, 크기, SHA-256, 확인하지 못한 이용조건과 파싱 상태를 manifest/검수 문서 및 수집 이슈에 기록한다.
- 법제처 API의 OC 인증 호출은 별도 등록·보관함 준비·승인 전까지 사용하지 않는다. OC 키 값이나 완성 호출 URL을 저장소·Jira·GitHub에 쓰지 않는다.
- 별도 RAG 프로젝트에서 평가한 뒤 집담 적용 계약을 다시 결정한다. 색인·답변 제공·제품 변경·Drive 업로드는 이 Task의 완료를 의미하지 않는다.

## 현재 증거

- 법제처 현행 주택임대차보호법·시행령 2건은 공개 본문 페이지에서 확보했다. 원문 API/OC는 호출하지 않았다. [현행 스냅샷 ZIP](../../data/raw/legal_rag/legal_rag_law_current_20261021_v1.zip).
- 기관 자료 ZIP에는 MOJ/HUG/HF 문서와 SGI 개인임차인용 페이지의 브라우저 렌더링 텍스트 및 HUG 실험 추출본이 있다. 2026-10-21 추가로 HUG 공식 약관 페이지가 연결한 PDF를 받아 기존 HWP와 함께 보존했다. 패키지 manifest에는 16개 원본/파생 자료의 URL/방식/시각/bytes/hash가 기록돼 있다. [기관 자료 ZIP](../../data/raw/legal_rag/legal_rag_institutional_20261021_v1.zip).
- 2026-10-21 06:52 UTC 법무부 표준계약서 공식 게시물을 재확인했다. 한국어 원본게시용 PDF는 2023-10-06 개정본이며 게시물은 공공누리 1유형(출처표시)을 표시한다. 2026-03-10 영어·중국어·베트남어 번역 게시물이 별도로 있으나 수집 #25 예약에서 번역본은 제외되어 있어 내려받지 않았다. 최신성 확인과 예약 경계를 manifest/검수기록에 남겼다.
- 2026-10-21 HUG 공식 약관 페이지가 현재 링크하는 PDF를 확인했다. PDF 첫 페이지 개정이력의 마지막 날짜는 2024-04-26이며 저장된 HWP와 같은 개정일이다. 이는 관찰 시점에 공식 페이지가 연결한 판본을 확인한 것이며, 향후 미게시 변경이 없음을 뜻하지 않는다. HWP 텍스트 변환은 남아 있다.
- 2026-10-21 06:59 UTC 해당 공식 연결 PDF를 내려받았다: `HUG/return_guarantee_terms_2024-04-26_official_linked.pdf`, 361,217 bytes, SHA-256 `b9fbc51d41866da4b1ebb7dd7be5d410d37597f373c8d815cdc66a54e4c5d41c`. PDF는 A4 가로 5장에 인쇄 페이지 1~10을 2-up으로 담고 있다. 표지와 마지막 장에서 약관명·개정이력·2024-04-26 부칙(2024-05-03 시행)을 시각 확인했고 PDF 텍스트 추출에서 제1~21조 제목이 HWP 실험 추출과 일치했다. 조문 전체의 시각 대조는 미완료다.
- 2026-10-21 07:10 UTC HUG 공식 PDF와 HWP 파생 텍스트의 조문 1~21을 분절해 한글/영문/숫자 기준 유사도를 비교했다. 1~5조 및 7~21조는 0.996~1.000, 6조는 PDF 2단 페이지의 각주가 조항 사이에 배치된 추출 순서 영향으로 0.898이었다. 인쇄 시트 2의 좌·우 칼럼에서 6조 첫 항/다음 항의 이어짐을 시각 확인했다. 이는 텍스트 추출 대응 검수이며 전체 시각 대조나 법률 해석 검수는 아니다. HWP 파생본은 `experimental_unverified`를 유지하고 색인하지 않는다.
- 2026-10-21 07:14 UTC HF 현재 상품 페이지(일반전세지킴보증)가 연결하는 `일반전세지킴보증 약관 및 유의사항` PDF를 확인했다. 24페이지 PDF 표지는 `2025. 2. 6 기준`을 표시하며, 기존 HF 공식 2024-12-09 게시물 첨부 PDF와 표제·기준일이 같았다. 두 다운로드 경로는 다르므로 바이트 동일성은 확인하지 않았고 기존 공식 첨부본을 보존·인용한다. 최신 링크 확인과 한계는 manifest/validation에 기록한다.
- HUG HWP에 대해 실험적 본문 추출본을 만들었다. 원본 OLE/압축 본문에서 167개 PARA_TEXT 레코드, 제1~21조 제목, 부칙을 확인했고 공식 연결 PDF의 첫 페이지 표제/개정일과 대조했다. 제어 정보로 보이는 CJK 28자는 제거했다. 기준 파서·조문 전체 시각 대조는 없으므로 파생본은 `experimental_unverified`이며 색인에 사용할 수 없다.
- SGI 최초 탐색 URL은 다른 보험상품으로 확인돼 제외했다. 올바른 개인임차인용 경로에서 상품·주요내용·유의사항·FAQ 7건을 확인했으며, 확보 텍스트는 서버 원본 HTML이 아닌 파생 캡처다. 약관 RD뷰어/다운로드는 사용하지 않았다.
- 2026-10-21 사용자가 SGI 보안 프로그램 설치를 알린 뒤 올바른 SGI 상품 페이지(`전세금반환보증보험`, `CCPPRD040301F01`)를 다시 열었다. `상품공시`에서 `전세금반환보증보험(개인임차인용)`의 판매기간 `2025.04.01 ~`을 선택해 공식 공시의 보험약관 다운로드 항목을 확인했다. 공시 링크를 눌렀지만 현재 Codex 인앱 브라우저에서는 문서·새 탭·다운로드 파일을 확인하지 못했다. 현재 작업 세션에는 SGI 보안 프로그램과 연결된 실제 브라우저가 노출되지 않아 설치 프로그램의 연동 여부나 파일 형식을 직접 확인할 수 없다. 공식 대체 경로 후보와 미확보 상태를 manifest/검수기록에 반영했다.
- 2026-10-21 06:46:57 UTC 재시도: SGI 공식 상품 페이지의 보험약관 메뉴를 열고 개인임차인용 링크를 선택했으나 메뉴만 닫히고 RD 뷰어·문서·새 탭·다운로드는 나타나지 않았다. 현재 세션에서 확인 가능한 브라우저는 Codex 인앱 브라우저뿐이므로 사용자가 설치한 Windows 보안 프로그램과 실제 브라우저의 연동은 확인할 수 없다. 실패 시도는 원문 수집으로 계산하지 않았다.
- 2026-10-21 06:56:44 UTC 재확인: SGI 상품공시에서 `전세금반환보증보험(개인임차인용)` 및 판매기간 `2025.04.01 ~`을 선택해 `보험약관` 다운로드 항목이 결과 행에 표시되는 것을 확인했다. 해당 항목을 눌렀지만 페이지가 그대로였고 PDF/뷰어/새 탭/다운로드 파일은 확인되지 않았다. 현재 세션의 브라우저 목록은 격리된 Codex 인앱 브라우저뿐이며, 사용자가 설치한 프로그램과 실제 브라우저 연동 여부는 검증하지 못했다. 원문 미수집 기록이며 manifest·validation 및 수집 #28에 반영한다.
- 2026-10-21 07:04:48 UTC 재시도: SGI 공식 상품 페이지에서 공시 ID `2026-0031`(유효기간 2026-01-16~2027-01-15)을 확인하고 RD-viewer/download 메뉴에서 개인임차인용 약관을 선택했다. PDF·RD 뷰어·새 탭·로컬 파일은 나타나지 않았고, 브라우저 자산 비교에서 `tooltip_close.png` 외 새 문서 자원은 확인되지 않았다. 이는 인앱 브라우저의 다운로드 handoff 실패 기록이며 사용자의 별도 브라우저에서 설치 프로그램이 작동하는지에 대한 판단은 아니다. manifest·validation에 재시도를 기록한다.
- ZIP 구조/CRC, manifest의 각 자료 파일 bytes/SHA-256 대조, 두 패키지 해시를 확인했다. HUG PDF/HWP 조문 대조, HF 현행 링크 확인 및 SGI 재시도 기록을 반영한 최종 기관 패키지는 1,594,659 bytes, SHA-256 `2a4b424fa32ac4c2a4d6f7697326404e4f0793f8d5b1795491985990b5671848`.

- 2026-10-21 07:26 UTC 공공데이터포털의 `주택도시보증공사_보증상품별 약관_20260930`(dataset 15040864, 목록상 이용허락범위 제한 없음) 묶음을 내려받아 이름이 정확히 일치하는 `전세보증금반환보증약관(2024년도 4월 26일 개정).hwpx` 1건만 추출했다. 다른 상품 약관과 묶음 전체는 코퍼스에서 제외했다. 선택 파일 63,223 bytes, SHA-256 `5ae51165e54dda95e98f7ef6cc761a9e363dc18fea883c6886e913c6f7176e74`; 묶음 원본 3,367,809 bytes, SHA-256 `0efdd19a1165833d01e925ea4514402bfe86ef810fb4cbfdc8e9c8b912227f5c`(원본 묶음은 패키지에 보존하지 않음).
- 선택 HWPX는 내부 ZIP 11항목/섹션 XML 2개가 정상이며 제1~21조를 포함한다. 기존 HWP 추출 텍스트와 정규화 조문 문자열이 모두 일치했다. 기존 공식 연결 PDF 추출과의 유사도는 0.759~1.000이며 제3·6·11조의 낮은 값은 2단/각주 읽기 순서 영향 가능성이 있어 전체 시각 대조는 계속 남긴다. 법률 해석 검수와 색인은 하지 않았다. 포털 자료의 2026 등록일은 대상 약관의 개정일을 의미하지 않으며 해당 약관은 기존 2024-04-26 판본과 같다.
- 기존 불변 v1 ZIP을 보존하고 HWPX·manifest·검수기록을 포함한 기관 패키지 v2를 만들었다: 1,653,554 bytes, SHA-256 `6b774e764bb9ca159efbe40be9ba4dccef2abc54d6584f9150722b7f6eaf918b`, 19 entries. [기관 자료 패키지 v2](../../data/raw/legal_rag/legal_rag_institutional_20261021_v2.zip).

- 2026-10-22 08:51 KST SGI 대체 공식 경로를 확인했다. SGI 도메인 검색 결과의 상품 페이지는 개인/법인 상품을 함께 설명했으나 공식 약관 PDF 직접 링크는 확인되지 않았다. 정확한 개인임차인용 약관 버전/파일은 여전히 미확보이며, 제3자 복사본은 공식 원문이 아니어서 제외했다. 시도와 미수집 상태를 manifest/validation 및 수집 #28에 기록했다.
- 이 확인기록을 반영한 최신 불변 기관 패키지 v3는 19 entries, 1,653,936 bytes, SHA-256 `3faa2de3df12fc939ef500e9879e0fc2f4e751db992689c8dc1682e8d403be7c`다. [기관 자료 패키지 v3](../../data/raw/legal_rag/legal_rag_institutional_20261021_v3.zip). v1/v2는 보존한다.

## 2026-10-21 Law.go 작업 보류

사용자 요청에 따라 Law.go 관련 추가 수집, 법령 API 인증 호출, 과거 시행본 본문·부칙 확보를 보류한다. 기존 공개 현행본 2건과 공개 연혁 목록 메타데이터는 보존한다. 법제처 포털의 실제 인증키 발급/신청 상태는 이 작업에서 확인하지 않았으므로 미발급으로 단정하지 않는다. 재개 전 포털 상태·사용범위 확인, credential ID의 로컬 암호화 보관함 준비, 별도 수집 예약 및 호출 보안 점검을 확인한다.

## 남은 확인

- 연혁 인벤토리에 표시된 과거 시행본 본문·부칙 수집(별도 범위 예약 및 API 안전한 보관함 credential 또는 승인된 공개 원문 경로 확인 후), 조문별 원문 대조와 문서별 인용 위치 검수.
- HUG 실험 추출본의 기준 파서 대조 및 조문별 원문/페이지 검수.
- HUG/HF/SGI 원문 재사용·재배포 조건 확인.
- SGI 공식 PDF는 확보했다. 사용자 지시에 따라 OCR은 사용하지 않고 원본 PDF 텍스트 레이어를 직접 읽었다(19쪽, 28,081자); HF 텍스트 레이어가 깨지는 경우에는 원본 페이지를 직접 렌더해 읽었다. 전체 법률 검수와 SGI/HUG/HF 문서별 재사용 조건 확인은 남았다. 다른 상품 경로의 검색 결과를 개인임차인용 근거로 대체하지 않는다.
- 별도 RAG 실험 코퍼스 이용범위·문서 갱신 기준을 정하고 외부 실험 저장소에서 검색·인용·거부 동작을 평가한다.

위 항목이 남아 있으므로 Task와 KAN-13은 진행 중이다. 합성 또는 문서 준비 결과를 제품 성능으로 표시하지 않는다.

## 완료 기준

- [x] LEGAL-CORPUS-001-AC-01 기관별 출처와 수집/캡처 방식·시각·bytes·SHA-256을 manifest에 기록하고 원본과 파생 추출물을 구분한다.
- [x] LEGAL-CORPUS-001-AC-02 별도 raw 패키지 격리를 유지하고 API 키, 색인, canonical/serving 반영, 원문 공유 업로드를 수행하지 않는다.

기본 저장소 검증은 위 완료 기준과 Task 추적만 확인한다. HUG/SGI 문서의 원문 사람 대조·이용조건 등 남은 검수 항목 때문에 Task 상태는 `in_progress`다.

[[verification]]
command = "Read-only ZIP CRC/entries and manifest bytes/SHA-256 comparison; inspect separation boundaries"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/legal-rag-source-snapshot-20261021.md#현재-증거"
acs = ["LEGAL-CORPUS-001-AC-01", "LEGAL-CORPUS-001-AC-02"]







- 2026-10-22 이용조건 범위를 재확인했다. HF 공식 HOUSTAT 이용약관은 HOUSTAT 통계/API/데이터파일에 대해 저작자·출처 표시 조건의 자유이용을 안내하지만 별도 수집한 HF 보증 약관·청구안내 PDF에는 적용된다고 확인하지 않았다. HUG 공공데이터포털 dataset 15040864의 이용허락범위 제한 없음 표시는 해당 항목에만 한정한다. 법무부 공공누리 1유형 표시는 수집한 표준계약서 게시물에 한정하며, SGI 재사용 조건은 미확정이다. 외부 RAG 인덱싱·배포 전 각 보증 문서별 이용조건 확인이 남는다. 해당 근거를 manifest/validation에 기록했다. 최신 기관 패키지 v4: 1,657,285 bytes, SHA-256 `01a149d949be57e134710c0461aceb6a0046895fe6715ac72a50b87ad4d48431`; v1~v3 불변 보존.

- 2026-10-22 SGI 설치 상태를 공식 보안프로그램 안내 화면에서 확인했다. 화면은 Windows 10 64-bit/Chrome 155 환경과 VeraPort, AnySign, TouchEn nxFirewall, TouchEn nxKey의 설치됨 상태를 표시했다. 메인 이동은 “잘못된 대리점 URL입니다” 오류를 냈고, 공식 상품/공시 경로는 이 Codex 인앱 브라우저에서 빈 접근성 영역만 보여 약관 PDF를 받지 못했다. 이는 해당 브라우저에서 프로그램 설치 상태가 탐지된 것을 확인한 것이며 약관 원문 확보를 뜻하지 않는다. [공식 SGI 보안 안내](https://chang.sgica.co.kr/biz/ccp/index.html?p=CCPCST050301F01). 시도와 한계를 manifest/validation에 기록했다. 최신 패키지 v5: 1,657,882 bytes, SHA-256 `4277cbd28790f223637602aecf4a0a2b8a437e71393614ac44f51e7669e747e1`.

- 2026-10-22 SGI 공식 `www.sgic.co.kr` 상품공시에서 개인임차인용·판매기간 `2025.04.01 ~`를 선택하고 `보험약관` 다운로드를 성공했다. PDF 291,808 bytes, SHA-256 `83d5a837ee42b5e6ea0429bfd8e3407c3078e01a1fbe5caad9d7f737778c9e8f`, 19쪽, 비암호화. 표지에 `전세금반환보증보험(개인임차인용) 보험약관 / 2025. 4. 1. 개정`, 목차에서 보통약관 제1~24조를 확인했고 p.18에는 보험료분할납입 특별약관이 있다. pypdf/pdfplumber 모두 한글 추출이 깨져 색인용 추출본은 만들지 않았다. OCR/기준 파서·전체 조문 페이지 검수와 문서별 이용조건 확인은 남는다. SGI 약관의 상품·판본 및 직접 다운로드 경로와 미확보 상태를 해소했으며, 시도/해시/한계를 manifest·validation에 기록했다. 최신 기관 패키지 v6: 1,886,002 bytes, SHA-256 `3e7093e974ce7ff74a2aebcbb8227bfd14f9fca6b9c28181b2b0086804ebf932`.

- 2026-10-22 OCR 후속 검수: 로컬 Poppler 180dpi 렌더 + EasyOCR ko/en CPU(모델 다운로드 비활성)로 19쪽 실험 추출본을 만들었다. 23,113자/52,807 bytes, SHA-256 `6d7585a02218e63b1b5f0de1bfe2271e8f2ed927e09df12471dd2be5a4f2fb61`. 한글 음절과 조항 숫자 오인식이 있어 legal evidence/색인에 사용하지 않고 검수 대기 상태로 둔다. PDF p.2-3을 시각 대조하여 보통약관이 제1~35조임을 확인했다. 이전 v6 기록의 제1~24조는 p.2에서 본 일부였으므로 본 목차 전체 수로 정정한다. 보험료분할납입 및 신용카드이용보험료납입 특별약관도 확인했다. 최신 패키지 v7: 1,902,577 bytes, SHA-256 `6df84bbef1a7037946c2bcaaf3bf1c6ef8023a3a73f554905a7419aa2ae5b840`.

- 2026-10-22 HF 현행 링크 실파일 대조: 공식 일반전세지킴보증 페이지에서 `sub02_sub02_05_01_20260619.pdf`를 내려받아 기존 공식 첨부본과 비교했다. 양쪽 모두 780,865 bytes, SHA-256 `310cc723db1682c5e35b61e4ee7c1a6b12070041862060eefb3f133d003fe9e1`로 바이트 단위 동일하다. 표지는 `2025. 2. 6 기준`이므로 파일명/메타데이터의 2026 표시는 신규 약관 판본 근거가 아니다. 중복 파일은 추가하지 않고 현재 상품 페이지 링크를 manifest에 보강했다. 최신 기관 패키지 v8: 22 entries, 1,902,952 bytes, SHA-256 `486ed0135ad815fe7671d4a3f9b2aa084328896ca799aba27206d1cb07453f1a`.

- 2026-10-22 HUG 공식 연결 PDF 5쪽을 130 dpi로 렌더해 인쇄 페이지 1~10을 모두 시각 점검했다. 개정이력·제1~21조·부칙이 읽히며 제3조(인쇄 p.2~3), 제6조(p.5~6·정의 상자), 제11조(p.6~7)의 페이지 이어짐이 추출 순서 차이를 설명할 수 있다. 누락된 절은 시각상 발견하지 못했다. 조문 전체의 문자 단위 대조·법률 검수는 아니므로 HWP/HWPX 파생 텍스트는 experimental_unverified, 색인 미승인으로 유지한다. 최신 기관 패키지 v9: 22 entries, 1,903,667 bytes, SHA-256 `f6ad8a3c023ec5436eba1801351d6543b78b3d3630ac42b00fbce7fdaaf19937`.

- HUG 전세보증금반환 FAQ 보관본의 페이지 표시를 오프라인 확인했다. 공식 EUC-KR HTML 4개가 각각 1/4, 2/4, 3/4, 4/4로 표시되어 캡처 당시 해당 FAQ 목록의 전체 번호 페이지를 보존한 것으로 확인했다. 다른 FAQ 구역 및 캡처 이후 갱신 여부까지 의미하지 않는다. 결과는 manifest/validation에 기록했다.
기관 자료 패키지 v10: 1,904,041 bytes, SHA-256 `b259325c36317d82ff5551e5516c74ab9347c679804c06830633d4bcbd08483c`.

- 기록 정정: v9/v10 ZIP에 00:30:00Z/00:32:00Z라는 실제 확인시각보다 뒤인 UTC 시각을 잘못 기재했다. 해당 시각을 근거로 쓰지 않는다. HUG PDF 레이아웃과 FAQ 1/4~4/4를 2026-10-22 00:18:21 UTC에 다시 확인해 현재 manifest를 정정했고, 불변 v9/v10을 대체하는 v11을 만들었다.
- SGI 공식 PDF 목차 p.2~3을 시각 확인해 보통약관 제1~35조, 보험료 적립률 별표 p.14, 보험료 분할납입 특별약관 p.15, 신용카드 보험료 납입 특별약관 p.16을 확인했다. 같은 목차의 EasyOCR에는 `제스조`, `제IO조` 등 조문번호/표제 오인이 보여 OCR은 검수 전 자료로 유지하고 색인하지 않는다. 이는 문서 구조 확인이지 본문 OCR 정확성 또는 법률 의미 검수는 아니다.
기관 자료 패키지 v11: 1,904,728 bytes, SHA-256 `4bdd96e7c3c1eb63eeef2ac96ddb3b427a6b761afcbafe053355f4dbfbc8aa8b`. v9/v10은 기록된 UTC시각 두 건의 오류가 있어 current manifest 대신 사용하지 않는다.

- 2026-10-22 SGI 공식 약관 목차 파생본을 추가했다. 원본 PDF p.2~3을 260dpi 렌더로 직접 읽어 보통약관 1~35조의 표제/인쇄 페이지, 적립이율 별표 p.14, 분할납입 특약 p.15, 신용카드 납입 특약 p.16을 수기 확인했다. OCR 오류를 그대로 고친 본문은 아니며 목차만 `verified_toc_only`로 기록했다. 원본 PDF 19쪽 중 TOC가 매핑하는 것은 인쇄 p.1~16이며 PDF 뷰어 p.17~19 내용은 추정하지 않는다. 파생본: `SGI/return_guarantee_terms_personal_2025-04-01_verified_toc.md` (2964 bytes, SHA-256 `261d6d7a13bda1249dee0e2d66d3cd153af7cae34fbba6a52d27a1f464c1f6be`). 본문 OCR 전체 검수와 이용조건은 미완료.
기관 자료 패키지 v12: 1,906,803 bytes, SHA-256 `ff1b6b777e0af22b4ed20ccbee8d84ce857845c9e8a503de57c51c8e6333e9c3`; 23 ZIP entries, manifest data files 20.

- v12 수집 산출물 검증: `python -X utf8 scripts/check_sdd.py` 통과(21 features, 106 acceptance criteria, 43 tasks, 118 changed paths). 기관 ZIP 23 entries/CRC 정상, manifest 20개 자료 파일의 bytes/SHA-256 및 ZIP payload 일치 확인. 검사 실행 시각 2026-10-22 00:24 UTC.
- SGI PDF 마지막 뷰어 페이지 17~19를 220dpi로 렌더해 시각 확인했다. 각각 인쇄 페이지 14(적립이율 별표), 15(보험료분할납입 특약 제1~2조), 16(신용카드 보험료 납입 특약 제1~4조)로 목차와 일치하며 19개 PDF 뷰어 페이지가 모두 목차에 매핑된다. 이전 파생 목차의 “viewer p.17~19는 미매핑” 문구는 부정확해 수정했다. 페이지 매핑 확인만 완료했으며 OCR 본문 검수·법률 검수·이용조건은 남아 있다.
- 기관 자료 패키지 v13: 23 ZIP entries, 1,907,374 bytes, SHA-256 `cdade161178a04d6f01e2f2f7db5555354a738038370398dc0ba1e3dbd109c2b`. v1~v12는 불변 보존하며 v13이 현재 SGI 목차/페이지 매핑 기록을 반영한다.
- 공식 이용조건 재확인: HF 일반 상품 페이지 footer의 `COPYRIGHT© KOREA HOUSING FINANCE CORPORATION / All Rights Reserved`는 보관 중인 약관 PDF에 대한 개별 이용허락이 아니다. HUG 공식 안내는 HUG가 저작재산권 전부를 보유한 자료에 한해 저작권법 제24조의2에 따라 자유이용 가능하다고 설명하지만, 수집한 각 약관 첨부물의 권리 보유 여부는 확인하지 못했다. SGI 공식 도메인에서 재사용/재배포 조건을 찾지 못했으나 검색 결과 부재를 권리 부재로 해석하지 않는다. 각 보증 문서의 외부 색인·재배포 권리는 모두 미확정으로 유지한다.
- 이 권리 확인을 반영한 기관 패키지 v14: 23 ZIP entries, 1,908,364 bytes, SHA-256 `4d4c6c1795496eb162f48cce5ac59a0d1f2d019981a38f0fd1285223cc30c93f`; v1~v13은 불변 보존한다.
- HUG 공공데이터포털 항목을 다시 열어 정확한 이용허락 범위를 대조했다. 데이터셋 `주택도시보증공사_보증상품별 약관_20260930`는 HWPX 형식, 단일 행, `이용허락범위 제한 없음`으로 표시된다. 보관한 2024-04-26 전세보증금반환보증 HWPX(63,223 bytes, SHA-256 `5ae51165e54dda95e98f7ef6cc761a9e363dc18fea883c6886e913c6f7176e74`)는 다운로드 묶음의 유일한 일치 항목이다. 이 표시는 해당 포털 자료 항목에만 기록하며, 별도로 받은 HUG HWP/PDF·웹페이지나 다른 상품 약관으로 확장하지 않는다.
- 항목별 포털 라이선스 표시를 반영한 기관 패키지 v15: 23 ZIP entries, 1,909,156 bytes, SHA-256 `3174bf2be861fd8f9a6ef8b8bfecdd3fa550814fb806c95bc8736029431777bb`; v1~v14는 불변 보존한다.
- 포털 HWPX의 XML 본문을 재추출했다. 내부 ZIP은 11항목이며 본문은 `Contents/section0.xml` 1개이고 `Contents/header.xml`은 별도다. 첫 추출 시 XML 텍스트 요소에 포함된 `<hp:fwSpace/>` 뒤의 tail 텍스트가 빠지는 문제를 확인해 `itertext()`로 보존하도록 수정했다. 결과 파생본은 8,814자/21개 조문 표제이며, HWP 기반 기존 실험 추출본과 정규화 본문을 대조한 결과 제1~21조 모두 정확히 일치했다. 이는 두 파생 추출 간 일치만 확인한 것이므로 PDF와의 조문별 문자 대조·법률 검수·색인 승인은 아니다. 파생본 `HUG/return_guarantee_terms_2024-04-26_datagokr_experimental.txt`, 21,282 bytes, SHA-256 `9c9e3be87b02371a98e8645e0bda9648a9baec9e7c02f0bc047031f0cfb85c72`는 계속 실험/색인 금지 상태다. 검수문서의 과거 “섹션 XML 2개/8,861자” 기재를 현재 ZIP에 맞게 정정했다.
- HWPX XML 파생본과 검수 정정을 반영한 기관 패키지 v17: 24 ZIP entries, 1,916,272 bytes, SHA-256 `c3ed8eb317ba07d479680160c39faf7cf7944d6506cefcb5ccf4d351cfa440c8`; v1~v16은 불변 보존한다.

- 2026-10-22 00:36:39 UTC HUG 공식 연결 PDF 인쇄 p.2~7을 확대 재확인하고 제3·6·11조의 HWPX 파생본과 PDF 텍스트 추출 결과를 비교했다. 정규화 문자 유사도는 각각 0.8285/0.8984/0.9592였고, 차이는 제3조 정의 상자 누락·제6조 추출 순서로 이동, 페이지 번호 삽입과 일치했다. PDF 화면에서는 제3조 정의가 p.3, 제6조 정의 상자가 p.4, 제11조 본문이 p.6~7로 이어지는 것을 확인했다. 이 결과는 PDF 추출기 읽기 순서 차이를 설명하지만 조문 전체 문자 일치나 법률 검수 증거는 아니므로 HUG 파생본은 계속 실험/색인 금지다. manifest·검수기록에 반영하고 기관 패키지 v18을 생성·대조한다.
- 기관 자료 패키지 v18: 24 entries, 1,916,890 bytes, SHA-256 `748be4bb54d9ff6360a49f1cd054a78bb799a46721612e67ec47fbcc4db05963`. ZIP CRC와 manifest 21개 자료 파일의 bytes/SHA-256/압축 payload를 대조 통과했으며 v1~v17은 불변 보존한다.

- 2026-10-22 00:40:42 UTC SGI PDF viewer p.4를 pypdfium2 300dpi로 렌더해 기존 180dpi EasyOCR와 비교했다. ko/en CPU EasyOCR를 문단/줄 단위로 각각 실행했지만 한글 음절 오인식은 남고 문단 모드에서 제1조 제10·11호를 합치며 줄 모드에서는 행 끝이 잘렸다. 시험용 산출물은 폐기하고 기존 OCR도 실험/색인 금지 상태로 유지한다. 추가 시도와 한계를 manifest/검수기록에 추가하고 기관 패키지 v19를 만든다.
- 기관 자료 패키지 v19: 24 entries, 1,917,367 bytes, SHA-256 `d5668fdb90dfddf59f16a6d5e776ef372de2757e0853a53b7e05c00c80819b4b`. ZIP CRC와 manifest 21개 자료 파일의 bytes/SHA-256/압축 payload 및 현재 수집 폴더 동일성을 대조 통과했다. v1~v18은 보존한다.


- 2026-10-22 user-provided HUG historical PDF added to the isolated corpus: `HUG/return_guarantee_terms_2017-10-23_user_provided.pdf` (245969 bytes; SHA-256 `f384fc411cb76a6b8c6faa5cbc2944e0838724c64efe672858e0530e1b2ca156`; 7 pages). The supplied PDF lists amendments through 2017-10-23 and Articles 1-19; direct native text extraction and page review used no OCR. It is retained as an unverified-provenance historical comparison only; official publication URL/current validity and reuse rights remain unconfirmed. The current-linked HUG 2024-04-26 terms are unchanged. Recorded in HUG collection issue #27 as a user-provided supplement.

- 기관 자료 패키지 v20 (`outputs/budongi_mvp_temp/data/raw/legal_rag/legal_rag_institutional_20261021_v20.zip`): 25 entries, 2,106,408 bytes, SHA-256 `61f37d0d6966302464685977a14e312733df2cb33a80bddc0693846e71b6fee3`. ZIP CRC와 manifest 22개 자료의 크기/SHA-256/압축 payload 대조 통과. `python -X utf8 scripts/check_sdd.py` 통과. v20은 새 HUG 2017 사용자 제공 약관을 포함한다. v1~v19는 불변 보존한다.


- HUG historical provenance search (2026-10-22T03:17:21Z): official-domain search located later HUG-hosted terms PDF `https://www.khug.or.kr/hug/homepage_file_upload/jeonse_guarantee_terms_20200712_rev.pdf`. Its indexed revision history includes 2017-10-23 and later amendments/cleanup through 2020-07-21. This supports that HUG published a terms series with that revision date, but does not establish that the supplied 7-page PDF is the exact official copy. No remote PDF was downloaded; exact origin and reuse rights remain open.


- 2026-10-22 official HUG 2020 historical terms PDF collected from `https://www.khug.or.kr/hug/homepage_file_upload/jeonse_guarantee_terms_20200712_rev.pdf`: HTTP 200, application/pdf, 328504 bytes, SHA-256 `507d6cc5ab8a5ef7ef034375746455eb2e3c2def995518bb66b9dd7b8deec117`, 9 pages. Its cover revision history ends 2020-07-21; native text layer directly exposes Articles 1-21, with no OCR. The official-linked 2024-04-26 file also has Articles 1-21; the user-provided 2017-10-23 file has Articles 1-19. This verifies document structure/revision metadata only, not article equivalence or legal interpretation. Item-specific reuse rights remain unresolved. Institutional package v22 is recorded below.


- 기관 자료 패키지 v22 (`outputs/budongi_mvp_temp/data/raw/legal_rag/legal_rag_institutional_20261021_v22.zip`): 26 entries, 2,365,819 bytes, SHA-256 `f96badcfecc8c0ac419e739288c599940540046f4d5bf7272038199e0a0365fb`. ZIP CRC와 manifest 자료 파일 23개의 크기/SHA-256/압축 payload 대조 통과. v1~v21은 불변 보존한다.


## 사용자 제공 PDF 직접 재열람 및 OCR 파생본 제외 — 2026-10-22T03:22:28Z

사용자가 “OCR을 왜하고 있어 이 PDF로 다시읽어”라고 지시해 SGI/HUG/HF 첨부 원본을 직접 다시 확인했다. 새 읽기 과정에서는 OCR을 사용하지 않았다. SGI 2025-04-01 PDF(19쪽)는 pypdf native text layer에서 한글 28,081자를 읽었고, HUG 2017-10-23 제공 PDF(7쪽)는 5,425자 및 제1~19조 표제를 확인했다. HF 제공 PDF(24쪽)는 추출 글자가 깨져 오프라인 렌더 페이지 1~24를 직접 확인했다. HF 표지 기준일은 2025-02-06이다. 세 파일의 SHA-256은 기존 corpus 원문과 일치해 중복 수집하지 않았다.

기존 실험 OCR 텍스트는 법적 근거나 색인으로 승인하지 않았으며, 사용자의 지시에 맞춰 현재 active corpus의 파일·manifest 기록에서 제외했다. 기존 v1~v22 ZIP은 불변 이력으로 보존하고 새 기관 패키지 v23을 현재 패키지로 지정한다. 과거 OCR 실험이 수행됐다는 기록은 validation 이력에 남겼다. 이번 직접 열람은 법률 해석·문서 이용허락·전체 조문 등가 검수를 뜻하지 않는다. Law.go API/과거 시행본 보류, 제품 색인/DB 반영 및 Drive 업로드 경계는 그대로 유지한다.

기관 자료 패키지 v23: 25 entries, 2,350,832 bytes, SHA-256 `8459841b96c40dc2df17848cee9e29808927a934eff4e89336d649b0907be9b5`. active manifest 22개 자료를 대상으로 ZIP CRC와 각 파일의 bytes/SHA-256 및 압축 payload 대조를 통과했다. 이전 v1~v22 패키지는 불변 이력으로 보존한다.


## 보증기관 문서 이용조건 공식 출처 재확인 — 2026-10-22T03:25:43Z

HUG 안내는 저작권법 제24조의2 자유이용을 주택도시기금이 저작재산권 전부를 보유한 자료에 한정한다. 수집한 약관 첨부물별 권리 보유 여부는 미확인이다. HF 공식 일반전세지킴보증 상품 페이지의 All Rights Reserved 표시는 개별 약관 PDF의 이용허락이 아니며, HOUSTAT 통계/API 이용약관도 보증약관/청구 안내 자료에 확대 적용하지 않는다. SGI 공식 상품·공시 경로에서 개인임차인용 약관 PDF의 개별 재사용 조건을 확인하지 못했으며, 이를 허가 또는 금지의 증거로 해석하지 않는다. 기존 공공데이터포털 제한 없음 표시는 정확히 일치한 HUG 2024-04-26 HWPX 항목에만 적용한다. 출처 URL과 범위는 active manifest에 반영했고 새 약관 원문은 내려받지 않았다.

기관 자료 패키지 v24: 25 entries, 2,351,389 bytes, SHA-256 `8ccfb85429697c321681f1761fb863ec4c74fa64aa8d18e112c2cd812efbdecb`. CRC 정상, manifest 자료 22개의 bytes/SHA-256/payload 대조 통과; active corpus에 OCR 파생본 없음. v1~v23 불변 보존.


## SGI PDF 원문 텍스트 레이어 파생본 — 2026-10-22T03:27:00Z

별도 RAG 실험의 원문 위치 추적을 위해 SGI 2025-04-01 PDF에 내장된 text layer만 pypdf 6.16.2로 추출하고 각 PDF 페이지 구분자를 유지했다. 19쪽에서 28,081자를 얻었으며 replacement character는 없다. OCR/정규화는 쓰지 않았다. 파생 텍스트는 전문 사람 대조·법률 검수가 끝나지 않아 `native_text_extraction_unreviewed_not_for_indexing`이다. 원본 PDF가 정본이며, HF 깨진 글자는 OCR로 보충하지 않았다. 문서별 이용조건도 계속 미확정이다.

기관 자료 패키지 v25: 26 entries, 2,365,960 bytes, SHA-256 `21f46c0daac7c1fbd3cf9398ac1879be92ec5f44719abb8619adbbfa2f0584a3`. CRC 정상, manifest 자료 23개의 bytes/SHA-256/payload 대조 통과. OCR 파생본은 제외하고 SGI PDF native text layer 파생본을 페이지 구분과 함께 포함했으며 검수 전/색인 불가 상태다.


## SGI 추출 문자 수 정정 — 2026-10-22T03:28:00Z

원본 SGI PDF에서 pypdf 6.16.2로 페이지별 추출 문자 수를 재합산한 값은 28,081이다. 앞선 28,099 기록은 오기여서 current manifest와 validation에서 정정했고, 직전 패키지 v25는 해당 오기가 포함돼 현재본에서 제외한다.

기관 자료 패키지 v26: 26 entries, 2,366,107 bytes, SHA-256 `bd46cf0473a96276efb847f15a11b41db268935dad7f6107d6d322820f6fbcd5`. CRC 정상, manifest 자료 23개의 bytes/SHA-256/payload 대조 통과. v25의 SGI 추출 문자 수 오류를 정정한 현재본이며, v25는 잘못된 추출 문자 수가 포함된 이전 산출물로 superseded 처리한다.


2026-10-22 HUG PDF 재열람 문자 수 정정: 사용자 제공 원본( SHA-256 `f384fc411cb76a6b8c6faa5cbc2944e0838724c64efe672858e0530e1b2ca156` )을 pypdf 6.16.2로 다시 읽어 7쪽 합계 5,425자를 확인했다. 기존 재열람 기록의 5,431자는 오기다. manifest와 본 Task의 현재 재열람 요약을 수정하고, 이전 패키지 v26은 이 오기가 담긴 과거 불변 스냅샷으로 남긴다.

기관 자료 패키지 v27: 26 entries, 2,366,254 bytes, SHA-256 `437622b6da413fc1d23b94f99651bed8f59154e0d3c5f1f0329b648a0b9291a8`. HUG 2017 제공 PDF의 직접 재열람 문자 수 5,425로 manifest/검수 기록을 정정한 최신본이다. ZIP CRC 및 manifest 23개 자료의 크기/SHA-256/압축 payload 대조 통과. v1~v26은 불변 이력으로 보존한다.


## HUG 약관 판본 간 추출 대조표 — 2026-10-22

HUG 약관 PDF 2017 제공본·2020 공식 호스팅본·2024 공식 연결본의 내장 텍스트층을 직접 비교했다. 2017 제공본은 제1~19조, 2020·2024 공식본은 제1~21조이며, 2017과 후속본의 제목/번호 체계는 달라 자동 조문 대응을 하지 않았다. 2020↔2024 같은 번호의 조문 제목 1~21은 일치했다. 추출 기반 문자 유사도에서 제6·7·8·9·10·14·21조가 0.95 미만이어서 원문 시각 대조 후보로 표시했다. 2024 PDF의 2-up 레이아웃 때문에 낮은 점수는 추출 순서 영향일 수 있으며 실제 개정 차이로 확정하지 않는다. 비교표는 실험/색인 금지/법률 검수 아님 상태다: `HUG/revision_comparison_2020-07-21_to_2024-04-26_experimental.md`.

기관 자료 패키지 v28: 27 entries, 2,369,011 bytes, SHA-256 `96755b537f953449b186e4a87e8e0cc1b47098b8f24da868aec0c05ca33eb5ba`. manifest 24개 자료를 대상으로 ZIP CRC 및 bytes/SHA-256/압축 payload 대조를 통과했다. v1~v27은 불변 이력으로 보존한다. HUG/HF/SGI 문서별 재사용 권리와 전문 원문 대조, 별도 RAG 실험은 여전히 남아 있다.


2026-10-22 직접 원문 페이지 대조 보강: HUG 2020 PDF 인쇄 p.3–6과 2024 2-up PDF의 인쇄 p.3–6을 렌더해 OCR 없이 비교했다. 2020본 제8조 제3항의 서면 보완요청과 2024본의 서면 또는 전자문서 보완요청/정의상자, 제9조의 항 구조 변경, 2024본 제10조 제3항의 심사 완료 후 3개월 내 명도 문구를 확인했다. 이는 선택 조항의 텍스트 차이만 확인한 것이며 법률상 효과 판단이나 전체 조문 검수는 아니다. 제14·21조 및 2017판과의 조문 대응은 남았다. 상세: [HUG 판본 비교표](../../data/raw/legal_rag/institutional_20261021_v1/HUG/revision_comparison_2020-07-21_to_2024-04-26_experimental.md).

기관 자료 패키지 v29: 27 entries, 2,370,164 bytes, SHA-256 `bf3156feb62c70f3170b004afa73825d7ade3a8e2b73e5b7771e2f8b9759e2e9`. manifest 24개 자료의 ZIP CRC, bytes/SHA-256/압축 payload 대사를 통과했다. v1~v28 불변 보존.


2026-10-22 제14·21조 및 부칙 직접 대조: 2020/2024 PDF 내장 텍스트와 해당 인쇄 페이지를 OCR 없이 확인했다. 제14조는 제1·2항 구조가 유사하나 2024본에 `[사기 또는 허위]` 정의 상자가 추가됐다. 제21조 본문 제1·2항 및 제1~5호는 대체로 유사하며, 낮은 자동 유사도에는 뒤따르는 부칙 및 2-up 추출 순서가 섞인 영향이 있다. 2024 PDF에는 2020-12-04에 더해 2022-12-29 및 2024-04-26 부칙(각 2022-12-30, 2024-05-03 시행)이 보인다. 정밀 문언·법률 검수는 남는다. 상세 비교표와 manifest/validation을 갱신했다.

기관 자료 패키지 v30: 27 entries, 2,370,930 bytes, SHA-256 `78e324c46df28c1038c00c6a5b0eac5b32d641fad9c28a9437f1a8814a24442f`. ZIP CRC와 manifest 24개 자료의 bytes/SHA-256/압축 payload 대사를 통과했다. v1~v29는 불변 이력으로 보존한다.


## SGI 이용조건 공식 경로 재확인 — 2026-10-22

SGI 공식 소비자포털 검색 결과에서 `© Seoul Guarantee Insurance. All rights reserved.` 일반 사이트 저작권 문구와 `이용약관` 링크를 확인했다. 웹 리더로 약관 링크 내용을 열 수 없었고, 개인임차인용 보증 약관 PDF의 개별 이용허락은 찾지 못했다. 일반 footer는 첨부 PDF의 허가 또는 금지를 뜻하지 않으므로 SGI PDF의 색인/재배포 조건은 계속 미확정으로 기록했다. 이 확인에서는 새 문서 파일을 수집하지 않았다.

기관 자료 패키지 v31: 27 entries, 2,371,341 bytes, SHA-256 `56ef48380c86752d1e517c98faa6bd7f9775fee5b8b0ee77690012137afc4901`. 최신 SGI 이용조건 탐색기록을 반영했으며 ZIP CRC와 manifest 24개 자료의 bytes/SHA-256/압축 payload 대사를 통과했다. v1~v30 불변 보존.


2026-10-22 SGI 인용 위치 점검: OCR 없이 pypdf 6.16.2 native PDF text layer에서 목차 36개 보통약관 조문 표제를 본문 표제/인쇄 쪽수와 대조해 36/36 일치, 불일치 0건을 확인했다(제25조의2 포함). PDF viewer page는 인쇄 쪽수+3이며, 부록·특별약관은 인쇄 p.14-16 = viewer p.17-19로 매핑된다. 이는 검색 인용 위치 메타데이터 검증이지 본문 전체 교정·법률 검수·색인/재배포 승인에 해당하지 않는다. 상세 매핑은 `SGI/return_guarantee_terms_personal_2025-04-01_verified_toc.md`에 반영했다.

기관 자료 패키지 v32: 27 entries, 2,372,023 bytes, SHA-256 `360759a0dca28191b816158255f6343c9be81696b499e9a4afe5ac536435eca1`. SGI 인용 위치 검증을 반영했으며 ZIP CRC와 manifest 24개 파일의 bytes/SHA-256/압축 payload 대사를 통과했다. v1~v31 불변 보존.

기관 자료 패키지 v33: 28 entries, 2,374,920 bytes, SHA-256 `d589504582b76c258aa023a111245a136d77256b5ba11488d404412bae6c1f32`. HF 약관·유의사항 24쪽의 수기 페이지 위치표를 추가했다. ZIP CRC와 manifest 25개 자료의 bytes/SHA-256/압축 payload 대사를 통과했으며 v1~v32는 불변 이력으로 보존한다. 전체 본문 법률 검수·문서별 이용조건·별도 RAG 평가가 남아 Task는 진행 중이다.

2026-10-22 HUG 2017 사용자 제공 PDF의 공식 원본 경로를 HUG 공식 도메인에서 제목·개정일 기준으로 재검색했다. 공식 HUG 호스팅 2020-07-21 판본의 개정이력에 2017-10-23이 확인되지만 정확히 일치하는 2017 PDF/게시물을 찾지 못했다. 이는 개정일 계보를 뒷받침할 뿐 제공본의 공식 provenance·파일 동일성·재사용 권리를 증명하지 않는다. 원문은 기존 사용자 제공 파일로 유지하고 `source_url=null`, 미검증 provenance 상태를 보존했다. 새 원문 다운로드는 하지 않았다.

기관 자료 패키지 v34: 28 entries, 2,375,354 bytes, SHA-256 `cb27a848e577556055596924888b54631d0bbdf5c64c33714a3edcffae18ff34`. HUG 2017 provenance 재검색 결과를 manifest/validation에 반영했다. ZIP CRC와 manifest 25개 자료의 bytes/SHA-256/압축 payload 대사를 통과했고 v1~v33은 불변 이력으로 보존한다.

2026-10-22 API 준비 안내를 현재 corpus 상태와 맞췄다. 법령 v2·기관 v34 경로, 보증기관 원문 확보 현황, user-provided HUG 2017 provenance 제한, Law.go API/history hold를 문서 상단에 명시하고 10월 21일 최초 수집 문장을 역사 기록으로 구분했다. 별도 RAG 색인·제품 DB·Drive 반영은 없다.

## 법제처 현행 공개 법령 재사용 조건 재확인 — 2026-10-22

법제처 국가법령정보 공동활용의 [공식 이용안내](https://open.law.go.kr/LSO/information/guide.do)를 다시 확인했다. 안내는 법령정보를 영리 목적을 포함해 자유롭게 활용할 수 있다고 하고, 출처를 법제처 국가법령정보센터로 표시하도록 요구하며 위조·변조 및 타 기관 자료로 오인시키는 제공을 금지한다. 공개 안내에는 이용조건 위반·제3자 권리 침해 등 서비스 제한 사유도 적혀 있다. 이 정책 기록은 현재 확보된 두 법령 원문을 위한 출처/이용 metadata이며 법률 검수나 인증 API 승인과는 별개다.

공동활용 안내 페이지는 데이터 활용 승인 후 사용과 승인 심의 절차를 설명하고, 회원가입 신청 화면은 OPEN API 자동승인을 안내한다. 실제 신청·승인 상태는 확인하지 않았고 OC/API 호출도 하지 않았다. 사용자의 Law.go 보류 지시는 그대로 유지한다. manifest/validation에 관찰 시각과 상충해 보이는 신청 안내의 한계를 기록했다.

현행 법령 로컬 snapshot의 현재 패키지 v2는 7 entries, 109,397 bytes, SHA-256 `27e4c63efb8d9088b5e31c7a11fd56c386ea66240ccfddf8b169e809d0b5f420`이다. 원문 HTML bytes는 바뀌지 않았으며 이용조건 근거를 manifest/validation에 추가한 버전이다. CRC와 manifest 파일 hash/payload를 확인했다. 기존 v1 ZIP은 불변 이력이다.


## HF 약관·유의사항 수기 페이지 위치표 — 2026-10-22

사용자가 제공한 `sub02_sub02_05_01_20260619.pdf`와 보존 PDF는 780,865 bytes, SHA-256 `310cc723db1682c5e35b61e4ee7c1a6b12070041862060eefb3f133d003fe9e1`로 동일하다. PDF 페이지 1-24를 렌더링해 확인하고, p.2 목차와 p.13-23 약관 조문 표제를 수기로 페이지 위치표에 기록했다. p.12는 약관 표지이고 제1조 본문은 p.13부터 시작한다. 텍스트층은 읽지 않았으며 OCR도 사용하지 않았다. 파생 파일 `HF/general_jeonse_protection_terms_2025-02-06_verified_locator.md`는 인용 위치 메타데이터일 뿐 전체 본문 교정·법률 검수·색인 승인·재배포 허가가 아니며, HF 문서별 이용조건 확인은 남아 있다.


## 2026-10-22 별도 RAG 실험 후보 묶음

보유 원문 가운데 이용조건이 확인된 것만 별도 프로젝트에 넘길 수 있도록 원본 전용 후보 ZIP을 만들었다. 포함 항목은 법제처 현행 주택임대차보호법/시행령 본문 HTML 2건, 법무부 2023-10-06 주택임대차 표준계약서 원본게시용 PDF(KOGL 제1유형), data.go.kr dataset 15040864의 HUG 2024-04-26 전세보증금반환보증약관 HWPX 1건이다. HUG의 이용허락범위 제한 없음 표기는 선택한 이 데이터셋 항목에만 적용한다.

- 후보 패키지: data/raw/legal_rag/legal_rag_test_candidate_20261022_v1.zip
- 크기 263,084 bytes, SHA-256 93f6dd3479ad5b43df56347266126feeeaad1576032df13de116a15e98a68883; ZIP CRC와 원문 4건의 manifest bytes/SHA-256/payload 대사를 통과했다.
- 2026-10-22 공식 페이지에서 현재 법령 판본이 보존본과 일치하고, 법무부 한국어 표준계약서가 2023-10-06 개정본이며 KOGL 제1유형임을 확인했다. 2026-03 번역 게시물은 이번 한국어 원문 범위에서 제외한다. HUG dataset은 2026-09-30 등록, 연간 갱신, 차기 예정 2027-09-30으로 표시된다.
- 원본 파일만 포함한다. OCR·파생 텍스트·색인·제품 DB·Drive 업로드는 없다. 이 후보 묶음은 별도 프로젝트에 전달하기 위한 raw source package로, 법률 해석/전문 검수/검색 품질 평가와 집담 적용 승인을 대신하지 않는다.
- HUG 2017 사용자 제공 PDF, HUG 공식 PDF/HWP 복사본, HF/SGI 보증 문서는 출처 또는 문서별 이용조건이 별도 확인되어야 하므로 이 후보 묶음에서 제외했다. Law.go API와 과거 시행본 본문은 사용자 지시대로 계속 보류한다.

무결성 세부는 data/raw/legal_rag/test_candidate_20261022_v1/validation.md 및 build_receipt.json을 따른다.

## 2026-10-22 별도 프로젝트의 검색 미리보기

사용자가 지정한 선행 실험 프로젝트 `C:\Users\SSAFY\Desktop\RAG_project`에 후보 ZIP을 복사하고, 별도 `output/legal-rag-candidate/` 경로와 `legalcandidate` namespace로 원문 구조화·인용 위치·검색 동작만 시험했다. 기존 공원/영화 데이터 영역과 집담 DB 경로는 별도다.

- 후보 원문 4건(현행 법령 HTML 2, 표준계약서 PDF 1, 권리표시가 해당 dataset 항목에 한정된 HUG HWPX 1), 구조 섹션 104개, 청크 120개.
- 원문 SHA-256, 문서 판본, 출처 URL, 이용조건, 조문 또는 PDF 페이지를 metadata에 보존했다. HTML DOM, PDF 텍스트층, HWPX XML만 사용했고 OCR/API 호출/LLM 생성은 없었다.
- 현재는 `UNVERIFIED` / `TEXT_EXTRACTED_UNREVIEWED`다. 기본 KnowledgeScope가 문서를 차단함을 검증했다. 검색 수치는 별도 고정 원본-hash preview scope에서만 계산했으며 기본/제품 검색의 성공을 뜻하지 않는다.
- 5개 수기 질의의 기대 섹션 Top-5: BM25 5/5 (MRR .8667), test-hash Vector 5/5 (.5067), Hybrid/RRF 5/5 (.8500). 이 질의는 사람 검수 Golden이 아니고 test-hash는 의미 임베딩이 아니다.
- 재실행은 120개 모두 변경 0건/삭제 0건. 프로젝트 전체 회귀검사 86건과 별도 importer 검사 3건 통과.
- 외부 URL·Law.go API·OC·생성 모델은 호출하지 않았고 제품 인덱스/DB는 연결하지 않았다. Ollama는 이 RAG 프로젝트 환경에 설치되어 있지 않고 GMS 임베딩은 지원되지 않아 의미검색 비교는 미수행이다.

재현·세부 보고서: `C:\Users\SSAFY\Desktop\RAG_project\docs\legal-rag-experiment-20261022.md`; 결과 JSON은 같은 프로젝트 `output/legal-rag-candidate/evaluation-report.json`이다. SGI/HF 약관, HUG 2017 제공본의 문서별 권리/공식 출처 상태는 그대로 미확정이라 색인에 넣지 않았다. 법률 검수·240개 사람 검수 Golden·실제 한국어 임베딩 비교 후에야 실험 인수 여부를 판단한다. KAN-13은 진행 중 유지.

### HF 공식 현재 링크 교차 확인 — 2026-10-22

공식 HF `일반전세지킴보증` 페이지가 연결한 약관·유의사항 PDF의 제목과 24쪽 구성을 확인했다. 저장된 `sub02_sub02_05_01_20260619.pdf`와 사용자 제공 파일은 780,865 bytes, SHA-256 `310cc723db1682c5e35b61e4ee7c1a6b12070041862060eefb3f133d003fe9e1`로 일치하며, PDF 표지의 기준일은 2025-02-06, 파일 메타데이터 수정일은 2026-06-16이다. 이는 현재 공식 링크가 가리키는 파일의 출처 및 내용 기준일을 구분해 기록한 것이며, 2026년 개정판이라는 증거나 문서별 재사용 허락은 아니다. OCR 없이 확인했고 새 파일을 내려받지 않았다. HF 개별 약관 이용조건과 전체 본문 검수는 계속 남는다.

## 2026-10-26 checkout 검증 참조 복구

TASK-ENV-003/KAN-24: Git 제외 raw 검증 파일을 새 checkout의 SDD 필수 경로로 요구하지 않도록 위 현재 증거의 과거 관찰 기록으로 연결했다. 원본 복원·재수집·재검증 또는 미완료 법률 검수의 승격은 수행하지 않았다.

## 2026-10-28 기존 Drive 백업 복원

KAN-13 후속으로 2026-10-23 사용자의 Drive 원문 백업을 인증된 연결로 내려받았다. ZIP 73,078,731바이트와 SHA-256 `9fb1febbcae518464561841696873d55bd909ce13048df7aad3a05d81211bf01`이 백업의 별도 SHA256SUMS와 일치하고 ZIP CRC가 정상이다. 기존 `data/raw/legal_rag`가 없는 것을 확인한 뒤 80개 파일을 복원했으며 ZIP 내부 원본과 복원 파일의 SHA-256 전수 비교에서 차이 0건이다.

별도 RAG 실험 후보 ZIP `legal_rag_test_candidate_20261022_v1.zip`은 기존 기록의 263,084바이트와 SHA-256 `93f6dd3479ad5b43df56347266126feeeaad1576032df13de116a15e98a68883`이 일치한다. ZIP CRC 및 manifest 원문 4개의 바이트 수·SHA-256이 일치하고, 각 원문이 복원된 개별 원본과도 일치한다. 이는 과거 보관 자료의 무결성 검증이며 현재 법령 효력·이용권·법률 검수·시맨틱 평가나 제품 색인 완료를 뜻하지 않는다. 새 외부 원문 수집·API/키 호출·업로드는 하지 않았다. KAN-13은 원문별 효력·권리·검수 등 미완료로 유지한다.

복원 후 `data/raw/legal_rag/`가 Git 무시 규칙에 빠져 있음을 발견해 제품 `.gitignore`에 이 경로만 추가했다. 원문·ZIP은 추적하지 않는다.

위키 maintenance/catalog/search 후 복원·Git 제외 범위의 `KAN13-RAW-RESTORE-20261028` 이벤트는 SKIP/execution_log/DONE/nonblocking이다. Jira [기록](https://kwulreobeu.atlassian.net/browse/KAN-13?focusedCommentId=10102)의 receipt를 남겼으며 새 위키 페이지는 없다. 이 판단은 전체 KAN-13 완료가 아니다.


### 2026-10-28 보관 패키지 추가 무결성 대조

복원된 기관 v34 ZIP은 기존 기록의 2,375,354바이트와 SHA-256 `cb27a848e577556055596924888b54631d0bbdf5c64c33714a3edcffae18ff34`에 일치하고, 28개 항목의 CRC가 정상이다. manifest의 자료 25개 모두 ZIP 내부 bytes/SHA-256에 일치하며, 복원된 개별 파일과 ZIP payload의 SHA-256도 25/25 일치한다. 나머지 3개는 manifest, validation, download-results 메타데이터다.

법령 v2 ZIP도 기존 109,397바이트와 SHA-256 `27e4c63efb8d9088b5e31c7a11fd56c386ea66240ccfddf8b169e809d0b5f420`에 일치하고, 7개 항목의 CRC가 정상이다. manifest의 5개 자료는 ZIP 내부 bytes/SHA-256과 복원된 개별 파일 해시가 5/5 일치한다. 이 중 `history_inventory.md`는 원문이 아니라 이력 목록의 파생 기록이다. 두 대조는 과거 스냅샷 보존 상태에 대한 것이며 현행 효력, 원문 전체 교정, 문서별 권리 또는 법률 검수를 증명하지 않는다. KAN-13의 기존 미완료 요건과 보류 상태는 그대로다.


### 연관 위키 검토 상태 — 2026-10-28

기존 데이터 카탈로그 위키 `WIKI-E162D573DBB6F1CD`의 대기 항목은 `shared_document_requires_review`다. 기록된 다섯 소스 중 `data-catalog.md`와 세 기존 validation 파일은 해시가 일치하지만 이 Task 원본은 10월 28일 복원·검증 기록 추가 후 기존 source hash와 다르다. 연관 위키의 근거가 변경된 상태로 남아 있으므로 이전 ACTIVE 표기를 현재 검증·원격 동기화 성공으로 간주하지 않는다. 공유 문서의 기존 내용과 원격 수정 여부 검토 전 덮어쓰지 않았으며 리뷰 대기 항목을 유지한다.


위 대기 사유 정밀 확인: 공유 문서 import의 본문 해시와 렌더는 일치하며 현재 근거 검사는 `source_changed`를 반환한다. 큐의 `shared_document_requires_review`는 여러 오류를 포괄하는 일반 사유이므로 원래 큐가 생성된 당시 원인을 단정하지 않는다. Confluence stable ID 검색으로 [원격 문서 589825](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/589825/WIKI-E162D573DBB6F1CD)를 확인했고 현재 revision 1 / 2026-10-22 작성 기준의 기존 수동 표가 있다. 로컬 요약 Markdown과 원격 표는 본문 형태가 다르므로 단순 재게시하거나 기존 표를 덮어쓰지 않았다. 소스 변경분 및 원격 문맥을 합쳐 재검토하는 작업과 기존 review 대기는 남아 있다.


하네스 검토 경로 확인: 현재 CLI의 `wiki retry`는 `markdown/wiki/jira`만 지정할 수 있고 `wiki receipt`는 `wiki/jira` outbox만 수락한다. 기존 review 채널 항목을 공식 CLI로 완료 처리하는 명령은 확인되지 않았다. 공유 문서가 현재 원본 해시와 불일치할 때는 카탈로그 import가 거부되므로, DB를 직접 수정하거나 원격 문서/로컬 메타데이터를 강제로 덮어쓰지 않았다. 관련 문서의 안전한 검토·재가져오기 및 review 항목 해소 계약이 별도 확인될 때까지 큐를 유지한다.
