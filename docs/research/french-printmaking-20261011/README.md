# French printmaking — 11 October 2026

After the completed 2,500-work Soviet Realism delivery, the user requested:
“ok, find another random topic and cover ir in the same way, then add more”.
The assistant selected French printmaking, beginning with nineteenth-century
prints and adding a further selection through 1970. This is an editorial topic,
not an invented art movement or a reassignment of existing artists' movements.
The original instruction and interpretation are in `authorization.json`.

## Delivery status

Completed and verified in production: **3,002 new artworks and 3,002 primary
images**, across **248 artists**, including **31 new artist records**. Of these,
**3,000 meet the backend's creation-date criteria**. Two additional works dated
“ca. 1970” remain explicitly flagged for date review and do not count toward
that eligible minimum. All 3,002 artworks retain catalogue review status and
are available through the unified catalogue.

The delivery extends the preceding 2,500-work topic batch by 500 eligible
artworks. All additions have documented Yale holdings, source citations and
authentic object-specific images. Production verification covers every record;
public SHA-256 checks cover every image. Nine anonymous artwork-detail and
artist-browsing samples passed. There are no image gaps among the delivered
records. Existing works and unresolved candidates never count as new artworks.

The final totals are recorded in [completion-verification.json](completion-verification.json).
The complete [3,002-row manifest](delivery-manifest-combined.csv) includes
source URLs, image checksums, exact source rights labels, both immutable plan
checksums and each record's creation-scope result. The original 3,000-record
verification and two-record supplement remain separately preserved.

## Sources and selection

Later the same day, the user requested further expansion. The separately
verified [continuation](../printmaking-continuation-20261011/README.md) delivered
all 188 previously reviewed reserve works and images, bringing this French
selection to 3,190 records. This report's original 3,002-work counts and immutable
verification files remain historical evidence for the first delivery.

