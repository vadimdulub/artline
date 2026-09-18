# Historical Events research and local delivery

Research started 17 September 2026; local import and verification completed
18 September 2026. User-confirmed cutoff: **2000**, inclusive.

The local personal preview contains **10,000 source-linked review records**,
including **100 unranked editorial starting points**, selected by default.
Nothing was published or deployed. This is a research catalogue, not a claim
that 10,000 narratives have each received independent scholarly verification.

Update, 18 September: all 10,000 records now have short attributed descriptions.
See [description enrichment](../event-descriptions-20260918/README.md). The counts
and payload below describe the original import, whose evidence is preserved.

## Collection

| Measure | Records |
| --- | ---: |
| Events | 8,768 |
| Historical periods | 702 |
| Movements | 530 |
| With a description | 9,592 |
| With country or historical-state tags | 7,236 |
| With a region mapping | 6,078 |
| With an established date envelope | 9,999 |

The First Buddhist council remains undated because the retained source does not
establish a date. It appears in the full-range index. All 100 featured entries
have descriptions and original editorial context explaining their significance.
The required French Revolution, world wars, Byzantine Empire, Columbus voyages,
and Reformation are included. Dates extend from 12000 BCE to 2000; no year zero
or CE suffix is used.

## Method and retained evidence

1. `top100.tsv` records the editorial selection, topic, type, and rationale.
   Titles were resolved through source identities and checked for redirects or
   ambiguous matches. `top-corrections.json` records the resulting corrections.
2. Wikidata class queries discovered historical candidates across 11 topics.
   Candidates needed documentation in at least three Wikimedia projects. A date
   prefilter narrowed the main pool; the 15,000 highest-documentation candidates
   were hydrated. Additional bounded subclass queries expanded expeditions and
   space missions. Top 100 identities were included independently of that rank.
3. Full source JSON, revisions, qualifiers, and query text are retained under
   `sources/`. Date processing respects source precision and uncertainty;
   alternatives produce an envelope, never an invented midpoint. Single known
   endpoints are identified as such. Fictional/calendar entities, unresolved
   chronology, and spans extending beyond 2000 are excluded from the wider pool.
4. The resulting 15,885 eligible candidates were selected by taking the editorial
   100 first, then cycling through available topics in documentation order until
   reaching 10,000. Source identifiers are unique; related wars, battles, and
   treaties may legitimately describe different aspects of the same history.
5. Country authorities come from the retained Wikidata claims. Existing Books
   authorities were reused with a recorded checksum. ISO-to-UN-M49 region mapping
   matches Books. Historical entities without that mapping remain unmapped.
6. `events.json` is the import payload; `selection-evidence.json` records source
   revisions and selection signals; `exclusions.json` records 2,022 exclusions.
   `manifest.json` has exact counts. `SHA256SUMS` covers 426 evidence/payload files.

The payload SHA-256 is
`44f9bf91f458a1b1bef6ce55efbda15cc14f3df1f3a49d95fda3b49ddbbeae5f`.

## Editorial checks

Additional institutional sources support corrections and context for the
[French Revolution](https://en.chateauversailles.fr/discover/history/key-dates/versailles-heart-french-revolution),
[Byzantium](https://www.metmuseum.org/essays/byzantium-ca-330-1453),
[Reformation](https://www.metmuseum.org/essays/the-reformation),
[Columbus voyages](https://www.loc.gov/exhibits/1492/about.html),
[First World War](https://www.theworldwar.org/learn/about-wwi/key-dates), and
[Second World War](https://www.nationalww2museum.org/war/articles/allies-world-war-ii).
Further sources include the Library of Congress for Gutenberg, NASA for Sputnik
and Apollo 11, the United Nations for Ghanaian independence and its Charter,
Egypt's Ministry of Tourism and Antiquities for Early Dynastic Egypt, and the
Stanford Encyclopedia of Philosophy for the Enlightenment. The corresponding
record stores the exact source links and explains editorial date conventions.

Columbus is described as sustained contact with existing American societies.
Gutenberg marks a European printing landmark, acknowledging earlier East Asian
printing. Sputnik and Apollo mark their launch/landing, not an invented mission
duration. Byzantine and Roman imperial endpoints are explained as periodisation
choices. World-war geographic tags were checked against museum accounts and
explicitly distinguish modern browsing labels from historical borders.

## Limitations

Documentation frequency is a discovery signal, not historical importance.
English labels and direct source classes introduce coverage bias. Conflict still
accounts for 3,829 records, while economics has 29. Other topic totals appear in
the manifest; multi-topic totals may overlap. The collection is not geographically
or thematically exhaustive. The Top 100 is open to editorial revision.

Countries, places and participants are partial. Modern locations and historical
states coexist, and regions are mapped only when supported. Missing metadata
does not authorize inference. Short source descriptions can use different date
conventions from structured claims; source evidence and date-basis notes remain
available for review. All records retain `review` status.

## Local safety and validation

A full pre-import database backup was created and its archive table of contents
checked at:
`/Users/vadimdulub/Library/Application Support/Artline/backups/artline-before-events-20260917.dump`.
Migration `0022_events_catalogue.sql` added the event table. The importer validated
exact counts, unique identities, source revisions, HTTPS links, review status,
and date bounds, then inserted all 10,000 records in one transaction. It refuses
changed/partial imports and never overwrites or publishes catalogue records.

The real database was audited with a connection forced to read-only. All 100
bounded keyset pages were traversed without gaps or duplicates. Required examples,
date overlaps, filter suggestions, density counts, and public visibility checks
passed. Representative selections included France (504), 1700–1800 (858),
1939–1945 (824), and BCE (700). The non-preview API returned no review records.

Representative `EXPLAIN (ANALYZE, BUFFERS)` checks used the Top 100 index and the
country/date indexes. Observed execution times were 0.073 ms for the Top 100 ID
page and 0.307 ms for France/1700–1900 IDs on this local database. These are warm
10,000-record observations, not evidence of performance at 10 million rows.
No fixture or test database was created. Load testing at larger scale remains
separate work.

Replaying the exact import returned “Identical event records already present;
no changes.” Go tests, seven chronology research tests, the Next.js production
build, and ESLint passed. Eighteen headless Chrome scenarios passed across Events
and the shared year controls (one error-recovery assertion was scoped to the
application alert before its successful rerun). Checks covered 1440/390/320px
layouts, keyboard focus, drawer accessibility, axe WCAG checks, BCE and invalid
years, the 2000 cutoff, mouse/touch dragging, filter combinations, real API counts,
pagination, reload, and browser history. Existing Books/author layout regressions
also passed. Desktop and phone screenshots were visually inspected. Disposable
screenshots and traces remain under `/tmp/artline-events-ui` and
`/tmp/artline-events-recovery`; no browser window was shown.

Implementation and shared-component details: [Events design](../../events-timeline.md).
