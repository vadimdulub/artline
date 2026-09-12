# Russia / Italy and NGA bulk expansion: verified local outcome

9 September 2026. No commit, publication, deployment or Terraform apply. This is one completed research/import pass; the 50,000-artwork target and national catalogue coverage remain incomplete.

## Actual changes

| Measure | Before | After |
|---|---:|---:|
| Artworks | 2,223 | 34,264 |
| Artist records | 1,002 | 5,315 |
| Institutions | 56 | 57 |
| Media assets | 211 | 230 |
| Published artworks | 0 | 0 |
| Display assertions | 0 | 0 |

Added 32,041 artworks: 31,983 NGA works, 49 Pushkin paintings, nine Brera paintings. There are 5,314 active artists (one pre-existing archived record). Current types: 3,851 paintings, 6,559 drawings, 23,849 prints and five frescoes. The remaining gap to 50,000 is 15,736, not a promised import yield. Ordinary museum holdings are not all masterpieces.

NGA: 33,493 selected source identities, including 1,510 existing artworks. Final selection has 3,204 paintings, 6,485 drawings and 23,804 prints. Added 4,313 source-backed artist records, of which 3,240 use literal unqualified closed lifespans and 1,073 explicitly labelled documented-work activity dates. No automatic popular-painter designation. Master CR constituent4866 and constituent37703 remain separate reviewed source authorities. No name-only fuzzy merge.

Pushkin: complete97-object legacy highlights feed,55 paintings,49 eligible selections for41 existing authorities. Six unresolved painting records preserved in deferred.json. Feed Last-Modified2018-10-25, not a fresh display check. Facts only; no authored narrative or photographs copied. Forty-nine museum-highlight designations were added from the explicit museum highlights source.

Brera: nine new paintings by Hayez, Albani, Anguissola and Appiani; four existing works preserved. Exact accessions, URLs, literal dates, medium, dimensions and factual descriptions. New museum highlights were not inferred. Italian country-level bulk ingestion remains outstanding.

Images: 20 exact primary-view openaccess=1 NGA candidates from384 complete rows of an explicitly partial256KiB metadata prefix. Nineteen downloaded,19 attached and byte/hash/rights/dimensions checked. Object41617 skipped for missing ETag on a ranged response. Earlier v1 receipt records three failed attempts caused by HTTP200 handling; v2 contains the actual19 successful attachments. Initial HTTP200 full responses are now bounded to2MiB; partial responses require consistent validators. General metadata CC0 is not used as an image licence. Local cached files without a matching source/checksum sidecar are conservatively refused if a future import tries to reuse them; existing attached media are preserved on replay.

## Backup and authoritative receipts

Pre-change backup: `/Users/vadimdulub/Documents/artline-russia-italy-backup-20260909.CXyVhG/before-bulk-expansion.dump`.
SHA256: `4a9c49cef3acb488332f78d5fb7d3b481ee7490c4506401050ee284f078f87bb`. Archive table of contents checked, not restore-tested.

- `docs/research/russia-italy-scale/nga-v3/manifest.json`: final34 chunks with sizes and SHA256 values. Source revision`f088836026d09d0d25001814fba0f84d757ebe62`.
- `output/nga-bulk-preview-v3-fixed/`: all34 rollback previews passed.
- `output/nga-bulk-applied-v3/`: chunks001-028 committed. Empty029 receipt is a rolled-back name conflict, not a success.
- `output/nga-bulk-applied-resume-v3/`:001-028 no-op replay;029-034 committed after the precise homonym exception was reviewed.
- `output/nga-bulk-replay-v3/`: all34 completed chunks replayed without mutation.
- `output/pushkin-applied-v1.json`: job`0aae0c08-9259-41c9-9bec-a0bc29d1a3d5`,49 additions.
- `output/brera-applied-v1.json`: job`96c22ce0-43fd-4bfa-8d77-6be6284e3ba8`,nine additions.
- `output/nga-images-applied-v2.json`:19 attached,one deferred.
- `output/russia-italy-verification.json`: before/after replay fingerprints across14 tables, actual counts, zero unsafe new rows,19 verified image files and baseline API observations.
- `output/russia-italy-api-optimized.json`: final API details/pagination/filter/access checks and improved timings.