The official Yale University Art Gallery collection supplies physical-object
records through its public [LUX service](https://lux.collections.yale.edu/),
documented by Yale's [LuxY project](https://github.com/project-lux/luxy).
Each selected object is checked against its linked official IIIF manifest for
the same native object ID, accession, title, creator, date and institutional
credit. The ordinary Gallery collection page's previously recorded human-check
hold is respected. Only the documented public collection service and the image
services explicitly linked by its records are used.

The bounded nineteenth-century search returned 5,757 illustrated print leads;
the follow-on 1901–1970 search returned 728. Search counts and machine date
bounds are discovery evidence, not eligibility decisions. The actual manifest's
literal creation statement decides whether an object enters this selection.
Primary and extension index captures preserve the exact queries and returned
object identities.

This survey includes lithographs, etchings, engravings and related prints by
source-identified French printmakers. It is a selection from Yale's collection,
not exhaustive coverage of French printmaking. Each accessioned sheet is one
record, even when it contains several vignettes. Printmakers, printers,
publishers, artists copied or referenced, individual impressions and print
states remain distinct. A holding record never establishes current display.

## Date and identity review

- Unknown `n.d.` dates remain held. No year is derived from a creator's life,
  the age of a sitter or an event mentioned in a title.
- Explicit early/mid/late nineteenth-century dates retain their literal wording
  and use the conservative whole-century envelope 1801–1900. Qualified decades
  likewise use the whole stated decade. No narrow boundary such as an invented
  “mid-century” year is supplied. Ranges crossing 1970 remain held.
- The final backend check classified Yale objects 99054, *Abstraction*, and
  13970, *Chateau Anonyme*, as date-review records because both source dates
  are “ca. 1970”. Those dates and records are retained without substitution.
  Two already reviewed reserve prints dated 1854 (81762 and 82020) were then
  added, bringing the fully eligible count to 3,000. Future source selection
  explicitly holds approximate dates ending in 1970. See
  `boundary-date-review.json` and the immutable `scope-topup/` evidence.
- The source's unqualified primary artist role must agree with the manifest.
  Separate printer, publisher and after/influence roles stay in the evidence
  and creator note. Names, source authority IDs, aliases and explicit life dates
  are reconciled against production artist records.
- Fifteen initially held creator matches were individually reconciled using
  shared authority identifiers, documented name variants and source-profile
  evidence. Lifespan conflicts remain explicit; existing artist biographies
  are not rewritten. See `artist-editorial-review.json`,
  `artist-editorial-review-followup.json`,
  `artist-editorial-review-followup-2.json` and their history folders.
- Activity ranges are not assumed to be lifespans. Three new-creator decisions
  had unsupported birth/death fields removed; original source labels remain in
  `creator-date-semantics-review.json`. Five works by three unresolved creator
  identities remain held after the final catalogue-name comparison. The source's
  Pierre-Yyves Trémois spelling is retained as evidence while the new artist's
  canonical name uses Pierre-Yves Trémois, verified from the same authority-linked
  source profile. See `cross-sheet-review/final-creator-collisions.json` and
  `creator-canonical-spelling-review.json`.
- An explicit modern restrike is held because its physical printing date is
  unresolved, even when the source supplies an eligible original design year.
  A 143 × 192-pixel source image is also held rather than enlarged artificially;
  see `image-quality-followup.json`. A cancelled Degas plate impression remains
  held pending its physical printing date. A wooden-wheel photograph incorrectly
  linked to a Gavarni record and an almost black pond reproduction are held after
  visual inspection; no image is fabricated or borrowed from another object.
- Existing Yale native identities and accessions are excluded from the new-work
  selection. Repeat accessions, image matches and ambiguous physical objects
  receive explicit holds. Different margins or colouring do not by themselves
  earn another delivered artwork.
- All delivered records remain in review and enter a personal editorial
  selection. They are not labelled as museum-designated masterpieces. Artist
  movements and existing catalogue metadata remain unchanged.

`objects/`, `identity-rows/`, `artist-decisions/`, `visual-sheets/` and
`visual-decisions/` preserve decisions, with immutable earlier parser outcomes
retained in history folders. The final image audit checks exact and perceptual
matches within the selection and against available existing creator images.

## Selection reconciliation

The immutable `selection-reconciliation.json` records the original selection
funnel. `completion-verification.json` adds the two-work supplement:

| Stage | Count |
| --- | ---: |
| Distinct discovery leads | 6,485 |
| Held at source/date/attribution review | 2,759 |
| Passed initial source review | 3,726 |
| Held at initial catalogue identity review | 38 |
| Image preparation gap | 1 |
| Prepared and visually reviewed images | 3,687 |
| Combined visual, duplicate and final identity holds | 497 |
| Original delivered artworks with images | 3,000 |
| Additional eligible reserve works delivered | 2 |
| Total new artworks with images | 3,002 |
| Fully eligible artworks | 3,000 |
| Additional creation-date review records | 2 |
| Prepared reserve remaining, not delivered | 188 |

The 497 combined holds include the 488 visual-review holds; those categories
must not be added together. All 142 contact sheets were reviewed. The image
audit compared 20,570 existing artist images, with no unavailable local files
in that comparison set. Held objects, alternate impressions and the reserve
do not count toward the delivered total.

The delivery comprises 2,537 works dated through 1900 and 465 later works,
including the two circa-1970 review records. It retains 2,219 exact dates,
354 approximate dates, 135 ranges,
264 century dates, 23 approximate ranges and seven decade dates. There are
248 artists, comprising 217 existing identities and 31 new identities.

Remaining research includes uncertain dates or printing dates, qualified or
multiple creators, conflicting object/creator metadata, loans and ambiguous
collection contexts. One source object remained unavailable after bounded
HTTP 500 retries. These gaps remain in the evidence ledger; no substitute
object or invented information was used to meet the target.

## Image evidence and safeguards

Images come from the exact museum manifest's image service. Selected source
renditions use the complete frame, bounded to 1,200 pixels, and are archived
separately from application derivatives. They are not the museum's master TIFFs.
Application JPEGs preserve proportions without cropping and are at most
100,000 bytes. Every delivered image receives actual visual review, create-only
storage upload and a public-file SHA-256 check.

The manifest's metadata CC0 statement is not treated as an image licence.
Image-specific labels, including territorial “No Copyright - United States”
statements, stay intact; territorial labels are stored as restricted rather
than a worldwide public-domain assertion. The user's instruction to continue
the same selected-image workflow is recorded separately. No rights label is
rewritten as an independently acquired permission. HTTP 401, 403 and 429 stop
further requests to the affected provider endpoint.

The delivered images retain 2,738 “No Copyright - United States” labels,
170 “In Copyright” labels and 94 “Not Assigned” labels. The last two groups
retain their exact labels with an unknown catalogue rights status; user approval
is separate from those source assertions.

Cloud SQL backup **1791719860784** completed successfully before catalogue
changes. Preimages and final verification snapshots belong under
`/Users/vadimdulub/Library/Application Support/Artline/backups/french-printmaking-20261011/`.
Selected source image files and contact sheets belong under the corresponding
`source-images/french-printmaking-20261011/` directory. No local database
connections, fixtures, test database, commit or deployment are used.

## Reproducible checks

Research: `ops/french-printmaking-20261011.py`.
Preparation and delivery: `ops/french-printmaking-delivery-20261011.py`.
Date-boundary supplement: `ops/french-printmaking-scope-topup-20261011.py`.
Seven offline date-scope tests in `ops/test_french_printmaking_20261011.py` pass,
covering literal dates, ranges, source qualifiers, event/lifespan confusion and
the 1970 boundary, including exact versus approximate 1970 dates. They create
no database fixtures.

Production writes use an immutable, checksum-pinned plan, the shared ingestion
lock, bounded identity checks and atomic 50-record batches. Read-only final
verification checks every manifest ID, creator, holding, source identifier and
citation, date, image hash/size and actual rights label. Public verification
checks anonymous artwork access, artist browsing and the uploaded image
receipts. The final reconciliation verifies all 3,002 collection members and
the 3,000 eligible / two date-review split. This catalogue
delivery is not evidence of ten-million-row load performance.
