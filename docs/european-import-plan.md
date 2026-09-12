# European museum research import

User authorization: research and add the previously assembled European collection
data to local PostgreSQL. Scope is the 59-candidate, four-painter inventory, not an
unbounded world import. No publication, image download, commit or Terraform action.

Completed: preflight source evidence, schema and existing identities. Reused the
prior research, verified three qualified attributions, kept Stockholm's signed date
as unknown creation date, found Modena inventory RCGE 8095, and sourced Pissarro's
Impressionist / active-in-France classifications. One existing Prado object matches.

Completed: bounded, transactional Go importer with dry-run, source hashes, audit
records and replay protection. All five focused tests pass, including isolated
100k-row exact-identity plans. Existing edits are preserved; conflicting identities
roll back the entire batch. No automatic museum-highlight designation.

Completed: private backup and local identity-index migration; dry-run rollback
verified; applied 58 new works, 25 institutions and 87 citations; replay made no
data/audit changes. All four live painter APIs and museum multi-select/unknown-date
filters checked. Publication remained closed. See european-import-verification.md.

Plan complete; no steps in progress. Broader discovery and images are separate
follow-ups, not silently enabled by this bounded metadata import.

Source classes: the prior inventory's official collection pages, national catalogues
and documented museum metadata. Preserve indexed-only access and publication-date
unknowns. Holdings do not imply legal ownership or current display; noncommercial
or unknown image rights remain link-only. No museum API calls during normal browsing.

## Gaps to resolve

| Gap | Evidence / confidence | Next check / decision |
| --- | --- | --- |
| Existing identities | Local four painter authority IDs known; baseline 387 works / 11 institutions | Match official URLs, institution+accession and qualified creator; no title-only auto-merge |
| Qualified authorship | Three candidates explicitly disputed/possible/attributed | Verify source wording; use attributed_to with explanatory citation, not primary |
| Incomplete date precision | Century, decade and signed-date qualifiers | Preserve literal dates and conservative intervals; no invented exact creation dates |
| Pissarro filters | Missing movement and country in local data | Official artist biography for Impressionism and active-in-France relationship |
| Custody/owner distinctions | Existing assertions support holding/loan context | Retain legal owner in sourced notes; never substitute it for custodian |
| Metadata versus image rights | Prior report separates permissions | Import metadata/citations only; preserve per-institution image deferrals |

The existing research PDF/inventory remains the reference artifact. This execution
produces the database update and machine-readable import report rather than a new
research presentation.
