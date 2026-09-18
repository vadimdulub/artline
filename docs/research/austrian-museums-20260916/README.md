# Austrian museum research — 16–17 September 2026

Completed 2026-09-16T21:02:54.031978+00:00. Both local and production databases were updated and checked. This is a source-backed expansion of selected Austrian museum holdings, not a complete inventory of every Austrian museum or of Austrian artists worldwide.

## Results

- **725 new artworks**, **95 new painter authorities**, **3 new museums**.
- **49 newly delivered images**, including **25 paintings by popular painters**; local files, both databases, Google Storage, image rights and anonymous public delivery checked.
- **5 institution-country gaps fixed**. Every selected holding institution now has independently supported Austrian geography.
- **95 artist cultural-affiliation rows added per database**, based on explicit source wording. Museum location was never used to infer an artist’s nationality.
- **639 new artworks have eligible known dates; 86 require date review**. Unknown years were left unknown.
- All new artwork and artist records remain **in review**. Holding evidence does not assert current display.
- No artwork deletion or merge, no schema change, no application deployment, no commit.

The initial Austrian catalogue had **62 paintings and 40 usable pictures** across 8 institution entries. This round brought it to **787 paintings and 89 pictures**. During final reporting, a separate existing image workflow attached **41 more KHM pictures**. The latest matching local/production snapshot therefore contains **787 paintings, 130 usable pictures and 657 missing pictures**. Those additional 41 are excluded from this round’s 49-image audit and delivery count.

The three new museum entries are **Neue Galerie Graz**, **Salzburg Museum**, and **Tiroler Landesmuseum Ferdinandeum**. Current official website URLs are recorded for all three.

## Current museum coverage

Snapshot: 2026-09-16T21:00:51Z. Counts are holdings in the current Artline catalogue, not estimates of each museum’s entire collection.

| Institution / collection entry | Paintings | With usable picture | Still missing picture |
| --- | ---: | ---: | ---: |
| Academy of Fine Arts Vienna | 128 | 4 | 124 |
| Albertina | 53 | 2 | 51 |
| Belvedere | 106 | 3 | 103 |
| Kunsthistorisches Museum, Gemäldegalerie | 251 | 77 | 174 |
| Lentos Art Museum | 17 | 1 | 16 |
| Leopold Museum | 105 | 12 | 93 |
| Paintings Gallery, Academy of Fine Arts Vienna | 1 | 0 | 1 |
| Salzburg Museum | 33 | 2 | 31 |
| Tyrolean State Museum | 28 | 1 | 27 |
| Universalmuseum Joanneum: Neue Galerie | 11 | 0 | 11 |
| Vienna Museum | 54 | 28 | 26 |
| **Total** | **787** | **130** | **657** |

There are 11 catalogue institution entries. The Academy university and its painting gallery already existed as separate entries; this research preserved that distinction. “11 entries” is not a claim of 11 distinct museums.

## What was researched

1. **1,045 unique Wikidata painting references** across 11 Austrian museum authorities. Current creator, holding institution, classification, dates and identifiers were checked. Expired holdings, conflicting versions, ambiguous creator mappings and out-of-scope dates were held back. Of 743 prepared candidates, 702 passed the reviewed main import plan: 685 new and 17 existing artworks.
2. **98 official Belvedere highlights**, using public catalogue pages and the published crawl delay. Fifty passed the final creator, accession, classification and date checks: 40 new artworks and 10 existing records enriched. Some overlap with the first plan’s existing records is intentional; do not sum enrichment counts as unique works.
3. **34 selected Wien Museum public object pages**. Exact creator roles, life dates, accession numbers, dates, medium and per-image rights were checked. Twenty-six records gained missing medium/dimensions. The internal API was not used.
4. Exact Wikimedia Commons file pages for independently sourced photographs, then **90 additional selected alternative-photo searches**. Twenty-eight Commons photographs and 21 Wien Museum images were accepted. Every accepted image was visually inspected against its identified artwork.

Copies, former attributions, sitters and works sharing a short title were not treated as interchangeable. For example, generic title matches such as “Beethoven” and “Self-portrait” were insufficient without creator and accession evidence. The official classification excluded the Klimt Old Burgtheater watercolour from this painting batch. Other painted forms require their own classification review rather than blanket inclusion as paintings.

## Source and image findings

