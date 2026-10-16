# South America: 1,057 additional artworks

The request was “try to cover all south america! add at least 1000 artworks.”
On 11 October 2026 this batch delivered **1,057 distinct new production artworks**:
1,056 across all twelve independent South American countries, plus one in French
Guiana. Earlier Swiss/Southern Cone deliveries are excluded from this count.

An existing Venezuelan painting was also linked to its documented museum and
received **one verified primary image**. It does not count as a new artwork.
**All 1,057 new works still have image gaps.** Complete nationwide museum holdings
coverage remains unfinished; directory entries and research candidates are not
counted as delivered artworks.

| Country / territory | New artworks | Selected collections |
|---|---:|---|
| Brazil | 350 | MASP, São Paulo |
| Colombia | 250 | Banco de la República collection, Bogotá |
| Peru | 180 | Museo de Arte de Lima |
| Chile | 150 | MNBA Santiago 144; Museo Regional de Rancagua 6 |
| Ecuador | 70 | Museo Nahím Isaías, Guayaquil |
| Uruguay | 30 | MNAV, Montevideo |
| Argentina | 10 | MNBA Neuquén |
| Venezuela | 10 | Museo Arturo Michelena, Caracas |
| Bolivia | 3 | Museo Nacional de Arte, La Paz |
| Guyana | 1 | National Gallery, Castellani House |
| Suriname | 1 | Stichting Surinaams Museum, Paramaribo |
| Paraguay | 1 | MNBA Asunción |
| French Guiana, France | 1 | Musée Alexandre-Franconie, Cayenne |
| **Total** | **1,057** | |

The existing work is Arturo Michelena's *Miranda en La Carraca* (1896), now linked
to Galería de Arte Nacional, Caracas. Its exact existing WikiArt identity was
reused. The large GAN painting is distinguished from smaller artist replicas.

## Sources and editorial decisions

