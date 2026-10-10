# Artline source index and first production enrichment — 9 October 2026

The local [source index](sources.jsonl) contains **20,000 distinct source URLs**,
with a [SQLite search companion](sources.sqlite), a [curated registry of 75
providers](providers.json), and evidence-backed links to **25,414 Artline
entities**. It is an index of museum objects, artist references, authorities,
books, catalogues and collection entrypoints, not a claim that there are 20,000
independent publishers or that every reference has been freshly verified.

**1,881 records have fresh structured metadata checks:** 455 exact museum
object responses, 728 Getty publications and 698 institutional art-library
records. **18,119 retain earlier catalogue citations and require a fresh
content/field review before new updates.** HTTP availability checks are recorded
separately and do not promote old citations to verified facts.

The first production delivery used this exact index revision to enrich **48
existing artworks**: **25 missing fields across 23 artworks** and **26 missing
primary images**. It also added 48 source citations, 48 audit records and three
source definitions. No new artworks, museums or publication/display assertions
were created. The real local database remained read-only; no fixtures, commits,
application deployment or Terraform changes were made.

## What is indexed

| Resource classification | Records |
|---|---:|
| Museum / collection object | 7,139 |
| Object or artist reference requiring finer classification | 7,655 |
| Artist reference | 1,699 |
| Artist authority | 667 |
| Book or catalogue | 1,433 |
| Museum directory / collection | 1,336 |
| Provider entrypoint | 68 |
| Reference dataset | 3 |

The resources span 1,028 hostnames and 1,009 provider groups. The 75 manually
organized providers include Cleveland, Chicago, Getty, SMK, the Louvre, Prado,
Rijksmuseum, Tate, Russian Museum, Tretyakov, Hermitage, Benaki, Goulandris,
Byzantine collections, Greek Ministry collections, Leventis, Cyprus archives,
Getty ULAN, RKD and scholarly libraries. Unknown/unclassified domains retain
`existing_citation_requires_field_review`; they are not silently granted the
authority of a museum.

Wikidata, Wikipedia, Pantheon and Artline's own imported-file mirrors are
excluded from the resource list. Their old evidence is preserved in the scoped
catalogue snapshot. WikiArt and Commons remain identifiable as separate source
classes. Museum object records cited for painter research are not automatically
reclassified as artist biographies.

Source discovery used a read-only snapshot of 9,988 existing artworks scoped to
151 institutions, their citations and identifiers, and the already retained
production painter-reference export. The 20,000-row selection is deterministic
and balances provider groups after prioritizing newly captured metadata. The
22,781 deduplicated candidate URLs and selection counts are recorded in
[index-summary.json](index-summary.json); selection is not exhaustive collection
or museum coverage.

## Authority is specific to the field

| Source family | Appropriate use | Limits |
|---|---|---|
| Native museum object record | Inventory, object/version, medium, dimensions, museum attribution, source dates and documented holdings | A holding is not current display; conflicting or qualified values remain explicit |
| Getty ULAN / RKD / library authorities | Creator identity, aliases and sourced biographical facts | Name similarity alone does not identify an artwork or establish influence |
| Museum or academic books and catalogues | Historical context, bibliography, catalogue raisonné/version evidence | Record edition and page before using a claim; old holdings and publication dates are not current holdings or creation dates |
| WikiArt | User-approved artwork/image reference, exact versions, supplied rights labels | Preserve actual labels and the project's matching/precedence rules, including the Louvre preference |
| Aggregators and image repositories | Discovery and contributor-attributed evidence | Follow the object back to its contributor; review each image's identity, rights and credits |
| Institution homepage / directory | Museum identity and a collection research lead | Does not justify inventing an artwork to make the museum browsable |

