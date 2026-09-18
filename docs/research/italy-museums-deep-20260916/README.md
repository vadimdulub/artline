# Italy: deep catalogue and artwork research

Research date: 16 September 2026. Scope: Italy only, including works held in Italy regardless of creator origin, and selected Italy-associated creators held abroad. This is a research delivery; database writes, imports, publication actions and image downloads: **zero**.

The strongest finding is a combination of **thin museum coverage, incomplete institution geography and a large image gap in existing records**. The national footprint is broader than the object research: sources were investigated across all 20 regions, while detailed primary object records concentrate on ten Italian regions plus three works in London. No national completeness percentage is claimed.

## Evidence and deliverables

- [Primary artwork review](primary-artwork-review.md): **99** selected source records with dates, creators, inventories, local-match outcomes and holds.
- [First 40 editorial reviews](priority-review-queue.md): concrete next objects, including missing-profile leads, existing objects needing enrichment, women artists, and Russian icons.
- [20-region source map](regional-museum-map.md): successful routes, blocked/failed routes and remaining regional work.
- [Full identity review](candidate-identity-review.json): **853** research candidates: 754 selected from an existing Lombardia snapshot and 99 current primary-source selections. These are not 853 new or eligible artworks.
- [Source ledger](source-ledger.json), [quality checks](quality-check.json), and [SHA-256 manifest](manifest.json): retrieval evidence, access limitations and reproducible checks.

The read-only database audit was taken at **2026-09-16 23:13:39.055410+03:00**; it saw 13,201 active artist records and 262,723 active artwork records across the catalogue. Later read-only identity checks have their own timestamp in [candidate-identity-summary.json](candidate-identity-summary.json). Concurrent work may change the live database after either snapshot.

## 1. What the local catalogue actually contains

| Measure | Audit result | Interpretation |
| --- | ---: | --- |
| Institutions with an IT place or IT venue | 31 | Includes review holdings; not all Italian museum identities |
| Active works linked to those institutions | 2,509 | All media and dates, deduplicated within country scope |
| Paintings among those works | 734 | Does not count drawings, prints or frescoes as paintings |
| Paintings with a stored end year ≤1970 | 721 | Numeric coverage, not newly validated eligibility |
| Such paintings with primary media | 47 (6.5%) | A media pointer, not a new image quality/rights certification |
| Such paintings without primary media | **674** | Immediate enrichment opportunity in existing records |
| Artist records associated with IT | 694 | Cultural affiliation and/or birth; not a nationality census |
| Associated artist records without any works | 26 | Requires occupation/identity review before calling them painter gaps |
| Associated artist records without dated paintings | 268 | Some have drawings, prints, frescoes or undated paintings |

The Italian holdings mix is 1,736 drawings, 734 paintings, 22 prints and 17 frescoes. Consequently, a large total artwork count can conceal weak painting coverage. All 2,509 scoped works are in review.

For Italy-associated artists **anywhere in the world**, the audit found 12,218 works, including 2,591 paintings; 2,414 paintings have a stored end year through 1970, with 1,196 primary-media pointers and 1,218 missing them. Do not add this total to the Italy-holdings total: they overlap and answer different questions.

There are 650 cultural-affiliation associations and 207 birth associations to Italy among the 694 records; 44 records are birth-only for Italy. Birth in Italy cannot independently establish Italian artistic identity. The 26 zero-work profiles also include Lisa del Giocondo, Margarita Luti, Donatello and Giovanni Pietro Bellori, so “26 missing Italian painters” would be misleading. Raw profiles and relationship types are preserved in [artist-coverage.json](artist-coverage.json).

