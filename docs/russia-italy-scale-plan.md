# Russia, Italy and bulk catalogue expansion — 9 September 2026

Audience: Artline's owner. Decision: which verified catalogue records can be added locally now, and what prevents 50,000–100,000 eligible artworks.

Scope: Russian and Italian museum catalogues in depth, with other official bulk collections as a scaling lane. Artworks created by 1970 with a documented museum connection; sourced descriptions and selected rights-cleared images. New creators are permitted when a stable source authority supports identity. Unknown or conflicting dates remain separate review records. Museum holding is not current display. No commits, publication, deployment or Terraform changes.

Success measures: actual normalized artwork additions, stable identities, source and rights provenance, safe replay, accurate exclusions, selected local images, and verified application queries. Staged objects, museum-directory rows and source collection totals never count toward the artwork target.

Planning tool is unavailable in this environment; this file is the working-plan fallback.

1. Complete — discovery and audit. Inspected schema and importer; Russian and Italian source lanes researched; confirmed NGA full metadata and official Russian catalogue counts; live Italian endpoints and large new downloads have access failures.
2. Complete — follow-up and implementation. Final NGA selection is 33,493 physical painting/drawing/print records in 34 immutable chunks. Added stable creator authorities and conservative life/activity handling. Recovered the Pushkin highlights JSON; reviewed nine Brera records. Source dates and rights failures are explicitly deferred.
3. Complete — local import and verification. Pre-import backup verified. Applied 31,983 new NGA works, 49 Pushkin paintings and nine Brera paintings; attached 19 selected NGA images. Database has 34,264 artworks. Full replays unchanged, cutoff/description/visibility checks pass, API pagination and both 100k scoped-query checks pass. Fixed unnecessary museum-profile enrichment; NGA works-page sample improved from 2.7 s to 0.45 s. Descriptions now exposed on demand in details. The 50k target remains unmet.
4. Complete — synthesis and delivery verification for this pass. Claim ledger and gap matrix reconciled. Four-page PDF generated, source links checked, and every page visually inspected. Both description browser tests, 22 frontend unit tests, TypeScript, lint, full Go tests and vet pass. Deliver actual results with the remaining 15,736-work gap to 50,000. No scheduled ingestion remains running.

Overall target: still open. Reliable national-scale Russian/Italian catalogue imports, further image coverage and the 50,000–100,000 total are not claimed complete. Next source-specific steps and access/rights gaps are recorded in the report and research log.

Primary source classes: national cultural ministries and museum registers, official collection APIs and exports, museum-managed open-data repositories, object records and first-party reuse terms. Secondary indexes are discovery aids, not substitutes for authoritative object provenance.
