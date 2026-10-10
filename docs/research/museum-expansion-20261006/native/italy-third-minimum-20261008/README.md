# Third Italian minimum pass — 8 October 2026

Added **242 real local artwork records**. All five museums now have at least 100 eligible works. Each addition has an exact national-catalogue identifier, source citation and accepted museum-holding assertion; all artworks remain in review.

| Museum | Added | Linked before → after | Eligible before → after |
| --- | ---: | ---: | ---: |
| Museo Nazionale di Palazzo Reale — Pisa (PI) | 60 | 64 → 124 | 60 → 120 |
| Pinacoteca Civica Alberto Martini — Oderzo (TV) | 104 | 71 → 175 | 66 → 170 |
| Museo Nazionale di Palazzo Mansi — Lucca (LU) | 39 | 99 → 138 | 67 → 106 |
| Pinacoteca Provinciale — Bari (BA) | 35 | 86 → 121 | 67 → 102 |
| Museo della Ceramica "Manlio Trucco" — Albisola Superiore (SV) | 4 | 106 → 110 | 96 → 100 |

The bounded source selection comprised 524 notices:124 Oderzo,37 Manlio Trucco,123 Bari,121 Mansi and 119 Pisa. All 524 object pages returned successfully and were reconstructed together with exact ArCo RDF responses. Six Bari graph batches hit a 10000-row truncation because a shared Address node had thousands of inverse links. The original HTTP 200 bodies are preserved. Narrower queries omitted Address-node traversal while keeping exact root, current museum/city and HTML address checks;90 object graphs were repaired. No access denial was bypassed and no failed object page retried. The [source adjustments](source-review-adjustments-001.json) document this and the custody interpretation: detenzione means custody, not ownership; an exact deposito room label at a verified museum means storage, not current display or an external loan.

The full identity screen covered 29,993 existing artworks and 61,740 citations. The final selected 274-object comparison used 18,289 artworks, adding search-only English titles and former/related maker names. It also included 111 objects in five related Pisa collection records. These were comparison scopes, not institution mergers. Original titles and school/qualified maker labels remain unchanged.

The [historical inventory audit](comparison-source-context-002.json.gz) reconstructed 637 source contexts from 166 pinned response bodies. It found four collisions invisible in the existing sparse artwork fields; two further selected paintings shared inventory 2101. All six were withdrawn before writes. The [final 242 decisions](editorial-reviewed-002.json.gz) supersede the preliminary 248. Shared-support Martini sheets, conflicting source dates, crossed illustration histories, Mansi recatalogued family trees and Pisa inventory 4456 sitter reidentifications remain outside the release.

Physical distinctions include separate Martini illustration/design sheets, four separately inventoried Massoni still-life canvases, copies versus prototypes, a preparatory cartoon versus the finished altarpiece, and panel versus canvas Sebastian paintings. Whole cycles and their components are not counted twice. Cretan and Byzantine school paintings remain first-class records without invented named creators. Explicit measurement units are retained and absent units remain unknown. Holdings do not establish current display.

**65 source/editorial holds and 217 deferred identities remain** in the [research queue](remaining-research-001.json.gz). These museums still have work toward 200. The [next-museum queue](next-museum-pass-001.json) prioritizes 231 other Italian museums below 100 eligible works. Existing source-access holds elsewhere in the campaign remain in force.

The [transaction plan](italy-third-additions-001-plan-001.json.gz) and [application receipt](italy-third-additions-001-applied.json) verify 242 artworks, identifiers, citations and holding assertions. All 426 initial target objects,3,911 scoped comparison objects and 10,456 prior campaign records were preserved. A fresh comparison ran inside the transaction. Thirteen offline checks and a zero-write replay passed;1,431 historical checks remain pinned and were not rerun. Backups are in the Artline Library backup directory. No images, painter links, publication or display claims were added; no commits or deployment.

Campaign totals: **9,913 new artworks and 785 reconciled holding links across 209 institutions**. The live audit still has **1,250 canonical museums below 100 linked artworks** and 1,389 below 200. The global goal remains active. The separate minimum 100 job is separately counted. Next work must rebase to 668 target records and 10,698 prior campaign records, not reuse this pass's 426/10,456 initial scopes.
