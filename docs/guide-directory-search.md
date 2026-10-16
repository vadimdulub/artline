# Guide directory search

`/guides` searches public editorial guides by artist or museum name, title,
subtitle, city and country, including titles in the available translations.
Artist, museum and Using Artline filters share query-specific counts. Search
parameters stay in the URL, with canonical metadata pointing to `/guides` and
filtered URLs marked noindex/follow. Existing individual guide editions and
PDFs keep their URLs and sitemap entries.

Go owns matching, accent normalization, relevance, counts and cursor pagination
at `GET /api/v1/guides`. Next renders the initial bounded response and fetches
subsequent searches through the existing public read proxy. Each page contains
at most 24 summaries; the full search index is not sent to the browser. There
is no member gate and no database access in guide search.

After editing editorial indexes or guide editions, run:

```
python3 ops/build-guide-search-index.py
python3 ops/build-guide-search-index.py --check
```

The generated `apps/server/internal/guides/index.json` records SHA-256 source
hashes. Deploy its API image alongside the matching web editions; the release
checks those hashes against the selected web source. The immutable projection
is loaded once per process. Its digest invalidates cursors after content changes;
stale links offer a return to the first page. No separate cache needs clearing.
The small editorial index is scanned in memory and does not query artwork
collections. This is not a performance claim about the million-artwork catalogue.

Validation: Go race tests for search and HTTP packages; web typecheck; guide and
sitemap unit tests; `e2e/guide-search.spec.ts` covers URL restoration, filtering,
paging, translated searches, no results, retry and mobile accessibility.