Do not use the earlier NGA v1/v2 exploratory selections as approved imports. They remain as research history. Source records excluded/deferred in NGA v3 total53,818; these offline JSON rows do not count as database artworks. The previous research_records evidence store was not expanded in this pass; new audit evidence is in import_records and immutable local snapshots.

## App and backend verification

Descriptions are now exposed by single-artwork detail APIs and by a safe Markdown disclosure in both painter and museum records. Long descriptions are deliberately removed from chronology page projections and omitted from museum cards. Description content is loaded only on disclosure for a painter record; remote image embeds and raw HTML are excluded. Existing JSON/date/filter/visibility logic remains in Go/PostgreSQL.

Large-museum review exposed repeated profile reconstruction and materialized per-object enrichment. Museum works now use a lightweight membership/visibility existence check; the shared works CTE is inlined so counts/facets do not build unnecessary artist JSON. Observed NGA works-page time fell from2,716ms to450ms (one local observation, not a production benchmark). The local API was restarted with the changes; the temporary comparison API on8081 was stopped.

Checks completed:

- Full Go test suite with isolated test schemas, and `go vet ./...`.
- New tests: SHA/source validation, cutoff traps, rollback, replay, descriptions/types, authoritative lifespan handling, precise homonym isolation, Pushkin/Brera batch evidence, image byte budgets and rights selection.
- Live API: NGA33,493 / Pushkin49 / Brera13 works; all on-view counts0. Cursor pages do not overlap; Monet+Pissarro filtering correct; chronology pages stay bounded and omit long text; single details include descriptions.
- Anonymous backend preview401, public Pushkin404; existing explicit local research-preview proxy behavior unchanged.
-100k unrelated-artwork identity fixture used three exact-match indexes without sequential catalogue scan. Museum-scoped100k temporary-row projection used indexes, observed2.997ms. Neither is a10-million-row or full-site concurrency benchmark.
-22 frontend unit tests, TypeScript and lint passed.
-Two project Playwright tests passed: Brera description at1440px and390px, link destination, horizontal overflow, WCAG2A/AA automated checks, Escape/focus return; painter record lazy description. An initial insufficient link contrast was fixed before the passing run.
- In-app browser bootstrap was unavailable due a tool connection error. Project browser tests were used instead. Both final Brera screenshots inspected;19 image files checked mechanically and three NGA reproductions visually sampled.

## Reproduction and next work

From `apps/server`, commands default to rollback; add `-apply` only for the reviewed local write. Use fresh receipt paths:

```sh
go run ./cmd/ingest-bulk -dir ../../docs/research/russia-italy-scale/nga-v3 -reports ../../output/nga-next-preview
go run ./cmd/ingest-european -batch pushkin-v1 -report ../../output/pushkin-next-preview.json
go run ./cmd/ingest-european -batch brera-v1 -report ../../output/brera-next-preview.json
```

Selected-image application requires fresh rights evidence; the pinned selection deliberately expires. Replaying catalogue metadata does not require any new download. Do not overwrite checksummed snapshots or old receipt files.

Remaining research/engineering: reliable full Pushkin and Russian Museum object capture; verified Hermitage/Tretyakov/Goskatalog export access; streamed ArCo RDF with release-specific rights, creator/physical-holder mapping and quarantine handling; complete Joconde retrieval with correct creation semantics. No scheduled ingestion is left running.

## Research artifact QA

`output/pdf/russia-italy-catalogue-expansion.pdf`: four pages,24 source hyperlinks,107,803 bytes; SHA256`f9dcc32eacafa6eb0201651c6a4d02dbaf70166d47d1ee2e91556d4ae83b5d13`. All four rendered pages inspected; no clipping, overlap or missing glyphs. Canonical links and key counts checked against PDF text/annotations. Internal canonical report, source ledger, gap matrix and research log are under`docs/research/russia-italy-scale/`.
