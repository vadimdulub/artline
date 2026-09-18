# Overnight country research — 13–14 September 2026

Start with the [complete report](chatgpt-handoff/final-20260914/REPORT.md), [ChatGPT instructions](chatgpt-handoff/final-20260914/RESEARCH_PROMPT.md) and [handoff guide](chatgpt-handoff/final-20260914/README.md).

The [verified upload package](chatgpt-handoff/artline-research-20260914-chatgpt.zip) contains 41 CSV files plus evidence, reports and audit receipts. Its SHA-256 is `b4a6721ded3f15824a33cff3e419043bff5fda8d4329b344aaed3732497891f4`. The package contains metadata and image-source links; recovery dumps and artwork binaries remain in their dedicated locations.

Twenty rounds for each of NL, GR, RU, FR, IT, ES, DE, AT, BE and FI were imported and verified in both databases. Additional Greek research was delivered; Portugal's 20 scopes produced 74 prepared candidates, with eight holds and no imports yet. The local-only follow-ups and production resume order are documented explicitly.

| Session result | Local | Production |
|---|---:|---:|
| Gross added artwork rows | 2,718 | 2,717 |
| Gross added creator profiles | 610 | 610 |
| Verified selected image assets | 1,535 | 1,506 |
| Active primary images from this session | 1,525 | 1,496 publicly observed |
| Artwork duplicates consolidated | 438 | 238 |
| Painter duplicates consolidated | 60 | 56 |

All active additions remain **In review**, with no invented publication or display claims. Of the active added works, 2,705 have a qualified creator-country relationship; two retain only a rejected historical attribution to Isaac Walraven and intentionally have no artwork country. The 610 added profiles all have cultural-affiliation records. The catalogue-wide country-gap queue still contains 3,589 active profiles.

An inserted row is not automatically a new physical discovery: 212 active additions were reconciled to older/other catalogue identities, and 11 added rows were subsequently archived. Original assertions, links, assets and recovery evidence were preserved. Remaining similarity groups are research leads, not a deletion list.

Cloud authentication expired during the run for `vadim@alingva.com`. [Resume instructions](chatgpt-handoff/final-20260914/RESUME_PRODUCTION.md) describe the queued production differences and guarded command. No alternate account was used, no Terraform apply or deployment was performed, and no records were published.

Recovery data is under `/Users/vadimdulub/Library/Application Support/Artline/backups/overnight-countries-20260913/`. Both the initial local dump and the final `local-after-20260914.dump` are retained; the final dump was hash-checked and inspected with `pg_restore --list`, without a restore or test database. Cloud SQL backup `1789326339640` succeeded before the first mutations. Selected original images are under the corresponding `Artline/source-images/overnight-countries-20260913/` directory; served derivatives remain in `apps/web/public/assets/artworks/`.

`WORKLOG.md` preserves the investigation history. Application receipts identify this session's work separately from concurrent imports. The original and final session indexes are immutable snapshots. The final local audit, public production ID observations, image checks and package validation are separate artifacts; public API observation does not claim transactionally consistent production database parity.
