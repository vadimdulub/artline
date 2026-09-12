# Source lanes and bounded gaps

Access date: 2026-09-09. Prior v1/v2 inventories and their source hashes reused.
This log supplements the object-level claim/source ledger, not a publication grant.

## Discovery and reconciliation

- NG lane: cached 18 previous queries; 16 nonzero caches reused, empty Cézanne and
  Turner caches preserved and replaced only in a NEW version directory with two
  exact-name responses. Parent independently retrieved the corrected responses.
  251 candidates, 86 initial selections, 165 decisions in `ng/decisions.json`.
- Source aliases: Caravaggio = Michelangelo Merisi da Caravaggio (maker PID
  0P3P-0001-0000-0000); Degas = Hilaire-Germain-Edgar Degas
  (0PIW-0001-0000-0000); Cézanne = Paul Cezanne (0P84-0001-0000-0000);
  Turner = Joseph Mallord William Turner (0PNY-0001-0000-0000). Evidence:
  official artist pages and documented API, native parent refs turn354view0-3;
  worker turn353view0, turn355view1/turn356view1. Current direct Artist role and
  historical=false required. These attribution-display values are names, not `by`.
- NG6700: first Overall entry empty; second displayed measurement 96 x 121.2 cm.
  Source response preserved; official 22 March 2024 acquisition announcement
  corroborates it (parent turn406view0, turn415view2). Older 95.5 x 121 alternative
  is noted, not averaged. One regression test covers the empty-entry parser case.
- NG224 deferred after parent object check (turn399view0/turn406view1). Initial
  selection has too-narrow numeric bounds for the literal possible 1540s start.
- NG formal policy/docs, publisher National Gallery, undated pages:
  https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api
  https://www.nationalgallery.org.uk/documentation/ngacuk/licences
  Native refs turn324view0, turn324view2. Confidence high, publicly documented
  endpoint; no image grant conflated with structured metadata CC0.
- Orsay lane delivered 30 exact objects across 15 artists: 29 Orsay-held, one
  Grenoble deposit. Object facts/URLs/native refs in `orsay.json`; final source
  update corrections are reflected in the immutable inventory. Three follow-ups:
  Degas1147 turn412view0; Manet904 turn412view1; Millet342 turn412view2, all updated
  2026-09-07. Card Players1312 parent returned 09-07 versus worker's 09-04; parent
  timestamp retained. Unknown update dates remain unknown, not access date.
- Parent critical checks: Card Players date (turn365view0); Van Gogh usufruct and
  separate canvas identity (turn365view1/turn399view2); Pissarro Grenoble deposit
  (turn414view0/turn415view0); Corot Louvre responsibility/Orsay conservation
  (turn414view1/turn416view0). Courbet RF325 indexed primary details and 09-04
  modification timestamp independently returned in turn414search0/1. Identity
  confidence high, access confidence medium; no further direct retries.
- Grenoble institutional geography: Musée de Grenoble, city museum, Grenoble FR.
  Official visitor page https://www.museedegrenoble.fr/1931-informations-pratiques.htm
  (turn414search3) and legal notice https://www.museedegrenoble.fr/2088-credits-et-mentions-legales.htm
  (turn414search5); undated, accessed 2026-09-09. No opening times/ticket prices
  imported. Painting publisher remains Orsay, separate from holding institution.
- Orsay policy, EPMO publisher, undated:
  https://www.musee-orsay.fr/fr/mentions-legales (turn365view2/turn399view3).
  Not an established open metadata/image licence; private local factual review
  only. Publication/commercial reuse requires separate assessment.

## Exclusions / remaining gaps

- 54 NG earlier-inventory matches; 21 date-review deferrals; seven joint-custody
  deferrals; three medium-review deferrals; 37 not accessioned main-collection
  pictures; 43 non-exact/qualified creator hits. Manual NG224 adds one deferral.
- Orsay Olympia712: FR403 and one EN403, excluded. Corot41: FR429 and one EN429,
  excluded. No repeated unchanged requests. Courbet924 FR timeout/EN403; accepted
  only as disclosed indexed-primary evidence after independent technical read.
- Wrong objects excluded: Gauguin bronze15293 and engraving262316; Signac
  pencil/watercolour201321 with undetermined date; photographic reproductions
  after Cézanne60078/31924, Renoir285943, Monet23216; Gachet drawings215796/201246.
- Prior Orsay1010/RF1676,715/RF1984164,379/RF2735 excluded. Jeunes filles au piano
  RF755 and Gare Saint-Lazare RF2775 remain distinct from other museum versions.
- No current masterpiece-list designation was established in this lane. Historical
  exhibition wording was not promoted to a live display or current curated list.
- Brief SMK technical preflight: existing KMSr171 core endpoint still works and
  Swagger UI is available (turn324view1); no new SMK objects in this supplement.
  Core curator data remains separate from AI enrichment. No broad new crawl.

Stop condition: 115 supported additions assembled and imported; important creator,
date, dimensions and custody distinctions resolved or explicitly bounded. Further
institutions/loans/pastels need separate evidence review. No claim to all museum
holdings or permission to republish copyrighted narrative/reproductions.
