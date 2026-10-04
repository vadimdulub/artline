# Islamic-world images — 25 September 2026

Added **12 selected museum objects with images** to the local review catalogue and the All → Islamic worlds and learning preview. The view now contains 12 illustrated artworks, 13 books and six events in its existing 600–1400 context window. Highlights remains off.

Follow-up: [20 further works](../islamic-world-more-20260925/README.md) bring the local view to **32 illustrated artworks**. The selection below records the first batch.

## Selection

The user requested Islamic-world pictures, suggesting patterns or other objects. This selection combines geometric and floral ornament with calligraphy, architecture and illustrated scientific knowledge. It is a small introduction, not a comprehensive survey of Islamic art.

| Museum object | Museum dates | Origin country | Reason |
|---|---|---|---|
| [Bowl](https://clevelandart.org/art/1956.225) (cleveland-133598; 1956.225) | 900s | IR | Stylized bird and ornamental borders |
| [Wall Tile](https://clevelandart.org/art/1915.638) (cleveland-95115; 1915.638) | 1300s | IR | Luster-painted wall decoration |
| [Wall Tile with Lotus Blossom](https://clevelandart.org/art/1915.645) (cleveland-95123; 1915.645) | c. 1300–50 | IR | Star-shaped tile with floral relief |
| [Dish with Splashes of Green](https://clevelandart.org/art/1915.304) (cleveland-94658; 1915.304) | 830–900 | IQ | Abbasid blue-and-green geometric decoration |
| [Luster Bowl with Antelope](https://clevelandart.org/art/1944.476) (cleveland-123967; 1944.476) | 1000s | EG | Fatimid luster painting with an antelope |
| [Folio from a Qur'an](https://clevelandart.org/art/1933.488) (cleveland-114247; 1933.488) | 1100s | IR | Ornamental Kufic calligraphy with illuminated medallions |
| [Qur'an Manuscript Folio](https://clevelandart.org/art/1933.440) (cleveland-114190; 1933.440) | 1200s–1300s | ES | Maghribi script from Islamic Spain |
| [Peacock-shaped Hand Washing Device (recto); Text Page, Arabic Prose (verso)](https://clevelandart.org/art/1945.383) (cleveland-124420; 1945.383) | 1315 | SY | Illustrated mechanical knowledge: a peacock automaton |
| [The Wade Cup with Animated Script](https://clevelandart.org/art/1944.485) (cleveland-123985; 1944.485) | 1200–1221 | IR | Inlaid metalwork with animated script and interlacing bands |
| [Column Capital](https://clevelandart.org/art/2021.4) (cleveland-423612; 2021.4) | c. 960–76 | ES | Carved architectural ornament from Madinat al-Zahra |
| [Folio from an Arabic translation of the Materia Medica of Dioscorides](https://clevelandart.org/art/1977.91) (cleveland-149172; 1977.91) | 1224 | IQ | Illustrated medicine in Abbasid Baghdad |
| [Mihrab (Prayer Niche)](https://www.metmuseum.org/art/collection/search/449537) (met-449537; 39.20) | dated 755 AH/1354–55 CE | IR | Geometric tile mosaic and architectural calligraphy |

## Evidence and identities

One bounded Cleveland Islamic Art metadata page (100 records) and one explicitly selected Met record supplied the candidates. Only the 12 pinned selections were downloaded. Exact source responses, hashes, retrieval receipts, policy captures, selected IDs and image checksums are retained here. No existing accession or canonical-URL match was found in the local catalogue.

All objects retain the museum’s numeric date intervals and displayed dates. The fourteenth-century pieces are later context within the existing 600–1400 window, not claims that they were made under the Abbasids. The wall tile’s API upper bound is 1400 although its displayed date is “1300s”; that supplied interval is preserved. Original museum culture strings, including “probably Sultanabad,” remain recorded. Country links describe object origin at country level; no historic nationality or uncertain city has been invented.

Eleven objects have no recorded maker. Abdallah ibn al-Fadl is retained as the medicine folio’s object-level creator label, supported by Cleveland’s native creator 59123, “written and illustrated by.” No biography, lifespan or new artist profile was invented. Composite museum images of recto and verso remain one parent accession each; the opposite sides were not imported as duplicate artworks.

Accepted holding assertions identify Cleveland Museum of Art or the Metropolitan Museum of Art. No current-display assertions were created. All 12 artworks remain `review`, `research_candidate=true`, with null publication dates. No production changes or publication were performed.

## Image review

Every Cleveland record explicitly states CC0; the Met record explicitly marks the selected mihrab reproduction public domain. The [Cleveland Open Access policy](https://www.clevelandart.org/open-access) and [Met Image and Data Resources policy](https://www.metmuseum.org/policies/image-resources) support unrestricted CC0 reuse. Each asset retains its exact source image URL, museum credit, source object, licence URL and archived retrieval evidence. The Met policy was captured through the web tool after a direct request returned HTTP 429.

All 12 derivative images were visually inspected in a contact sheet. Complete source frames are preserved by proportional resizing and JPEG compression. The largest served derivative is **99,096 bytes**; no synthetic reconstruction or cropped replacement was used. Original downloaded reproductions remain separately archived.

## Implementation and verification

- Migration `0028_decorative_art_types.sql` adds ceramic, metalwork, sculpture and calligraphy types, with corresponding API/ingestion validation and UI filter choices. The existing manuscript-illumination type covers the two illustrated scientific folios. Actual source classifications remain in evidence.
- The All gallery now calls these entries “artworks” in loading/status text. Its existing compact title-and-creator layout is preserved.
- The preset description and source links now mention the new material. A star-shaped lotus tile is available as cover metadata; the starting-page featured-card selection is unchanged.
- Read-only verification checked all 12 records, image hashes/sizes, dates, source links, CC0 evidence, review state, accepted holdings, origin links and absent display/artist assertions.
- API country filters return Iran 6, Iraq 2, Egypt 1, Spain 2 and Syria 1. Every artwork detail endpoint returns its correct title, type, date, holding, licence, source and creator label.
- Chrome checks at 1440px and 390px verified all 12 loaded images, compact cards, the mihrab drawer, source link, licence, date and no horizontal page overflow or JavaScript errors. Screenshots were visually inspected.
- Go HTTP API, ingestion and atlas package tests passed; frontend TypeScript and targeted ESLint checks passed.
- The broader artwork infinite-scroll suite passed six of seven tests. The Painters “changing filters ignores a late incremental response” case timed out waiting five seconds for the search to finish, including one isolated rerun. Its screenshots and traces are in `/tmp/artline-islamic-scroll-tests/` and `/tmp/artline-islamic-scroll-recheck/`. This remaining failure is outside the new Islamic-world checks; no test timeout was increased to hide it.
- No catalogue fixture rows or test databases were created. Browser tests read the live local preview; disposable proofs are under `/tmp/artline-islamic-*`.

The selected import uses indexed museum accession/source identities and returned artwork IDs. This is not a 10-million-row load test. The new type constraint validates the artwork table during migration; a production rollout still needs its own migration-window assessment. No production migration was run.

## Local recovery and reproducibility

Validated pre-import PostgreSQL custom archive: **641,247,621 bytes**, at `/Users/vadimdulub/Library/Application Support/Artline/backups/islamic-world-images-20260925/local-before.dump`. The archive listing was validated without creating/restoring a database. Pinned plan and exact preimages for the new country records are in that backup directory. Originals and receipts are under the matching `source-images/islamic-world-images-20260925/` directory. Served images are under `apps/web/public/assets/artworks/imported/islamic-world-images-20260925/`.

The import script is `ops/add-islamic-world-images-20260925.py`; phases are `discover`, `plan`, `prepare`, `backup`, `apply`, `verify`. Application requires pinned metadata, explicit recorded visual review and a matching recovery archive, runs atomically, and rechecks accession identities before writing. The local account is the existing active review account. `verify` uses a read-only connection. A first application attempt failed the actor foreign-key check and rolled back completely; it was corrected to the existing account before the successful transaction.
