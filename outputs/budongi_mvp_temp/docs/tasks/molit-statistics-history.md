# TASK-MOLIT-HISTORY-001 — 거래량 통계 기간 정합 MOLIT 수집

```toml
kind = "task"
id = "TASK-MOLIT-HISTORY-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/12_molit_collection_spec.md", "outputs/budongi_mvp_temp/docs/specs/14_statistics_storage_spec.md", "docs/specs/data_collection_record_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/collection.py", "outputs/budongi_mvp_temp/src/budongi/collection_cli.py", "outputs/budongi_mvp_temp/src/budongi/source_registry.json", "outputs/budongi_mvp_temp/tests/test_collection.py", "outputs/budongi_mvp_temp/docs/specs/12_molit_collection_spec.md", "outputs/budongi_mvp_temp/docs/plans/molit-statistics-history.md", "outputs/budongi_mvp_temp/docs/tasks/molit-statistics-history.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/molit-statistics-history-validation-20261015.md", "outputs/budongi_mvp_temp/AGENTS.md", "AGENTS.md", "docs/data-collection.md", "docs/sdd/traceability.json"]
acs = ["MOLIT-001-AC-02", "MOLIT-001-AC-05", "MOLIT-001-AC-06", "MOLIT-001-AC-07"]

[[verification]]
command = "Owner-reported collection status/build-db/pack verification; SDD metadata migration only, not rerun"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/molit-statistics-history-validation-20261015.md"
acs = ["MOLIT-001-AC-02", "MOLIT-001-AC-05", "MOLIT-001-AC-06", "MOLIT-001-AC-07"]
```

## Approval and scope

2026-10-15 user selected the transaction-volume statistics range `2024-01~2026-08` and Seoul25구. Existing 202510~202608 XML is reused; only missing 202401~202509 is reserved in GitHub #7 and newly collected. No new source type, national expansion, matching, coordinate/facility collection, recommendation linking, or Drive upload is included.

## Acceptance criteria

2026-10-15 SDD 정합 보정(TASK-CLI-HARNESS-001): 메타데이터는 실제 등록된 MOLIT-001 AC를 참조한다.
아래 HISTORY 표시는 이 Task의 세부 체크 항목으로 보존한다. 수집 범위·검증 상태·미완료 조건은 바꾸지 않았다.
AC-02는 재사용/누락 범위, AC-05는 오프라인 DB, AC-06은 ZIP/계보, AC-07은 명시 기간을 검증한다.
이후 원 담당자가 verified 및 실제 수집/재구성/ZIP 검증 기록을 추가했다. 위 verification은
해당 담당자 기록을 등록 Spec ID에 연결하는 메타데이터 이관이며, 하네스 담당자의 신규 수집/재구성 실행이 아니다.

- [x] MOLIT-001-AC-02 기존 담당자의 원본 재사용/전체 완료 검증 기록
- [x] MOLIT-001-AC-05 기존 담당자의 오프라인 DB/계보 검증 기록
- [x] MOLIT-001-AC-06 기존 담당자의 ZIP/해시 검증 기록
- [x] MOLIT-001-AC-07 기존 담당자의 명시 기간 검증 기록

- [x] MOLIT-HISTORY-AC-01: Explicit observation start is persisted in the plan, CLI, and rebuilt DB period; invalid ranges are rejected. The plan records 2024-01-01 through 2026-08-31.
- [x] MOLIT-HISTORY-AC-02: The 825 overlapping queries are hash-verified/reused and the only 1,575 new queries cover 202401–202509; all 2,400 target queries are complete.
- [x] MOLIT-HISTORY-AC-03: Original XML, manifests, staging lineage, normalized DBs, status, summary, final ZIP hash, and GitHub #7 results reconcile; raw data remains out of Git and quality remains source_unverified.

## Verification record

- [x] Targeted unit contract suite: `test_collection.py` passed 16 tests with TMP/TEMP directed to `.codex-tmp` after the sandbox temp directory produced WinError 5.
- [x] Existing query reuse: 825 overlapping service×district×month queries were SHA-256 verified against donor `molit-seoul-three-api-20261012` and reused. The separately reserved missing scope was 1,575 queries.
- [x] Explicit credential mapping: user approved the rental/trade/trade-detail mapping after the wiki and prior issue search found no saved service-ID mapping. No credential values or IDs are written into the archive or validation record.
- [x] Actual API fetch: 1,575 new queries completed from 2026-10-15 00:35:35 to 01:12:29 UTC; no service errors. Total target status is 2,400/2,400 `complete` (800 per service), with no missing, invalid, failed, or zero-row queries.
- [x] Full offline DB rebuild: `integrity_check=ok`, foreign-key violations=0, rejected=0, outside-period=0. Raw/imported rows: rental 685,575; trade 192,142; trade-detail 192,142. Staging joins: rental 685,575 and sale 384,284; source services remain separate observations.
- [x] Final package: ZIP contains 2,400 query manifests and 5,090 entries; internal period is 2024-01-01–2026-08-31, Seoul 25 districts × 32 months, `source_unverified`. `ZipFile.testzip()` returned `None`. ZIP SHA-256: `5c929e5869c17075810ba24eca5ca2c71227df643416e08464112760ac6f91e6`.
- [x] GitHub #7 records final query/row counts, DB reconciliation, collection time, manifest details, package SHA-256, and that Drive upload is pending/not in scope. Raw data, DBs, and ZIP remain ignored by Git.

The previous collection owner was `@keulreobeu / Codex` in [GitHub #5](https://github.com/keulreobeu/jipdam/issues/5). The wiki search found no service-to-credential-ID mapping; the user later approved an explicit mapping for this fetch. The final ZIP is local, and Drive upload was not performed.
