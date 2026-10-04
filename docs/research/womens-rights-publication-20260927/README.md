# Women’s rights publication — 27 September 2026

Live at [Women’s rights in Artline](https://artline-web-lpuqqlugnq-ew.a.run.app/all?preset=womens-rights).
The user explicitly authorized publication and deployment. The production API and
website now serve the reviewed release at 100% traffic.

The historical period covers global history, including Japan. Its illustrated
timeline contains **44 artworks, 34 books and 32 events**. Six additional suffrage
prints are visible in the [London Museum catalogue](https://artline-web-lpuqqlugnq-ew.a.run.app/museums/london-museum)
with source links and without restricted reproductions. The museum has six
accepted holdings and zero current-display claims.

## Publication and preservation

- Of the 50 selected artwork records, 35 are published (33 newly published).
  Fifteen existing records with unknown work types retain their internal review
  status under the incomplete-data instruction in AGENTS.md. They remain visible
  in the public research preview, without “In review” badges. No type or other
  missing fact was invented to pass a publication check.
- All 34 selected books and 32 events are published. Their original imported JSON
  and source checksums are preserved. The status column is authoritative in the
  API; keeping source checksums preserves the book discovery projection joins.
- Production received nine missing artworks, one book and 26 events, plus their
  necessary citations, source records, holding assertions and dependencies.
  Only three media metadata rows were missing. All 44 selected image objects
  already existed in the image bucket and matched checksums; no image upload or
  source-image download was necessary for this publication.
- Ikeda Shōen’s *Cherry-blossom Viewing* already existed in production with a
  different UUID. Its production identity is used in the release preset, and no
  duplicate was inserted. The source-preparation script preserves this mapping.
- Existing artist and institution profiles retain their state. Unrelated records,
  imported source payloads, and the 26 further research leads were not published
  or rewritten by this operation.

The release removes public artwork/artist/book/event review labels and includes
correctly labelled institutional links in the event drawer. Editorial tools keep
internal status controls. The period defaults to all its selected works, so a
Highlights default does not hide 23 of its 44 illustrated artworks.

## Isolated release and checks

The source was assembled from deployed baseline `9b24873`, with the new period,
selected-book focus support, its default Highlights setting, and the requested
public-label changes. Other local UI and ingestion work was excluded. All 30
previous period definitions match the live baseline. Their IDs and definitions
were not replaced by the broader, unfinished local preset edits.

- Go atlas and HTTP API tests passed; TypeScript checking passed.
- All 179 web unit tests passed across 18 test files.
- The real local catalogue test passed under a database-enforced read-only
  transaction. No test database or fixture was created.
- Candidate API counts were 44/34/32; seven-entry keyset pages returned every
  selected entry without gaps or duplicates. All 44 public image responses
  matched the catalogue SHA-256 values.
- The Edo and Renaissance lanes matched the previous API revision. An initial
  request to the old live API returned a transient 503; the subsequent comparison
  passed for both versions (Edo 46/0/2; Renaissance 1697/7/8).
- Desktop 1440 px and mobile 390 px browser checks passed for period selection,
  loaded images, artwork details, the Japanese election and National Diet Library
  source link, no review badges, no overflow, no browser exceptions and no API
  writes. An initial test read the drawer before its detail request completed;
  the final test waits for the detail content and passed.
- Production traffic, live API counts, London Museum metadata and publication
  statuses were checked after release. Browser screenshots remain in `/tmp`.
- The existing query-plan limitation documented in the original research remains:
  these checks do not establish performance at ten million artworks.

The in-app browser connection failed with its sandbox metadata error, so browser
verification used the installed Playwright/Chrome fallback after reading the
Browser skill. This did not require user authentication or additional permissions.

## Release and recovery

| Service | Live revision | Image digest | Regional build |
|---|---|---|---|
| API | `artline-api-womens-0927` | `sha256:194622e2c5ea305ca7efe489ab7dc843293279d8678f85fa0399f8b57c9a9813` | `2afd31d3-883a-456d-9945-0ad1634819aa` |
| Web | `artline-web-womens-0927` | `sha256:d34338da1c890abc77fe2fb6b18710300a5d6d36026cdd23d4f28fcea9774620` | `48428419-70cf-4130-8332-f6c7546232e3` |

Both services are in `europe-west1`, project `artline-508319`. The API and web were
first deployed with zero traffic; promotion followed successful candidate checks.

Cloud SQL recovery backup **1790505821419** completed before data changes. The
validated local PostgreSQL dump is 642,224,693 bytes. Backup paths, hashes, pinned
exports and private pre-release service configurations are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/womens-rights-publication-20260927/`.
No backup was restored and no unrelated database or artwork asset was removed.

Traffic can be rolled back to API `artline-api-release-0924` and web
`artline-web-release-0923`; this leaves the source-backed published data intact.
A data reversal, if ever requested, must use the exact preimages and check for
later edits rather than delete catalogue records.

`plan.json`, `plan-pin.json`, `backups.json`, `storage.json`, the local/production
receipts, release source hashes and verification reports preserve the evidence.
The two `ops/*womens-rights*20260927.py` scripts prepare the release and perform
pinned publication. No commit or Terraform apply was made.
