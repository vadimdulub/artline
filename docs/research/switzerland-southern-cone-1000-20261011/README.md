# Additional 1,000 artworks: Switzerland, Argentina, Uruguay and Paraguay

Requested and delivered on 11 October 2026. The user requested “add 1000
artworks for this counteis and images.” This batch adds **1,000 distinct new
production artwork records and 98 verified primary images**. The earlier
[176 additions](../switzerland-southern-cone-museums-20261011/README.md) are
separate and do not count toward this target.

**Image coverage remains incomplete: 902 of these new works have no image.**
Nationwide museum collection coverage also remains incomplete. Directory entries,
unselected source records and existing catalogue objects are not new artworks.

| Country / collection | New artworks | New primary images |
|---|---:|---:|
| Switzerland — Kunstmuseum Basel | 800 | 0 |
| Switzerland — Museum Rietberg | 100 | 98 |
| Argentina — MNBA Neuquén | 35 | 0 |
| Uruguay — MNAV, Montevideo | 50 | 0 |
| Paraguay — MNBA, Asunción | 15 | 0 |
| **Total** | **1,000** | **98** |

Country totals are Switzerland 900, Argentina 35, Uruguay 50 and Paraguay 15.
All 1,000 have native source identifiers, source citations and accepted museum
holding assertions. There are 269 supported links to existing artist records;
unresolved and qualified creators retain their original object-level labels.
One institution record was added for MNBA Asunción, with official address and
country evidence. These are holdings, with **no current-display assertions**.

All new artworks retain `review` / `research_candidate` and remain unpublished.
Under the unified catalogue policy, active review records are available in the
catalogue; historical publication status is not a browsing gate. All selected
works have explicit source creation years/ranges within the through-1970 scope.
The image selection follows the existing through-1955 policy. Creator lifespans
were never substituted for artwork dates.

## Sources and object reconciliation

