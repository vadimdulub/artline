# Deep production museum research — 8 October 2026

Fresh production audit: **228** active canonical museums with exactly one non-archived linked artwork at 2026-10-08T13:48:27Z. Final independent database verification at 2026-10-08T14:50:54Z: **211**. Counts include review records and use the actual current production database.

Applied **93 new artworks**, including **11 icons**, and **6 existing-artwork museum links** across **14 museums**. Reconciled **3 additional duplicate museum identities**, preserving their records, old routes and existing artworks. This round reduced the one-artwork count by **17**. All newly created artworks remain in review.

[Database verification](verification.json) · [99 artwork additions/links and their sources](artwork-results.csv) · [Museum counts](museum-results.csv) · [Museum aliases](museum-alias-results.csv) · [All 228 cohort research statuses](cohort-research-register.csv) · [211 remaining one-artwork museums](remaining-one-artwork-museums.json.gz).

## Research coverage and decisions

Reviewed **849 selected source candidates and entity records**: 456 official Artefact museum objects, 17 QAGOMA objects, 21 Italian ArCo objects, and 355 selected Wikidata artwork candidates, with 171 associated creator entities. Also captured 25 exact existing WikiArt artwork pages for identity/link review. These counts are source records, not a claim of 849 distinct physical artworks. Museum-scoped catalogue selection preceded any enrichment; this round downloaded no artwork images.

- **Official Artefact:** reviewed two bounded catalogue index pages per museum, capped at 48 candidates across each of ten museums. Accepted 74 new records after native-ID, collection, date, type, creator/date, title-translation and version checks. Museum-scoped catalogue membership and each object’s explicit Collection field are retained with captured page hashes. Source Russian labels and anonymous icon creators remain explicit; uncertain dates retain their intervals.
- **Official QAGOMA:** 16 new records from 17 selected native pages. Preserved object numbers, accessions, own-object creator labels, original dates and acquisition credits. A discovered related-artists parsing problem was corrected before planning/delivery. The collection relationship is to the Queensland Art Gallery Board of Trustees catalogue; it does not assert display in a particular QAG building.
- **Referenced Wikidata:** 25 museum authorities reviewed by full museum name, location and official website; no institution authority metadata overwritten. Fifteen bounded object indexes were captured successfully. The SPARQL endpoint throttled further indexing, including a later retry after backoff, so it was stopped. Previously saved successful indexes supplied candidates for the separately available public entity API. Eight records met the strict referenced-collection/type/date checks; three were added and one existing Manessier work was subsequently linked with primary-source corroboration. Unreferenced or conflicting holdings remain held.
- **Italian ArCo:** 21 native candidates across five museums; six passed source checks but remained held because generic titles lacked sufficient distinct-object identity against existing records. No ArCo additions were forced through.

This round individually investigated or reconciled 44 of the 228 starting museums; the register explicitly marks **184 without individual source research this round**. Twenty-seven investigated museum entries produced no mutation, including authority-only cases whose object indexes were deferred. The remaining 211 museums are an open research backlog, not a conclusion that they lack additional eligible holdings. The preserved local catalogue audit supplied no additional approved candidates.

## Existing works linked

The six links preserve all existing creator relationships, dates, images and publication states. Three use exact WikiArt artwork IDs and explicit Location fields: Roerich’s *Beda the Preacher* and *Nastasia Mikulichna* at Novosibirsk, and Levitan’s *Dandelions* at Chuvash. The Chuvash English museum-label variant was independently reconciled with the official museum catalogue.

Mashkov’s *Cypress in the cathedral walls. Italy* (1913, 59 × 67 cm) and Grabar’s *Dugino. Sunrise* (1904, 66.5 × 88.5 cm) were matched using exact creator/date, translated titles and distinctive dimensions. Their WikiArt pages have no Location field: the actual holding evidence is the official Artefact catalogue, for Vladimir-Suzdal and Chuvash respectively. Editorial confidence is 0.90.

