# Artwork image enrichment completed — 13 September 2026

**12,446 distinct existing artworks now have verified images**, saved locally
and uploaded to Google Cloud Storage. Every JPEG is at most **100,000 bytes**;
the copies total **1,115,534,477 bytes** (about 1.12 GB). Full-frame proportions
are preserved. No generated images were used.

The closing [all-campaign audit](verification-completion-all-campaigns.json)
found **zero errors**. It decoded all local images, compared all GCS object
checksums and sizes, and checked every exact artwork link, media metadata,
rights source, and eligibility/selection predicate in both databases. All
12,446 records remain in **review** on both targets. No painters or artwork
records were added, and no publication or holding/display claims were changed.

| Museum | Images added |
| --- | ---: |
| National Gallery of Art | 3,633 |
| Statens Museum for Kunst | 2,714 |
| Art Institute of Chicago | 2,244 |
| Metropolitan Museum of Art | 2,196 |
| Cleveland Museum of Art | 1,634 |
| Rijksmuseum | 25 |
| **Total** | **12,446** |

The Met total includes four museum-donated CC0 files recovered through
Wikimedia Commons and one retired-ID recovery matched by the exact accession
number in both databases to the museum’s current public-domain record.
Original external identifiers were retained.

## Selection outcomes

The frozen passes covered **16,634 distinct existing eligible artworks**:

- **12,446** images added and verified.
- **4,169** had no image meeting the explicit rights/availability checks.
- **19** remain unavailable after bounded attempts: 17 blocked Chicago image
  URLs and two missing Met API records.

There are **zero unattempted selections, zero prepared-but-not-uploaded files,
and no live import workers**. A final read-only
[remaining-painting check](remaining-painting-scope.json) found no additional
eligible paintings with the supported museum identifiers, selection evidence
and an empty primary-image slot outside the frozen selections. This does not
claim exhaustive image coverage of every artwork or museum in the catalogue.
Unknown/ineligible dates and images without confirmed reuse rights remain
outside this workflow. Matching titles were insufficient for substitution:
one Dürer alternative was rejected because its print accession differed.

## Storage and evidence

- Local images: `apps/web/public/assets/artworks/open-museums/`
- GCS: `gs://artline-508319-images/assets/artworks/open-museums/`
- Rights snapshots, official source responses, file hashes, museum IDs,
  derivatives and append-only upload/attachment events are retained in each
  campaign directory.

The final campaign reports are:

- [Initial 10,000-work selection](verification-final.json)
- [Additional paintings](../image-expansion-20260912-paintings/verification-final.json)
- [Rijksmuseum](../image-expansion-20260912-rijks/README.md)
- [Three Met drawings through Commons](../image-expansion-20260912-commons/verification-final.json)
- [Romney painting through Commons](../image-expansion-20260912-commons-paintings/verification-final.json)
- [Sisley accession-matched recovery](../image-expansion-20260912-retired-met/verification-final.json)

The production URLs of the recovered Sisley and Romney paintings returned
HTTP 200 with the exact saved bytes. Earlier local/production artwork API
and asset checks also passed. Fifteen offline tests cover compression,
identity/rights gates, database reconnection and separation of local
preparation from uploads. Audits used read-only queries on the real catalogue;
no test databases or catalogue fixtures were created. Query-plan evidence and
the remaining ten-million-row load-testing limitation are documented in the
[workflow notes](README.md). Backups and research evidence were preserved.
No commits, deployment or Terraform changes were made.
