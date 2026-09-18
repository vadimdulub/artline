# Dutch and German museums — first delivered batch

17 September 2026. This implements the user's authorization to fix museum
geography and upload catalogue data and selected rights-cleared reproductions.
It is a bounded first batch, not a complete national museum import.

## Delivered to local and production

| Change | Result |
|---|---:|
| Existing museum country/city associations repaired | 21 |
| Source-backed physical venue records added | 19 |
| New artwork records, all in review | 43 |
| Existing artworks enriched with primary-source evidence | 12 |
| Selected images uploaded and attached | 17 |

New artworks comprise 23 Mauritshuis works, 16 works from the Pinakotheken, and
four Berlin Gemäldegalerie paintings. The images comprise 13 Pinakothek
reproductions and four Berlin reproductions. No direct Mauritshuis image was
downloaded in this batch because object-level reuse statements conflict with
the museum's more permissive general policy.

Examples include Clara Peeters' *Still Life with Cheeses, Almonds and Pretzels*,
Rachel Ruysch's *Vase with Flowers*, Judith Leyster's *A Young Woman Being
Harassed by a Man*, Altdorfer's *The Battle of Alexander at Issus*, Kandinsky's
*Träumerische Improvisation*, Raphael's *The Tempi Madonna*, Jan van Eyck's
*Die Madonna in der Kirche*, and Berlin's two Vermeer paintings.

No existing artworks, artist biographies, attributions, dates, primary images,
or publication statuses were replaced. No records were deleted. No current
display claims were added and no holdings were accepted by this import. New
works retain review holding assertions and no current-institution pointer.
Consequently they must not be advertised as newly published museum holdings.

Four source dates with abbreviated/uncertain or multiple creation phases retain
their original wording with unknown numeric bounds. The joint Jan Brueghel/
Peter Paul Rubens creator statement remains an object-level label, without a
fabricated artist profile. Three source-name variants were linked to unique
existing artists only after matching both supplied lifespan endpoints.

## Geography and unresolved identities

All 21 previously identified records now have sourced country/city associations.
Nineteen have new review-status physical venues. Berlin's Nationalgalerie
umbrella and the composite Haags Historisch Museum/De Gevangenpoort record have
city geography only: this pass did not invent a single physical venue for either.

The Alte Pinakothek alias remains separate; merging references safely is still
pending. The Kassel Gemäldegalerie Alte Meister was correctly kept separate from
Dresden. Wallraf–Richartz was assigned Cologne/Germany despite the misleading
older `spain-research-...` slug.

The artwork parser distinguishes the Pinakothek **Collection** field from its
**Displayed** field. For example, works belonging to the Neue Pinakothek but
temporarily shown in the Alte Pinakothek were not assigned to the latter as a
holding collection. Display text is preserved as evidence, not asserted as a
fresh current-on-view record.

## Sources and image review

- The [Pinakothek catalogue](https://www.sammlung.pinakothek.de/en) provided
  native object IDs, collection attribution, dates, accession numbers, and
  explicit object-level CC BY-SA 4.0 image links. Thirteen selected eligible
  painting images were downloaded under those declarations.
- The [Berlin collection record for Van Eyck](https://search.smb.museum/object/obj-868435)
  and the three other pinned Berlin records supplied exact inventories and
  per-image Public Domain Mark 1.0 credits. Photographer credits were retained.
- [Mauritshuis collection](https://www.mauritshuis.nl/en/our-collection) metadata
  was captured from individually selected native object pages. The download
  modal on those pages limits non-commercial reuse, while its
  [general Dutch image policy](https://www.mauritshuis.nl/contact/beeldmateriaal-aanvragen)
  is more permissive. This conflict is held for resolution, not treated as open
  image permission.

Sixty-five selected Mauritshuis/Pinakothek object pages and four selected Berlin
object pages were captured, with receipt URLs, timestamps and SHA-256 hashes.
Fourteen candidates were held: four requiring Sammlung Schack institution
setup, three non-paintings, five qualified-attribution works, and two possible
duplicate-title identities. Their evidence was preserved; no duplicate records
were inserted to bypass the uncertainty.

All 17 image derivatives received actual visual inspection through
`contact-sheet.jpg`, with the row/column mapping in its index. They are faithful
full-frame proportional JPEG derivatives, not generated illustrations or
retouched artwork. File sizes are 89,619–99,171 bytes. Rights evidence, source
checksums, licence URLs, and credits are attached to each media record.

## Verification and remaining issues

`verification-summary.json` records the final result and its limits.

- Both database deliveries completed with transaction-time checks, target-
  specific UUIDs, protected preimages, and pinned review manifests.
- Each uploaded cloud object was downloaded again and checksum-verified.
- An independent post-upload local read-only audit confirmed all delivered
  counts, review states, 17 image evidence records, and no new accepted/display
  assertions.
- Every one of the 17 public image URLs returned HTTP 200 with matching JPEG
  bytes and SHA-256 checksums. Public museum-detail responses for Frans Hals,
  Folkwang, and Neue Nationalgalerie returned HTTP 200 with the repaired venues.
- Eight offline Python tests and the Go image-preparation tests passed. No
  disposable database, catalogue test fixture, or large-scale load test was used.

Two limitations remain:

1. The live museum directory request with `country=NL&q=Frans Hals` returns HTTP
   500. API logs confirm `timeout: context deadline exceeded`; individual museum
   details work. The current source contains a global materialized membership
   CTE in the directory query, a performance lead rather than a proven production
   query-plan diagnosis. See `listing-timeout.json`. No application change was
   deployed to address this.
2. After all uploads completed, the OS began denying read/execute access within
   Documents, including the repository and installed `gcloud`. This prevented
   a fresh complete cloud-database re-audit and final workspace checks. Independent
   local database and public HTTP checks still completed from outside Documents.
   Cloud transaction-time checks are not represented as a later full parity
   snapshot. Folder/tool access must be restored before further workspace work.

No commits, publication, Terraform changes, or application deployment were made.
Remaining national coverage includes Dresden Old Masters, Kunstmuseum Den Haag,
Teylers, Lenbachhaus, and the broader regional/modern museum queues from the
preceding gap audit. This report does not claim those gaps are closed.

## Recovery and evidence

Pre-mutation recovery data:

`/Users/vadimdulub/Library/Application Support/Artline/backups/dutch-german-museums-20260917/`

This contains the validated `local-before.dump` and exact geography/artwork/image
preimages. Cloud SQL backup `1789643238621` completed successfully before writes;
its receipt and local archive hash are in `backups.json`.

Selected source originals are under:

`/Users/vadimdulub/Library/Application Support/Artline/source-images/dutch-german-museums-20260917/`

Served derivatives are under `apps/web/public/assets/artworks/imported/`, with
matching keys in the existing private `artline-508319-images` bucket. Public
delivery uses the existing Artline asset route; no bucket permissions changed.

Key evidence: `geography-plan.json`, `geography-review.json`, both geography
receipts, `metadata-v2-plan.json`, `metadata-v2-review.json`, per-record
`metadata-applied/` receipts, `image-selection.json`, `image-visual-review.json`,
`images-prepared/`, `image-uploaded/`, `image-upload-summary.json`, and captures.
Earlier parser/plan versions remain preserved; only the reviewed v2 metadata
plan was applied. The v1 parser's temporary-display mapping and stripped studio
qualifier were corrected before any artwork write.
