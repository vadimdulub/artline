# Research log and remaining gaps

9 September 2026. Internal provenance; reports use descriptive source links, not tool IDs.

Discovery merged existing schema, previous coverage research, official NGA CSVs, and Russian / Italian national and museum documentation. Focused parallel follow-up assigned Russia (Pushkin, Russian Museum, Hermitage, Tretyakov, Goskatalog) and Italy (ArCo/ICCD, Uffizi, regional sources) to two independent research workers. They did not write catalogue data or report drafts. Main agent handled bulk selection, verified critical claims, and performed every local import.

Targeted investigations: museum name + official collection/open data/API/use conditions; exact Pushkin JSON routes; KAMIS painting fund13 and object77624; Russian Museum painting pagination, Nikitin object and author pages; ICCD ArCo release1.1 notes, Swagger, archive HEAD/range, current SPARQL/OAI, current catalogue terms; Lombardia, Emilia-Romagna and Piemonte open-data portals; Brera technical object records and accession identities; French Joconde official downloadable resource and CSV headers; NGA source roles, physical child associations, literal date conflicts, creator authorities and image metadata.

Bounded network actions: normal fetch with allowlisted URLs, time/byte limits and no redirect surprises. Full Joconde and NGA image CSV downloads stalled and were not repeatedly retried. A different small-range strategy recovered the complete 298,183-byte Pushkin highlights feed and an explicitly partial262,144-byte NGA image metadata sample with stable validators. Nineteen selected NGA images downloaded successfully after adding bounded support for IIIF HTTP200 responses; the remaining image lacked ETag on a multi-request response and was stopped. No image workaround bypassed an access denial.

| Gap | Evidence / confidence | Contradiction or missing piece | Next action |
|---|---|---|---|
| 50,000 eligible artworks | Actual34,264 / high | Target short15,736; prints/drawings dominate NGA | Implement next official catalogue adapter; never count staged rows |
| Pushkin full paintings | Official search1,729 / high | All dates, possible overlap with49 highlights; no full harvest | Snapshot paginated KAMIS objects, review identities/dates, reconcile accession aliases |
| Russian Museum | Worker observed4,628 online / medium-high | Later main retrieval fails; other-museum works appear on artist pages; dimensions conflict | Restore reliable HTML capture, parse only current museum collection; verify object-level dates and rights |
| Hermitage / Tretyakov / Goskatalog | Official pages found / limited live access | No verified usable bulk export in this run | Obtain documented operational metadata feed; no speculative crawler |
| ArCo Italy | Official release and historical5.12GB dump / high | Old dump rights vs current catalogue terms; mixed entities, location and quarantine semantics | Confirm release rights and stage streamed RDF in separate evidence store; never load whole graph into RAM or public works |
| Uffizi | Official maintenance notice / high | Administrative exports are not artworks | Recheck collection archive after service recovery |
| Italian regional data | Official portals inspected / variable | Lombardia xnav-xbdb counts artworks per museum, not objects; Emilia-Romagna lead was Jewish cemeteries; Piemonte unresolved | Require object granularity, stable IDs, creation fields, holder and terms before importing |
| Brera remaining | Nine verified additions / high | Daniele Crespi and Michelangelo Anselmi absent local authority; reversed source dates for La toeletta di Venere | Resolve authority with primary catalogue evidence, preserve incorrect date as source conflict |
| Images |19 new locally / high | This is a256KiB sample, not full NGA image export; Russian/Italian image rights not cleared for general reuse | Retrieve more bounded source image metadata, then per-image rights checks |
| NGA deferred |53,818 paint/draw/print source rows / high |7,836 blank literal dates among11,922 literal-date deferrals; missing/multiple makers and inseparable children | Separate review tasks; no lifespan-derived dates or inflated physical-object counts |

Stop rationale: usable sources have been imported and mechanically verified; the remaining country-scale routes require a new adapter or recovery/rights decision, not another variant of the same search. Research is incomplete at country scale and the50k target remains unmet. The report is a verified progress artifact, not an exhaustive museum census or a claim to have harvested all catalogues.
