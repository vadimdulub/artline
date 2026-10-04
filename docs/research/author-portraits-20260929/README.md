# Selected author portraits — 29 September 2026

Books now has Books (edition covers/title pages) and Authors (portraits) galleries. Existing book covers are unchanged. Author portraits are a versioned selection, attached after normal catalogue visibility checks to exact creator ID + Wikidata URL pairs. No database rows, publication states, or biographies were changed.

27 creators with books in the local highlights selection were chosen for an initial research batch. Read-only SQL joined `book_creators`, `book_creator_links`, and `book_discovery`, grouping creators where `d.top100`. `creator-identities.json` preserves the selected identities. Wikidata P18 supplies the candidate Commons identity, not automatic permission to display it. Source responses and revisions are in `captures/`; `candidates.json` retains all results and failures.

17 public-domain reproductions were selected after source/identity review. Wikimedia rate-limited six remaining metadata requests; those candidates remain without portraits. Four further images were held: an explicit identity dispute for Emily/Anne Brontë, a modern Orwell colorization, a copyright claim recorded on the Austen reproduction, and source reuse terms requiring another reproduction for Hugo. Nothing missing was invented. Dante and Murasaki are explicitly labelled later depictions.

`selection-audit.json` records source image URLs, source and transformed SHA-256 hashes, rights categories, dates, and output sizes. Local JPEGs preserve the supplied composition (some source files were already crops), with proportional resizing and compression. Each is under 100,000 bytes. The API manifest is `apps/server/internal/books/portrait-selection.json`; static assets are under `apps/web/public/images/authors/selected-20260929/`. Credits, source links and public-domain labels appear in author details. Remove an entry from the manifest to withdraw it; raw imported portrait fields are ignored.

Reproduction scripts: `ops/research-author-portraits-20260929.py` (metadata only) and `ops/select-author-portraits-20260929.py` (explicit selected downloads, macOS `sips`). Cached source images and browser proofs belong in `/tmp`; durable research responses remain here.

The galleries request 60 records per page and retain at most three pages of cards. Scroll spacers and saved cursors permit backward navigation without loading the catalogue into the browser. Date extent aggregates reuse the server's matching predicates before pagination; publication and filters remain server-owned. Functional checks on the local catalogue are not a 10-million-row load test. That scale still needs representative load fixtures and latency checks.

Portrait files are shipped in the web image under `/images/authors/`, outside the `/assets/` Cloud Storage rewrite. No storage upload is needed for this selection.

## Verification

- Web: 187 unit tests passed; TypeScript and lint checked for changed components.
- Browser: 12 Books/Authors and automatic-discovery checks passed at desktop, 390px and 320px widths, plus four existing All-gallery regression checks. Covered keyboard focus restoration, forward/backward paging and eviction, retry after a failed next page, portrait attribution and broken-image fallback, accessibility, unrestricted movement choices, Pre-Raphaelite filtering, and matching date extents for books, events, artworks and All.
- Backend: affected Go package tests passed. Three enforced read-only catalogue checks passed for author identity/visibility, cursor pages and the new date extent. Forty Tolstoy books retained the same 1852–1911 extent on one-record pages. The author audit checks actual published links (31 creator identities), rather than assuming the public catalogue must be empty.
- Local author aggregate plans including min/max dates: about 211 ms across all authors, 12 ms with a language filter. These timings describe this local catalogue only, not the planned 10-million-artwork capacity.
- All 17 local assets matched their retained SHA-256 checksums; largest JPEG: 97,019 bytes. Screenshots and test traces remain under `/tmp`.
