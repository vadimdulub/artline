# Creator reconciliation follow-up — 13 September 2026

Completed in **both local and production**: **967 retained artworks linked to 129 existing painters**. No painters or artworks were created, deleted or merged. Every selected artwork remains in review. The user's research scope explicitly includes new museums and collections beyond the original 342 institutions; creator reconciliation has no restriction to that earlier institution list.

| Evidence source | Artwork links |
| --- | ---: |
| joconde | 502 |
| smk | 323 |
| lombardia | 53 |
| wikidata | 32 |
| rijks | 21 |
| walters | 14 |
| tate | 11 |
| moma | 5 |
| fng | 3 |
| mia | 3 |

The Wikimedia subset includes 32 works from the preceding museum-catalogue pass, including works by Konstantinos Volanakis, Théodore Ralli and Guercino. The remaining links use preserved official museum captures and exact object matches from earlier research. Missing metadata was retained: **101 unknown creation dates** and **100 unknown artwork types** stayed unknown. Titles, museum fields, images and painter biographies were unchanged.

## Identity policy and unresolved cases

Audited **76,932 unlinked review artworks**, representing 28,192 distinct object-level creator labels, against the current 11,315 active painter identities. Reviewed 24,003 unresolved works with official creator facts and previous exact-object matches restricted to still-unresolved original CSV identities.

A link requires an exact museum person/Wikidata identifier, or a documented full-name variant plus **both matching lifespan boundaries**. Contradictory known dates, ambiguous identities, qualified attributions, archived/non-person records, impossible artwork/lifespan relationships and conflicting existing Wikidata identities are held. An existing source hold is not bypassed by a later matching source. No name-only or fuzzy identity merges are made.

Guercino's older Q110476382 identifier is an explicit Wikidata redirect to Q334262. Its captured redirect evidence supports the existing painter identity without renaming or replacing the original authority record. See `guercino-redirect.json` and [the source identity](https://www.wikidata.org/wiki/Q334262).

**75,965 unlinked review artworks remain in each database.** These are unresolved records, not rejected/deleted artworks. The hold log records decision attempts and can include more than one reason for a work; it is not a count of unique remaining artworks. Anonymous and workshop/uncertain identities retain object-level labels rather than fabricated person links.

## Guarded application and verification

Plan SHA-256: `311ced7cedb54d7dbb751d0133ebe9bac7d76bfdb15c0425a5c17b084ecba900`. Both databases passed current-record preflight before writes. Ten serializable batches per database (at most 100 artworks each) add one primary creator link, clear the resolved object-level label, and add a citation preserving the original label, source evidence, painter identity and plan checksum. Original research facts, supplied CSV cells and their checksums are rechecked. The existing ingestion advisory locks are used.

Read-only verification checked every intended link/citation, publication status, unchanged metadata and painter records, original CSV/source evidence, and exactly 967 fewer unresolved artworks. Full artwork and painter row counts did not change. Local retains its pre-existing three-row artwork/painter difference from production; all selected reconciliation mappings match. No media pointers changed during this phase.

Seven offline identity-policy tests passed: namesake ambiguity, insufficient name-only evidence, documented name variants with corroborating dates, contradictory biography despite a person ID, explicit Wikidata redirects, conflicting Wikidata authorities and workshop labels. No real-catalogue test fixtures or test databases were created. A read-only indexed lookup on 100 actual linked artworks completed in 1.259 ms locally. This is not a ten-million-row load benchmark.

## Live URL correction

Live checks exposed an existing validation bug affecting **322 newly linked artworks across 31 painters**: source-derived slugs such as `niels-bjerre-smk-132_person` were rejected by chronology and painter-filter validation. The profile endpoint already returned 200, while its artwork detail returned 404. Existing stable painter slugs were preserved; the API now accepts single underscore separators for artist identities while museum/movement validation remains unchanged.

The backend HTTP/catalogue tests passed with real-database fixture opt-ins unset. Three old invalid-input tests now use a double underscore to retain malformed-input coverage. The first local test invocation encountered a stale GOROOT setting; rerunning with that stale variable unset succeeded. An initial Cloud Build source upload used a bucket the existing build service account could not read; the successful build used the already-configured private build-source bucket, without any IAM changes.

The isolated release uses tracked server source from commit `b848edcbbf3deebba817fc40dc477dfc14503520` (server code identical to deployed `bac160f`) plus `artist-slug-fix.patch`; unrelated workspace changes were excluded. Build **1d542be9-fe5b-4887-a245-a57f5ecbe729** succeeded with API digest `sha256:f46b649efdc16e9ced7168ce99237e3924ad5810315ff5f7999e37c073cf7138`. No Git commit was created for this follow-up.

Release tag: `20260913-creator-slugs-57a4f08a`. Live revisions: **artline-api-00010-98s** and **artline-web-00010-5nl**, both at 100% traffic. The web image's digest was reused unchanged. Terraform's saved plan was checked down to the changed field paths: only the two container image references changed, with zero resource additions/removals. The local image-tag variable now matches the release, and the final full Terraform plan reports no changes.

After deployment, **43 public artwork checks** passed across all ten evidence sources and all 31 affected legacy painters. Painter options and timeline filters also accepted the legacy identity. The anonymous editor-coverage endpoint still returned 401. See `live-verification.json`. No browser interaction test is claimed.

## Recovery and durable evidence

- Fresh local full dump: `/Users/vadimdulub/Library/Application Support/Artline/backups/creator-reconciliation-followup-20260913/local-before.dump`; custom archive listing and SHA-256 verified before writes.
- Fresh successful Cloud SQL backup: **1789320088588**, completed at 17:22:59 UTC before reconciliation writes.
- Full selected artwork/painter preimages and backup receipts are under `/Users/vadimdulub/Library/Application Support/Artline/backups/creator-reconciliation-followup-20260913`.
- Audit inventories, pinned plan, hold reasons, per-batch receipts, both database verification reports, source redirect capture and release evidence are beside this report.
- `archive-receipt.json` records the final private Google Storage evidence archive. Terraform binary plans and any credential-bearing configuration remain outside the archive in the private temporary deployment directory.
