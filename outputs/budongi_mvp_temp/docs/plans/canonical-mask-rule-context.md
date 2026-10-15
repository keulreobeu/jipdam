# Canonical masked-label rule context for GMS draft

This is an excerpt-only, non-sensitive source brief. It contains no real records, database rows, credential values, or raw data.

## User-approved behavior

The approved CANONICAL-001 contract allows deterministic candidate proposals from shared labels, but candidates are not confirmed relationships or foreign keys. Multiple official IDs remain unresolved. Do not join transactions, infer aptSeq for rentals, geocode, or auto-promote candidates. Public masking such as `***` means the value is unknown and must not become identity evidence.

## Current normalized input fields

`collection_db.normalize_row()` maps public MOLIT fields as follows:

```python
"sgg_cd": _required(raw, "sggCd")
"legal_dong": _optional(raw, "umdNm")
"apartment_name": _required(raw, "aptNm")
"jibun": _optional(raw, "jibun")
```

Only trade-detail observations may create an official complex from `aptSeq`. Rental rows do not receive an official complex ID from that API field.

## Current candidate proposal

`collection_integrate._candidates()` groups official labels, then equates all four fields. It already creates only pending/unverified suggestions and keeps the supporting observation:

```python
CREATE TEMP TABLE official_labels AS
    SELECT complex_id,sgg_cd,legal_dong,jibun,apartment_name,
           MIN(observation_id) AS supporting_observation_id
    FROM observations
    WHERE complex_id IS NOT NULL
      AND length(trim(legal_dong))>0
      AND length(trim(jibun))>0
    GROUP BY complex_id,sgg_cd,legal_dong,jibun,apartment_name
```

```sql
JOIN official_labels b ON a.sgg_cd=b.sgg_cd AND a.legal_dong=b.legal_dong
  AND a.jibun=b.jibun AND a.apartment_name=b.apartment_name
WHERE m.batch_id=? AND a.complex_id IS NULL
```

For each row not already present, the code inserts `review_status='pending'`, `confidence='unverified'`, `confidence_score=NULL`, match basis, and supporting evidence.

## Draft request

Review this implementation for a false-candidate risk when masked strings such as `***` are treated as ordinary values. Draft the smallest deterministic fix and synthetic regression tests. Preserve exact fully unmasked matches. If remaining fields do not satisfy an explainable rule or multiple official IDs remain possible, leave the result unresolved/pending. Do not introduce fuzzy matching or broaden match keys without a defensible deterministic rule grounded in the current Spec. Never set a confirmed status, `observations.complex_id`, or non-null `confidence_score` from this rule. Return proposed code/test edits as reviewable text only; do not execute tools, access a database, or use real records.