| Local institution identity | All linked active works | Paintings dated through 1970 | With primary media | Geographic issue |
| --- | --- | --- | --- | --- |
| Uffizi Galleries | 35 | 29 | 15 | Main place missing; IT venue exists |
| Palazzo Pitti — Galleria Palatina | 1 | 1 | — | IT mapped |
| Palazzo Pitti | 2 | not in geographic count | not audited here | No country or IT venue |
| Pinacoteca di Brera | 13 | 13 | 3 | IT mapped |
| Accademia di Belle Arti di Brera | 609 | 37 | — | IT mapped |
| Galleria Borghese | 23 | 20 | 15 | IT mapped |
| Accademia Carrara | 117 | 116 | — | IT mapped |
| Pinacoteca Ambrosiana | 121 | 121 | — | IT mapped |
| Museo Poldi Pezzoli | 44 | 10 | 2 | IT mapped |
| Gallerie dell’Accademia di Venezia | 22 | 18 | 12 | IT mapped |
| Galleria Estense | 1 | 1 | — | IT mapped |
| Galleria Nazionale d'Arte Antica | 3 | not in geographic count | not audited here | No country or IT venue |
| Galleria Sabauda | 1 | not in geographic count | not audited here | No country or IT venue |
| Turin Civic Gallery of Modern and Contemporary Art | 3 | not in geographic count | not audited here | No country or IT venue |

Counts above belong to separate local identities. **Accademia di Belle Arti di Brera is not Pinacoteca di Brera.** Palazzo Pitti, its Palatina gallery and the wider Uffizi organization also need distinct institutional and venue relationships; their counts are not safely interchangeable.

The geography review contains **25 countryless institution-place records**: 24 discovered through Italian website domains and Barberini Corsini through a verified museum route. Uffizi and Scrovegni already have Italian venues and are included in the 31-institution audit. The other 23 need location reconciliation; do not treat all 25 as invisible to the country audit. Source-backed review candidates include Sabauda, GAM Torino, Ca’ Pesaro, Ca’ Rezzonico, Palazzo Pitti, Ricci Oddi, the Ligustica museum, Genoa’s Strada Nuova museums and Abruzzo. See [the geography queue](italian-institution-geography-review.json).

No mapped institution identity was found in the local inventory review for several major routes, including Capodimonte, Siena, the national galleries of Umbria and Marche, Bologna’s national picture gallery, Palazzo Abatellis and Palazzo Lanfranchi. This is an identity/coverage finding, not proof that no related work exists under another title, creator or free-text location. Vatican City remains a separate geography; its zero geocoded institutions is not evidence that Vatican-related artworks are absent everywhere.

## 2. The most useful object-level findings

