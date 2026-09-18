# Expanded artwork research — rounds 11–15

Completed five more consecutive research rounds. Every round was backed up, applied to local and production, verified row by row, and checked through the live API before starting the next round.

| Round | Artwork links | New painters | Metadata enrichments | Remaining unlinked |
| --- | ---: | ---: | ---: | ---: |
| 11 | 312 | 17 | 312 | 77,187 |
| 12 | 176 | 15 | 176 | 77,011 |
| 13 | 122 | 20 | 122 | 76,889 |
| 14 | 21 | 21 | 21 | 76,868 |
| 15 | 53 | 0 | 53 | 76,815 |

Totals: **684 distinct artworks linked**, **73 new named painters**, and **684 artworks enriched**. Local and production verification hashes agree for every selected row; no artwork is counted in two rounds.

Rounds 11–13 searched 240 previously unsearched Rijksmuseum creator names in three bounded groups. Official object and creator metadata was captured with stable identifiers, source URLs, checksums and retrieval timestamps. Qualified attributions and unresolved object/creator conflicts were held. [Official search API documentation](https://data.rijksmuseum.nl/docs/search).

Round 14 re-examined all preceding source captures to establish eligible named museum creator identities using documented artwork activity where lifespan details were incomplete. Round 15 reconciled further works against the resulting artist catalogue. Unknown birth/death boundaries remain unknown; documented activity is explicitly distinguished from lifespan. Missing artwork dates remain in review.

**76,815 retained artworks still have unresolved creator links.** Original CSV evidence and object-level named creator labels are preserved. Anonymous/unknown creators and qualified attributions remain excluded from this CSV workflow. No artwork rows were created, deleted or published in these five rounds. Museum evidence was not converted into a claim of current display. No images were downloaded.

The object-identity audit now indexes identifiers by museum domain and preserves query-string object identifiers when comparing canonical URLs. This avoids treating two Smithsonian object URLs with different `id` values as one object. Five offline regression tests passed; replaying historical rounds 7, 10 and 11 preserved all earlier recorded conflicts. This change makes no database writes itself.

Per-round README files, source evidence, backup receipts, application logs, local/production verification and live API receipts are preserved in the sibling round directories. Private source archives and completion evidence are stored under `gs://artline-508319-images/research/expanded-roundN-20260913/`. Backups remain under `/Users/vadimdulub/Library/Application Support/Artline/backups/`.

Rounds 11–13 used fresh managed Cloud SQL backups. After the managed-backup frequency limit was reached, rounds 14–15 retained the successful full backup from round 13 and added fresh, complete preimages of every planned artwork and related identity, attribution, citation, audit and ledger records. The scoped backups complement that full backup; they are not full database dumps. Each round also has a fresh local full dump.

Verification was scoped to the selected records and preservation of catalogue counts; it does not demonstrate 10-million-row performance.
