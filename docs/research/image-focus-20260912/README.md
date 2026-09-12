# Image-first batch — 12 September 2026

The owner switched from manual CSV research to finding and attaching authentic
images. No new artworks were imported in this batch. No commit, publication,
deployment or Terraform action was performed.

## Applied and verified

Twelve existing SMK paintings received local images: four each by Christen Købke,
Michael Ancher and Vilhelm Hammershøi. Live catalogue: **106,350 artworks / 656
artworks with pictures**, up from 644 pictures. All records remain in review.

Each checked item below passed the exact official object number, source artist
authority, title, creation date, accepted local holding, image URL and per-object
Public Domain Mark checks. These are image outcomes, not completed painter
research or new masterpiece designations.

### Christen Købke

- [x] [KMS359 — View from Dosseringen, 1838](https://open.smk.dk/artwork/image/KMS359): image attached and verified; 66,489 bytes.
- [x] [KMS844 — Morning View of Østerbro, 1836](https://open.smk.dk/artwork/image/KMS844): image attached and verified; 73,968 bytes.
- [x] [KMS1345 — The Transept of Århus Cathedral, 1830](https://open.smk.dk/artwork/image/KMS1345): image attached and verified; 71,635 bytes.
- [x] [KMS1662 — View from the Loft of the Grain Store, 1831](https://open.smk.dk/artwork/image/KMS1662): image attached and verified; 85,089 bytes.
- [ ] Other image gaps remain; painter research is not exhaustive.

### Michael Ancher

- [x] [KMS1222 — The Lifeboat is Taken through the Dunes, 1883](https://open.smk.dk/artwork/image/KMS1222): image attached and verified; 87,749 bytes.
- [x] [KMS4002 — The Sick Girl, 1882](https://open.smk.dk/artwork/image/KMS4002): image attached and verified; 91,029 bytes.
- [x] [KMS3820 — The Girl with the Sunflowers, 1889](https://open.smk.dk/artwork/image/KMS3820): image attached and verified; 79,084 bytes. Museum frame and colour chart are retained as supplied; no crop or retouching.
- [x] [KMS1691 — The Artist's Wife Reading, 1881](https://open.smk.dk/artwork/image/KMS1691): image attached and verified; 59,597 bytes.
- [ ] Other image gaps remain; painter research is not exhaustive.

### Vilhelm Hammershøi

- [x] [KMS3696 — A Room in the Artist's Home, 1901](https://open.smk.dk/artwork/image/KMS3696): image attached and verified; 80,361 bytes.
- [x] [KMS3697 — A Room in the Artist's Home, 1902](https://open.smk.dk/artwork/image/KMS3697): image attached and verified; 66,850 bytes. Different accession, date and composition from KMS3696; never merged by title. The museum IIIF filename contains `cropped`, but visual inspection shows the painting composition rather than a detail; Artline requests the full supplied frame and performs no additional crop.
- [x] [KMS1542 — Amalienborg Square, 1896](https://open.smk.dk/artwork/image/KMS1542): image attached and verified; 94,642 bytes.
- [x] [KMS8010 — Tree Trunks, 1904](https://open.smk.dk/artwork/image/KMS8010): image attached and verified; 67,018 bytes.
- [ ] Other image gaps remain; painter research is not exhaustive.

## Evidence and safeguards

- Twelve official API responses and timestamped URL/SHA256 receipts:
  `content/imports/image-focus-20260912/smk/`. Each response explicitly has
  `has_image=true`, `public_domain=true` and the
  [Public Domain Mark 1.0](https://creativecommons.org/publicdomain/mark/1.0/).
- The web browsing tool failed to retrieve the SMK overview/API pages. The
  established Go connector successfully captured the documented official API
  directly. These tool failures are not evidence of an Artline service error.
  No source access restriction was bypassed and no API retries were needed.
- Immutable selected batch: `output/image-focus-20260912/smk-selection.json`,
  SHA256 `8458e6558721303057eec3971a805947c3cb698c410d3b8aa6cd0381de95a5ce`.
- Before mutation, created and checked PostgreSQL custom-format backup:
  `/Users/vadimdulub/Library/Application Support/Artline/backups/image-focus-20260912.7rkwTr/before-images.dump`.
  SHA256 `b2943a066730c4539dd270b88dabb8711d8e135beb11fa490f81aba2ff21f855`.
  Archive listing verified; no restoration or test database created.
- Preview, application and non-mutating replay-preview receipts are in
  `output/image-focus-20260912/`. Replay preserves existing images.
- All 12 files were fully decoded, SHA256/size/dimension checked against receipts,
  linked through `primary_media_id` with structured rights evidence, and served
  from `http://127.0.0.1:3000` with matching SHA256. Each is <=100,000 bytes.
- Visually inspected all twelve final derivatives, not just successful requests.
- Before/after read-only audits preserve artwork metadata (excluding authorized
  media/revision/update fields), artist profiles, attribution links, institutions,
  popularity, curated selections and every previously existing media row.
- Go tests and vet passed for the research/image commands. Negative tests cover
  source artist, attribution, date and title drift using real retained captures;
  no fixture database was used.
- Local static asset delivery is verified, not the separate right-panel UI
  visibility issue. Monet remains 300 records / 32 existing images in the older
  checkpoint; this batch did not investigate or fix his UI visibility.
- The six-column manual CSV remains the original 644-picture snapshot. It was
  not overwritten, because the owner may already be editing it.

## Next queue

1. Resume the two Athens icon image candidates already captured in
   `content/imports/data-collection-20260912/athens-followup/`: Michael BXM 01353
   and Saint Marina. Source/rights metadata exist; images remain unattached.
   Verify exact subject/accession/side and photograph licensing, then extend the
   closed anonymous-icon importer deliberately. Do not invent painter profiles.
2. Rotate to another European museum or continue a new bounded Danish batch:
   Michael Ancher KMS1336 and KMS3821; Christen Købke KMS1767 and KMS1493.
   These are leads from older source captures, not fresh reviewed/downloaded works.
3. Do not repeat unchanged SMK Pissarro queries for KMS3573, KMS3574 and KMS4323:
   the earlier exact-object review found no supplied image. Seek a separately
   licensed, identity-matched source instead.
4. Preserve prior blocked/rights-deferred decisions. No claim of exhaustive
   artwork or museum image coverage is made.
