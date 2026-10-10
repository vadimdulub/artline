# Local missing-image recovery — 5–6 October 2026

**411 new pictures are saved locally and attached to existing database artworks.** This recovery has reviewed 1,097 distinct artworks, including alternate-file searches and native museum follow-ups. Of these, 686 still need source, identity or rights work. Recovery of the broader catalogue remains open.

The verified additions comprise fourteen Commons images, 88 photographs from the Academy of Fine Arts Vienna, eleven from Wien Museum, seven from the National Gallery of Art, Washington, one directly from the National Museum in Warsaw, and 290 from the Walters Art Museum. Every attachment has source evidence, an approved licence, a visually inspected reproduction, an archived original and a full-frame application JPEG of at most 99,993 bytes. Museum and photographer credits are retained where required. All 411 live database primary-image references, local files, archived originals, creator links and identifiers were checked together. Earlier per-operation HTTP checks passed for 65 attachments. The last server checks timed out, so 346 recent attachments still lack a completed HTTP delivery receipt; the server was not restarted or checked again in these operations.

At this checkpoint the local catalogue contains 300,038 artworks, with 197,846 lacking a primary image. This recovery began with 298,858 artworks and 197,077 missing images. Concurrent work increased both catalogue size and the missing-image count by a net 1,180; this recovery attached 411 images to existing records. Thus the global missing-image count must not be read as this recovery's change alone. This recovery created no catalogue records or fixtures. Artwork titles, creation dates, holdings, creator links, identifiers and review status were preserved. Production was not changed.

