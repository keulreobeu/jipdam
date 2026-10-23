# LEGAL-CORPUS-001 — 별도 RAG 실험용 공식 문서 스냅샷

```toml
kind = "spec"
id = "LEGAL-CORPUS-001"
status = "baseline"
owner = "Codex"
revision = 1
```

## 현재 동작과 범위

집담 요청에 따라 별도 RAG 실험 후보인 임대차 법령, 표준계약서, 보증기관 상품 안내 원문을 로컬 원천 패키지로 준비한다. 자료는 `data/raw/legal_rag/`에 보관하고 canonical·serving DB 및 제품 인덱스와 분리한다. RAG 실험은 별도 프로젝트에서 수행하며, 실험 결과 인수 후 집담 적용 여부와 계약을 다시 정한다.

이 스냅샷 준비는 키 발급·사용, 원문 재배포 권리, 법률 해석, 가입 적격 판정, 제품 통합을 대신 승인하지 않는다. 화면에서 추출한 렌더링 텍스트는 원본 파일 바이트와 구분한다. 출처와 재사용 조건이 불명확하면 그 상태를 manifest에 남기고 검수 전 색인하지 않는다.

## LEGAL-CORPUS-001-REQ-01 출처·버전 계보

### LEGAL-CORPUS-001-AC-01

패키지의 모든 자료는 출처 URL, 확보 방식·시각, 크기와 SHA-256을 manifest에 남긴다. 파생 렌더링 텍스트는 원본 HTML/PDF와 구별되고, 버전·이용조건·파싱 한계를 확인하지 못했으면 그 상태를 명시한다.

## LEGAL-CORPUS-001-REQ-02 실험 코퍼스 분리

### LEGAL-CORPUS-001-AC-02

준비 산출물은 별도 RAG raw 폴더에만 보존한다. 이 작업으로 API 비밀값이나 완성 인증 URL, 법령/기관 문서 색인, canonical·serving DB 갱신, Drive·GitHub 원문 파일 업로드가 발생하지 않는다. 별도 RAG 검색·인용 평가 후 집담 통합 범위를 정한다.

현재 자료별 확보/검수 상태는 [TASK-LEGAL-RAG-CORPUS-001](../tasks/legal-rag-source-snapshot-20261021.md)에서 추적한다.
