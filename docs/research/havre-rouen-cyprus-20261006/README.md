# Le Havre, Rouen and Cyprus museum data — 6 October 2026

Completed the user's request: “check havre museum and ruan museums and cyprus museums, find and upload data.” Havre and Ruan were interpreted as Le Havre and Rouen. Delivery targets the production catalogue; the real local catalogue was audited read-only.

**208 new artworks, 24 existing metadata updates, 68 links to existing painters and 71 uploaded images.** There are **235 distinct changed artwork records**, including 3 existing records changed only by their new images. All remain unpublished review records. Added 223 source-backed holding assertions, one museum (CVAR), and Nicosia place links for the existing Leventis and State Gallery institutions. No new current-display assertions were made.

| Museum | New artworks | Existing metadata updates | Painter links added | Images added |
| --- | ---: | ---: | ---: | ---: |
| MuMa, Le Havre | 53 | 9 | 35 | 0 |
| Musée de l'Ancien Havre | 1 | 0 | 0 | 0 |
| Musée des Beaux-Arts de Rouen | 40 | 0 | 16 | 3 |
| Musée national de l'Éducation, Rouen | 27 | 0 | 0 | 0 |
| Musée Flaubert et d'histoire de la médecine, Rouen | 8 | 0 | 0 | 0 |
| Centre of Visual Arts and Research (CVAR), Nicosia | 79 | 6 | 17 | 68 |
| A. G. Leventis Gallery, Nicosia | 0 | 5 | 0 | 0 |
| State Gallery of Contemporary Cypriot Art, Nicosia | 0 | 2 | 0 | 0 |
| Bank of Cyprus Cultural Foundation, Nicosia | 0 | 2 | 0 | 0 |
| **Total** | **208** | **24** | **68** | **71** |

The MuMa figures combine its two existing catalogue representations for reporting. MuMa and Rouen each already had separate museum/Joconde institution records; their identities were not merged in this operation. Exact object reconciliation retained the existing institution representation.

See [every delivered record, source URL and image association](delivered-records.json), [machine-readable totals](delivery-summary.json), [French verification](france-verification.json) and [Cyprus verification](cyprus-verification.json).

## Source coverage

The initial read-only audit covered 14 existing institution rows and 2,243 scoped production artworks; the corresponding local scope had 2,281 artworks. Local-only source leads were compared by source identities, not database UUIDs.

