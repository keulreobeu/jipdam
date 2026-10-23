# Team Reference Import Validation — 2026-10-20

## Result

Four ZIPs were downloaded from the Drive links recorded in GitHub #9, #13, #14, and #15. Their SHA-256 values matched each issue. ZIP CRC checks, the manifest identity/quality checks, and every listed package file's byte length and SHA-256 passed.

The separate `team_reference.sqlite3` contains 157,602 accepted normalized records and one rejected academy row with its rejected status preserved. Each record retains the package payload and `source_unverified` state. `PRAGMA integrity_check` returned `ok`; `PRAGMA foreign_key_check` returned no rows. The database SHA-256 is `1275ade96fb328c59a0ede2e9af2566e6e340a3a086c727d5e554826a397518c`.

| Source | Issue | Accepted | Rejected | ZIP SHA-256 |
| --- | ---: | ---: | ---: | --- |
| HUG regional guarantee accidents | #9 | 828 | 0 | `9ebf178baba3612e492128a732c38e54fcb6e2d2fb07202ef4e16fbfa3c0dcda` |
| NEIS academies | #13 | 138,523 | 1 | `8da8dd9a1445138ed3929d1b5abedbfe1de6143b8583663f73d348ab4e4f2eda` |
| National libraries | #14 | 3,597 | 0 | `1e15a13cbcc153a6332cbc3288ff18ebcfdaf4262951551afedd9f8f66a46dbb` |
| Child protection zones | #15 | 14,654 | 0 | `38651cf6384358b3ea4ebf1b4e2b94fd18defa084efb879de5b4ad7094985a63` |

## Commands

Import and package verification:

```powershell
python -X utf8 outputs/budongi_mvp_temp/scripts/import_team_reference_packages.py --package-root outputs/budongi_mvp_temp/data/collection/team_import_20261020 --database outputs/budongi_mvp_temp/data/collection/team_import_20261020/team_reference.sqlite3
```

Read-only SQLite count, integrity, and foreign-key audit:

```sql
SELECT source_id, record_type, validation_status, COUNT(*)
FROM records GROUP BY source_id, record_type, validation_status;
PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

The rental canonical/serving databases were not modified. The imported rows remain unverified and are not connected to location matching, maps, or recommendations. Other packages from #10–#12 were outside this import request.
