# Dutch and German museum coverage audit — 17 September 2026

## Outcome

The gap is real. Germany has very sparse coverage of major painting collections;
the Netherlands is heavily concentrated in the Rijksmuseum. Missing images are
only part of the problem: missing museum geography and split institution
identities also affect discovery.

This was a read-only audit of the actual local and cloud `artline` databases,
with primary-source research. No catalogue writes, image downloads/uploads,
publication, commits, or deployment were performed.

## Measured baseline

Local snapshot: 2026-09-17 10:07:33 UTC. Cloud snapshot: 10:07:35 UTC.
Both connections reported `transaction_read_only=on`. The following totals and
all per-institution counts agree between the two databases.

| Scoped collection | Institution records | Eligible paintings | With primary media | Missing primary media |
|---|---:|---:|---:|---:|
| Netherlands | 10 | 1,459 | 1,434 | 25 |
| Germany | 24 | 393 | 336 | 57 |

These are **our catalogue counts**, not national or museum collection totals.
Eligibility means `work_type='painting'` and the database's creation-date
classifier returns `eligible` under the through-1970 policy. Review records are
included. Drawings, prints, sculpture, unknown dates, and ineligible dates are
not included in this painting baseline; they remain in the evidence snapshots.

"With primary media" means an attached primary-media record, not a fresh check
of image bytes, delivery, or public visibility. This pass does not certify that
every recorded image works in production.

The Rijksmuseum accounts for 1,298 of the 1,459 Dutch eligible paintings (89.0%).
The other nine scoped Dutch institution records together account for only 161.

### Priority examples

| Museum | Eligible paintings | With primary media | Main issue |
|---|---:|---:|---|
| Gemäldegalerie, Berlin | 1 | 0 | Extremely sparse linked collection |
| Alte Pinakothek, Munich, two records combined | 9 | 8 | Sparse collection and split institution identity |
| Städel, Frankfurt | 61 | 51 | Collection expansion and 10 image gaps |
| Hamburger Kunsthalle | 24 | 23 | Collection expansion |
| Staatliche Kunsthalle Karlsruhe | 127 | 88 | 39 image gaps in existing eligible paintings |
| Museum Folkwang, Essen | 2 | 1 | Sparse collection and missing geography |
| Neue Nationalgalerie, Berlin | 12 | 12 | Missing geography and collection expansion |
| Mauritshuis, The Hague | 23 | 15 | Collection expansion and 8 image gaps |
| Van Gogh Museum, Amsterdam | 19 | 10 | Collection expansion; reproduction rights need care |
| Kröller-Müller Museum, Otterlo | 16 | 13 | Collection expansion and 3 image gaps |
| Museum Boijmans Van Beuningen, Rotterdam | 36 | 34 | Collection expansion |
| Frans Hals Museum, Haarlem | 8 | 8 | Sparse collection and missing geography |
| Stedelijk Museum, Amsterdam | 1 | 1 | Sparse pre-1971 collection and missing geography |

Alte Pinakothek's combined count is a union of artwork IDs, not an unverified
sum. This does not itself authorize merging its institution records.

## Discovery and identity issues

- Only 5 of 10 scoped Dutch institution records and 8 of 24 German records have
  stored country geography. The remaining 21 have neither a country on the
  institution's place nor venue-country entries in this snapshot. They contain
  67 Dutch and 116 German eligible paintings.
- The current museum country filter requires an eligible venue joined to a
  country-bearing place; see `apps/server/internal/catalog/museums.go`,
  `Repository.Museums`. These records cannot match that country filter as stored.
  This is code/data evidence, not a deployed-UI test.
- `alte-pinakothek` and `wikimedia-museum-q154568` describe the same named museum
  but split its linked works across two institution records. Reconciliation
  should preserve sources and references rather than blindly deleting one.
