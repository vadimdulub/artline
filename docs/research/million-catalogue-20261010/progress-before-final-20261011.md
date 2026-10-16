> Historical progress notes, superseded by README.md and goal-audit-final.json. Pending items and resumption instructions below describe earlier checkpoints.

# One-million-artwork expansion — 10 October 2026

The user explicitly authorized continued production expansion of painters,
artworks and authentic images toward **1,000,000 active artworks**. The goal is
not yet complete. Source records and candidate counts are not production totals.

## Continuation — 11 October 2026

Production authentication is restored. The previously committed sixth Rijks
window passed independent verification, followed by another **20,614 artworks,
1,061 artists and 16,088 creator links** in `04000-04500`. The production
snapshot at 10:54:50 UTC contained **889,078 active artworks and 38,363 active
artists**. Other authorized jobs contribute to these global totals. The
Rijks controller continues subsequent windows, checking each before proceeding.
Its current log is `/tmp/artline-million-rijks-resume-20261011.log`.

The pending **231 Rijksmuseum primary images** are now attached and independently
verified: primary links, media checksums, attachment rows, source evidence,
search projections, public file hashes and four sampled public artwork routes.
Original artwork fields and real local database counts are unchanged.

The user's instruction to add more WikiArt images has delivered **174 new
primary images across 109 artists**. The first selection researched 480 gaps
across 129 artists, excluding the separate active 500-painter campaign. It
prepared 171 images and attached 156 after inspection of every reproduction.
A follow-up added 16 further Kmetty János images. A complete, legible Eric Gill
emblem was accepted at its native 150 × 144 pixels without enlargement. A
further 83 date-research leads yielded one George Romney portrait: the National
Trust's object 1535162 confirms creation before 1789, while WikiArt's 1759 date
conflicts with the sitter's dates. That discrepancy remains explicit evidence;
the catalogue's unknown creation date was preserved. Every delivered image passed
production and public byte-hash checks, with one public artwork route checked
per affected artist in each phase. The source labels include 68 restricted and
106 public-domain designations; user approval is recorded separately, and no
rights label caused exclusion or an additional approval request.

The unresolved selections remain explicit: 390 lack an eligible literal
source date, two Antoniazzo records show the same painting, and 13 Guanxiu images are monochrome rubbings
whose relationship to the original compositions requires version review. No
dates, titles, creator links, holdings or publication states were rewritten.
See verification receipts in `wikiart/images-001/` through `images-004/`.

This continuation has delivered **405 images**; the million-catalogue campaign
has delivered **926 images cumulatively** (922 primary, four alternate).
The earlier Cesi/Top 100 campaign is separate from that subtotal.

Rijks metadata harvesting is complete at **16,943 pages**. The initial feed
reported 16,936 expected pages; the controller preserves all existing pinned
windows and appends the seven-page tail after confirming the final empty token.
Offline selection through page 16,935 contains **407,317 candidates before
reconciliation**, not additions. MoMA's first production plan contains **19,935
potential additions**, with no MoMA writes yet. Further museum metadata is being
prepared because the reconciled Rijks and MoMA totals alone may remain short
of one million. Images continue to be individually selected; no image dump is
downloaded.

The Art Institute of Chicago's official metadata archive supplied 139,747
object records and 17,017 agent records. Operative selection `aic/selection-v2.json.gz`
contains 41,108 eligible candidates; the exploratory first plan estimated
30,194 additions before the latest reconciliation. Qualified authority names,
including imitators and circles, remain object labels rather than invented
people. The nine offline AIC semantic tests pass. No AIC images were downloaded.
`ops/million-next-sources-20261011.py` waits for the verified Rijks windows and
then generates fresh MoMA and AIC phase `002` plans if the target is still unmet.

The expanded lifetime audit found seven new short-range interpretations that
needed individual review. Four artists now have explicit, source-backed
activity timelines: Johann Otmar, J. Erxleben, Francesco de Nanto and Benjamin
Recknagel. Three ambiguous NGA ranges no longer assert birth/death dates;
their timelines explicitly estimate documented works, and their lifespans
remain unresolved. All seven corrections were independently verified; the 14
related artworks and creator links were unchanged. A regression test prevents
new unqualified ranges shorter than 15 years from silently becoming lifespans.
See `lifetime-followup-20261011/activity-review/`.

