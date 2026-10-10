# All museums: minimum 100 artwork campaign

**In progress.** Latest production verification: 2026-10-07T15:24:05Z. The initial audit found **1,271 canonical museum records below 100 artworks**, with a shortfall of 113,077. This is catalogue coverage, not a claim that every museum has 100 eligible physical objects. Unreconciled museum identities remain research gaps.

Verified production additions: **23,636 new artworks** and **7,473 existing-artwork museum links**. **178** initial targets now have at least 100 linked records; **1,093** remain below 100, with **88,595** further links/additions needed. Source research remains incomplete.

Aargauer Kunsthaus now has **115 linked artworks**, **115** with eligible dates, and **2** with existing images. Its initial count was one. Official native object pages and catalogue index agree on selected titles, creators, dates and museum credits; incoming loans and unresolved entries were held. The Anker *Kinderbegräbnis* was reconciled to the existing *Child funeral* record using WikiArt's original-title field, creator/date and museum, rather than duplicated.

[Complete initial museum gap list](all-museums-below-100.csv) · [Live campaign register](all-museums-progress.csv) · [Latest database audit](progress.json). Each source wave retains selected source bodies, hashes, original retrieval dates, duplicate holds and pinned plans. Transaction preimages are under `~/Library/Application Support/Artline/backups/all-museums-minimum-100-20261006/`.

New artwork records remain in review. Existing dates, images, creator links and publication states are preserved. Holdings do not assert current display. This operation has not imported new images or written to the local catalogue. The previous 1,813-work, 50-museum batch is separate and remains in production.

Continuation: [worker status](jobs/continuation-20261007/status.json), [execution log](jobs/continuation-20261007/worker.log). The worker processes bounded museum-specific Wikidata and official Italian catalogue batches, checks pinned script hashes and object versions, commits reviewed plans and repeats this production audit after every wave. A source-pass finish with remaining gaps is not campaign completion. Source denials, changed scripts, conflicting versions and failed verification stop the affected work and preserve evidence.
