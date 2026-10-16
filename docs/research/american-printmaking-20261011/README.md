# American printmaking, 1800–1970 — 11 October 2026

The completed batch added **2,369 new production artworks and 2,369 verified
primary images**, covering 578 artists, including 170 newly added artists.
All 2,369 works meet the backend creation-date scope (1800–1970) and have
accepted Yale holding evidence. Records remain in review and are available in
the unified catalogue. This is a selected topic survey, not exhaustive coverage.

The user requested further illustrated catalogue expansion after French
printmaking. Prior deliveries do not count toward this American batch.

## Sources and decisions

The official Yale University Art Gallery collection provides physical-object
records through [LUX](https://lux.collections.yale.edu/), documented by Yale's
[LuxY project](https://github.com/project-lux/luxy). Each selected object must
agree with its linked official IIIF manifest on native identity, accession,
creator, title, literal creation date and museum credit. The ordinary Gallery
web-page access hold remains binding; the documented public API is the source.
HTTP 401, 403 or 429 stops further requests to the affected provider.

Discovery captures at most 4,500 illustrated metadata leads. The selection uses
source-identified American print artists, not an inference from subject matter
or current museum location. Prints, impressions, states, portfolios, publishers,
printers and after/influence roles remain distinct. Unknown or complex dates,
posthumous/restrike uncertainties, loans, contradictory metadata and unresolved
creator identities remain explicit holds. Approximate dates ending in 1970 are
held for date review. No date is invented from an artist lifespan or title.

Production artists are reconciled by authority identifiers, source names and
explicit life dates. Activity ranges are not assumed to be lifespans. New
artworks and artists retain review status; accepted holding evidence establishes
scope eligibility without claiming museum masterpiece endorsement or display.
Existing French selection records are preserved separately.

## Images and verification

Only selected source-eligible objects enter image preparation. Images use the
exact manifest's service and preserve the complete frame and proportions.
Original selected 1,200-pixel renditions and contact sheets are archived under
`~/Library/Application Support/Artline/source-images/american-printmaking-20261011/`.
Application JPEGs are bounded to 100,000 bytes. Per-file technical checks,
existing-image comparisons, actual visual review, create-only uploads and
public-file checksums precede catalogue attachments.

Actual image rights labels, credits and source receipts remain intact; user
approval is recorded separately. Metadata CC0 is not treated as an image licence.
“In Copyright” and territorial “No Copyright - United States” labels are stored
as restricted, not worldwide public-domain assertions.

Research: `ops/american-printmaking-20261011.py`. Reconciliation and delivery:
`ops/american-printmaking-delivery-20261011.py`. Production uses immutable pinned
plans, the shared ingestion lock and atomic batches. Final verification checks
every new record, date, artist, holding, citation, source identity and image,
followed by public access checks. The real local database remains read-only;
there are no fixtures, commits or deployments.

## Selection audit

The pinned plan contains 2,369 artworks across 578 artists, including 170 new
artist identities. Discovery checked 4,500 object records: 2,793 passed source
selection and 1,707 remained held. Creator/native-object staging retained 2,684
candidates and held 109. These are successive selection stages, not additive
production totals.

All 2,691 prepared source images were actually viewed on 94 contact sheets,
including images subsequently held by creator reconciliation. Visual review
held 187 images. The final source, chronology, object and image audit held 145
records; these sets overlap. The audit compared 10,815 existing catalogue
images with no missing local comparison files. Additional cross-sheet holds
preserve uncertain name variants and compact creator-date conflicts. One source
image failed technical preparation. Every unselected source identity remains in
`selection-summary.json` and the underlying object, identity and image ledgers.

The selection excludes unsupported aggregate components, printing blocks,
transfer drawings, title leaves, repeated compositions awaiting impression
review, poor photographs, merged creator authorities, chronology conflicts
and corporate creator roles requiring reconciliation. Activity dates and
education dates never become invented biographies. Existing creator names,
life dates and publication states are preserved. Separate Yale authorities
reconciled to the same artist share one production artist identity.

`delivery-manifest.csv` lists every selected source, accession, artist, literal
date, image and checksum. `delivery-plan-pin.json` pins the plan. A pre-ingestion
revision classified ten explicit copyright statements with unlocatable rights
holders as restricted; prior plans and upload receipts are retained under
`history-delivery-plans/`. Exact source labels remain unchanged. The final plan
has 1,476 restricted and 893 unknown-rights images, with separate user approval.

Eleven offline safeguard tests passed, covering cutoff uncertainty, physical
impressions, corporate roles, printing matrices and contradictory creator dates.
The source/API access holds remain intact. Production completion and public
verification are reported only in the dedicated verification receipts.

## Completed production verification

All 2,369 records, primary images, artist identities, source identifiers, dates,
source citations and accepted holding assertions passed verification. Every
public image matched its prepared checksum; seven anonymous artwork-detail and
artist-browsing samples passed. No current-display claim or publication change
was made. The real local database was not connected to or changed.

Images total 133,722,746 bytes, each at most 100,000 bytes. Cloud SQL backup
1791734142380 succeeded before the operation. Production applied the pinned
plan in 48 atomic batches; initialization added 170 artists and reused 408.

Receipts: [production verification](production-verification.json),
[public verification](public-verification.json),
[delivery manifest](delivery-manifest.csv),
[selection summary](selection-summary.json), and
[implementation checks](implementation-verification.json).