## Baseline and completed NGA pass

The immutable baseline records **427,414 active artworks**, **152,981 primary
images** and **24,073 active artists**. The initial gap was 572,586 artworks.

The National Gallery of Art pass inserted 44,271 source-backed museum objects
and 3,549 artists in bounded transactions. Subsequent cross-source review
consolidated seven confirmed painting duplicates into older WikiArt records:
**44,264 net active additions**. The seven new duplicate rows remain archived
with audit evidence and redirects; their native identifiers and documented NGA
holdings now connect the original records. The first four retained their original
metadata. The three later reconciliations preserve circle/workshop attribution,
resolve two unknown dates from literal museum evidence and reuse two existing
NGA images. These reused files are not new-image additions. New records remain in review.

The image pass delivered **239 CC0 reproductions**: **235 primary images and
four alternate reproductions**. Every delivered file passed a public byte-hash
check. All 240 prepared images were visually reviewed; one whole-triptych image
was withheld because its target record describes only the left panel. Source
frames are preserved, derivatives are at most 100,000 bytes, and source files
are retained outside Documents.

The complete NGA pass was independently verified against production: all
44,271 objects, citations, native identities, holding assertions and matching
search documents; 40,903 creator links and 3,549 artist citations. Eight public
artwork routes returned HTTP 200. Its chronology audit retained 53 out-of-life
cases for review, predominantly prints that may be posthumous impressions.

## Completed Met pass

The official 484,956-row CSV supplied 109,285 eligible metadata candidates.
Phase `002` inserted **84,726 artworks, 1,641 artists and 34,247 creator links**.
All artwork metadata/state checks, citations, native identifiers, holdings and
search documents passed independent production verification. Four planned
objects remain excluded: three composite records with creator labels longer
than the database field and one erroneous object Wikidata reference that
identifies the artist Johann Balthasar Probst. The source values remain intact
in immutable evidence. A disconnected database transaction was resumed from
committed receipts and independently checked.

The Met image pass added **63 primary images**, all visually reviewed,
CC0-labelled, and verified against public file hashes and production rights
evidence. The source API returned HTTP 403 after 83 selected object responses;
that surface remains held. A second pass used only those cached responses,
recognizing literal multilingual title alternatives in the CSV. No denied API
request was retried or bypassed. Current source dates and creator wording remain
in image evidence; catalogue dates were preserved. The first selection was
240 paintings; unsupported and inaccessible images remain held.

Together the completed NGA and Met passes added **128,990 net active artworks,
5,190 artists and 302 authentic images** (298 primary and four alternate).
The production snapshot at 20:59:51 UTC held **556,942 active artworks** and
29,263 active artists. Other authorized jobs also contribute to global totals.
Real local database counts still match the campaign's read-only baseline.

## Rijksmuseum checkpoint before authentication resumed

The current OAI feed reports 846,756 metadata records. Six bounded source
windows have committed **160,079 artworks, 5,182 artists and 109,334 creator
links**. The first five windows, through `03000-03500`, passed independent
metadata, citation, holding, native-identity and search-document checks.
The sixth (`03500-04000`, 21,395 artworks) committed all 22 transactions but
its independent verification awaits renewed Google Cloud authentication.
Committed receipts are not a substitute for that final verification.

The last independently verified snapshot, at **22:45:18 UTC on 10 October**,
contained **698,457 active artworks and 33,619 active artists**. The conservative
goal count was **697,299**, excluding 1,158 explicit Rijksmuseum verso views
pending physical-sheet review. Existing view records remain preserved in review;
new records with `(V)` or `(VERSO)` inventory suffixes are held. This prevents
front/back views of the same sheet from advancing the million-artwork target.
The later committed batch is additional to this snapshot; no unverified current
global total is asserted.

