# Popular-painter images — regional museums, 18 September 2026

**Six additional paintings now have images in both local and production databases and Google Storage.** All six source/file/database audits, six storage audits and eighteen anonymous live checks pass. All six artworks remain **in review**.

| Painter | Painting / official catalogue record | Holding museum | Photograph and licence |
|---|---|---|---|
| Claude Monet | [Etude de Glycines](https://pop.culture.gouv.fr/notice/joconde/02410000233) | musée d'art et d'histoire de Dreux — Dreux | [CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Dreux_%C3%A9tude_de_glycine_1919-1920_Claude_Monet_Eure-et-Loir_France.jpg) |
| Claude Monet | [La Vallée de la Creuse, soleil couchant](https://pop.culture.gouv.fr/notice/joconde/M0028004853) | musée d'Unterlinden — Colmar | [CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Mus%C3%A9e_Unterlinden_-_Claude_Monet_-_La_vall%C3%A9e_de_la_Creuse,_soleil_couchant_(1889).jpg) |
| Gustave Courbet | [La truite](https://pop.culture.gouv.fr/notice/joconde/M5060000042) | musée d'Orsay — Paris | [CC BY 3.0](https://commons.wikimedia.org/wiki/File:Gustave_courbet,_la_trota,_1873.JPG) |
| Gustave Courbet | [Remise de chevreuils au ruisseau de Plaisir-Fontaine](https://pop.culture.gouv.fr/notice/joconde/000PE000691) | musée d'Orsay — Paris | [CC BY 3.0](https://commons.wikimedia.org/wiki/File:Gustave_courbet,_esercizi_dei_cerbiatti_nella_riserva_di_plaisir-fontaine,_1866,_01.JPG) |
| Jean-Baptiste-Camille Corot | [LE CONCERT CHAMPETRE](https://pop.culture.gouv.fr/notice/joconde/00000076477) | musée Condé — Chantilly | [Public domain](https://commons.wikimedia.org/wiki/File:Corot_concert_champ%C3%AAtre_Cond%C3%A9_Chantilly.jpg) |
| Élisabeth Vigée Le Brun | [Portrait de la comtesse Joséphine Mathilde Henriette Caroline de Baussancourt, née Bernard de Sassenay ; Portrait de la comtesse de Baussancourt née de Sassenay (titre ancien)](https://pop.culture.gouv.fr/notice/joconde/03030001787) | musée des beaux-arts et d’archéologie — Troyes | [CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Comtesse_de_beaussancourt_Vigi%C3%A9e_Lebrun_03322.jpg) |

## Coverage

Both databases now report **2,335 / 5,266 popular-painter paintings with usable images; 2,931 missing** (44.34% coverage). Among paintings with eligible creation dates and documented selection/holding evidence: **2,208 / 4,158 have images; 1,950 missing** (53.10%). This round added six images to each group, from this round's baseline of 2,329 and 2,202 respectively. Historical rounds used earlier snapshots; do not attribute unrelated changes between rounds to these six deliveries.

## Research and source verification

- Searched 180 existing eligible popular-painter gaps using French catalogue titles and painter surnames, including less prominent museum collections. Searches returned 625 distinct file records, including 59 preliminary original-photograph leads. These are discovery counts, not confirmed matches or image downloads.
- Matched exact national Joconde identifiers, complete inventory alternatives, creators, dates and the Commons artwork template or structured object identity. Copies and similarly titled works remain separate.
- Wikidata's API reported replication lag. Two source-refresh attempts exhausted their three 60-second backoffs. The work reused original September 14–15 authoritative responses, preserving retrieval dates and verifying original response hashes and exact entity equality. It did not bypass the API's pause or describe cached authorities as fresh.
- All six selected works were independently rechecked against **current official POP object pages**, including exact Museofile holding links, titles, accessions, creator lines, painting classification and date intervals. This establishes current native museum identity without inventing a Wikidata museum crosswalk. Current Commons file revisions and per-file licences were checked separately.
- Seven photographs passed the cached object identity and current rights checks. Six passed complete current native-catalogue verification and both-database selection. Courbet's *Le cerf à l'eau* remains queued: its POP response did not expose the required native museum link. The separate official Marseille collection page is retained as evidence for further review; its website photograph was not downloaded.
- Other cases remain held for missing exact authority evidence, conflicting accessions, missing original photographic credit or unclear separate photo rights. Twelve additional artwork authorities could not be refreshed or resolved from available verified caches; their discovery captures remain available.
- Downloaded only the six selected, rights-cleared images. Each was visually inspected individually. Full compositions and original frames remain visible; the Colmar Monet photograph also includes some surrounding wall. Only proportional resizing and JPEG compression were applied. No generation, cropping or colour alteration.
- Source rights: one Public Domain Mark, two CC BY 3.0, three CC BY-SA 4.0. Photographer credits, licence versions/links, exact file sources, verification times, image checksums and transformation notices are retained. Restricted museum-supplied reproductions were not substituted for these independent photographs.

## Delivery and validation

- Backed up the six existing artwork, creator and identifier rows in each database outside the project, under the approved Artline backup location, before writing.
- Existing attachment and delivery tools added six primary images locally and six in production. Source identifiers, licences, image sizes, byte hashes and Google Storage metadata match the saved receipts.
- Read-only preimage audits confirm that only primary image associations and revision timestamps changed. Creator links, artwork facts, institution links and review status are preserved. No duplicate primary image hashes were found on other artwork records.
- Eighteen anonymous live checks passed: six image byte checks, six museum-detail pages and six painter-detail pages, including exact source, credit and licence fields. One initial museum-detail request returned HTTP 500; the error is preserved and all checks passed on retry. Its cause was not established.
- No application code, schema change, deployment or catalogue publication was required. This was a data-only image round using the existing validated adapters; no new fixtures or test data were inserted.

## Evidence

- `approved-image-manifest.jsonl`: six delivered image records and provenance.
- `reviewed-images.json`: six checksummed visual-review decisions.
- `regional/official-verified.json`: fresh official object facts and Museofile links, with page capture hashes.
- `regional/official-pages/`: source captures; `regional/official-retry/`: preserved unsuccessful Marseille national-record retry.
- `cached-authority-integrity-audit.json`: original cached response hashes and entity equality checks.
- `regional/review-ready-cache.json`, `regional/review-held-cache.json`, `regional/official-held.json`: candidate decisions.
- `regional/searches/` and `regional/gap-candidates.json`: bounded discovery records for all 180 gaps.
- `local-final-audit.json`, `production-final-audit.json`: six passing source/file/database checks each; production also verifies Google Storage.
- `final-preimage-and-duplicate-audit.json`: both-target preservation and duplicate checks.
- `public-initial-error.json`, `public-all-images-final.json`: initial transient failure and eighteen final successful checks.
- `coverage-both-before.json`, `coverage-both-final.json`: read-only coverage snapshots.
- `round-summary.json`: aggregate round results.
- `artifact-safety-scan-final.json`: scoped credential/private-reference pattern scan and delivered JPEG metadata checks.
