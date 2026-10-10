# Nikos Kazantzakis Museum — selected additions, 9 October 2026

Added **100 production review artworks**, taking the museum from **18 to 118 catalogue works** and **12 to 112 date-eligible works**. Both 100-work minimums are reached. The preferred 200-work target remains open: 82 more catalogue works, or 88 more date-eligible works. The real local catalogue is unchanged, with no records linked to this institution.

- [100 added artworks](added-production-artworks-001.csv)
- [All 134 object decisions](all-source-decisions-001.csv)
- [Dated museum register](production-institution-register-001.csv)
- [Verification and remaining work](delivery-001.json)

The [museum’s art collection](https://repository.kazantzaki.gr/) and its [Anemoyannis theatre archive catalogue](https://www.searchculture.gr/aggregator/portal/collections/Kazantzakis) identify holdings of the same Nikos Kazantzakis Museum Foundation. They are collection categories within the existing Myrtia institution. Holdings do not establish current display, venue, custody or legal ownership. See [institution reconciliation](institution-reconciliation-001.json).

This selection reviewed 120 theatre objects and 14 dated art objects. It adds 86 theatre design sheets, nine Kirk Hughey cover-design sheets and five Odyssey illustration sheets labelled “Hans, Enri” by the source. Ninety-five works are drawings; the five illustrations retain an unknown physical type and medium. Materials, dimensions and accessions remain unknown where unstated. Only the explicitly described pencil medium was added to one design. The 28 post-1970 objects and four correspondence records were excluded.

The original theatre creator fields say unknown, while EKT semantic enrichment names Giorgos Anemoyannis. Both statements are preserved separately, with the attribution unresolved. Dedicated object dates remain distinct from artist lifespans and depicted historical subjects. Several 1937–1938 design descriptions leave the specific production unidentified; that qualification and the catalogue date remain explicit. Native category pages repeat 2005 for several otherwise undated historical works; those dates were not used to rewrite any existing record.

One hundred and one selected low-resolution references were inspected. One object’s thumbnail was unavailable; its distinct catalogue description supports an unillustrated entry. Multi-figure sheets, attached fabric samples, reverse studies and grids of cover proposals count as one physical artwork each. Unfinished drawings remain actual artworks. Two records remain held: **34231** is explicitly a reverse of an unidentified artwork, and **34257** displays only an inscription for a costume. Their complete physical supports must be reconciled before adding another record. See [visual observations](visual-assessment-001.json). The source NC/ND image labels are retained; no new production images were attached.

Nineteen offline tests passed. Successful Cloud SQL backup **1791564596026** preceded the atomic write. Readback verified all 100 new artworks and accepted collection holdings; replay made zero writes. All 21 existing comparison records and 821 prior campaign records remained unchanged. The latter comprise 820 earlier additions and one previously linked existing work. No existing dates, images, artist links or statuses changed. The local database remained read-only.

Identity checks found no prior exact source IDs. The three additional translated-title comparators belong to Larionov, Stepanova and Bernard Rosenthal and describe different works. Scoped query plans and timings are retained; these checks are not a ten-million-row load test.

The selected production phase totals **920 additions and one existing-work link across seven museums**, separate from historical local work. Only this museum’s counts were refreshed. The priority queue now contains 232 remaining entries; that queue is not a fresh global count of all museums below 100.

[Next-source discovery](next-source-discovery-001.json.gz) contains **54 unreviewed art leads** from four public index pages sorted by ascending date. Their individual metadata still needs review. Continue from those leads, then page 5 onward if necessary, toward 200. The full museum-by-museum goal remains active.

The main Kazantzakis website archive page and Anemoyannis homepage returned 403 and were not retried. Their independent, openly linked repository and SearchCulture object catalogues supplied this research. The SearchCulture JSON link returned an HTML application error; normal object HTML supplied the preserved literal fields. No exhaustive archive or image download was performed.
