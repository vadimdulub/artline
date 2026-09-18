# Historical books — September 2026

Requested scope: 10,000 books and foundational literary works, including ancient,
religious and philosophical texts. The user confirmed that books from any year
may be included. All imported records stay in **review**, visible in the local
research preview. This is a sourced discovery collection, not a claim that a
universal or academically validated list of the 10,000 most important books exists.

## Selection

The candidate pool combines Wikidata's literary-work and written-work records,
ranked by `wikibase:sitelinks`. Queries were bounded to 12,000 results per class,
with at least 3 sitelinks; the combined pool retains the highest-ranked 14,500
identities with at least 5 links. The original 17 editorial selections are kept.
Additional eligible records are selected by descending sitelink count, with a
stable numeric Wikidata ID tie-break, until the collection contains 10,000 records.

Eligibility requires an English display label and either a literary-work
classification or an Open Library **work** identifier. Explicit editions,
translations, series, periodical/scientific articles and screen works are excluded.
Future-dated works are excluded when their source dates all exceed 2026.
Formats and cultural origins are not exclusion criteria. Identical titles by
one author can describe different stories, collections or plays; these are not
silently merged. Wikidata work IDs are the identity key. Exclusions are retained.

Sitelinks indicate documentation across Wikimedia projects; they are **not**
sales, readership, historical influence, a count of Wikipedia languages alone,
or an expert quality score. This selection inherits Wikidata's coverage and
English-label biases. Further editorial work is needed to assess balance across
traditions and verify influence, identity, dating and attribution.

## Sources and dates

Structured metadata comes from [Wikidata](https://www.wikidata.org/wiki/Wikidata:Data_access)
under its [CC0 terms](https://www.wikidata.org/wiki/Wikidata:Licensing).
The research fetch uses `wbgetentities` batches of at most 50, with caching,
retries and backoff for rate limits. It downloads metadata only. No book text,
historical cover or artwork reproduction is downloaded.

`sources/*.json.gz` preserve response bodies, source claims and references.
`candidate-ranking.json` records discovery scores; `excluded.json` records
rejected candidates. `manifest.json` records checksums, retrieval completion,
counts and source filenames. `books.json` is the prepared review import.
Source revisions are retained where returned; early response batches did not
request revision info and remain identifiable by their saved response checksums.
Every imported work and creator links to its Wikidata source identity.

Work dates prefer recorded inception/composition (`P571`), then the earliest
recorded publication (`P577`). This does not establish a verified first edition.
Creator lifespans come from birth/death claims (`P569`/`P570`), with alternatives
and approximate labels retained. Century, millennium and decade precision use
full intervals; qualifier uncertainty is retained. See
[Wikidata's date model](https://www.wikidata.org/wiki/Help:Dates).
No usable work date means a null interval and no timeline placement. The original
17 editorial date ranges are preserved with their existing composition/publication
basis. Biography text is a source description, not a newly invented biography.

The Dhammapada's existing traditional attribution is linked to the Buddha's
source record with an explicit traditional-credit label. Collective attributions
such as the Bible's have no single lifespan. These links do not resolve disputed
authorship or chronology and do not authorize publication.

## Storage and checks

The additive book schema is separate from artwork tables. The local schema and
migration ledger were backed up in Artline's designated backup folder before
applying migration 0020. The importer validates the prepared records, inserts
them atomically in review and does not run migrations or publish content.

Browser fixtures are confined to the test runner. Real catalogue audits use
read-only connections and never insert fixtures or create test databases.
The completed local import and audit are recorded in `verification.json`:

- 10,000 distinct source identities, all in review; no published books.
- 4,092 creators and 9,988 work/creator credits.
- 103 works with BCE starts; 2,910 dated after 1970.
- 1,566 works have no usable date and remain unplaced on the graph. The Undated
  filter includes undated sacred works as well as the ordinary Undated grouping.
- All 100 keyset pages were checked for completeness, order and duplicates.
  All 42 full-range period counts agree with their drilled-down views.
- Public reads cannot expose these unpublished records. Identical import replay
  made no changes. No database fixtures were created or inserted.
- 14 browser regression cases and 2 live catalogue cases passed, along with
  Go checks, Python date checks, frontend lint and the production build.

`query-plans.sql` reproduces read-only EXPLAIN ANALYZE checks against the real
collection. Saved plans show the chronology index on bounded first pages and
indexed foreign-key lookups for creator enrichment. The author filter still
scans chronology entries; aggregate density examines the matching collection.
The final local samples took approximately 0.8 ms for the first page, 19 ms for
the author-filtered page, 0.08 ms for a two-book creator batch and 156 ms for
density. These are single local samples during test activity, not latency
guarantees or evidence for millions of books. Larger-scale search and aggregate
load tests remain necessary before expansion.

To regenerate from the saved candidate pool:

```sh
python3 ops/research-historical-books.py --candidates docs/research/historical-books-20260916/sources/ranking-combined.json.gz
```

This reuses saved response bodies and fetches only missing sources. Database
imports remain a separate, explicit `cmd/import-books -apply` operation.
