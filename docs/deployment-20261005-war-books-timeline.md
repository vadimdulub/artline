# War literature and artwork timeline — 5 October 2026

The selected collection adds 38 war-related books, including 19 by Nobel
laureates, works recognized by other literary awards, and Egyptian and African
perspectives. Five were published in World War I calendar years and seven in
World War II calendar years; later publications about those conflicts are also
included. Publication dates are distinguished from composition and performance
dates. The additions appear when the Books “Top 100” filter is off.

The artwork gallery now grows to accommodate its contents and expanded year
overview. The “Explore artworks by year” summary stays above the range slider,
including in short desktop windows.

## Book publication

The user explicitly requested publication. The selected records passed the
existing Go import validator, identity checks, source/date review, and guarded
local import before release. A Cloud SQL backup completed before publication:
`1791182148526`.

The production transaction inserted exactly 38 published books and 13 creators.
The local transaction published the matching 38 records. Both databases now have
10,136 books and 72 published books, as measured immediately after this release's
transactions. The 256 highlight selections, existing creators, unselected books,
source payloads and discovery projections were preserved. The publication plan
SHA-256 is
`9fa634ffbf62dcf3d1429408a4311406c01157a83cc08d228729f4b36b12ce82`.

Research evidence and receipts remain under
`docs/research/war-books-africa-20261004/`, with publication receipts in its
`publication/` directory. The four illustrated Egyptian/African war-art research
candidates were not imported; their reproduction rights remain unresolved. No
new artwork images were downloaded.

## Web release

The release is based on the exact source of the serving Account panel update,
Cloud Build `e46c4e24-fdac-4ccf-b9b0-056045cac241`. Its source archive was verified
against Cloud Build provenance. Only `components/PainterPaintings.css` differs;
all 272 uploaded source files were checked against the release manifest. The 40
existing selected book and author images are preserved.

The first build was superseded before deployment when the concurrent Account
panel release went live. Its stale-service guard prevented an update. The
rebased build is `10543d4b-2c0b-4fb7-82a4-9505cbf99dbe`.

- Web revision: `artline-web-war-timeline-1005`, ready and serving 100%.
- Web image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:5dbf26272380348091558fdc98986ad1eb4c3cbec4e312094aa6e462fe331d4f`.

The candidate passed verification before an etag-protected traffic update.
Runtime settings, API deployment and prior tagged revisions were preserved. The
local Terraform web image pin records the serving digest; no Terraform apply or
Git commit was performed.

## Verification

- The Go importer validated all 38 books.
- Anonymous production API checks verified all 38 published records, their
  reviewed metadata and creator links, and three bounded searches. Production
  local-debug access remains disabled.
- All eight local layout states passed: four viewport sizes, with the year
  overview closed and expanded. Checks cover range overlap, footer overlap and
  horizontal overflow; screenshots were inspected.
- The two existing gallery view-switch regression tests passed locally.
- The same eight layout states passed on both the candidate and public site at
  2048×1152, 1440×900, 1440×680 and 390×844. Candidate screenshots were inspected.
- Candidate and final public API checks again verified all 38 published books
  and three bounded searches. All 40 retained images matched the source bytes
  on both the candidate and public site.

Private service preimages, database preimages, source manifests, deployment
operations and release evidence are retained under
`~/Library/Application Support/Artline/backups/war-publication-20261005/`.
