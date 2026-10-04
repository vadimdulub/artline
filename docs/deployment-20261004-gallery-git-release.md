# Committed gallery release — 4 October 2026

The user requested committing, pushing and deploying the pending application
changes. Commit `3094bce` records 402 pending files and was pushed to
`origin/master`. It includes the previously deployed catalogue, books, navigation,
branding, SEO and performance work, plus the new artwork gallery ordering.

Both build contexts were extracted from this exact Git commit. Their uploaded
source archives were downloaded using Cloud Build's resolved object generations
and matched the recorded SHA-256 checksums. Compared with the preceding live
archives, the only new application behavior is the gallery priority ordering;
the web's generated type declarations also differ. Database migrations match
the previously deployed source.

## Production

Both services are ready and serve 100% of normal traffic in project
`artline-508319`, region `europe-west1`:

| Service | Revision | Successful Cloud Build |
| --- | --- | --- |
| API | `artline-api-gallery-git-1004` | `51c0373a-be05-47a9-8870-6104fdbb790d` |
| Web | `artline-web-gallery-git-1004` | `8696ba97-0366-4ed2-b3a0-c4a0eedb75a7` |

- API image: `europe-west1-docker.pkg.dev/artline-508319/artline/api@sha256:df6ce2ade65b2042b641dec1db5c47f6437df81f07998aaaaf5a12f4f371081d`.
- Web image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:c5303b347697f3cce60a228d7b84c18d35b8ab2788f0bdc2299f7f184395f61f`.
- Canonical website: <https://artlines.org>.

Candidates received no normal traffic until their checks passed. Runtime
configuration, environment, secrets, authentication, ingress, scaling and
resources were preserved. The ignored Terraform image pins were synchronized
without a Terraform apply. No catalogue ingestion, publication or new schema
migration was performed.

The previous API revision `artline-api-perf-search2-1004` and web revision
`artline-web-performance-1004` remain available for traffic rollback.

## Verification

- All Go package tests, 201 web unit tests and web lint passed before release.
  Cloud Build completed the production Go and Next.js builds, including web
  TypeScript validation. Fixture database tests remained opt-in and were not
  pointed at the real catalogue.
- Candidate and live API checks preserved totals, density and date extent.
  Rembrandt's 1,329 illustrated works comprise 77 paintings, 13 works of unknown
  type, then 1,239 graphic works. Results matched independent work-type filters.
  Page and medium-group boundaries passed next/previous navigation checks.
- Book, event, period metadata and public painter-timeline sample responses
  matched their pre-release responses. Production sessions did not enable
  local debug access, and catalogue/session responses retained no-store rules.
- Painters and All passed gallery checks at 1440px and 390px on the candidate
  and canonical site. First-page ordering, scrolling to 300 records without
  duplicates and drawer navigation passed. Live checks also waited for the
  first displayed artwork image to load. Screenshots were inspected.
- Five header widths, logo/favicon byte checks, seven route responses,
  canonical metadata, Google verification, sitemap discovery and anonymous
  session behavior passed on the candidate and live website. No browser
  JavaScript errors occurred in those checks. This was not a new Google sign-in
  round trip.

Release log review found two museum-detail HTTP 500 responses. Follow-up reads
of `the-met` and `national-gallery-of-art` reproduced approximately eight-second
timeouts on **both the new and previous API revisions**. That existing museum
detail performance problem remains unresolved; museum query code did not change
in this release.

Private service preimages, source archives/manifests, build results, release
operations, verification reports and screenshots are under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/gallery-git-release-20261004/`

Additional local navigation/style/test edits appeared after commit `3094bce`.
They were preserved and are outside this committed production snapshot.
