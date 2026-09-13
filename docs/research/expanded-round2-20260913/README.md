# Second research round — expanded artwork CSV

**Complete and verified in local and production.** Every imported row matches
across the two databases, and live checks passed for all five museum sources.

This round audited all **91,589 remaining unlinked review artworks** from the
previously imported expanded CSV. It does not reinsert the CSV or create duplicate
artwork rows. Original source records and unresolved artworks remain preserved.

The reviewed plan links **7,785 artworks** to **725 existing painters** and
**1,458 newly documented named painters**. It enriches **5,640 artworks** with
museum metadata. All linked artworks remain in review with their research
candidate flag set. Missing information is not a publication decision.

| Source | Artwork links | New object metadata |
|---|---:|---:|
| Finnish National Gallery | 4,244 | 4,244 |
| MoMA | 1,396 | 1,396 |
| Joconde | 1,869 | Already researched |
| Tate | 186 | Already researched |
| SMK | 90 | Already researched |

## Research evidence and matching

New sources are official museum releases:

- [Finnish National Gallery API documentation](https://kokoelma.kansallisgalleria.fi/api/swagger/)
  documents a public, unauthenticated metadata package. The captured package has
  89,072 object records. Only candidates from the supplied CSV are matched; no
  artwork images were downloaded.
- [MoMA's collection dataset](https://github.com/MuseumofModernArt/collection)
  provides artist/object metadata under CC0. This round pins commit
  `7f1a337ee48e7daa05b5fdbc575a1797ac23b6cf`; image URLs and on-view values are not
  imported as image rights or current-display claims.
- [NGA's data dictionary](https://github.com/NationalGalleryOfArt/opendata/blob/main/documentation/Data%20Dictionary.txt)
  documents artist alternative names. The alias file was fetched at the same
  `f088836026d09d0d25001814fba0f84d757ebe62` revision as the prior preserved NGA
  authority data. Spouse names are excluded as aliases.

The earlier Joconde, Tate and SMK captures remain the sources for their existing
object facts. Creator reconciliation adds exact documented name variants plus
corroborating biography years; it does not silently replace those original facts.

New object matching requires creator, title, museum and date agreement and one
source object. Ambiguous objects, qualified creators, multi-creator objects,
physical parts and unsupported known types are held. Matching accepts name word
order and diacritics without collapsing distinct full names or ordinal suffixes.
Stable source/Wikidata IDs are checked first; a name variant otherwise needs at
least one positive biography boundary and no contradictory known boundary.
New painters need documented closed lifespans, named-person attribution, and no
plausible existing or newly proposed alias collision. These are source-based
identities, not a claim that all possible historical namesakes have been resolved.

The new sources yielded 6,731 exact object candidates. `new-source-matches.json`
preserves these mappings, including candidates whose painter identity remains
held. Full captured data and SHA256 receipts remain under
`content/imports/expanded-round2-20260913/`. Records needing further investigation
remain actual review artworks in the database, not deleted rows.

Draft plans exposed 19 repeated proposed identities across sources. Full name and
closed-biography agreement reconciled those, and an additional 18 artwork links
with possible new-painter alias collisions were held. One otherwise eligible
creator label contained a literal escaped-Unicode artifact and was held rather
than creating a malformed painter name. Draft plans and hold evidence are retained.

## Date and metadata handling

New metadata supplies work type, date wording/bounds, medium, dimensions and
accession number. There are 5,638 newly classified paintings and two drawings.
Museum creator life dates populate only new painter records; existing painter
biographies are preserved. No nationality, place entity, accepted museum holding,
current display, image, popularity or masterpiece designation is invented.

An explicit museum date such as “Paris, June-July 1914” supports the year 1914.
Short ranges such as `1914–18` remain ranges. Open/disputed dates stay unknown.
Twenty-seven Finnish records supply a range identical to the painter's lifespan;
these are explicitly retained as undated, not treated as known creation ranges.
All selected source date wording was audited for post-1970 years; none contained
one. Unknown dates still require review. The resulting subset has 7,211
creation-eligible records and 574 needing date review; all remain unpublished.

## Plan, safeguards and verification

Plan SHA256:
`8448d36c68fce734e2bada8a9ef9d57023fed8e2d3b385571c3f8d11a9e9eae7`.

Migration 0018 adds a source-evidence ledger with foreign keys to the real
artwork, painter and original research-link records. Each batch checks original
CSV cells, original entry checksum, source-fact checksum/state/supplemental
review, current artwork fields, painter biographies, existing attribution links
and unique source object identifiers. It uses the existing ingestion advisory
lock and a serializable transaction. New metadata and painter links are atomic.
No existing artwork is merged by title or painter name.

The first local attempt found an ambiguous SQL column reference and rolled back
its entire transaction. The qualified-column correction changed no plan data.
The local run then completed 32 batches of at most 250 records. Replaying the
first real batch created zero artists and changed zero artworks. No test fixture
or test database was used. Five offline policy tests cover dates, uncertainty,
name variants and namesake separation.

Bounded read-only audits compare every intended field, unchanged artwork fields,
existing painter metadata, attribution links, citations and ledger membership.
They also check that artwork and original research-record totals stay unchanged,
new painters have the documented lifespans, and the remaining-unlinked count
falls by exactly the applied number. Generated IDs, audit timestamps/revisions
and independently managed image pointers are excluded from cross-database hashes.
The pre-update row checksum matched in local and production; local retains three
extra archived artwork/painter pairs from the earlier documented correction.

Local verification: 210,501 artwork rows (unchanged), 9,147 painter rows,
115,258 original research records (unchanged), and **83,804 remaining unlinked
review artworks**. These include identities without enough evidence and the
large group not yet uniquely matched to an official object. This round is not
an exhaustive resolution of every supplied record, nor a ten-million-row load
performance proof.

## Backups and durable archive

Backups precede all writes and remain under:
`/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round2-20260913/`.

- Local `local.dump`: 335,050,206 bytes; SHA256
  `ba0c179f9885c56ebd05e55aaf8067d4dc9480efb7967d6aed3d927cd81d00f3`;
  archive listing validated before writes.
- Production Cloud SQL backup `1789297362074`: `SUCCESSFUL`, completed
  13 September 2026 at 11:04:13 UTC, before production changes.

The pinned plan and museum source captures are archived privately at:
`gs://artline-508319-images/research/expanded-round2-20260913/plan-and-sources-v1.tar.gz`.
The 46,498,034-byte archive has SHA256
`92f405e57f85aae347e2e2dc78f8e82af29a3e770639872df041062cf88c43b2`;
its cloud MD5 matches the local archive. The corrected writer is separately
archived as `apply-expanded-round2-v2.py`, with a checksum receipt in
`writer-correction.json`. The original archive remains immutable.

Production uses project `artline-508319`, instance `artline-postgres`, database
`artline`, through the existing authenticated proxy. No public application
redeployment is needed for these additive schema/data changes. Concurrent UI and
image work is preserved.

Production's initial four batches committed 1,000 links. A subsequent connection
drop left the next transaction uncommitted; Cloud SQL logged an unexpected client
EOF with an open transaction, without restarting the postmaster. The exact
1,000-entry committed prefix was checked against the ledger before resuming
from entry 1,001 in batches of 100. The plan stayed unchanged. See
`production-resume.json`; the writer with configurable batch size is archived as
`apply-expanded-round2-v3.py`. All new-source matches, including identity holds,
are additionally archived as `all-new-source-matches.json.gz`.

A read-only query of 100 actual ledger entries uses its primary-key index and
completed in 1.702 ms locally (`local-ledger-plan.json`). This bounded check does
not substitute for the outstanding capacity-scale load tests.

Final production verification: 210,498 artwork rows (unchanged), 9,144 painter
rows, 115,258 original research records (unchanged), and 83,804 remaining unlinked
review artworks. The complete imported-row SHA256 matches local:
`89acc54f2fff0c106a7ac9ab8026fdbb710287f7eb28bb4108334e6ceab90f3a`.
Production's 72 committed batches cover the plan exactly once; creation/update
totals match local (`execution-comparison.json`). The final comparison checks
all intended fields, preserved fields, painter identities, citations, ledger
entries and publication/cutoff status (`database-comparison.json`).

Live bounded artwork endpoints returned HTTP 200 with the expected new work and
metadata for Louisa Lesca-Etevenot, Johannes Goedaert, Wally Hedrick, Gudmund
Lervad and Dugald Sutherland Maccoll. The Goedaert, Lervad and Maccoll works remain
undated while correctly linked to their painters. See `live-verification.json`.
The five live checks completed in 0.22–1.33 seconds after import.
