# Africa, Asia and Cyprus expansion — 5 October 2026

Added to the real local Artline catalogue and delivered to production on 5 October 2026: **177 artwork records, 14 artist profiles and 43 selected image attachments**. All new records remain in editorial review and are available through the existing research preview. No records were published; no application deployment or commit was needed.

The selection contains **50 African, 112 Asian and 15 Cyprus-related works**, all explicitly dated in or before 1970. The 15 Cyprus-related works comprise nine by reconciled Cypriot creators and six museum-catalogued Cyprus subjects with five source-supplied creator labels. Those five labels remain at object level; foreign visitors were not assigned Cypriot nationality and depicted places were not converted into creation places.

## Country coverage

| Country / connection | New artwork records | New pictures |
| --- | ---: | ---: |
| China | 30 | 15 |
| Cyprus | 15 | 0 |
| Egypt | 4 | 3 |
| Ethiopia | 5 | 0 |
| India | 27 | 8 |
| Indonesia | 6 | 3 |
| Iran | 16 | 6 |
| Iraq | 1 | 0 |
| Lebanon | 4 | 0 |
| Morocco | 3 | 0 |
| Nigeria | 2 | 1 |
| Philippines | 11 | 0 |
| South Africa | 31 | 4 |
| South Korea | 7 | 3 |
| Sudan | 5 | 0 |
| Syria | 2 | 0 |
| Türkiye | 5 | 0 |
| Vietnam | 3 | 0 |

## New artist profiles

