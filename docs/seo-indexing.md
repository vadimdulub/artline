# Search indexing and public release

Implemented and deployed on 20 September 2026 after explicit authorization.
See [the deployment record](deployment-20260920-seo.md) for live revisions,
verification, backup and rollback details. Production migration 0026 is applied;
no records were published, and no Search Console submission or domain purchase
was performed. The local catalogue was accessed read-only.

## Publication is the current launch dependency

A read-only audit of the real local catalogue found 23,286 active artists,
276,977 active artworks and 860 institutions, all in `review`; none were
published. These are local counts, not a claim about production. The documented
Cloud Run website returned 200 for `/`, but 404 for `/robots.txt` and
`/sitemap.xml` before this change.

Research visibility does not confer publication approval. The new discovery
queries only select `published` records, even when public preview or an editor
token is enabled. No statuses, source evidence, uncertain dates, creator labels,
museum holdings or artwork assets are changed by this work.

Pages containing the public research preview have `noindex, follow`. In preview
mode, the sitemap contains only `/about` and the informational `/artists`
directory; the directory does not advertise review profiles. In public release
mode it pages through published artists. Editorial pages inherit `noindex`, and
both the Go API and the web API proxy send `X-Robots-Tag: noindex`.

Do not remove these exclusions to make review material appear published. Use
the existing explicit validation/publication workflow, including creation-date,
selection, source and image-rights checks. Then turn off public research preview
on both services for a published-only launch. If review access must remain on the
public production host, separating a published view from the research preview
is additional backend visibility work; do not grant crawlers different content.

## Domain and webmaster configuration

`ARTLINE_SITE_URL` is the canonical origin for metadata, structured data,
robots and sitemap URLs. It is read at runtime, accepts an HTTP(S) origin and
rejects paths, credentials, queries and fragments. Until the owner selects a
domain, its fallback is the documented Cloud Run address. No proposed domain
has been installed as the real canonical origin.

The owner's naming shortlist is **Artline Atlas** (`artlineatlas.com`) and
**Artchrona** (`artchrona.com`). Both .com registry RDAP lookups returned 404 on
20 September 2026, meaning no registration record was found; this is not a
guarantee of registrar availability or price. The website remains branded Artline.

After purchasing and connecting the domain:

1. Set `ARTLINE_SITE_URL` to its final HTTPS origin. Terraform exposes `site_url`
   and maps it to the web service; this does not configure DNS or TLS itself.
2. Choose one preferred hostname. Configure permanent redirects for HTTP and
   the alternate www/non-www hostname as part of the domain setup. Existing
   Cloud Run pages will point canonically to the configured domain.
3. Verify domain ownership in Google Search Console and Bing Webmaster Tools.
   DNS verification works independently of the application. Optional HTML
   tokens use `ARTLINE_GOOGLE_SITE_VERIFICATION` and
   `ARTLINE_BING_SITE_VERIFICATION` (Terraform variables
   `google_site_verification` and `bing_site_verification`). These are public
   ownership tokens, not account credentials.
4. In an explicitly authorized release, deploy the backend and web changes
   together, including migration `0026_search_discovery_indexes.sql`. No
   migration was applied locally during this task. Keep public preview settings
   aligned across the two services.
5. Submit `https://YOUR-DOMAIN/sitemap.xml` to both webmaster tools and inspect
   `/about`, a published artist, an artwork and a museum. Check rendered HTML,
   the selected canonical, response status and Google indexing exclusions.
   Review Google Search Console's generative AI inclusion settings as applicable.
6. Monitor indexed pages, crawl failures, Core Web Vitals, search impressions and
   queries. Sitemap submission and structured data cannot guarantee indexing,
   rankings or citations in AI answers.

## What the implementation provides

- Distinct descriptions and canonical URLs for public routes, artist profiles,
  individual artworks and museum pages. Filter variants consolidate to their
  base route; directory cursor pages have their own canonical URLs.
- Artwork-specific H1s, Open Graph/Twitter metadata and safe JSON-LD describing
  published artworks, artist profiles, collections, breadcrumbs and the website.
  Non-primary attributions never become definite `creator` claims. Source date
  labels are not converted into invented ISO dates or lifespans. No display or
  ownership claims are inferred from a museum reference.
- Complete artist biographies and selected artwork descriptions in the initial
  HTML. Museum names and collection descriptions render on the server. Artwork
  detail pages fetch one complete record, including works beyond the ten
  representative cards. Image alt text falls back to the recorded title.
- A server-rendered artist directory, 60 entries per keyset page, with ordinary
  links. Artist pages link directly to their selected artwork records; legacy
  `?work=UUID` links redirect permanently to the artwork route. Invalid works
  return 404, and old artist slugs redirect to their resolved canonical slug.
