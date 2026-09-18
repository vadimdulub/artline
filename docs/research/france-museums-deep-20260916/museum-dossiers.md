# France museum research: findings and priorities

Research date: 16 September 2026. Read this with [measured coverage](coverage.md), the [733-museum regional inventory](regional-inventory.md), [177 catalogue routes](catalogue-routes.md), and the [object-level review](object-review.md). The local figures include review records and are not production-visible counts.

## What is actually missing

There are four separate gaps:

1. **Collection coverage:** small highlight selections do not represent the broader holdings. Louvre, Grenoble, Lyon and the modern-art networks are particularly underrepresented in this audit.
2. **Image coverage:** even existing works usually lack an attached image. There are 9,774 such French-linked paintings with stored end dates through 1970 in the local audit.
3. **Source coverage:** Joconde is a contribution-based national catalogue, not a mirror of every museum's complete inventory. Native catalogues frequently contain far more material, and native images can exist when the Joconde image flag is negative.
4. **Identity/provenance:** duplicate museum identities, unlinked geography, deposits and same-title versions can create false gaps and false additions.

The national census therefore combines the official directory, existing Joconde data, native museum catalogues, regional networks and file-specific image evidence. The 1,328 bounded source candidates are not 1,328 proven missing works: 35 already produce institution-scoped accession leads and 58 produce same-title leads. These sets overlap and are not deduplicated additions.

## Louvre — priority 1

**Measured:** 15 local paintings dated through 1970, 10 attached images, compared with 5,446 painting-domain notices in the pinned Joconde export. These are different date/selection scopes, but clearly establish that the local Louvre selection is small.

