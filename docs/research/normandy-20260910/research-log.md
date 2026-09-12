# Regional museums: Normandy — 10 September 2026

## Database result

Added **288 paintings**; the catalogue now contains **105,921 artworks**.
All 292 source-linked works (288 new, four exact existing matches) remain in
review and satisfy the creation cutoff ending no later than 1970.

| Source selection | Examined | Selected | New | Existing matches |
| --- | ---: | ---: | ---: | ---: |
| MuMa official highlights | 46 object pages | 30 | 28 | 2 |
| Rouen official collection themes | 62 object pages | 33 | 31 | 2 |
| Joconde, MuMa/Rouen painting supplement | 3,494 candidates | 229 | 229 | 0 |
| Total selected/imported | Overlapping source scopes; do not sum coverage | 292 | 288 | 4 |

MuMa Le Havre grew from **4 to 49** works; Rouen from **2 to 245**. Additions
include Monet's *Les Nymphéas* at MuMa, Velázquez's *Démocrite* at Rouen,
paintings by Sisley, Renoir, Boudin, Matisse, Delacroix and Poussin, and two
Pissarro harbour paintings with inventories **A 494** and **A 495**. Rouen's
supplement also includes 91 Jacques-Émile Blanche paintings.

**30 museum-designated highlights** were linked using MuMa's own highlights
page. No personal must-see choices were created. No generic museum membership
was promoted into a masterpiece label. No current-display claim was added.
Artist authorities remain 5,315; institution/collection rows remain 294.

## Museum discovery and coverage

