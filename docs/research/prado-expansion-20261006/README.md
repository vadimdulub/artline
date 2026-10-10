# Prado paintings expansion — 6 October 2026

Verified production result: **7,130 Prado catalogue records, 3,430 with images**, at 2026-10-06T14:19:27Z. **234 of the original 295 image gaps are filled; 61 remain.** This report records completed deliveries and the remaining object-level research and download limits.

The paintings expansion added **6,515 distinct paintings**: 6,517 rows were created, then two source-proven duplicate imports were archived and their references consolidated into existing illustrated records. No records or images were deleted. All 7,129 selected source paintings have exact museum-native identities in production and remain in review. One pre-existing D007473 drawing record is retained outside this P-inventory selection.

## Source scope

The [independent March 2026 snapshot of Prado catalogue pages](https://zenodo.org/records/19261880), published 27 March 2026, contains 23,002 objects and 7,141 unique P-inventory painting records. **7,129 selected paintings are accounted for; 12 explicit post-1970 Ramón Gaya paintings are excluded.** This is an independently archived scrape, not an official export or a fresh complete museum inventory. The [museum describes approximately 8,000 paintings](https://www.museodelprado.es/actualidad/noticia/el-bsc-y-el-museo-del-prado-ensean-a-la-ia-a/b3e3e805-5beb-cdda-f1a3-ddb4191be5ec); this pass does not establish coverage of that entire holding.

The [complete painting inventory](all-paintings.md) preserves Spanish titles, literal dates, creator qualifications, inventory numbers and per-object official links. Missing dates and unknown/qualified creators remain explicit; no artist authorities or years were invented. A museum collection connection does not imply current display or physical whereabouts.

## Images delivered

| Source | Newly attached images |
|---|---:|
| WikiArt | 46 |
| Independently licensed Commons files | 70 |
| Prado-origin reproductions under explicit user approval | 3,044 |
| Total in this expansion | 3,160 |

The original 253 illustrated Prado records were preserved. Metadata reconciliation also brought 17 already illustrated records into the Prado collection, giving 270 before these image attachments. Every attached derivative is proportionally resized without cropping and at most 100,000 bytes; source originals are archived outside Documents. All attached public image bodies were checksum-verified before their database attachment. Source labels and credits are preserved individually.

The user explicitly approved WikiArt across all project source/image-use policies and extended that collection/display policy to Prado-origin images. [Policy](../../ARTLINE_IMAGE_USE.md) · [Prado authorization](prado-image-authorization.json). Museum-origin images are stored as `restricted`, with the museum terms and separate Commons labels retained; user approval is recorded separately from source rights claims.

[Per-painting image outcomes](image-outcomes.md) and [all original-gap decisions](original-gap-outcomes.md) distinguish attached images, existing images, object/source review and pending downloads.

The initial museum selection and five reviewed addenda contain **3,169 distinct matched artworks**. **3,046 selected files were prepared and visually reviewed**: 3,044 were attached, the already illustrated Jovellanos record kept its existing WikiArt image, and the Fra Angelico predella candidate was held because it shows only one scene. A separately inspected Teniers kitchen candidate remains held because its source identifies another copy. Superseded crops and unused candidates were archived outside the application asset directory; [archive receipt](unused-derivative-archive.json).

**[123 selected files remain pending download](pending-image-downloads.md)** after bounded retries and provider rate-limit pauses. The original source URLs, preparation events and resumable selection are preserved in the [preparation inventory](museum-image-delivery/final-selection-preparation-outcomes.json.gz). Image-host limits were respected with persisted Retry-After pauses and a shared request queue. These files are not counted as attached images. Direct WikiArt access also returned an access denial during the follow-up; cached captures and indexed sources were preserved, without bypassing the restriction.

## Reconciliation and verification

Exact Prado object IDs take precedence over duplicate Wikidata authorities. P002046 / Jacob’s Journey and P006808 / Asturias were consolidated using explicit museum accession/native links in the existing image records, with corroborating creator/dimension evidence. [Consolidation plan](duplicate-consolidation/plan.json.gz) · [application receipt](duplicate-consolidation/applied.json). Distinct Alfonso XIII portraits P008071/P008072 and La Sabiduría study/large work P007728/P008170 remain separate despite overlapping titles or authorities.

The [latest integrated verification](latest-verification.json) checks all 7,129 exact source identities, original catalogue metadata and existing images, newly attached media/rights records, archived duplicate outcomes, source citations and representative live artwork API responses. There are no new display claims or publications. The real local database was not modified.

Production recovery backup **1791286791075** succeeded before import. Plans, locked preimages, after-images and recovery evidence are under `~/Library/Application Support/Artline/backups/`. Originals and visual review sheets are under `~/Library/Application Support/Artline/source-images/`. [Metadata verification](metadata-verification.json) · [latest per-painting outcomes](verification/20261006T141927Z/all-painting-outcomes.json.gz).

Nine offline import tests passed, including conservative date parsing, creator qualification, shared-authority and multipart inventory cases. Scoped native-identifier and bounded museum-page query plans are retained with each integrated verification. No ten-million-artwork load test was performed. Direct museum-page access and the in-app browser had access/runtime limits; source snapshots, indexed museum pages, public API and public image responses supplied the evidence. No commit, deployment or local fixtures were created.
