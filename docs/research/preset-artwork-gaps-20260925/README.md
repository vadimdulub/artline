# Artworks for the empty historical categories — 25 September 2026

Twelve selected Met objects fill four missing categories: three each for Writing and the first cities, The classical world, Buddhism across Asia, and West African trade and learning. The previous 44 Islamic-world artwork rows remain unchanged.

| Object / source | Source date | Origin / creator note |
|---|---|---|
| [Proto-Cuneiform tablet with seal impressions: administrative account of barley distribution with cylinder seal impression of a male figure, hunting dogs, and boars](https://www.metmuseum.org/art/collection/search/329081) | ca. 3100–2900 BCE | Mesopotamia, probably from Uruk (modern Warka) |
| [Cylinder seal and modern impression: three "pigtailed ladies" with double-handled vessels](https://www.metmuseum.org/art/collection/search/327067) | ca. 3300–2900 BCE | Southern Mesopotamia |
| [Hippopotamus ("William")](https://www.metmuseum.org/art/collection/search/544227) | ca. 1961–1878 B.C. | From Egypt, Middle Egypt, Meir |
| [Terracotta krater](https://www.metmuseum.org/art/collection/search/253422) | ca. 775 BCE | Greek, Attic; Attributed to the Workshop of New York MMA 34.11.2 |
| [Terracotta amphora (jar)](https://www.metmuseum.org/art/collection/search/247238) | ca. 550 BCE | Greek, Attic; Attributed to the Amasis Painter |
| [Marble portrait of the emperor Augustus](https://www.metmuseum.org/art/collection/search/247993) | ca. 14–37 CE | Roman |
| [The Death of the Buddha (Parinirvana)](https://www.metmuseum.org/art/collection/search/38452) | ca. 3rd century | Pakistan (ancient region of Gandhara) |
| [Standing Bodhisattva Maitreya (Buddha of the Future)](https://www.metmuseum.org/art/collection/search/38474) | ca. 3rd century | Pakistan (ancient region of Gandhara) |
| [Buddha Maitreya (Mile) Altarpiece](https://www.metmuseum.org/art/collection/search/42162) | dated 524 (5th year of Zhengguang reign) | China |
| [Seated figure](https://www.metmuseum.org/art/collection/search/314362) | 13th century | Mali; Middle Niger artist |
| [Long-necked vessel](https://www.metmuseum.org/art/collection/search/317989) | 12th–16th century | Mali; Middle Niger artist(s) |
| [Vessel with footed base](https://www.metmuseum.org/art/collection/search/310384) | 14th century | Mali, Bandiagara Escarpment; Tellem artist |

## Editorial decisions

Ancient cultural names are not converted into guessed modern origins. Five objects therefore have no modern country link; the first two Mesopotamian objects keep the museum's unclassified type as unknown. The cylinder-seal title explicitly identifies the accompanying **modern impression**. Its ancient date describes the seal, not the modern impression.

The Amasis Painter and Workshop of New York MMA 34.11.2 keep “Attributed to” as an object-level label. “Middle Niger artist(s)” and “Tellem artist” remain collective labels; no named artist identities or religion are inferred. Museum year intervals remain unchanged, including the broad 200–350 interval on the Maitreya sculpture. Missing culture is SQL NULL, not an invented value.

The three Mali works represent Middle Niger and Tellem material cultures of the wider Sahelian period. The preset does not claim the makers served a specific empire or were Muslim. No suitable book is currently selected for that category; its artwork and event layers are populated.

Only the pinned selection was downloaded, after read-only accession and canonical-source duplicate checks against the real local database. Each full-frame derivative was visually inspected and remains at most 100,000 bytes. All new artwork records remain **review** research candidates with null publication timestamps. No display claims or artist biographies were invented; accepted museum holdings are separate from current display.

The workflow preserves raw source responses, retrieval receipts, a hashed plan, original reproductions, image hashes, visual-review approval and verification results. A validated `pg_dump -Fc` backup preceded each atomic import; no test database or fixtures were created. Import scripts are idempotent after a completed apply and reject changed evidence.

## Recovery and evidence

- Script: `ops/add-preset-artwork-gaps-20260925.py`.
- Validated backup: `/Users/vadimdulub/Library/Application Support/Artline/backups/preset-artwork-gaps-20260925/local-before.dump` (641,509,275 bytes).
- Original reproductions: `/Users/vadimdulub/Library/Application Support/Artline/source-images/preset-artwork-gaps-20260925/`.
- Served derivatives: `apps/web/public/assets/artworks/imported/preset-artwork-gaps-20260925/`; largest 99,343 bytes.
- Research, plan, visual review and application receipts: this directory. Disposable browser proofs remain under `/tmp`.

All imported rows passed independent read-only verification. The final all-category audit and browser checks are recorded in [the preset review](../preset-clarity-review-20260925/README.md). No publication, production upload, deployment or commit was performed.