- [Wien Museum collection terms](https://sammlung.wienmuseum.at/ueber-uns/): public object pages contain usable factual metadata and image-specific licences. Its internal API has separate restrictions; the research used public HTML. Only the exact image attached to a verified CC0 or CC BY statement was downloaded; photographer credits were preserved.
- [Belvedere highlights](https://sammlung.belvedere.at/highlights/images) and [open-content selection](https://sammlung.belvedere.at/opencontent/images): a museum’s open-content programme does not clear every photograph. Restricted primary images, including the checked primary photograph of *The Kiss*, were excluded. IIIF alone was not treated as permission. Factual title, creator, date, accession, medium and dimension fields were recorded; authored descriptions were not copied.
- [Wikidata data licensing](https://www.wikidata.org/wiki/Wikidata:Licensing): independent structured source facts and stable identifiers remain cited. Wikimedia file-page rights and original image provenance were checked separately. Unclear origin, restricted native photographs, mirrors and search-engine images were rejected.
- [Neue Galerie Graz](https://www.museum-joanneum.at/neue-galerie-graz), [Salzburg Museum](https://www.salzburgmuseum.at/) and [Tiroler Landesmuseen](https://www.tiroler-landesmuseen.at/): current institutional identity and location corroborated. A blocked programmatic request to the Tiroler site was respected; no workaround or hidden API was used.

The 49 approved images comprise 24 CC BY 4.0, 4 CC BY-SA 4.0, 12 CC BY-SA 3.0, 8 Public Domain Mark and 1 CC0 image. Exact source image URLs, full licence URLs, credit, retrieval and rights-check times are retained. Reproductions were proportionally resized and JPEG-compressed without cropping; required attribution and ShareAlike terms remain attached.

Institution country and artist nationality remain separate. Explicit cultural affiliations were stored as cultural affiliations, not citizenship. Historical labels such as Austro-Hungarian and Flemish were not automatically mapped to modern countries. Seventy-five researched artist authorities still need clearer country evidence. The single missing New Zealand country code was added from the [UN M49 country table](https://unstats.un.org/unsd/methodology/m49/overview) for an explicitly documented artist affiliation.

## Verification and safeguards

- Real catalogue queries used read-only sessions for audits; no fixture records or test databases were created.
- Full local PostgreSQL backup and completed Cloud SQL backup preceded mutations. Receipts are in `backups.json`; backup files and row preimages are outside the project under the documented Artline backup directory.
- Both databases contain all 725 planned new artwork IDs, source citations, reconciled creators, accepted holding evidence and Austrian institutional country. Semantic fields match after timestamp normalization to UTC.
- No conflicting source identifiers, normalized institution/accession collisions, or same-artist/title/date/museum candidates were found for these new imports against the catalogue. This is not an exhaustive historical duplicate census.
- All 49 approved source/file checks, local DB checks, production DB checks and Google Storage checks passed. Anonymous delivery verified 49 image byte payloads and 49 artwork API responses. No browser UI test is claimed.
- No exact delivered-image hashes were shared with the preceding popular-painter image round or another catalogue primary image in the image audit snapshot. Different photographs of a single object still require object-identity review.
- **65 synthetic tests passed** across Austrian research, popular-painter photo matching, Commons image matching and original-source checks.
- Source captures, receipts and approved-image evidence are retained locally and excluded from version control where appropriate. The final artifact audit scans this round’s evidence, relevant operational code and delivered JPEG metadata for credential patterns and private-reference paths. The scan checked 5,766 text files and all 49 delivered JPEGs: zero credential patterns, private-reference paths or embedded-image-metadata errors were found. No private discovery dataset was used.

## Deliverables and next research targets

- [Aggregate report](final-aggregate-report.json)
- [725 new artwork records with public-source provenance](new-artworks.jsonl)
- [49 approved-image records](approved-image-manifest.jsonl)
- [Local / production metadata and duplicate audit](final-metadata-audit.json)
- [Production image and Storage audit](production-image-audit-final.json)
- [Anonymous public delivery audit](public-all-images-final.json)
- [Final artifact scan](artifact-safety-scan-final.json)

The artwork export is a database snapshot using existing Artline fields, creator relations and public-source citations. `hasPicture` describes that snapshot; the 41 image references from the separate workflow are not part of this round’s image manifest. Records and images remain independently attributable without any private discovery reference.

The largest current picture gaps are KHM (174), Academy of Fine Arts (124, plus 1 in the separate gallery entry), Belvedere (103), and Leopold Museum (93). Belvedere native-image licensing is a substantial constraint; independently photographed, explicitly licensed reproductions remain useful.

Additional collections identified for a future selected-object pass, **not imported or claimed complete here**:

- [Alte Galerie Graz](https://www.museum-joanneum.at/alte-galerie/entdecken/sammlungen): medieval painted panels, frescoes and old masters; distinguish its holdings and loans from the separate Neue Galerie.
- [Residenzgalerie Salzburg](https://www.domquartier.at/residenzgalerie-sammlung-online/): a separate collection from Salzburg Museum.
- [Klosterneuburg Abbey art collection](https://www.stift-klosterneuburg.at/konvent/aufgabe/wissenschaft/sammlungen/kunstsammlung/): medieval panels and altarpieces among mixed collection types.
- [Upper Austrian cultural collections](https://www.ooekultur.at/): reconcile the present museum/operator authority before importing the held discovery record.

The operational scripts under `ops/` retain the reviewed plans, per-record receipts and restart checkpoints. `audit-austrian-catalogue.py` accepts a fresh output path for another read-only coverage snapshot; completed export/report artifacts intentionally fail if overwritten. Keep existing evidence and use a new run directory for subsequent research.
