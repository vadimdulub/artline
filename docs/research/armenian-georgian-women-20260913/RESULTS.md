# Completed Armenian/Georgian research and Women artists filter

Both databases received the same reviewed batch:

| Result | Local | Production |
|---|---:|---:|
| New artwork records | 271 | 271 |
| New artist profiles | 41 | 41 |
| New verified images | 38 | 38 |
| Artwork dates retained as unknown / conflicting | 94 | 94 |
| Named-creator objects awaiting profile reconciliation | 5 | 5 |
| Women artists with source evidence, total | 521 | 521 |

All 271 new artworks and 41 new profiles remain in review. The five unlinked objects retain Hovsep Pushman's supplied name and provenance; no biography or lifespan was fabricated. Seven other object labels were reconciled to exact authority profiles created elsewhere in this same batch. There were no duplicate artwork identities in either target plan, and no existing artworks or images were replaced.

The 38 images total 2,476,056 bytes; each is a JPEG of at most 99,886 bytes, preserves the source frame, has an explicit Commons public-domain label, source identity evidence, credit and checksums. Images were visually checked, uploaded to Cloud Storage, and linked in both databases. Local and production painter-scoped API/asset smoke checks passed for representative Armenian and Georgian works.

Image coverage includes Vardges Sureniants (8), Gevorg Bashinjaghian (7), Yeghishe Tadevosyan (6), Arshak Fetvadjian (3), Panos Terlemezyan (3), Ivan Aivazovsky (3), Yenok Nazarian (2), Zakar Zakarian (2), and one each for Gigo Gabashvili, Alexander Mrevlishvili, Hmayak Hakobyan and Charles Garabed Atamian.

The **Women artists** checkbox is immediately before **Only popular painters**. It combines independently with popularity and other filters. The 519 initial women-artist identities were supplemented by Gohar Fermanyan and Mariam Aslamazian. Two conflicting initial identity records remain deferred. Server filtering, counts/facets/options, URL history, desktop/mobile layout and local data checks pass; see [filter validation](FILTER-VALIDATION.md).

Armenia was missing from the database's country reference table and was added using AM / Western Asia, consistent with the existing region taxonomy and [UN M49](https://unstats.un.org/unsd/methodology/m49/overview). Explicit source affiliations are retained alongside citizenship and other country relationships. Local API verification returned 41 Armenia-filtered profiles, 9 Georgia-filtered profiles, and 2 women under the Armenia filter. These are overlapping source-based memberships, not exclusive nationalities.

To explore the new artist profiles, turn off **Only popular painters** and select Armenia or Georgia. Review artwork pages are available through the painter chronology. Museum collection assertions remain in review; the holding projection therefore stays unset until validation, and museum-specific holding pages do not imply acceptance of these claims. Owner research selections are distinguished from museum-designated masterpieces. No on-view claims were added.

The feature code was implemented and tested locally, with database migration/evidence and artwork/image data applied in production during the research session. Following the user’s subsequent authorization, the application was also deployed and verified in production. See the [production release evidence](production-release/README.md). No commit was created.

Read the [research synthesis](RESEARCH.md), [271-work inventory and image credits](INVENTORY.md), [709-authority discovery index](ARTISTS.md), and [final database verification](verification-final/final-verification.json). The survey and capped queries are not a claim of exhaustive coverage or 12,753 imported artworks.

![Reviewed selected reproductions](quality-review/contact-sheet.jpg)

## Recovery and provenance

Pre-mutation local dump: `/Users/vadimdulub/Library/Application Support/Artline/backups/armenian-georgian-women-20260913/local-before.dump` (387,655,407 bytes; SHA-256 `302ef1b42300a0a5ad37d1fa61f748ad0cda01a64b0248b29cb1162783377de6`). Verified successful Cloud SQL backup: `1789326954000`.

Original selected reproductions are preserved under the same backup directory in `selected-originals/`. Research captures, primary citations, identity evidence, native-title captures, immutable plans, application receipts and the final archive manifest are retained with this session. No test database or test fixture was created in the real catalogue.
