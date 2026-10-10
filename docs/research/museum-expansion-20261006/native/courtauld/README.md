# Courtauld selected artwork expansion — 7 October 2026

Added **90 real artworks to the local review catalogue**, bringing The Courtauld Gallery from 16 linked/15 eligible works to **106 linked/105 eligible works**. All 106 linked entries remain in review and have distinct normalized inventory numbers. The 90 additions have original native object evidence, eligible production dates and accepted museum-holding assertions; no images, artist links, display claims or publication changes were made.

[Full read-back](minimum-100-verification.json) preserves all 23 pre-existing linked/pending artwork rows and their 32 citations, 23 artist links, 13 media links, 23 identifiers and 23 location assertions. Counts do not newly validate all 16 legacy physical-object identities, and the older unknown creation date remains unknown. [Replay](replay-001.json) inserted zero rows.

## Evidence and selection

The [official collection entrypoint](https://courtauld.ac.uk/online-collections/) links to the [gallery catalogue](https://gallerycollections.courtauld.ac.uk/), separately from its photographic collections. Four artist-sorted painting pages contain 208 index entries from a reported 612. The bounded pass retained 196 P-prefixed native object records; twelve LP-prefixed loan index entries remain separate. Only metadata HTML was requested. Read-only public search/sort POSTs are retained with their source forms and HTTP receipts.

[Captured selection](selected-capture-001.json.gz), [current facts](native-candidates-002.json.gz), [database identity scope](native-identity-002.json.gz) and [comparisons](native-comparisons-002.json.gz) retain the full source chain. Creator identity search covers 598 artist rows, 2,502 aliases, 672 artist IDs, 21,103 scoped artwork rows and 16,923 artist links. These are discovery and deduplication scopes, not artist-link approvals or a ten-million-row performance test.

The second facts snapshot separates explicit artist lifespan/activity lines from maker labels while preserving them as evidence. The initial facts/identity snapshots and initial parser are retained. Actual names in submit-button values, plain-text names, absent maker fields, workshop/copy/forgery/former-attribution labels and multiple makers remain distinct. Production dates never come from maker lifespans, acquisition years or prototype dates.

[Ninety reviewed decisions](editorial-reviewed-001.json.gz) approve exact objects at 95% editorial confidence, an assessment rather than a calibrated probability. The additions include Gounaropoulos’s circa 1925–1926 still life, Barnaba’s signed Byzantine-influenced panel, Bell’s 1944 Duncan Grant study, three Degas paintings, seven Etty life studies and eleven separately inventoried Teniers reproductive studies. Three multi-panel parent accessions are counted once. Child views are excluded and recto/verso subjects remain under one inventory. Giunti’s circa 1920–1929 forgery remains explicitly qualified and is not treated as a Renaissance Botticelli.

The [applied plan](courtauld-native-additions-001-plan.json.gz), SHA-256 `caefaa8c6c9b30564d8c571516df51a18e4462cf8950904c155a64f41c647168`, pins original HTML, HTTP receipts, metadata, decisions, scripts and policy. The transaction rechecked the complete existing museum scope and database identity snapshot before writing; its [receipt](courtauld-native-additions-001-applied.json) records full verification. Preimages and reviewed-plan backups are under `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-expansion-20261006/`.

## Remaining research

[Follow-up queue](followup-queue-001.json.gz): 106 unadded retained objects, comprising 30 component/grouping holds, 17 source holds, 13 editorial holds, 5 existing-identity leads and 41 further identity reviews. Twelve loan index leads are preserved separately. They are research leads, not import approvals.

Specific holds retain the reunited Blanchard fragments; Garofalo and Daddi existing-version leads; a Bassano prototype-name conflict; the German 19th-century copy labelled 1550; a Gotlib production/provenance conflict; Gainsborough’s later completion; source-contaminated provenance; missing objects; absent makers; and dates beyond or crossing 1970. Refresh identity comparisons before further writes because the 90 additions change that scope. Public pagination state may expire and should be rediscovered from retained official forms when needed.

The museum meets the requested minimum and needs 95 additional eligible records for the preferred 200. The all-museum goal is unfinished. Campaign [wave 40 verification](../../verification-after-wave-40.json) records 4,266 additions and 765 existing-artwork links. All 486 offline museum-expansion tests passed, including 20 Courtauld tests, without catalogue fixtures or a test database.
