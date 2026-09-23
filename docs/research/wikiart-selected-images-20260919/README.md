# WikiArt selected image delivery — 19–20 September 2026

Completed: 674 additional reproductions for 95 existing artist profiles; 674 local artwork attachments and 644 production attachments. All 674 files were uploaded, and all public image URLs were verified against the prepared SHA-256 hashes. Thirty production identities were absent or differed from the local catalogue and were preserved rather than overwritten.

The application JPEGs total 47,767,393 bytes. Every served image is at most 100,000 bytes, resized proportionally without cropping. Larger original downloads are separate source archives, not served application assets.

The user selected artworks created more than 70 years ago and explicitly requested public image visibility without independent rights-clearance review blocking this campaign. Selection uses creation dates ending in or before 1955. WikiArt's labels remain truthful: 639 public-domain labels and 35 copyright-protected labels stored as `restricted`. Artwork age is not represented as a copyright licence. Existing artwork metadata and publication states were preserved.

## Verification and live display

- [Completed verification](verification-674-1789853313.json): 674 local attachments, 644 production attachments, 674 exact public-file checksum checks and 30 public artwork API samples; no errors.
- The Go media readers now return attached storage paths regardless of rights label, verification timestamp or missing alt text. Source links and labels remain in the API response.
- Production backend revision `artline-api-images-0920` receives 100% of traffic. Previous revision `artline-api-atlas-0918` remains available for rollback. The frontend was not redeployed.
- Cloud Build `16cd40a2-3dc5-44bb-8c94-3b31a4d85d6d`; image digest `sha256:f762596ec37fa753c5d56ae0ce96634320ecdb1b4597e35ac00b4f03f8fb3350`.
- Full Go server suite passed. Opt-in real-catalogue read-only tests checked 12 actual restricted/unverified media examples across artist, atlas and museum readers. Existing scoped museum query-plan checks also passed; these checks do not establish ten-million-row capacity.
- Nine Python identity, date, source-label and immutable-evidence checks passed. No test database or fixture was created in the real catalogue.

## Files and recovery

- `audit-expanded.json`, `discovery-v2/`, `discovered-v2.json`: artist-scoped metadata selection and ambiguous-source exclusions.
- `captures/`, `selected/`, `images/`: source captures, source labels, selected identities and compressed-image checksums.
- `delivery-plans/`, `delivery/`: immutable target plans and application receipts. `prepare-held-history/` retains resolved preparation exceptions.
- Application assets: `apps/web/public/assets/artworks/wikiart/` and corresponding objects in `gs://artline-508319-images/assets/artworks/wikiart/`.
- Exact target preimages: `/Users/vadimdulub/Library/Application Support/Artline/backups/wikiart-selected-images-20260919/`.
- Downloaded originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/wikiart-selected-images-20260919/`.

Scripts: `ops/wikiart-selected-images.py` and `ops/test_wikiart_selected_images.py`. Follow-on artist-directory coverage is recorded in `../wikiart-artist-coverage-20260920/`.
