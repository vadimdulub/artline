# Denmark and Switzerland museum coverage audit — 17 September 2026

Read-only catalogue audit and official-source research. No catalogue edits,
ingestion, publication, image downloads/uploads, commits or deployment in this pass.

## Findings

Local and production database count summaries match. The production website's
anonymous country-filtered directory returns **4 Danish museums and 2 Swiss
museums**. Name searches find Hirschsprung, Kunstmuseum Basel and Kunstmuseum Bern,
but adding the appropriate country filter removes each. These are missing
geography/venue associations, not missing institution identities.

| Audit measure | Denmark | Switzerland |
| --- | ---: | ---: |
| Active institution candidates identified | 7 | 26 |
| Candidates with stored country / country-filter venue | 4 | 2 |
| Candidates without stored country | 3 | 24 |
| Linked active artwork records, all types | 25,115 | 277 |
| Paintings classified date-eligible, through 1970 | 4,002 | 242 |
| Of those, with primary media attached | 2,969 | 229 |
| Of those, without primary media | 1,033 | 13 |
| Records needing creation-date review, all types | 808 | 33 |
| Published artwork records in this scope | 0 | 0 |

The institution candidate set includes libraries and archives as well as museums.
Countries absent from stored geography were **suggested for research by official
website country domains**, not asserted as catalogue facts. This is a bounded
coverage audit, not an exhaustive census of either country.

Artwork associations include current-institution pointers and nonsuperseded
holding assertions in review or accepted state. They are **not a new validation
of ownership, accepted holdings or current display**. Country totals deduplicate
artwork IDs across institutions. Media attachment / metadata-policy pass does not
certify image bytes, rights evidence, resolution or public delivery. Research
preview can expose review records; these are not published records.

### Denmark: concentration rather than absence

SMK accounts for **3,958 of 4,002 date-eligible paintings (98.9%)**. The other six
identified institutions together contribute only 44. The much larger all-type
total includes 12,687 drawings and 8,338 prints; it should not be presented as
25,115 paintings or evidence of broad museum coverage.

| Institution | Date-eligible paintings | With primary media | First action |
| --- | ---: | ---: | --- |
| SMK | 3,958 | 2,928 | Reconcile existing selected-image backlog; avoid duplicate imports |
| Skagens Museum | 18 | 18 | Expand selected collection coverage |
| Ordrupgaard | 14 | 11 | Expand selected French and Danish holdings |
| Nivaagaard Collection | 6 | 6 | Expand selected holdings |
| Thorvaldsen Museum | 5 | 5 | Verify geography and painting-specific collection sources |
| Hirschsprung Collection | 1 | 1 | Repair discovery and research highlighted works |
| Frederiksborg / Museum of National History | 0 | 0 | Verify geography; select documented portraits |

Previous Danish ingestion already added substantial SMK metadata and selected
images: see `../danish-painters-20260913/README.md`. Museum country must not be
confused with artist nationality; French works in Denmark belong in this audit.

### Switzerland: both discovery and substantial collection gaps

Kunsthaus Zürich has 147 date-eligible paintings and Beyeler has 13. Other
institutions are thin and mostly lack stored geography:

| Existing institution | Date-eligible paintings | With primary media |
| --- | ---: | ---: |
| Kunstmuseum Basel | 29 | 29 |
| MCBA, Lausanne | 10 | 10 |
| Kunstmuseum Bern | 6 | 6 |
| Kunstmuseum Solothurn | 5 | 2 |
| Bündner Kunstmuseum | 2 | 2 |
| Museum Langmatt | 2 | 2 |
| MAH, Geneva | 1 | 0 |
| Aargauer Kunsthaus | 1 | 1 |
| Kunst Museum Winterthur — Reinhart am Stadtgarten | 1 | 1 |
| Villa Flora | 1 | 1 |
| Kunstmuseum St. Gallen | 1 | 1 |
| Kunstmuseum Luzern | 0 | 0 |

MAH Geneva already exists as `spain-research-museum-q679075`: that legacy slug is
not country evidence and must not cause a second museum record. Likewise,
**Reinhart am Stadtgarten is not the Sammlung Oskar Reinhart “Am Römerholz.”**
Winterthur venues and parent institutions need explicit reconciliation.

## Prioritized official-source research queue

Sources checked 17 September 2026. “Not found” means no match in the active
institution register by the recorded name/slug/website aliases, not proof that
every possible legacy identity or unlocated artwork has been excluded.

