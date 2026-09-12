# Artline: a larger, source-backed catalogue

Audience: Artline's owner. Date: 9 September 2026. Scope: Russian and Italian museums in depth, plus official bulk sources to expand museum-connected artworks created by 1970. This is a verified progress report, not a complete national catalogue or museum census. Web sources were accessed on 9 September 2026; where no publication date is supplied, the access date is not a claim of recent content.

## What was actually added

The local database grew from 2,223 to 34,264 artworks: 32,041 additions. It now contains 5,315 artist records (5,314 active), 57 institutions and 230 media assets. This pass added 19 real images. New catalogue records remain in review; published artwork and current-display assertion counts remain zero. These figures come from direct SQL, import receipts and successful replay checks, not museum collection-size estimates.

| Source batch | New artworks | What the count means |
|---|---:|---|
| National Gallery of Art | 31,983 | 1,694 paintings, 6,485 drawings, 23,804 prints |
| Pushkin State Museum of Fine Arts | 49 | Date- and authority-checked paintings from its highlights feed |
| Pinacoteca di Brera | 9 | Individually reviewed paintings, not a complete museum export |
| Total added | 32,041 | Distinct local artwork records, after existing-record reconciliation |

The 50,000 target is not reached: 15,736 further eligible artworks are needed, or 65,736 to reach 100,000. The present catalogue contains 3,851 paintings, 6,559 drawings, 23,849 prints and five frescoes. It would be misleading to call the total 34,264 paintings or masterpieces. Ordinary museum holdings are kept separate from museum-designated highlights and personal must-see selections.