- [MASP](https://masp.org.br/acervo/): 650 selected object pages yielded 558
  dated fine-art candidates. Final selection excludes loans/deposits, 51 bronzes
  whose model/casting dates need reconciliation, a creation date contradicting
  the source's own creator biography, and unresolved translated-title/version
  candidates. Only `BR-final` was applied; the earlier plans were superseded.
- [SURDOC](https://www.surdoc.cl/): 840 bounded object records across three
  institutions yielded 327 eligible facts. Duplicate inventory records were
  reconciled before selecting 150 objects. The 80 researched Pinacoteca
  Universidad de Concepción records did not supply unambiguous creation fields
  for this selection; signature transcriptions and acquisition dates were not
  automatically substituted. That institution received no placeholder records.
- [Banco de la República](https://colecciones.banrepcultural.org/es/arte): native
  object identities, creation dates, creators and inventories support 250 new
  objects. The collection authority is kept distinct from individual venues
  such as Museo Botero, MAMU and Casa de Moneda. Historical reserve/display text
  is preserved as source evidence, never asserted as current display.
- [MALI](https://coleccion.mali.pe/): 426 museum-designated highlights were
  checked; 238 explicitly dated candidates received individual detail checks,
  yielding 196 eligible fine-art facts and 180 selected new works.
- [Ecuador's national catalogue](https://colecciones-ecuador.skin-web.org/):
  150 individual records yielded 89 eligible fine-art facts; 70 were selected.
  Explicit eighteenth/nineteenth-century labels retain their date ranges.
  Twentieth-century ranges crossing 1970 and unknown dates were held.
- Argentina and Uruguay reuse captured native museum records from the previous
  research, with a fresh production duplicate check. Paraguay adds Vicente
  Forte's *Pescado y mesa* (1962), supported by the MNBA catalogue reproduced on
  [Portal Guaraní](https://www.portalguarani.com/detalles_museos_otras_obras.php?PqwoiflUYTeslk=MTYzOA==).
- Venezuela's [Ministry of Culture collection list](https://www.mincultura.gob.ve/noticias/hoy-16-de-junio-el-museo-arturo-michelena-celebra-su-60-aniversario/)
  supports the ten new MAM paintings/studies. Approximate dates remain
  approximate; a study is not collapsed into its finished composition.
- Bolivia's [1999 museum loan annex](https://www.lexivox.org/norms/BO-DS-25549.xhtml)
  explicitly identifies three selected paintings as La Paz museum property.
  This is archival holding evidence, not a fresh display assertion. The fourth
  painting, San Pedro de Alcántara, remains held because catalogues disagree on
  title/dimensions. The source is labelled as a decree transcription.
- Guyana's [artist conversation and gallery caption](https://www.stabroeknews.com/2015/05/03/features/guiana-land-of-the-dolorous-garde/)
  document E. R. Burrowes's 1951 painting in the National Collection.
- Page 58 of the [Stedelijk Museum reader](https://stedelijkstudies.com/wp-content/uploads/2021/07/Surinamese-School-Reader-2021.pdf)
  was rendered and visually checked: Nic Loning, *MAXIE Queen of Paramaribo*,
  1967, oil on linen, collection Stichting Surinaams Museum, Paramaribo.
  Amsterdam was the exhibition venue, not the holding institution.
- French Guiana's drawing is supported by the [French Ministry of Culture's
  Joconde record](https://pop.culture.gouv.fr/notice/joconde/M1063000042). The
  original monogram LK and first-half-twentieth-century date remain explicit.

All new works retain `review`, `research_candidate` and an unpublished state.
The unified catalogue exposes active review records. Original creator labels,
qualified attributions, inventories and unknown fields are preserved. There are
66 supported links to existing artist records; other creators remain explicit
object-level labels. No biographies, missing inventories or current-display
claims were invented. Fifteen collections were affected, including eleven new,
nonempty institutions. Country/city evidence accompanies their placement.

## Images, coverage gaps and verification

The single delivered image is WikiArt's exact *Miranda en La Carraca*
reproduction. Its actual “Public domain” label and the separate user-approved
WikiArt policy are retained. The complete source frame was visually reviewed,
proportionally reduced to a 94,228-byte JPEG, uploaded, attached and independently
retrieved from the public site with a matching SHA-256. Source originals and
recovery snapshots are in Artline's Library directories, outside Documents.

Native noncommercial/restricted or unlicensed reproductions remain unserved.
The existing image cutoff is through 1955. Commons media remains held after its
earlier HTTP 429; the IDB PDF host returned HTTP 403 and was not bypassed. Museum
website integrity/DNS failures and all other gaps are recorded in
[research-gaps-reviewed.json](research-gaps-reviewed.json) and the per-work
[image ledger](image-gaps-final.csv). The Soviet Realism image approval is a
separate collection policy and was not generalized to this batch.

The [production audit](production-verification-final.json) checks all planned
IDs, 1,018 distinct source-body hashes, native identifiers, citations, date and
attribution preservation, country placement, accepted holdings and image evidence
in a read-only production transaction. The [manifest](catalogue-manifest-final.csv)
lists each new object and the separate existing-object enrichment. Public API
checks succeeded for one new work in every country and French Guiana; the image
was also fetched and checksum-verified publicly.

Cloud SQL backup **1791712823423** succeeded before ingestion. Recovery plans and
row snapshots are under
`~/Library/Application Support/Artline/backups/south-america-1000-20261011/`.
New artwork counts exclude prior batches, existing objects, unresolved variants,
unsupported source records and directory leads. No local database connection,
fixture, publication change, commit or application deployment was performed.
The captured scoped query plan is not a ten-million-row load test.

## Museum research ledger

The [combined institution ledger](institution-reconciliation-final.csv) preserves
**5,798 research rows** across the twelve countries. These include overlapping
directory entries, native institutional leads and the delivered collection
authorities; they are not a count of unique museums. Each row retains source
evidence, identity candidates, earlier reconciliation where available, this
batch's object additions or enrichment, and remaining collection gaps.

| Country | Research rows |
|---|---:|
| Argentina | 735 |
| Bolivia | 44 |
| Brazil | 3,013 |
| Chile | 532 |
| Colombia | 556 |
| Ecuador | 164 |
| Guyana | 7 |
| Paraguay | 170 |
| Peru | 67 |
| Suriname | 14 |
| Uruguay | 486 |
| Venezuela | 10 |

Brazil's finite Ibermuseos country results were captured through the last page:
3,012 registry entries, plus a separate delivered MASP authority row. The other
Ibermuseos results contain 43 Bolivian, 485 Chilean, 555 Colombian, 148 Ecuadorian
and 66 Peruvian entries. Venezuela returned zero, so its Ministry of Culture
institution list is preserved instead. Native sources supplement Chile, Ecuador,
Guyana and Suriname. Argentina, Uruguay and Paraguay reuse the earlier combined
national/registry research with its identity and collection-review evidence.

The separate [French Guiana ledger](GF/institution-reconciliation-final.csv)
tracks two institutional leads under country France and territory French Guiana.
Moengo is correctly retained in Suriname. Neither this territorial selection nor
any registry establishes complete national museum or artwork coverage. Counts are
also saved in [directory-summary-final.json](directory-summary-final.json).
