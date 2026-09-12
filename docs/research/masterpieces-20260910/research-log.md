# Painter picture coverage and museum highlights — 10 September 2026

## Result

Audited database coverage for **all 5,315 painter authorities**. This is a complete
coverage inventory, **not an individual art-historical review of every painter or
of all 105,943 artworks**, and not exhaustive image coverage.

Added **76 authentic local reproductions for 61 artists** and **104 source-backed
museum highlight designations** to existing artwork records. All new images are
CC0 under the supplying museum's per-object metadata; no AI artwork, museum essay
copying into descriptions, publication, deployment, Terraform apply, or commits.

| Coverage | Before | After |
| --- | ---: | ---: |
| Painter authorities | 5,315 | 5,315 |
| Artworks | 105,943 | 105,943 |
| Artworks with local pictures | 310 | 386 |
| Painters with at least one picture | 193 | 225 |
| Popular painters without pictures | 38 | 35 |
| Museum highlight entries | 465 | 569 |
| Personal must-see entries | 5 | 5 |
| Published artworks | 0 | 0 |

219 painters have no linked artworks. That is a separate research/identity gap,
not a failed image download. The 21 unlinked icon creator records are retained
separately rather than converted into fictitious named painters.

The new pictures occupy **5,811,735 bytes** in total; the largest is **99,857
bytes**. Source web renditions are downsampled, preserving aspect ratio, and
JPEG-compressed to a maximum 100,000 bytes. No additional crop or invented detail.
Some museum filenames already contain `cropped`; the derivative preserves the
museum-provided image frame, not a claim about its relationship to the physical
object's edges. The earlier 310 assets were preserved, not recompressed.

## Selection and primary evidence

The review matched source object identifiers to existing local artwork records
across the expanded painter catalogue, rather than only the original 1,000-person
cohort. Titles, accession numbers, holding institution, status and existing record
fingerprints are checked before attachment. Both database and fresh source dates
must pass the existing creation cutoff policy (1970), without replacing dates.

