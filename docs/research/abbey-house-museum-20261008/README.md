# Abbey House Museum — 8 October 2026

**Production now has 18 Abbey House Museum artworks, up from one.** The user's
request to “add more artworks and connect existing ones”, followed by “go ahead”,
authorized this selected catalogue expansion and reconciliation.

| Result | Count |
| --- | ---: |
| New artwork records | 15 |
| Existing artworks newly linked to the museum | 2 |
| Previously linked artwork enriched | 1 |
| New links to existing painter records | 2 |
| Museum artwork records verified in the database and live API | 18 |
| Anonymous/school records retained in discovery outside this selection | 8 |

The existing works newly linked are **The Dyeworks, Rawdon, Leeds** by Ernest
Forbes and **Kirkstall Abbey, Leeds** (1793). The previously linked **Kirkstall
Abbey by Moonlight** by Walter Linsley Meegan received missing medium and size
details. All three retained their existing titles, dates, creator links, images
and publication states. Only empty accession, medium and dimensions fields were
filled. New records include paintings attributed to Johann Baptiste Bouttats,
Joseph Rhodes's views, Philip Naviasky's *Solomon Wolfson*, Frederick Morgan's
*Marguerites*, and works with supplied creator labels for Charles Nicholson,
Clarence Henry Roe, W. J. Crampton, F. Carl, L. Nitra and John Senior.

All 18 records remain in review. Nine retain unknown creation dates; those works
are not automatically classified as eligible before 1970. Four qualified
attributions are preserved explicitly. Two new works link to verified existing
Philip Naviasky and Frederick Morgan records; thirteen new works retain their
supplied creator labels without inventing painter identities or biographies.
The two paintings called *Sailing Boats at Sea* remain separate objects because
their accession numbers end in `.0007` and `.0006`.

The scope is catalogue data and museum connections. The existing WikiArt image
for the 1793 painting was retained; no new application images were uploaded.
Seven Commons image-metadata records are retained as research leads, not image
delivery receipts. A single museum-derived reproduction was archived privately
to compare the 1793 painting with its existing image.

## Sources and identity decisions

The [official museum page](https://museumsandgalleries.leeds.gov.uk/abbey-house-museum-trlc)
confirms the institution. The collection discovery used a bounded query for
explicit [Abbey House Museum](https://www.wikidata.org/wiki/Q4664027) collection
claims, followed by full object entities with accession numbers, titles,
qualified source dates, creator labels and Art UK object references. The actual
captured catalogue source is **Wikidata**, with Commons metadata where available.
The direct Art UK venue returned HTTP 403, and two public Museum Data Service
searches returned no matches. Original Art UK references remain in citations
and identifiers; this report does not claim a fresh direct Art UK catalogue fetch.

The museum connections have 90% editorial confidence from explicit collection
claims, exact inventories and object references. The 1793 painting has 99%
object/holding confidence after visual comparison of the same ruins, figures,
river, livestock and composition in the existing WikiArt image and the Art UK
reference. These are editorial assessments, not calibrated probabilities.
Holdings do not imply current display. The museum's official article mentioning
a Herkomer portrait in a temporary exhibition was not used to infer ownership.

The 1793 painting's creator authority requires separate reconciliation: the
existing record links William Williams (1727–1791), while the museum-derived
source names William Williams of Norwich (1727–1797). Object identity is secure;
the existing creator assignment was preserved and the discrepancy recorded in
the database citation. Morgan's source birth year also differs from the existing
artist record, although its explicit Wikidata creator identity agrees. No artist
biography was rewritten.

Six other title/version candidates were excluded and verified unchanged. They
include Carl Haag's *On the alert* (1876), other artists' *Marguerites*, a 1952
*Kirkstall Abbey*, and Meegan's separate moonlight painting with accession ending
`.0002`. Accession namespaces and creator identities prevent title-only merges.

## Verification and recovery

The transaction created 17 accepted holding assertions and 18 source citations.
All 18 objects have their exact Wikidata and Art UK identifiers. A fresh database
read checked all artwork fields, creator links, holdings, identifiers and image
associations against the pinned plan; all 18 live museum artwork API checks
passed at **10:30:52 UTC on 8 October 2026**. Existing publication states and
the six unrelated candidates were preserved. The local database was read only.

Cloud SQL backup **1791455220484** completed before production writes. Locked
preimages and committed after-states are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/abbey-house-museum-20261008/`.
The comparison images, procedure, logs and report archive use the matching
`source-images/abbey-house-museum-20261008/` directory. Actual ID/institution-scoped
queries and an execution plan are retained; this is not a 10-million-row load test.
No application deployment, git commit or local catalogue fixtures were needed.

- [Delivered artwork list](artworks.csv)
- [Pinned plan checksum](plan-pin.json)
- [Source object records](source-records.json)
- [Committed production receipt](applied.json)
- [Database and live API verification](verification.json)
- [Successful production backup](cloud-sql-backup.json)
- [William Williams comparison source](williams-comparison-reference.json)
- [Initial production state](production-baseline.json)

The procedure is `ops/enrich-abbey-house-museum-20261008.py`. The apply phase
already committed and must not be repeated. Immutable source captures and the
full plan are stored alongside this report.
