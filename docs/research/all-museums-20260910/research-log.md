# Museum registry and catalogue expansion — 10 September 2026

## Scope and result

This is a local, metadata-first continuation of the owner's request to expand across known museum catalogues. It is not a complete census of world museums or their holdings. The retained scope is museum-connected paintings, drawings and prints, assigned conservatively to existing artist authorities, with source-supported creation dates no later than 1970. Unknown/ambiguous/cross-cutoff dates, ambiguous authorship and unresolved physical-object identities are deferred. No automatic masterpiece designation, publication, ownership or current-display claim is made.

Verified result: **41,648 artworks added**, from a baseline of 63,073 to **104,721**. There are still 5,315 artists and 230 media assets; institution/collection rows increased from 280 to 294. These rows are not necessarily distinct physical museums. All new works remain unpublished review records and pass the creation cutoff. Two preexisting date-review records remain unchanged.

Current types: **13,737 paintings, 32,005 drawings, 58,974 prints and 5 frescoes**. This wave added 3,752 paintings, 7,872 drawings and 30,024 prints. These are not 104,721 validated masterpieces. Receipts matched 241 existing artworks rather than duplicating them; one Cleveland record received a missing-field enrichment.

| Source | Captured records, all included source types | Selected | Actually new | Matched existing |
| --- | ---: | ---: | ---: | ---: |
| Metropolitan Museum of Art | 484,956 | 21,309 | 21,196 | 113 |
| Cleveland Museum of Art | 68,778 | 9,887 | 9,835 | 52 |
| Lombardia regional catalogue, outside the previously processed Milan subset | 54,488 | 323 | 323 | 0 |
| Art Institute of Chicago | 134,078 | 10,370 | 10,294 | 76 |

Raw-source totals are not new database artworks: they include out-of-scope objects, unresolved creators, dates after 1970, duplicate/compound identities and already represented records. They must not be advertised as imported counts.

## Museum/source register

The inherited directory has 5,869 source rows: 4,542 Wikidata discovery candidates, 1,216 official Muséofile entries and the supplied 111-source registry. Sources overlap; some entries are collection organizations or mixed-subject museums. Wikidata discovery is not official collection evidence. The earlier Italy discovery partition failed and remains a coverage gap.

The baseline reconciliation produced 5,923 register rows, mapping all 280 baseline institution rows either through an exact authority/source identifier, an explicit source alias, or a separate local entry. No fuzzy institution mergers were performed. The final export contains **5,937 overlapping source/register rows**, mapping all 294 institution/collection rows and preserving their exact current counts. A null count means unmapped, **not zero**; counts repeated on linked source rows are not additive.

One HEAD request was made to each of the 111 supplied catalogue routes, without redirects or credentials. Responses: 59 reachable, 13 redirect-review, 23 access-restricted/no-retry, 10 route-unavailable, and 6 unavailable/review-required. No 403/429 access controls were bypassed. HEAD reachability is neither permission to ingest nor a measurement of catalogue completeness. For example, a stale/unsupported catalogue route does not invalidate a separately documented official bulk export.

Files: `access-summary.json`, individual `access/*.json`, `museum-register-before.json/.csv`, and final `museum-register-after.json/.csv`. The optional spreadsheet rendering tool was unavailable (`sandboxPolicy` initialization error), so the deliverable is CSV, not an unverified Excel workbook. Spreadsheet-oriented safeguards keep identifiers textual, quote cells, neutralize formula-leading values and distinguish unknown coverage from zero. JSON preserves the original identifiers and data types.

## Primary source evidence and reuse

### Metropolitan Museum of Art

