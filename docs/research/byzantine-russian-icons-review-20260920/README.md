# Byzantine art and Russian icons — catalogue review

Reviewed 20 September 2026. Read-only catalogue review; no catalogue edits, publication, uploads, image replacement or deletion.

**Subsequent owner-approved delivery:** [3 images uploaded and 19 existing records updated in both catalogues](delivery/README.md). The audit results below describe the pre-update snapshot and remain preserved as evidence.

## Result

Reviewed **119 local candidate records**, including anonymous and workshop-labelled objects, and inspected all **74 existing local images**. Every image file is present, decodes successfully, matches its recorded hash/size/dimensions, and is **at most 100,000 bytes**. Largest: **99,973 bytes**. All 119 counterparts were confirmed in the cloud, with no differences in the compared core artwork fields.

The candidates are not all historical Byzantine art or Russian icons:

| Review group | Records | With image | Without image |
| --- | ---: | ---: | ---: |
| Byzantine, early Christian and post-Byzantine candidates | 71 | 54 | 17 |
| Russian icon candidates | 13 | 5 | 8 |
| Russian manuscript miniatures needing identification | 4 | 4 | 0 |
| Other Orthodox traditions / unresolved source groupings | 8 | 7 | 1 |
| Related modern works and false search matches | 23 | 4 | 19 |
| **Total** | **119** | **74** | **45** |

These are provisional review groupings, not new database classifications. The unresolved group includes early icons that may belong in the Byzantine group after object-level reconciliation. All 119 records retain `review` status.

See [the complete work-by-work review](WORK-BY-WORK.md) for every object, creator label, stored date, image availability and review decision.

## Findings that matter

1. **A component attribution has been lost.** For *Kazan Mother of God Icon with Oklad*, Artline links Semenov as primary creator without the museum's qualifier: he is credited for the **oklad**, the metal cover. This is not sufficient evidence that he painted the icon. The related object 44.817 needs component-level investigation too, but its current museum credit is less specific; that second attribution is not a confirmed error. Both museum pages expose CC0 images, making them candidates for a later, selected image workflow. [Walters 44.819](https://art.thewalters.org/object/44.819/), [Walters 44.817](https://art.thewalters.org/object/44.817/).

