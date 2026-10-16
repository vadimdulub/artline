# Switzerland, Argentina, Uruguay and Paraguay

The subsequent [additional 1,000-artwork batch](../switzerland-southern-cone-1000-20261011/README.md)
delivered 1,000 new production objects and 98 images. Its counts are separate
from the 176 additions reported below; image and nationwide coverage gaps remain
explicit in the newer audit and institution ledgers.

Requested 11 October 2026. Nationwide museum work proceeds in this order:
Switzerland, Argentina, Uruguay, Paraguay. This supersedes India as the next
country after Switzerland; earlier research remains preserved.

Broad institution coverage precedes deeper collections. National directories
are research inventories, not proof of eligible artworks or current display.
Every researched institution must retain its identity sources, catalogue
reconciliation, delivered objects and unresolved source gaps separately.

## Starting evidence

The [earlier Swiss campaign](../switzerland-india-museums-20261011/README.md)
captured 1,328 directory profiles and 1,328 native-site outcomes. Its first
three production waves are now committed and verified: 90 new review artworks,
five existing artworks enriched, and one new primary image across 27 distinct
collections. These additions are not new additions for this continuation.
`swiss-waves1-3-verified-handoff.json` points to the immutable plans, final
verification and per-institution ledger; reconcile those identities before
overlapping Swiss additions. The original conversation explicitly reconfirmed
Argentina, Uruguay and Paraguay as the next countries, deferring India.

The earlier campaign also captured Argentina's official national-museum page
as `AR/national-directory.json.gz` (24 named institutions and cultural venues).
This is a national-government subset, not all Argentine museums. Its separate
`datos.cultura.gob.ar` request returned HTTP 403 and remains held.

## Safeguards

- Select documented museum objects created through 1970. Unknown dates remain
  explicit review cases; never infer creation from artist lifetimes or accession.
- Reconcile native IDs, accessions, title variants, creators and object versions
  against existing catalogue records before adding objects or museum links.
- New records remain in review; existing statuses, pictures and metadata remain
  preserved unless a separately evidenced correction is explicitly recorded.
- Apply `docs/ARTLINE_IMAGE_USE.md`, retaining actual rights labels, source
  evidence and credits. Prepare and visually verify only selected reproductions.
- Archive source images and database recovery snapshots under Artline's Library
  directories. Never write catalogue or test fixtures to the real local database.
- Do not invent objects for empty museums. Holding evidence is not a current
  display claim. No application deployment or commit is part of this request.

## Status

The initial directory pass and six selected production batches are delivered.
**Nationwide artwork coverage remains incomplete.** Directory pagination is
exhausted for the captured sources, but many institutions have no accessible
individual object catalogue. No empty museum was populated with invented works.

### Production delivery in this continuation

| Country | New review artworks | Existing objects enriched | Collections receiving object work |
|---|---:|---:|---:|
| Switzerland | 18 | 5 | 2 |
| Argentina | 81 | 4 | 3 |
| Uruguay | 58 | 0 | 3 |
| Paraguay | 19 | 0 | 3 |
| **Total** | **176** | **9** | **11** |

The 185 objects have 185 source citations and 184 new holding assertions; one
accepted holding was already present. New objects retain review status. The 62
new records without numerical date bounds include explicitly unknown dates and
Paraguayan century captions: the supplied centuries remain in `date_display`.
Maker qualifications, unnamed makers and unresolved named creators remain explicit.

- Switzerland: Museo Comunale d'Arte Moderna di Ascona and Museum zu Allerheiligen.
- Argentina: Museo Pettoruti (57 objects), Malba (8) and MNBA Neuquén (20).
- Uruguay: MNAV (40), Museo Figari (2) and Museo Blanes (16).
- Paraguay: Museo de Arte Sacro (6), Casa de la Independencia (8) and the
  Diocesan Museum of Jesuit–Guaraní Art in San Ignacio Guazú (5).

Eight additional existing collections received evidenced city/country placement,
covering 29 existing artwork records without altering their holdings: seven Swiss
collections and MNBA Buenos Aires. This includes separate Winterthur venues;
they were not merged. Paraguay was added to the country reference table so its
three delivered museums can participate in country browsing.