- `wikimedia-museum-q1501219`, named "Gemäldegalerie Alte Meister", points to
  `museum-kassel.de`. It is the Kassel institution, **not Dresden**. Names alone
  are unsafe identifiers.
- `spain-research-museum-q700959` is labelled Wallraf–Richartz Museum and points
  to its official website. Its slug must not be used as Spanish geography.
- Berlin's Nationalgalerie umbrella and Neue Nationalgalerie are different
  organizational/venue concepts; do not merge them merely because names overlap.
- Museum geography is independent of artist nationality. Previous Dutch-artist
  work involving the Metropolitan Museum does not fill Dutch-museum coverage.

An alias/name/domain search of the complete 857-record local institution
register did not identify confident matches for Dresden's **Gemäldegalerie Alte
Meister**, Kunstmuseum Den Haag, Teylers Museum, Lenbachhaus, Museum Ludwig,
Kunsthalle Bremen, Staatsgalerie Stuttgart, or Museum der bildenden Künste
Leipzig. These are identity-research priorities, not proof that every artwork
from those collections is absent: some works may lack a reconciled museum link.

## Primary-source acquisition routes

Sources checked on 17 September 2026. These are selection and verification
routes, not permission for exhaustive harvesting. Large museum-wide totals
include other media and post-1970 works and must not be used as denominators
for our eligible-painting counts.

