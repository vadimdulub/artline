# Japan artwork publication — 25 September 2026

Published the exact 36 artworks from the [24 September expansion](../japan-expansion-20260924/README.md) in the live and local catalogues after the user's explicit instruction. All 36 have source-backed creation dates before 1971, an accepted museum holding, museum citations and CC0 image evidence. The batch contains 29 paintings and seven prints. No current-display claims were added.

- Production received 36 artworks, 36 media records and their evidence, 23 new creator profiles, and 30 Japanese affiliation links (23 new profiles plus seven existing profiles).
- Artworks now have `status=published`, `research_candidate=false` and a publication timestamp. Source dates, titles, creator identities and attribution remain intact.
- New creator profiles retain their research state; existing profile fields were preserved. Full artist-profile publication has a separate biography/evidence gate. Public research browsing remains enabled, so the profiles and their works are visible.
- All 36 selected JPEGs were uploaded to the production image bucket with create-only generation preconditions. Existing objects would only be accepted after hash/length verification.
- Read-only verification matched all 36 local and production artwork states. All 36 public artwork API responses and all 36 served image checksums passed.

## Recovery and provenance

Local validated PostgreSQL backup: `/Users/vadimdulub/Library/Application Support/Artline/backups/japan-publication-20260925/local-before-publication.dump` (641,238,814 bytes), SHA-256 `c2b086fbdc74b1cfa19bba053cbebfe2f06514f0d32412c18a5fad435eacdc86`.

Cloud SQL backup `1790320988908` for `artline-postgres` completed successfully before publication. The pinned export, exact preimages and operation receipts are retained beside the local backup. No unrelated database or asset was removed.

The operation is reproducible from `ops/publish-japan-20260925.py`. `plan.json`, `plan-pin.json`, `backups.json`, `storage.json`, `production-applied.json`, `local-applied.json` and `verification.json` retain the operation evidence locally.

## Browsing labels

Removed research/review notices from the header, museum browsing, book details, structured evidence and selection confirmations. Unknown locations and rights remain plainly marked as not recorded. The public catalogue no longer shows or filters by editorial status; editor-only status controls remain available. Artwork visibility rules and stored research statuses were not changed by these presentation edits.

These UI changes are local and have not been deployed. No application deployment or commit was performed. TypeScript and scoped ESLint checks passed; 21 existing component/configuration tests passed. Browser smoke checks confirmed records and images remain visible without review notices on the affected local screens.

## More Edo research

The [Japanese museum scan](../edo-japanese-museums-20260925/README.md) captured 35 selected official pages, producing 17 dated Edo artwork candidates, nine book/edition records and ten historical-event leads. Those finds are research candidates, not part of this published batch.
