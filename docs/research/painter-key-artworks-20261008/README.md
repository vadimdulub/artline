# Painter opening artworks — 8 October 2026

The user requested a key artwork for each painter, shown when opening the painter,
and explicitly identified the test target as the real local `artline` catalogue on
this Mac. This operation therefore updated **local and production** catalogue data.
No disposable databases or catalogue/member test fixtures were created.

The feature is deployed at https://artlines.org. Painter drawers open on the saved
choice; full painter pages show it above the chronology. Explicit artwork links,
filters, pagination, and previous/next navigation retain their own selections.
Choices do not change artwork metadata, representative-work ordering, or
publication status. The server suppresses an archived, ineligible, or non-public
choice when the request cannot see it.

## Final coverage

| Catalogue | Active painters | Saved eligible choices | Choices with images | Still without a saved choice |
| --- | ---: | ---: | ---: | ---: |
| Local | 23,409 | 17,313 | 10,191 | 6,096 |
| Production | 23,450 | 17,353 | 10,216 | 6,097 |

This is **not complete image coverage**. A further 7,122 local selections and
7,137 production selections have metadata but no attached picture. Unsupported
dates, identities, and missing works were retained for research; no artwork or
creation date was fabricated to fill a slot. Both databases have a saved choice
where this pass found a supported eligible artwork. Production gained additional
painter records during the work, so its current totals differ from local.

The complete remaining queues are `local-final-unresolved-v4.json.gz`,
`production-final-unresolved-v4.json.gz`, and the corresponding
`*-selected-without-images-v4.json.gz` files. The final aggregate checks are in
`*-final-verification-v4.json`.

## Selection and research

Selections are stored in `artist_key_artworks`, independently from catalogue and
publication fields, with exact artwork/creator attribution, source URLs, selection
basis, evidence, batch identifier, timestamp, and database audit history. The
composite foreign key preserves the existing creator/object relationship.

The selection pass considered visibility, available imagery, secure attribution,
explicit notable-work evidence, museum highlights, existing representative orders,
and an editorial representative fallback. The fallback is labelled as an
**editorial representative**, not a museum designation or a claim that the work
is the painter's most important. Holdings are not treated as current display.

Wikidata queries checked all 17,167 available painter authorities for P800 notable
works with a matching P170 creator, finding 6,172 relationships. Matches used
existing artwork authorities. Mona Lisa also received an exact WikiArt
creator/object source review. Most remaining choices use existing source-backed
catalogue records rather than a canonical-masterpiece claim.

For 9,702 painter authorities without an existing eligible illustration, a bounded
source query selected one dated, illustrated, museum-connected candidate per
painter. It returned 913 candidates. Entity statements, attribution qualifiers,
creation-date precision, creator life evidence, Commons file metadata and rights,
existing object identities, and image content were checked before attachment.
Only selected reproductions were downloaded.

The final additional-image pass accepted 243 visually reviewed reproductions:

| Result | Local | Production |
| --- | ---: | ---: |
| New artwork records, all in review | 167 | 164 |
| Existing artworks newly illustrated | 76 | 77 |
| New image attachments | 243 | 241 |
| Existing production primary images preserved | — | 2 |

Production reused six already-existing artwork identities rather than creating
duplicates. Three previously unlinked, exact creator labels were reconciled to
existing painter authorities; the original labels were retained. Painter UUIDs
were resolved independently in each database through existing Wikidata identities.
The transaction guard caught the initial identity discrepancy before any production
gap writes committed; the reconciled production plan is
`gap-production-plan-v3.json.gz`.

A final production gap pass added 68 further supported choices. Twenty-seven
selected records for painters already present locally were copied into local
review, including 16 existing production reproductions and their rights evidence.
Their sources and dates were retained; untransferred local holdings were left
unknown. No new painter fixtures or member records were introduced.

A final metadata-only pass added 32 source-backed choices in each database for
painters whose selected reproductions could not be downloaded. All 32 local
records and 30 production records were new review entries; production reused
two existing works after verifying exact creator labels and authorities. Original
creator labels and all existing object metadata were preserved. These selections
are explicitly recorded as having no attached image. See the metadata-gap plans,
receipts and seven successful local/live API checks.

