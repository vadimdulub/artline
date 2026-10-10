# Second Italian minimum pass — 8 October 2026

Added **88 real local artwork records**, each with a primary-source citation, external identifier and accepted museum holding. **Four more museums now meet100 eligible works**. All additions remain in review.

| Museum | Added | Linked before → after | Eligible before → after |
| --- | ---: | ---: | ---: |
| Pinacoteca dell'Accademia Albertina di Belle Arti — Torino (TO) | 30 | 81 → 111 | 70 → 100 |
| Museo Civico e Pinacoteca del Palazzo Malatestiano — Fano (PU) | 26 | 113 → 139 | 78 → 104 |
| Musei Civici di Pavia | 0 | 291 → 291 | 80 → 80 |
| Galleria Estense | 27 | 122 → 149 | 83 → 110 |
| Galleria Corsini — Roma (RM) | 5 | 171 → 176 | 96 → 101 |

The bounded research selection covered893 notices:177 Estense,190 Albertina,164 Corsini,182 Fano and180 Pavia. The Italian Ministry object pages and exact ArCo RDF subject responses were captured, with891 successful page responses and two retained timeouts. Of the successful pages,159 Pavia responses were empty catalogue shells; these are not approvals. Source receipt hashes and actual SPARQL responses were independently reconstructed. An initial query exceeded the endpoint's documented10000-row sorted limit; the preserved server error was diagnosed and the corrected bounded query succeeded. No access denial was bypassed and no failed object request was retried.

The first identity scope included41,615 existing artworks and83,287 citations. The selected93-object supplemental pass used4,779 existing artworks, adding comparison-only English titles and former/related maker names from source histories. Five additional cases were deferred, leaving88 additions. A separate museum-local inventory audit reconstructed140 pinned historical source bodies and found no selected inventory collisions. Existing regional Lombardia URL aliases identified six Pavia records already in the database. Those are not duplicated.

The [editorial review](editorial-reviewed-001.json.gz) records individual physical-unit and comparison reasons. It distinguishes the two Calori Cesis portraits by canvas/panel, size and inventory; separated Scandiano frescoes; paintings copied after lost or extant prototypes; distinct Vacca theatrical sheets; and separate Fano canvases within a twelve-picture group. Vernier floor plans and structurally similar sheets remain deferred where orientation alone would not establish a separate leaf. Anonymous schools, attributed authors and workshop/manner qualifiers remain object labels. No painter authority was invented. Explicit units and frame notes are retained; missing measurement units remain explicitly unknown. Museum holdings do not assert present display.

**416 source/editorial holds and389 deferred identities remain**. These include historical external deposits needing qualified holding interpretation, empty Pavia pages, existing-object reconciliations, date/attribution issues and unresolved physical versions. The [remaining queue](remaining-research-001.json.gz) and [next-museum queue](next-museum-pass-001.json) preserve the work. Four targets meet100eligible; their200-work preference remains open. Pavia has291linked records, including80eligible; linked counts are not invented eligible dates.

The [transaction plan](italy-second-additions-001-plan-001.json.gz) and [application receipt](italy-second-additions-001-applied.json) verify88 artworks, identifiers, citations and holding assertions. All807 initial target objects,1,040 scoped comparison objects and10,368 prior campaign records were preserved. A fresh identity comparison ran inside the write transaction. Ten offline checks and a zero-write replay passed;1,421 historical checks remain pinned and were not rerun. Backups are under the Artline Library backup directory. No catalogue images, display claims, publication changes, commits or deployment.

Preparation initially stopped before writes because another workflow added the museum-browsing paragraph to AGENTS.md. The exact old text was reconstructed and its previous hash verified; the [policy supersession](policy-supersession-001.json) preserves both versions. The new instruction does not authorize invented works or change this review-only catalogue scope. All remaining prior artifact pins verified.

Campaign totals are **9,671 new artworks and785 reconciled holding links across205 institutions**. The live audit still has **1,254 canonical museums below100linked works**, and1,389 below200. The global goal remains active. The separate minimum100 job remains separately counted. Next work should start from895 target objects and10,456 campaign records, not reuse this pass's807-object initial snapshot.