Two selected WikiArt reproductions were delivered: Kahlo's *Autorretrato con
chango y loro* and Matta's *The Disasters of Mysticism*. Full source frames and
actual rights labels are preserved; derivatives are 80,467 and 97,000 bytes.
The Matta attachment uses the native museum's circa-1942 evidence for image
eligibility while preserving the existing catalogue's unknown date.
Six additional Commons matches have file-specific rights evidence but remain
unattached after the media host returned HTTP 429. No rate-limit workaround was
used. Native Paraguayan sculpture photographs remain rights-research gaps.

### Directory evidence and remaining work

| Country | Captured source entries | Reconciled research ledger |
|---|---|---|
| Switzerland | 1,328 museum-directory profiles, reused from the earlier campaign | [Swiss ledger](CH/institution-reconciliation.csv) |
| Argentina | 734 Ibermuseos profiles | [Argentina ledger](AR/institution-reconciliation.csv) |
| Uruguay | 252 government profiles plus 233 Ibermuseos profiles | [Uruguay ledger](UY/institution-reconciliation.csv) |
| Paraguay | 54 government portal entries, 108 ICOM entries and 7 Ibermuseos profiles | [Paraguay ledger](PY/institution-reconciliation.csv) |

These counts overlap. They are neither unique-museum totals nor artwork totals.
Paraguay's sources include archives, libraries, cultural centres and event leads;
the Swiss source includes cross-border leads. Each source entry retains its
individual identity, native-site result and object-source gap.

The additional collection-link pass recorded outcomes for all 734 Argentine,
485 Uruguayan and 169 Paraguayan source entries. Linked collection pages were
found for 54, 39 and 6 entries respectively. These are metadata discovery leads,
including generic municipal pages that still require institution-specific review.
The prior Swiss campaign retains its 200 collection-discovery outcomes.

Paraguay's initial supplemental pass encountered a common FONDEC sponsor link.
The corrected `native-reviewed` and `collection-reviewed` outcomes supersede
that pass: 41 linked pages checked, 25 access/availability gaps and 49 entries
without a supplied individual website among the 115 supplemental entries.

Object reconciliation holds are recorded in
[object-and-image-gaps.csv](object-and-image-gaps.csv): the duplicate Pettoruti
*Recuerdo* page, ambiguous Figari *Candombe* and Torres-García composition
identities, a Hodler version, a 1983 Valenti work, and Berni's creation/modification
span crossing 1970. Additional source-specific gaps remain beside each batch.
Blanes's display of the MNAV-owned *Juramento* was not converted into Blanes
ownership or a fresh on-view claim. Neuquén custody likewise remains distinct
from national-collection ownership. Paraguay's government portal supplies an
incorrect Asunción address for the San Ignacio museum; the university museum
source establishes the accepted San Ignacio Guazú location.

Next collection work should use the captured native links, reconcile additional
institution aliases/duplicate legacy records, and inspect individual catalogue
objects. Current gaps include the inaccessible Argentine national-data endpoint,
native sites returning access restrictions, unnamed gallery slides, collection
lists lacking object facts, and images without supported reuse evidence. The
older Swiss corpus and all unresolved countries remain available for continuation.

### Verification and recovery

[Completion verification](completion-verification.json) links the production
audit and both image receipts. [The catalogue audit](production-verification-v3.json)
checks pinned input files, captured object-source hashes, exact dates and maker
labels, accepted holdings, preserved existing metadata/images, nonempty museums
and geography. The image attachment transactions separately verify that only
media associations change. Uploaded bytes were checked against their public URLs.
Python compilation and targeted whitespace checks passed.

One unrelated municipal refuse-collection capture has inconsistent receipt/body
hashes from concurrent retrieval. Its original evidence is preserved and excluded
from valid object evidence. All delivered object captures passed integrity checks;
per-URL process locks now prevent that race.

Production recovery: successful Cloud SQL backup `1791705399399`; immutable plans,
locked preimages and transaction after-images are under the Artline Library backup
directory. Source image originals are in the corresponding Library image archive.
The real local database received **zero writes**. No publication status changes,
current-display claims, application deployment or commits were made.

Query plans are saved with each batch. Lookups use selected institutions, creators
and identifiers. This operational verification is not a ten-million-row load test;
no application query behavior changed in this pass.
