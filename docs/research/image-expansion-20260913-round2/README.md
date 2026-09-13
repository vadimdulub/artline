# Additional images after the database update — 13 September 2026

Completed: **398 SMK images**, plus **two Monet images** in the companion
[Joconde/Commons pass](../image-expansion-20260913-joconde-commons/README.md).
All 400 local files, Google Storage objects, database links and rights records
passed verification. See [RESULTS.md](RESULTS.md) for the combined result.

This pass selects 622 existing SMK research artworks with eligible creation dates
and no primary image. The records have an exact official museum object URL in
their research evidence, but remain unvalidated review candidates. An image does
not validate a creator identity, establish an accepted holding, or publish a work.

The catalogue audit also identified eligible image gaps among 24,398 Joconde and
1,054 Tate research records. Those counts are opportunities for further rights
research, not permission to copy the associated reproductions. This bounded pass
uses SMK's explicit per-object Public Domain Mark evidence.

`candidates.json` freezes the selection. Before an image download, the adapter
requires the exact current SMK object number (including `verso`), matching title,
the same museum creator identifier, matching creation-date endpoints no later
than 1970, an available primary image, `public_domain: true`, and the exact
Public Domain Mark rights URL. Responses and retrieval receipts are retained in
`metadata`; selected evidence precedes downloads in `selected`; final image
receipts reside in `images/smk`.

The local and cloud imports have different artwork, snapshot and source UUIDs.
The two identity maps preserve those differences while requiring the same
research record, object key, immutable entry/plan/facts checksums, title, dates,
slug and official source citation. Attachment rechecks these conditions under an
artwork row lock. It changes only primary media, revision and update audit fields.
Existing primary images are preserved. No external artwork IDs or museum holding
assertions are invented to make these review records fit the older adapter.

Each reproduction is proportionally resized and JPEG-compressed to at most
100,000 bytes, without cropping or generated content. Local files and private
Google Storage objects use immutable checksum-based names. Uploads are
create-only and require matching byte size and MD5 before database attachment.
Rights evidence retains the complete museum response and research identity chain.

Verification decodes all saved images, checks local SHA-256 and GCS MD5/size,
checks exact media and rights evidence in both databases, and compares every
non-media artwork field and creator link with the respective baseline.
`verification-canary.json` records the successful first eight images;
`live-canary.json` records HTTP 200 and matching image bytes through the live web
asset route. `verification-final.json` reports 398 verified SMK images and no
unaccounted errors. Of the 224 skips, 204 lack explicit public-domain permission
and 20 have no museum image. Two initially skipped official URLs were recovered
by supporting accession filenames and uppercase `.JPG` extensions.

The other database enrichment process changed eight overlapping local records
between the initial audit and preflight. Its changes were preserved; initial
hashes remain in `local-before-initial-audit.json`, with refreshed pre-image
baselines in `local-before.json` and `cloud-before.json`. The same eight creator
changes reached the cloud after its baseline. Reconstructing their pre-import
labels and empty creator links reproduced every original hash exactly; their
new artist links and attribution notes also match the separate import plan.
`verified-concurrent-creator-changes.json` preserves that proof. The final audit
accounts for those external changes without replacing its original baseline;
the initial audit that detected them is retained separately. Existing full
backups are documented in `backup-and-concurrency.json`.

`identity-query-plan.json` records the actual local single-artwork query plan,
using indexed research/artwork/citation lookups. This is not a 10-million-row load
test; representative large-scale load testing remains outstanding. Preflight and
verification use bounded batch queries to avoid hundreds of cloud round trips.

Commands (from the repository root, using the image workflow Python environment):

```sh
python ops/enrich-research-images.py select --run docs/research/image-expansion-20260913-round2
python ops/enrich-research-images.py apply --run docs/research/image-expansion-20260913-round2
python ops/enrich-research-images.py verify --run docs/research/image-expansion-20260913-round2
python -m unittest discover -s ops -p test_research_image_identity.py
```

The adapter resumes completed or explicitly unavailable/uncleared candidates;
failed downloads retain their evidence and can be retried. The seven offline tests
cover exact-side identity, unresolved source creator labels, changed titles and
creators, unknown/cross-cutoff dates, changed research provenance, and safe
accession-based SMK thumbnail filenames with explicit public-domain rights. They do
not connect to or insert fixtures into either catalogue database.
