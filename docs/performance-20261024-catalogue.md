# Catalogue browsing changes — 24 October 2026

Implemented locally. No deployment, production migration, catalogue mutation,
or real-local database write was performed for these application changes.

## Result

- Museum galleries default to highlights first and return 24 cards, with bounded
  keyset pagination (48 is available in the UI; the API maximum remains 60).
  Artwork details and creator/image enrichment follow page selection.
- Documented, active-source museum selections take priority. Collections without
  one receive an automatic Artlines starting selection of up to 24 works,
  illustrated first, then canonical title/ID order. Its labels and API source
  distinguish it from museum designations. Nothing is persisted as a museum
  highlight, holding, or current display claim.
- All and standalone Artworks browse paintings only. The backend enforces this
  for ordinary pages, searches, totals, picked IDs, legacy filters, and cursor
  navigation. All retains its existing requirement for an attached local image.
  Other collection/detail routes retain their existing media policy.
- All hides unmatched historical photographic illustrations in event drawers;
  canonical painting reproductions retain artwork links, captions, and credits.
- Painter galleries default to With pictures in both embedded and full profiles.
  Explicit opt-outs persist. The text-only artwork record index remains available.
- Museum counts/highlight candidates and standalone artwork counts use the
  existing catalogue revision cache and one-minute expiry. Source edits invalidate
  cached results; historical display evidence keeps its existing expiry rules.

## WWII selection

Three existing illustrated paintings were added to the preset, with stable slug
identity mappings and source references:

| Painting | Creator | Evidence |
| --- | --- | --- |
| A Canadian War Factory | Wyndham Lewis | [WikiArt](https://www.wikiart.org/en/wyndham-lewis/a-canadian-war-factory-1943) |
| For the Armenians-fighters, veterans of World War II | Martiros Sarian | [WikiArt](https://www.wikiart.org/en/martiros-sarian/for-the-armenians-fighters-veterans-of-world-war-ii-1945) |
| Seacombe Ferry in Wartime | Albert Richards | [National Museums Liverpool / Bridgeman](https://www.bridgemanimages.com/en/richards-albert/seacombe-ferry-1941-oil-on-board/oil-on-board/asset/6318592) |

The production read-only preset query returned **35 illustrated paintings**,
including all three additions. These are new preset connections, not new artwork
or image records. Existing metadata, rights, review states, and attributions stay
intact. Their stored image bytes were retrieved through authorized Cloud Storage
reads and visually checked. Public image probes returned HTTP 403; this run does
not establish current public CDN delivery. Tate's denied source routes were held.

Dalí's *The Face of War* was inspected but excluded from this addition: its holding
assertion remains in review and it has no eligible stored curation. The
[museum's collection research](https://www.boijmans.nl/en/collection/research/a-dream-collection-surrealism-in-museum-boijmans-van-beuningen)
is retained as a research lead; this change does not promote that assertion.

## Verification

An isolated PostgreSQL cluster contained 400,000 museum works and 200,000 unrelated
works. Both implementations started with empty application caches; PostgreSQL's
buffer cache was warm. Latest serial run:

| Check | Result |
| --- | --- |
| Previous first page | 1.888 s |
| New first page, including counts and facets | 1.287 s |
| New next page | 10.7 ms |
| Cards returned | 24 |
| Page-query index candidates | 49 illustrated; 25 unillustrated |
| Deep cursor after work 390,000 | Passed; bounded index scan |
| Missing/unsupported media and cursor boundary | Passed |

`EXPLAIN (ANALYZE, BUFFERS)` verifies ordered, bounded artwork scans before evidence
and card enrichment. Regression checks reject a page plan reading over 500 rows
from either museum seek index in this fixture. Counts/facets still aggregate the
matching collection on a cache miss. This is a serial 600,000-row proof, not a
10-million-row or concurrent production load test.

Additional validation: affected Go packages; 75 frontend tests; TypeScript;
targeted ESLint; production Next build; read-only artwork directory/search and
event-image SQL; production read-only All paging, creator filtering, legacy print
exclusion, and WWII selection. Chrome checked museum paging, both highlight
sources, a 390px layout, painter default pictures and opt-out persistence.
The in-app Browser tool was unavailable (`missing field sandboxPolicy`); the
project's Playwright/Chrome runner supplied browser verification.

Evidence, plans, image hashes, and logs are retained under
`~/Library/Application Support/Artline/implementation/catalogue-performance-20261024/`.
The real local `artline` database stayed read-only. The isolated test cluster's
mutating edge case rolls back its transaction.

## Release requirement

Migration `0059_museum_gallery_seek.sql` supplies the institution/title and
illustrated institution/title seek indexes, plus the standalone painting-directory
index. It has been applied only to the isolated fixture. On populated production,
prebuild its three indexes concurrently through the established operator workflow
before recording the migration and releasing the tested application.

The three research supervisors remain independent, with new dispatch scheduled
to stop at **12:24:47 UTC / 15:24:47 Asia/Nicosia on 24 October 2026**.
