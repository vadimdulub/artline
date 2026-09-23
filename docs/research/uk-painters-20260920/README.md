# UK painters and selected artworks — 20–21 September 2026

Delivered to both the real local catalogue and live Artline collection.

[Open UK painters](https://artline-web-lpuqqlugnq-ew.a.run.app/?country=GB&popular=false) · [Full painter list](ARTISTS.md) · [Artwork and image index](ARTWORKS.md) · [Review queue and public alternates](REVIEW.md)

| Verified result | Local | Live |
| --- | ---: | ---: |
| New artist profiles | 8,545 | 8,545 |
| Active UK-linked profiles | 9,574 | 9,574 |
| New artwork records | 18,882 | 18,882 |
| New image attachments | 9,217 | 9,217 |
| Total UK-linked artwork records | 29,364 | 29,333 |
| Total UK-linked artworks with images | 13,203 | 13,201 |

## Coverage and selection

Surveyed all 10,514 identities returned by the uncapped Wikidata painter census across the UK, constituent countries and historical states. Historical polity alone was insufficient to infer present-day UK cultural affiliation. Other national relationships and existing biographies were preserved. 327 of 329 profiles in [WikiArt’s British directory](https://www.wikiart.org/en/artists-by-nation/british/text-list) were reconciled; remaining identities are documented in the review queue. These are source inventories, not an exhaustive list of every UK painter in history.

Of the 9,574 active UK-linked profiles in the live catalogue, 5,877 have artwork records and 2,873 have illustrated works. Profiles with no resolved artworks remain in the full painter index.

The collection-source search covered 10,514 painter identities and captured 154,261 source rows. Selected up to four further collection-linked records per painter and up to eight further featured historical WikiArt works per matched profile. Artwork creation dates determine image eligibility. Painter birth or death dates are not used as artwork dates.

Added 17,640 collection-source artwork records and 1,242 WikiArt records. Source-pass totals include unresolved affiliations and eight works retained with a Viking cultural context rather than a named painter; the UK-filter totals are reported separately. 4,807 new collection-source records have unknown dates and remain in review. Unresolved named creators remain object-level labels. Wikidata collection statements can identify museums, galleries or other collections; they were retained as citations without inventing accepted holdings or current display claims. Owner selections remain distinct from museum designations.

## Public images and verification

Uploaded 9,284 public files. Every derivative is at most 100,000 bytes; the largest is 99,999 bytes. Selected image creation dates end by 1955. Source licences, restricted/unknown rights labels and credits are preserved. Public alternate links remain available for unresolved object matches.

Final verification `final-verification-1790014440.json` recorded zero errors. Checks cover exact database receipts, authority IDs, creator links, date fields, review states, collection membership, recovery hashes, all uploaded public image hashes and bounded artwork API checks. The UK timeline returned HTTP 200 in 0.79 seconds. Whole-catalogue image-size metadata audits found no oversized or unknown-size images in either database. No test fixtures or test databases were created. No code was deployed or committed. This validates the actual collection operation; it is not a 10-million-row load test.

Forty-seven offline tests passed for source-image review, WikiArt selection/delivery, request pacing and same-name identity matching. Six confirmed namesake errors were corrected in both catalogues, preserving older artist records and artworks. Five remaining name matches are explicitly listed for manual confirmation in the review queue. Public file checksum receipts retain their actual check timestamps; successful immutable-file checks from the earlier delivery are reused alongside fresh checks for the final batch.

## Research and recovery locations

- Source captures, per-record decisions and verification receipts: this research directory.
- Artist/artwork preimages, correction snapshots, receipt chains and selected Commons originals: `/Users/vadimdulub/Library/Application Support/Artline/backups/uk-painters-20260920/`. Earlier artist baselines preserve alias text rather than complete alias-table row IDs.
- Original WikiArt downloads: `/Users/vadimdulub/Library/Application Support/Artline/source-images/uk-painters-20260920/`.
- Operation runners: `ops/uk-painters-20260920.py` and `ops/verify-uk-painters-20260920.py`.

The query service used Wikimedia’s documented main-graph endpoint with paced, bounded requests and service backoff. Resumed media requests use a shared two-connection gate and 16 Mbps client bandwidth ceiling; Action API calls use one shared connection and a pause after slow responses, following the [Wikimedia robot policy](https://wikitech.wikimedia.org/wiki/Robot_policy). Larger final-selection originals use the API-provided 1280-pixel version, one of the [standard thumbnail sizes](https://www.mediawiki.org/wiki/Common_thumbnail_sizes). Server retry delays are retained and extended after repeated failures. Artist records preserve explicit life-date precision or supplied activity periods without inventing missing years.

## Production synchronization — 21 September 2026

The production follow-up checked all 9,447 artist records and 18,949 artwork records touched by this batch, including existing records. All 9,284 image objects were already present in production and matched the local byte counts and checksums; no image upload remained. Added 37 missing owner-collection links for existing artworks that had received WikiArt images. Artist/artwork metadata, image files and review states were preserved. Forty fresh public artwork/image checks passed. Receipt: `production-sync-1790015632.json` (zero errors).

Collection preimages and selection details are under the existing Library backup root in `production-sync/collection-memberships/`. The reconciliation runner is `ops/sync-uk-production-20260921.py`, with its exact contents archived under `operation-scripts/`.
