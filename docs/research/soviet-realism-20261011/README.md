# Soviet Realism — 11 October 2026

The user requested a Soviet Realism movement, 2,000–3,000 eligible artworks,
and all selected authentic source images, explicitly approving their use
regardless of source rights labels. The original instruction and its scope are
preserved in [authorization.json](authorization.json).

## Delivery

The completed production delivery contains **2,500 new artworks and 2,500 primary images**,
associated with **448 artists**: 426 new artist records and 22 existing artists.
The movement is **Soviet Realism**, slug `soviet-realism`, ID
`a99da3f1-8cb8-5a8d-9adb-b2707942cfaa`. The existing broader
`socialist-realism` movement is preserved.

Read-only production verification passed at **10:57:57 UTC on 11 October 2026**:
all 2,500 distinct manifest records are date-eligible with selection evidence,
their expected primary images, creator links and source evidence. There were
no verification errors. The complete results are in
`production-verification.json` and the 50 receipts in `applied-batches/`.
Each batch is committed atomically; an
interrupted transaction is rolled back and deterministic identifiers support
resuming without counting a record twice.

| Source | New artworks | Primary images | Source rights status |
| --- | ---: | ---: | --- |
| SOVCOM | 1,876 | 1,876 | Restricted |
| Kyiv collectors club Socrealizm | 624 | 624 | Unknown |
| **Total** | **2,500** | **2,500** | Original labels retained |

The delivered creation dates span **1918–1970**. There are 1,981 exact-year
records, 477 explicit decades wholly before the cutoff, and 42 bounded ranges.
The selection contains 2,263 paintings, 128 drawings and 99 watercolours;
10 records retain an unknown work type. No creation year was invented.

The item-level [delivery manifest](delivery-manifest.csv) includes creator,
title, date precision, medium, dimensions, source/native identifier, original
image URL, public image URL, checksum, byte size and actual source rights label.
The immutable plan is `delivery-plan.json.gz`, SHA-256
`6c50358789664167de34249b1607784092d4ee4db816870fa038752c828f495b`.

## Movement and selection scope

This is an editorial survey of the Soviet tradition of Socialist Realism and
related realist practice, including Severe Style, portraits, rural and
industrial life, public history, landscapes and still lifes. It does not claim
that every selected work follows the narrow official doctrine or that every
work in an artist's career belongs to a single style. The source collection
classification, native creator profile, dated object record and visual review
support each selection; Soviet nationality alone is insufficient.

