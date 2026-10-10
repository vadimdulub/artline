# Brest — production expansion, 9 October 2026

Added **33 production artworks in review**, taking the Musée des Beaux-Arts de Brest from **79 to 112 artworks**. All 33 new creation dates or periods are within scope. The additions comprise 29 drawings, two prints, one painting and one sculpture. The real local database remains unchanged at 79 works.

- [33 delivered artworks](added-production-artworks-001.csv)
- [All 103 source decisions](all-source-decisions-001.csv)
- [Complete production museum threshold audit](production-threshold-audit-001.csv)
- [Creation-date eligibility threshold audit](production-date-threshold-audit-001.csv)
- [Institution register with count precision](production-institution-register-001.csv)
- [Verification and remaining research](delivery-001.json)

Sources are the [museum collection website](https://musee.brest.fr/les-collections), the [national museum record M0197](https://pop.culture.gouv.fr/notice/museo/M0197), and individual Ministry of Culture Joconde object notices. All delivered records retain source identifiers, inventory numbers and literal evidence. Museum holdings do not establish current display, custody or ownership. Historical exhibitions are not treated as current display.

The bounded source selection contains 103 distinct notices: 66 were already catalogued, 33 were added, three remain source/group holds and one remains an editorial identity hold. Another 21 unique national-source records are outside this selection. The direct municipal artwork index returned HTTP 500 during preceding discovery and was not retried; the national metadata source remained accessible. No exhaustive artwork or image download was performed.

The additions include 14 Schuffenecker drawings, 11 Moret drawings and Lacombe’s 1898 mahogany relief *Autoportrait en crucifié*. The relief is distinct from its documentary photograph and the existing *Calvaire* drawing. Jourdan’s two-sided cardboard painting and Moret’s two-sided coastal sheet each count as one physical work. Moret’s similar coastal sheets retain separate inventories, studio numbers, measurements and subjects. A pastel poster design remains a drawing; Jean-Haffen’s SNCF lithographic poster remains a print.

A folded Sérusier support bearing two independently named drawings, two prints sharing one frame, and a documentary photograph remain outside this addition. Bernard’s *Maisons flamandes* remains held because a similarly sized *Les vieilles maisons* needs stronger identity evidence. Coincident inventory numbers at other museums were not merged. Existing dates and metadata were preserved, including broad dates on previously imported works. New period ranges were not shortened using artist lifespans or acquisition dates.

Twelve offline policy checks passed. Successful Cloud SQL backup 1791547970587 preceded atomic application and readback. A repeat application verified the result with zero writes. All 129 existing comparison/museum records and all 206 earlier production additions were preserved. There were no image attachments, artist-authority links, publication changes or current-display claims.

The fresh threshold audits cover all **2,135 active canonical museum records**. Catalogue counts show **1,645 below 100** and **1,913 below 200**, with gaps of **142,796** and **325,202** works respectively. Restricting to eligible creation dates gives **1,712 below 100** and **1,966 below 200**, with gaps of **147,896** and **335,840**. These are counts of direct museum links; they do not prove that each institution has enough eligible artworks available from sources.

Each audit used a read-only repeatable-read snapshot, 50 museums per query and a limit of 200 qualifying works per museum. Values below 200 are exact; 200 means “at least 200.” Larger exact collection totals were not recomputed. The live query plan uses the institution artwork index. These scoped audits replace the missing priority thresholds without retrying the earlier unbounded query, changing indexes or claiming representative 10-million-row load testing. The two audit snapshot times are retained separately.

Brest has reached 100 and needs 88 more works to reach 200. The selected production phase now totals 239 additions across Girodet, Béziers and Brest; historical local-only totals remain separate. The priority queue includes underfilled Greek, Cypriot and Russian museums, while every other canonical museum remains tracked in the full audit. The overall goal is unfinished; records will not be invented to fill quotas.

Next research starts with the Museum of Byzantine Culture in Thessaloniki, currently 31 catalogue works / 30 with eligible dates. Its official category pages yielded 11 wooden-icon and five paper-icon object links. These are leads only; two paper-icon cards share a title despite different URLs, and object pages must settle their identities. [Collection context](next-mbp-collection-context-001.json.gz) · [Icon category leads](next-mbp-icon-category-leads-001.json.gz).
