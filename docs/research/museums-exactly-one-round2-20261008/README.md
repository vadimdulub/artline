# Exactly-one-artwork museums: round two

Fresh production selection 2026-10-08T11:04:47Z: **263 museums** had exactly one non-archived linked artwork, including review records. Verified 2026-10-08T11:29:09Z: **91 new artworks and 4 existing-artwork links across 15 museums**. All new artworks remain review.

[Museum before/after counts](museum-results.csv) · [Every artwork and source](artwork-results.csv) · [Database verification](verification.json) · [19 passed source-validation tests](tests.json).

Separate read-only production checks verified all 95 changes against their saved plans. [Live API checks](api-verification.json) passed for one added artwork in each of the 15 expanded museums, with HTTP 200 and the expected title.

The collection research covered 22 previously unqueried museum authorities, with bounded index pages and 555 new object entities inspected. Full creator, creation, object-type, collection-statement and reference checks produced 98 source candidates. Production native-ID, inventory, title and version checks admitted 83 new works; conflicting holdings and unresolved title collisions remain held. The actual source is referenced Wikidata metadata, with full original statements retained; underlying referenced documents were not independently opened. Confidence is 0.85 editorial assessment, not calibrated probability.

Eight additional works use fresh official Crocker catalogue pages, with agreement between visible fields and embedded native metadata. The sample covered two 12-object collection pages and selected eight exact-year paintings/drawings. Official purchase and collection credit lines support holdings, not current display. Source labels, inventoried physical objects, creator names, medium, dimensions and creation dates are retained. A Percy Gray drawing dated 1907 and a Claude Lorrain drawing dated 1635/1636 share A Rocky Hillside but have different inventories and institutions; the retained production comparison resolves the collision without altering the Chicago work. Crocker confidence is 0.95 editorial assessment.

Four existing-artwork links use exact artwork/creator authorities and referenced collection statements qualified only by past collection start or inventory. The Carisbrooke painting retains unknown creation dates: 1950 is collection-start evidence and was not copied into creation fields. Three separately inventoried Tucson paintings retain their literal title Unknown and 1920 dates; distinct native object IDs and inventories establish their identity without invented titles. Direct PastPerfect access was unavailable; actual source attribution remains Wikidata. Existing titles, dates, creators, images and publication states were independently verified preserved.

At verification **248 museums** in this snapshot still had exactly one artwork. Source gaps and holds remain research work; they are not evidence that eligible holdings do not exist. Concurrent catalogue changes, if any, are separate CSV deltas and excluded from this round's totals. No image downloads, display assertions, local database writes, publication, commits or deployment.

Recovery uses completed Cloud SQL backup 1791456055193 and exact locked transaction preimages under `~/Library/Application Support/Artline/backups/museums-exactly-one-round2-20261008/`. Shared ingestion locking was respected while another production import completed.

| Museum | Before | Added | Linked | After |
|---|---:|---:|---:|---:|
| Tucson Museum of Art | 1 | 23 | 3 | 27 |
| Huis Van Gijn | 1 | 19 | 0 | 20 |
| National Coal Mining Museum for England | 1 | 12 | 0 | 13 |
| Crocker Art Museum | 1 | 8 | 0 | 9 |
| Carisbrooke Castle | 1 | 6 | 1 | 8 |
| Blake Museum | 1 | 5 | 0 | 6 |
| Sorolla Museum | 1 | 5 | 0 | 6 |
| Auld Kirk Museum | 1 | 3 | 0 | 4 |
| Abelló Museum | 1 | 2 | 0 | 3 |
| Leominster Museum | 1 | 2 | 0 | 3 |
| Wrexham County Borough Museum | 1 | 2 | 0 | 3 |
| Museu Episcopal de Vic | 1 | 1 | 0 | 2 |
| Museum of the French Revolution | 1 | 1 | 0 | 2 |
| Prittlewell Priory | 1 | 1 | 0 | 2 |
| Tyntesfield | 1 | 1 | 0 | 2 |
