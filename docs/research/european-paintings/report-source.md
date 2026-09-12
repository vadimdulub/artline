# European painting collections: a practical expansion for Artline

Audience: Artline owner and implementation team. Research checked 9 September 2026.
Scope: Bosch, El Greco, Claude Monet and Camille Pissarro; European museums including
the UK; paintings created by 1970. These are reviewed research candidates, not
automatically imported, published, or rights-cleared assets.

## Executive answer

There is substantially more useful European coverage than the current small Artline
museum catalogue represents. This investigation assembled 59 painting records at
26 institutions in 12 countries: 15 museum-listed Bosch records, 11 El Greco records,
22 Monet records and 11 Pissarro records. Three records carry explicit disputed,
possible or attributed authorship, so these are not counts of undisputed autograph
masterpieces. Counts are calculated from the accompanying inventory, whose official
object links support each inclusion.

The next expansion should be source-led and selective. Start with exact object
identities and museum connections; add images only after checking the individual
digital asset. MSK Ghent, Städel, Rijksmuseum and selected Nationalmuseum photographs
are promising image candidates. The National Gallery and Louvre are strong metadata
candidates, but their image terms need separate handling. These priorities are our
inference from verified access and rights evidence, not completed integrations.
[MSK object and IIIF](https://www.mskgent.be/en/collection/1908-h),
[Städel image policy](https://www.staedelmuseum.de/de/bildnachweise),
[Rijksmuseum data services](https://data.rijksmuseum.nl/docs/),
[Nationalmuseum reproduction policy](https://www.nationalmuseum.se/en/explore-art-and-design/images/rights-and-reproductions),
[National Gallery licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences),
[Louvre JSON documentation](https://collections.louvre.fr/en/page/documentationJSON).

This is a representative, actionable seed set, not a complete European holdings
census. The appendix carries every candidate, native title, recorded date,
accession or explicit identifier gap, and official link. No permission requests,
account registrations, image downloads, database imports or publication occurred.

## What the research changes

Bosch coverage can extend beyond the Prado to Lisbon, Ghent, Berlin, Paris,
Rotterdam, London, Madrid's Lázaro Galdiano and two Vienna collections. El Greco
also has documented holdings in London, Paris, Toledo, Edinburgh, Madrid and
Modena. Monet and Pissarro extend the map through French regional museums,
Cardiff, Edinburgh, Frankfurt, Amsterdam, Riehen, Charlottenlund, Stockholm and
Vienna. The institution-grouped appendix supplies primary evidence for each place;
it does not infer a current exhibition or that a visitor can see every listed work.

Geographic gaps remain: exact object evidence was not secured for several Norway,
Prague, Budapest, Lille, Lyon and Bowes leads within this pass. Lack of a verified
record here is not evidence that a museum has no relevant paintings. The scope is
four painters; it does not claim research coverage of every iconic painter.

## Integration priorities

1. MSK Ghent: two exact Bosch object records, Public Domain image labels and
   documented object-level IIIF manifests. One authorship is disputed, so image
   availability must not override attribution review.
   [Saint Jerome](https://www.mskgent.be/en/collection/1908-h),
   [Christ Carrying the Cross](https://www.mskgent.be/en/collection/1902-h).
2. Rijksmuseum and Städel: exact Monet identifiers and explicit per-image Public
   Domain evidence. Rijksmuseum documents search, incremental/bulk data and IIIF;
   Städel documents CC0 metadata through OAI DC/LIDO after registration. No
   registration has been submitted.
   [Rijksmuseum services](https://data.rijksmuseum.nl/docs/),
   [Städel OAI](https://sammlung.staedelmuseum.de/en/oai),
   [Städel image rights](https://www.staedelmuseum.de/de/bildnachweise).
3. Nationalmuseum: the Monet object has multiple photographs with different rights.
   A selected Public Domain photograph is promising; do not assign one licence to
   all its images. A public integration API was not verified.
   [View over the Sea](https://collection.nationalmuseum.se/en/collection/item/19182/).
4. National Gallery: use the documented Elasticsearch/PID data services for exact
   accessions. Structured data are CC0, prose CC BY 4.0, and images CC BY-NC-ND 4.0.
   Artline's existing accepted-image policy should therefore keep those images
   link-only unless a separate approved licence is established. IIIF remains
   described as under development, not a verified production dependency.
   [API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api),
   [Licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences),
   [Collection images](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-images).
5. Louvre and other catalogue-led museums: official JSON or curated object pages
   can support selective metadata intake. Louvre text reuse and photograph reuse
   are separate. Many other collections have useful catalogues but no public
   automated interface verified in this investigation. Do not substitute scraping
   at scale for an agreed data route.
   [Louvre JSON](https://collections.louvre.fr/en/page/documentationJSON),
   [Louvre terms, updated 19 March 2026](https://collections.louvre.fr/page/cgu).

## Exceptions that must survive ingestion

Authorship: Ghent's Christ Carrying the Cross is explicitly disputed on the museum's
own page. London's Saint Jerome as Cardinal is only possibly by El Greco; the
Italian national catalogue qualifies the Modena Triptych as attributed. Keep these
as separate attribution tiers. Exclude the Thyssen Last Supper from autograph
El Greco counts: its current artist is an anonymous Venetian painter. The Boijmans
Wedding at Cana must not be imported as autograph Bosch from an old attribution.
[Ghent record](https://www.mskgent.be/en/collection/1902-h),
[London record](https://www.nationalgallery.org.uk/paintings/possibly-by-el-greco-saint-jerome-as-cardinal),
[Modena national record](https://catalogo.beniculturali.it/detail/HistoricOrArtisticProperty/0800675920),
[Thyssen current attribution](https://www.museothyssen.org/en/collection/artists/anonymous-venetian-artist-active-ca-1570/last-supper),
[Boijmans Bosch catalogue](https://www.boijmans.nl/en/collection/artists/3077/jheronimus-bosch).

Identity and dates: Orsay RF 2735 / LUX 367 is one Pissarro under several titles,
including Côte Saint-Denis à Pontoise and Les Toits rouges. Orangerie's Les Nuages
is one composition assembled from three panels. Preserve ranges, circa, century
dates and signed-date qualifiers. Rouen's cathedral label says 1894 despite a
discussion of painting in 1892-93; Thyssen's Thaw is dated 1880 despite its 1881
signature. Do not resolve those differences by inventing one definitive year.
[Orsay identity](https://www.musee-orsay.fr/fr/oeuvres/cote-saint-denis-pontoise-379),
[Les Nuages](https://www.musee-orangerie.fr/fr/oeuvres/les-nuages-196302),
[Rouen cathedral](https://mbarouen.fr/fr/oeuvres/la-cathedrale-de-rouen-le-portail-et-la-tour-d-albane-temps-gris),
[The Thaw](https://www.museothyssen.org/en/collection/artists/monet-claude/thaw-vetheuil).

Custody and display: the Prado Garden of Earthly Delights is on permanent loan from
Patrimonio Nacional; two selected Boijmans works have foundation-loan credits.
Carmen Thyssen Collection works must remain distinct from national museum ownership.
Orsay's French and English Pissarro pages conflict on display. Keep this conflict
unresolved rather than choosing the more convenient language version. A building
name or historical exhibition reference is not current display confirmation.
[Prado record](https://www.museodelprado.es/en/the-collection/art-work/the-garden-of-earthly-delights-triptych/02388242-6d6a-4e9e-a992-e1311eab3609),
[Boijmans loan credit](https://www.boijmans.nl/en/collection/artworks/101305/the-flood),
[Carmen collection credit](https://www.museothyssen.org/en/collection/artists/pissarro-camille/route-versailles-louveciennes-winter-sun-and-snow),
[Orsay French](https://www.musee-orsay.fr/fr/oeuvres/cote-saint-denis-pontoise-379),
[Orsay English](https://www.musee-orsay.fr/en/artworks/les-toits-rouges-coin-de-village-effet-dhiver-379).

Rights and data quality: Belvedere's current Monet photograph notices are more
restrictive than its older Open Content publicity. Treat reuse as unresolved until
the exact file's licence is reconciled. Four MuMa records lack exposed accessions;
their official URLs support candidates, not invented accession numbers. Cardiff's
Pissarro page contains conflicting artist/classification fields; quarantine those
fields rather than propagating them into painter or genre filters.
[Current Belvedere record](https://sammlung.belvedere.at/objects/2683/eine-allee-in-monets-garten-in-giverny),
[Older Open Content statement](https://www.belvedere.at/sites/default/files/2023-12/Pressemappe_JahresPK_2024_EN.pdf),
[MuMa Pissarro](https://www.muma-lehavre.fr/fr/collections/oeuvres-commentees/impressionnisme/pissarro-soleil-levant-eragny),
[Cardiff Pissarro](https://museum.wales/collections/online/object/192e3ef3-dd3e-3894-a7ec-1496222df455/Pont-Neuf-Snow-Effect-2nd-series/).

## Implications for Artline's filters and backend

Implemented in this change: searchable, multi-select painter controls; multiple
movement, country, region and work-type choices on the timeline; multiple painters
and movements in museum discovery; multiple painters, movements, venues and work
types in collection detail. Values use OR within a category and AND across categories.
Museum list filters mean a collection has a matching artwork, not that it contains
every selected painter. Museum cards retain clearly labelled total catalogue counts.

Go validates and bounds selections to 32 values per category, canonicalizes lists,
and passes parameterized arrays to SQL. Painter search returns at most 30 matches
plus at most 32 selected identities; it never sends all 20,000 painters to the
browser. Museum pagination remains keyset-based and bound to the selected filters.
Timeline painter filters use painter=, distinct from the artist= profile drawer.
Old one-value bookmarks remain valid; the popular-painters default is retained.

Data limitations are separate from filter correctness. The current local Pissarro
record has no country or movement classification, so adding those filters can
exclude him. Subject genres such as portrait/landscape are not modeled; movement
and work type have not been misleadingly renamed to genre. Classification repair
needs source-backed editorial work, not frontend guesswork.

Recommended future backend work, not implemented here: preserve separate source
identities, artwork identities, qualified creator assertions, owner/custodian
relationships, composition/component links, and per-image rights evidence. Build
source adapters as bounded, resumable, idempotent ingestion jobs. Use stable
(source, source-object-ID) keys before title matching; reconcile conflicting dates
and attribution claims in review. Keep normal browsing independent of museum APIs.

At 10-million-artwork scale, the global museum discovery/facet CTE remains a
scaling risk: bounded response sizes do not prove bounded database work. A reviewed
museum/artist/movement summary projection with explicit invalidation and visibility
semantics is a likely next step, followed by production-like load tests. The existing
100,000-row temporary plan fixture validates scoped index access, not full-scale
throughput. No 10-million-row performance claim is made.

## Evidence limits and stopping decision

Research used official object records, national collection catalogues, documented
data interfaces and institutional reuse policies. Two independent painter lanes
were merged, followed by a targeted Nordic/Central-European gap pass and a
coordinator check of important attribution, API and rights claims. Some Prado,
KHM and Italian records were available only through official indexed text or timed
out; those access limitations are recorded in the inventory. Publication dates not
observed remain unknown; access date is not substituted for publication date.

Research stopped at a geographically broader, actionable set with explicit gaps.
Further broad searches were producing weaker, inaccessible, historical-loan or
non-painting leads. A subsequent approved import should begin with a small reviewed
batch and exact-asset rights audit, then expand museum by museum. This report is
completed for that bounded scope, not an assertion of exhaustive coverage.

## Candidate catalogue

The rendered appendix is generated from inventory.json. It groups all 59 candidates
under their 26 institutions and includes official hyperlinks, source-date/access
notes, identifier gaps and applicable cautions. Review all defaults alongside each
record; none is automatically approved for download or publication.
