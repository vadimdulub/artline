# Louvre WikiArt images — 6 October 2026

Verified production delivery at 2026-10-06T09:03:08Z.

- Added images to **442 existing Louvre records**, using **441 distinct WikiArt images**.
- Preserved the 33 existing primary images. The Louvre catalogue now has **475 of 3286 records with images**.
- Reconciled date metadata on 423 records: 159 previously unknown numeric dates filled, 68 existing numeric dates/ranges corrected, and 196 changes to date labels or precision only.
- All 442 updated records remain in review. Creators, titles, museum holdings, display assertions and publication state were preserved.
- 2811 records still lack a securely matched image. The final object review held 28 provisional selections because of unresolved versions, studies or dimension discrepancies.

The user instructed: “wiki art is the source of truth” and “go ahead and add as much as possible.” The policy is recorded in [AGENTS.md](../../../AGENTS.md) and [Artline image use](../../ARTLINE_IMAGE_USE.md). Explicit WikiArt dates take precedence once the same object is identified; displayed circa qualifiers and unknown fields are retained. A shared title alone does not establish the same version.

Every selected source has its WikiArt page, image URL, rights label and attribution retained. Originals are archived separately. Derivatives preserve the complete supplied frame and are at most 100,000 bytes; the largest delivered file is 99,994 bytes. WikiArt's public-domain label records its assertion, not an independently obtained licence.

Verification covered all 442 database changes, field-level source citations, rights evidence, automatic audit history and before/after backups. All 441 public image URLs returned HTTP 200 with the expected JPEG bytes and SHA-256 checksum. 10 sampled production artwork API responses returned the expected image and dates.

## Delivery evidence

- [All attached records, source pages and images](delivery-20261006/report.html)
- [Production verification](delivery-20261006/verification.json)
- [Pinned production plan](delivery-20261006/plans/727f2e787002c4c87b2c41d13939dad041e9e031e8164562de72dcfcd57d6f36.json)
- [Final object/version decisions](delivery-20261006/final-object-review.json)
- [343 dimension comparisons and flagged candidates](delivery-20261006/dimension-review.json)
- [Source date, image and visual checks](delivery-20261006/selected-records-qa.json)
- [Sampled production API responses](delivery-20261006/production-api-checks.json)

Backup directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/louvre-wikiart-20261006`. Source originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/louvre-wikiart-20261006`. Per-record before/after snapshots and database audit history preserve the previous values. Catalogue records were not merged or deleted; two independently identified catalogue records share one WikiArt image.

[The original research report](report.html) is an immutable earlier snapshot. Its match counts precede this user-authorized source-precedence and object-review pass; use the delivery evidence above for the production result.