Application JPEGs are under `apps/web/public/assets/artworks/imported/<operation>/`. Original reproductions and visual review sheets are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/<operation>/`. Locked preimages and correction recovery snapshots use the corresponding `backups/<operation>/` directories. Exact operation names appear in the linked reports and CSV.

| Operation | Records assessed in operation | Net attached images |
| --- | ---: | ---: |
| [Initial Commons recovery](../local-commons-recovery-20261005/README.md) | 180 | 3 |
| KHM Commons source review | 80 | 0 |
| Commons follow-up | 120 | 3 |
| Alternate Commons files | 30 revisits | 2 |
| [Academy native images](../local-academy-images-20261006/README.md) | 80 | 26 |
| [Academy follow-up](../local-academy-followup-images-20261006/README.md) | 18 | 13 |
| [Academy reconciled cases](../local-academy-reconciled-images-20261006/README.md) | 9, including 6 revisits | 8 |
| [Further Commons review](../local-commons-priority-followup-20261006/README.md) | 120 | 1 |
| [Academy person-reference review](../local-academy-person-review-20261006/README.md) | 10 revisits | 10 |
| [Wien Museum exact photograph](../local-wien-native-image-20261006/README.md) | 1 revisit | 1 |
| [Wien Museum follow-up](../local-wien-followup-images-20261006/README.md) | 17, including 4 revisits | 8 |
| [Academy identity and date review](../local-academy-identity-followup-20261006/README.md) | 19 revisits | 19 |
| [NGA current native downloads](../local-nga-native-images-20261006/README.md) | 7 | 7 |
| [Wien identity reconciliation](../local-wien-reconciled-images-20261006/README.md) | 2 revisits | 2 |
| [Academy inventory and date review](../local-academy-inventory-review-20261006/README.md) | 25 revisits | 11 |
| [Academy self-portrait reverse](../local-academy-verso-image-20261006/README.md) | 1 revisit | 1 |
| [Multiple Commons files and current Warsaw IDs](../local-commons-multiple-images-20261006/README.md) | 5 revisits | 2 |
| [Psyche photographer alternate](../local-commons-photographer-alternate-20261006/README.md) | 1 revisit | 0 |
| [Warsaw native self-portrait](../local-commons-warsaw-followup-20261006/README.md) | 1 | 1 |
| [Native museum priority audit](../local-open-museum-priority-images-20261006/README.md) | 19 | 0 |
| [Anonymous/workshop Byzantine review](../local-byzantine-commons-image-review-20261006/README.md) | 7 | 0 |
| [Further Commons review](../local-commons-next-images-20261006/README.md) | 100 | 1 |
| [Walters native CC0 images](../local-walters-native-images-20261006/README.md) | 30 | 23 |
| [Walters native follow-up](../local-walters-followup-images-20261006/README.md) | 30 | 22 |
| [Later Walters paintings](../local-walters-later-images-20261006/README.md) | 30 | 27 |
| [Mid-century Walters images](../local-walters-midcentury-images-20261006/README.md) | 40 | 31 |
| [Walters individual reconciliation](../local-walters-reconciled-images-20261006/README.md) | 26 revisits | 19 |
| [Walters authority follow-up](../local-walters-authority-followup-images-20261006/README.md) | 40 | 40 |
| [Later Walters authority follow-up](../local-walters-authority-later-images-20261006/README.md) | 40 | 38 |
| [Walters image-file concordance](../local-walters-asset-concordance-images-20261006/README.md) | 7 revisits | 4 |
| [Further Walters authority follow-up](../local-walters-authority-next-images-20261006/README.md) | 40 | 40 |
| [Byzantine independent-photographer lead](../local-byzantine-photographer-review-20261006/README.md) | 1 | 0 |
| [Reviewed Byzantine icon face](../local-byzantine-reviewed-face-image-20261006/README.md) | 1 revisit | 1 |
| [Reviewed Russian Deesis panel](../local-walters-reviewed-panel-image-20261006/README.md) | 1 revisit | 1 |
| [Walters images dated 1880–1915](../local-walters-authority-modern-images-20261006/README.md) | 40 | 40 |
| [Further twentieth-century Walters images](../local-walters-authority-final-images-20261006/README.md) | 7 | 5 |
| [Cleveland native and independent-photo review](../local-cleveland-commons-images-20261006/README.md) | 4 | 0 |
| [Further Commons review and Dou reproduction](../local-commons-later-images-20261006/README.md) | 80 | 1 |

Counts in the table overlap; the combined total is 1,097 distinct artworks. The licence breakdown is 99 CC BY, twelve public domain, one CC BY-SA, 298 CC0 and one attribution-only licensed photograph. These are image-use decisions, not artwork publication decisions. The Fabritius and Dou additions and 74 Walters additions are source-provided monochrome archival reproductions; that limitation is retained in their database attribution and evidence.

The [Walters creator-qualification audit](../local-walters-creator-qualification-20261006/README.md) made the native `(?)` marker explicit in seven earlier image credits and their stored evidence, with no artwork or image-byte changes. Together with one separately attached qualified work, eight Walters images retain this uncertainty explicitly. The [latest native-source audit](walters-source-audit-411.json) reparsed all 290 Walters source captures and photograph-specific grants using the current validators, including the recent-creator copyright guard. All complete stored evidence was also checked against the live database. Stable native person IDs resolved name variants without changing artist records. Four individually approved filename differences are supported by the museum's explicit object-to-image list, with no general relaxation of inventory matching.

The [Walters policy review](../local-walters-authority-followup-images-20261006/source-policy-review.json) retains the museum's artist-copyright exceptions. The latest selections hold the parent album 35.101 for a truthful component-view workflow and the Zamacois image 37.2934 for missing per-photograph permission. One Bonvin download returned an empty body; a separately licensed and visually checked front from the same page was attached instead, with the failed response preserved privately.

The [further Walters follow-up](../local-walters-authority-next-images-20261006/README.md) preserves Inness’s exact `1867/1880` date phrase, resolves the Fortuny name variant through its museum person ID and checks six treatment-view fronts. Two empty downloads have individually reviewed same-page replacements. One large Gifford source uses a SHA-pinned, bounded JPEG decoder path; the general size limit remains in place.

The [reviewed Byzantine face attachment](../local-byzantine-reviewed-face-image-20261006/README.md) adds an exact-inventory independent photograph for Athens icon ΒΧΜ 00995, with separately scoped public-domain artwork and attribution-only photograph permissions. The image-only operation preserves its unknown catalogue dates and PostgreSQL date scope of `review`; the pictured Crucifixion face is explicit in its view label, accessible text and attribution. A [Russian Deesis panel attachment](../local-walters-reviewed-panel-image-20261006/README.md) similarly identifies its Virgin panel and retains the source’s monochrome limitation. Both records keep their anonymous maker labels and review status. No date, maker or publication status was invented.

The [Walters 1880–1915 selection](../local-walters-authority-modern-images-20261006/README.md) adds forty images, including a complete open Russian triptych, a clearly labelled album cover and individual album leaves. The triptych maker’s native activity dates are not treated as established birth/death years. One empty display URL was resolved through the museum’s download endpoint for the exact same licensed photograph. Across this recovery, three images have explicit partial-view labels: two icon faces/panels and one album cover. One icon retains unknown catalogue creation dates and date scope `review`.

The [further Walters selection](../local-walters-authority-final-images-20261006/README.md) adds five Brödel/Burroughs photographs and leaves two later-creator rights cases held. The [Cleveland review](../local-cleveland-commons-images-20261006/README.md) preserves four missing-image findings, including a conflict between the native Hassam artwork copyright claim and Commons permissions. The [new Commons selection](../local-commons-later-images-20261006/README.md) reviews eighty more records and adds Dou’s complete oval *A Flute Player* reproduction with its RKD credit and monochrome limitation. Three other exact Commons matches remain held under source-specific museum policies.

Eight initially attached museum-source images were withdrawn when conflicting originating-source restrictions were identified: five KHM images, two from Joanneum and one from Salzburg Museum. They are excluded from the 411-image total. Their evidence and bytes remain private, their public files are absent and their image associations are held. Two National Galleries of Scotland/Art UK images and a visually incorrect reproductive print also remain unattached; their derivatives are absent from the public folder. The rejected studio face of a two-sided Subleyras canvas also remains private; its correct self-portrait reverse was attached separately. The Walters photograph showing only the Virgin panel of a three-panel Deesis group was rejected for Full composition use. That decision remains intact; a separate, explicitly labelled Virgin-panel association is now attached. All five historically rejected prepared file paths remain absent from the public folder and their private originals remain intact. The newly approved qualified panel has its own path and evidence. Existing rights holds were preserved. The [source-policy correction review](../local-source-policy-review-20261006/README.md) documents the three additional withdrawals.

- [All 411 attached pictures, source pages and local paths](attached-images.csv)
- [All 1,097 artwork outcomes and source-specific findings](artwork-outcomes.csv)
- [Combined verification and counts](report.json)

Individual reports preserve their historical checkpoint counts; superseded combined CSV/JSON checkpoints are retained in `history/`. This combined report is the latest checkpoint for these thirty-eight operations. Since the previous 405-image checkpoint, ninety-one more existing artworks were reviewed and six received images, bringing the distinct review count from 1,006 to 1,097.