- [Gebre Kristos Desta](https://www.wikiart.org/en/gebre-kristos-desta)
- [Chaibia Talal](https://www.wikiart.org/en/chaibia-talal)
- [Ibrahim Salahi](https://www.wikiart.org/en/ibrahim-salahi)
- [Walter Battiss](https://www.wikiart.org/en/walter-battiss)
- [Lin Fengmian](https://www.wikiart.org/en/lin-fengmian)
- [M.F. Husain](https://www.wikiart.org/en/m-f-husain)
- [S. H. Raza](https://www.wikiart.org/en/s-h-raza)
- [Basuki Abdullah](https://www.wikiart.org/en/basuki-abdullah)
- [Behjat Sadr](https://www.wikiart.org/en/behjat-sadr)
- [Rafa Nasiri](https://www.wikiart.org/en/rafa-nasiri)
- [Louay Kayyali](https://www.wikiart.org/en/louay-kayyali)
- [Roberto Chabet](https://www.wikiart.org/en/roberto-chabet)
- [Park Seo-Bo](https://www.wikiart.org/en/park-seo-bo)
- [Yun Hyong–keun](https://www.wikiart.org/en/yun-hyong-keun)

Thirty-seven sourced cultural-affiliation links were added for selected artists whose target country link was missing. WikiArt nationality labels support those links; citizenship and birth location were not inferred. Existing artist biographies, lifespans and publication status were preserved.

## Sources and selection

This is a bounded regional highlight pass, using 61 selected WikiArt artist profiles and at most five new dated featured works per artist. All 178 initially selected WikiArt object pages passed title, source-ID, artist and date comparisons. The final import contains 162 WikiArt records plus five works from the [Leventis Gallery’s Cypriot artist catalogue](https://cypriotartists.leventisgallery.org/en/adamantios-diamantis/works) and ten from [CVAR’s painting collection](https://cvar.severis.org/en/explore/collections-archives/paintings/). The Leventis public website API was read without credentials.

Examples of documented sources include [Ibrahim El-Salahi](https://www.wikiart.org/en/ibrahim-salahi), [Gebre Kristos Desta](https://www.wikiart.org/en/gebre-kristos-desta), [Le Pho](https://www.wikiart.org/en/le-pho), and [Rooftops at Nicosia](https://cvar.severis.org/en/collections/item/rooftops-at-nicosia/12769/).

Artists and objects were reconciled against the local catalogue by source URL/ID, normalized names, aliases, and creator-scoped titles. The research avoided 133 existing WikiArt matches and 40 existing Leventis matches. Eighteen selected candidates were held back after review: two detail views and sixteen repeated artist/title records requiring composition-level reconciliation. Unknown artwork dates and post-1970 works remain in the research holds, not in this dated import. Bengali affiliation alone was not converted into a country.

No types, biographies, museum holdings or current display assertions were invented. WikiArt works retain unknown work type where the captured object metadata does not provide a reliable mapping. Museum collection labels, provenance and conflicting source facts remain in the citations. New artwork records are research candidates; selection does not publish them. All 177 belong to the existing personal owner collection, separate from museum designations.

## Pictures

Forty-four selected images from 16 artists were downloaded only after capturing an explicit WikiArt per-object public-domain label. All were visually inspected. One Olowe of Ise image was rejected because it is a modern gallery advertising composite; its artwork metadata was retained, and its downloaded evidence was preserved. **43 full-frame JPEGs were attached**, each under 100,000 bytes. No cropping, inpainting or generated content was used.

“Public domain” is the captured WikiArt source label, not an independent worldwide rights determination. Restricted/unknown reproductions were retained as source links without image downloading. The Cyprus museum pictures remain unattached because no reusable image licence was established.

## Verification

- Read-only post-import verification passed for all 177 works, 14 new artists, 43 image hashes, personal collection membership and the sourced country links.
- All 177 local API detail responses and all 43 images served by the local web app passed checks. The existing loopback local-debug mode provided access without Google login or a paid subscription; its safeguards were unchanged.
- Twelve date/uncertainty cases and all selected metadata checksums passed. No test database or catalogue fixtures were created.
- All imported works remain in review, have creation-date bounds ending by 1970, and have no accepted museum holding or current-display assertion.
- These are data correctness checks, not evidence of ten-million-row performance. No query or application code was changed.

## Evidence and recovery

- [Full artwork list](ARTWORKS.md), [application plan](application-plan.json), [application receipt](applied.json), [database verification](verification.json), [API verification](api-verification.json).
- Artist profiles, raw page/API captures, selection decisions, rights labels and checksums are retained in this directory.
- Recovery dump and exact transaction preimages: `/Users/vadimdulub/Library/Application Support/Artline/backups/africa-asia-cyprus-20261005/`.
- Validated pre-import dump: **782,000,069 bytes**, SHA-256 `b3fcd45ab8a47e9d838e14a25909a6106710f64703b836b10830c5ada5a93c89`.
- Downloaded originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/africa-asia-cyprus-20261005/`.
- Served derivatives: `apps/web/public/assets/artworks/imported/africa-asia-cyprus-20261005/`.
- Disposable visual proof sheets remain under `/tmp/artline-regional-review-*.jpg`.
- Entry point: `ops/research-africa-asia-cyprus-20261005.py`; local importer: `ops/apply-africa-asia-cyprus-20261005.py`.

## Production delivery

The user requested production delivery after the local import. Production preflight found all 177 artworks absent, reconciled 33 existing artist identities and selected 14 new profiles. The transaction inserted the exact reviewed records, citations, identifiers, 37 sourced artist-country relationships and personal collection membership. Existing artist records were preserved. The 43 selected JPEGs were uploaded with a create-only storage precondition and verified against their saved checksums.

Cloud SQL backup **1791221858401** completed successfully before the import. The production plan is pinned at SHA-256 `63d0ae3ced7d02e143ca2145b1fb4230659d466d3bc63b04b7757228d840c7f7`. Backup metadata, transaction preimages and the delivery script archive are under the local backup directory's `production/` subdirectory.

Read-only production checks confirmed every inserted field, all 177 live research detail responses and all 43 live image hashes. All 14 new artist pages passed on `artlines.org` and retain `noindex`; three sampled artwork responses and three image hashes also passed on the canonical domain. Published-only requests for three sampled review works returned 404. The existing research-preview configuration was preserved; creation dates, unknown fields, review status and the absence of accepted holding/display assertions match the local batch.

Production evidence: [pinned plan](production/plan.json), [backup receipt](production/backup.json), [storage receipt](production/storage.json), [import receipt](production/applied.json), [live verification](production/verification.json), [canonical-domain checks](production/canonical-domain-verification.json), [artist-page checks](production/artist-page-verification.json). Delivery entry point: `ops/deliver-africa-asia-cyprus-20261005.py`.
