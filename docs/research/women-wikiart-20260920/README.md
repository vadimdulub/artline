# Frida Kahlo and women artists — 20 September 2026

Completed in local and production: **1,555 image attachments across 189 artists**, comprising **1,534 new review artwork records** and **21 images on existing artworks**. All 1,556 selected files were uploaded and publicly checksum-verified. One duplicate reproduction remains unattached.

The review covers **682 women already in the database**: the original 535 with gender evidence and 147 additional existing artists explicitly listed in [WikiArt’s Female artists directory](https://www.wikiart.org/en/female-artists). No new artist authorities were created.

| Result | Local | Production |
| --- | ---: | ---: |
| Women in the complete review ledger | 682 | 682 |
| Reconciled profiles with review citations | 275 | 275 |
| Added women-filter memberships | 147 | 147 |
| Added image attachments | 1,555 | 1,555 |
| New review artworks with personal collection membership | 1,534 | 1,534 |
| Existing artworks given an image | 21 | 21 |

## Frida first

[Frida Kahlo’s WikiArt profile](https://www.wikiart.org/en/frida-kahlo) was processed first. Six images were added: *The Two Fridas*, *The Dream (The Bed)*, *Roots*, *The Broken Column*, *The Wounded Deer*, and *My Grandparents, My Parents, and I*. Four are new review records; two fill existing records. The bilingual *The Two Fridas (Las dos Fridas)* identity was reused, preserving its existing metadata.

Frida now has **ten illustrated review artworks** in each database: all nine profile highlights and the existing Family Tree record. All ten public images and artwork API responses passed [verification](frida-verification.json). The six added reproductions were also visually inspected.

## Complete artist coverage

[The artist-by-artist CSV](all-women-review.csv) lists all 682 women, their source profiles when matched, additions in each database, current artwork/image counts and selection holds.

All 639 entries in WikiArt’s women directory were captured across eleven pages and reconciled against the real catalogue and the prior complete A–Z survey. Of the 275 matched profiles, 189 received images. The other 86 had no additional selected image because of existing coverage, date eligibility or identity constraints. **407 women have no confirmed profile in the surveyed WikiArt directories**; their records and unknown fields were preserved.

The 147 women-filter additions rely on explicit source inclusion. Every addition passed [the public filter API check](public-women-filter-verification.json). All 275 reviewed artists received citations while their existing biographies, dates and publication states remained unchanged.

Rosalba Carriera, Leonor Fini and Valentine Hugo required further reconciliation because source birth years disagree. Their existing Wikidata identities explicitly link the WikiArt profiles through P6002. Captures and disagreements remain in `identity-authorities/` and `supplemental-artist-matches.json`; no lifespan was overwritten.

## Selection and identity review

This bounded highlight pass selected at most twelve additional featured works per matched artist, plus Frida’s existing-record image gaps. The continuing WikiArt rule requires creation dates ending by **1955**. Approximate dates and ranges remain intact; unknown dates and museum holdings were not invented.

Twenty-six possible title/edition matches were held before download. Fifty-eight later same-title cases were visually distinguished as separate portraits, compositions, illustration pages, card designs or stained-glass panels. See [the visual decisions](reviewed-title-decisions.json). Source titles and attributions remain review claims.

Lilla Cabot Perry’s *The Black Hat* variant shows the same composition as an already illustrated record. Its additional source ID is preserved in a source-variant citation on that existing artwork in both databases. The canonical identifier and primary image are unchanged; no second artwork was created. See `held-source-duplicates.json` and `duplicate-source-mapping/`.

Elin Danielson-Gambogi’s *The Piano Player* and *Pianospelare* have separate source IDs but identical image bytes. Both supplied review records carry an explicit shared-reproduction citation pending editorial reconciliation. Counts describe source records and attachments; these two records do not establish two distinct compositions. See `source-duplicate-evidence/`.

Gwen John’s *Nude Girl* had different database UUIDs. Its identical deterministic research slug, artist, title, dates, dimensions, medium and other artwork metadata established the existing production match. Exact preimages and the former hold remain in `target-identity-resolutions/` and `target-identity-history/`.

## Delivery and verification

The 1,556 JPEGs total **93,597,546 bytes**; the largest is **99,983 bytes**, below the 100,000-byte limit. They retain the full source frame with proportional resizing and JPEG compression. Larger originals are archived separately.

WikiArt supplied 1,056 public-domain labels, 499 copyright-protected labels retained as `restricted`, and one unspecified label retained as `unknown`. These labels follow the recorded collection/display instruction in [Artline image use](../../ARTLINE_IMAGE_USE.md). Artwork age was not converted into an independent licence or clearance claim.

[Final delivery verification](verification-1556-1789909855.json) passed with **zero errors**: all 1,556 local/public image hashes, both databases’ media and artwork states, all 1,534 new review records and personal memberships per target, and 40 sampled public artwork API responses.

[The scope audit](completion-audit-1789909795.json) also passed with zero errors: 682 women per target, 275 unchanged artist records and citations per target, recovery/source-capture hashes, date eligibility and selection evidence for every attachment. Separate checks cover Frida’s ten images and all 147 new public filter memberships.

Twenty existing date, identity and source-label unit tests passed without a test database or catalogue fixtures. This is correctness verification, not a ten-million-row load test. No application deployment, Terraform apply or commit was performed.

## Recovery and evidence

- Exact preimages: `/Users/vadimdulub/Library/Application Support/Artline/backups/women-wikiart-20260920/`.
- Original downloads: `/Users/vadimdulub/Library/Application Support/Artline/source-images/women-wikiart-20260920/`.
- Served derivatives: `apps/web/public/assets/artworks/wikiart/`.
- Final selection: `final-selected.json`; previous selections remain in `selection-history/`.
- Captures, profiles, artist applications, image manifests, upload/attachment receipts and personal-selection receipts remain in this research directory.
- Entrypoint: `ops/women-wikiart-20260920.py`, using `/tmp/artline-popular-20260917-venv/bin/python`.

Earlier progress logs include subsequently resolved holds. Final receipts show one intentional unattached duplicate variant and no unresolved delivery failure.
