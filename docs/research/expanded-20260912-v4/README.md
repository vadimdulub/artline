# Expanded CSV upload: final review and receipts

The supplied export contains **285,090 rows**: the existing **106,350** plus
**178,740 additions**. The final import stores **104,934 distinct research
entries**, preserving **108,074 supplied rows** and their original record numbers.
They cover **32,235 creator labels**, not verified counts of unique painters.

These entries are in research staging in both local `artline` and production
`artline` in `artline-508319`. **No new catalogue painter or artwork pages have
been created.** The six-column export omits museum object IDs, source links,
artwork types and creator authorities. Those companion research details are
required to promote these rows without inventing identities or types.

| Outcome for the 178,740 additions | CSV rows |
|---|---:|
| Anonymous/unidentified creators excluded | 41,801 |
| Ambiguous attributions, workshops, schools, geographic/collective labels deferred | 27,672 |
| Other ambiguous creator identities deferred | 1,193 |
| Named artwork candidates retained | 108,074 |

The retained set includes 3,140 repeated rows, preserved as record-number lists
rather than discarded or asserted to be duplicate physical objects. Of the retained
rows, 64,540 have straightforward closed date strings within the cutoff; 43,534
require date interpretation. Both groups still require source and identity review.
No dates, painter lifespans, artwork types, nationality or on-view claims were invented.

## Evidence

- [Final inventory and checksums](review.json), [deferred/excluded rows](deferred.json),
  and 21 `chunk-*.json` files retain the full mapping locally.
- Input SHA256: `210a729ead48d12b0f228eb9e1fe0c5a6708750b196be38ddfbbb270aa1355c8`.
- Baseline SHA256: `3e89837f9ab91fbb9365a03c33ad6f9fd5b89c21a89b758615bcd2d9aefdc26b`.
- Original supplied CSV: `/Users/vadimdulub/Downloads/artline-artworks-expanded-2026-09-12.csv`.
- Private cloud copy: `gs://artline-508319-images/research/expanded-20260912/210a729ead48d12b0f228eb9e1fe0c5a6708750b196be38ddfbbb270aa1355c8.csv`.
- `hasPicture` remains a supplied claim. There are no image URLs or rights records
  in the CSV; no images were downloaded, attached or declared rights-cleared.

## Import and correction

The first completed upload used [v2](../expanded-20260912-v2/README.md), with
104,984 entries. A final language audit identified 50 additional regional or
collective labels, including `Pittore Lombardo` and `Various artists`.
The final filter removes these and preserves genuine role-prefixed names such as
`Painter: Philip Guston`. v1 and v3 are retained offline audits, not applied inventories.

`ops/reconcile-expanded-creators.py` verifies that v4 is a strict subset of v2,
that all surviving facts are unchanged, and that every removal belongs to the
reviewed regional/collective labels. Its generated SQL checks the prior snapshots,
locks the staging importer, removes only those 50 newly imported entries and
reassigns surviving entries to their corrected checksum-pinned chunks in one
transaction per database. Existing catalogue entities and earlier research survive.
The same SQL was applied locally and in production. The original v2 receipts remain
historical evidence; use the final inventory for replay.

Backups and the exact correction SQL are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-research-20260912/`.
The complete local backup and scoped production research backup are detailed in
the v2 receipt. Both passed archive listing checks. `production.dump.incomplete`
is an interrupted, redundant full transfer and must not be used to restore.

## Verification and continuation

[Read-only database verification](database-verification.json) confirms that all
21 final chunk hashes, entry counts and original-row multiplicities match between
local and production. Both have **115,258 research rows** after this upload,
including the prior 10,324. Both still have **5,328 artists and 106,350 artworks**.
The generated correction removed exactly 50 rows and reassigned 34,934 surviving
rows to seven corrected snapshots on each target; no catalogue row was changed.

The existing Go ingestion tests and HTTP API tests passed with
`ARTLINE_TEST_DATABASE_URL` unset. Additional offline tests cover multilingual
creator labels, preserving role-prefixed named creators, uncertain dates,
CSV quoting/newlines, repeated rows, incomplete baselines, overwrite protection
and explicit Cloud SQL target selection. No test databases or catalogue fixtures
were created. Real-data replay returned `replayed=true` without inserting duplicates.

Provide the companion museum source/object and creator research to reconcile the
staged candidates into catalogue records. Repeated generic titles must remain
unresolved until stable object identities are supplied. New catalogue records
must retain review status, respect the artwork creation cutoff and preserve
separate holdings/current-display evidence. No ten-million-artwork performance
claim follows from this batch.