The first Rijks image pass delivered **219 primary images**, all visually
reviewed and independently checked against production primary-media links,
attachments, rights evidence, search projections and public byte hashes.
Twenty-one of its 240 selections were held. Four sampled public artwork API
routes returned HTTP 200. The next selection has **231 visually accepted,
prepared images awaiting upload**, seven incomplete network downloads and two
source photographs whose clipped subjects need whole-object/detail review.
All six contact sheets for each selection were inspected. No pending image
is included in delivered totals.

Across NGA, Met and the committed Rijks windows, receipts record **289,072 net
active artwork additions, 10,372 artists and 521 delivered images** (517 primary,
four alternate). This artwork subtotal includes the preserved Rijks view records;
they are explicitly subtracted from progress toward distinct physical artworks.
The real local catalogue still matches its read-only baseline.

Google Cloud returned **“Reauthentication failed. cannot prompt during
non-interactive execution”** while starting sixth-window verification. The user
has been asked to renew their existing login with `gcloud auth login`; no new
permission or ingestion approval is needed. Public source research and offline
selection continue. At the recorded checkpoint, eight further source windows
contain **111,183 eligible candidates before production reconciliation**.
They are not yet catalogue additions. Later offline windows continue to be
prepared by `million-rijks-preselect-20261011.py`; a selection lock prevents races
with the production controller. Source windows include the final partial page
window through page 16,935. The goal remains incomplete.

MoMA's official repository was pinned to one commit before capturing its
160,700 artwork and 15,935 artist records. A conservative pass selected **24,993
metadata candidates**: 1,319 paintings, 4,164 drawings, 8,529 prints, 10,314
photographs and 667 sculptures. Only simple standalone inventories with literal
eligible dates are selected. Complex and parent inventories, book/portfolio/view
records, ambiguous dates and unresolved creator alignment are preserved as
holds. The 57 creator-alignment holds retain their object-level labels.
**No MoMA production writes or image downloads have occurred.** Its metadata
CC0 dedication explicitly excludes images. Five additional offline tests pass.
After current-window verification, the generic importer supports `plan moma
--phase 001`, followed by reviewed application and independent verification.

After authentication is restored, resume
`ops/million-rijks-continue-20261010.py --start 0`. It first verifies the committed
unfinished window, then continues bounded selection, reconciliation, ingestion
and verification. Image delivery resumes with
`ops/million-rijks-images-20261010.py deliver --phase 002`. Both workflows retain
transaction preimages, deterministic identities and immutable receipts.

The Met chronology audit retained 1,009 out-of-life cases, including 881 print
links and nine dates preceding an artist's birth. These are factual review
cases, not automatic corrections. Some source biographies attach the wrong
same-name person; some object dates describe prototypes or posthumous editions.
The strengthened prospective importer holds explicit pre-birth conflicts and
original painting/drawing dates wholly after the named creator's death, while
preserving qualified attributions and possible posthumous print/cast dates.

One individually confirmed Met homonym error was corrected: the 1731 *Burial
of Saint Petronilla* now links to **Jakob Frey (1681–1752)** instead of the
nineteenth-century Johann Jakob Frey. The Rijksmuseum's corresponding print
composition and Getty ULAN 500056707 establish the elder's identity. The original
Met biography, QID and creator link remain in the correction citation and backup;
object dates, status, images and holdings were unchanged. See
`lifetime-followup-20261011/`.

Rijks SK-A-203 illustrates why dates must not simply be clamped to an artist's
life: the museum documents Duyster's original painting in the early 1630s and
later anonymous additions around 1645 and 1650. Both source creator labels and
the full creation range remain appropriate. The review is recorded in
`rijks/duyster-multi-stage-creation-review.json`.

The Met CSV repeats the same `Constituent ID` for unrelated artists; for
example, 1206 is shared by Ding Yunpeng, Li Liufang, Yang Wencong and others.
That field is preserved as raw evidence and **never used as a person identity**
in the operative selection. Explicit artist Wikidata references or labelled
derived name/biography evidence keys support reconciliation. Ambiguous list
alignment, contradictory authority fields and unresolved people retain object
labels. Superseded phase `001` was never applied.

## Scope and identity safeguards

Metadata selection precedes images. No placeholder records or generated artwork
images are used. Physical museum objects, not virtual collections or inseparable
views, form catalogue units. Distinct physical print impressions can remain
separate; an identical composition alone does not justify merging them.

