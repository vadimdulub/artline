# Russian, Greek and Byzantine icons — first implementation batch

10 September 2026. Local personal research only; no publication, commits, cloud
writes, Terraform application, image downloads or museum display assertions.

## Applied result

| Official collection | New artworks | Linked artist authorities | Source-level creator labels |
| --- | ---: | ---: | ---: |
| Byzantine and Christian Museum, Athens | 15 | 0 | 15 |
| Moscow Kremlin Museums | 7 | 1 existing | 6 |
| Total | 22 | 1 existing | 21 |

The database now has **105,943 artworks, 5,315 artist authorities and 296
institution/collection records**. The latter is not a count of distinct museum
buildings. Media assets remain 310. All 22 new works are in review and satisfy
the backend creation-scope policy. No new artist biographies were manufactured.
No previously stored artwork rows were changed by this import.

Kremlin object 9453 is linked to the existing Theophanes the Greek authority,
Q319403, with `attributed_to`, not `primary`. The catalogue's question mark is
retained. Its creation interval is 1376–1400, the full last quarter of the 14th
century. Modern holding country does not establish creator nationality.

## Why this required backend work

Previously museum visibility required a visible linked artist. An icon with an
unidentified maker could therefore disappear even when its own catalogue and
holding evidence were sound. Migration 0012 adds nullable object-level fields:

- `unlinked_creator_label`: reviewed catalogue wording, not a shared fictional
  “Anonymous” person. Can also preserve an unresolved named/stylistic attribution.
- `cultural_context`: source-backed tradition/school context, separate from the
  holding country and production place.
- `object_form`: currently `icon`; the underlying `work_type` remains `painting`.
  This does not pretend that mosaics, carved icons or metal icons are paintings.

No old row receives an automatic anonymous designation. An explicit unlinked
label grants the alternative visibility path only if **no artist links exist**;
it cannot bypass a hidden or archived linked artist. Work/institution publication
and preview authentication rules remain in force. Museum counts, bounded cards,
details and text search share the backend policy. Search also covers alternative
titles and creator/context labels. English alternative titles for Kremlin works
are editorial translations, not English-language museum catalogue fields.

Next.js renders the source-level maker label in the grid/right panel and shows
form and cultural context separately from medium and holding. There are no fake
life bars for anonymous makers. Existing painter timeline bounds are unchanged.
Unlinked works are currently discoverable through museums, not a fabricated
anonymous-painter entry in the timeline or painter catalogue.

## Evidence routes and access limits

