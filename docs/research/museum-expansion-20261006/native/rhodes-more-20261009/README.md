# Rhodes — further selected artworks, 9 October 2026

Added **65 production review artworks**, taking the Municipal Art Gallery of Rhodes / Museum of Modern Greek Art from **107 to 172 catalogue works** and **101 to 166 date-eligible works**. The preferred 200-work target remains open: 28 more catalogue works, or 34 more date-eligible works. The real local catalogue remains unchanged at 3 linked works, 1 date eligible.

- [65 delivered artworks](added-production-artworks-001.csv)
- [All 160 source decisions](all-source-decisions-001.csv)
- [Dated museum register](production-institution-register-001.csv)
- [Verification and remaining work](delivery-001.json)

Individual records in the [official digital collection](https://portal.mgamuseum.gr/) establish object identities and museum holdings. The prior [institution reconciliation](../rhodes-20261009/institution-reconciliation-001.json) remains applicable. Holdings do not establish current display or venue.

This batch reviewed 160 further native records: 65 additions, 1 existing exact object skipped, 64 explicit post-1970 exclusions, 27 unknown-date research leads and 3 cutoff holds (two circa1970 portraits/studies and one1970s Weaver). Across both Rhodes rounds, 280 of the portal’s reported 1502 objects have individual metadata reviewed; 1222 remain unexamined. Sixty next index leads are captured separately, without individual detail review. This is selected research, not exhaustive downloading.

New works include Semertzidis paintings and separately documented physical studies, Afro’s four1938 season panels, Ajmone’s circa1939–1941 island views, works by Asteriadis,Parthenis,Lagana,Pentzikis,Bekiari,Vakalo and Vasiliou, and selected prints. Two threshing-machine studies depict different men despite equal titles and dimensions. Composite study sheets and painted manuscript double pages count as one artwork each. No mural, complete cycle or album was added as another parent object.

Physical creation remains separate from depicted events, ancient prototypes, artist lifespans and repository dates. Asteriadis’s Ploughing retains an unknown lower bound and the explicit before1948 endpoint. A1841/1841–1842 print-publication discrepancy remains a range. Exact1970 is eligible; circa1970 and the1970s remain held. Dry-media drawings and watercolours use their documented materials while retaining the portal’s broader painting classification in source evidence.

Four selected reference images were inspected for two translated-title comparisons. Kontopoulos’s1958 museum oil differs from the existing [1959 WikiArt drawing](https://www.wikiart.org/en/alekos-kontopoulos/one-country-1959). Parthenis’s square pomegranate still life differs from the [wide WikiArt still life](https://www.wikiart.org/en/konstantinos-parthenis/still-life-1935). Images, observations and checksums are retained in [visual assessment](visual-assessment-001.json). No new images were attached and existing catalogue images were preserved.

Nineteen offline tests passed. A successful Cloud SQL backup preceded the atomic write and readback; replay made zero writes. All 235 protected existing records and 712 prior production additions remained unchanged. Identity reconciliation reviewed 8879 bounded artwork candidates,17552 citations and153 focused full-row comparators. Query plans and timings are retained; they are not a10million-row load proof. Preparation first stopped on a file-enumeration typo before any database write; the helper was corrected, its existing identical prewrite backup preserved, and tests and preflight rerun.

This selected production phase totals **777 additions across six museums**, separate from historical local totals. Only the Rhodes register row was refreshed; global counts retain their earlier observation dates. Continue Rhodes toward200 using index leads280–339,pages14–16,then page17 onward if needed. The all-museum goal remains active.
