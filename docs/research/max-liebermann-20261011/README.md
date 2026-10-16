# Max Liebermann: artwork discovery and production expansion

Research and delivery date: 11 October 2026. Artist: Max Liebermann
(1847–1935), Wikidata Q158062, Artline
`b05c66ac-a834-4677-857a-79ee9c321a08`.

## Delivered

The [public artist page](https://artlines.org/artists/max-liebermann-q158062)
now contains **796 active artwork records**, up from 109. This operation added
**677 museum-supported objects** and connected **10 existing records** with
verified, unqualified Liebermann creator statements. The additions comprise
69 paintings, 267 drawings, 2 watercolours and 339 prints.

These are physical catalogue objects, including separate museum impressions of
prints. They are not 796 distinct compositions, nor a certified complete lifetime
oeuvre. All new records remain in review. Unified catalogue policy makes them
publicly browsable without changing their audit status.

- [Artline artwork list, CSV](artline-artworks.csv): all 796 linked public records,
  with dates, media, inventory numbers, source links and individual Artline links.
- [Source research register, CSV](source-records.csv): 1,517 source records from
  16 catalogues/datasets, with addition, existing-match, research-hold or discovery
  decisions. Counts overlap across sources and include entries by other makers
  or inseparable book components; do not sum these as unique Liebermann works.
- [Coverage counts](coverage.json), [production receipt](applied.json),
  [final verification](smk-supplement/verification.json), [public page checks](public-page-checks.json).

A supplementary review normalized SMK’s native Danish object types (`Tegning` and
`Litografi`) and added eight further records. Three source date ranges matching
the artist lifespan remain numerically unknown. See the
[supplement receipt](smk-supplement/applied.json) and
[supplement verification](smk-supplement/verification.json). The original main-batch
receipts and CSV exports are preserved separately.

No reproductions were downloaded or attached during this metadata operation.
The subsequent [375-work image pass](../max-liebermann-images-20261011/README.md)
added 227 verified pictures while preserving the ten existing images in that
requested subset. Existing artwork metadata, media,
statuses and holding records were preserved, including on the ten linked records.
Original unlinked creator labels remain as historical evidence. The real local
database was never connected to or modified.

## Museum expansion

| Source | New records |
| --- | ---: |
| Hamburger Kunsthalle | 353 |
| Staatliche Museen zu Berlin | 222 |
| Städel Museum | 27 |
| ALBERTINA | 25 |
| National Gallery of Art | 13 |
| Rijksmuseum | 8 |
| Bavarian State Painting Collections / Neue Pinakothek | 6 |
| SMK | 13 |
| Art Institute of Chicago | 4 |
| Museo Nacional Thyssen-Bornemisza | 2 |
| Museum of Modern Art | 2 |
| Metropolitan Museum of Art | 1 |
| Cleveland Museum of Art | 1 |
| **Total** | **677** |

Each new object has a native source identifier, museum inventory, source citation,
artist relationship and documented holding assertion. Holdings do not establish
current display. SMB departmental source details remain in research evidence;
the catalogue uses the existing Staatliche Museen zu Berlin institution record.

114 additions have no safely parsed numeric creation date. Their literal source
dates or explicit unknowns remain visible; no dates were inferred from the
artist's lifespan. Simple ranges and circa dates preserve their precision.

## Source coverage and remaining work

- [Hamburg exact artist search](https://online-sammlung.hamburger-kunsthalle.de/de/suche?filter%5Bfacet_obj_artistName%5D%5B0%5D=Max%20Liebermann):
  all 588 results and object pages captured. Search results include later makers,
  reproductions and library-volume components, not only independent original works.
- [Berlin search](https://search.smb.museum/?involved=Max+Liebermann):
  all 279 results and native object data captured. Roles distinguish creator,
  designer, depicted person and other participants. Related-object recommendations
  were excluded from object parsing.
- [Städel](https://sammlung.staedelmuseum.de/en/person/liebermann-max):
  27 object pages captured.
- [ALBERTINA](https://sammlungenonline.albertina.at/people/18384/max-liebermann/objects):
  32 object pages captured; five separately indexed versos are held to avoid
  counting the same sheet twice. Other attribution holds are recorded individually.
- Met: 67 native rows mention Liebermann; NGA: 39 constituent-linked rows,
  including two in which he is a former owner. Creator roles and physical-unit
  associations determine eligibility, not a name match alone.
- Chicago: 16 exact artist matches; Cleveland: 6; SMK: 20; MoMA: 7.
  MoMA's official pinned open dataset supplied two standalone prints and five
  book/periodical records. Website access failure was not bypassed.
- Rijksmuseum: 25 fine-art candidates in the already captured OAI source pages.
  This is coverage of that captured source slice, **not a complete Rijksmuseum
  search or full OAI harvest**. Letters and other non-art records are separate.
- Pinakothek: 9 native pages; Thyssen: 2. One Pinakothek branch assignment remains
  held. Two translated painting titles were reconciled with existing WikiArt
  records, retaining those records instead of creating duplicates.
- [WikiArt](https://www.wikiart.org/en/max-liebermann/all-works/text-list):
  the heading reports 72 works; the available index exposed 71 links and 70
  validated object pages. The remaining “The farmer” page lacks usable object
  metadata. All results are preserved for cross-source reconciliation; they were
  not blindly inserted in addition to museum records.
- Wikidata: all 315 items returned by the P170=Q158062 query, with full creator
  claims, date precision, collection IDs, inventory numbers and external source
  links. The bounded query returned fewer than its cap. These are overlapping
  discovery leads, not 315 further unique additions. Ten existing records could
  be securely linked using one unqualified creator statement each.
- Buchheim: 14 object pages captured; native metadata and series/physical-unit
  reconciliation remain outstanding. Salzburg's discoverable results could not
  be fully inspected because the direct source returned HTTP 503.
- [Liebermann-Villa](https://liebermann-villa.de/en/museum/collection-research/)
  describes its collection and research, but the overview is not a complete
  object inventory. No placeholder objects were created from its collection count.

Completeness requires further object-level research in museum collections,
private holdings, lost works and catalogues raisonnés. In particular, Matthias
Eberle's two-volume *Max Liebermann 1847–1935: Werkverzeichnis der Gemälde und
Ölstudien* (1995–1996; ISBN 377746760X) is documented in the
[Rijksmuseum library catalogue](https://www.rijksmuseum.nl/en/collection/publication/Max-Liebermann-1847-1935-Werkverzeichnis-der-Gemalde-und-Olstudien--7073a2adb4d4390e3c81f30d7e1ce955).
Its complete object entries were not available in this pass. Published print
catalogues and ongoing pastel research also need object-by-object reconciliation.
The current source register must not be described as a complete catalogue raisonné.

## Identity and unit review

- Source URLs, native IDs, museum inventories and exact creator roles were
  reconciled with the existing production catalogue before insertion.
- Hamburg inventory variants with and without `HK-` were reconciled. This caught
  an otherwise duplicated *Gerhart Hauptmann* painting. Distinct drawings and
  prints with the same title remain separate when native object evidence supports it.
- Pinakothek artwork dates come from the artwork title block; the separate artist
  lifespan `(1847–1935)` is not an artwork creation range.
- Mechanical reproductions, makers working “after Liebermann,” owned-only or
  depicted-only objects, inseparable NGA children, bound library components and
  separately indexed versos were held. Their literal source records remain in
  the register. Some holds may become eligible after further physical-unit review.
- Two existing unlinked title leads duplicate already linked paintings and remain
  untouched; they were not linked to inflate the artist count.
- Unknown or complex dates remain explicit. No artwork was declared a masterpiece
  or currently on view. No artist or artwork was published by status mutation.

## Verification, recovery and reproducibility

`ops/research-max-liebermann-20261011.py` performs creator-scoped, resumable metadata
discovery without database writes or image downloads.
`ops/deliver-max-liebermann-20261011.py` records selection, review, read-only
preflight, production application, verification and CSV export.

The reviewed plan SHA-256 is
`e3bb10c1720da7e70347266e5ba86c8715e4df9995ae5c8fc948c5fbdb51b8dd`.
The supplemental plan SHA-256 is
`97c1d8ea2a5ed7e18d0948c052e1f8d3611064930463624ff9f8f46a1e5755be`.
Earlier drafts are retained as evidence. Production writes used one transaction,
the shared curated-ingestion advisory lock, live collision checks and a stable
audit marker for recovery. A successful Cloud SQL backup preceded mutation:
`1791700773769`, description `max-liebermann-artwork-expansion-20261011`.
Local recovery receipts and pre/post images are under
`~/Library/Application Support/Artline/backups/max-liebermann-20261011/`.

Verification re-read all inserted and linked records, compared preserved records
with preimages, checked citations and artist/holding relationships, and traversed
all **16 bounded public API pages**, finding exactly 796 unique IDs. The artist
page and a new individual artwork page returned HTTP 200 without a login redirect.
All 1,085 captured source responses passed SHA-256 checks; non-200 responses remain
recorded as access failures. Reused US source files were also hash-checked.

Read-only artist query plans and museum-scoped collision evidence were saved.
The broader initial museum snapshot was expensive and was reused for subsequent
editorial passes; final live collision checks use requested IDs, URLs and inventories.
These checks establish this batch's correctness. They are not a 10-million-row
load benchmark. No application deployment, schema migration, commit or local
database mutation was required.
