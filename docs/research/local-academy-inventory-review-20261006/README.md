# Academy Vienna inventory and source-date review — 6 October 2026

Revisited the 25 remaining Academy artworks and attached eleven verified CC BY 4.0 photographs. A twelfth work, Subleyras's self-portrait, was resolved in the [separate reverse-face follow-up](../local-academy-verso-image-20261006/README.md). Thirteen records remain without an attachment: four lack an exact native painting-object match, and nine have qualified, multiple or differing source attributions.

Five attachments reconcile individually documented inventory forms such as `1430` and `GG-1430`. Exact native records, creators, subjects and dimensions support these decisions; no general prefix-stripping rule was added. Existing inventories remain unchanged. Translated titles and fuller artist names were likewise reviewed individually. Differences between source measurements remain in the evidence.

Four paintings have blank native dates and coarse object dates in Wikidata. The original precision is preserved: three identify the seventeenth century (1601–1700), and one the 1680s (1680–1689). The encoded timestamps are not treated as exact creation years. The [Wikidata date documentation](https://www.wikidata.org/wiki/Help:Dates#Precision) and its [saved capture receipt](date-precision-reference.json) establish these meanings. Acceptance requires an individually pinned object-level interval entirely before 1971 and compatible with the unchanged catalogue interval. Artist lifetimes do not fill blank artwork dates.

Other date differences remain unresolved and preserved. Weenix's Dirck Schey portrait is dated 1692 natively and 1693 in the catalogue. Nickelen's native circa-1710 date differs from the stored 1712–1755 range. Reuter's source says “after 1622” with numeric fields set to 1622; this boundary is not substituted for the existing 1662 date. Fabriano's native date field contains an activity statement for 1447–1448, retained verbatim alongside the independently sourced object date 1452. The unknown catalogue death years for Reuter and Nooms remain null; native lifespans support rights review only.

Visual inspection rejected the main Subleyras photograph because it depicts the studio face of a two-sided canvas. That image was never attached; its public derivative was removed after hash checking and preserved privately. Its exact self-portrait reverse was reviewed separately. No substitute historical photographic objects were used for the four unresolved inventories.

The eleven accepted images passed source identity, licence, photographer-credit, database, file and unchanged-catalogue checks. Seven semantic negative controls rejected missing inventory reconciliation, the other Schey portrait number, missing coarse-date evidence, a timestamp used as an exact year, a century crossing 1970, additional date uncertainty and a qualified creator despite a recomputed native checksum. The previous 76 Academy attachments also passed the revised inventory/date validator.

JPEGs are at most 99,102 bytes under `apps/web/public/assets/artworks/imported/local-academy-inventory-review-20261006/`. Originals, visual review sheets, rejected-face bytes and validation controls are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-academy-inventory-review-20261006/`; locked preimages use the matching `backups/` directory. Source captures remain in `metadata/`. All artworks retain their prior metadata, creator links, identifiers and review status. The latest HTTP check again timed out on the existing local web server. Production was not changed.

- [Eleven attachments](attached-images.csv)
- [All 25 current outcomes](artwork-outcomes.csv)
- [Individual inventory and date decisions](native-identity-review.json)
- [Exact inventory probes](inventory-probe.json)
- [Bounded broader searches](broad-inventory-probe.json)
- [Visual review, including rejected face](visual-review.json)
- [Database and file verification](verification.json)
- [Native source, rights and unchanged creator fields](native-rights-verification.json)
- [Counts](report.json)