The primary route is [Louvre Collections](https://collections.louvre.fr/), not a general-image search or a count of pictures tagged Louvre. Its more-than-500,000 records cover multiple departments and the Musée Delacroix; that number must not be presented as a painting count. Individual records provide persistent ARKs and explicitly linked JSON representations. Start from the department, artist or a bounded curator-selected list.

The [museum's masterpiece album](https://collections.louvre.fr/album/2) provides an explicit curatorial designation. Four object checks in this report demonstrate why careful matching matters:

- Titian's *La Femme au miroir*, INV 755: already local, no primary media; the catalogue gives 1525–1550.
- Dürer's self-portrait, RF 2382: already local with media; the record's display field differs from a blanket “masterpiece is on view” assumption.
- La Tour's *Tricheur*, RF 1972 8: acquisition in 1972, creation around 1636–1640; eligible creation must not be confused with accession year.
- Rigaud's Louis XIV, INV 7492: do not merge with Versailles version MV 2041.

Under the [Louvre terms](https://collections.louvre.fr/page/cgu), catalogue texts and photo reuse have different conditions. Textual catalogue information is available under the Open Licence; photographs are not blanket CC0. Preserve source attribution and update dates. For Artline image use, assess the specified use and each photo's credit/terms, or locate an independently reusable reproduction of the same object. A download button alone is not permission for every use.

Coverage must include non-French artists held in France. For a later medieval/Byzantine pass, keep anonymous and workshop objects visible in research instead of excluding them because they cannot yet be attached to a named painter. That does not authorize importing them through the named-creator workflow.

## Paris modern art: two different institutions

### Centre Pompidou / Musée national d'art moderne — M5050

The pinned national feed has 34 notices under this museum code but **no painting-domain notices**. No matching institution identity was established in the local audit. Neither observation implies that the museum lacks paintings.

Use the [native collection portal](https://collection.centrepompidou.fr/) and [official artwork search](https://www.centrepompidou.fr/fr/recherche/oeuvres?display=Grid). The search exposed a painting facet of 6,790 at the research check; dynamic search counts are not a certified physical inventory. The museum's [masterpiece selection](https://www.centrepompidou.fr/fr/collection/les-chefs-doeuvre) supplies a bounded starting point.

[Matisse's *La Blouse roumaine*](https://www.centrepompidou.fr/fr/ressources/oeuvre/cLrja8b), AM 3245 P, is an exact object lead: April 1940, oil on canvas, 92 × 73 × 2.5 cm. The record labels the artwork public domain but separately credits/distributes the photograph through GrandPalaisRmn. This distinction must survive ingestion. Its creation in Nice is not evidence of a Nice museum holding. Loan locations and future exhibition dates are not changes of ownership.

### Musée d'Art Moderne de Paris — M1101

This is the municipal museum, **not** Pompidou. The audited local alias lacks a country/place link and contains only 7 dated paintings; 6 have primary media. The [museum collection page](https://www.mam.paris.fr/fr/collections) and [Paris Musées catalogue](https://www.parismuseescollections.paris.fr/fr) should be used together.

The object shortlist includes Suzanne Valadon's *Nu* (1925, AMVP 1057) and *La boîte à violon* (1923, AMVP 1712), each explicitly carrying CC0 image credit. Her *Trois baigneuses nues* is recorded separately as a drawing. These are useful sources for women artists, but artist gender is not inferred from a portrait's subject or a name alone.

### Petit Palais and the other municipal collections

Petit Palais Paris, M1111, has 42 dated paintings in the local audit and 20 media attachments. Its CC0 sources include Monet, Morisot, Cézanne and Courbet. Morisot's PPP488 already exists locally with media: use the museum source to improve provenance, not create another work.

The wider Paris Musées catalogue also routes to Carnavalet, Cognacq-Jay, the Musée de la Vie romantique and artist/house museums. Museum identity must remain attached to the object. **Petit Palais Paris is not the Petit Palais in Avignon.**

## Dieppe — priority 1, more than an Impressionist footnote

**Measured:** 43 local dated paintings, 4 media attachments. The source snapshot contains 270 painting notices, 194 marked with an image. [The official museum record](https://pop.culture.gouv.fr/notice/museo/M0712) and [Normandy network museum page](https://www.musees-normandie.fr/musees-normandie/musee-de-dieppe/) establish a broader collection spanning maritime, Northern-school and later painting. The network's whole-collection figures include objects such as ivory; they must not be relabelled as painting totals.

Two exact checks:

- [Pissarro, *Vue de l'avant-port de Dieppe*](https://pop.culture.gouv.fr/notice/joconde/07120002591), 1902, inventory 902.18.1: municipality-owned; several alternate inventory references and photographs. A separate Commons photo carries an explicit CC BY-SA 2.0 label and is recorded in the image shortlist. It still needs a visual match/crop/credit check.
- [Renoir, *Portrait de Madame Paul Bérard*](https://pop.culture.gouv.fr/notice/joconde/000PE015361), 1879: Orsay/state ownership, deposit at Dieppe. Preserve both D.981.1.1 and RF 1978-14, and both institutional roles. The source directs photo reuse enquiries to RMN.

The bounded snapshot candidates also identify Sickert, Lapostolet, Vollon, Hostein, Ménard, Lacoste, Mathey and Stanfield works with source references and supplied inventory information. Anonymous Dieppe material is retained with attribution-review flags, not assigned an invented painter.

The [Dieppe heritage portal](https://patrimoine.dieppe.fr/collections) is a separate library/archive resource; its digitized documents are not automatically Château-Musée holdings. The [Normandy collection network](https://collections.musees-normandie.fr/) is the stronger regional object-catalogue route.

## Le Havre / MuMa — priority 1

**Measured after unioning two local museum aliases:** 52 dated paintings, only 1 with primary media. Joconde supplies 452 painting notices, 343 with images; only 19 of those source references occur among the scoped local works. Some museum-site works can already be local under other identifiers.

Use [commented works](https://www.muma-lehavre.fr/fr/collections/oeuvres-commentees/tout), the specialist artist material, and regional/Joconde records. The [museum's Dufy collection essay](https://www.muma-lehavre.fr/fr/expositions/raoul-dufy-au-havre/le-fonds-raoul-dufy-du-muma) describes a 128-work corpus in its historical publication context. It is not a claim that all 128 are paintings or that 128 remains a current total.

[Boudin collection history](https://www.muma-lehavre.fr/fr/expositions/eugene-boudin-latelier-de-la-lumiere/boudin-au-muma) records a donation of 240 studies under one inventory number. A group accession cannot therefore be used as an unconditional one-object deduplication key.

The Dufy checks distinguish a final painting, an oil study and a pencil study of *Fin de journée au Havre*, acquired at different times. A separately acquired *Port du Havre* around 1900 is not a similarly titled 1906 work belonging to Wuppertal that appears in an exhibition catalogue. All caption/date variants remain recorded in `primary-objects.json`.

For Monet's *Fécamp, bord de mer*, the official snapshot and a [Commons file page](https://commons.wikimedia.org/wiki/File:MuMA_-_Monet_-_Fécamp,_bord_de_mer.jpg) agree on accession 994.01 and Joconde ID 07200000523. The file offers a PD-Art-labelled reproduction, 2,020 × 1,640 pixels. This is an individual image lead, not a licence for the museum's website photography. File revision, jurisdiction and visual-quality checks remain open.

The older Normandy research selected only parts of MuMa/Rouen. Its outputs remain useful provenance, but do not close collection coverage. Continue to Honfleur, Rouen, Caen, Fécamp, Cherbourg, Vernon, Giverny, Bayeux and Saint-Lô through the region inventory rather than treating Le Havre as the entire Normandy task.

## Nice — four distinct high-priority collections

| Museum | Local dated paintings / images | Main research route |
|---|---:|---|
| Beaux-Arts Jules Chéret, M0880 | 48 / 2 | Official city/museum pages, Joconde and exact image-file matches |
| Matisse, M0884 | 22 / 0 | Museum collection publications + Joconde accession crosswalk |
| MAMAC, M0888 | 21 / 0 | Native Navigart catalogue + collection records/publications |
| Marc Chagall, M5029 | 59 / 0 | National museum object pages + final-work/study reconciliation |

### Beaux-Arts Jules Chéret

The [City of Nice museum page](https://www.nice.fr/lieux/musee-des-beaux-arts/) is an official institutional starting point. The pinned source has 176 painting notices, including 125 image flags. Selected source records in this packet include Landon, Van Loo, Bloemaert and Henriette Browne (*Portrait d'un Nubien*, 1878, N.Mba 174); these retain their source facts rather than inventing biographies.

An explicit conflict deserves review: source 08800000080 describes a work dated 1879 with a creator label containing Joseph Fricero's life dates 1807–1870. Do not repair the creator or date by guesswork. Commons' museum category is useful for discovery, but every file needs its own licence and matching museum evidence; a category membership is not sufficient provenance.

### Musée Matisse

Joconde's 32 painting-domain notices have zero image flags in this export. Yet the museum's [2024–25 collection publication](https://www.musee-matisse-nice.org/wp-content/uploads/2025/03/CP_La-collection_Musee-Matisse-Nice_oct2024-avr2025.pdf) documents *Nature morte aux grenades*, November 1947, and *Nu bleu IV*, 1952, with photo credits. The latter is cut paper and an Orsay/state deposit, not an oil painting acquired into municipal ownership.

The PDF text was available through indexed primary-source results; direct access returned 403, so its layout/images were not inspected. The date/type/caption evidence is flagged accordingly. Earlier [press-use conditions](https://www.musee-matisse-nice.org/wp-content/uploads/2022/07/DP_Hockney-Matisse_FR.pdf) are restricted to exhibition press purposes; they do not establish permission for a permanent Artline image archive. No conclusion about present rights is inferred solely from old copyright lines.

### MAMAC

The [native catalogue](https://www.navigart.fr/mamac/) is independently listed by the Ministry. It is JavaScript-rendered and produced no readable object text in the research browser; that is an access limitation, not zero holdings. Joconde has 253 painting-domain notices, all with negative image flags in the snapshot.

The indexed [museum teaching sheet](https://www.mamac-nice.org/wp-content/uploads/2020/06/FICHE_PEDA_la_couleur_2020.pdf) and source record agree on Martial Raysse's *Nissa Bella*, inventory 990.1.1: created 1964, acquired 1990, signed 1996. Its mixed-media construction should not be simplified to oil on canvas. The official source credits ADAGP; direct PDF inspection was blocked.

Other bounded leads include Frank Stella's *Damascus Gate II* (1969), Niki de Saint Phalle's *Tir au soulier* (1961), Yves Klein, Jean Villeri and Albert Chubac. They require individual date/type/rights review, not wholesale adoption of a modern-art catalogue that also contains post-1970 work.

### Musée national Marc Chagall

The [museum's collections](https://musees-nationaux-alpesmaritimes.fr/chagall/collections) distinguish the biblical cycle, other paintings, preparatory works, prints and sculpture. Donations in 1966/1972 are not the creation dates of their contents.

The [Cantique cycle](https://musees-nationaux-alpesmaritimes.fr/chagall/collection/periode/le-cantique-des-cantiques) contains final works with dates and dimensions. The object review separates I (1960), III (1960), IV (1958) and V (1965–1966). Joconde also has many same-title studies with distinct MBMC accessions. Title-only matching would attach the wrong image or merge distinct works. One page's alternative image text conflicts with its full caption; that disagreement is retained.

These official pages have images despite the zero Joconde image flags. They carry RMN-GP/photographer and ADAGP credits; this research has not established an open image licence. Date ranges crossing 1970, such as the 1970–1973 Elijah mosaic lead, remain outside automatically eligible selections.

## The Côte d'Azur must extend beyond Nice

These are distinct institutions, not aliases of Nice's museums. Codes and snapshot website routes are included in the national inventory.

| Place / collection | Code or authority | Why it belongs in the next research batch |
|---|---|---|
| Biot, Musée national Fernand Léger | M5028 | Native [collection sections](https://musees-nationaux-alpesmaritimes.fr/fleger/collections); paintings, paper works and designs need separate types |
| Vallauris, Picasso La Guerre et la Paix | M5047 | National-museum route; monumental work and creation/installation dates need separation |
| Vallauris, Magnelli / ceramics museum | M0892 | Separate municipal institution and holdings |
| Antibes, Musée Picasso | M0867 | 219 painting-domain notices in the snapshot; native collection verification and rights |
| Cagnes-sur-Mer, Musée Renoir | M0871 | No painting notices under this code in the snapshot does not close the research |
| Cagnes-sur-Mer, château-musée | M0870 | Separate collection from Musée Renoir |
| Le Cannet, Musée Bonnard | M1135 | Native catalogue route is listed by the Ministry; absent Joconde painting feed |
| Menton, Palais de Carnolès | M0878 | 59 source painting notices; broader collection than a Cocteau-only city search |
| Menton, Musée Jean Cocteau | M0879 | Distinguish drawings/paintings and work dates; six painting-domain notices in snapshot |
| Saint-Paul-de-Vence, Fondation Maeght | Independent foundation | [Foundation collection](https://fondation-maeght.com/collection-permanente/?lang=fr); do not confuse with Galerie Maeght or assume Muséofile covers it |
| Saint-Tropez, L'Annonciade | M0941 | 142 source painting notices, 130 with image flags; local 45 / 2 |

The national museums' [shared mission page](https://musees-nationaux-alpesmaritimes.fr/fleger/nos-missions) confirms Chagall, Léger and Vallauris are coordinated but distinct museums. The [MAMAC-at-Biot exhibition](https://musees-nationaux-alpesmaritimes.fr/fleger/agenda/evenement/leger-et-les-nouveaux-realismes) is a concrete reminder that an exhibition venue must not replace a lending museum as owner.

## Priorities across every French region

This is an editorial research queue, not a claim that every named collection has been object-by-object verified. Each museum's registry facts, native route where listed, and measured source/local counts are in the accompanying inventories. Do not rank museums only by their Joconde contribution volume.

| Region | First collections to investigate beyond the named-city deep dives |
|---|---|
| Auvergne-Rhône-Alpes | Grenoble; Lyon Beaux-Arts and macLYON separately; Saint-Étienne MAMC; Chambéry; Brou/Bourg-en-Bresse; Crozatier/Le Puy; Paul-Dini/Villefranche; Roger-Quilliot/Clermont-Ferrand |
| Bourgogne-Franche-Comté | Dijon Beaux-Arts and Magnin; Besançon; Dole; Autun/Rolin; Mâcon/Ursulines; Ornans/Courbet; Saint-Claude/Abbaye; Beaune |
| Bretagne | Rennes Beaux-Arts; Quimper Beaux-Arts and Musée breton separately; Pont-Aven; Brest; Vannes; Saint-Brieuc; Musée de Bretagne for eligible image/document leads |
| Centre-Val de Loire | Tours; Orléans; Bourges/Estève; Loches/Lansyer; Montargis/Girodet; Blois; Châteauroux/Bertrand; Chartres and Dreux |
| Corse | Ajaccio/Palais Fesch first, then Maison Bonaparte and Bastia. Fesch has zero painting notices in this feed despite its major native painting collection |
| Grand Est | Strasbourg Beaux-Arts and MAMCS separately; Colmar/Unterlinden; Nancy; Reims; Troyes modern and fine-art museums separately; Épinal/MUDAAC; Bar-le-Duc; Verdun |
| Hauts-de-France | Lille Beaux-Arts; LaM; Roubaix/La Piscine; Le Cateau/Matisse; Douai/Chartreuse; Valenciennes; Chantilly/Condé; Amiens/Picardie; Beauvais/MUDO; Compiègne; Saint-Omer |
| Île-de-France | Louvre, Pompidou, MAM Paris, Petit Palais; Orsay, Orangerie, Marmottan, Picasso, Moreau, Henner, Carnavalet, Cognacq-Jay; Versailles; Fontainebleau; Boulogne/Années Trente; Maurice-Denis/Saint-Germain-en-Laye; independent collections such as Custodia and Jacquemart-André |
| Normandie | Dieppe and MuMa, then Rouen, Caen, Honfleur, Cherbourg/Thomas Henry, Fécamp/Pêcheries, Vernon/Blanche Hoschedé-Monet, Giverny, Bayeux/MAHB, Saint-Lô, Eu |
| Nouvelle-Aquitaine | Bordeaux Beaux-Arts and CAPC separately; Bayonne/Bonnat-Helleu; Pau; Agen; Libourne; Rochechouart; Limoges; La Rochelle; Poitiers; Niort through Aliénor and museum catalogues |
| Occitanie | Montpellier/Fabre; Toulouse/Augustins, Abattoirs and Bemberg separately; Montauban/Ingres-Bourdelle; Castres/Goya; Albi/Toulouse-Lautrec; Céret; Collioure; Nîmes; Rodez/Soulages; Sète/Paul-Valéry; Perpignan/Rigaud; Narbonne |
| Pays de la Loire | Nantes/Musée d'arts; Angers; Le Mans/Tessé; Fontevraud; Laval; Les Sables-d'Olonne/Abbaye Sainte-Croix; La Roche-sur-Yon; Cholet |
| Provence-Alpes-Côte d'Azur | Nice/coastal sequence above; Marseille Beaux-Arts and Cantini; Aix/Granet; Avignon Calvet and Petit Palais; Toulon; Martigues/Ziem; Saint-Rémy/Estrine; Arles/Réattu |
| Overseas territories and departments | Saint-Denis/Réunion Léon-Dierx first; Saint-Paul/Villèle; Guadeloupe/Saint-John-Perse and art-history collections; Martinique; Guyane/Franconie; New Caledonia native catalogue. Expand beyond the snapshot's combined overseas bucket in a later administrative crosswalk |

Three independently corroborated reasons to widen the source strategy:

- [Nantes' own collection introduction](https://museedartsdenantes.nantesmetropole.fr/collections/) routes to its online catalogue and separates old, nineteenth-century, modern and contemporary material. Apply the creation cutoff to returned objects, not to the museum name.
- [Palais Fesch's collection presentation](https://www.musee-fesch.com/collections-du-musee-fesch-palais-des-beaux-arts-d-ajaccio/presentation) documents extensive Italian painting, Corsican painting and other holdings. A zero in Joconde cannot justify omitting Corsica.
- [Léon-Dierx collection history](https://www.musee-leondierx.re/fr/histoire-des-collections) documents the Vollard donations and later additions. Prints must remain distinguishable from paintings, and acquisition in the 1980s–1990s does not establish post-1970 creation.

Native collection systems already mapped include Navigart/Videomuseum, Webmuseo, Opacweb, Louvre ARK/JSON, Paris Musées and individual municipal portals. They are different providers with different reuse/access conditions; one universal scraper is not an established solution.

## Image research: actionable sources and limits

| Source | Evidence from this research | Next step |
|---|---|---|
| Paris Musées | Eight individual painting records carry CC0 labels; published IIIF links recorded for five of them | Recheck selected asset and current terms; use documented API/manual workflow, retain credit/source; resolve existing works first |
| Dieppe alternate Pissarro photograph | File page labels the photograph CC BY-SA 2.0 and credits Patrick/Morio60 | Verify latest revision, exact work, frame/crop and attribution/share-alike handling |
| MuMa Monet alternate reproduction | Exact accession + Joconde match; file page asserts PD-Art/Public Domain Mark | Review jurisdiction and image quality before accepting the asset |
| Reims museum portal | [Indexed official terms](https://musees-reims.fr/fr/annexes/article/mentions-legales-et-conditions-generales-d-utilisation) offer reuse of specified public-domain content under Open Licence conditions; direct policy fetch returned 403 | Confirm live terms and each artwork/photo; preserve author, photographer, museum and source; use allowed access path |
| Louvre | Open textual metadata; conditional photography terms | Keep metadata and media licences separate; assess actual intended use |
| Chagall / Matisse / MAMAC / Léger | Official sources clearly contain images beyond Joconde's image flags, with identified credits | Permissions/licensing research or independently cleared file-specific alternatives |
| Regional networks | Rich metadata and many image flags | Check each contributing museum/asset; no network-wide open-image assumption |

The [Paris Musées API](https://apicollections.parismusees.paris.fr/) requires an account/token. Its [terms](https://apicollections.parismusees.paris.fr/cgu) permit CC0 reuse for explicitly marked images while distinguishing reserved content, and constrain unauthorized automatic extraction. No account was created and no authentication was bypassed. Published IIIF URLs in this packet are routing evidence, not fetched or approved image payloads.

CC0/CC BY-SA/public-domain labels, artwork copyright, photograph rights and database/API access are separate fields. No image binary was downloaded in this research, so none has a completed visual-quality, checksum, storage or production-rendering check.

## What remains unresolved

- The 733 art-interest museums have a national metadata inventory, not equal-depth individual research. Native targets in the 177-link index are not all tested. Private/unlabelled institutions are outside the registry census unless explicitly added as leads.
- Direct Nice PDF access returned 403; their indexed captions are identified as such. MAMAC/Grenoble/Céret Navigart routes returned JavaScript shells without readable object data. Some museum homepages timed out or rejected access. No bypass was attempted.
- Exact source-ID absence is only one deduplication signal; 35 candidate accession matches already demonstrate why it is insufficient. Work variants, panels, studies, group accessions and deposits need editorial handling.
- No inference was made that holdings imply current display. No production database, publication status, code, deployment or ingestion changed.
- The highest-impact next action is a bounded, source-reviewed image/metadata pilot for MuMa, Dieppe, Nice and Paris Musées, accompanied by museum identity reconciliation. The detailed proposed batches are in [next-batches.md](next-batches.md).
