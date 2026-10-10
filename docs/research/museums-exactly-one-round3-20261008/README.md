# Production one-artwork museums: identity fixes and third expansion

Fresh production audit: 2026-10-08T12:16:08Z. Final verification: 2026-10-08T12:43:00Z. The fresh initial count was **248** canonical museum records with exactly one non-archived linked artwork. Several represented duplicate museum identities whose other records already held substantial collections.

Applied **10 museum alias reconciliations**, preserving the original institution records, URLs, source citations and all existing artwork metadata. Added **27 new review artworks** and linked **4 existing artwork records** across **9 further museums**. The final fresh production-wide count is **228 active canonical museums with exactly one artwork**.

[Database verification](verification.json) · [Artwork and source list](artwork-results.csv) · [Museum counts](museum-results.csv) · [Museum identity fixes](museum-alias-results.csv) · [Remaining current one-artwork museums](remaining-one-artwork-museums.json.gz).

The initial audit uses indexed institution lookups capped at two artworks, then reads only the selected records. It does not reuse old counts. Each reviewed alias connects the specific same museum and city, supported by retained official museum/government pages; separate museums, collection sites and similarly named institutions were not combined. Publication, dates, creator links, media relationships and original source identities were independently verified preserved. Both old and canonical URLs passed identical artwork API responses for all ten aliases. [Live museum overview checks](aliases/overview-api-verification.json) also confirmed the full collection counts through every old one-artwork URL.

Twelve previously unmapped museum names were individually matched to full Wikidata museum authorities, including their city and official website. Bounded museum-specific queries inspected 618 object entities and 330 creator entities. Forty-one source candidates passed full collection-statement, reference, creation-date, type and attribution checks. Production native-ID, title, creator and date checks, followed by individual version review, admitted 27 additions. The actual addition source is referenced Wikidata metadata (editorial confidence 0.85); underlying object references were not independently opened. Full statements and museum-authority evidence are retained in each new record’s citation. Unreferenced holdings, qualified dates, conflicting collections and unresolved object versions remain held.

Stone City, Iowa (painting) and Nude with a Hat were recognized as already-catalogued works, not new objects. Picasso’s Jester on horseback was matched to the existing Harlequin on the horseback: creator, 1905 date, translated subject and distinctive 100 × 69.2 cm dimensions agree. Its holding source is the referenced Wikidata statement; the fresh WikiArt page supplies identity evidence and has no Location field. RKD direct access was unavailable. Confidence is 0.90 editorial assessment.

Three other existing links use exact fresh WikiArt artwork IDs, creators, titles and explicit museum Location fields: Benjamin West’s General Thaddeus Kosciusko, Hopper’s High Noon, and Modigliani’s Portrait of Maude Abrantes. Official Hecht evidence identifies the latter as the reverse side of the canvas carrying the already-linked Nude with Hat. Both existing face records are preserved; this pass creates no additional Modigliani object and does not rewrite the existing 1907 dates to the official page’s 1908. Counts are catalogue artwork records, not an assertion that every legacy record is a separate physical canvas. Confidence is 0.95 editorial assessment.

Validation: [13 source-guard tests passed](tests.json); separate read-only checks verified every added/linked record and all ten identity reconciliations. [Live checks](api-verification.json) passed for 13 new/existing artwork URLs, plus [both museum URL forms](aliases/api-verification.json) for ten aliases. No new images, display assertions, automatic publication, local database writes, commits or deployment. Recovery: successful Cloud SQL backup 1791461266671 and locked per-record preimages under `~/Library/Application Support/Artline/backups/museums-exactly-one-round3-20261008/`.

## Existing collections recovered through museum identities

| Former one-work museum record | Existing collection before | After |
|---|---:|---:|
| Musée des Beaux-Arts de Caen | 673 | 674 |
| Musée des Beaux-Arts de Carcassonne | 164 | 165 |
| Musée des Beaux-Arts de Dole, Dole, France | 282 | 283 |
| Musée des Beaux-Arts de Nancy, Nancy, France | 122 | 123 |
| La Piscine Museum, Roubaix, France | 151 | 152 |
| Goya Museum | 261 | 262 |
| Indianapolis Museum of Art (IMA), Indianapolis, IN, US | 105 | 106 |
| Gallery of Modern and Contemporary Art (GAM), Turin, Italy | 5 | 6 |
| Bashkirian State Museum of Fine Arts (Nesterov Museum), Ufa, Russia | 1 | 2 |
| Victoria Memorial Hall, Kolkata | 200 | 201 |

## Additional catalogue coverage

| Museum | Before | Added | Existing linked | After |
|---|---:|---:|---:|---:|
| Hecht Museum (University of Haifa), Haifa, Israel | 1 | 5 | 1 | 7 |
| Virginia Museum of Fine Arts, Richmond, VA, US | 1 | 5 | 1 | 7 |
| Taft Museum of Art, Cincinnati, OH, US | 1 | 5 | 0 | 6 |
| Allen Memorial Art Museum (AMAM), Oberlin, OH, US | 1 | 3 | 1 | 5 |
| Smith College Museum of Art (SCMA), Northampton, MA, US | 1 | 4 | 0 | 5 |
| Dayton Art Institute (DAI), Dayton, OH, US | 1 | 1 | 1 | 3 |
| Santa Barbara Museum of Art (SBMA), Santa Barbara, CA, US | 1 | 2 | 0 | 3 |
| Joslyn Art Museum,Omaha, NE, US | 1 | 1 | 0 | 2 |
| Krannert Art Museum (University of Illinois at Urbana–Champaign), Champaign, IL, US | 1 | 1 | 0 | 2 |