- [Cleveland Open Access](https://www.clevelandart.org/open-access): fetched all
  300 records in the API's explicit `highlight=1` selection, three bounded pages.
  Verified each selected record's `is_highlight=true`, CC0 status and absent
  conflicting copyright notice. Added 13 images and 20 highlight entries.
- [Met Open Access](https://www.metmuseum.org/hubs/open-access) and
  [official Collection API documentation](https://metmuseum.github.io/): used
  the already-pinned official CSV to identify relevant missing coverage, then
  requested fresh metadata for 146 exact objects. Added 63 images and 84 highlight
  entries. `isHighlight=true` and `isPublicDomain=true` are separate gates.

Examples now illustrated include Bruegel's
[The Harvesters](https://www.metmuseum.org/art/collection/search/435809),
Velázquez's [Juan de Pareja](https://www.metmuseum.org/art/collection/search/437869),
Cézanne's [The Card Players](https://www.metmuseum.org/art/collection/search/435868),
and Turner's [The Burning of the Houses of Lords and Commons](https://www.clevelandart.org/art/1942.647).
Bronzino, Pieter Bruegel the Elder and Paolo Veronese no longer have empty picture
coverage. 29 other painters also received their first image.

Every designation remains explicitly **museum** curation. No popularity-derived
masterpiece labels and no additions to the owner's personal must-see lists.
No current-display claims were added; room numbers in raw source metadata are not
treated as fresh display evidence.

## Deferrals and remaining coverage

154 entries passed metadata selection: 76 with downloadable cleared pictures,
78 without permitted/available pictures. Those 78 still retain their catalogue
records and documented highlight status. For example, the current Met API returns
`isPublicDomain=false` and no primary image for Monet's *Garden at Sainte-Adresse*;
the artist's historical dates are not used to override that source gate.

26 Met candidates were deferred before application: one HTTP 404, 24 whose fresh
metadata no longer flags them as highlights, and one title discrepancy. These
are recorded in `selection-v1.json`, with the fetched evidence in `captures/`.
No pre-existing designations were removed or silently rewritten. Older source
designations, where present, retain their original dated evidence and need
editorial reconciliation rather than an automatic destructive refresh.

The remaining **35 popular painters with no picture** are listed individually
in `coverage-after.json`. Priorities include Botticelli, Fra Angelico, Piero della
Francesca, Cimabue, Uccello, Sisley, Signac, Repin and Kandinsky. Some have copyright
constraints; others need a different independently permitted image source or
work-level editorial selection. Lack of a museum highlight flag is not proof
that an artwork is unimportant.

European museum and Russian/Greek/Byzantine priorities remain in effect. No Athens
or Kremlin photographs were copied: their previously documented image-use/access
constraints remain unresolved. No blocked Chicago image endpoint was retried or
bypassed. The independently checked
[Commons reproduction guidance](https://commons.wikimedia.org/wiki/Commons:Reuse_of_PD-Art_photographs)
does not establish a blanket licence for museum photographs; Commons files would
need exact object matching and individual rights review in a subsequent batch.
NGA's [museum-selected must-sees](https://www.nga.gov/visit/must-sees) are a further
bounded research lead, not already-imported images or new designations in this run.

## Verification and recovery

- Full before/after fingerprints of 105,943 artwork rows: only the intended media
  links, revisions and update stamps changed. Titles, dates, descriptions, artist
  authorities, attributions and holding/display assertions are unchanged.
- Existing 310 media records and all previous curated items preserved exactly.
- All 76 new file hashes, sizes, JPEG dimensions and per-image rights evidence
  verified. Representative served asset hashes and authenticated API details
  checked; museum-highlight/image-only pagination and unauthenticated visibility
  are covered by `ops/verify-masterpieces-api.mjs`.
- Replaying the same reviewed selection added **zero images and zero highlights**
  and preserved the post-import database state.
- New Go tests cover compression/format limits, aspect ratio, no upscaling,
  transparency, stale/future evidence, duplicate objects, forged metadata/rights,
  unknown hosts, and immediate no-retry stops after 403/429.
- Full Go tests and vet, plus database-backed catalogue/ingestion tests, run for
  this change. This offline audit is not a 10-million-row performance benchmark.

Local backup (readable custom-format archive; not restore-tested):
`/Users/vadimdulub/Documents/artline-masterpieces-backup-20260910.R133SB/before-masterpieces.dump`

SHA256: `8500a11931a2cf97c29b5f3ebec57b29a952f79d702a6bcbb380d0631b213b0f`

Selection SHA256:
`c08d47bcc3cc03bb6d598e9484836f94066831b2d54d925cc3f4c9bf2669b4aa`

Receipts: `output/masterpieces-{preview,apply,replay}-v1.json`,
`output/masterpieces-state-{before,after,replay}.json`, and
`output/masterpieces-api-verification-v1.json`.

## Reusable workflow

From `apps/server`, with the explicitly configured local `DATABASE_URL`:

```sh
go run ./cmd/review-masterpieces -mode audit -out /absolute/new-coverage.json
go run ./cmd/review-masterpieces -mode stage -out /absolute/new-batch/selection.json
go run ./cmd/review-masterpieces -mode preview -selection /absolute/new-batch/selection.json -sha256 REVIEWED_SHA256 -out /absolute/new-preview.json
go run ./cmd/review-masterpieces -mode apply -selection /absolute/new-batch/selection.json -sha256 REVIEWED_SHA256 -out /absolute/new-receipt.json
```

Staging does not download pictures or write to the database. Review and pin the
selection, take a backup and baseline, then explicitly apply. Evidence expires
after 24 hours. Use new paths: source captures and receipts are immutable.
Transfers have a 512 MiB execution ceiling, a 4 MiB per-image ceiling and pacing;
403/429 or three consecutive failures pause that host without retrying it.