**Empty profiles with concrete museum evidence.** Ambrogio Lorenzetti has zero linked works locally, while Siena supplies [Annunciation (1344), inventory 88](https://www.pinacotecanazionalesiena.it/portfolio/dal-palazzo-pubblico-di-siena/) and [the Carmine painted cross, inventory 598](https://www.pinacotecanazionalesiena.it/ambrogio-lorenzetti-croce-dipinta/). Baldovinetti also has zero: the Uffizi records [Annunciation, inventory 483](https://www.uffizi.it/opere/annunciazione-baldovinetti) and [the Cafaggiolo altarpiece, inventory 487](https://www.uffizi.it/opere/madonna-col-bambino-e-santi-baldovinetti). Carlo Levi has zero; Matera documents [Lucania ’61 (1961)](https://www.museonazionaledimatera.it/collezione/lucania-61/), six assembled panels forming one catalogue work. These are strong research priorities, with existing-object deduplication still required.

Plautilla Nelli has zero linked works. [Santa Maria Novella’s institutional account](https://www.smn.it/it/magazine/l-ultima-cena-di-plautilla-nelli-a-santa-maria-novella/) supports her Last Supper and the museum connection but supplies no creation date. Keep the candidate and its provenance with that field unknown; the 2019 restoration date is not an artwork creation year. Pisanello also has zero: the National Gallery’s [NG1436](https://www.nationalgallery.org.uk/paintings/pisanello-the-vision-of-saint-eustace) and [NG776](https://www.nationalgallery.org.uk/paintings/pisanello-the-virgin-and-child-with-saints) are useful Italian-art coverage outside Italy. Their abbreviated source dates remain held for explicit interpretation.

**Brera’s missing-highlight leads.** Among eight selected paintings from the official highlight route, existing source/inventory checks account for Mantegna’s dead Christ, Raphael’s Marriage, Hayez’s Kiss, Bellini’s Pietà and Caravaggio’s Emmaus. The remaining source-backed leads are [the Bellini brothers’ Saint Mark sermon, inventory 160](https://pinacotecabrera.org/collezioni/collezione-on-line/predica-di-san-marco-in-una-piazza-di-alessandria-degitto/), [Piero’s Montefeltro altarpiece, inventory 180](https://pinacotecabrera.org/collezioni/collezione-on-line/madonna-col-bambino-e-santi-angeli-e-federico-da-montefeltro-pala-di-san-bernardino/), and [Tintoretto’s Finding of Saint Mark, inventory 5959](https://pinacotecabrera.org/collezioni/collezione-on-line/il-ritrovamento-del-corpo-di-san-marco/). Their absence from tested identities is a review lead, not certified global uniqueness.

**Florence needs several distinct collection passes.** Uffizi leads include [Tondo Doni, inventory 1456](https://www.uffizi.it/opere/sacra-famiglia-detta-tondo-doni), [Simone Martini and Lippo Memmi’s Annunciation, inventories 451–453](https://www.uffizi.it/opere/annunciazione-e-i-santi-ansano-e-massima), [Leonardo’s Adoration, inventory 1594](https://www.uffizi.it/opere/leonardo-adorazione-dei-magi), and [Giotto’s Ognissanti Madonna, inventory 8344](https://www.uffizi.it/opere/madonna-col-bambino-in-trono-angeli-e-santi-maesta-di-ognissanti). Distinguish the last from Cimabue’s separate inventory 8343. Pitti adds Palatina works, eleven selected modern-gallery works, and six Russian icons. Modern candidates include Fattori, Abbati, Ussi, Bezzuoli, Elisabeth Chaplin, Chini, Conti and Viani. Creation date determines the cutoff even when an artist lived beyond 1970.

**Central and southern Italy require institutional breadth.** The reviewed sources document Piero’s [Flagellation in Urbino, DE 229](https://gndm.it/opere/flagellazione/) and [Sant’Antonio polyptych in Perugia, inventories 111–114](https://gallerianazionaledellumbria.it/opere-archivio/63106-polittico-di-santantonio/); Lavinia Fontana’s [Gozzadini family in Bologna, inventory 1161](https://pinacotecabologna.cultura.gov.it/en/opere-darte/la-famiglia-gozzadini-998); Antonello’s [Annunziata at Palazzo Abatellis, dated approximately 1474–1477 by the regional source](https://www2.regione.sicilia.it/beniculturali/dirbenicult/info/beniinamovibili/PaAnnunziata.html); and Carlo Levi at Lanfranchi. Capodimonte’s sources support [Caravaggio’s Flagellation](https://capodimonte.cultura.gov.it/mostra/capodimonte-doppio-caravaggio-lecce-homo-e-la-flagellazione-di-cristo/), [Parmigianino’s Antea](https://capodimonte.cultura.gov.it/domenica-7-giugno-2026-ad-ingresso-gratuito/) and [Titian’s Danae](https://capodimonte.cultura.gov.it/domenica-7-giugno-2026-ad-ingresso-gratuito/), but the selected context pages lack individual inventories. Do not treat a visiting Ecce Homo as a permanent Capodimonte holding. The Flagellation’s FEC ownership is distinct from its museum custody.

**Women and icons remain explicit priorities.** The selections include Artemisia, Sofonisba, Lavinia Fontana, Plautilla Nelli, Vigée Le Brun and Elisabeth Chaplin; artworks held in Italy are in scope regardless of creator origin. An inventory check identifies Uffizi Artemisia’s Judith as an existing record despite its English local title. Brera Sofonisba’s Pietà is also already present. Neither should be added as a duplicate. Russian-icon research preserves five anonymous/workshop labels and [Vasilij Grjaznov’s named 1728 icon](https://www.uffizi.it/opere/madre-di-dio-tichvin). The [Hellenic Institute museum](https://istitutoellenico.org/it/elementor-2432/) and [Bari’s collection route](https://www.pinacotecabari.it/index.php/collezioni) provide further Greek, Byzantine and post-Byzantine research paths; no anonymous icon was forced into a named-creator import.

## 3. Lombardia: useful scale without a new bulk harvest

The already-preserved 10 September regional snapshot contains **54,488 notices of all selected media**, including **15,643 painting notices**, 12,475 with a populated named-creator field, and 12,612 with numeric date bounds ending by 1970. There are 1,429 painting notices without a museum label. The snapshot’s 90,929,096 bytes were verified against SHA-256 `0726630aee0ca6b9f81ccab962999f8305a9638dbca833d1ac534254e8f49e04`; no copy of its images was downloaded.

Selection retained at most two notices per creator label per museum and twelve per museum: **754 candidates across 98 museum labels**. Those labels are not 98 reconciled institution identities. This cap creates a tractable review sample; it is neither exhaustive nor a curated masterpiece ranking. Anonymous/workshop and qualified attribution labels remain explicit holds. Numeric bounds do not override “before/after/circa” qualifiers.

A populated creator-name field is not proof of a named person: the snapshot puts labels such as anonymous, unknown and regional painter in that field. A conservative label check leaves 12,138 painting notices with at least one apparently named creator label, still requiring authority review. Mixed creator strings retain their components and remain held for attribution-role review. The raw source creator field is preserved alongside the classification.

Large source pools include Carrara (1,629 painting notices), Ambrosiana (1,502), Pavia (730), Tadini (511), Palazzo Morando (295), Como (282) and the Castello Sforzesco art collections (282). These are source notice counts, not verified distinct paintings or denominators for local completeness percentages. The first eight bounded live-page checks encountered access holds; their preserved snapshot evidence must not be relabelled as freshly revalidated object pages. Details are in [lombardia-summary.json](lombardia-summary.json) and [the institutional inventory](lombardia-institution-inventory.json).

## 4. Identity results and unresolved source problems

| Result across all 853 research candidates | Count | Meaning |
| --- | ---: | --- |
| Exact stored source identity | 94 | Existing artwork records; review/enrich rather than add |
| Museum-scoped inventory match | 10 | Probable existing object; human comparison still required |
| Normalized-title collision | 121 | Could be a copy, print, different version or another creator |
| No exact source/title match in tested scope | 628 | Candidates for further deduplication, not confirmed missing objects |

Within the 99 primary selections: 8 source matches, 10 inventory matches, 18 title-collision reviews and 63 unmatched in the tested identities. Exact source comparisons include archived objects so research does not accidentally recreate withdrawn records. Local title checks use Italy-associated works and the bounded Italian-institution scope; this is not a multilingual physical-object comparison of every global artwork. Parent/component duplicates and overlap between the primary sample and the regional sample still need review.

The primary date classification is 75 records whose source date fields parse through 1970, 12 with no extracted creation date, 8 abbreviated ranges, 2 open-bound dates and 1 period-only date. One object, [Warhol’s Vesuvio (1985)](https://capodimonte.cultura.gov.it/domenica-7-giugno-2026-ad-ingresso-gratuito/), is deliberately held out by the cutoff. The 75 numerically dated records still need editorial validation, identity and museum review; this is not an eligibility approval.

Specific quality issues prevent blind copying:

1. **Museum pages can contain errors.** The captured Brera catalogue displays a reversed 1790–1695 range for *La toeletta di Venere*. The Uffizi Madonna della Seggiola page gives Raphael an impossible 1483–1420 lifespan. Bologna’s Gozzadini page supplies a suspect 1522 birth year for Lavinia Fontana. Preserve the receipts, flag the affected fields, and use a separate artist authority before changing biographies.
2. **Attribution is not binary.** Borghese uses “attributed to” for several Bassano entries and question marks for Garofalo and Bril. The primary sample contains 6 qualified named-creator records and 8 anonymous/notname records. Keep source wording and roles; no automatic accepted attribution.
3. **Composite works need structure.** The Uffizi dukes diptych has two inventories, the Simone/Lippo work three, the Umbria polyptych four, the Russian menologion two, and Lucania six assembled panels. Neither flatten the evidence nor count each inventory as an independently selected masterpiece.
4. **Location evidence ages.** [GAM’s current Quarto Stato record](https://www.gam-milano.com/percorsi/collezioni/focus1/il-quarto-stato) and [the municipal 6 July 2022 notice](https://www.gam-milano.com/it/web/guest/-/il-quarto-stato) support its return from Museo del Novecento. Older Novecento pages cannot establish current location. GAM pages also differ on acquisition year (1920/1921), so that field remains unresolved. No current on-view claim has been made.
5. **Narrative chronology can conflict.** The Venice Tempesta page combines differing acquisition/provenance dates and discusses dating hypotheses. Its empty extracted creation field remains in review; publication does not get an invented exact year. Raphael’s “by February 1506” is an open bound, not an exact 1506 date.
6. **Record pages and context pages differ.** Capodimonte’s event URL supports multiple artworks and cannot uniquely identify each one. Such URLs are marked `object_identity_url: false` and excluded from automatic exact-object matching. Dates from events, acquisitions, restorations and artist lifespans were not promoted to creation years.

## 5. Source access, rights and limits

The fixed metadata fetch lists produced **131 successful HTML captures and 28 held capture records**. They include indexes, homepages, policies and object pages, with some repeated URLs and failed earlier routes. Counts are receipts, not unique museums. Ten manually curated primary entries additionally use saved web-tool evidence or a separately captured regional page. Inaccessible routes retain their errors; alternate official sources were used when available, without claiming the original route succeeded.

Sources are ranked by use: an official object page with inventory for object identity; an official museum or regional catalogue for attribution/date/collection context; a dated institutional statement for historical movement; a general museum page for discovery only. [Catalogo Generale](https://catalogo.cultura.gov.it/) and the [Ministry’s open-data entry point](https://cultura.gov.it/open-data-e-linked-data) warrant a future bounded national metadata pass. Administrative catalogue groupings must be reconciled with actual holding institutions and venues.

**No image in this research is cleared for reuse.** A website image, a source-image URL, an open metadata licence or a primary-media pointer is insufficient evidence of reproduction permission. The official [Barberini Corsini image-request page](https://barberinicorsini.org/servizi/richiesta-immagini/) is preserved as an operational rights route. Image selection and any subsequent downloads require object-specific rights evidence in the approved workflow. No broad legal conclusion is drawn from metadata licensing.

This pass is deepest in Tuscany and Lombardia. Lazio, Veneto, Marche, Umbria, Emilia-Romagna, Campania, Basilicata and Sicily have selected object evidence; other regional routes are discovery-level or access-held. Churches, fresco cycles, private collections, drawings, pastels, sculpture casts, regional catalogues and Italian artists held worldwide remain incompletely covered. The selected Venice drawing and plaster sculpture are typed separately from paintings. No exhaustive artwork or image harvest was attempted.

## 6. Concrete next review sequence

1. Reconcile the 25 institution-place gaps and distinguish organizational parents, museums and venues. Preserve existing institution and artwork IDs.
2. Review the [40 prioritized objects](priority-review-queue.md), starting with empty creator profiles, missing Brera/Uffizi highlights and central/southern museum identities. Match existing source IDs and inventories before proposing additions.
3. Validate anonymous-master, workshop, qualified-attribution and composite-work handling. Keep unknown metadata in review; do not invent missing years or creator biographies.
4. Work the **674 already-existing dated Italian-holding paintings without primary media** as a separate, selected image-rights research queue. Confirm identity before selecting a reproduction.
5. Broaden regional object research, particularly Piemonte, Liguria, Emilia-Romagna, Puglia, Calabria, Abruzzo, Molise, Sardegna and the northern border regions. Follow the preserved routes; prioritize museum highlights and documented holdings through 1970.

Every proposed addition remains research-only. This delivery does not authorize a database import, publication, deployment, deletion, merge or bulk download.

## Reproduction

`audit.py` performs repeatable-read, read-only catalogue queries. `research.py --stage lombardia` verifies and samples the already-pinned snapshot. `research.py --stage fetch --input <reviewed-list.json>` retrieves only the fixed metadata URLs, with robots checks and bounded requests. `extract.py` extracts source fields while retaining uncertainty. `research.py --stage identity` runs read-only, scoped source/inventory/title checks. `deliver.py` builds these reports and verifies the saved evidence offline. Re-running the database steps will create a new snapshot, so preserve this dated evidence before doing so.
