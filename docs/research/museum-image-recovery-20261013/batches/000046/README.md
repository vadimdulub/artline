# Iteration 46

Checked ten distinct previously unchecked Cleveland Museum of Art holdings after cursor `11ed48cc-3d5b-5615-aa86-2fa8eda16ea9`. All 450 prior checked IDs from 45 receipts were read and excluded. Prior completion pins and batch 107 recovery evidence were validated. Prior write receipts had independent verification, and this batch had no interrupted writes. No earlier delivery was counted again.

Two existing museum-held artworks received primary images: Crusader's Vigil (native 108456, accession 1926.173) and Head of Bearded Banqueter (native 128277, accession 1951.27). All ten exact museum pages and official API records returned HTTP 200 and agreed on native ID, accession and title; each source object is accessioned and not on loan. Eight page images remain copyright-held; they were not downloaded. There were no unavailable-page or source-no-image outcomes.

Both CC0 originals and both derivatives were individually viewed with the image-viewing tool. The drypoint retains its full printed composition, supplied narrow margins and lower handwritten marks. The terracotta fragment retains the full surviving head, cap and wreath, with an explicit front-view label; unseen surfaces or a complete lost figure are not claimed. Derivatives are 98,341 and 98,256 bytes and preserve source proportions. Both source filesize values differ from the downloads; native URLs and decoded dimensions agree, and both sizes and actual SHA256 values are retained. Print state and edition remain unknown. No catalogue metadata was corrected or invented.

Production proxy target and active transactions were inspected before selection and writing. Storage uploads were create-only. The transaction acquired `artline-curated-ingestion`, locked all ten artwork rows, rechecked null primary images, and preserved catalogue facts, creators, holdings and editorial state. Two null-to-primary updates committed without concurrent-image skips. Independent read-only verification matched two exact audit events, media/rights associations and search projections. Separate Storage downloads matched pinned hashes and object generations. Both public images and artwork API responses returned HTTP 200 with matching images and object metadata. The eight held records remain unchanged.

Originals and receipts are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000046/`. Recovery baseline, locked preimages, pinned plans and precommit postimage are under `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000046/`. Backups cover affected rows, not the whole database; no Cloud SQL backup was created.

No real local catalogue connection, Translation, paid search, deletion, commit, push, deployment or infrastructure change occurred. Supervisor/prompt and existing artwork/exhibition programmes were not modified; no other workers were launched. An initial Python invocation lacked psycopg and ended before any database connection; the existing research virtual environment completed the work.

Campaign coverage: 460 distinct IDs (450 Cleveland, ten Städel). Continue after Cleveland cursor `122ea5cf-c60a-4a36-9acd-e06b5a041f72`, excluding all checked IDs and preserving the source-queue holds. This is one bounded iteration, not completion of all 1,000 iterations.

| Artwork ID | Museum native / accession | Title | Outcome |
| --- | --- | --- | --- |
| 11f0f00a-c969-4784-a671-b50630a20d30 | 138569 / 1962.430.32 | Walt Whitman | rights-deferred |
| 11f1630a-3dd2-515d-8ac0-c86817ca6277 | 108456 / 1926.173 | Crusader's Vigil | attached-and-verified |
| 11fb5270-d316-46f3-86f8-3f2a11439277 | 160393 / 1998.230 | Untitled | rights-deferred |
| 11fc77cb-66c3-41aa-a853-fb157062cffe | 145977 / 1971.177.5 | Transitions:  No. 5 | rights-deferred |
| 11fe3f07-ae27-455c-9a2e-b2b5690f1600 | 157442 / 1994.294 | Alain Bosquets-Painted Words: Skin | rights-deferred |
| 11ffd974-1583-5247-98ce-154f52df3ec0 | 141263 / 1964.494 | Behind the Hay-mow | rights-deferred |
| 121cc1bf-bcf5-5037-a70e-15e9a54981c8 | 115141 / 1935.292 | For the Innocent | rights-deferred |
| 121df5db-224b-447d-8a21-9906f7783c4f | 115131 / 1935.280.4 | The Episode of Nausicaä | rights-deferred |
| 12298a19-42ab-5d40-bbc3-820b55f90163 | 128277 / 1951.27 | Head of Bearded Banqueter | attached-and-verified |
| 122ea5cf-c60a-4a36-9acd-e06b5a041f72 | 169307 / 2011.181 | Eagle | rights-deferred |
