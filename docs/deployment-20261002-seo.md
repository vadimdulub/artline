# SEO release — 2 October 2026

Deployed after the owner approved the prepared SEO work with “ok do it”.

Live guide: <https://artlines.org/art-history-timeline>.
Live sitemap: <https://artlines.org/sitemap-pages.xml>.

At release, the web service served 100% of normal traffic from `artline-web-seo-1002`.
The [3 October Search Console setup](deployment-20261003-search-console.md)
subsequently added the ownership token in a configuration-only revision using
the same image.
Cloud Build `c47443a8-c447-4997-9cc8-474b984632e0` produced immutable image
`europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:8a9481c1fd5c334949ce586117dea2a25290123a2d426b121223d0e60e421000`.

## Scope and source

The release adds the indexable timeline guide, its sitemap entry and internal
links, a statically generated sharing image, recorded artwork-image credit and
license metadata, and the custom-domain fallback. It preserves research-preview
exclusions and does not publish catalogue records.

Source was reconstructed from the exact live period/filter build
`4adfaeb7-a2b0-400b-a6b8-924d30b82817`, image
`sha256:062b9f61e2247c118a915a4ad1693a6639fa649b4704d0d26e4cc671caa2c2f4`.
Only the seven SEO application files were overlaid. Both baseline and new source
archives matched Cloud Build SHA-256 provenance. The new archive has 217 files;
it does not include environment secrets, dependencies, generated build output
or unrelated workspace changes.

The candidate was staged with zero normal traffic and promoted after checks.
Cloud Run runtime template, ingress, access and scaling settings matched their
pre-release values apart from the new image and revision. Google sign-in,
production local-debug safeguards, API configuration, public research preview
and canonical domain were preserved. No API deployment, migrations, database
writes, ingestion, Terraform apply or Git commit was performed. The local ignored
web image pin was updated to the live digest.

## Verification and outstanding work

- Exact release snapshot: 13 SEO unit tests and targeted lint passed. Cloud
  Build passed production compilation and TypeScript.
- Candidate and live-domain browser checks passed with JavaScript disabled:
  guide content, title/canonical metadata, breadcrumbs, internal links, sitemap
  inclusion, robots discovery, 1200 × 630 PNG and unchanged homepage `noindex`.
- Desktop and mobile screenshots were inspected locally; candidate and live
  mobile viewport checks passed. Existing About, Artists, Books, Events, All,
  Museums and Account routes returned 200 in both release checks.
- Final service read confirmed readiness and 100% traffic to the exact revision.
  No ERROR-level logs were returned for the new revision during verification.
- Public artist discovery was empty. Read-only publication validation failed
  for Leonardo da Vinci and El Greco: insufficient sourced biographies,
  incomplete influences/citations, and zero published representative works;
  El Greco also needs movement review. The
  [validation reports](research/seo-release-20261002/publication-candidates.json)
  are retained. No publication checks were bypassed.
- At this release, Search Console setup awaited the owner's public HTML
  verification tag. Ownership verification and sitemap submission were
  [completed on 3 October](deployment-20261003-search-console.md).
  The domain's authoritative nameservers are Cloudflare; DNS was unchanged.

Private configuration preimages, operations, source archive and checksums, build
receipt, screenshots and release scripts are under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/seo-release-20261002/`

Disposable checks are under `/tmp/artline-seo-release-20261002/`. Configuration
backups may contain secrets and must remain private.

## Rollback

Restore the preceding web revision without changing the API or catalogue:

```sh
gcloud run services update-traffic artline-web --account=vadim@alingva.com --project=artline-508319 --region=europe-west1 --to-revisions=artline-web-periods-1002=100
```

Restore the previous web image pin if rolling back. The previous immutable image
is the period/filter baseline digest recorded above.