- [Athens icon collection](https://www.ebyzantinemuseum.gr/?c=9&i=bxm.en.collections):
  three index pages expose 69 selected catalogue entries, **not** the whole
  collection. Captured the first 24 individual records, then selected 15.
- [Athens Crucifixion, BXM 01354](https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=33):
  double-sided object, 14th century, catalogue attribution to Constantinopolitan
  workshops. One accession remains one object; no duplicate recto/verso records.
- [Kremlin catalogue](https://collectiononline.kreml.ru/): reviewed eight
  individual object pages, selected seven. Catalogue overview and two thematic
  search routes are discovery only, not a completed collection capture.
- [Theophanes attribution](https://collectiononline.kreml.ru/entity/OBJECT/9453)
  and [Novgorod icon, mid-12th century](https://collectiononline.kreml.ru/entity/OBJECT/9679)
  provide individual object IDs, production dates, media and inventory numbers.
- Kremlin robots disallows `/api/`. No request to that route was made. Object
  facts were read from the data already embedded in the allowed HTML detail
  pages; the embedded JSON keys containing `/api/` are not network requests.
  One public JavaScript bundle was inspected to understand the site's format,
  before deciding not to use the disallowed API route.
- [Athens terms](https://www.ebyzantinemuseum.gr/?i=bxm.en.terms) and
  [Kremlin terms](https://collectiononline.kreml.ru/terms-of-use) restrict reuse.
  App descriptions contain short factual summaries, not museum essays. Images
  remain absent pending a separate rights-cleared workflow.
- [Thessaloniki wooden icons](https://www.mbp.gr/en/collections/wooden-icons/)
  and [Recklinghausen collections](https://ikonen-museum.com/en/ikonen-museum/sammlung)
  were reviewed for discovery only. Recklinghausen's museum-digital route timed
  out; the local collector stopped at a robots 404 and did not proceed.
- Russian Museum discovery URL returned 403, Benaki 520, and a British Museum
  detail page 403. No access-control workarounds or alternative proxy requests.

41 successful captures total **1,884,819 bytes**, from 17:32:58 through 17:41:33
UTC. Each has its exact URL, retrieval timestamp, byte count and SHA-256 receipt
in `content/imports/icons-primary-20260910/`. Capture is bounded, paced at 10.5
seconds, uses no automatic redirects/retries, caps each page at 2 MiB and forbids
API/image paths. Raw HTML is private research evidence, not public web content.

## Deliberate deferrals

Athens object IDs not imported from the selected first page:

- 32: 9th-century core, later front/reverse painting phases. Needs pre-1100
  timeline/date support and a multi-phase object model; not redated to fit 1100.
- 44: mosaic icon; needs a supported medium plus verified creation dating.
- 34: combined relief carving and painting; needs mixed-medium classification.
- 245: separated painting layers with distinct inventory identities; needs
  explicit component/derivative relationships before further import.
- 23 and 239: current selected detail text did not establish a creation interval.
- 45: named/workshop attribution and creation dating need additional review.
- 54 and 66: historical context or an artist's period of activity is insufficient
  on its own to assign an artwork creation interval.

Kremlin 11064 has compound production wording (late 18th / early 19th century,
before 1843); deferred rather than parsing it as an exact creation year.

For imported works, full centuries conservatively represent early/late/mid
qualifiers; explicit halves and quarters use their full intervals. The literal
date remains visible. Athens 41 retains “a few years prior to 1501” as an exclusive
upper-bound date, with no invented lower year. Source provenance such as a church
is kept separate from a confidently established production place.

This is a first implementation batch, **not broad coverage of these traditions**.
Next priorities remain named Cretan/post-Byzantine creators, early Byzantine
works, mixed media and multi-layer objects, and additional Russian/Greek museum
records with individually reviewed image rights.

## Reproducibility and verification

- `ops/research-icons.mjs`: bounded source captures; `ops/assemble-icons.mjs`:
  offline individual evidence mapping, no database/network writes.
- Athens manifest pin: `000659a06cef548f86baf9f1c85c96679db5141b1515186fece05adedbab2809`.
- Kremlin manifest pin: `59f9160a1a2f062414ba7dca5b4761472611563e4cc5ec45eadc9a04ac5c83a6`.
- Each batch is one checksum-pinned chunk. Existing source/accession collision
  checks remain mandatory. Linked/unlinked attribution conflicts fail safely.
- Before schema/data writes, custom-format PostgreSQL backup:
  `/Users/vadimdulub/Documents/artline-icons-backup-20260910.9hv0UW/before-icons.dump`.
  SHA-256 `a9b7cd2e5809f4b3c0e2c16782beefd2746538369b108e6e9cc264cb19d75a4a`.
  `pg_restore --list` succeeded (253 lines); not a full restore rehearsal.
- Preview fingerprints showed no changes. Apply created 22 works, two museum
  institutions and 46 citations. Replay created/changed nothing. Original
  artwork rows, artists, images, rights and personal/museum selections remain
  unchanged. Receipts: `output/icons-{athens,kremlin}-{preview,apply,replay}-20260910/`.
- Full Go integration suite and vet passed; dedicated anonymous visibility,
  creator conflict, checksum, rollback and replay tests passed.
- Web lint/typecheck and all 24 component/unit tests passed. Two Chrome E2E
  scenarios passed, covering desktop/mobile creator labels, right-panel details,
  qualified Theophanes link, Escape/focus restoration and automated axe checks.
  Screenshots: `docs/screenshots/icons-athens-drawer-{1440,390}.png`.
- In-app browser bootstrap failed with a missing `sandboxPolicy` runtime field;
  the project Chrome/Playwright tests were the disclosed fallback.
- First HTTP pass: 22 checks, mostly 0–26 ms; global museum directory 1,091 ms.
  Follow-up: **24 checks passed**, including English alternate-title search and
  anonymous-only directory coverage. The global directory/search took 1,860–2,081
  ms during the final parallel test run; scoped English-title search took 14 ms.
  See `output/icons-api-verification-v2.json`. Global directory aggregation is a
  remaining performance concern, not demonstrated production-scale readiness.
- Museum-scoped 100,000-row temporary fixture retained indexed access and took
  2.899 ms. This is **not a 10-million-row performance claim**; global counts,
  summaries/indexing and realistic concurrency still need scale work.
