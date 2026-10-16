# Germany museum research — 11 October 2026

The user requested the same deep museum-artwork research for Germany, with an authentic artwork image for every selected museum.

- **322 artworks across 29 collections and all 16 federal states.**
- **180 reviewed pictures; all 29 selected museums illustrated.**
- 312 dated records end by 1970; ten incomplete/unknown upper dates remain in review.
- 40 icon/religious-object records in the two specialist icon museums, with 28 pictures; Bode adds a Byzantine mosaic icon.
- 1,335 distinct association membership entries (1,336 raw entries / 64 pages / one exact duplicate). The directory includes foreign members and non-art collections and is not a German museum census.
- **Zero Germany production uploads, database writes or local database mutations.**

Open [the illustrated report](report.html). Download [the artwork CSV](selected-artworks.csv) and [membership discovery ledger](museum-directory.csv). This is a selected nationwide pass, not exhaustive artwork or museum coverage.

## Canonical evidence

- `selection-final.json`: 313 initial reviewed records plus nine Albertinum paintings transcribed from the public museum guide; source qualifications, exact inventories and evidence retained.
- `images-reviewed.json`: 177 museum-source reproductions plus three exact WikiArt matches, all visually checked. ≤100,000 bytes each; proportional resizing, no additional cropping.
- `visual-review.json`: accepted image hashes, partial-view labels and rejected Friedrich version matches.
- `report-artworks.json` and `report-summary.json`: portable report data and counts.
- `local-identity-review-final.json`: 47 single local identity candidates; 275 without a local match. This is not a new-artwork count or production identity map.
- `association-directory-reviewed.json`: full deduplicated membership ledger and limitations.
- `selection-reviewed.json`, parser drafts, HTTP receipts and source captures preserve earlier decisions; resolved parser errors in drafts are not current research gaps.

## Important object decisions

The Dresden Moon painting is not the later Metropolitan version on WikiArt. It retains its museum metadata but no selected image. Otto Dix’s Der Krieg is the four-panel 1929–1932 painting, not the print portfolio. Museum and WikiArt dates are retained separately. Private loans, especially Modersohn-Becker at the Albertinum, do not become assertions of museum ownership. Model dates, casts, reworking and Klee catalogue numbering remain distinct. Rodin’s Munich bronze has a documented acquisition in 1912, establishing physical existence before the image cutoff without inventing its casting year.

Source-published Hannover details, the Frankfurt cross face and oklad, the central St Columba panel and GNM documentation strips are labelled. WikiArt’s actual rights statements remain intact, including Dix’s restricted “Fair Use” label. Existing user source approval is separate from legal rights evidence; no new licence is asserted.

Image access denials from mdbk.de, skd-online-collection.skd.museum and thumb.wikimedia.org were recorded. No alternate access to those denied reproductions was pursued. Separate public WikiArt sources supplied the three independent museum illustrations. After the first two host denials an identical retry occurred before stop-state persistence was corrected; no further denied-host retries should occur.

## Production handoff

Google Cloud authentication for `vadim@alingva.com` failed with “Reauthentication failed. cannot prompt during non-interactive execution.” The user must refresh it with `gcloud auth login vadim@alingva.com`. This is an authentication dependency, not a request for image approval.

After authentication:

1. Take a fresh, scoped read-only production snapshot and reconcile institutions, source/native IDs, inventories, exact versions/casts, artist identities and existing images. Never use local IDs as production IDs or count the 275 unmatched-local records as guaranteed new additions.
2. Build a concrete selected import/enrichment plan. Preserve all historic values and citations. Keep new records in review, unknown fields explicit, and qualified or anonymous creators supported. Distinguish collection holdings, private loans and current display.
3. Upload only the 180 accepted selected derivatives as needed, verifying hash and ≤100 KB limits. Reuse suitable existing media; record source page, source rights, view type, attribution and separate source-policy approval.
4. Apply authorised selected additions/enrichment through the established audited workflow, with preimage checks and backups under Application Support. Verify final counts and app responses. Do not mutate the real local catalogue or publish/change statuses in bulk.

The unified catalogue includes active review records. Preserve separate login requirements for museum browsing and private bookmarks. No application access-policy changes are part of this research.

## Remaining coverage

Kassel primary-source timeout; wider object coverage in small selections; additional Mainz caption reconciliation; unresolved dates and copies; remaining Leipzig/Dresden pictures. Directory membership is only a discovery lead, never a placeholder artwork or holding assertion.

Originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/germany-deep-20261011/`.
Backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/germany-deep-20261011/`.
Disposable visual QA: `/tmp/artline-germany-delivery/`.

Research scripts: `ops/germany-deep-*-20261011.py`. No commits or deployment performed. Browser QA results are in `report-browser-checks.json` after verification.