The Getty books were obtained through the public search endpoint used by its
[Publications & Reports catalogue](https://www.getty.edu/publications-reports/search?can_download=true).
The 698 library references are bounded metadata selections from institutional
collections on Internet Archive: painting/painters, Greek/Byzantine/Russian/icon
research, art history and collection catalogues. Full books were not downloaded
or treated as already read. A free download listing does not clear illustrations
for reuse. Modern publication dates are valid for research references; they are
not imported as artwork dates or automatically added to Artline's book catalogue.

## Using the local file

`sources.jsonl` is the canonical UTF-8 file: one JSON object per line. Key fields:

- `id`, `url`, `host`, `title`, `kind`: stable resource identity and classification.
- `provider_id`, `provider_name`, `authority_scope`, `provider_availability`: source role and a separate entrypoint availability check.
- `review_state`, `checked_at`: fresh structured metadata versus earlier references.
- `artline_bindings`: production entity type, UUID and label; a binding retains its original citation limitations.
- `citation_evidence`: citation/record IDs, field names, retrieval dates and short evidence previews. Full evidence remains in the referenced snapshot, with a digest of the original note.
- `discovery_evidence`: capture URL, raw-body path, checksum and record locator.
- `facts`: explicitly supplied object or bibliographic metadata; image rights are distinct from image availability.
- `image_permission`, `update_eligibility`: inclusion in the index is not permission to overwrite catalogue fields or download every image.

Search without loading the whole index into a browser:

```sh
/tmp/artline-influences-venv/bin/python ops/source-index-20261009.py search --query 'Byzantine' --limit 15
/tmp/artline-influences-venv/bin/python ops/source-index-20261009.py search --query '"Van Gogh"' --limit 15
```

The SQLite companion has `resources`, `bindings` and an FTS5 `search` table.
Its data are rebuildable from the JSONL file. The scripts require Python with
`psycopg`, `requests` and `beautifulsoup4`; image delivery also uses Pillow and
Google Cloud Storage. The `/tmp` virtual-environment paths above are the current
machine's working environments, not portable dependencies.

This revision is pinned by a completed delivery. `build` refuses to overwrite
it after pinning. Future research should create a versioned successor, retain
these checksums and receipts, and compare new assertions with current production
rows before writing.

## Production changes and verification

| Institution | Existing artworks enriched | New images |
|---|---:|---:|
| Cleveland Museum of Art | 25 | 25 |
| Statens Museum for Kunst | 22 | 1 |
| Art Institute of Chicago | 1 | 0 |
| Total | **48** | **26** |

The metadata additions are **18 medium fields and seven dimension fields**.
Source wording, including Danish technical terms, was retained. No populated
field was replaced. Titles, creation dates, unknowns, creator links, qualified
attributions, museum holdings, existing image attachments and historical
publication states were compared with the locked preimages and preserved.
Decorated mirror reverses, a named album leaf and an individual triptych panel
have explicit image-view labels.

The plan resolves every change through a fresh `source_index_id`, a production
UUID binding, the captured body checksum and the complete index SHA-256. It
rechecked the production state, used the shared curated-ingestion advisory lock,
locked the affected artwork rows, wrote atomically and created per-artwork audit
entries. Existing catalogue cache-invalidation triggers cover these updates.

- [Pinned plan](delivery-plan-pin.json) and [complete plan](delivery-plan.json.gz).
- [Applied receipt](production-applied.json) and [independent database readback](production-verification.json).
- [Public artwork API checks](public-api-recheck.json): **48/48 passed**. The
  [initial check](public-api-verification.json) had 13 HTTP 500/503 responses;
  all thirteen passed a subsequent sequential recheck. Both records are retained.
- [Index verification](index-verification.json): 20,000 unique IDs/URLs, 467 distinct raw-body checksums covering 1,881 fresh records, SQLite integrity and search checks.
- [Visual review](visual-review.json) and [contact-sheet bindings](contact-sheet-index.json).
- 28 offline identity/preservation tests passed. Each of the 26 uploaded files was fetched from the public site and checked against its SHA-256 before attachment. Derivatives preserve the complete selected source frame and stay at or below 100,000 bytes.

[delivered-artworks.json](delivered-artworks.json) lists every changed artwork,
the exact fields added, its source-index ID, museum source, public record URL and
new image URL. Replaying the applied plan returned **zero writes**.

[Actual query plans](scoped-query-plans.json) document bounded institution
lookups on the current production catalogue. These are not a ten-million-row
load test, and no such performance claim is made.

Cloud SQL recovery backup **1791543350518** completed before the transaction.
Locked preimages, the recovery plan and transaction after-state are under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/source-index-20261009/`

Original selected images and contact sheets are under the corresponding
`source-images/source-index-20261009/` directory. Application derivatives are in
`apps/web/public/assets/artworks/imported/source-index-20261009/` and the matching
production image-storage paths. These images and the source evidence are
retained; no unrelated assets or databases were removed.

## Remaining evidence gaps

[remaining-research.json.gz](remaining-research.json.gz) retains each unresolved
object and the next action. Of 462 selected exact native lookups, 455 yielded a
usable structured record, and 452 passed the automatic identity screen. Ten
remain held for missing/ambiguous responses, attribution or title/translation
review. Eighteen additional candidates need a reliable native binding before a
lookup. These counts describe different stages, not additive artwork deliveries.

The 106 image candidates yielded 28 prepared images; 26 passed visual review:

- Chicago's first image request returned **403**. Requests stopped; the 75 selected Chicago matches remain pending. No alternate endpoint or proxy was used to bypass that refusal.
- Three Cleveland handscroll thumbnails were too thin for this derivative path. Museum-listed print-size panoramas remain a useful follow-up; the 1–2 GB TIFFs were not downloaded.
- Two Ten Bamboo Studio primary photographs showed closed binding covers. They were withheld pending a reviewed, museum-listed open-page view appropriate to the named contents.

The [provider checks](provider-check-summary.json) record 47 readable
entrypoints, ten requiring further content inspection, and 18 unavailable or
held. This is availability coverage only. Existing [access holds](inherited-source-access-holds.json)
and new `access-holds/` receipts remain in force. The later Chicago image refusal
is recorded separately in [image-host-hold-chicago.json](image-host-hold-chicago.json).
No complete museum coverage, complete painter biography review or blanket image
rights clearance is claimed.
