# Deep European collection expansion

Authorized continuation, 9 September 2026. Audience: Artline owner; output: a
larger source-backed local review catalogue plus a linked research/import report.
User asks for the deepest practical review of European museum websites, not a
claim of literal completeness. Prior baseline: 445 artworks, 36 institutions,
211 media assets, 1,001 active painters. Preserve the previous 59-record snapshot.

Assumptions: broaden beyond Monet/Pissarro/Bosch/El Greco to the existing iconic
painter cohort; paintings created by 1970, selected highlights or museum-linked
holdings. No sculpture, drawings, temporary-loan-only ownership claims, speculative
creator matching, publication, image bulk download, account registration, external
messages, commits or deployment. Museum catalogue metadata and permission-cleared
data routes first. Keep factual fields, not wholesale copyrighted museum essays.

The update_plan tool is not available (tool metadata checked); this file is the
working plan. Exactly one step stays in progress until verification is complete.

1. COMPLETE — discovery and coverage audit. Reuse current inventory; examine
   official European collection/catalogue and API routes. Two independent regional
   research lanes (Iberia/Italy and Benelux/Germanic/Nordic); coordinator owns
   France/UK/Ireland, integration preflight and evidence reconciliation.
2. COMPLETE — focused follow-up. Resolve official object identity, creator qualifiers,
   dates, institutions versus branches, ownership/deposit distinctions, dimensions,
   material, image policy and data access. Quarantine unsupported records.
3. COMPLETE — backend/import implementation. Versioned, bounded, hash-pinned batches,
   stable identity dedupe, source snapshots, audited non-overwriting enrichment;
   no changes to public visibility. Reuse the tested import engine where safe.
4. COMPLETE — synthesis and verification. Private database backup, isolated tests,
   dry-run, transactional apply, no-op replay, API/count checks, structured source
   inventory and a professionally formatted research/import artifact.

Source classes: official individual museum records; documented museum APIs and
open datasets; official national catalogues; first-party collection/rights pages.
Search snippets may support explicitly marked indexed-only metadata; they are not
equivalent to successful direct retrieval. No access-control or rate-limit bypass.

## Gap matrix

| Claim family | Evidence needed | Confidence / conflicts | Next action |
| --- | --- | --- | --- |
| Broader museum coverage | Official institutional identity and exact works | Prior 26 European museums, not exhaustive | Regional discovery, registry comparison |
| More than four painters | Existing authority identities + official creator | Names alone can collide | Resolve exact source artist against local cohort |
| Rich artwork details | Source title/date/material/dimensions/accession | Many prior fields missing | Prefer factual structured metadata |
| Object vs version/panel | Accession and canonical object IDs | Repeat titles are not duplicates | Reconcile before database writes |
| Workshop/disputed authorship | Explicit qualifier and source | Do not flatten to primary | Preserve role plus note |
| Institution vs current display | Holding/deposit evidence; fresh display separately | Time-sensitive / sometimes conflicting | Import holdings, defer live-display claims |
| Image reusability | Exact asset licence + source policy | Metadata access is not image permission | Record leads; no automatic downloads |
| Existing edits and scale | Snapshot checks + indexed identity matching | 10m-row headroom remains unproven | Isolated rollback/replay/plan tests |

Stop after substantial primary-backed geographic and painter expansion when
remaining targeted searches produce weaker, inaccessible or duplicate evidence;
record uncovered sources and routes instead of claiming all Europe is complete.

Discovery results: 52 selected National Gallery API records from a fixed 18-artist,
227-candidate metadata-only query; 175 exclusion/cap decisions saved. Four source
name/attribution patterns yielded no automatic selection and remain explicit gaps.
Regional evidence: 45 Iberian/Italian exact objects plus a separate Naples holding
lead; Northern/Central lane delivering about 40. Louvre's official masterpiece
album and JSON records support a designation-backed French expansion. Ireland's
official highlights identify seven paintings, including a Jesuit-owned long loan.

Reconciliation result: 157 records / 28 collections / 41 artists / 14 countries.
155 new works, two exact-accession enrichments, 19 new collections, 338 citations
and 17 museum-authored highlight selections applied locally. Total 600 artworks,
55 institutions, unchanged 1,001 active painters and 211 media. Zero publication
or current-display claims. All Go tests/vet and isolated 100k identity-plan check
pass. Dry-run and both v2/v1 replay fingerprints unchanged. Source-linked 31-page
PDF generated (244 links), all pages rendered and visually inspected; no clipped
text, broken glyphs or layout defects found. Full source inventory and import
verification/receipts retained. No required work remains in this bounded batch;
geographic, API, image-permission and production-scale gaps are documented.