2. **Four Rublev entries show manuscript miniatures, not portable panel icons.** Their possible identification with the Khitrovo Gospel remains an inference pending exact folio comparison. RSL gives approximate manuscript dating and qualified participation by several painters; conservation research also distinguishes multiple hands. Do not treat all four as independently authenticated Rublev paintings dated exactly 1400. [RSL manuscript record](https://www.rsl.ru/fondy-i-katalogi/fondy-spetsializirovannyh-otdelov/fond-rukopisey/or-evangelie-hitrovo), [technical research](https://www.gosniir.ru/library/articles/conservation/rublev/evangelie-khitrovo.aspx).

3. **Some early dates need object-level reconciliation.** Artline's *Christ and Abbot Menas* is dated exactly 750; the Louvre currently gives **700–799**, so the issue is unsupported precision, not a wholly incompatible century. For *Blachernitissa*, Artline stores 439, whereas the Kremlin describes its relief icon as late fifteenth–early sixteenth century. First establish that the local reproduction is the same object; do not substitute a new date from a similar title. The anonymous *Nativity* dated 500–600 also remains unverified, not visually authenticated. [Louvre object](https://collections.louvre.fr/en/ark:/53355/cl010048163), [Kremlin collection document, printed p. 26](https://kreml.ru/storage/files/kontseptsiyakomplektovaniya.pdf#page=26).

4. **Six existing image records are not labelled freely licensed:** five `restricted`, one `unknown`. They are Pantokrator; Virgin and Child between Saints Theodore and George; Christ and Abbot Menas; Black Madonna of Częstochowa; Nativity; and Blachernitissa. Preserve the existing provenance and rights labels. The other 68 have recorded open/public-domain labels; this review is not a new legal clearance of every source photograph.

5. **Image gaps are partly deliberate.** The main Byzantine/post-Byzantine group lacks seven Chourri, nine Athens and one Tzanes image. The Russian-icon group lacks six Kremlin and two Walters images. Existing Chourri receipts hold reproduction permission restrictions; a fresh Apsida check confirms that written permission is required. Artwork age alone is not a reason to override that source hold. [Apsida example](https://apsida.cut.ac.cy/items/show/15208).

6. **Classification and metadata are incomplete.** Only 27 candidates have explicit `object_form=icon`; 27 have unknown work type. Seven Chourri source records already describe icons, but that form is not populated. The six anonymous mosaics currently have unknown type, not an incorrect painting type. Preserve frescoes, mosaics, manuscript pages, panels, composite covers and image details as distinct concepts. Orthodox does not automatically mean Russian: the Brancaleon candidate is Ethiopian-context art, and the Maniava icon must retain its own Ukrainian/Ruthenian context. [Walters Brancaleon record](https://art.thewalters.org/object/36.15/).

7. **Some uncertainty is already handled correctly.** Five records have creation scope `review`; the two Met Tzanes heads have genuinely unspecified object dates on their current pages. Do not replace these with artist activity years. The Kremlin Theophanes attribution is correctly qualified, and the two Met wall fragments retain their modern-restoration qualifier. [Head of Christ](https://www.metmuseum.org/art/collection/search/437856), [Head of the Virgin](https://www.metmuseum.org/art/collection/search/437858), [qualified Theophanes attribution](https://collectiononline.kreml.ru/entity/OBJECT/9453).

## Holding, display and import safeguards

67 candidates have an institution and an accepted, source-backed holding assertion. No candidate has a separate display assertion; this review makes no on-view claim. Thirty candidates lack accepted selection evidence. Neither a date before 1971 nor a recognizable title authorizes publication.

The existing general Met research/downloading helpers still impose a **1000–1970** range and named-artist authority requirements (`ops/research-overnight-met-selection.py`, `ops/overnight-image-campaign.py`). Those workflows cannot comprehensively cover early or anonymous Byzantine art. This is an importer limitation, not the current backend creation-scope rule. A future expansion needs an explicitly supported anonymous/workshop path and no artificial lower-year cutoff; it should remain selected, not exhaustive.

## Method, evidence and limits

- Read-only local and cloud PostgreSQL connections; no test database, fixtures or catalogue writes. Discovery used titles, cultural labels, creator metadata and icon-source identifiers, then enriched bounded batches of at most 200 artwork IDs.
- The first pass found 114 local / 116 cloud candidates. Direct lookup showed that its two apparently cloud-only records **already existed locally**. Explicit Cyrillic/Greek case normalization resolved the locale-sensitive discovery issue and broadened the local set to 119. The original root snapshots/parity file are preliminary evidence, **not a missing-record finding**; use the final [Unicode recheck](unicode-recheck/audit-summary.json).
- The expanded broad cloud SELECT hit its 180-second statement timeout. The final cloud check therefore used the 119 local slugs, not another full scan; its indexed lookup plan took 117 ms. This verified the reviewed cohort but cannot rule out further cloud-only candidates. The independent initial cloud search did complete. [Timeout and fallback record](unicode-recheck/cloud-broad-query-timeout.json).
- Discovery is an offline broad scan, not a production browsing query. The expanded local plan took 26.2 seconds; the cloud timeout reinforces that this approach is unsuitable for interactive browsing. Completed `EXPLAIN (ANALYZE, BUFFERS)` plans are preserved in the snapshots. This is not evidence of 10-million-artwork performance; no load test was performed.
- Every discovered row received a stored-evidence review and scope decision. Fresh primary-source checks are explicitly enumerated in [primary-source-review.json](primary-source-review.json); this does **not** claim that every museum URL was freshly reopened or that every attribution is authenticated.
- Visual QA used five contact sheets, plus independent file decoding, hashes, dimensions and byte counts. Source crops/details are not automatically complete-object photographs. This is not conservation examination or full-resolution authentication. See [visual-review.json](visual-review.json) and [contact-sheet index](contact-index.json).
- The search covers discoverable records already in Artline, not every Byzantine artwork worldwide. Completely missing or unlabelled metadata may conceal additional relevant works. Modern copies, architectural studies, depictions of icons and substring false matches were separated, never deleted.

Detailed evidence: [review decisions](reviewed-scope.json), [final local snapshot](unicode-recheck/local-snapshot.json), [final cloud snapshot](unicode-recheck/cloud-snapshot.json), [file checks](image-file-audit.json), [machine findings](unicode-recheck/review-ledger.json).

## Recommended next action

Reconcile the confirmed component-attribution issue and the flagged object identities/dates first. Then select missing images with recorded per-image permission, starting with the two Walters candidates. Keep uncertain records and anonymous/workshop creators in review; do not publish or bulk-download based on this audit alone.
