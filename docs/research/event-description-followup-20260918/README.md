# Event description follow-up, 18 September 2026

Reviewed all **452** descriptions that still relied on Wikidata after the first
English Wikipedia pass. The priority was meaningful context for records with
only a generated classification-and-date sentence.

## Results

| Stage | Records |
| --- | ---: |
| Existing fallback records examined | 452 |
| Other-language article candidates | 386 |
| Introductions with matching Wikidata identity | 380 |
| English summaries reviewed and applied | **118** |
| Matched articles retained for further review | 262 |
| Redirects / unusable introductions excluded | 6 |
| No sitelink in the additional languages checked | 66 |

The applied descriptions draw on French (60), Russian (24), Spanish (16),
German (12), Dutch (2), Swedish (2), Polish (1), and Italian (1) Wikipedia.
They are English translations and adaptations, not English Wikipedia quotations.
Every detail panel identifies the source language, links the article and
CC BY-SA 4.0 licence, and labels the text “English summary.”

Local coverage now consists of **9,658 Wikipedia descriptions**, **334 Wikidata
descriptions**, and **8 retained editorial descriptions** backed by institutional
sources. All 10,000 events have text and attribution. Of the remaining 334,
296 have short English Wikidata descriptions and 38 still have basic descriptions
assembled from recorded classification and dates. More matched articles are
research leads, not completed English summaries.

## Evidence and judgment

`sources/` preserves compressed API responses, request parameters and retrieval
times. `matched-introductions.json` records article URLs, revisions, introductions,
languages and evidence filenames. Redirects must still resolve to the exact event
Wikidata identifier; a broader article is not substituted automatically.

`reviewed-summaries.json` contains the manually reviewed English text. Summaries
retain uncertainty, omit unsupported outcomes and avoid adding current claims.
Descriptions of violence remain factual and non-graphic. `content-review.json`
records source/date issues separately from the catalogue.

Two of the 120 matched basic descriptions were held: the Treaty of Windsor
record's chronology conflicts with its linked article, and the French Russian
constitution introduction contradicts itself. Other summaries use only supported
context where the article's date range differs or the introduction discusses a
broader agreement framework. Catalogue dates were not silently reconciled.

The previous corpus classification concerns remain in
`../event-descriptions-20260918/content-review.json`. This pass enriches existing
review records; it does not establish that every sourced entity is an appropriate
event or certify its historical importance.

## Reproduction and application

`ops/research-event-description-followup.py` has four stages: `authorities`,
`introductions`, `match`, `prepare`. The first two reuse cached network evidence;
the latter two reconstruct matches and the payload without network access.
`manifest.json` checksums the evidence and JSON artifacts, and identifies the
original payload used for the before-state comparison.

Application uses `cmd/enrich-event-descriptions` with `-count 118`. Each update
requires both the exact previous description and previous attribution. Conflicts
abort the complete transaction; replay is a no-op. Only `description` and
`descriptionSource` change, plus the corresponding source checksum. No events are
inserted or published.

Before application, the real event table was backed up to:

`/Users/vadimdulub/Library/Application Support/Artline/backups/events-before-description-followup-20260918.dump`

The local API was rebuilt and restarted with `default_transaction_read_only=on`.
The enrichment command uses a separate connection for its explicitly scoped
transaction; the browsing server remains read-only.

## Verification

- 118 descriptions applied; second application changed **0** rows.
- Read-only audit checked all 10,000 rows against the original import: historical
  metadata and review status unchanged; all description sources valid.
- Go Events and HTTP API tests passed, including expected-source reconciliation,
  unknown-field preservation, conflicting updates and language/host validation.
- Seven Python extraction/source-matching tests passed.
- Headless browser checks cover the translated source credit, English excerpts,
  retained fallback, licence links, description search and accessible drawers.

Disposable browser evidence is under `/tmp/artline-design-final/`, outside
Documents. No commits, deployment or publication occurred.