The remaining queue contained 126 painters with 234 P800/P170 notable-work
relationships. A follow-up captured 250 missing source entities before Wikidata
returned HTTP 429; automated source requests stopped. Of the available evidence,
11 candidates had unqualified creator/notable statements, a supported pre-1971
creation year and compatible creator-life dates. One was a literary work and was
excluded. The other 10 became new review artworks and notable selections in each
database, with no image attachment. Eight local/live API checks passed. Unknown,
qualified and later dates remain held, as do 143 relationships requiring source
evidence that could not be retrieved in this pass. See `notable-gap-held.json.gz`
and the notable metadata plans and receipts.

One existing discrepancy remains explicit: Derek Mynott's *In the Conservatory*
has a local circa-1952–1953 date, while production records its creation date as
under review. The production choice was withheld, and neither catalogue date was
silently rewritten.

## Review exclusions and unavailable images

Visual review rejected a portrait reverse, a place photograph instead of the
painting, a schematic recreation, an incomplete triptych view, an unreadable
panorama case view, and an unresolved edition. Creator-life checks also rejected
impossible or implausible recorded creation dates.

The Art Gallery of NSW records *Almost once* with dates 1968 and 1991 and a second
maker. Its photographed large version was therefore withheld from this pre-1970
pass. [Museum record](https://www.artgallery.nsw.gov.au/collection/works/339.1991/).

Wikimedia ultimately rejected 169 image downloads with rate-limit/robot-policy
responses. Requests were slowed and standard thumbnail sizes tried in accordance
with the service's instructions; remaining failures were retained without further
automated attempts. See `gap-image-preparation-retry.json.gz` and
`gap-final-held-v2.json.gz`. Ten rejected derivatives were moved out of application
assets into the source-image review archive. These sources have not been represented as successfully
attached images.

## Verification and delivery

- Go catalogue and HTTP API tests passed; nine focused record-rendering tests passed.
- Real local database checks ran in read-only transactions, with no fixtures.
  The saved-work query uses indexed artist and artwork lookups and enriches one
  returned work. EXPLAIN ANALYZE evidence is retained with the release backup.
- Three painter-preview browser tests passed at 1440, 390 and 320 pixels, covering
  the saved default, neighboring works, explicit selection, filtering, enlargement,
  and accessibility.
- Candidate and live full painter pages passed image-loading, layout and dialog
  checks at those widths. Thirteen additional live painter/image samples passed
  raw image checksum and API identity checks.
- All 243 uploaded selected JPEGs passed checksum verification and the 100,000-byte
  limit. Proportions were preserved. The local supplement reused 16 checked
  production images and their original rights evidence.
- Both isolated production builds passed. Existing unrelated application source,
  public assets and runtime settings were preserved. No Git commit or Terraform
  apply was performed.

These checks do not constitute a 10-million-artwork load test. The new request-time
lookup is bounded to one saved object and does not rank or scan a painter's full
collection. Artist responses remain `no-store`; key choices do not change cached
directory membership or counts.

Initial feature revisions: `artline-api-key-artworks-1008` and
`artline-web-key-artworks-1008`, both promoted successfully to 100%. Subsequent
concurrent releases now serve `artline-api-nonempty-museums-1008` and
`artline-web-remove-artworks-nav-1008`. Fresh live browser and API/image checks
confirmed that these later releases preserve the feature. Their traffic was
retained; no older release was restored.
See [deployment receipt](../../deployment-20261008-key-artworks.json).

Immutable preimages, source archives, release manifests, service configurations,
SQL plan evidence and rollback material are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/key-artworks-20261008/`.
Downloaded source reproductions and reviewed sheets are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/painter-key-artworks-20261008/`.
Accepted new JPEGs are in `apps/web/public/assets/artworks/imported/painter-key-artworks-20261008/`
and the matching private image-bucket prefix. Source policy labels and credits
remain those of the actual providers.

A code rollback must start from the currently serving release and preserve later
unrelated changes; do not blindly restore a pre-feature revision. Data rollback
can restore only this
operation's key selections and image attachments from preimages. Newly introduced
review records and media should be retained or explicitly reviewed before removal;
do not delete unrelated catalogue data. The additional table is additive and does
not need to be dropped to roll back the application release.
