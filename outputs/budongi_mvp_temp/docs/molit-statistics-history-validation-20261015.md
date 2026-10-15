# MOLIT statistics history collection validation — 2026-10-15

## Scope and approval

- User-selected basis: apartment transaction-volume statistics, 2024-01 through 2026-08; Seoul 25 districts.
- Services: apartment rental, trade general, and trade detail. Contract observation period: 2024-01-01–2026-08-31; 32 months × 25 districts × 3 services = 2,400 queries.
- GitHub reservation and final result: [Issue #7](https://github.com/keulobeu/jipdam/issues/7). The existing #5 overlap is reused; no matching, coordinates, facilities, recommendation linking, or Drive upload was performed.
- Wiki and #5 search identified prior owner `@keulreobeu / Codex` but no service-to-credential-ID mapping. The user explicitly approved the proposed rental/trade/trade-detail mapping before fetching. Credential values and IDs are excluded from this record and archive.

## Query coverage and retrieval

Batch: `molit-seoul-stats-volume-20261015`; plan stores `observation_from=2024-01-01`, `snapshot_date=2026-08-31`, Seoul 25 districts, and months 202401–202608.

- 825 completed queries from 202510–202608 were page/hash-verified and reused from `molit-seoul-three-api-20261012`.
- The only new queries were the 1,575 queries for 202401–202509. User-approved service credential mapping was used.
- Final archive status reverified all 2,400 queries as `complete` (800 per service); no missing, invalid, failed, or zero-row query. The new-query retrieval window was 2026-10-15 00:35:35–01:12:29 UTC; `fetch-result.json` reports `new_queries=1575` and `service_errors={}`.
- Per-service XML raw row totals: rental 685,575; trade 192,142; trade-detail 192,142.

## Offline DB reconciliation

Full `collection build-db` output is in the local ignored batch directory `data/collection/molit-seoul-stats-volume-20261015/db/`.

| Service | Raw rows | Imported | Outside period | Rejected |
| --- | ---: | ---: | ---: | ---: |
| Rental | 685,575 | 685,575 | 0 | 0 |
| Trade general | 192,142 | 192,142 | 0 | 0 |
| Trade detail | 192,142 | 192,142 | 0 | 0 |

`integrity_check=ok`; foreign-key violations=0. Staging joins: rental observations 685,575 and separate sale observations 384,284. Raw-row totals reconcile exactly to imported + outside-period + rejected. Sale-general and sale-detail rows remain distinct observations, not a de-duplicated transaction count. Quality remains `source_unverified`.

Database SHA-256:

- `rental.sqlite3`: `d588eb175ef7cf4b54d68fc3af2ee132c7543dec75e30feab738f9887f7632cc`
- `sales.sqlite3`: `d63e850ac3acd20fc8708bae46c10b0c9c5fa8f55c8dcec0b0bc7ca3fdc075f9`
- `staging.sqlite3`: `405c5ac6c9ed4d51f2cdc19d372a85568969b9c5179438e717a5ff82f5568a6c`

## Package and verification

- Local ZIP: `outputs/budongi_mvp_temp/data/collection/molit-seoul-stats-volume-20261015.zip` (590,805,091 bytes; ignored by Git).
- Package manifest reports complete, 2024-01-01–2026-08-31, 25 districts, 32 months, `source_unverified`; ZIP contains 5,090 entries, including all 2,400 query manifests.
- `ZipFile.testzip()` returned `None` (all members passed CRC verification).
- Final ZIP SHA-256: `5c929e5869c17075810ba24eca5ca2c71227df643416e08464112760ac6f91e6`.
- Targeted `test_collection.py`: 16 tests passed, including explicit observation-period, reuse, and credential mapping contracts.
- GitHub #7 updated with reservation results, query and row counts, integrity/lineage, collection time, manifest/ZIP hash, and `Drive: upload_pending`. Raw XML, databases, and ZIP remain excluded from Git.

Drive upload is outside this approved scope and remains pending separate handling. This task does not mark the source records as verified or connect them to canonical entities or recommendations.
