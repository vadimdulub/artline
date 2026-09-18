# France catalogue and image campaign — 16 September 2026

Authorized by the owner: add catalogue data and upload images, working for 4–8 hours.
Started 2026-09-16 20:22:53 UTC. Earliest intended wrap-up 2026-09-17 00:22:53 UTC.

This campaign follows `../france-museums-deep-20260916/`. New records remain in
review; no publication, deployment, institution merges, or invented metadata.
Source records, exact-identity conflicts, rights decisions, backups, preimages,
and application receipts are retained separately. All image acquisition is
bounded by individually selected eligible objects and explicit file licences.

Backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/france-catalogue-20260916/`.
Cloud SQL backup requested: `1789590593680`; completion must be verified before writes.

Priority: Dieppe, MuMa/Le Havre, Nice, Louvre, Paris modern-art collections;
then regionally balanced museum pilots. Existing images and editorial fields
are preserved. Holding evidence never implies current display.

## Verified outcome — partial campaign

Final database verification: **2026-09-17 07:47:02 UTC**.

- **8 new artwork records** committed to both local and production databases.
- **2 authentic images** uploaded to the production image bucket and attached
  to the corresponding existing local and production records.
- All ten affected artworks remain **review / research candidate**. No
  publication, accepted holding, current-display claim, commit or deployment.
- Every new artwork has a review-only museum association, preserved creator
  label, source record and source hash. Two Niki de Saint Phalle reliefs retain
  `work_type=unknown`; no invented painting classification.
- Full local backup and successful Cloud SQL backup verified before writes.

This is **not** a completed nationwide expansion or 4–8 hours of uninterrupted
research. A long interruption occurred after the initial pilot, followed by a
broken shared Python environment and additional delays. The recorded wall-clock
interval is not a measure of active work. No campaign worker is left running.

### New records

| Source reference | Artwork | Museum association (review only) |
|---|---|---|
| 000PE000014 | Madame de Loynes | Orsay |
| 000PE000269 | Louis Français | Orsay |
| 07200000977 | La plage du Havre | MuMa, Le Havre |
| 08800000057 | Voyage d'inspection de l'Empereur Qian-Long dans le Sud de la Chine | Nice, Jules Chéret |
| 08880000768 | Tir au soulier | Nice, MAMAC |
| 08880000767 | Tir à la raquette – Séance galerie J. | Nice, MAMAC |
| 08880001075 | Il mistero della piramide | Nice, MAMAC |
| 08880000138 | Alpha Lambda | Nice, MAMAC |

### Uploaded and verified images

| Artwork | Reuse evidence | Derivative |
|---|---|---|
| Monet, Fécamp, bord de mer (MuMa) | Commons Public Domain Mark; photograph by Pymouss | 1000 × 812, 89,764 bytes |
| Pissarro, Vue de l'avant-port de Dieppe | CC BY-SA 2.0; Patrick Monchicourt / Morio60; Commons Flickr licence review | 600 × 534, 91,065 bytes |

Both actual files were visually inspected, fully decoded, checked against the
100,000-byte ceiling, uploaded with create-only storage preconditions, and
downloaded back from storage for hash verification. The Pissarro photograph
includes a substantial frame and is a modest-resolution study reproduction.
No crop or generated replacement was used. Credits and ShareAlike terms are
stored with the media. Public website rendering was not verified, and these
review records were not made public.

### Counts and remaining queue

Of the first **116** pinned source notices, **35** already had an exact global
source identity, **71** were held during automated preflight, and **2** additional
works were held after manual review. The other **8** were imported. A title-only
lead is not a confirmed duplicate: the 73 held notices need individual review.

The existing-image scan selected 150 local gaps, but only 25 passed the existing
cross-database/museum-authority prerequisites. Their Wikidata research stopped
after three replication-lag backoffs; no image from that batch was attached.
The separate two-image pilot completed. The Orsay Madame de Loynes image remains
held because its machine-readable and rendered licence descriptions conflict.

Measured live totals (include unrelated concurrent catalogue work):

| Target | Active artists | Active artworks | Artworks with media |
|---|---:|---:|---:|
| Local | 13,365 | 264,362 | 79,983 |
| Production | 13,365 | 264,360 | 79,981 |

The eight new records and two images have verified cross-database parity. The
two-record global difference is outside this campaign's measured changes; no
global synchronization was attempted.

### Evidence and continuation

- `backups.json`: validated archive and successful Cloud SQL backup receipts.
- `metadata-001/`: 116 selected raw source rows, pinned plans, manual review,
  eight per-target application receipts and result counts.
- `images-001/`: selected existing image gaps, cross-database holds and preserved
  replication-lag response evidence. Resume metadata checks only after source
  recovery; do not rerun a general image downloader without licence review.
- `images-pilot001/`: Commons file revisions/licences, target identity evidence,
  pinned Go selection, image preparation, visual review and upload receipts.
- `verification-final.json`: measured local/production state of all ten works.

Next work: reconcile the 73 held notices (starting with MuMa and Dieppe source
matches already in the catalogue), resolve creator authorities without inventing
biographies, then expand Nice/Louvre/native modern-art and regional batches from
the original deep-research queue. Source IDs have variable lengths and may
contain letters; do not constrain Joconde identities to eleven digits.

The spreadsheet skill informed preservation of raw source fields and separate
source facts versus interpreted fields in the import manifests; no workbook was
created. Twelve pure Python parsing tests and three Go downloader/compression
tests passed. No fixture or test database was created in the real catalogue.

The shared `/tmp/artline-images-venv` lost package files during the interruption.
The isolated continuation runtime is `/tmp/artline-france-campaign-venv/bin/python`.
Go was run with the installed Go 1.24.5 root and an isolated temporary build
cache because the inherited GOROOT pointed at a different toolchain version.
