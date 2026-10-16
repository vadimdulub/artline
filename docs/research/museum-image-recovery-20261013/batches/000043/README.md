# Iteration 43

Checked 10 distinct previously unchecked Cleveland Museum of Art holdings after cursor `112d8ceb-38f1-400a-bc8e-3da78f945166`. All 420 prior checked IDs across 42 campaign receipts were read and excluded. Prior completion pins and saved production batch 107 reconciliation receipts were validated before selection; earlier deliveries were not counted again. No interrupted writes existed in this iteration directory.

Four existing artworks received independently verified CC0 primary images:

| Internal artwork ID | Museum native ID / accession | Title | Derivative bytes |
| --- | --- | --- | ---: |
| 11322d76-c315-58cb-9c29-acbe51a4e1c2 | 124250 / 1945.244 | Chalice Vine | 98,301 |
| 1132a439-6f6c-5605-80f0-8cef6810d50b | 120804 / 1941.531 | Procession at Arles | 99,404 |
| 1153d2cc-2b75-5f7b-9077-a5dfb9a344f9 | 163153 / 2004.1.7 | Album of Daoist and Buddhist Themes: Procession of Daoist Deities: Leaf 7 | 98,009 |
| 115e0564-885a-5417-bfa3-22c86b0c3ee3 | 160887 / 1999.174.1 | On Happiness, Calligraphy in Seal Script Style (zhuanshu) | 97,712 |

All ten official museum pages and corresponding official API records returned HTTP 200. Exact native IDs, accessions and titles agree. Six other works have museum-page images but Copyrighted labels without established reusable licences and remain held. These are rights holds, distinct from no-image or unavailable-page outcomes. No source access restriction was bypassed and no search API was used.

All four originals and all four derivatives were individually viewed with the available image viewer. Complete supplied source frames, margins and proportions are preserved. Chalice Vine retains museum state I/I without claiming an independent visual state determination. The prints retain unknown physical dimensions, and Vernet and Delpech retain their artist and printer/publisher roles. The anonymous Daoist album image is specifically leaf 7, accession 2004.1.7. Yang Yisun's calligraphy is one individually accessioned scroll, 1999.174.1, from the six-scroll set; the narrow source image agrees with the calligraphy title and is not represented as the whole set. No translation or metadata correction occurred. Museum filesize metadata differs from actual bytes for all four originals; exact native routes and pixel dimensions agree, with actual sizes and SHA256 retained.

Originals and download receipts are archived under `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000043/`. Exact affected-row baseline, transaction preimages, pinned plans and precommit postimage are under `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000043/`. These are affected-row recovery snapshots, not a full database backup. No Cloud SQL backup was created.

The production proxy target and active transactions were inspected before selection and again before writing. Create-only storage uploads preceded the database transaction. The transaction acquired `artline-curated-ingestion`, locked all selected rows, rechecked null primary images and preserved unrelated metadata, creators, holdings and editorial status. Four attributable null-to-primary updates committed with no concurrent-image skips. Independent database verification confirmed exact audit events, associations, rights evidence and search projections. Independent Storage downloads matched the pinned checksums and original upload generations. All four public images and artwork API records passed identity, checksum and byte-size verification.

The real local catalogue was never connected to or changed. No Translation, paid search, deletion, commit, push, deployment or infrastructure change occurred. No additional worker was launched; supervisor/prompt and both other programmes remain unchanged.

Campaign coverage is now 430 distinct IDs: 420 Cleveland and 10 Städel. Continue after Cleveland cursor `1168ebf5-b0eb-4006-84d3-01953224a320`, excluding all 430 checked IDs and preserving `source-queue.json` holds. This completes one bounded iteration, not all 1,000 requested iterations.
