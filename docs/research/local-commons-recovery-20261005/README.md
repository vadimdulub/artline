# Local missing-image recovery — 5–6 October 2026

Latest checkpoint: the [combined recovery report](../local-image-recovery-20261006/README.md)
includes this work and the Academy/Wien Museum/NGA/Warsaw/Walters/FNG/SMK/Rijksmuseum/Chicago/WikiArt follow-ups: 897 attachments across
1,765 distinct reviewed artworks. The eleven-image counts below describe the
earlier Commons checkpoint. Three of those eleven attachments were subsequently
withdrawn after the [additional source-policy review](../local-source-policy-review-20261006/README.md);
the current combined count excludes them. Subsequent Commons follow-ups bring
the current Commons contribution to fourteen pictures, including the separately
qualified Byzantine icon-face photograph.

Added **11 verified Wikimedia Commons reproductions to existing local review
artworks**. The local application served all eleven files with matching SHA-256
checksums. No artwork, artist, date, holding, publication state or production
record was created or changed by this image recovery.

The read-only selection reviewed 380 distinct missing-image artworks across
three bounded sets. A further 30 file reviews examined alternative reproductions
for some of those same artworks. These sets do not constitute a review of the
entire missing-image catalogue: 197,066 local records still lacked a primary
image at the final audit. Continued research remains necessary.

## Verified results

- [Session report and exact attached image paths](session-report.json)
- [Eleven attached artworks, sources, licences and checksums](session-attached-images.csv)
- [All 380 artwork decisions](session-artwork-outcomes.csv)
- [Local application HTTP and checksum verification](local-http-verification.json)
- [First set: final verification after source-policy correction](verification-after-source-review.json)
- [Alternate-file attachments](../local-commons-alternates-recovery-20261006/verification.json)
- [Follow-up attachments](../local-commons-followup-recovery-20261006/verification.json)

Final outcomes: 11 attachments, 281 requiring further identity/image/rights
research, 80 source-policy holds, seven existing rights holds preserved, and one
rejected reproductive print. All accepted images are full-frame JPEG renditions
no larger than 100,000 bytes. The source reproductions, file revisions, licence
URLs, credits, metadata receipts and image transformations are retained.

The added artists are Egon Schiele, Benedicte Scheel, Edward Okuń, Hubert Sattler,
Karl Heffner, Piotr Stachiewicz, Friedrich von Amerling, August Kurtz, Bernhard
Strigel, Juan Fernández Navarrete and Maximilian Pirner. Each artwork retains its
original review status and catalogue facts.

## Source-policy correction

The first operation initially attached eleven images. A subsequent inspection
of earlier rights evidence established a KHM museum-source conflict that also
applied to five new files. Those five attachments were reversed, their media
records marked unknown and removed from serving, and their exact bytes retained
privately. The earlier verification is historical; the final six-image receipt
linked above supersedes it. No older media or artwork records were removed.

The [correction receipt](source-policy-correction.json) records the affected IDs
and locked recovery snapshots. KHM's indexed
[image database terms](https://www.khm.at/fileadmin/pdf_KHM/agb/AGB_Bilddatenbank.pdf)
still describe noncommercial reuse; the direct PDF fetch returned 403, so no
successful direct PDF capture is claimed. Museum-source images from the selected
KHM set were held. One RKD reproduction of a lost Van Dyck painting was visually
rejected as a printed reproduction and archived without attachment.

Two selected National Galleries of Scotland / Art UK images were also held:
the museum's [image licensing policy](https://www.nationalgalleries.org/copyright-image-licensing)
restricts reuse, and an unrestricted primary-source licence for those exact
Art UK images could not be verified. These are operational source-clearance
decisions; they do not alter attribution, underlying artwork copyright claims,
or museum holdings.

## Storage and recovery

Served files are under `apps/web/public/assets/artworks/imported/`, in these
operation directories:

- `local-commons-recovery-20261005/` — six retained images.
- `local-commons-alternates-recovery-20261006/` — two images.
- `local-commons-followup-recovery-20261006/` — three images.

All 19 downloaded source reproductions and the four visually inspected contact
sheets are preserved under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/`, using the
corresponding operation names. Rejected/held derivatives remain in those private
directories or the correction recovery archive. Per-set
`visual-review-archive.json` files identify the preserved contact sheets and
their hashes.

Locked pre-mutation artwork, creator and identifier snapshots are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/`, also grouped by
operation name. Each successful attachment transaction checked the pinned
artwork and creator/identifier preimages and preserved existing images.

The operational runner is [recover-local-commons-images-20261005.py](../../../ops/recover-local-commons-images-20261005.py).
Its phases separate selection, source research, download, manual visual review,
local attachment and verification. It has no production upload path. Sources
were read serially with the existing provider rate gates. When the Wikidata
Action API continued to report replication lag after its bounded retries,
published entity JSON supplied revisioned authority evidence; Commons file
metadata, licences and structured object identity were fetched independently.

This is an operational audit of the real catalogue. No test database or
catalogue fixtures were created. It is not a 10-million-row load/performance
proof. No commits or deployments were performed.
