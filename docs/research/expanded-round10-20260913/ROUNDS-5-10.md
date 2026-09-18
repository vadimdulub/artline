# Expanded artwork research — rounds 5–10

Completed six consecutive research rounds, bringing this research run through round 10. Each round was backed up, applied to local and production, verified row by row, and checked through the live API before the next round began.

| Round | Artwork links | New painters | Metadata enrichments | Remaining unlinked |
| --- | ---: | ---: | ---: | ---: |
| 5 | 691 | 135 | 691 | 80,936 |
| 6 | 2,128 | 147 | 2,128 | 78,808 |
| 7 | 507 | 14 | 507 | 78,301 |
| 8 | 445 | 55 | 445 | 77,856 |
| 9 | 193 | 193 | 177 | 77,663 |
| 10 | 164 | 0 | 159 | 77,499 |

Totals: **4,128 distinct artworks linked**, **544 new named painters**, and **4,107 artworks enriched**. All selected-row verification hashes match between local and production; no artwork is counted in two rounds.

Rounds 5–8 researched Walters, Smithsonian American Art Museum, Rijksmuseum and Finnish National Gallery holdings. Round 9 established stable named museum creator identities from documented artwork activity where lifespan details were incomplete. Round 10 linked further works to established painter identities. Unknown fields remain unknown; activity periods are explicitly distinguished from lifespan dates.

**77,499 retained artworks still have unresolved creator links.** Existing object-level creator labels and original CSV evidence remain available for further review. Anonymous/unknown creators and qualified attributions remain excluded from this CSV workflow. Conflicting identities and duplicate museum object identifiers were held for review.

These rounds enriched existing review records: no artwork rows were created, deleted or published. Source museum information was not converted into a claim of current display. Metadata research did not download images.

Per-round README, plan, source evidence, backup receipts, application logs, local/production verification and live API receipts are preserved in the sibling round directories. Private source archives and completion evidence are stored under `gs://artline-508319-images/research/expanded-roundN-20260913/`. Backups remain under `/Users/vadimdulub/Library/Application Support/Artline/backups/`.

Verification was scoped to the selected records and preservation of surrounding catalogue counts; it does not demonstrate 10-million-row performance.
