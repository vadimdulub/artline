# Museum profile review — 30 October 2026

The owner authorized review of all **2,574 remaining institution profiles**. Research was explicitly stopped after 220 updates; no process remained running. The later instruction, “ok, go ahead, try to find something else”, resumed the review with additional official sources.

This checkpoint contains **416 reviewed profiles**, including **196 completed after that pause**. The overall request remains **incomplete: 2,158 frozen targets remain**. The earlier 91 reviewed profiles are excluded from the 416. No new institutions are counted toward the frozen target.

| Source group | Profiles |
| --- | ---: |
| French Ministry of Culture Muséofile | 349 |
| Korean museums, municipal and tourism references | 16 |
| Italian museums, municipalities and Ministry of Culture | 25 |
| New Zealand museums and galleries | 26 |
| Total | 416 |

Each profile has an original two-paragraph English introduction, 41–64 words, and a reviewed city/country link. The delivery includes **155 location-link corrections**, **98 city records without inferred coordinates**, 416 citations and 11 source records. **941 atomic changes and explicit audits** were verified. Institution names, identifiers, statuses and all non-profile fields are preserved; existing venue and citation rows were checked for preservation. No artworks, makers, images, holdings, programme memberships or current-display assertions were changed.

## Sources and editorial decisions

The French register is a previously captured official CSV, independently rehashed and matched by exact museum identifier for all 349 profiles. Its metadata is published under Licence Ouverte 2.0. Selected history, collection and subject fields informed the summaries; older visitor information was not treated as current. The register is evidence about an institution, not a current exhibition checklist. No fresh native POP or museum HTTP was used.

Current operator information corrected the AP-HP museum’s older Paris address to **Le Kremlin-Bicêtre**. Independent operator pages also resolved Marly-le-Roi’s combined register locality. **Saint-Denis, Réunion** is explicitly qualified so it cannot reuse an ambiguous mainland Saint-Denis place. Country FR follows the existing French departmental grouping; no country-table changes were made. Crécy-la-Chapelle’s empty narrative fields required a separate Ministry of Culture account of the Altmann donation and the collection’s later rediscovery.

Korean full street-address place labels were replaced by city or county labels. Daegu Kansong remains distinct from Seoul, and Yeongam’s Ha Jung-woong museum remains distinct from Gwangju’s similarly named museum. Dolhareubang sculptures are described as re-creations. The Itami Jun overview does not reproduce the full audio-guide transcript.

Italian summaries distinguish academies, historic houses, research collections, specialist museums and conventional galleries. Same-city or similarly named profiles were not merged. The Bertarelli research collection is not presented as a walk-in picture gallery. Historical descriptions of Signorini Corsi, Treia and other affected places do not promise current access. An uncorroborated transfer assertion was retained only as qualified research evidence and was not adopted as a holding or location fact.

Twenty-six saved New Zealand primary homepages were matched to exact existing website hosts and independently rehashed. Selected published operator pages and council material supplemented thin homepages. Objectspace’s Auckland and Christchurch locations, McCahon’s museum and separate trust office, the Marlborough gallery’s former name, and the Arts House Trust’s exhibition loans are distinguished. No collection ownership or branch relationships were rewritten.

Direct web-tool failures were preserved as failures. Blue Oyster `/about/` returned 403 and Toi Mahara `/visit/` timed out; neither was retried. Saved successful primary material and independently published council evidence were used. Other inaccessible Korean homepage results are not represented as successful page captures. There were no new native third-party source or image requests, Storage uploads or source-policy recovery attempts.

## Verification and public availability

All 11 batches passed exact database postimage/audit checks, prior venue/citation preservation and serving-repository projection checks. **370 live museum detail responses** returned the exact reviewed description, city and country. **46 records** have no visible collection under the serving repository’s existing policy and correctly return 404. Their metadata is verified in the database; they are not counted as live description-page proofs. No memberships or access rules were changed to make an empty collection appear populated.

The final read-only snapshot verifies **507 profiles**: all 416 updates and preservation of the previous 91. It checks the exact institution, citation, source and new-place postimages and all **1,147 explicit audits** across these operations. Every saved writing transaction retains all three shared ingestion locks. Each write was applied once; completed plans, SQL, citations and audits must never be replayed.

The initial public verifier encountered an actual 404 for the empty Tourcoing collection; its original response is retained. The corrected verification distinguishes empty collections from available detail pages and reuses saved responses. A prematurely started Korean verifier stopped because the writer had not yet staged its receipt; it made no database writes. The first cumulative verifier used raw UUID objects as dictionary keys while the saved IDs are strings; its local KeyError and original script are retained. Version 2 normalizes those keys and verifies complete unique audit coverage. Neither incident caused a delivery replay.

Two pre-write clarifications preserved original drafts and plans: Bourg-Saint-Maurice’s ambiguous historical-century wording and the Réunion city qualifier. Only the clarified plans were applied.

## Files and continuation

- `target-manifest.json`: the exact 2,574 frozen targets.
- `batches/*/profiles-reviewed.json`: the curated English copy, city/country and source references.
- `batches/*/applied.json`: actual transaction, counts and lock proofs.
- Per-batch database, preservation, repository and public receipts.
- `cumulative-database-verification-v2.json`: fresh combined database and audit proof.
- `checkpoint-v1.json`: counts, remaining targets and immutable artifact pins.

Raw source captures, production preimages, complete transaction postimages and response bodies are retained outside Documents under `~/Library/Application Support/Artline/`. The delivery procedure is `ops/museum-all-profiles-20261030.py`; the combined verifier is `ops/museum-all-profiles-checkpoint-20261030.py`.

Future work starts from the **2,158 unapplied frozen targets**, with fresh identity and preimage reconciliation. Existing completed batches are immutable. Name similarity alone is insufficient: the saved preliminary matching candidates were not applied because they include different institutions, cities and countries. No agents, schedules, background readers or automatic research jobs were started. No application or infrastructure deployment was required for these data updates; the deployed museum UI and Cyprus map layer are preserved.
