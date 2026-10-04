# Loading performance — 4 October 2026

This release reduces repeated discovery work and improves image delivery without
changing the Cloud Run sizes/scaling or the `db-f1-micro` PostgreSQL instance.

## Behavior

Timeline request keys exclude the browser-only `fit` flag and normalize omitted
and explicit default dates. Finishing an unchanged date fit now reuses the bounded
response. Date/filter/cursor changes still fetch server-owned results. Renaissance
on All makes one catalogue request instead of two.

The Go API caches allowlisted discovery responses in a process-local LRU with a
16 MiB body budget, 128-entry limit, 1 MiB per-response limit and one-minute expiry.
Concurrent identical misses share one computation. A fresh PostgreSQL visibility
snapshot is part of every lookup key: committed writes, including imports or edits
through other instances, make earlier results unreachable. Access is checked before
every hit; research and published visibility are separate. Errors, cookies, oversized
responses, member/auth/editor routes and cancelled fills are excluded. Snapshot
lookup failure falls back to normal queries. Browser/API proxy responses remain
private and non-cacheable. Unrelated transactions can conservatively cause misses,
and each API instance warms independently.

Period metadata retains menu labels, dates, descriptions, cover art and source
links while keeping internal relationship IDs and identity maps on the server.
The production response fell from 227,949 to 74,831 bytes (67.2%). Matching and
provenance records remain unchanged.

Artwork text search resolves title/label and creator-ID candidates through existing
indexes before full record enrichment. Alias/movement/country/place search sets
are evaluated independently rather than per artwork. Native entity-search scopes
use the existing covering index; only a shared All text query still needs titles
in that native projection. No new database index or migration was required.

Cloud CDN uses origin headers on the existing web backend, including full host,
protocol and query-string cache keys. Negative caching and stale serving are
disabled. Image width/quality/source query keys and Accept format variants remain
separate. Images/static assets cache at the edge; account, session and catalogue
responses remain private/no-store. Original image paths and rights information
were not changed.

## Verification and limits

Focused TypeScript, lint, authentication/request-key tests and Go race tests passed.
Read-only comparisons for seven searches in both visibility modes preserved whole
responses, including totals, dates, ordering and cursors. No fixtures or test
catalogues were created. Production and local EXPLAIN evidence is archived outside
Documents. The final production query completed in 3.21 seconds under normal
settings; the old Rossetti request timed out after 20 seconds. These are observations
on the current catalogue, not a 10-million-artwork capacity test. Representative
scale/load testing remains outstanding. Cold starts and uncached queries remain
possible with minimum instances still zero.

For urgent media withdrawal, update the underlying catalogue/asset authorization,
clear the Next image optimizer cache (a fresh web revision clears its process-local
storage), and invalidate the CDN image/asset paths. Catalogue writes need no manual
metadata-cache purge because the visibility snapshot changes. Future server-derived
fields that depend on time or external systems need explicit invalidation review.

## Production release

- Web: `artline-web-performance-1004`, serving 100% of normal web traffic.
- Web image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:15894183ef562b6b07aeeeb8f02b4d03dcff011678820353312a88bb6ead630a`.
- Web Cloud Build: `2ba69a34-baf9-473e-b558-abc33664f381`.
- API: `artline-api-perf-search2-1004`, serving 100% of normal API traffic.
- API image: `europe-west1-docker.pkg.dev/artline-508319/artline/api@sha256:bf1b0593d1039b1909d962d016130a9b600d8a344e57020f2fa67044cf84c664`.
- API Cloud Build: `7a3e0129-a299-497b-93ac-e43ba91ab05b`.

The release was reconstructed from the exact live source archives with only
reviewed performance files overlaid. Cloud Build source checksums matched.
Candidates were tested before traffic promotion. The intermediate search
candidate that still timed out was never promoted and its traffic tag was removed.
No Git commit, Terraform apply, data ingestion, publication or schema change was
performed. Only immutable image pins were synchronized in the ignored tfvars;
`domain.tf` records the scoped CDN configuration update.

Final runtime comparisons preserved CPU (1), memory (512 MiB), concurrency,
minimum/maximum instances (0/3), environment, secrets, authentication and ingress.
Cloud SQL remains `artline-postgres`, `db-f1-micro`, in europe-west1. The previous
web revision `artline-web-member-nav-1004` and cached API revision
`artline-api-performance-1004` remain available for traffic rollback.

All 15 canonical-site browser checks passed after the final API release: filter
and date behavior, one-request Renaissance fitting, cache/privacy behavior and
eight Full view cases including nested details, keyboard focus and accessibility.
Google verification, canonical URLs, sitemap discovery, logo assets and anonymous
session safeguards passed separate live checks. Final revision logs returned no
ERROR records during verification.

The final mobile-viewport browser check measured Renaissance ready in 1.63–1.65 s,
compared with the earlier 2.52 s check. Each action made one catalogue request,
with cache misses in these samples. Default Paintings was still about 1.93 s on
misses, comparable to the earlier 1.94 s; there is no claim that every first load
became faster. Cached image probes returned valid CDN Age headers and took about
56–95 ms, with width and WebP/JPEG variants verified separately. These timings are
small unthrottled samples from this connection, not a broad device/network benchmark.

Repeated exact Paintings requests subsequently returned cache hits in 160–175 ms;
Renaissance hits were 170–372 ms. Initial repeats can reach a different instance
or a changed database snapshot and miss. These figures measure API responses,
not the complete page becoming interactive.

Private service preimages, source manifests, builds, request timings, query plans
and browser reports are retained under:

- `/Users/vadimdulub/Library/Application Support/Artline/backups/performance-20261004/`
- `/Users/vadimdulub/Library/Application Support/Artline/backups/performance-search-final-20261004/`
