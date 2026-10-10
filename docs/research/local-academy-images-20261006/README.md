# Local Academy Vienna image recovery — 6 October 2026

Attached 26 verified museum photographs to existing local artworks after reviewing 80 missing-image records. All 26 files load through the local web app and match their database SHA-256 checksums. The catalogue now has 197,040 records without primary images out of 298,858; further recovery remains open.

The photographs come directly from the [Academy of Fine Arts Vienna collection](https://collection.kunstsammlungenakademie.at/). Each exact photograph has an explicit CC BY 4.0 licence and both museum and photographer attribution. Selection reconciled the stored Wikidata identity, current authority claims, unique native museum inventory number, unqualified artist and object-level creation evidence. Eighteen individual title/name variations were reviewed against pinned native records; seventeen passed the other checks. For Vermeyen and Pynacker, native artist lifetimes support reproduction rights only: missing catalogue biographies and dates were not filled.

Both contact sheets were visually inspected. Downloaded originals and review sheets are preserved under `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-academy-images-20261006/`. Full-frame application JPEGs are in `apps/web/public/assets/artworks/imported/local-academy-images-20261006/`, each at most 99,457 bytes. Locked transaction preimages are in the matching `backups/` directory; the backup receipt records their path and checksum.

Only primary image references, revision bookkeeping, media associations and image-rights evidence were added. Artwork titles, dates, institutions, creator links, identifiers and review status were preserved. No catalogue fixtures, production uploads or publication occurred.

The other 54 records remain without an attachment from this operation: 13 have differing native search/object creator references; 11 need title reconciliation; 9 have non-unique or missing inventory matches; 8 have absent, multiple or qualified attribution; 6 need creator-rights review; 5 need artist-name reconciliation; 1 lacks object-level date corroboration; and 1 lacks an exact inventory result. These are review holds, not findings that an image cannot exist elsewhere.

- [All artwork outcomes](artwork-outcomes.csv)
- [Attached images and source pages](attached-images.csv)
- [Summary and counts](report.json)
- [Visual decisions](visual-review.json)
- [Database, file and metadata verification](verification.json)
- [Local HTTP, native rights and unchanged artist-year verification](local-http-native-rights-verification.json)

Five offline mutation checks rejected changed licences, wrong image URLs, wrong inventory numbers, wrong artist authorities and missing attribution. Exact source captures, receipts and individual identity reviews remain in this directory. This operation adds to the eleven net images in the [preceding Commons recovery](../local-commons-recovery-20261005/README.md).
