# European catalogue expansion — 9 September 2026

Audience: Artline owner. Decision: which additional museum-connected paintings can
be safely added to the local research database, without publication or image downloads.

Scope: existing painter authorities; European holdings; creation no later than
1970. Preserve uncertain dates, attribution, ownership/custody and image rights.
Reuse the previous two immutable inventories and same-day official response caches.
Do not overwrite editorial fields, conflate holding with display, or label ordinary
holdings as masterpieces. No commits, infrastructure changes or remote writes.

Planning tool unavailable in this environment; this document is the fallback plan.
All four phases are complete.

1. Complete — bounded discovery. Review National Gallery cached candidates
   and official API documentation; independently research exact Orsay/French museum
   records and National Gallery creator-name gaps. Reconcile source/object identity,
   creation dates and collection evidence. Source classes: museum object records,
   documented APIs/IIIF, official collection catalogues and policies.
2. Complete — gap-focused follow-up. Merge evidence; verify consequential matches;
   exclude previous accession/URL identities, unsupported attributions and loans
   without a known holder. Record exclusions and remaining gaps. Stop once this
   batch is supported and further queries have diminishing returns.
3. Complete — implementation and local import. Assemble a new immutable offline
   snapshot; extend the Go allowlisted importer with a new version; test cutoff,
   deduplication, rollback and replay. Back up PostgreSQL; preview then apply the
   reviewed metadata only; verify receipts, database counts and bounded API output.
4. Complete — synthesis and verification. Write the canonical internal research
   source and claim/source ledger; create a concise PDF supplement, render and
   inspect it. Record actual additions and limitations. Preserve earlier artifacts.

Research workers may investigate distinct substantial lanes, as required by the
deep-research skill. They must not spawn workers, edit files, write reports or mutate
the database. The coordinator owns evidence review, implementation and delivery.

Discovery result: 251 National Gallery metadata candidates from 18 fixed queries;
16 prior same-day response caches reused, two corrected-name responses collected.
86 candidates pass initial selection, 165 have explicit deferral/duplicate reasons.
NG224 requires further date review and will not enter this snapshot. Orsay research
is bounded to 30 exact new objects. Existing 600-artwork DB remains unchanged.

Follow-up complete: approved 115 objects (85 National Gallery, 29 Orsay-held,
one Grenoble deposit), 24 existing painter authorities and three institutions.
One new institution is required to avoid assigning Grenoble's Pissarro to Orsay.
Courbet RF325 has indexed primary evidence with disclosed direct-access limits.
Two explicit deposits preserve holder versus responsible institution. API creator
aliases and NG6700's later nonempty Overall measurement were checked independently.
Orsay content has no established open-reuse licence; private review only. No new
current-display or masterpiece-list assertions. Stop: bounded supported supplement
complete; further expansion is a separate evidence batch, not an unbounded crawl.