| Priority | Museum / route | Register finding | Selection rationale and constraint |
| --- | --- | --- | --- |
| 1 | [Hirschsprung collection](https://www.hirschsprung.dk/en/collection/art) | Existing, missing geography | Explicit museum highlights; Golden Age, Skagen and women artists |
| 1 | [Kunstmuseum Basel highlights](https://kunstmuseumbasel.ch/de/sammlung/schwerpunkte) | Existing, missing geography | Old Masters and modernism; preserve foundation/deposit credits |
| 1 | [Kunstmuseum Bern catalogue](https://www.kunstmuseumbern.ch/en/collection-research) | Existing, missing geography | Swiss painting and international modernism; provenance and associated foundations require object-level checks |
| 1 | [MCBA Lausanne collection](https://www.mcba.ch/en/collection/) | Existing, missing geography | Searchable selected works with dates; mixed media and post-1970 works require filtering |
| 1 | [Ny Carlsberg Glyptotek](https://glyptoteket.com/explore/art) | Not found | Danish Golden Age and French painting; archaeology/sculpture totals are not painting totals |
| 1 | [Sammlung Oskar Reinhart “Am Römerholz”](https://www.roemerholz.ch/en/the-collection) | Not found; different Reinhart institution exists | Old Masters and French Impressionism; official page links to federal online collection |
| 1 | [Zentrum Paul Klee](https://www.zpk.org/en/collection) | Not found | Klee paintings and works on paper; also documented Jawlensky/Kandinsky holdings; do not flatten media types |
| 2 | [ARoS](https://www.aros.dk/permanente-vaerker/aros-samling/) | Not found | Danish Golden Age through early modernism and CoBrA; select creation dates, not contemporary display dates |
| 2 | [Kunsten Aalborg online collection](https://collection.kunsten.dk/) | Not found | Danish/international modernism; only eligible pre-1971 subset |
| 2 | [Louisiana collection](https://louisiana.dk/en/museum/collection/) | Not found | Select eligible works from its predominantly postwar collection, not the whole contemporary collection |
| 2 | [Fuglsang Kunstmuseum](https://fuglsangkunstmuseum.dk/en/udstilling/dansk-kunst-fra-1780-til-idag/) | Not found | Golden Age, landscapes and early modernism; distinguish own works from deposits |
| 2 | [Faaborg Museum](https://www.faaborgmuseum.dk/udstillinger/) | Not found | Funen painters; select object-level evidence before import |
| 2 | [MASI Lugano online collection](https://collezione.masilugano.ch/it/) | Not found | Canton/city collections plus deposits; retain actual collection ownership and museum connection |

Existing Ordrupgaard, Nivaagaard, Skagen, Langmatt, Aargau, Solothurn, St. Gallen,
Chur and Geneva merit expansion too. Subsequent regional discovery should check
Ribe, Randers, Sorø, Skovgaard, Willumsens and Bornholm in Denmark, and Jenisch,
Gianadda, Neuchâtel, Thun and Rietberg in Switzerland. These later targets are
**a research backlog, not verified import candidates**.

## Concrete artwork leads — not yet approved new records

These are source-selected leads, not claims that the works are absent everywhere
in Artline. Next pass must reconcile inventory/source IDs and artist-scoped
existing records, then preserve exact ownership and attribution wording.

| Source | Lead and source date | Review note |
| --- | --- | --- |
| [Hirschsprung women artists](https://www.hirschsprung.dk/en/collection/art/women-artists) | Anna Ancher, *The Maid in the Kitchen*, 1883–1886 | Museum-designated highlight; preserve the range |
| Same | Bertha Wegmann, portrait of Jeanna Bauck, 1885 | Object inventory/title reconciliation still needed |
| [Basel Old Masters](https://kunstmuseumbasel.ch/en/collection/alte-meister) | Hans Holbein the Younger, *The Dead Christ in the Tomb*, 1521–1522 | Do not confuse with the existing Wyrsch *Dead Body of Christ*, 1779 |
| [Basel highlights](https://kunstmuseumbasel.ch/de/sammlung/schwerpunkte) | Catharina van Hemessen, self-portrait at the easel, 1548 | Women-artist priority; reconcile official object record |
| Same | Paul Gauguin, *Ta matete*, 1892; Paul Klee, *Villa R*, 1919 | Separate objects; no title-only merges |
| [Bern collection](https://www.kunstmuseumbern.ch/en/collection-research) | August Macke, *Gartenrestaurant*, 1912; Meret Oppenheim, *Verzauberung*, 1962 | Metadata eligibility does not clear reproduction rights |
| [MCBA collection](https://www.mcba.ch/en/collection/) | François Bocion, open-air portrait of the Chatelain of Montagny and children, 1854; Marius Borgeaud, *Intérieur aux deux verres*, 1923 | Resolve individual object pages and inventory numbers |
| [Louisiana historical collection presentation](https://louisiana.dk/en/exhibition/louisianas-time/) | Francis Bacon, *Three Studies of George Dyer*, 1969 | Historic display page, not a current on-view claim; image credit explicitly restricted |

Basel's Paula Modersohn-Becker *Self-Portrait as a Half-Length Nude with Amber
Necklace II* (1906) already exists in the audited institution-linked set; reuse
its identity. Research should strengthen evidence rather than duplicate it.

Russian/Greek/Byzantine priorities remain in scope regardless of museum country.
Zentrum Paul Klee documents Jawlensky/Kandinsky holdings, and
[Louisiana's focus areas](https://louisiana.dk/en/museum/collection/focus/) include
early Russian Constructivist works on paper. These are collection-level leads,
not permission to infer individual works, dates or attributions. Anonymous and
workshop-attributed icons need the explicit supported workflow before importing;
do not silently discard them or force named creators.

## Image workflow and rights

1. Resolve selected eligible objects first. Preserve missing dates and ambiguous
   ranges in review; creation ranges crossing 1970 are not automatically eligible.
2. Reuse existing source research and attached assets where identities match.
   Denmark's 1,033 missing eligible-painting media attachments include 1,030 at
   SMK and 3 at Ordrupgaard. This is a prioritized backlog, not a download mandate.
3. For SMK, use the existing API/source evidence workflow and verify each chosen
   object's public-domain status. Do not ingest its full API or bulk image archive.
4. [Hirschsprung's photo policy](https://www.hirschsprung.dk/en/the-museum/photos)
   links selected public high-resolution reproductions but separately specifies
   restrictive terms for ordered photographs. Check the actual file's license;
   do not treat the entire museum website as openly reusable.
5. [Kunstmuseum Bern's image-ordering page](https://www.kunstmuseumbern.ch/en/node/1225)
   provides a request route, not a blanket open license. Basel's object credits
   likewise distinguish photographers and rights holders. Keep rights-unresolved
   metadata records without an image instead of uploading an unlicensed file.
6. Clear artwork and reproduction rights per file, record source/credit/license,
   then use the approved selected-image upload/verification workflow. No automatic
   publication or current-display claims follow from attaching media.

## Proposed implementation order (requires a change request)

1. Reconcile the 27 geography candidates against authoritative museum addresses;
   repair verified institution/place/venue associations with an explicit dry-run
   diff. Start with the four source-confirmed priorities: Hirschsprung, Basel,
   Bern and MCBA. Do not apply countries solely from website domains.
2. Add missing institution identities only after duplicate/parent/venue checks.
3. Prepare bounded, museum-balanced batches of selected pre-1971 works. Retain
   unresolved named creators and supplied provenance in review; do not invent
   dates, biographies, object types or accepted holdings.
4. Upload only selected rights-cleared reproductions. Check local/production
   parity, country discovery and bounded artwork/image delivery before handoff.
5. Keep validation/publication separate. Geography repair is not approval of
   every related artwork, holding assertion or image.

## Evidence and reproducibility

- `audit.py`: PostgreSQL read-only, repeatable-read transactions; institution
  candidates resolved before artwork enrichment. No fixtures or test databases.
- `local-summary.json`, `cloud-summary.json`: matching count snapshots at
  approximately 19:51 UTC on 17 September 2026, with read-only mode recorded.
- `*-institution-register.json`, `*-institutions.json`, `*-scoped-artworks.json`:
  source IDs, scoped evidence and per-institution counts for reconciliation.
- `check-discovery.mjs` / `discovery-check.json`: eight bounded anonymous
  production GET probes, all HTTP 200; country/name filter results and active
  institution alias checks. No pagination beyond the bounded pages was needed.

Audit output files use exclusive creation to preserve evidence. Do not rerun in
place over existing snapshots. These checks establish current coverage and
discovery behavior, not 10-million-row performance or exhaustive national totals.