The [current official Muséofile register](https://www.data.gouv.fr/datasets/musees-de-france-base-museofile)
contains 90 Normandy entries in the saved snapshot. Of these, 36 have painting
in the thematic fields and 34 have painting-domain records in the saved Joconde
export. These are different measures, not interchangeable collection totals.
Twenty-three entries map to existing local institution records.

See [all 90 entries and local coverage](museum-coverage.json) and the immutable
source-field audit in `audit/museum-directory.json`. Null local coverage means
unmapped, not an assertion that the museum has no artworks. Museofile covers
the French statutory museum designation; this is **not every museum in
Normandy, nor every small museum in Europe**.

Nearby sources reviewed include [Honfleur's official collections](https://www.musees-honfleur.fr/collections.html),
[Caen's official catalogue](https://mba.caen.fr/collections), and the
[Normandy museum network](https://www.musees-normandie.fr/musees-normandie/).
Existing coverage includes Honfleur, Caen, Dieppe, Cherbourg, Vernon, Fécamp,
Pont-Audemer and other regional collections; those existing records are not
counted as new additions here. Their remaining object catalogues need separate
reconciliation passes. The network's direct HTTP route returned 403; automated
capture was stopped for that host. No access workaround was attempted.

## Source capture, selection and rights

- [MuMa highlights](https://www.muma-lehavre.fr/fr/collections/oeuvres-commentees/incontournable):
  46 canonical detail links captured from the selected index. The site's displayed
  highlight count is 47; this pass does not assert complete coverage of that count.
- [Rouen collections](https://mbarouen.fr/fr/collections): six selected themes:
  Impressionism, Renaissance, European Baroque, French seventeenth century,
  Romanticism and landscape. Not the entire Rouen collection.
- [Joconde open metadata](https://www.data.gouv.fr/datasets/collections-des-musees-de-france-base-joconde):
  reused the complete, hash-verified 9 September export under Licence Ouverte 2.0.
  Only MuMa M0720 and Rouen M0729 painting candidates enter this supplement.

119 pages including robots/legal/index pages, 4,096,366 bytes, captured from
16:17:20 to 16:29:24 UTC. Object HTML and URL/SHA/size/timestamp receipts are in
`content/imports/normandy-primary-20260910/`. Each host's requested ten-second
crawl delay was respected by the collector (10.5-second spacing); requests
were serial per host, capped at 2 MiB/page, without automatic redirects/retries.
No artwork image binaries were requested.

Only factual object labels from the primary museum sites enter descriptions.
Curatorial essays and photographs are not reproduced. MuMa's
[legal notice](https://www.muma-lehavre.fr/fr/mentions-legales) reserves those
materials; Rouen's captured legal page provides no reusable-image grant.
**No new images were added**; all 310 existing media records and rights evidence
were fingerprint-verified unchanged.

Go owns offline authority matching, date validation and selection. The import
uses the existing atomic, hash-pinned, local-only Go/Postgres workflow. Exact
URLs and institution/inventory identifiers resolve existing works; no title-only
merging, guessed accession, unknown creator assignment or date invention.

The Joconde supplement defers creators represented in the primary pages, even
when the primary record itself was deferred. This conservative overlap rule
avoids cross-source duplicates pending accession reconciliation. Two individually
reviewed exceptions are the separate 1903 Pissarro harbour works, A 494/A 495;
they do not match the existing 1876/1882/1894/1901 scenes. See
`joconde-v1/overlap-gates.json`. Artist names in this exclusion step only cause
deferral; they never establish artwork identity.

### Explicit unresolved source issues

- MuMa labels Pissarro 1831–1903, conflicting with the existing 1830 authority.
  Those four primary-page records were deferred; existing works and authority
  data were preserved. The two new harbour records use Joconde evidence.
- MuMa's main *Les Nymphéas* caption gives 89 × 93 cm, while its header/HD
  caption gives 89 × 92. The description preserves the conflict and canonical
  dimensions remain empty pending review.
- Grouped objects, uncertain/qualified creators, unresolvable names, missing or
  unsupported date labels, missing/deposit cases and cutoff conflicts remain
  deferred. Source records are retained; `muma-v1/deferred.json`,
  `rouen-v1/deferred.json` and the Joconde summary record the decisions.

## Backup, pins and verification

Fresh custom-format public-schema backup before DB writes:
`/Users/vadimdulub/Documents/artline-normandy-backup-20260910.puTRiw/before-normandy.dump`.
SHA-256 `9316ca22535eebf1bdb1dc6236329e9e764ac253b23430a7033edd4cf2669cfa`.
Restore inventory readable (251 lines); this is not a restore rehearsal.

Pinned selection manifests:

- MuMa: `36bfe3abad9271388956cbcec4007c99e534778b9ac15a8f6b761140304fb412`
- Rouen: `720a8fe858f949cfb9650fd8d4c91f584f901e316b4a3e5cd0075c7c970f8a18`
- Joconde: `fa7af96f17c95654ecefc43504df720bcf5ecfbc57bbc27b659cbec7e161ed4f`

Each source passed rollback preview, explicit application and unchanged replay.
Ten table fingerprints were unchanged by previews and replays. The six original
works' titles, dates, descriptions and media were preserved. No publications,
current-display assertions, new artist authorities or existing image changes.

Receipts: `output/normandy-{muma,rouen,joconde}-{preview,apply,replay}-20260910/`.
Verification: `output/normandy-{before,preview,after,replay}-verification.json`.

- Three Node extraction tests passed (factual labels, grouped-object deferral,
  omission of essays/image URLs).
- New Go date/label/non-overlap tests passed.
- Go unit tests, full opt-in local integration suite and `go vet ./...` passed.
- Twenty-one real bounded API checks passed: museum counts, distinct keyset
  pages, Monet-or-Pissarro filtering, highlights, source-backed details, empty
  on-view results and unauthenticated visibility restrictions. Observed local
  responses were 3–87 ms; not a concurrency SLA or 10-million-row benchmark.
- No frontend changes or browser tests were needed for this data-only pass.

Nothing was committed, deployed, published or applied to Terraform/Google Cloud.

## Owner's added priority

Russian icons, Greek artists and Byzantine/post-Byzantine art are now explicit
project priorities in `AGENTS.md` and
[the dedicated source/model checklist](../../russian-greek-byzantine-priority.md).
The current named-painter/1100-onward importer does not yet cover anonymous
or earlier Byzantine material adequately. That gap is recorded, not claimed
fixed. No Russian/Greek/Byzantine works were imported in this Normandy batch.