- [Kunstmuseum Basel collection](https://sammlung.kunstmuseumbasel.ch/): a bounded
  6,000-record metadata index informed selection of 1,600 individual object pages.
  Final normalization yielded 1,214 eligible candidates and 386 explicit holds.
  Exact native IDs, inventories, existing creator/title/date matches and physical
  object relationships were reconciled before selecting the 800 new objects.
  Loans, unresolved related components, reverse views and ambiguous dates were
  held. The initial and final fact sets are retained, not silently overwritten.
- [Museum Rietberg / City of Zürich open data](https://data.stadt-zuerich.ch/dataset/mrz_drenowatz_sammlung):
  189 object records yielded 171 eligible candidates and 18 holds; 100 distinct
  new objects were selected after existing-record reconciliation. Inventoried
  album leaves retain their individual titles and identities; ensemble parents
  were excluded when component leaves are present. Attribution qualifications,
  painter/calligrapher roles, original date labels and date bounds are preserved.
- [MNBA Neuquén](https://www.mnbaneuquen.gob.ar/): 200 individual collection pages
  yielded 59 explicitly dated candidates and 141 held cases. Existing objects
  and ambiguous versions were reconciled before selecting 35 new works. Original
  creator labels remain explicit; dimensions do not acquire invented units.
- [MNAV public inventory](https://acervo.mnav.gub.uy/datos.php?tipo=obras&encabezado=1):
  8,198 object rows and 996 creator rows were captured. Selection required an
  explicit eligible creation date, numeric inventory and native location at MNAV,
  excluding documents. Of 1,122 eligible candidates, 50 distinct new works were
  selected. All other rows retain their source data and selection outcomes.
- [Paraguay's Secretaría Nacional de Cultura](https://cultura.gov.py/museos/museo-nacional-de-bellas-artes/)
  establishes MNBA Asunción's institution identity. Twenty-three object pages
  reproducing the museum collection catalogue on Portal Guaraní were reviewed;
  15 dated works were selected and eight held. For example, the
  [Moreno Carbonero catalogue entry](https://www.portalguarani.com/detalles_museos_otras_obras.php?PqwoiflUYTeslk=MTYxNw==)
  supplies object-specific title, creator, date, medium and dimensions. These
  archival holdings carry a documented 0.91 editorial confidence assessment,
  not a calibrated probability or current display claim. Pages identifying stolen
  works were excluded. Juan Luna's painting also has fresh 2026 government
  holding corroboration. Biographical errors were not imported as artwork facts.

Candidate plans preserve existing-object matches, version ambiguities and
eligible but unselected records. Raw captures retain retrieval URLs, timestamps
and SHA-256 evidence. `CH/final-facts.json.gz`, `RIETBERG/selected-facts.json.gz`,
`AR/complete-facts.json.gz`, `UY/final-facts.json.gz` and
`PY/complete-facts.json.gz` record the complete researched object outcomes.

## Images delivered and remaining gaps

The Rietberg publisher expressly designates its image files public domain,
separately from its metadata licence. Only the 100 selected exact inventory-named
artwork files were retrieved from the public ZIP using exact member byte ranges;
the complete archive and provenance/seal image collection were not downloaded.
Each member's length and CRC were checked, and original source files are archived
under Artline's Library source-image directory.

All 100 prepared derivatives received visual review across three contact sheets,
with closer inspection of dimension discrepancies. Ninety-eight complete painting
fields were accepted. Album spreads preserve their facing calligraphy pages;
fan backgrounds and calibration marks remain intact. Full source frames were
proportionally resized without cropping. Photographer/museum credit and actual
public-domain evidence accompany each attachment. Every JPEG is at most 100,000
bytes, and its public `artlines.org` response matched the prepared SHA-256.

Two images were rejected: RCH 1134 shows a title/frontispiece instead of the full
poem scroll; RCH 1155 shows only part of a landscape handscroll. Their originals
and rejected derivatives remain in Library research storage, outside public
assets. Neither is attached or uploaded. Detailed decisions appear in
`CH-rietberg/visual-review.json` and `rejected-derivative-locations.json`.

The 902 image gaps are individually recorded in [image-gaps-final.csv](image-gaps-final.csv):

- 800 Basel objects: the first selected native image request returned HTTP 403.
  Provider image requests stopped immediately. No alternate-size, header or
  route workaround was used. Public metadata remained separately accessible.
- 35 Argentine, 50 Uruguayan and 15 Paraguayan works: native images lack a
  sufficient reproduction grant, or an approved exact object/version match is
  still unresolved. Actual source restrictions remain recorded.
- Two Rietberg works: incomplete source photographs, as described above.

Independent WikiArt checks covered 30 existing verified artist profiles plus
three profiles recovered from existing citations, with additional selected
Southern Cone artist indexes. No secure new image match resulted. Those bounded
index checks do not establish that WikiArt has no suitable image anywhere.
Commons media requests remain held after the earlier HTTP 429; no workaround
or automatic retry was attempted. See `source-access-holds.json` and `wikiart/`.

## Verification and recovery

[production-verification-final.json](production-verification-final.json) verifies
all 1,000 planned IDs in a read-only production transaction: source/native IDs,
852 distinct source-body hashes, titles, dates, attributions, country placement,
accepted holdings and all 98 image bytes/rights/upload receipts. Image attachment
also asserted that metadata, creators, holdings and publication state were
unchanged. [catalogue-manifest-final.csv](catalogue-manifest-final.csv) lists every
new object and its image outcome.

The six immutable applied plans and receipts are in `CH-wave1`, `CH-wave2`,
`CH-rietberg`, `AR-wave1`, `UY-wave1` and `PY-wave1`. Cloud SQL backup
**1791710730189** completed successfully before ingestion. Row snapshots and
recovery plans live under
`~/Library/Application Support/Artline/backups/switzerland-southern-cone-1000-20261011/`.
Original images live under the matching `Artline/source-images/` directory.
The real local database received **zero connections and zero changes**.
No application deployment or commit was performed.

Updated institution ledgers preserve all overlapping source entries: 1,328 Swiss,
734 Argentine, 485 Uruguayan and 169 Paraguayan entries. These are research rows,
not unique museums or proof of artwork coverage. Each country directory contains
`institution-reconciliation-final.csv`, retaining unresolved institution and
object-source gaps. Queries were scoped to selected IDs and institutions; the
captured production query plan is not a ten-million-row load test.
