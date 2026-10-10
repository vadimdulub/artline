# Béziers Fine Arts — production expansion, 9 October 2026

Added **88 production artworks in review**, taking the Musée des Beaux-Arts de Béziers from **85 to 173 linked works**. Its count with creation dates within scope rose from **84 to 136**. The additions comprise 73 drawings, nine sculptures and six paintings: 52 have eligible dates, 34 retain an open “after” date, one has a questioned date and one retains a twentieth-century range crossing 1970. The real local database remains unchanged at 85/84.

- [88 delivered artworks](added-production-artworks-001.csv)
- [All 485 discovered object decisions](all-source-decisions-001.csv)
- [Production institution register](production-institution-register-001.csv)
- [Verification and counts](delivery-001.json)
- [Reviewed object identities and source evidence](editorial-reviewed-002.json.gz)

The [Ministry of Culture record M0467](https://pop.culture.gouv.fr/notice/museo/M0467) identifies the museum. The [city’s Fayet page](https://www.ville-beziers.fr/culture/musee-fayet) describes the Fine Arts collection; [Fabrégat](https://www.ville-beziers.fr/culture/centre-detude-et-de-conservation-fabregat/faq-fabregat) is a study and conservation centre. The planned future merged museum does not change current institution identities. These are holdings, without current-display or ownership claims.

Joconde returned 2,675 museum records. A bounded 400-record discovery pass followed by 200 filtered Fine Arts records yielded 485 distinct records. Of those, 83 were already present, 88 were added and 314 remain in the source/scope ledger. No exhaustive retrieval or image download was performed. Another 435 Fine Arts records remain outside this selection; their next source page is recorded in delivery-001.json. Directory coverage is not complete artwork coverage.

The new drawings include original Jean Moulin/Romanin cartoons. Their 1975 acquisition is not their creation date. Original sheets are distinct from magazine reproductions; alternative captions do not create extra artwork records. Eight recorded “vers” inscriptions retain approximate dates despite unqualified catalogue year fields. The two Bonnes Amies drawings have different inventories, dimensions, captions and publication dates.

The new Injalbert sculptures retain separate object identities: two faun heads differ in height and inventory; the two satyr busts differ from the existing 1895 bust. One bust with two faces is one object. A fountain assembled from multiple sculptures, a two-bust group, sketchbooks and loose sketchbook pages remain held pending component reconciliation. The source’s inconsistent Sylvestre birth date is preserved as a research gap. A former Louvre/Fabre portrait and nine state deposits also require identity reconciliation. No unsupported date or artwork was introduced to fill a quota.

The Delacroix Sainte Catherine was already present under a Wikidata source with the same 896.1.8 inventory and was not recreated. Benson’s proposed attribution remains qualified to the artist or his circle. Jan Bruegel’s elder/younger ambiguity remains unresolved. Anonymous and uncertain works retain object-level creator labels.

Twelve offline policy checks passed. The pinned plan used a successful Cloud SQL backup 1791546489193, atomic application/readback and a zero-write replay. Checks preserved 271 existing comparator/museum records and all 50 prior Girodet additions. The identity capture contains 3,705 existing artworks and 7,529 citations. No images, artist-authority links or publication changes were added.

Béziers still needs 27 more linked works to reach 200, or 64 more with eligible dates to reach 200 eligible works. The production phase now has 138 verified additions across Girodet and Béziers. Historical local-only campaign totals remain separate. A complete institution directory is retained, but global production counts remain unverified after earlier timeouts. This pass captured read-only EXPLAIN plans and statistics without retrying the blanket count; planner estimates are not representative 10-million-row load testing. Prior source-access holds and research queues continue from the previous checkpoint.
