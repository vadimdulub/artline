# Russian icon production delivery — 21 September 2026

**All 217 reviewed images and their artwork records are now in production.**
The user explicitly requested “ok, upload them to production” after the local
delivery. Scope is the 217 visually approved images, not the 771 remaining source
matches or the unreviewed/duplicate image candidates.

| Museum source | Images and artwork records |
| --- | ---: |
| State Russian Museum | 100 |
| Andrei Rublev Museum | 77 |
| Icon Museum and Study Center | 40 |
| **Total** | **217** |

The upload contains 17,359,564 bytes of application images; the largest is
99,998 bytes. All GCS objects were created with a generation-zero precondition
and verified against their local byte size and MD5. The live application then
served all 217 files with their expected SHA-256 checksums.

## Records and provenance

Read-only production checks found no conflicts by artwork UUID, slug, native
museum identifier, image storage path or museum accession. Accession comparison
preserved internal punctuation; it did not collapse distinct Russian Museum
inventory numbers. The source export came from read-only queries against the
real local catalogue.

The database import committed in one transaction at **2026-09-21 18:34:44 UTC**:

- 217 artworks, 217 media records and 217 media-rights evidence records.
- 217 native source identifiers and 435 provenance/image citations, including
  the alternate source card for the double-sided icon.
- 217 existing, source-supported holding assertions. No display assertions.
- 217 memberships appended to the existing personal owner collection, retaining
  its distinction from museum-designated highlights.
- Three attribution links to the existing Andrei Rublev artist record. All other
  object-level creator labels remain as supplied; no artist biography was created.
- Two missing museum records, both in review: Andrei Rublev Museum and the Icon
  Museum and Study Center. Unknown geography remains unknown.
- Six provenance sources. The existing Russian Museum and artist records were
  reused unchanged.

All artworks retain `status=review`, `research_candidate=true` and null
`published_at`. Source dates, ranges, cultural context, object form, attribution
qualifiers, accession numbers and view labels match the local records. All images
remain `restricted` with actual museum copyright labels and source links;
`verified_at` and `verified_by` remain null. The production upload does not change
the rights policy or assert copyright-holder permission.

No local catalogue data changed during promotion. No application deployment,
Terraform change, commit, publication, deletion or unrelated import was performed.

## Verification

- [Database verification](database-verification.json): every imported artwork,
  media record, creator association, identifier, citation, holding assertion,
  collection membership and rights-evidence row matches the pinned local export,
  apart from the necessary appended collection positions.
- [Public verification](public-verification.json): **217/217 artwork detail
  responses and 217/217 image responses passed** on the production application.
  Checks include exact dates, creator context, view label, source links, rights
  labels, review status and full image checksums. No current-display claim appears.
- [Museum-page verification](museum-page-verification.json): both new museum pages
  return HTTP 200; their bounded artwork pages report 77 and 40 illustrated records.
- [Preflight](preflight.json): exact dependency mappings and conflict checks. The
  scoped 217-ID production lookup took 0.687 ms in this run; this is a real-catalogue
  check, not a 10-million-row benchmark.
- [Commit receipt](applied.json): inserted row counts and recovery checksum.

Production collection pages:
[Andrei Rublev Museum](https://artline-web-lpuqqlugnq-ew.a.run.app/museums/andrei-rublev-museum),
[Icon Museum and Study Center](https://artline-web-lpuqqlugnq-ew.a.run.app/museums/icon-museum-and-study-center).

## Recovery and assets

Exact source export, production preflight, the locked owner-collection preimage,
new-record/dependency IDs and the verified production after-snapshot are under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/russian-icon-images-20260921/production/`

This is a scoped recovery archive, not a full database dump. The database's normal
audit triggers also recorded the inserts and owner-collection revision update.
Any future recovery must account for subsequent edits; no blind rollback was run.

Application objects are in bucket `artline-508319-images` under
`assets/artworks/imported/russian-icon-images-20260921/`. Per-object generations,
checksums and upload receipts are retained in `uploads/`. Full-size originals
remain in the separate local source-image archive documented in the parent report.