Manessier’s *La Passion de Notre Seigneur Jésus-Christ* (1952) was matched by the exact WikiArt URL referenced in Wikidata. The underlying [official Alfred Manessier public-collections catalogue](https://www.alfredmanessier.com/collections-publiques/) was independently opened and confirms that title, date and La Chaux-de-Fonds museum. The existing unknown dimensions were preserved. Confidence is 0.95; the other exact WikiArt Location links also use 0.95. All confidence values are editorial assessments, not calibrated probabilities.

## Identity and source limitations retained

Two Artefact records describe the same Zhukovsky *Summer Morning. Rozhdestveno Estate* (1918): identical creator, museum and 91.3 × 122.6 cm dimensions. Only one artwork was created. Its citation preserves both source records, and a separately verified secondary-source citation indexes the other exact native URL to prevent a later duplicate. The catalogue permits one external identifier per provider scheme; the additional source is correctly represented as a citation.

Fechin’s *A Bad Joke* remains explicitly identified as a study, and Myasoyedov’s *The Flight of Grigory Otrepyev* is the museum’s 1867 replica rather than the 1862 original. These version notes are saved in both source and holding evidence. New source creator labels remain object-level labels; this pass does not infer painter links.

Held cases include an illustrated-album author/creator ambiguity, conflicting Abram Yefimov/Arkhipov labels, incompatible Fechin dimensions, a Raffaelli study needing existing-version comparison, the Nicholas Mas/Nicolaes Maes portrait identity, unresolved Braque still-life identity, two-sided/version ambiguities, unsupported date intervals and works outside the creation cutoff. A Petrov-Vodkin source with an impossible early date was excluded. Every accepted creation range falls wholly in or before 1970; no unknown creation year was invented.

Hopper’s *Hotel By A Railroad* remains unlinked in this round: WikiArt says Private Collection, while referenced museum evidence names Hirshhorn. Official Smithsonian results support Hirshhorn, but direct catalogue captures returned 403; retained the discrepancy and source-access evidence for follow-up. Other sources returning throttling/security responses were not repeatedly queried. No held case is evidence that a museum lacks additional works. Full candidate decisions remain in the immutable source and final plans under `waves/`.

## Museum results

| Museum | Before | New works | Existing linked | After |
|---|---:|---:|---:|---:|
| Queensland Art Gallery (QAG), Brisbane, Australia | 1 | 16 | 0 | 17 |
| Chuvashian State Arts Museum | 1 | 11 | 2 | 14 |
| Vladimir-Suzdal Museum Reserve, Vladimir, Russia | 1 | 10 | 1 | 12 |
| Irkutsk Regional Museum of Fine Arts (Sukachev Museum), Irkutsk, Russia | 1 | 10 | 0 | 11 |
| Kursk State Art Gallery (Deyneka Museum), Kursk, Russia | 1 | 9 | 0 | 10 |
| Novosibirsk State Museum of Fine Arts, Novosibirsk, Russia | 1 | 7 | 2 | 10 |
| Museum Complex of I. Ya. Slovtsov | 1 | 8 | 0 | 9 |
| Murmansk Regional Museum of Art | 1 | 7 | 0 | 8 |
| Krasnodar Regional Museum of Fine Arts, Krasnodar, Russia | 1 | 5 | 0 | 6 |
| Kirov Regional Museum of Fine Arts (Vasnetsov Museum), Kirov, Russia | 1 | 4 | 0 | 5 |
| Dagestan Museum of Fine Arts, Makhachkala, Russia | 1 | 3 | 0 | 4 |
| Musée des Beaux-Arts de La Chaux-de-Fonds, La Chaux-de-Fonds, Switzerland | 1 | 1 | 1 | 3 |
| Frances Lehman Loeb Art Center (Vassar College), Poughkeepsie, NY, US | 1 | 1 | 0 | 2 |
| Hirshhorn Museum and Sculpture Garden, Washington, DC, US | 1 | 1 | 0 | 2 |

## Duplicate museum identities resolved

| Former one-work record | Canonical collection before | After |
|---|---:|---:|
| Galleria Naionale d'Arte Moderna — Roma (RM) | 47 | 48 |
| National Gallery of Ancient Art (GNAA), Rome, Italy | 142 | 143 |
| National Gallery of Umbria (Palazzo dei Priori), Perugia, Italy | 19 | 20 |

The Rome modern-art spelling error, English Rome ancient-art collection name and English Perugia museum name were each reconciled against retained official museum pages. Separate venues and storage/deposit institutions were not merged. Existing artwork metadata, source IDs, images and publication states were verified preserved.

## Validation and recovery

**25 source-guard tests passed** ([12 native-source guards](native-tests.json), [13 Wikidata guards](wikidata-tests.json)). Independent read-only SQL verified every new record’s exact source facts, source identifiers, citation body, eligible creation interval, review state, museum holding and absence of publication/display mutations. The existing-artwork link verifier checked all six complete preimages and relationships. Alias verification preserved all three existing objects and their source/media relationships.

[Live artwork API checks](api-verification.json): **20 passed**, covering one new work in every expanded museum and every existing-artwork link. [Live museum overviews](overview-api-verification.json): **17 passed**, including all three former one-work alias routes. Both old and canonical artwork URLs also passed the [three alias comparisons](aliases/api-verification.json).

Production writes used the shared curated-ingestion advisory lock, row/preimage/source checks and guarded transactions. Recovery evidence includes successful Cloud SQL backup **1791461266671** and exact transaction preimages under `~/Library/Application Support/Artline/backups/museums-exactly-one-deep-20261008/`. No local database writes, image changes, automatic publication, current-display claims, commits or deployments. Baseline `snapshot-comparison.json` is retained as inherited historical bookkeeping against round 2; the fresh baseline and final verification above are the authoritative counts for this round.