Creation dates must come from literal object metadata, never from a creator's
life or museum search bounds. This first bulk selection holds unparsed dates,
post-1970 dates and approximate dates at the cutoff for separate review. Artist
lifetimes come from explicit source biography/birth/death fields. Incomplete
lifetimes remain unknown; an estimated timeline from documented works is labelled
as an estimate rather than presented as a lifespan. Explicit activity periods
are preserved as activity.

Deduplication checks source IDs, Wikidata identifiers, museum inventories,
same-export collisions and unresolved same-title records. The strengthened
cross-source check also searches matching creator/title records without museum
assignments. NGA has 153 such object candidates (163 pair comparisons); four
paintings were initially confirmed and consolidated. Other candidates
require version/impression/copy review and are not automatically merged.
Three additional painting pairs are now consolidated and independently verified:
Tarbell's *Josephine Knitting*, the *Portrait of a Young
Woman in White*, and *Saint Jerome with Saint Paula and Saint Eustochium*.
The latter two explicitly preserve the museum's circle/workshop attribution.
See `nga/identity-followup-002/verification.json`. The three duplicate rows
remain archived with source history and redirects, so they no longer inflate
the active total or require an additional subtraction from the goal count.

Official museum holdings do not establish current display. All new catalogue
records remain in review, which is compatible with the unified active catalogue.
No publication, deployment, commits, local database writes or test fixtures.

## Evidence and recovery

- `baseline.json.gz`, `authorization.json`, and source receipts are immutable.
- NGA operative plan: `nga/plan-v2.json.gz` and its SHA-256 pin. All 45 production
  batch receipts are in `nga/batches/`. Earlier `plan.json.gz` is superseded.
- NGA identity review: `nga/cross-source-candidates.json.gz`, captured WikiArt
  pages, the four-painting reconciliation plan and receipt.
- NGA image review/delivery: `nga/images-001/`, with per-file preparation,
  visual decisions, upload receipts and attachment receipts.
- Met operative input: `met/selection-v2.json.gz`; operative plan and receipts:
  `met/002/`. Earlier input/phase `001` are retained solely as review history.
- Met execution exclusions: `met/002/execution-exclusions-v2.json` supersedes
  the original three-record exclusion list; both hashes are retained by batch.
- Met image evidence: `met/images-001/`, cached-response follow-up
  `met/images-002/`, and `met/images-verification.json`.
- Rijks operative selections use the `-v3` suffix, preserving approximate
  birth labels such as `ca. 1599`. Earlier selections were never applied.
- Rijks per-window plans, batch receipts and independent verifications are in
  `rijks/NNNNN-NNNNN/`; image evidence is in `rijks/images-001/` and `images-002/`.
- `production-auth-hold-20261011.json` records the authentication dependency and
  exact resumption checkpoint. Ten offline source-boundary tests pass, including
  the rule excluding verso views from new physical-object imports.
- Cloud SQL recovery backup: **1791660971061**, verified successful before writes.
- Scoped transaction preimages and source originals are under
  `~/Library/Application Support/Artline/backups/million-catalogue-20261010/`
  and the corresponding `source-metadata` / `source-images` directories.

Production transactions use the shared catalogue-ingestion advisory lock,
precondition checks, deterministic identifiers and committed batch receipts.
Contention retries roll back first and resume from the committed checkpoint.
Database triggers maintain search rows, directory totals, audit entries and
cache invalidation. Production query plans are captured; these are not a
ten-million-row load test.

## Primary sources

- [NGA open data and documentation](https://github.com/NationalGalleryOfArt/opendata)
- [NGA Open Access image policy](https://www.nga.gov/terms-and-notices)
- [Met official bulk data](https://github.com/metmuseum/openaccess)
- [Rijksmuseum OAI documentation](https://data.rijksmuseum.nl/docs/oai-pmh/)

The NGA image policy was observed through the web tool. A later direct request
returned HTTP 403; that surface remains on hold. The separate documented NGA
image API served selected open-access images successfully. No denied surface
was retried or bypassed.
