# Eighty additional museum guides — 11 October 2026

Requested: add 80 museum guides using the approved editorial approach, nine translations, illustrated entries, downloadable PDFs, reading links and the two static Artline portal cards. Production deployment was explicitly authorized in the guide request.

## Published scope

80 new guides across 24 countries, each with 20 distinct selected artworks: 1,600 artwork IDs with no repeats between the new guides. Together with the six existing guides this makes 86 guides and 1,735 artwork entries. Each guide has English, Russian, Italian, German, Simplified Chinese, French, Spanish, Portuguese, Japanese and Arabic editions and PDFs. The new batch contains 800 editions and 800 PDFs (23 pages each; 18,400 PDF pages).

These are editorial selections from documented collections, not a world ranking or a claim that the museums lack official guides. Official collection/visitor links remain in each guide. Holdings, loans, institution branches and present display are distinguished. Museum closures, travelling selections and fragile works receive relevant visit notes. No current-display assertion is inferred from a catalogue holding.

## Evidence and decisions

- `candidates.json` names the 80 institutions; `catalogue/` contains bounded read-only production exports. `selections/` retains original object metadata; `copy/` contains the individually written English prose. No local database or production catalogue records were changed.
- `sources/` preserves request receipts and retrieved bodies. Successful retrieval is not assumed for rate-limited or access-controlled pages. The selected object identity was checked against museum records and approved WikiArt references. Gated sources were supplemented with primary museum pages where available. Historical/excluded candidate receipts are retained, including rejected URLs; they are not all publication links.
- `field-overrides.json`, the named `*-guide-only-holdings.json` files, `selection-review-notes.json`, `guide-only-media.json` and `assembly/` record article-only corrections and object/version reconciliation. Source labels and original values remain in the exports. Artwork dates are not inferred from artist lifespans. Qualified/unknown creators remain explicit.
- Examples of resolved version differences: Van Gogh's 1888 Amsterdam Bedroom versus Chicago's 1889 canvas; Matisse's 1909 MoMA Dance versus the Hermitage's 1910 painting; Warsaw's smaller 1880 Chełmoński Four-in-Hand versus Kraków's 1881 canvas; the Smithsonian's 1872 carved Old Arrow Maker versus its earlier model. Stolen Gardner paintings and Rublev's Trinity after its transfer to the Lavra are excluded. The Phillips/PAFA and branch/loan distinctions are documented in the relevant guide.
- Fifty-two object entries have guide-only matches to existing artist records. `catalogue-link-repairs.json` records these. An explicit null `catalogueArtistSlug` sends the artwork link to the existing ID-based artwork view; the verified artist remains available in the lifespan diagram. This avoids claiming that a database creator relationship was written.
- `books.json` contains 17 reading resources. Each guide explains what its linked book adds. Access labels distinguish full texts, samples, digitized catalogues and availability-dependent scans. Historical books retain context about period terminology and viewpoint.

## Editorial and translation review

English entries use the editorial manual: visible details, a specific reason for inclusion, qualified attributions, and no invented narrative about what an artist felt. The selection describes paintings, drawings, sculpture, icons, scrolls and album leaves according to their object records.

Translations use the English edition as their source. `translation-receipts/` records model, source hash and final edition hash. Every edition was checked for completeness, preserved IDs/source evidence, matching work order, translated prose and valid text. Samples in all nine languages and qualified creator labels were reviewed. Corrections include preserving Flores as a person's name, replacing Japanese exhibition terminology where the text means this guide, and correcting the French Europa introduction. These are AI-assisted translations, not independently proofread by native speakers; the discreet label appears on the page and in the PDF.

## Verification

- `edition-validation.json`: 800 complete editions, 20 works each, evidence and identity preserved across translations.
- `image-http-validation.json`: all 1,600 selected image URLs returned HTTP 200 with image content types. Contact sheets for all 80 selections were visually reviewed before publication.
- `pdf-validation.json`: all 800 PDFs checked for 23 pages, text, artwork images, and object/book/portal links. PDFs fail generation on page overflow. Rendered samples cover all ten languages, long credits, reading pages and Arabic direction; final rendered pages were inspected.
- Unit/SEO tests, TypeScript, browser tests and deployment checks are recorded in the release receipt. Four existing lint warnings concern the guide's plain image elements; there are no lint errors in the changed runtime files.

Research is deliberately outside the publication folder. The guides remain file-backed content; no CMS was added. Release uses a generation-pinned, hash-verified overlay on the deployed web source. Only the new guide files, guide index, two artwork-routing files and a title-wrapping CSS correction are included. Existing six guides and unrelated shared-checkout changes are excluded from the overlay.

The expanded browser suite passed 87 tests initially. A Russian Minneapolis title
exceeded a 320-pixel viewport; adding title wrapping fixed it and the targeted
retest passed. A subsequent check of every new edition (800 pages at 320 pixels)
found no overflow, including RTL bounds. The other initial failure was the
Armenia portal against an unavailable local catalogue API; that interaction and
the guide-only creator artwork drawer are required candidate checks before
activation. This local dependency failure is not reported as a passing test.


## Source identifier compatibility found during candidate checks

The Rietberg diagram originally omitted Mei Qing, Hongren and Kuncan. Read-only
reconciliation found their existing `met-qid-Q…` artist IDs, while both URL and API
filters lowercased the Q. The same issue affected their direct artwork pages.
All 1,014 Met Wikidata-derived artist slugs in the production catalogue use the
uppercase-Q convention; no lowercase counterparts were found.

A small API compatibility patch restores this known source convention before
exact indexed lookups and keeps filter-choice values in the lowercase form used
by the interface. It preserves the source IDs, existing validation and selection
limits, with no database writes, schema changes or SQL predicate changes. The
HTTP API tests pass, including mixed-case lookup, bounded filters and malformed
input rejection. The guide release requires verification of all 80 exact artist
selections and all 1,600 artwork links against the API candidate.


The all-guide diagram check also exposed a conflict in Smithsonian object
F1909.245c (Landscape: pavilions on a mountain side; a stream below). The museum
names Ma Yuan, active around 1200, and dates the leaf to the sixteenth century.
The guide now states that conflict explicitly in all ten editions, preserves the
object, date, image and original credit, and leaves the creator attribution
unresolved instead of presenting an accepted Ma Yuan relationship. The artwork
opens through its ID; the diagram includes the other eleven linked artists.
See `field-overrides.json` and the primary Smithsonian collection record. The
ten PDFs were regenerated and revalidated, with corrected pages visually checked.

`api-diagram-validation.json` confirms exact artist selections for all 80 guides.
`api-artwork-link-validation.json` confirms all 1,600 artwork endpoints return
the selected ID. The API compatibility revision preserves runtime settings and
is deployed independently of the file-backed guide pages. A small content-only
web image layer applies the Smithsonian correction on the verified guide image;
it reuses the same compiled application and checks all 20 predecessor/output
hashes for the ten JSON/PDF pairs.