The [WikiArt Socialist Realism reference](https://www.wikiart.org/en/Artists-by-Art-Movement/socialist-realism)
was used to establish the relationship to the existing movement. Object and
image evidence comes from the
[SOVCOM Soviet painting catalogue](https://sovcom.ru/chastnye_prodazhi/sovetskaya-zhivopis/)
and the [Socrealizm public catalogue](https://www.socrealizm.com.ua/).
These are collector/auction sources, not museums. The works are personal
editorial selections in the existing owner collection. There are no invented
museum holdings, museum masterpiece designations or current-display claims.

The database models movements through artists. The new artists use the survey
as their primary catalogue grouping; links to existing artists are associated
links, preserving their prior primary classifications. Consequently, the
movement filter can also return an existing artist's earlier catalogue works.
Only the 2,500 explicit manifest IDs count toward this delivery.

## Reconciliation and exclusions

- SOVCOM's 630 current category records led to a bounded selection of 140
  creator portfolios. Their 4,809 historical listings were reconciled to 2,230
  candidate objects; 407 repeat listings were not counted separately and 2,172
  listings retained source/date/identity holds.
- Socrealizm's public category metadata yielded 8,018 unique cards and 1,244
  date-eligible leads. A thematic selection of 700 received individual object
  and creator-page checks. 688 object captures entered reconciliation. The
  remaining 12 retained capture or identity issues, including one empty error
  string; the earlier `objects-summary.json` counted only 11 nonempty holds.
- The combined 2,918 candidates produced 2,821 identity-approved candidates and
  97 holds. Production matching used native source URLs, full native names,
  transliterations/aliases, birth evidence and creator-scoped title checks.
  Ambiguous cross-language identities were held, not guessed.
- All 2,821 candidate images were decoded and prepared. Perceptual/exact image
  checks held 35 candidates. A second comparison against 785 locally available
  production images for the reconciled creators held three more matches; three
  emigrant-period Shukhaev works were also held.
- Every delivered image received visual review, recorded across 72 contact
  sheets. Manual review caught further reframed, recoloured and differently
  titled repeats, conflicting labels, multi-work lots, copy/version questions,
  abstract works and poor reproductions. Combined delivery-stage holds cover
  187 candidates. Another 134 eligible illustrated candidates remain outside
  the 2,500-work selection and do not count as delivered.

Full decisions remain in `sovcom-records.json.gz`, `artist-plan.json.gz`,
`identity-plan.json.gz`, `image-audit.json`, `existing-image-audit.json` and
`visual-decisions/`. Historical provisional plans are preserved in the
`history-*` directories. This is a selected survey, not exhaustive coverage of
all Soviet collections or all work by these artists.

## Images and production safeguards

The delivered JPEGs preserve each source frame and aspect ratio. Their combined
size is 181,915,125 bytes; the largest is 99,986 bytes, within the 100,000-byte
limit. All 2,500 objects were uploaded with create-only generation checks and
then fetched through `artlines.org` to verify their SHA-256 hashes. Upload
receipts are in `uploads/`; source-page captures and original image-download
receipts retain checksums and retrieval timestamps.

SOVCOM's reserved-rights label remains restricted. Socrealizm's unspecified
reproduction licence remains unknown. User approval is recorded separately in
each media evidence record; no public-domain or other licence was fabricated.
HTTP 401/403/429 access holds stop a provider. Private catalogue access was not
used; capture failures remain explicit.

New artworks remain in review, with no publication timestamp. Source attribution
is retained in creator notes and citations. Images are attached only to their
pinned artwork identities. Existing artwork metadata, holdings and publication
states are preserved. All work used the production connection; there were
**zero connections or writes to the real local database**.

Cloud SQL backup **1791713691191** completed successfully before the import.
Database preimages, transaction backups and final verification snapshots are
under `/Users/vadimdulub/Library/Application Support/Artline/backups/soviet-realism-20261011/`.
Source originals and contact sheets are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/soviet-realism-20261011/`.
Source/image evidence and scoped query plans are retained here. No test database,
test fixture, commit or deployment was created for this delivery.

The existing owner collection permits shared ordering ranks, capped at 100,000.
Each atomic batch uses a shared append rank within that limit, with the existing
artwork-ID tie break. No schema change was needed. Artist and object duplicate
checks are batched and scoped; the recorded plan uses the indexed creator
relationship lookup and indexed artwork-ID lookup. This production pass is
not a ten-million-row load test; that capacity validation remains separate.

## Reproducible checks

The scripts are `ops/soviet-realism-20261011.py`,
`ops/soviet-realism-sovcom-20261011.py`,
`ops/soviet-realism-delivery-20261011.py` and
`ops/soviet-realism-review-20261011.py`. Date-parser tests in
`ops/test_soviet_realism_dates.py` pass, including exact 1970, decades crossing
1970, ranges, uncertainty and event years separated from object creation dates.

Final read-only verification checks all manifest IDs, creator links, source
identifiers/citations, date eligibility and personal-selection evidence, media
checksums/sizes, actual rights labels, movement links, review status and the
absence of museum/display or publication changes. Public API checks are
recorded separately in `public-verification.json` and passed: the movement
facet and artist directory return 448 artists, six sampled artwork pages are
available anonymously with the expected dates, image and source citations,
and the [live movement page](https://artlines.org/artists?movement=soviet-realism)
returns HTTP 200. The facet check explicitly uses `popular=false`, since its
default is the separate popular-artist selection.