[Official Open Access repository](https://github.com/metmuseum/openaccess) supplies CC0 collection metadata. The captured Git LFS CSV is pinned to repository revision `6fa206f0df6cf349d4fe558028d4c08e95f44eb6`; bytes 317,650,992, SHA-256 `de617b9c947458e426111207f81a65bd1379a151c0077d3ce29cfc22fc0b9183`.

Only exact painting/drawing/print classifications were selected. Qualified/multiple creator records were deferred. Source Wikidata identifiers are used only when they resolve to existing local authorities and do not contradict known names/lifespans; fallback is unique full-token name matching, never surname/fuzzy matching. Every member of a shared-accession group is deferred, even if one member is outside the eligible subset. Physical groups, ambiguous date literals and incompatible artist lifetimes are excluded.

Selected types: 1,936 paintings, 4,644 drawings, 14,729 prints. The initial v1 selection was previewed but never applied; v2 corrects shared-accession handling. As a live-source spot check, [Rembrandt, Saint Jerome Reading](https://www.metmuseum.org/art/collection/search/334627) confirms the selected creator, 1634 date and accession 1994.110.1. Public-domain image status was not used to trigger an image download.

### Cleveland Museum of Art

[Official Open Access repository](https://github.com/ClevelandMuseumArt/openaccess) and [official API](https://openaccess-api.clevelandart.org) document the full metadata export and its CC0 terms. Captured revision `0abfbf9c4217696d3abd600b8623118e6cd5598b`; bytes 343,476,981, SHA-256 `0c15cb6b3b195e69f901af00fbd5205697c4fca50049196d4d232fa8af08fc94`.

Exactly one unqualified artist is required, with a unique existing authority match. Related/grouped objects and compound inventories are deferred. Literal creation dates must agree with numeric date fields. v1 failed an evidence-field date-format check before any public write; v2 stores a date-only update field and preserves the original timestamp in raw evidence. Selected types: 660 paintings, 1,082 drawings and 8,145 prints. The official [Monet record, 1916.1044](https://www.clevelandart.org/art/1916.1044) was checked directly by HTTPS; its creator, 1888 date and accession matched the export. The research web reader could not retrieve that page, so this is a direct-fetch check, not a successful web-reader result.

### Lombardia regional catalogue

[Official dataset metadata](https://www.dati.lombardia.it/api/views/ay8b-p38f.json) declares CC0 and supplies the SIRBeC object export. Dataset update timestamp was 7 September 2026. A bounded, ordered request captured all 54,488 rows for the requested painting/drawing/print/watercolour labels: 15,643 paintings, 38,509 drawings, 332 prints and four watercolours. This is a filtered parent export, not every record in SIRBeC.

Milan's 36,350 source rows were deferred because that subset was processed in the preceding campaign. A reviewed, exact 27-name/city institution crosswalk produced eligible works for 14 additional institutions. Qualified authorship, shared national catalogue identities, grouped objects and uncertain institutions were not promoted. The [Ceresa attributed work](https://www.lombardiabeniculturali.it/opere-arte/schede/C0050-00001/) was inspected and excluded because its source attribution is qualified.

Selected types: 309 paintings and 14 drawings. Source institution fields document museum connection, not ownership: a GAMeC record mentions a historical deposit and another owner in its narrative, so those facts remain unresolved review evidence. An attempted live Monza object check returned 502; it is not counted as a successful page validation. Official dataset evidence is retained separately.

### Art Institute of Chicago

[Official API documentation](https://api.artic.edu/docs/) and [official API data repository](https://github.com/art-institute-of-chicago/api-data) identify the bulk archive route. Using the bulk export avoids excessive per-object API requests. An initial full download timed out. One bounded recovery downloaded 115 sequential ranges from the same public object, respecting a one-second interval and verifying consistent ETag, content ranges and each part's checksum. It did not work around authentication or a 403/429.

Final archive: 119,891,546 bytes, SHA-256 `97e77e71e29721251c15eae35e294358c7aa44fb5953013370a0488eb41a9fa0`, ETag `"2a4a6375ca842dc45f171d91fec44f1e-23"`. **The object's Last-Modified is 16 February 2025**, despite current documentation discussing periodic exports. Retrieval on 10 September 2026 is not evidence that its records or display flags are current.

The streaming reader examined 134,078 artwork JSON records without extracting archive paths or executing its included Git hooks. Candidate types: 3,944 paintings, 14,769 drawings/watercolours and 46,353 prints. Other resources, photos and architectural drawings are outside this selection.

The archive's `json/info.json` explicitly assigns **CC BY 4.0 to the artwork `description` field and CC0 to its other artwork metadata**, subject to [source terms](https://www.artic.edu/terms). This is checked before selection and preserved in `chicago-v1/artworks-license.json`. The 10,370 selected works include 1,020 paintings, 2,179 drawings and 7,171 prints; 1,231 have source narrative descriptions. Included narratives retain source wording, strip HTML formatting, and carry Art Institute of Chicago attribution, object links, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) and an adaptation notice. No image rights are inferred from metadata licensing. An official website object request returned 403 and was not retried.

## Data protection and verification

Pre-write public-schema backup: `/Users/vadimdulub/Documents/artline-all-museums-backup-20260910.c3iw6D/before-campaign.dump`. SHA-256 `44538cbca7b28b5f35608e70f876368fa92d0005c6ff1bb35d5afb43f77a3a2d`; archive listing is readable (251 lines), **not restore-tested**.

Imports are local-only and offline; only reviewed checksum-pinned manifests can run. Each chunk contains at most 500 works and is a serializable transaction with an advisory lock. An earlier completed chunk stays committed if a later chunk fails; immutable receipts and idempotency keys support safe resumption. Exact source identity/URL and institution+accession reconciliation are used, never title-only merges. Existing editorial values and intentional clears are preserved. No new artist authorities were created.

All **85 final-selection chunks** passed full rollback previews, then apply and unchanged replay. Fingerprints of 15 tables matched exactly across previews and replays. Source receipts distinguish actual new works from reused records and confirm no added highlights. Every newly created work has a nonempty description, eligible creation range, review status and no publication timestamp. No current-display assertions exist, and the existing media/rights records and artist authorities were preserved.

Final verification completed:

- `ARTLINE_TEST_DATABASE_URL=... go test ./... -count=1` and `go vet ./...` passed, including all seven reviewed continuation sources and Chicago attribution/description/date unit tests. Integration fixtures use disposable schemas or rolled-back transactions.
- All three opt-in query-plan tests passed on 100,000-row isolated fixtures. Artist chronology counts/page used indexed painter links (1.234/0.941 ms core SQL); the museum-scoped query used an artwork index (2.701 ms core SQL); source identity reconciliation used all three exact-identity indexes with no sequential scan. Fixture construction is outside those query timings. These are not production concurrency or 10-million-row tests.
- **31 authenticated/unauthenticated API requests** verified museum counts against SQL, five-item keyset pages without overlap, details, Monet/Pissarro multi-selection, withheld long prose on list payloads, Chicago licence attribution, 401 on unauthenticated preview and 404 on an unpublished museum's public route.
- An initial API assertion incorrectly assumed the oldest Met seed record had a description. Direct SQL proved it was a preexisting null description, not a failed new import. The check now compares exact API/DB values for existing records and explicitly checks descriptions on newly created works; no text was fabricated to satisfy the test.
- Independent Ruby CSV parsing checked **all 5,937 rows × 13 columns** against the JSON export, including identifiers, quoted fields and blank unknown counts.

Evidence: `output/campaign-final-summary-20260910.json`, `output/campaign-final-api-verification.json`, `output/campaign-{initial,chicago}-{before,preview,applied,replay}*-verification.json`, and `output/campaign-{met,cleveland,lombardia,chicago}-{preview,applied,replay}-20260910*/`. `receipt-summary.mjs` reconciles actual receipts and CSV cells; it performs no database writes. The corrected Met full preview is the `-v2` directory/verification, not the superseded v1.

## Remaining coverage

- The four-source wave is complete. The registry-wide collection effort is not: only a small fraction of source routes have implemented, reviewed adapters.
- For a concrete coverage gap, the final local database has only 13 Louvre and 21 Prado works. Their full collections have **not** been imported; those catalogue-specific adapters remain priorities.
- Catalogue-specific adapters and authority reconciliation remain necessary for most registry entries. A reachable landing page is not a usable complete object feed.
- Continue official French/Italian/Russian catalogue adapters and additional US/European bulk sources where documented reuse and collection identity permit. Existing Louvre, Prado, Hermitage and other coverage must not be described as exhaustive.
- Retain qualified creators, uncertain dates, deaccessions, related physical units and missing authority matches for explicit editorial reconciliation; do not increase totals by weakening these gates.
- Rights-cleared representative images are a separate selected workflow. No new image downloads, current-display refresh, publication, commits, Terraform apply or deployment occurred in this campaign.
- This work does not establish 10-million-row or concurrent production performance. Fixture plan checks and local API response tests are narrower evidence.
