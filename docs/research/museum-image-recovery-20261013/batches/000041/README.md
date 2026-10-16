# Iteration 41

Checked 10 distinct previously unchecked Cleveland Museum of Art holdings after cursor `10afaa10-88dc-4feb-b5f2-474340f4308b`. All 400 prior checked IDs were read and excluded. Prior completion pins and the saved production batch 107 reconciliation receipts were validated before selection; earlier deliveries were not counted again.

Five existing artworks received independently verified CC0 primary images:

| Internal artwork ID | Museum native ID / accession | Title | Derivative bytes |
| --- | --- | --- | ---: |
| 10b32ee0-0864-5ea8-8741-724bae181952 | 156952 / 1993.111 | Black-Figure Band Cup: Stags and Panthers | 98,320 |
| 10b7b606-40e4-5aa0-a9e1-01a10e91beaf | 123022 / 1943.279 | Fragment of a Wall Decoration from the Palace of Xerxes: "Guardsman" in Procession | 98,643 |
| 10be537b-a7ae-5147-bfb9-01efa994878f | 678440 / 2025.82.4 | Westlake Panorama | 98,206 |
| 10d5f6b3-a388-5694-955f-2e685b36ad51 | 106526 / 1924.587 | Design for a Chalice (recto) Architectural Plan (verso) | 98,794 |
| 10e1a1fc-3dbb-5c43-a170-d5c18b7b4d07 | 106855 / 1924.872 | Black-Figure Neck-Amphora (Storage Vessel): Animal Friezes | 99,509 |

All ten official object pages and corresponding official API records returned HTTP 200. Native IDs, accessions and titles agree. Five other works have museum-page images but Copyrighted labels without established reusable licences and remain held. Still Life, accession 1976.147, additionally exceeds the normal through-1970 scope. No museum-page-unavailable or no-image-at-checked-source outcomes occurred.

All five original files and all five derivatives were individually viewed. Complete source frames and proportions are preserved. The cup, relief and amphora use representative whole-object views. Westlake 2025.82.4 remains one individually accessioned sheet of a four-print panorama. The chalice source supplies a combined front-and-back image; the architectural plan named in the catalogue title is not discernible, and no claim of its legibility is made. That source discrepancy, the museum's record type and dimensions, and the amphora's attributed-to qualifier remain explicit. Museum file-size metadata differs from actual bytes for four originals and is absent for the fifth; native routes and pixel dimensions match. Actual sizes and SHA256 hashes are retained.

Originals and download receipts are archived under `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000041/`. Exact transaction preimages, baseline and checksum-pinned plans are backed up under `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000041/`. These are affected-row backups, not a full database backup. No Cloud SQL backup was created.

Production proxy target and active transactions were inspected. Create-only storage uploads preceded the transaction. The transaction acquired the shared `artline-curated-ingestion` advisory lock, locked the selected rows, and rechecked null primary images. Five attributable null-to-primary updates committed without concurrent-image skips. Independent verification checked exact audit events, media/rights associations, search projections, creator links, holdings and editorial-state preservation. Storage bytes were downloaded independently and checked against their pinned hashes and upload generations. All five public image responses and artwork API records passed identity, size and checksum checks.

The real local catalogue was never connected to or changed. No Translation, paid search API, deletion, commit, push, deployment or infrastructure change occurred. Other programmes and the supervisor/prompt were unchanged. The initial system Python lacked psycopg; the established `/tmp/artline-research-venv/bin/python` completed the workflow without package installation.

Campaign coverage is now 410 distinct IDs: 400 Cleveland and 10 Städel. Continue after Cleveland cursor `11071d6b-0186-5d67-a0a0-e64db2b98cae`, exclude all 410 checked IDs and preserve the holds recorded in `source-queue.json`. This completes one bounded iteration, not all 1,000 requested iterations.