The largest source was the museum-managed [NGA Open Data repository](https://github.com/NationalGalleryOfArt/opendata), pinned to its 9 September 2026 revision. Of 87,311 painting/drawing/print source records, 33,493 passed the selected physical-object, attribution, date and identity gates. This includes 1,510 artworks already present. The remaining 53,818 source records are excluded or deferred, not secretly counted as additions.

All new artworks have factual descriptions, source URLs and museum context. Longer text is now available through “About this artwork” in painter and museum records and is loaded on demand. The NGA [Free Images and Open Access policy](https://www.nga.gov/artworks/free-images-and-open-access) is checked separately from its metadata licence: 19 exact primary-view, open-access images were stored locally. This is a small selected image sample, not comprehensive image coverage.

## Russia: real additions, larger remaining catalogues

Pushkin is the first new Russian institution in this pass. Its official [Open data documentation](https://pushkinmuseum.art/open_data/index.php?lang=ru) links a [machine-readable highlights feed](https://pushkinmuseum.art/json/masterpieces.json). The complete downloaded feed has 97 objects of different types, including 55 paintings. Forty-nine were imported for 41 existing painters after matching credited names and interpreting creation dates. Six were deferred for unresolved identities or incomplete dates. The HTTP Last-Modified date is 25 October 2018: this is historical catalogue evidence, not fresh evidence of gallery display.

The full [Pushkin painting collection search](https://collection.pushkinmuseum.art/entity/OBJECT?fund=13) shows 1,729 records across all dates. This is a concrete next acquisition route, but not 1,729 new eligible records: it overlaps the highlights, includes later artworks and still needs object-level reconciliation. The larger mixed-object catalogue should not be substituted for a painting count.

The research lane observed 4,628 online paintings and 318 highlights in the [Russian Museum painting catalogue](https://rusmuseumvrm.ru/collections/painting/index.php?lang=ru&p=0&page=1&ps=500&show=asc&t=0). Later direct retrieval failed, so those are an observed listing snapshot rather than a guaranteed current denominator. No Russian Museum batch was imported. Artist pages can also list other museums' works; one Nikitin painting has conflicting dimensions on two official presentations. These require explicit reconciliation.

Hermitage, Tretyakov and Goskatalog were researched but not bulk-imported. The [Hermitage digital collection](https://www.hermitagemuseum.org/digital-collection/37067) had failed direct retrieval; [Tretyakov's virtual-gallery FAQ](https://my.tretyakov.ru/app/faq) did not establish a usable catalogue export; the Ministry's [museum-exhibits open-data landing](https://opendata.mkrf.ru/opendata/7705851331-museum-exhibits/) could not be verified operationally. A library bibliography or a virtual gallery is not a replacement for artwork records.

Russian image and authored-text reuse remains source-specific. [Pushkin's use conditions](https://pushkinmuseum.art/usage_policy/index.php?lang=ru) contain restricted noncommercial allowances and permission workflows; [Russian Museum material-use terms](https://rusmuseumvrm.ru/terms/index.php) also need to be respected. No Russian images or authored essays were copied in this pass; the imported descriptions restate factual catalogue fields.

## Italy: small verified batch, substantial bulk opportunity

Nine paintings were added from the [Pinacoteca di Brera online collection](https://pinacotecabrera.org/collezioni/collezione-on-line/), taking the museum's local representation from four to thirteen. They include Hayez's [Il bacio](https://pinacotecabrera.org/collezioni/collezione-on-line/il-bacio/), Albani's [Danza degli Amorini](https://pinacotecabrera.org/collezioni/collezione-on-line/danza-degli-amorini/), two Anguissola works and five Appiani works. Each record preserves the museum accession, credited painter, literal creation date, medium, dimensions and exact object URL. Photographs were not downloaded merely because a download link exists.

The strongest national-scale lead is ICCD/CNR's ArCo. Its [version 1.1 release notes](https://github.com/ICCD-MiBACT/ArCo/blob/master/ArCo-release/release_notes/1.1.md) document a quarantine graph and changes to agent/site identity construction. The linked [historical knowledge-graph archive](http://arco.istc.cnr.it/arco-data/1.1/arco-knowledge-graph-1.1.nt.gz) responded to a header request with 5,121,864,209 compressed bytes and a 26 October 2020 modification date; a small gzip sample was valid N-Triples. The full archive was not downloaded or imported.

This graph is not five billion bytes of eligible paintings. It mixes cultural property, supporting entities, places and historical records. A correct adapter must identify the artwork, creation event, credited creator and current physical collection separately, exclude quarantine, and retain release-aware authority mappings. One inspected [Castello Sforzesco painting record](https://catalogo.beniculturali.it/detail/Lombardia/HistoricOrArtisticProperty/B0020-00337_R03) dates the work after 1605/before 1618, while its catalogue record was compiled in 1996. Confusing those dates would put the artwork outside the cutoff incorrectly.

The [ICCD open-data documentation](https://iccd.cultura.gov.it/it/per-condividere/dati-aperti) describes national services, but live SPARQL/OAI probes failed in this run. Current [national catalogue terms](https://www.catalogo.beniculturali.it/termini-uso) and historical ArCo licensing references also need release-specific reconciliation; current metadata terms must not be applied retroactively to an old archive without evidence. Images have separate conditions.

Uffizi's [digital archives page](https://www.uffizi.it/pagine/archivi-digitali) reported maintenance. Regional follow-up found some museum-level artwork counts rather than object records, and unrelated cultural-heritage datasets. These were not imported as paintings. Within Brera, absent creator authorities and a reversed source date were deferred instead of guessed. Italian coverage therefore remains small, despite the stronger national bulk lead.

## Verification and the next expansion

The backend importer works in checksum-pinned chunks of at most 1,000 artworks, with local-only commands, transactional rollback previews and replay keys. A fresh pre-import PostgreSQL backup was created and its archive contents verified; a full restore test was not performed. All 34 final NGA chunks and the Pushkin, Brera and earlier NGA batches replayed without changing fingerprints across the checked catalogue, evidence, media and audit tables.

New NGA creator identities use stable museum constituent IDs and source QIDs when present. There were 4,313 new artist records, including printmakers. Of these, 3,240 have closed, unqualified source lifespan dates; 1,073 use explicitly labelled documented-work activity intervals. Missing life dates are not invented. Two source artists called Master CR were deliberately retained as separate authorities, not merged on name. New artists were not automatically labelled popular.

Full Go tests, Go vet, frontend unit tests, TypeScript and lint checks passed. Scoped identity and museum queries were also checked with 100,000-row isolated/temporary fixtures; these are not 10-million-row benchmarks. The actual NGA works-page observation improved from 2,716 ms to 450 ms after avoiding repeated full-profile work and unnecessary per-row enrichment. Results vary with cache, hardware and concurrency; larger production-scale testing is still required.

Live API checks cover museum totals, non-overlapping cursor pages, Monet-plus-Pissarro filtering, painter chronology, individual descriptions and review-only access. All 19 new image files match stored byte sizes and SHA256 values; three were visually sampled. One selected image was skipped because a ranged response lacked a stable validator. No publication, Git commit, deployment or Terraform apply was performed.

Next, prioritize an operational Pushkin/Russian Museum object capture path and an ArCo adapter with resolved release rights. France's official [Joconde dataset](https://www.data.gouv.fr/datasets/collections-des-musees-de-france-base-joconde), published by the Ministry of Culture, is another large metadata opportunity, but its full download failed here. Its record-creation field must not be mistaken for artwork creation. These source routes are opportunities, not forecasts of how many eligible records they will yield.

The path to 50,000 should stay evidence-based: acquire a complete bounded source snapshot; reconcile physical objects and creator identities; check creation by 1970 and museum connection; preview, apply and replay; then add only rights-cleared pictures. Current country coverage, image coverage and the overall count target remain incomplete. No work continues in the background after this handoff.
