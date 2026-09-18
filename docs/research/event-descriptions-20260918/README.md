# Short event descriptions

Requested 18 September 2026: add a short sourced description to every event.
Scope is the existing 10,000 local review records; historical dates, selection,
filters, and publication status are preserved.

Completed locally: **10,000 descriptions**, comprising **9,540 Wikipedia
excerpts, 452 Wikidata-based descriptions, and eight original descriptions based
on institutional sources**. All 408 previously empty descriptions are filled.
Of the Wikidata fallbacks, 156 are assembled from recorded classification and
dates; 296 use the retained English Wikidata description. The longest prepared
description is 839 characters. Four unusually long opening sentences use a
word-boundary ellipsis.

The payload checksum is
`c942e140ac2068153c120f8ce26991fe58bab573209ed62d1d2d0cc843e56228`.
`SHA256SUMS` covers 487 source and preparation artifacts.

## Sources and preparation

`ops/research-event-descriptions.py fetch` retrieves introductions for the 9,645
existing English Wikipedia links, in sequential batches of at most 20. It uses
the [TextExtracts API](https://www.mediawiki.org/wiki/Extension:TextExtracts), with
plain text, lead-only content, a 1,000-character source limit, cached responses,
`maxlag`, a descriptive user agent, and retry backoff. No article images or full
article bodies are downloaded. Source snapshots include request parameters,
retrieval time, article revision, and the article's Wikidata identity.

`compile` requires the fetch to be complete. An introduction is accepted only
when its Wikidata identity matches the event exactly and the article is not a
disambiguation page. Redirects to broader topics are recorded in `issues.json`
and excluded from automatic excerpting. List-navigation openings are also
excluded. Introductory text is shortened to at most two complete opening
sentences when possible; long openings receive a word-boundary ellipsis. The
normal limit is 850 characters. Paragraph spacing is normalised, while the
source wording is otherwise preserved. Tests cover abbreviations, initials,
parenthetical dates, truncation, and missing content.

Eight original descriptions based on institutional sources are retained,
including Byzantium, the Reformation, Columbus, Gutenberg, Sputnik, early Egypt,
Ghanaian independence, and the French Revolution. These carefully explain the
specific event being displayed. Their source credit is shown below the text.

Where an exact Wikipedia introduction is unavailable, use the retained Wikidata
description. For records without either, assemble a basic description from the
explicit source classification and date envelope. These are labelled as based
on Wikidata metadata; no participant, cause, outcome, or significance is guessed.
Final source counts and the exact payload checksum are in `manifest.json`.

There were 96 article identity mismatches and one list-only introduction. They
received Wikidata fallbacks. The article text also flagged 30 existing records
for classification review (for example, military units or references to
mythological subjects). `content-review.json` retains those flags. Enrichment
does not independently validate the original selection or silently reclassify
these records; they remain in review.

## Attribution

Each description has structured provenance in `descriptionSource`. Wikipedia
excerpts link to the article and credit its contributors, indicate shortening,
and link to [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Wikidata descriptions identify their source and
[CC0](https://creativecommons.org/publicdomain/zero/1.0/). Original Artline prose
links to the institutional source used for its facts. These credits follow the
[Wikimedia reuse terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use#7._Licensing_of_Content).
Only the excerpted text is reused; no Wikipedia images or branding are included.

Descriptions are stored in PostgreSQL and rendered by the existing event drawer.
Opening an event makes no request to Wikipedia. Search uses the stored
description through the existing generated search column. The browser continues
to receive bounded event pages.

## Apply and audit

The importer at `apps/server/cmd/enrich-event-descriptions` validates the full
payload before connecting to the database. With `-apply`, it updates only
`description`, `descriptionSource`, and the record checksum in one transaction.
It requires existing review records and the expected prior description, refuses
to overwrite conflicting provenance, preserves unknown JSON fields, and makes an
identical replay a no-op. No event is inserted or published.

The pre-change event table backup is:
`/Users/vadimdulub/Library/Application Support/Artline/backups/events-before-descriptions-20260918.dump`.
Its archive table of contents was checked. The original import payload and its
research evidence remain unchanged in `../historical-events-20260917/`.

The opt-in `TestReadOnlyEventDescriptions` audit forces a read-only connection,
checks all 10,000 descriptions and their attribution, and compares every other
JSON field against the original import evidence. Unit tests separately prove
conflict refusal, preservation of unknown metadata, unsafe-source rejection,
and idempotency without inserting test fixtures into the catalogue.

Hidden Chrome checks cover the description and licence links on desktop and
phone, the metadata fallback, description search, and drawer accessibility.
Test screenshots and traces are kept under `/tmp`, outside the research folder.

Completed checks: the real read-only audit verified all 10,000 descriptions and
proved that every other historical JSON field matches the original import.
Replaying the update changed zero rows. Go tests, six extraction tests, the web
production build, ESLint, and all 11 headless Chrome scenarios passed. Desktop
and phone screenshots were inspected. No public deployment was performed.