- `robots.txt` permits public crawling for search and AI user agents, including
  scripts and assets needed for rendering. Review/editorial pages stay crawlable
  so compliant crawlers can see their `noindex` directives. Robots rules are not
  access control and cannot force any crawler to comply.

The current strategy follows [Google's AI search guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
and [Bing's sitemap guidance for AI search](https://blogs.bing.com/webmaster/July-2025/Keeping-Content-Discoverable-with-Sitemaps-in-AI-Powered-Search):
make useful, sourced content discoverable through ordinary search infrastructure.
Google states that special AI text files are not required for its search features.

## Sitemap bounds, performance and invalidation

The root `/sitemap.xml` is an index. Child documents are served at the same root
level (`/sitemap-pages.xml`, `/sitemap-artists-abc.xml`,
`/sitemap-artworks-abc.xml`, `/sitemap-museums-abc.xml`) to avoid directory-scope
ambiguity. URLs are absolute and XML-escaped. They exclude editorial endpoints,
filters, aliases and unpublished records. `lastmod` is intentionally omitted:
an entity's own timestamp does not reliably capture changes to related images,
citations or essays. A timestamp will need a proper invalidation projection
before it can honestly represent those updates.

Go selects occupied ranges by jumping between the first three hexadecimal UUID
digits using index seeks: at most 4,096 ranges per entity type. It does not fetch
or sort the entire artwork catalogue. Each shard caps source rows at 10,000 and
detects overflow with a bounded 10,001-row probe; overflow fails instead of
silently omitting records. Only the selected artwork IDs join to their creator
links. A deterministic published creator is chosen once for a work with several
attributions, preferring a primary attribution. Creator entity type is not a
filter, so published anonymous masters, workshops and collectives remain eligible.
Object-level creators without a published artist route need a separate public
artwork route before they can be added; their records remain intact.

Partial published-ID indexes and a published artist-slug index are defined in
migration 0026 and deployed in production. The API and sitemap handlers currently use `no-store` so an
unpublication or rename is visible on the next crawl request without a stale
application cache. Backend failures return 503 with `Retry-After: 60`, never a
successful empty sitemap. No external cache or search-index projection was added.

At 10 million uniformly distributed artwork UUIDs, a three-digit range averages
about 2,441 records; this is a planning estimate, not measured production scale
or a guarantee against skew. Before reaching that load, benchmark published-ID
indexes with representative publication ratios and attribution fanout, test
concurrent crawlers and Cloud Run memory, and check occupied-range skew. Split
oversized shards or introduce an explicitly invalidated sitemap projection when
the metrics justify it. Changing shard limits must preserve complete coverage.

Read-only `EXPLAIN (ANALYZE, BUFFERS)` on the actual 276,977-review-artwork
catalogue confirmed primary-key index scans for the same range/seek shape
substituting `review` solely to exercise populated data. The `abc` range returned
56 rows in about 228 ms on its initial read; the occupied-range traversal returned
4,096 prefixes in about 545 ms. These measurements do not test migration 0026's
then-unapplied local indexes or prove 10-million-row performance.

Books, events and atlas filter results still primarily use interactive APIs.
Their route metadata is improved, but dedicated book/event detail URLs and a
server-rendered browse hierarchy are future content-discovery work. Keep that
work bounded and governed by backend publication policy.

## Verification

- Frontend lint, TypeScript and production build.
- Frontend unit suite: 159 tests passed, including new domain, preview, JSON-LD, XML and sitemap
  failure tests. The linked-artwork test now checks the page's H1 explicitly.
- Go catalogue and HTTP tests with `ARTLINE_TEST_DATABASE_URL` unset.
- `TestSEOPublishedDiscoveryReadOnly` against the real database inside a
  read-only transaction. Mixed publication/attribution cases use inline SQL
  `VALUES`, without creating tables, inserting records or making a test database.
- `e2e/seo-readonly.spec.ts` checks the built site with JavaScript disabled:
  robots and sitemap discovery, canonical URLs, preview/editor exclusions,
  artwork description HTML, redirects, missing-work 404s and museum headings.
  All four browser checks passed, including navigation with JavaScript enabled
  and verification that the canonical URL and title update with the selected work.
  It is opt-in via `ARTLINE_SEO_EXPECTED_ORIGIN`. Test server databases use
  `default_transaction_read_only=on` and `-skip-migrations`; no editor token.
  Disposable browser outputs are under `/tmp/artline-seo-browser-results/`.
- Terraform formatting and configuration validation passed; no plan or apply.
