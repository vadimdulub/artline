# Cyprus painters: selected import, 14 September 2026

Completed in **both local and production databases**: 7 artist profiles, 36 artworks, 3 verified public-domain images, and the missing CY country reference. Six profiles are Cypriot painters; Theodore Apsevdis is explicitly recorded as a Constantinopolitan painter active in Cyprus. These relationships remain distinguishable.

[Open Cyprus in Artline](https://artline-web-lpuqqlugnq-ew.a.run.app/?country=CY&popular=false). Popularity must be disabled to include these research additions. Loukia Nicolaides-Vassiliou also appears with the Women artists filter.

| Artist | Artworks | Cyprus relationship |
| --- | ---: | --- |
| Ioannis Kissonerghis | 8 | Cypriot cultural affiliation |
| Adamantios Diamantis | 8 | Cypriot cultural affiliation |
| Loukia Nicolaides-Vassiliou | 1 | Cypriot cultural affiliation |
| Solomos Frangoulides | 8 | Cypriot cultural affiliation |
| George Pol. Georghiou | 8 | Cypriot cultural affiliation |
| Vasilis Michaelides | 1 | Cypriot cultural affiliation |
| Theodore Apsevdis | 2 | Cyprus activity; Constantinopolitan painter |

All new artists and artworks remain **in review**; all new artworks are research candidates. Ten works retain unknown creation dates. Museum catalogue exhibitions, source collection labels and accepted holdings are distinct: this import created only review holding assertions, no accepted holdings, no on-view claims, and no publication. No artist was made popular merely to appear in the default filter.

## Selection and sources

The [A. G. Leventis Gallery's Cypriot artist catalogue](https://cypriotartists.leventisgallery.org/) supplies primary artist profiles and object-level museum/exhibition connections. The public website exposes these through unauthenticated read endpoints (POST requests used by its own JavaScript application); response bytes, request bodies and checksums are retained. No authentication credential was required. Biography prose was not copied into the app; concise descriptions, factual fields and source citations were added. Up to eight works per modern painter were selected; 20 remaining entries are held outside this delivery for later research or date/scope reasons.

[Vasilis Michaelides's Madonna and Child](https://www.wikidata.org/wiki/Q22661822) is linked to the State Gallery collection and the Europeana 280 selection. The [Commons reproduction](https://commons.wikimedia.org/wiki/File:Madonna_and_Child_-_Vasilis_Michaelides.jpg) has explicit public-domain evidence. Wikidata's 1875 time statement includes five years of forward uncertainty, so the database retains 1875–1880 rather than inventing an exact date. The Commons page displays 1875. The [Limassol municipal museum guide](https://www.limassol.org.cy/uploads/History-Center-pdfs/08dd27d8eb.pdf) corroborates Michaelides's painting activity; the [official State Gallery listing](https://www.visitcyprus.com/discover-cyprus/culture/museums-galleries/state-gallery-of-contemporary-art/) establishes the institution identity.

[Cyprus Tourism documents Apsevdis's work in Cyprus](https://www.visitcyprus.com/discover-cyprus/routes/religious-routes/monasticism-and-asceticism-route-e-religious-route/) and explicitly describes him as Constantinopolitan. His numeric birth/death years are left empty; the timeline uses the documented 1183 work date. The two Commons mural details retain their supplied names, attribution and dates in review; no precise current museum location was invented. They are labelled as mural details, not complete mural-cycle reproductions. The disputed Virgin-and-Child/Araka attribution was not imported.

The bounded Wikimedia discovery also checked Giovanni Kyprios, Onouphrios and other Cypriot painter authorities. These searches are evidence of leads, not proof of exhaustive coverage; no identity was fabricated when the exact object or image remained unresolved.

## Images and remaining gaps

Three source-framed JPEG derivatives were visually inspected: Madonna and Child, Fresco of a Saint, and Fresco of Joseph. Each is at most 100,000 bytes (largest: 99,973), with original SHA-1 verification, retained SHA-256 checksums, source credits and per-file rights evidence. The originals and recovery dump are kept under the dedicated Artline backup directory. The served assets are present locally and in Cloud Storage.

The 33 modern artworks have museum image URLs preserved in citations and the inventory, but no downloaded image attached. A museum's displayed image does not itself grant reuse rights. The two Kissonerghis Commons photos identify the uploader as photographer and give a photo licence, without documented clearance of the underlying painting; those reproductions were held. No modern painting was assumed public domain solely because a Commons page exists. Some artwork dates are also unknown and need review before any image download.

![Selected reproductions; two right panels are mural details](contact-sheet.jpg)

## Verification and recovery

- Read-only identity planning checked source IDs, names/aliases and relevant artwork source URLs against both real catalogues. No test database or test fixture was created.
- Local recovery archive: `local-before.dump`, checked with `pg_restore --list` and SHA-256 before writing. Cloud SQL backup `1789369991390` completed successfully before import.
- Each target used one atomic database transaction, a shared ingestion lock and identity rechecks. Cloud images were uploaded conditionally and byte/checksum verified before committing media references.
- Read-only final verification proved exact parity for these seven artists, 36 artworks, creator links and women evidence. This is scoped parity, not a claim that all unrelated catalogue data are globally synchronized.
- All three live image URLs returned matching bytes. The production Cyprus timeline returned seven painters with popularity disabled; the Cyprus Women filter returned one.
- Eight date-parser cases passed without any database access. Artwork detail smoke tests are recorded separately in `public-api-verification.json`.
- No app source release, infrastructure change or commit was needed. The existing production application renders the new database-backed country and records.

Exact rows: [artwork inventory](artwork-inventory.csv). Immutable application plan, checksums, approval-by-agent quality review, per-target receipts and verification snapshots accompany this report. The user had already authorized additions to local and production databases; image QA is an internal preparation check, not an additional permission request.