| Institution | Primary source | Practical next step |
|---|---|---|
| Mauritshuis | [Collection](https://www.mauritshuis.nl/en/our-collection); [image policy](https://www.mauritshuis.nl/contact/beeldmateriaal-aanvragen) | Start with museum-designated highlights; retain object ID, attribution, date, and collection credit. The collection-download policy permits reuse, but press-archive restrictions are separate. |
| Städel | [Digital Collection and reuse policy](https://sammlung.staedelmuseum.de/en/concept) | Select Old Master and eligible modern paintings. Current policy makes images of public-domain artworks freely reusable; preserve the museum credit and exact object-level evidence. Metadata and curatorial prose have different reuse terms. |
| Karlsruhe | [Official CC0 policy](https://www.kunsthalle-karlsruhe.de/en/cc0/) | Research the 39 existing image gaps first. CC0 applies to reproductions of public-domain works, not automatically to every object online. |
| Pinakotheken | [Bavarian State Painting Collections catalogue](https://www.sammlung.pinakothek.de/en) | Use institution, creation date, and object filters. Its catalogue spans multiple museums: keep holding institution and display location separate. Download only images carrying the applicable CC BY-SA 4.0 designation. |
| Dresden Old Masters | [Museum and official collection link](https://gemaeldegalerie.skd.museum/en/) | Resolve the missing institution identity, then select museum-supported highlights through SKD object records. Image reuse is not cleared by the existence of a viewer. |
| Kröller-Müller | [Official collection](https://www.krollermuller.nl/en/collection) | Build a selected pre-1971 painting list, recording native object identities; research image rights separately. |
| Teylers | [Art collection and catalogue link](https://teylersmuseum.nl/en/discover/collection/art) | Include its nineteenth-century paintings and distinguish its important drawings/prints from paintings. Its own overview identifies Jacobus van Looy's *The Garden* (1893) as a masterpiece. |
| Kunstmuseum Den Haag | [Official museum](https://www.kunstmuseum.nl/en) | Resolve institution identity and follow the museum's collection route; prioritize eligible Mondrian/De Stijl works without assuming rights clearance. |
| Lenbachhaus | [Official collection search](https://www.lenbachhaus.de/en/digital/collection-online/search) | Resolve institution identity; select eligible works, including Russian-linked artists where documented. Keep post-1970 works outside automatic eligibility. |
| Rijksmuseum | [Current data-service documentation](https://data.rijksmuseum.nl/docs/); [bounded search](https://data.rijksmuseum.nl/docs/search) | Lower priority than the sparse museums above. The current search route supplies Linked Art identifiers without an API key; use selected object resolution, not whole-collection image downloads. |

Van Gogh Museum's indexed [collection-image conditions](https://www.vangoghmuseum.nl/assets/05aed642-6e2a-46e6-bb93-3a6826d63e91/Conditions-for-Use-of-Collection-Images-Van-Gogh-Museum-2022?c=1ae93a4fe2d6eb2875672ed16d59058741397476be6cd1c15ca16cc5e924d786)
describe a non-commercial download allowance and a separate commercial-use
contact. Treat this as a restriction requiring current verification, **not** a
blanket open licence. No images from that source were acquired in this audit.

## Recommended implementation order, subject to authorization

1. Reconcile museum identities and source country/city/venue geography, starting
   with the 21 known gaps. Geography repair must not accept unverified holdings,
   publish records, or assert current display.
2. Prepare a bounded first metadata batch for Berlin Gemäldegalerie, Dresden Old
   Masters, Alte Pinakothek, Mauritshuis, Van Gogh Museum, Kröller-Müller,
   Kunstmuseum Den Haag, and Frans Hals Museum. Include creators of all
   nationalities; deliberately check women artists and the Russian/Greek/
   Byzantine priorities where supported by those collections.
3. Work the rights-cleared image backlog in Karlsruhe, Städel, and Mauritshuis
   alongside that metadata batch. The combined existing gap is 57 images;
   this is a candidate queue, not a promise that all 57 have reusable files.
4. Expand regional/modern coverage: Folkwang, Wallraf–Richartz, Kunstpalast,
   Lenbachhaus, Bremen, Stuttgart, Leipzig, Museum Ludwig, Stedelijk, Centraal,
   Rijksmuseum Twenthe, Teylers, and Boijmans. Apply the creation cutoff to each
   work, not to the artist's life dates.
5. Preserve object-source snapshots, native IDs, attribution wording, uncertain
   dates, image licence/credit, and checksums. Keep museum highlights separate
   from personal selections. Retain unresolved named-creator records in review;
   handle anonymous/workshop/icon cases through their explicitly supported
   workflow, not by forcing them into the expanded named-creator CSV import.
6. Verify database parity, bounded API output, and selected image delivery after
   an authorized import. Publishing and deployment remain separate decisions.

## Evidence and limits

- `audit.py`: replayable read-only query logic. It uses institution-scoped
  artwork IDs before enrichment and a repeatable-read transaction per database.
  Output creation is exclusive, protecting existing snapshots from overwrite.
- `local-summary.json` / `cloud-summary.json`: timestamps, read-only evidence,
  and country totals.
- `local-institutions.json` / `cloud-institutions.json`: all 34 scoped records,
  research-only country classifications, and per-museum counts.
- `local-scoped-artworks.json` / `cloud-scoped-artworks.json`: selected artwork
  details, date classification, creator-link state, and primary-media metadata.
- `local-institution-register.json` / `cloud-institution-register.json`: complete
  bounded institution-register snapshots for alias checking.

Scope includes current institution pointers and nonsuperseded holding assertions
in `review` or `accepted`. It does not establish that every holding is validated.
The exported counter named `review_holding_only_all_types` includes either of
those assertion states when there is no matching current institution pointer.
It should be read as an assertion-only count, not solely unaccepted assertions.

The 21 additional country mappings are explicit research crosswalks based on
named institutions and their recorded identifiers/websites; they were not
applied to the database. The scope is not a comprehensive national museum list.

Institution snapshots match exactly. Artwork content compared by stable slug
also matches after excluding database-specific artwork/media UUIDs and storage
paths and comparing media attachment as a boolean. Raw artwork snapshots are
not byte-identical: 915 local artwork IDs do not occur in the cloud snapshot.
Never use local UUIDs blindly for production updates.

No performance load test, production UI test, or fresh current-on-view check
was performed. Review/publication and deployment-specific preview rules mean
these database totals must not be presented as guaranteed public-facing totals.
