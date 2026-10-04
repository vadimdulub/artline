# Search indexing and public release

## Reviewed collection launched — 3 October 2026

The user approved the first ten artist profiles and their public launch. The
[artist directory](https://artlines.org/artists) now links ten sourced profiles
and fifty reviewed artwork pages. Those pages render published content only,
carry canonical URLs and indexable metadata, and are included in the public
sitemap, which contains 63 URLs including the existing informational pages.
Research preview remains available separately and retains its `noindex` rules.
The work-account verification tag is preserved. Google indexing of the new
pages has not yet been confirmed. See the
[public collection release receipt](deployment-20261003-public-collection.md).

The local database was read-only. Publication updated the exact approved
production records through the existing validation gate; all other research
remains in review. The user deferred new guides and promotion.

## Organic traffic audit — 2 October 2026

The public homepage at `https://artlines.org/` returns `noindex, follow`.
Before this release, `/sitemap-pages.xml` listed only `/about` and `/artists`, both using
the custom domain. This was consistent with research-preview mode, which
intentionally excludes the catalogue from search. The owner confirmed that a
custom domain exists but Google Search Console was not yet set up. No search-traffic,
ranking or indexing-account data was available for this audit.

Improvements deployed on 2 October after the owner's “ok do it” instruction.
See [the release receipt](deployment-20261002-seo.md). Live guide:
<https://artlines.org/art-history-timeline>.

The deployed changes include:

- `/art-history-timeline` is a server-rendered introductory guide with useful
  routes through artists, artworks, museums, books and events. It has its own
  title, description, canonical and breadcrumbs. It contains no unpublished
  catalogue records and is included in the public sitemap during preview.
- The footer, About page and artist directory link to the guide with ordinary
  crawlable links. The existing layout and mobile styles are reused.
- Pages using the shared metadata helper have a 1200 × 630 branded PNG at
  `/share-image`. Permitted artwork-specific sharing images retain precedence.
  The card uses no third-party artwork, remote fonts or runtime API calls and
  is generated statically at build time.
- Published artwork JSON-LD now describes permitted reproductions as
  `ImageObject`, carrying recorded image credits, captions and valid HTTP(S)
  license URLs. It does not infer photographers, copyright owners, license
  versions or license-acquisition pages. Restricted and unknown-rights images
  retain their existing exclusion.
- The fallback canonical origin is now the live custom domain,
  `https://artlines.org`; an explicit `ARTLINE_SITE_URL` still takes precedence.

The homepage and research records retain their `noindex` safeguards. These
improvements do not make the catalogue indexable. Read-only production API
validation of Leonardo da Vinci and El Greco found missing biographies, source
and influence review, and zero published representative works; El Greco also
needs movement review. Both were in review at that audit; their reviewed profiles were published on
3 October as described above. The original audit reports are in
[publication-candidates.json](research/seo-release-20261002/publication-candidates.json).
No data, publication statuses, DNS or external accounts were changed by the
2 October release. On 3 October, the owner authorized browser setup: the
`https://artlines.org/` URL-prefix property was verified using the live HTML tag,
and Google accepted `https://artlines.org/sitemap.xml` with status **Success**.
Its child `/sitemap-pages.xml` still reports **Couldn't fetch**, although
Google's live test retrieves it successfully; follow-up processing remains open.
See the [Search Console setup receipt](deployment-20261003-search-console.md).

Verification: all 13 targeted SEO tests passed, as did lint on changed frontend
files, TypeScript and the production build. Read-only browser checks with
JavaScript disabled verified the guide's content, canonical, breadcrumbs,
internal links, preview sitemap inclusion and the unchanged homepage `noindex`.
Desktop and mobile layouts and the 1200 × 630 PNG were inspected. Disposable
screenshots and the browser check script are under `/tmp/artline-seo-*`.
No database writes or test fixtures were required.
The exact release snapshot passed the same 13 tests and targeted lint. Its Cloud
Build passed production compilation and TypeScript. Candidate and canonical-site
browser checks passed before and after promotion, respectively.

### Launch and measurement

1. **Completed 3 October:** verified the `https://artlines.org/` URL-prefix
   property in [Google Search Console](https://search.google.com/search-console?resource_id=https%3A%2F%2Fartlines.org%2F).
   Keep `ARTLINE_GOOGLE_SITE_VERIFICATION` in production and the matching
   `google_site_verification` value in the ignored local Terraform variables.
   This is HTML verification; no DNS Domain property was added.
   The owner subsequently requested removal of the personal account. Ownership
   now belongs solely to `vadim@alingva.com`; the personal account's HTML token
   was replaced, and Google confirmed its removal. Preserve the work account's
   token in future releases.
2. **Completed 3 October:** submitted `https://artlines.org/sitemap.xml`; the
   Sitemaps report shows **Success** for the index. Recheck the child
   `/sitemap-pages.xml`: it still reports **Couldn't fetch** after direct
   submission and one retry, despite a successful Google live fetch.
   The reviewed collection release now adds artist and artwork URLs; the
   earlier report covered informational pages only.
   Google's live test found `/art-history-timeline`
   available and indexable, with valid breadcrumbs; its indexing request was
   accepted. Use URL Inspection to monitor indexing and Google's selected
   canonical. A submission is not an indexing guarantee.
3. **Completed 3 October:** reviewed and published ten artists with five
   representative artworks each. Dates, museum connections, attribution and
   existing image-rights evidence were checked. Incomplete research was retained.
4. **Completed 3 October:** implemented a published view alongside research
   preview. Explicit `preview=0` reads stay published-only in Go; standalone
   public profiles use that scope and server-render their selected works.
5. **Website checks complete:** all sixty new record pages and their sitemap
   URLs passed. Follow up in Search Console for actual indexing, crawl errors
   and Google’s selected canonical. Museum research pages are not part of this
   publication. The preferred HTTPS hostname remains `https://artlines.org`.
6. Record a baseline and review weekly: indexed eligible pages, crawl errors,
   non-brand impressions/clicks, queries, landing pages, and image-search
   impressions/clicks. Use Core Web Vitals field data when available; a new or
   low-traffic site may lack enough field data. Measure visits that lead into
   the atlas or artwork records if consent-appropriate analytics are introduced;
   no analytics or tracking integration was added here.

### A practical first 90 days

The following are editorial hypotheses and a suggested cadence, not measured
keyword volumes or traffic forecasts.

| Timing | Work | Evidence to review |
| --- | --- | --- |
| Weeks 1–2 | Search Console, the guide and the initial reviewed collection are live. Monitor crawl processing and indexing of the approved pages. | Correct canonical and index directives; accepted sitemap; no broken public routes. |
| Weeks 3–6 | Develop one or two carefully sourced guides each week around questions readers can explore in the atlas. Link them to approved records and back to related guides. | Queries and pages beginning to earn impressions; accuracy and usefulness of each guide. |
| Weeks 7–12 | Improve pages that show useful search demand, develop the most promising topic cluster, and share useful examples with relevant educators and communities. | Non-brand clicks, image-search traffic, engaged visits and links from relevant sites. |

Artline's distinctive material suggests initial topics such as comparing
Byzantine and post-Byzantine art, exploring Russian icons across museum
collections, Greek painters in a historical timeline, and understanding which
artists and books belong to the same period. Each guide needs its own sourced
answer and reviewed examples. Test narrow questions as well as the broader
“art history timeline” topic; do not create hundreds of thin keyword variants.

Make something useful to share: a short illustrated comparison, a documented
museum collection trail, or a classroom exercise using the timeline. Offer
those resources to art-history teachers, museum educators, specialist writers
and relevant communities, following their participation rules. Reuse only
rights-cleared images with the required credit and license. No outreach,
posting, accounts, paid links or mailing-list subscriptions were performed.

Useful content, ordinary links and clear image context are supported by
[Google's SEO starter guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
and [image-search guidance](https://developers.google.com/search/docs/appearance/google-images).
See also [Search Console setup and monitoring](https://developers.google.com/search/docs/monitor-debug/search-console-start),
[the effect of noindex](https://developers.google.com/search/docs/crawling-indexing/block-indexing),
and [image license metadata](https://developers.google.com/search/docs/appearance/structured-data/image-license-metadata).
Expect to evaluate organic growth over weeks and months; rankings and traffic
are not guaranteed.

## Original SEO release — 20 September 2026

The original SEO infrastructure was implemented and deployed on 20 September 2026 after explicit authorization.
See [the deployment record](deployment-20260920-seo.md) for live revisions,
verification, backup and rollback details. Production migration 0026 is applied;
no records were published, and no Search Console submission or domain purchase
was performed. The local catalogue was accessed read-only.

## Publication is the current launch dependency

A read-only audit on 20 September of the real local catalogue found 23,286 active artists,
276,977 active artworks and 860 institutions, all in `review`; none were
published. These are local counts, not a claim about production. The documented
Cloud Run website returned 200 for `/`, but 404 for `/robots.txt` and
`/sitemap.xml` before this change.

Research visibility does not confer publication approval. The new discovery
queries only select `published` records, even when public preview or an editor
token is enabled. No statuses, source evidence, uncertain dates, creator labels,
museum holdings or artwork assets are changed by this work.

Pages containing the public research preview have `noindex, follow`. In preview
mode, the original September sitemap contained only `/about` and the informational `/artists`
directory; the directory does not advertise review profiles. In public release
mode it pages through published artists. Editorial pages inherit `noindex`, and
both the Go API and the web API proxy send `X-Robots-Tag: noindex`.
The deployed 2 October change also includes the informational timeline guide.

Do not remove these exclusions to make review material appear published. Use
the existing explicit validation/publication workflow, including creation-date,
selection, source and image-rights checks. Then turn off public research preview
on both services for a published-only launch. If review access must remain on the
public production host, separating a published view from the research preview
is additional backend visibility work; do not grant crawlers different content.

## Domain and webmaster configuration

`ARTLINE_SITE_URL` is the canonical origin for metadata, structured data,
robots and sitemap URLs. It is read at runtime, accepts an HTTP(S) origin and
rejects paths, credentials, queries and fragments. As verified on 2 October,
the live site uses `https://artlines.org`; the local fallback now uses the same
origin. The original September release used the documented Cloud Run address.

The owner's September naming shortlist was **Artline Atlas** (`artlineatlas.com`) and
**Artchrona** (`artchrona.com`). Both .com registry RDAP lookups returned 404 on
20 September 2026, meaning no registration record was found; this is not a
guarantee of registrar availability or price. The website remains branded Artline.

Original deployment checklist (the custom-domain step is now complete):

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
