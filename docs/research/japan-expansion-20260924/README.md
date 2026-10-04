# Japanese artworks — 24 September 2026

Added **36 artworks and 36 CC0 museum images to the local catalogue**: 29
paintings and seven prints, across 31 artists. Created 23 named artist profiles
and added documented Japanese cultural affiliations to seven existing profiles.
Every new artist and artwork remains in **review**, with no publication or
production import.

Examples include Katsushika Ōi's *Operating on Guan Yu's Arm*, Kiyohara
Yukinobu's *Autumn in Takao*, two paintings by Tawaraya Sōtatsu, landscapes by
Sōami and Tani Bunchō, and prints by Ippitsusai Bunchō and Hosoda Eishi.
The complete delivery is in [added-artworks.csv](added-artworks.csv).

## Scope and evidence

Read-only planning inspected 260 current Cleveland Museum of Art records:
two bounded pages of 100 paintings and one page of 60 prints. Selection favored
breadth, with at most three artworks per artist and a ceiling of 60 additions.
Thirty-six passed source, attribution, date, physical-object and identity review.
Only their selected primary images were downloaded.

The museum's [Open Access policy](https://www.clevelandart.org/open-access)
and each exact object's `share_license_status=CC0`, accession, primary-image
URL, creator, and creation interval were captured before download. Raw metadata,
retrieval timestamps and SHA-256 receipts are in `captures/` and `discovery.json`.
`plan.json` and `plan-pin.json` fix the final selection. Earlier plans are retained
as superseded research, not imported selections.

Accepted holding assertions require the museum's `legal_status=accessioned` and
`on_loan=false`. No display claims, museum-highlight designations, or personal
masterpiece rankings were added. Existing creator biographies and dates were
preserved. Missing life dates remain unknown; new profiles use the documented
work interval for their activity timeline when a complete lifespan is absent.

## Identity and date decisions

- Chōbunsai Eishi was linked to existing Hosoda Eishi using Getty ULAN
  [500121365](https://www.getty.edu/vow/ULANFullDisplay?find=500119324&nation=&role=&subjectid=500121365)
  and agreeing birth/death years. No duplicate profile was created.
- Yamamoto Kanae matches existing Kanae Yamamoto by reordered full name and both
  life years; the same-title artwork requires physical-object reconciliation,
  so this candidate was held.
- Four proposed works by Ike Taiga remain held because the catalogue contains
  separate Ike Taiga and Ike no Taiga profiles. Neither existing profile nor
  its works was merged or deleted.
- *Forbidden to the Vulgar* (CMA 140435) remains held. Its displayed date,
  “late 1800s–early 1900s,” conflicts with the numeric interval 1765–1820 and
  the named artist's lifetime. No year was invented and no image downloaded.
- Anonymous or qualified creators, multipart records, conflicting biographies,
  duplicates and uncertain dates remain documented in the final plan's held list.

Seven existing profiles gained sourced `JP` cultural-affiliation relationships:
Gion Nankai, Kiyohara Yukinobu, Murase Taiitsu, Okumura Masanobu, Sakai Hoitsu,
Shūgetsu Tōkan and Tani Bunchō. This makes 23 previously recorded works part of
the Japan-linked audit cohort in addition to the 36 new records. These older
works were neither re-imported nor re-dated; their existing review/visibility
rules still apply.

## Verification

`verification.json` confirms all 36 records, creator associations, exact source
dates and types, accepted holding evidence, citations, media-rights evidence,
review states, absence of publication/display claims, and image checksums.
Existing artist-row preimages and existing country relationships were preserved.

Every image was visually inspected in contact sheets. Full frames, orientation
and proportions were retained; the largest served JPEG is **98,871 bytes**.
The faint appearance of CMA 135273 is present in its source image and was not
artificially enhanced. `visual-review.json` records the inspection and pins the
image manifest. Source originals and preserved contact sheets are archived below.

| Local Japan-linked cohort | Before | After |
|---|---:|---:|
| Artists | 117 | 147 |
| Artworks | 4,579 | 4,638 |
| Artworks dated through 1970 | 4,447 | 4,488 |
| Artworks with primary images | 2,877 | 2,916 |

The larger cohort increase includes existing works of the seven newly linked
artists; **only 36 artworks and 36 images were inserted** in this pass.

Eleven offline regression tests passed, covering date uncertainty and the 1970
boundary, conflicting source dates, attributions, loans, multipart objects,
image rights and object identity, unknown life dates, and image compression.
No test database or catalogue fixtures were created. Tests run with:

```sh
/tmp/artline-japan-20260924-venv/bin/python -m unittest ops/test_expand_japan_20260924.py
```

An initial transaction rolled back on the editor-account foreign key; it left
no imported data. The successful atomic import uses the existing research editor
account. The exact successful recovery preimage path is in `applied.json`.
The local API was unavailable during optional HTTP checks, so this pass asserts
database and file verification, not browser/API rendering verification.

## Recovery and files

- Validated pre-import PostgreSQL dump: 640,969,822 bytes; hash and archive path
  in `backup.json`. No restore or secondary database was created.
- Backups, locked preimages, operation scripts and contact sheets:
  `/Users/vadimdulub/Library/Application Support/Artline/backups/japan-expansion-20260924/`.
- Downloaded source reproductions and receipt hashes:
  `/Users/vadimdulub/Library/Application Support/Artline/source-images/japan-expansion-20260924/`.
- Served images:
  `apps/web/public/assets/artworks/imported/japan-expansion-20260924/`.
- Import and verification receipts: `applied.json`, `verification.json`;
  image manifest: `images.json`; identity decisions: `identity-review.json`.

No production writes, publication, deployment, commits, Terraform actions,
existing-artwork edits, or deletions were performed.