- [MuMa's featured collections](https://www.muma-lehavre.fr/fr/collections/oeuvres-commentees): 143 object pages captured.
- [Rouen's collections](https://mbarouen.fr/fr/collections): 140 object pages captured across all 15 collection themes.
- [CVAR's paintings catalogue](https://cvar.severis.org/en/explore/collections-archives/paintings/): first four index pages, 96 entries; 91 selected object pages captured after excluding five explicitly post-1970 index dates.
- [Leventis's Cypriot artist catalogue](https://cypriotartists.leventisgallery.org/): five artist catalogues containing 53 works. Nine entries explicitly identify holdings at Leventis, the State Gallery or Bank of Cyprus Cultural Foundation; exhibition/private-collection references were not promoted to holdings.
- French Ministry of Culture/Joconde: 38 same-day source checks for local-only leads at the [education museum](https://pop.culture.gouv.fr/notice/joconde/M50678474991), [Flaubert museum](https://pop.culture.gouv.fr/notice/joconde/07340001800) and [Ancien Havre museum](https://pop.culture.gouv.fr/notice/joconde/M0718000001); 36 records delivered.

This is a bounded source-backed selection, not a claim to have imported every object or every Cyprus museum. The initial audit also includes Saint Neophytos, Kykkos, XeniArtSpace and Le Havre's natural history museum; no new object selection from those institutions was delivered in this pass.

Source parsing produced 369 candidate fact records: 104 MuMa, 132 Rouen, 88 CVAR, 9 Leventis-catalogue records and 36 Joconde records. Of these, 232 received metadata writes, 72 needed no metadata changes, and 65 were held. Three of the 72 unchanged metadata records subsequently received images.

## Matching, dates and attribution

Exact source URLs and inventory identities were checked before creating records. Cross-source MuMa/Rouen matches required a unique full-creator identity, exact title, narrow concordant creation date and the same documented museum. Similar titles alone caused a hold. Existing duplicate records were preserved.

Only unambiguous existing painter identities were linked. Supplied anonymous, school, disputed and unresolved creator labels remain object-level labels with their primary museum evidence. No painter biographies or nationalities were invented, and no new painter records were created.

Creation eligibility uses the artwork date through 1970. Source date wording is retained, including ranges, approximate dates and centuries. Nine French additions have unknown or unresolved date precision and remain research candidates in review. Acquisition dates, artist life dates and dates depicted in titles were not substituted for creation dates. The ambiguous Rembrandt-copy date was held because it may date the original rather than the copy. Existing nonempty dates and images were not overwritten.

## Images

The 68 CVAR images use the existing [Cyprus museum/artist source approval](../../ARTLINE_IMAGE_USE.md#explicit-cyprus-source-extension--20-september-2026) and have source creation ranges ending by 1955. Actual restricted rights labels, credits, paper margins and watermarks remain preserved. One source-catalogued Bakst sketchbook page consists of written notes; its supplied page image was retained without synthesizing an illustration.

The three French images come from WikiArt under the [user-approved source policy](../../ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026):

- Géricault, [Study of a Dapple Grey](https://www.wikiart.org/en/theodore-gericault/study-of-a-dapple-grey-1824), matched to Rouen's *Cheval arabe blanc-gris*.
- Delaroche, [Joan of Arc Being Interrogated](https://www.wikiart.org/en/paul-delaroche/joan-d-arc-being-interrogated-1824).
- Monet, [Rouen Cathedral, the Portal and the Tour d'Albene, Grey Weather](https://www.wikiart.org/en/claude-monet/rouen-cathedral-the-portal-and-the-tour-d-albene-grey-weather).

All three WikiArt pages label their images public domain; this is preserved as source evidence, separately from user approval. A selection of 61 exact existing museum-object titles was searched, with 14 WikiArt object pages captured and 3 accepted matches. The remaining 58 searched records lack a corroborated new image match in this pass; source-approval policy was not used as an exclusion.

All 71 application JPEGs are at most 100,000 bytes, retain the complete supplied composition, and passed visual contact-sheet inspection. Downloads occurred only after selection. Uploads used unique paths and create-only storage preconditions; existing media associations were preserved. See [Cyprus visual review](cyprus-visual-review.json), [French visual review](france-visual-review.json) and [WikiArt matching evidence](wikiart-review.json).

## Held source records

The 65 candidate-plan holds are source entries, not a count of unresolved artworks across the full production catalogue:

| Reason | Source entries |
| --- | ---: |
| object type or title review | 14 |
| same museum creator title variant requires reconciliation | 24 |
| title creator or museum collision requires object reconciliation | 26 |
| unknown creator and creation date | 1 |

An additional 96 source entries were excluded or held before candidate planning:

| Reason | Source entries |
| --- | ---: |
| after artwork creation cutoff | 11 |
| caption layout review | 1 |
| copy original creation date needs review | 1 |
| deposit or restitution context requires review | 14 |
| exhibition or private collection only | 36 |
| group or component review | 28 |
| group or destroyed original review | 2 |
| grouped sketchbook parent components kept separate | 1 |
| joconde source date type or holding review | 1 |
| photograph or surrogate review | 1 |

These include possible duplicate objects, grouped/component identities, loans or restitution contexts, post-cutoff works, and references that establish only exhibition history or private ownership. Full reasons and object links remain in the immutable plans and the [fact extraction](facts/b456c561e6af58bbf01668beeae20d435b0be246ec36630ff8545c5c7ff6bb6d.json).

## Verification and recovery evidence

Production verification checked all **235 changed artwork rows**, their audits, source evidence, retained review state and holdings. **21 live museum detail API checks** passed, and **all 71 live image responses matched their saved SHA-256 checksums**. Seven offline tests passed for date parsing, medium/type classification, creator normalization and pinned Cyprus facts. No test database or catalogue fixtures were created. Scoped query plans are retained; this operation does not establish performance at ten million artworks.

Cloud SQL backup **1791309359006** completed successfully before writes. Exact selected preimages, immutable plans and transaction after-images are preserved under `/Users/vadimdulub/Library/Application Support/Artline/backups/havre-rouen-cyprus-20261006/`. Original images and contact sheets are under the matching `source-images/havre-rouen-cyprus-20261006/` directory. Application derivatives are under `apps/web/public/assets/artworks/imported/havre-rouen-cyprus-20261006/` and the matching production storage paths.

- [france immutable plan](plans/france-ff420714dedfcac389036d422c04f0a82e5f0add512ef3eb28fa1e9824ccfea0.json), applied content SHA-256 `9abc24c7084ac2976f47085d7cbd85fd026a30f54f8f7ae86c131bcc284a35a9`.
- [cyprus immutable plan](plans/cyprus-e48dcec766f8c93e962c6df2db51b5418a684fd7ba015c77e75312474d15eabf.json), applied content SHA-256 `d3dfc920bd3f758cdf13f7319c207dfac4d7c0d03cbb46f01055f94c866a003c`.

- [Institution geography changes](institution-geography-applied.json).
- [Verified Nicosia institution identities and place links](institution-geography-verification.json).
- [Cloud backup receipt](cloud-backup.json).
- [Research and guarded delivery script](../../../ops/research-havre-rouen-cyprus-20261006.py).
- [Offline regression tests](../../../ops/test_havre_rouen_cyprus_20261006.py).

No local catalogue writes, Git commits, deployments, record deletion or publication occurred in this operation.
