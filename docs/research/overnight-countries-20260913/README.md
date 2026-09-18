# Artline overnight research — verified production delivery

The queued local/production deliveries completed after renewed Google Cloud sign-in on 14 September 2026. Start with the [updated report](chatgpt-handoff/resumed-20260914/REPORT.md), [ChatGPT research prompt](chatgpt-handoff/resumed-20260914/RESEARCH_PROMPT.md) and [CSV package](chatgpt-handoff/artline-research-resumed-20260914-chatgpt.zip).

| Session result | Local | Production |
|---|---:|---:|
| Gross added catalogue artwork rows | 2,778 | 2,778 |
| Added creator profiles | 628 | 628 |
| Verified selected image assets | 1,564 | 1,564 |
| Active primary image assets | 1,554 | 1,554 |
| Artwork duplicates consolidated | 438 | 438 |
| Painter duplicates consolidated | 60 | 60 |

All 2,767 active added works remain **In review**. All 628 added profiles have cultural-affiliation records; two works linked only through rejected historical attribution intentionally do not inherit the former painter’s country. Catalogue-wide country gaps and unlinked creator labels remain research queues.

Twenty country scopes for each of eleven countries now have completed verification receipts, including Portugal. Additional Greek historical scopes make 240 entries in the country ledger; earlier primary-museum/image follow-ups are documented separately. Portugal added 60 artworks, 18 painter profiles and 29 images. Fourteen candidates remain held for source identity, attribution or usable creator chronology; these are research holds, not pending production uploads. Missing creation dates were retained on 13 imported Portuguese records.

The final comparison covers 3,476 affected artworks, 1,082 painter records, selected image metadata and all 498 duplicate redirects. Both environments matched. An initial ordering-only difference was caused by database collation; the original comparison evidence is retained, and no database correction was needed. All 58 images newly delivered since the earlier handoff passed public HTTP/checksum verification. The Dutch and Portuguese timelines returned 582 and 27 painters respectively.

The updated archive contains 55 files, including 39 CSVs. SHA-256: `d1a3e12558fb68b91b39e2b5d068088c05f245201f11b65c7b0be325456b5258`. It contains metadata, rights/source links and evidence; image binaries and database dumps remain in their dedicated locations. The [earlier archive](chatgpt-handoff/artline-research-20260914-chatgpt.zip) and [pre-resume index](README-pre-resume-20260914.md) remain unchanged historical evidence. Gross inserted rows are not a count of newly discovered physical objects: replacements and later archived duplicate rows are explicitly identified.

Recovery snapshots are under `/Users/vadimdulub/Library/Application Support/Artline/backups/overnight-countries-20260913/`. The current local dump is `local-after-resumed-20260914.dump`; successful post-delivery Cloud SQL backup: `1789364642427`. No restore or test database was created. See [recovery receipts](final-audit/resumed-20260914/recovery-backups.json).

Use `session-application-index-resumed-20260914.json` for current session membership. The `final-audit/resumed-20260914/` receipts and `duplicates/resumed-20260914/local-audit.json` describe final verification. `WORKLOG.md` retains the investigation and delivery history. The guarded production resume now has a completion receipt; fresh research needs its own reviewed plan and evidence phase. No publication, deployment, Terraform apply or commits were performed during this resumed delivery.
