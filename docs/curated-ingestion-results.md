# Curated import result — 2026-09-08

This is the historical first-batch report. See the subsequent
[popular-painters and Prado review](popular-painters-review.md) for updated
catalogue totals, additional images and completed browser verification.

## Local catalogue

- 1,000 ranked painter candidates in the imported cohort; 1,001 active painter
  records including the preserved Hokusai seed outside that cohort.
- 350 new museum-selected artworks; 365 artworks including the original 15.
- 184 new CC0 images, 33,916,672 bytes (about 32.3 MiB); all image checksums,
  byte counts and dimensions verified against PostgreSQL rights evidence.
- 183 cohort painters have imported highlights; 119 have at least one image
  when the preserved seed images are included. **Most of the cohort is not yet
  an illustrated, editorially complete profile.**
- Nine museums/holding collections and ten physical venues.
- No published painters, no invented on-view assertions, no eligibility
  violations in the imported artworks. Six Wikidata identity conflicts remain.
- 994 cohort entries received direct Wikidata enrichment. Source-labelled short
  descriptions/aliases and P135 associations are review material, not completed
  biographies or independently reviewed movement classifications.

The original seed's names, biographies and images were preserved. One newly
imported Krøyer duplicate was reconciled into the original record, with the
duplicate archived and its URL redirected. Seven automatically imported slugs
were made compatible with the existing ASCII API routes; source names remain
unchanged and old slugs are retained in history.

## Backend implementation

- Inclusive 1970 creation policy in Go plus SQL parity tests; unknown dates,
  crossing intervals and open-ended "after" dates require review.
- Painter publication checks all public associated works, not only the ten
  representative slots, for creation scope and sourced selection/holding evidence.
- Museum-specific requests identify artwork candidates via indexed holdings and
  display assertions before enrichment. Added artist/alias/artwork trigram indexes
  and museum paging/display indexes.
- Explicit local-only Go CLI; allowlisted sources and HTTPS hosts; bounded pages,
  per-invocation painter/work limits, source snapshots and payload hashes,
  per-record outcomes, checkpoints, duplicate identities and preserved edits.
- Media eligibility is independent of metadata eligibility. JPEG/PNG signatures,
  dimensions, byte limits, checksums, institutional CC0 evidence and credits are
  checked. New downloads require source-rights snapshots within 24 hours.
- 512 MiB media budget per execution; repeated image errors pause that source.
  Long Retry-After requests stop the run for a later resume.

## Discovery and limitations

Sources: [Pantheon](https://pantheon.world/data/datasets),
[Wikidata](https://www.wikidata.org/wiki/Wikidata:Data_access),
[Met API](https://metmuseum.github.io/),
[Cleveland API](https://openaccess-api.clevelandart.org/), and
[Art Institute of Chicago API](https://api.artic.edu/docs/).

Museum flags used: Met `isHighlight`, Cleveland `is_highlight`, and Chicago's
`is_boosted` essentials selection (documented by its API). Their own designations
are preserved; the application does not assert an objective masterpiece ranking.
The default slice selects up to five works per painter; a supplementary Met-only
slice adds bounded selections to improve coverage alongside earlier institutions.
Representative profile slots remain capped at ten; chronology includes all works.

Chicago metadata imported, but its image endpoint returned HTTP 403. Those images
were not bypassed or substituted; eligible object links and placeholders remain.
Met's initial broad search returned irrelevant types and intermittent failures.
Department-scoped discovery, per-record failure handling and slower requests
completed a bounded 435-record metadata slice. No entire museum image collection
was downloaded. Some initially rejected/failed discovery rows remain as history.

The remaining 817 cohort painters need further reviewed museum sources before
they have imported highlights. Open-image availability biases this first slice
toward these three museums. The 1,000-person popularity cohort itself still needs
editorial review of multidisciplinary artists and evidence of pre-1971 output.
Unknown rights remain link-only; six authority conflicts need manual resolution.

## Verification

- Go tests, including isolated PostgreSQL import idempotence/edit-preservation
  and catalogue regression fixtures; policy boundaries and SQL/Go parity.
- Painter and museum query plans checked on separate temporary 100,000-artwork
  fixtures; no full artwork scan in the scoped paths.
- 19 frontend unit tests, ESLint and Next.js production build passed.
- Live frontend proxy returned density mode for the full 1,001-record atlas and
  bounded, grouped artwork chronology for Van Gogh. The API was restarted with
  the backend changes. Original 15 assets also passed their manifest audit.
- In-app Browser bootstrap failed at the environment boundary. No new visual
  browser verification is claimed, and the old browser suite's seed-specific
  exact-count assumptions need an isolated test database before reuse.

Not yet complete: 10-million-row load testing, global museum-directory count
projections/caching, publication dependency invalidation, full editorial/source
review UI, scheduled refresh, geographic breadth, or images for all 1,000 painters.
No commits, publication, Terraform apply, or deployment were performed.
