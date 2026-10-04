# Documented visual roots of computer art — 25–26 September 2026

Two public-domain paintings fill the digital preset through documented influence. The user explicitly selected “Include documented visual roots.” These are paintings with original dates, never relabelled as computer-made works.

| Object / source | Source date | Origin / creator note |
|---|---|---|
| [Highway and Byways](https://commons.wikimedia.org/wiki/File:Highway-byways.png) | 1929 | Modern country not established |
| [Composition in line, second state](https://commons.wikimedia.org/wiki/File:Mondrian_-_B082.83_(second_state).jpg) | 1916–1917 | Modern country not established |

## Editorial decisions

The [V&A Americas Foundation](https://vamaf.org/our-work/acquisitions/hommage-a-paul-klee-13-9-65-nr-2-print-by-frieder-nake-1965/) documents Klee's painting as the basis for Frieder Nake's 1965 homage. [A. Michael Noll's first-person account](https://ethw.org/First-Hand:Early_Digital_Art_At_Bell_Telephone_Laboratories,_Inc) describes his use of Mondrian's line composition. These direct relationships determine the selection; other works by those painters do not enter this preset.

The main digital period stays 1970–2000. The wider context begins in 1916 to show its documented visual roots. Its scope and description explain this, and details distinguish main period from wider context. Existing Klee and Mondrian identities are linked without changing their biographies. A minimal Museum Ludwig institution record is added in review, supported by the official collection identity.

The two images are faithful 2D reproductions from Wikimedia Commons marked PD-Art, separately from restricted museum photographs. Klee died in 1940; Mondrian in 1944; the paintings predate 1931. Rights are **public_domain**, not CC0. Reproduction credit, Commons file pages, rights statements and downloaded-file hashes are preserved. No Molnár, Nake or Noll image is copied without appropriate rights: the NGA Molnár object had no download permission, the Flickr upload's claimed dedication was not from a verified rights holder, and ETHW's article licence is noncommercial.

Museum Ludwig's direct endpoint returned a proof-of-work page and the old Kröller-Müller endpoint redirected to a redesigned site. Both unsuccessful responses are preserved as such. Primary museum identity/date excerpts retrieved through the search index are separately labelled in `primary-index.json` and `mondrian-index.json`; no fresh on-view claim is taken from the index. The Kröller-Müller exhibition text gives the second state's interval as **1916–1917**, retained instead of flattening it to Commons' 1916. The Klee dimensions retain the official catalogue's 83.5 × 67.5 cm; source variants remain in the captures.

Only the pinned selection was downloaded, after read-only accession and canonical-source duplicate checks against the real local database. Each full-frame derivative was visually inspected and remains at most 100,000 bytes. All new artwork records remain **review** research candidates with null publication timestamps. No display claims or artist biographies were invented; accepted museum holdings are separate from current display.

The workflow preserves raw source responses, retrieval receipts, a hashed plan, original reproductions, image hashes, visual-review approval and verification results. A validated `pg_dump -Fc` backup preceded each atomic import; no test database or fixtures were created. Import scripts are idempotent after a completed apply and reject changed evidence.

## Recovery and evidence

- Script: `ops/add-digital-art-roots-20260925.py`.
- Validated backup: `/Users/vadimdulub/Library/Application Support/Artline/backups/digital-art-roots-20260925/local-before.dump` (641,546,594 bytes).
- Original reproductions: `/Users/vadimdulub/Library/Application Support/Artline/source-images/digital-art-roots-20260925/`.
- Served derivatives: `apps/web/public/assets/artworks/imported/digital-art-roots-20260925/`; largest 97,756 bytes.
- Research, plan, visual review and application receipts: this directory. Disposable browser proofs remain under `/tmp`.

All imported rows passed independent read-only verification. The final all-category audit and browser checks are recorded in [the preset review](../preset-clarity-review-20260925/README.md). No publication, production upload, deployment or commit was performed.
