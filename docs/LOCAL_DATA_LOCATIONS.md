# Local Artline data

## Historical research archives — 9 October 2026

Large historical research payloads and snapshots last modified before 1 October
2026 were compressed and moved out of the project during the requested storage
cleanup. The archives, per-file SHA-256 manifests, removal receipts and recovery
utility are under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/project-cleanup-20261009/`

The cleanup archived 50,959 files (46.90 GB) into 177 verified archives
(5.16 GB), and removed 1,139 generated files (0.77 GB). Net space reclaimed,
including the retained archive and audit files, was approximately **42.5 GB**
(decimal units). All 151,239 public files were unchanged, and all 22,301
protected application test-data files remained present.

Historical reports retain their original repository-relative evidence paths.
If one of those files is absent, consult `archive-summary.json` and the
`*.manifest.json` files in that directory. Each `.tar.zst` archive also embeds
its file manifest. Every member was decompressed and checksum-verified before
its original was removed; originals changed during cleanup were retained.

Restore a file to its original location with the supplied utility (requires
Python 3 and `zstd`):

```sh
python3 "/Users/vadimdulub/Library/Application Support/Artline/backups/project-cleanup-20261009/restore.py" \
  --path docs/research/production-release-20260927/before/local-snapshot.json
```

Use `--prefix docs/research/production-release-20260927/` for an entire archived
research group, `--list` to inspect matches, or `--destination /tmp/artline-restored`
to restore elsewhere. The utility verifies archive and file hashes and refuses
to overwrite existing files. Restore archived inputs before rerunning historical
one-off import or research commands.

The cleanup retained Markdown reports, tracked files, artwork assets, research
modified on or after 1 October, and data groups referenced by application tests.
It made no database changes. Stale Python bytecode, Finder metadata and the unused
Turbopack cache were deleted separately; the running Webpack development server
and its cache were preserved. Exact counts and sizes are recorded in
`cleanup-summary.json` in the archive directory.

## Additional 2,000 Nordic artworks — 8 October 2026

The [second Nordic continuation report](research/nordic-2000-20261008/README.md)
records 2,000 additional production review artworks: 310 at Denmark's SMK,
773 at Sweden's Nationalmuseum and 917 at Norway's National Museum. Earlier
additions and existing objects were excluded from this new-object count.
Source captures, the pinned plan, delivery CSV and verification receipts are
under `docs/research/nordic-2000-20261008/`. Superseded research plans remain
explicitly marked and were never applied. Existing catalogue metadata and images
were preserved, no new images were attached, and the real local catalogue was
unchanged. National museum coverage remains incomplete; the original institution
and object-source gap ledger still applies.

Recovery plans, locked preimages and transaction postimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/nordic-2000-20261008/`.
Cloud SQL backup `1791484855597` completed before the atomic insert transaction.

## Additional 1,000 Nordic artworks — 8 October 2026

The [Nordic continuation report](research/nordic-1000-20261008/README.md) records
1,000 new production review artworks and documented collection links across
12 institutions: 45 in Denmark, 597 in Sweden and 358 in Norway. Existing artwork
records were excluded from this count. Source captures, the final plan, delivery
CSV and verification receipts are under `docs/research/nordic-1000-20261008/`.
No existing artwork, artist or institution metadata was updated, and the real
local catalogue was unchanged. This pass attached no new images.

Recovery plans, locked preimages and transaction postimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/nordic-1000-20261008/`.
Cloud SQL backup `1791482654794` completed before the atomic insert transaction.

## Nationwide Greek museum catalogue and images — 8 October 2026

The [Greek museum delivery](research/greek-museums-20261008/README.md) records
621 new production review artworks, one existing artwork newly linked to its
museum, 73 new institutions and 500 verified primary-image attachments. Greece
now has 80 collections with 1,264 catalogue works. All 214 official directory
entries have a coverage ledger; 173 still need individual-object research.
The real local catalogue was queried read-only and its baseline counts remained
unchanged. No test databases, fixtures, application deployment or commit were made.

Source captures, immutable plans, applied receipts, CSV ledgers and checks are
under `docs/research/greek-museums-20261008/`. Before/after snapshots use
`/Users/vadimdulub/Library/Application Support/Artline/backups/greek-museums-20261008/`;
Cloud SQL backup `1791471559641` completed before writes. Source originals and
contact sheets use the matching `source-images/greek-museums-20261008/` directory.
Accepted derivatives use `apps/web/public/assets/artworks/imported/greek-museums-20261008/`
and matching create-only production bucket paths. Research holds and superseded
source interpretations are preserved; they are not additional delivered images.

## Denmark, Sweden and Norway museums — 8 October 2026

The [Nordic collection report](research/nordic-museums-20261008/README.md) records
109 new production review artworks, 40 new institutions, additional evidence for
24 existing artworks, and geography/authority updates for 25 existing institutions.
Source captures, the pinned plan, delivery and gap ledgers, and verification
receipts are under `docs/research/nordic-museums-20261008/`. The real local
catalogue was queried read-only. Existing images and publication states were preserved.

Recovery plans, locked preimages and transaction postimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/nordic-museums-20261008/`.
Cloud SQL backup `1791475818698` succeeded before writes. No image files were
downloaded or attached in this collection-coverage pass.

## Painter opening artworks — 8 October 2026

The [key-artwork report](research/painter-key-artworks-20261008/README.md) records
17,313 local and 17,353 production painter selections, with 10,191 and 10,216
illustrated choices respectively. The user explicitly requested writes to the
local `artline` catalogue and production for this operation. New catalogue records
remain in review; unresolved dates, identities and unavailable images are recorded.

Preimages and release artifacts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/key-artworks-20261008/`.
Source reproductions and review sheets use the matching
`source-images/painter-key-artworks-20261008/` directory. Accepted new derivatives
use `apps/web/public/assets/artworks/imported/painter-key-artworks-20261008/` and the
same image-bucket prefix. No test databases or catalogue/member fixtures were made.

## Local to production catalogue alignment — 8 October 2026

The [alignment report](research/catalogue-alignment-20261008/README.md) records
6,200 new review artworks, 108 institutions, 6,500 documented holding assertions
and their missing sources and relationships. Production's existing data and
images were preserved; 201 artwork identities were reused. The local database
was read-only. Cyprus geography was repaired and the explicitly approved API
visibility fix was deployed: the country filter now returns 22 collections,
including Cyprus Museum with 102 works.

Immutable plans, preimages, source packages and service configurations are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/catalogue-alignment-20261008/`.
Cloud SQL backup `1791456055193` completed before writes. The delivery CSV,
receipts, source decisions and verification results are in the report directory;
temporary release files and PDF review renders remain in `/tmp`.

## Abbey House Museum collection — 8 October 2026

The [Abbey House Museum report](research/abbey-house-museum-20261008/README.md)
records 15 new production artworks, two existing artworks newly linked to the
museum and enrichment of its previously linked artwork. All 18 records remain
in review and passed database and live API checks. Source captures, the pinned
plan, delivery CSV and receipts are under `docs/research/abbey-house-museum-20261008/`.
The real local database was queried read only. Existing images were preserved;
this catalogue pass uploaded no new application images.

Production preimages and after-states are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/abbey-house-museum-20261008/`;
Cloud SQL backup `1791455220484` completed before writes. Visual comparison
references, procedures and logs use the matching `source-images/` directory.

## Local image recovery production sync — 8 October 2026

The [production sync report](research/production-local-image-recovery-20261008/README.md)
verifies all 1,214 recovered images: 1,024 new primary images, 44 new alternate
images and 146 identical existing images reused with additional evidence.
Production retained 190 existing primary images, catalogue metadata and
publication states. All 1,214 database attachments and public image checksums
passed, together with 46 museum artwork API samples. No local data was changed.

The pinned package, plan, delivery CSV, upload receipts and final verification
are under `docs/research/production-local-image-recovery-20261008/`.
Recovery snapshots are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/production-local-image-recovery-20261008/`;
Cloud SQL backup `1791453150679` completed before writes. Final procedures and
logs use the matching `source-images/production-local-image-recovery-20261008/procedures/completed/`
directory. Local JPEGs and source originals remain in their original recovery
operation directories. Production uses corresponding asset paths in the
`artline-508319-images` bucket, with create-only writes for 1,068 new objects.

## Le Havre, Rouen and Cyprus production collection — 6 October 2026

The [museum collection report](research/havre-rouen-cyprus-20261006/README.md)
records 208 new production artworks, 24 existing metadata updates and 71 image
attachments. The real local catalogue was queried read-only. Source captures,
immutable plans, applied receipts and verification results are under
`docs/research/havre-rouen-cyprus-20261006/`.

Production preimages and rollback evidence are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/havre-rouen-cyprus-20261006/`;
Cloud SQL backup `1791309359006` completed before the writes. Source originals
and reviewed contact sheets use the matching `source-images/` directory.
The 71 application derivatives use
`apps/web/public/assets/artworks/imported/havre-rouen-cyprus-20261006/`, with
matching create-only uploads in the production image bucket. Existing assets,
source rights labels and artwork review state were preserved.

The [combined missing-image recovery report](research/local-image-recovery-20261006/README.md)
records 1,214 verified local image attachments across 2,321 distinct reviewed
artworks on 5–7 October 2026. The operation-specific locations follow below.

## Further Chicago local images — 7 October 2026

The [sixty-record review](research/local-chicago-more-images-20261007/README.md)
adds 59 verified CC0 photographs and preserves one inventory conflict for review.
JPEGs: `apps/web/public/assets/artworks/imported/local-chicago-more-images-20261007/`.
Originals, visual sheets, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-chicago-more-images-20261007/`.
Locked preimages use the matching `backups/` directory. Nine individual creator
reviews, three title concordances and three explicit view labels are preserved.

## Remaining seven-artist local images — 7 October 2026

The [twenty-record review](research/local-wikiart-russian-next-final-leads-images-20261007/README.md)
adds seven verified WikiArt images and retains thirteen unresolved records, including
one current native creator conflict. JPEGs:
`apps/web/public/assets/artworks/imported/local-wikiart-russian-next-final-leads-images-20261007/`.
Originals, native references, alternatives, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-next-final-leads-images-20261007/`.
Locked preimages use the matching `backups/` directory. Four unknown source dates,
two absent original titles, biography differences and three view limitations are preserved.
The [seventeen-artist discovery](research/local-wikiart-russian-next-artists-20261007/README.md)
is fully reviewed: 68 leads, 41 attached, 27 unresolved, zero pending.

## Savrasov, Somov and Bakst local images — 7 October 2026

The [twenty-three-record comparison](research/local-wikiart-savrasov-somov-bakst-images-20261007/README.md)
adds fourteen verified WikiArt images and retains nine different versions as unresolved.
JPEGs: `apps/web/public/assets/artworks/imported/local-wikiart-savrasov-somov-bakst-images-20261007/`.
Originals, native references, alternatives, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-savrasov-somov-bakst-images-20261007/`.
Locked preimages use the matching `backups/` directory. Source rights, unknown dates,
medium/holding discrepancies and five source-view qualifications are retained.
The [seventeen-artist discovery](research/local-wikiart-russian-next-artists-20261007/README.md)
now has 48 of 68 leads reviewed: 34 attached, fourteen held and twenty pending.

## Konchalovsky local image recovery — 7 October 2026

The [twenty-five-record comparison](research/local-wikiart-konchalovsky-images-20261007/README.md)
adds twenty verified local WikiArt images and retains five different versions as unresolved.
JPEGs: `apps/web/public/assets/artworks/imported/local-wikiart-konchalovsky-images-20261007/`.
Originals, native references, alternatives, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-konchalovsky-images-20261007/`.
Locked preimages use the matching `backups/` directory. Source watermarks and actual restricted
rights labels remain intact. Unknown local creator life fields are unchanged.
The [seventeen-artist discovery](research/local-wikiart-russian-next-artists-20261007/README.md)
has 25 of 68 leads reviewed, with twenty attached, five unresolved and 43 pending.

## Remaining Russian Museum title variants — 7 October 2026

The [seventeen-record comparison](research/local-wikiart-russian-final-title-variants-images-20261007/README.md)
adds one verified local Roerich image with an explicit source-framing qualification.
JPEG: `apps/web/public/assets/artworks/imported/local-wikiart-russian-final-title-variants-images-20261007/`.
Originals, native references, alternatives, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-final-title-variants-images-20261007/`.
The locked preimage uses the matching `backups/` directory.
All 222 title-variant leads are reviewed: 99 attached, 123 unresolved and zero pending.

## Further Russian Museum versions — 7 October 2026

The [sixteen-record version review](research/local-wikiart-russian-further-versions-images-20261007/README.md)
adds four verified local WikiArt images: two Bilibin illustrations and two Nesterov works.
JPEGs: `apps/web/public/assets/artworks/imported/local-wikiart-russian-further-versions-images-20261007/`.
Originals, native references, alternatives, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-further-versions-images-20261007/`.
Locked preimages use the matching `backups/` directory. Three source reproductions have explicit
view qualifications; the monochrome Lazarus image preserves unknown source years.
The sixteen-lead discovery queue is fully reviewed: four attached and twelve unresolved.

## Russian Museum metadata review and further artist discovery — 7 October 2026

The [42-record subject review](research/local-wikiart-russian-subject-mismatch-review-20261007/README.md)
rejects unsuitable fuzzy source suggestions without downloading images or writing to the database.
Its procedures use `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-subject-mismatch-review-20261007/procedures/`.
The title-variant queue now has 205 reviewed: 98 attached, 107 unresolved and 17 pending.
The separate [eight-artist discovery](research/local-wikiart-russian-further-artists-20261007/README.md)
found 16 exact-title leads among 641 eligible gaps. Its procedures and artist-selection evidence use
the matching `source-images/local-wikiart-russian-further-artists-20261007/procedures/` directory.
No visual approvals or new images are implied by these metadata-only findings.

## Roerich, Serov and Commons portrait review — 7 October 2026

The [seven-record visual review](research/local-wikiart-roerich-serov-final-leads-images-20261007/README.md)
adds one verified local Serov image and retains six unresolved Roerich versions.
JPEG: `apps/web/public/assets/artworks/imported/local-wikiart-roerich-serov-final-leads-images-20261007/`.
Originals, native references, alternatives, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-roerich-serov-final-leads-images-20261007/`.
Locked preimages use the matching `backups/` directory.
The separate [four-record Commons metadata review](research/local-russian-commons-portrait-review-20261007/README.md)
made no image downloads or database writes; procedures use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-russian-commons-portrait-review-20261007/procedures/`.
At that checkpoint the title-variant queue had 163 of 222 records reviewed: 98 attached, 65 unresolved and 59 pending.

## Malevich Suprematism image recovery — 7 October 2026

The [two-inventory review](research/local-wikiart-malevich-suprematism-images-20261007/README.md)
adds two verified local WikiArt images and completes the seven-artist exact-title queue:
26 reviewed, 23 attached, three unresolved and zero pending.
JPEGs: `apps/web/public/assets/artworks/imported/local-wikiart-malevich-suprematism-images-20261007/`.
Originals, native references, alternatives, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-malevich-suprematism-images-20261007/`.
Preliminary metadata and native-reference procedures use the adjacent
`source-images/local-wikiart-malevich-suprematism-review-20261007/` directory.
Locked preimages use the matching `backups/` directory. One lower source edge is qualified.

## Malevich and Filonov image recovery — 7 October 2026

The [fifteen-record review](research/local-wikiart-malevich-filonov-images-20261007/README.md)
adds thirteen verified local WikiArt images. Black Square and Narva Gates remain unresolved versions.
Source date and medium differences are preserved; one source date remains unknown and one lower image edge is qualified.
JPEGs: `apps/web/public/assets/artworks/imported/local-wikiart-malevich-filonov-images-20261007/`.
Originals, native photographs, alternatives, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-malevich-filonov-images-20261007/`.
Locked preimages use the matching `backups/` directory. At that checkpoint the seven-artist queue had
24 reviewed: 21 attached, three unresolved and two pending Suprematism records.

## Alexandre Benois image recovery — 7 October 2026

The [nine-record review](research/local-wikiart-benois-images-20261007/README.md)
adds eight verified local images with actual Public domain US source labels retained as restricted.
Four drawing frames carry explicit margin qualifications. The original alphabet-cover drawing remains unresolved.
JPEGs: `apps/web/public/assets/artworks/imported/local-wikiart-benois-images-20261007/`.
Originals, native photographs, alternatives, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-benois-images-20261007/`.
Locked preimages use the matching `backups/` directory. The separate
[seven-artist discovery](research/local-wikiart-russian-modern-artists-20261007/README.md)
had nine of 26 leads reviewed at that checkpoint: eight attached, one unresolved and seventeen pending.
Its discovery procedures use the matching `source-images/local-wikiart-russian-modern-artists-20261007/procedures/` directory.

## Roerich landscape versions — 7 October 2026

The [six-record review](research/local-wikiart-roerich-landscape-versions-images-20261007/README.md)
adds one verified local image of Stronghold (Lhasa), preserving source 1942 and catalogue 1947 separately.
Five records remain unresolved after version review. JPEG:
`apps/web/public/assets/artworks/imported/local-wikiart-roerich-landscape-versions-images-20261007/`.
Originals, native photographs, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-roerich-landscape-versions-images-20261007/`.
Locked preimages use the matching `backups/` directory. At that checkpoint the 222-lead title-variant queue had
152 reviewed records: 97 attached, 55 unresolved and 70 awaiting individual image review.

## Further Russian Museum studies — 7 October 2026

The [twelve-record review](research/local-wikiart-russian-further-studies-images-20261007/README.md)
adds one verified local image, Repin’s Maria Artsybasheva drawing, with an explicit outer-paper-margin qualification.
Eleven records remain unresolved after version review. JPEG:
`apps/web/public/assets/artworks/imported/local-wikiart-russian-further-studies-images-20261007/`.
Originals, native photographs, comparisons, procedures and logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-further-studies-images-20261007/`.
Locked preimages use the matching `backups/` directory. The 222-lead title-variant queue now has
146 reviewed records: 96 attached, 50 unresolved and 76 awaiting individual image review.

## Polenov Abbey image review — 7 October 2026

The [individual review](research/local-wikiart-polenov-abbey-image-20261007/README.md)
adds one verified local WikiArt image through an exact authority-linked Commons photograph.
Source circa 1875 and catalogue/authority 1911 remain separate; unknown catalogue fields are preserved.
JPEG: `apps/web/public/assets/artworks/imported/local-wikiart-polenov-abbey-image-20261007/`.
Originals, comparison photograph, visual sheets, procedures and phase logs:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-polenov-abbey-image-20261007/`.
Locked preimages use the matching `backups/` directory. The earlier read-only discovery
is retained separately under `local-polenov-abbey-image-review-20261007`.
All 71 eight-artist exact-title leads have now been reviewed: 38 attached and 33 unresolved.

## Four Russian artists image review — 7 October 2026

The [fifteen-record review](research/local-wikiart-russian-four-artists-images-20261007/README.md)
adds five local WikiArt images and preserves ten unresolved version matches.
Source/catalogue dates remain distinct; one Surikov study has an explicit lower-paper-edge qualification.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-four-artists-images-20261007/`.
Originals, native photographs, alternatives, comparison sheets, procedures and phase logs are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-four-artists-images-20261007/`;
locked preimages use the matching `backups/` directory. The eight-artist discovery now has
70 leads reviewed, 37 images attached, 33 held and one Polenov Abbey lead pending.

## Shishkin image review — 7 October 2026

The [twelve-record review](research/local-wikiart-shishkin-images-20261007/README.md)
adds four local WikiArt images and preserves eight unresolved composition matches.
One source date remains unknown under an exact native study proof; the study frame and one printed design have explicit qualifications.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-shishkin-images-20261007/`.
Originals, native photographs, alternatives, comparison sheets, procedures and phase logs are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-shishkin-images-20261007/`;
locked preimages use the matching `backups/` directory. The eight-artist discovery now has
55 leads reviewed, 32 images attached, 23 held and sixteen leads pending.

## Levitan image review — 7 October 2026

The [twelve-record review](research/local-wikiart-levitan-images-20261007/README.md)
adds seven local WikiArt images and preserves five unresolved composition matches.
One printed design and two painting/pastel frames have explicit view qualifications.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-levitan-images-20261007/`.
Originals, native photographs, alternatives, comparison sheets, procedures and phase logs are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-levitan-images-20261007/`;
locked preimages use the matching `backups/` directory. The eight-artist discovery now has
43 leads reviewed, 28 images attached, fifteen held and 28 leads pending.

## Kuindzhi version review — 7 October 2026

The [fifteen-record version review](research/local-wikiart-kuindzhi-versions-images-20261007/README.md)
adds seven local WikiArt images and preserves eight unresolved version matches.
Three source dates remain unknown under individual native date proofs; four views are explicitly qualified.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-kuindzhi-versions-images-20261007/`.
Originals, native photographs, alternatives, comparison sheets, procedures and phase logs are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-kuindzhi-versions-images-20261007/`;
locked preimages use the matching `backups/` directory. The eight-artist discovery now has
31 leads reviewed, 21 images attached, ten held and forty leads pending.

## Kuindzhi and Mashkov image recovery — 7 October 2026

The [sixteen-record review](research/local-wikiart-kuindzhi-mashkov-images-20261007/README.md)
adds fourteen local WikiArt images, including five explicitly qualified source frames.
The separate [eight-artist discovery](research/local-wikiart-russian-additional-artists-20261007/README.md)
records 71 title leads among 322 eligible gaps; 55 of its leads still await individual review.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-kuindzhi-mashkov-images-20261007/`.
Originals, private alternatives, native photographs, comparison sheets and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-kuindzhi-mashkov-images-20261007/`;
locked preimages use the matching `backups/` directory. Two different mountain versions remain unresolved.
Discovery procedures and artist-selection evidence use the sibling
`source-images/local-wikiart-russian-additional-artists-20261007/procedures/` directory.

## Russian Museum untranslated-index matches — 7 October 2026

The [twelve-record review](research/local-wikiart-russian-untranslated-index-images-20261007/README.md)
adds six local WikiArt images, including five individual English/native title reconciliations and three qualified portrait views.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-untranslated-index-images-20261007/`.
Originals, private alternatives, native photographs, comparison sheets and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-untranslated-index-images-20261007/`;
locked preimages use the matching `backups/` directory. Six different physical versions remain unresolved.

## Russian Museum expanded-name matches — 7 October 2026

The [twelve-record review](research/local-wikiart-russian-expanded-names-images-20261007/README.md)
adds twelve local WikiArt images, preserving one individually reviewed unknown source date and one qualified printed design.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-expanded-names-images-20261007/`.
Originals, private alternatives, native photographs, comparison sheets and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-expanded-names-images-20261007/`;
locked preimages use the matching `backups/` directory.

## Russian Museum portraits and figure studies — 7 October 2026

The [sixteen-record review](research/local-wikiart-russian-portraits-figures-images-20261007/README.md)
adds three local WikiArt images, including one explicitly described monochrome source.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-portraits-figures-images-20261007/`.
Originals, private alternatives, native photographs, comparison sheets and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-portraits-figures-images-20261007/`;
locked preimages use the matching `backups/` directory. Thirteen different objects or versions remain unresolved.

## Russian Museum prints and landscapes — 7 October 2026

The [sixteen-record review](research/local-wikiart-russian-prints-landscapes-images-20261007/README.md)
adds eight local WikiArt images, including seven explicitly qualified printed designs.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-prints-landscapes-images-20261007/`.
Originals, private alternatives, native photographs, comparison sheets and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-prints-landscapes-images-20261007/`;
locked preimages use the matching `backups/` directory. Seven landscapes and one hand-coloured lithograph remain unmatched.

## Additional Russian Museum title variants — 7 October 2026

The [twenty-one-record review](research/local-wikiart-russian-additional-title-variants-images-20261007/README.md)
adds seventeen local WikiArt images, preserving three monochrome sources and a qualified drawing view.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-additional-title-variants-images-20261007/`.
Originals, private alternatives, native photographs, comparison sheets and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-additional-title-variants-images-20261007/`;
locked preimages use the matching `backups/` directory. Four distinct physical versions remain unmatched.

## More Russian Museum title variants — 7 October 2026

The [twenty-three-record review](research/local-wikiart-russian-more-title-variants-images-20261007/README.md)
adds eighteen local WikiArt images, including an explicitly labelled detail of a Repin study.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-more-title-variants-images-20261007/`.
Originals, private alternatives, native photographs, comparison sheets and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-more-title-variants-images-20261007/`;
locked preimages use the matching `backups/` directory. Five distinct physical versions remain unmatched.

## Further Russian Museum title variants — 7 October 2026

The [twenty-one-record review](research/local-wikiart-russian-further-title-variants-images-20261007/README.md)
adds nineteen local WikiArt images, including an explicitly framed monochrome portrait view.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-further-title-variants-images-20261007/`.
Originals, private alternatives, native photographs, comparison sheets and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-further-title-variants-images-20261007/`;
locked preimages use the matching `backups/` directory. The school and seated-Orlova studies remain unattached.

## Russian Museum title variants — 7 October 2026

The [thirteen-record review](research/local-wikiart-russian-title-variants-images-20261007/README.md)
adds twelve local WikiArt images with individually resolved title spellings and physical versions.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-title-variants-images-20261007/`.
Originals, private alternatives, native references, comparison sheets and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-title-variants-images-20261007/`;
locked preimages use the matching `backups/` directory. The panoramic Serov Ж-4288 remains unattached.
The metadata-only [222-lead discovery](research/local-wikiart-russian-title-variants-20261007/README.md)
now retains 88 additional records awaiting individual image review after the subsequent passes.

## Remaining Russian Museum title leads — 7 October 2026

The [thirteen-record review](research/local-wikiart-russian-remaining-leads-images-20261007/README.md)
adds nine local images, including five explicitly qualified printed designs.
JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-remaining-leads-images-20261007/`.
Originals, private alternatives, native references, contact sheet and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-remaining-leads-images-20261007/`;
locked preimages use the matching `backups/` directory. Four records remain unattached.
The [91-title-lead live audit](research/local-wikiart-russian-leads-20261006/title-lead-review-outcomes-20261007.json)
records 51 attachments and forty remaining gaps across this bounded discovery.

## Serov drawings with undated WikiArt sources — 7 October 2026

The [six-record drawing review](research/local-wikiart-serov-undated-drawings-images-20261007/README.md)
adds the exact Bakst portrait, with unknown source dates and individual native date evidence preserved.
The JPEG is under
`apps/web/public/assets/artworks/imported/local-wikiart-serov-undated-drawings-images-20261007/`.
Originals, private alternatives, native references, contact sheet and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-serov-undated-drawings-images-20261007/`;
locked preimages use the matching `backups/` directory. Five records remain unattached.

## Russian Museum WikiArt drawing studies — 7 October 2026

The [five-record study review](research/local-wikiart-russian-studies-images-20261007/README.md)
adds one local image. The JPEG is under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-studies-images-20261007/`.
Originals, alternatives, native references, contact sheet and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-studies-images-20261007/`;
locked preimages use the matching `backups/` directory. Four records remain unattached.
An exact Commons Pompeii reproduction is retained under `private-commons-alternatives/`
with a documented originating-source permission hold.

## Russian Museum WikiArt self-portrait drawings — 7 October 2026

The [six-record self-portrait review](research/local-wikiart-russian-self-portraits-images-20261007/README.md)
adds five local images. Application JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-self-portraits-images-20261007/`.
Originals, unused alternatives, native references, contact sheet and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-self-portraits-images-20261007/`;
locked preimages use the matching `backups/` operation directory. Bryullov’s unfinished
drawing remains unmatched. Serov’s source-frame limitation and date conflict are explicit.

## Further Serov and Roerich WikiArt images — 6 October 2026

The [nine-record follow-up](research/local-wikiart-serov-roerich-followup-images-20261006/README.md)
adds three local images. Application JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-serov-roerich-followup-images-20261006/`.
Originals, unused alternatives, native references, contact sheet and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-serov-roerich-followup-images-20261006/`;
locked preimages use the matching `backups/` operation directory. Six different
physical works remain unmatched. Source dates and all catalogue values are preserved.

## Kustodiev WikiArt drawings and portraits — 6 October 2026

The [nine-record drawing/portrait review](research/local-wikiart-kustodiev-drawings-images-20261006/README.md)
adds eight local images. Application JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-kustodiev-drawings-images-20261006/`.
Originals, unused alternatives, native references, contact sheet and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-kustodiev-drawings-images-20261006/`;
locked preimages use the matching `backups/` operation directory. One illustration
remains unmatched. Source dates and all catalogue values are preserved.

## Repin WikiArt studies — 6 October 2026

The [nine-record version/title review](research/local-wikiart-repin-images-20261006/README.md)
adds four local images. Application JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-repin-images-20261006/`.
Originals, unused alternatives, native references, contact sheet and procedures are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-repin-images-20261006/`;
locked preimages use the matching `backups/` operation directory. Five records remain
unmatched. Two source-frame limitations and all catalogue values are preserved.

## Petrov-Vodkin WikiArt versions — 6 October 2026

The [nine-record version/date review](research/local-wikiart-petrov-vodkin-images-20261006/README.md)
adds four local images. Application JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-petrov-vodkin-images-20261006/`.
Originals, unused candidate images, native references, contact sheet and procedures
are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-petrov-vodkin-images-20261006/`;
locked preimages use the matching `backups/` operation directory. Five different physical
works remain unmatched. Source discrepancies and all catalogue fields are preserved.

## Serov and Roerich WikiArt versions — 6 October 2026

The [eight-record exact-version review](research/local-wikiart-serov-roerich-images-20261006/README.md)
adds six local images. Application JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-serov-roerich-images-20261006/`.
Originals, unused candidate images, native references, contact sheet and procedures
are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-serov-roerich-images-20261006/`;
locked preimages use the matching `backups/` operation directory. Two separate paper
studies remain unmatched. All catalogue fields and review status are preserved.

## Russian Museum alternative image versions — 6 October 2026

The [nine-record alternative-version review](research/local-wikiart-russian-followup-images-20261006/README.md)
adds seven local images. Application JPEGs are under
`apps/web/public/assets/artworks/imported/local-wikiart-russian-followup-images-20261006/`.
Originals, unused candidate reproductions, native references, contact sheet and procedures
are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-followup-images-20261006/`;
locked preimages use the matching `backups/` operation directory. Two different physical
versions remain unattached. Catalogue values and review status are preserved.

## Russian Museum WikiArt versions — 6 October 2026

The [eight-record physical-version review](research/local-wikiart-russian-images-20261006/README.md)
and [alternate Kustodiev painting](research/local-wikiart-bathing-image-20261006/README.md)
add three local images. Application files use their corresponding operation directories
under `apps/web/public/assets/artworks/imported/`. Originals, private native references,
rejected derivatives, contact sheets and procedures use the same operation names under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/`; locked preimages
use the matching `backups/` directories. Five reviewed records remain unresolved.
The separate metadata-lead audit is archived under `source-images/local-wikiart-russian-leads-20261006/`.

## Papaloukas WikiArt photographs — 6 October 2026

The [two-record Greek museum review](research/local-wikiart-papaloukas-images-20261006/README.md)
adds two images under `apps/web/public/assets/artworks/imported/local-wikiart-papaloukas-images-20261006/`.
Downloaded sources, private museum references, the contact sheet and procedures use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-papaloukas-images-20261006/`;
locked preimages use the corresponding `backups/local-wikiart-papaloukas-images-20261006/` directory.
The existing illustrated portrait duplicate is preserved. Both actual source rights
labels remain restricted, separately from the user’s WikiArt approval.

## Moronobu native photograph — 6 October 2026

The [Getty/LoC creator review](research/local-chicago-moronobu-image-20261006/README.md)
adds one image under `apps/web/public/assets/artworks/imported/local-chicago-moronobu-image-20261006/`.
The original, contact sheet and procedures use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-chicago-moronobu-image-20261006/`;
the locked preimage uses the matching `backups/local-chicago-moronobu-image-20261006/` directory.
All local biography fields and review status remain unchanged. This resolves the
last hold from the preceding sixty-record selection.

## Further Chicago photographs and creator reviews — 6 October 2026

The [next sixty-record selection](research/local-chicago-further-images-20261006/README.md)
adds 51 images under `apps/web/public/assets/artworks/imported/local-chicago-further-images-20261006/`.
Its [eight-record authority follow-up](research/local-chicago-further-authorities-20261006/README.md)
adds eight images under `apps/web/public/assets/artworks/imported/local-chicago-further-authorities-20261006/`.
Originals, contact sheets and procedures use the matching operation directories under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/`;
locked preimages use the matching directories under `backups/`.
Canaletto’s pictured component is explicitly labelled. Moronobu was subsequently resolved above;
all catalogue metadata, creator biographies and review status remain unchanged.

## Individually reviewed Chicago creator identities — 6 October 2026

The [25-record individual creator review](research/local-chicago-reviewed-authorities-20261006/README.md)
adds 23 images under `apps/web/public/assets/artworks/imported/local-chicago-reviewed-authorities-20261006/`.
Originals, the privately held sideways portrait, contact sheets and procedures use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-chicago-reviewed-authorities-20261006/`;
locked preimages use the matching `backups/local-chicago-reviewed-authorities-20261006/` directory.
Two records remain held. Existing biography fields and creator links remain unchanged;
qualified Sadeler and Zuccaro source attributions are explicit in image credits and accessible text.

## Further local Chicago photographs — 6 October 2026

The [sixty-record Chicago review](research/local-chicago-breadth-images-20261006/README.md)
adds 48 images under `apps/web/public/assets/artworks/imported/local-chicago-breadth-images-20261006/`.
Originals, contact sheets and research procedures use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-chicago-breadth-images-20261006/`;
locked preimages use the matching `backups/local-chicago-breadth-images-20261006/` directory.
At that checkpoint twelve records were held; subsequent individual decisions are linked above. Four attached images have explicit page/recto labels.

## WikiArt under explicit source approval — 6 October 2026

The [individual WikiArt incomplete-data review](research/local-wikiart-catalogue-review-images-20261006/README.md)
adds ten images under `apps/web/public/assets/artworks/imported/local-wikiart-catalogue-review-images-20261006/`.
Originals, private comparisons and review procedures use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-catalogue-review-images-20261006/`;
locked preimages use the matching `backups/local-wikiart-catalogue-review-images-20261006/` directory.
Nine unknown creation dates, all existing creator links and the Cardiff institution’s blank Wikidata ID remain unchanged.
Bosch’s reproduction explicitly identifies its three interior panels.

The [individual WikiArt alternative-image review](research/local-wikiart-version-correction-images-20261006/README.md)
adds two images under `apps/web/public/assets/artworks/imported/local-wikiart-version-correction-images-20261006/`.
Originals, private comparisons, the contact sheet and research procedures use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-version-correction-images-20261006/`;
locked preimages use the matching `backups/local-wikiart-version-correction-images-20261006/` directory.
These resolve the earlier Matisse and Degas version holds while preserving the rejected photographs privately.

The [local reuse of earlier WikiArt research](research/local-wikiart-reused-images-20261006/README.md)
adds 66 images under `apps/web/public/assets/artworks/imported/local-wikiart-reused-images-20261006/`.
Verified originals, private native/authority comparisons, thirteen held derivatives,
contact sheets and research procedures use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-reused-images-20261006/`;
locked preimages use `backups/local-wikiart-reused-images-20261006/`.
Fifteen records were held at that checkpoint, including two earlier print-impression retractions.
The Matisse and Degas records subsequently received the separately reviewed alternatives described above.

The [local WikiArt selection](research/local-wikiart-approved-images-20261006/README.md)
adds 58 images under `apps/web/public/assets/artworks/imported/local-wikiart-approved-images-20261006/`.
Originals, three contact sheets and two held derivatives use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-approved-images-20261006/`;
locked preimages use the matching `backups/local-wikiart-approved-images-20261006/` directory.
The research directory retains source-page captures, creator crosswalks, actual rights
labels and a separate receipt for the user's newly confirmed source approval. The two
held public files are absent; their catalogue records remain unchanged.

The [local WikiArt follow-up](research/local-wikiart-followup-images-20261006/README.md)
adds 59 further images under `apps/web/public/assets/artworks/imported/local-wikiart-followup-images-20261006/`.
Originals and three contact sheets use the matching
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-followup-images-20261006/`
directory; locked preimages use `backups/local-wikiart-followup-images-20261006/`.
Source labels and printed reproduction credits are retained separately from user approval.

The [local WikiArt artwork-crosswalk operation](research/local-wikiart-crosswalk-images-20261006/README.md)
adds three images under `apps/web/public/assets/artworks/imported/local-wikiart-crosswalk-images-20261006/`.
Originals, private museum/authority comparison images and the contact sheet use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-crosswalk-images-20261006/`;
locked preimages use the corresponding `backups/local-wikiart-crosswalk-images-20261006/` directory.

## Chicago and Rijksmuseum follow-up images — 6 October 2026

The [Chicago selection](research/local-chicago-native-images-20261006/README.md)
adds 36 images under `apps/web/public/assets/artworks/imported/local-chicago-native-images-20261006/`.
Selected originals and the two reviewed contact sheets use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-chicago-native-images-20261006/`;
locked preimages use the matching `backups/local-chicago-native-images-20261006/` directory.
Three source sheets have explicit recto labels; their reverse subjects are not shown.
The [Chicago discovery audit](research/local-chicago-native-audit-20261006/README.md)
contains metadata only and does not represent 4,056 approved or downloaded images.

The [further Chicago selection](research/local-chicago-followup-images-20261006/README.md)
adds 31 images under `apps/web/public/assets/artworks/imported/local-chicago-followup-images-20261006/`.
Its originals and contact sheets use `source-images/local-chicago-followup-images-20261006/`
and its locked preimages use `backups/local-chicago-followup-images-20261006/`, both under
`/Users/vadimdulub/Library/Application Support/Artline/`. The individual Rousseau
native-title discrepancy and Renoir recto qualification remain in image attribution
and source evidence; all existing catalogue facts are preserved.

The [additional Chicago selection](research/local-chicago-next-images-20261006/README.md)
adds fifty images, and the [published-download recovery](research/local-chicago-download-recovery-20261006/README.md)
adds ten previously held images. Application JPEGs use the respective
`apps/web/public/assets/artworks/imported/local-chicago-next-images-20261006/` and
`apps/web/public/assets/artworks/imported/local-chicago-download-recovery-20261006/` directories.
Originals and contact sheets use the matching operation names under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/`; locked preimages
use the matching names under `backups/`. Exact source grants, historical HTTP failure
receipts and explicit sketchbook-page/recto decisions remain in the research directories.

The [Rijksmuseum follow-up](research/local-rijks-followup-images-20261006/README.md)
adds six images under `apps/web/public/assets/artworks/imported/local-rijks-followup-images-20261006/`.
Originals and the review sheet use `source-images/local-rijks-followup-images-20261006/`
and locked preimages use `backups/local-rijks-followup-images-20261006/`, both under
`/Users/vadimdulub/Library/Application Support/Artline/`. Exact native collection pages,
image-service and policy captures remain in the corresponding research directories.

## Rijksmuseum image recovery — 6 October 2026

The [Rijksmuseum selection](research/local-rijks-native-images-20261006/README.md)
adds five images under `apps/web/public/assets/artworks/imported/local-rijks-native-images-20261006/`.
Original reproductions, the approved review sheet and a rejected 71 × 85 pixel
grey source thumbnail use `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-rijks-native-images-20261006/`;
locked preimages use the matching `backups/local-rijks-native-images-20261006/` directory.
The grey thumbnail has no public derivative or database attachment. Current native
Linked Art, EDM, collection pages and image-service receipts remain in the research directory.
The [Smithsonian source audit](research/local-saam-native-audit-20261006/README.md)
preserves fourteen current object records and the relevant metadata shards only;
it created no image files or database records.

## Current SMK image recovery — 6 October 2026

The [current SMK selection](research/local-smk-current-images-20261006/README.md)
adds two images under `apps/web/public/assets/artworks/imported/local-smk-current-images-20261006/`.
Original photographs, approved and rejected review sheets and the rejected black
primary reproduction use `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-smk-current-images-20261006/`;
locked preimages use the matching `backups/local-smk-current-images-20261006/` directory.
The black primary derivative is absent from the public folder and was never attached.
The complete current metadata index is retained separately under
`docs/research/local-smk-current-metadata-20261006/metadata/`; it contains metadata only.

## Finnish National Gallery image recovery — 6 October 2026

The [Finnish National Gallery selection](research/local-fng-native-images-20261006/README.md)
adds seventeen images under
`apps/web/public/assets/artworks/imported/local-fng-native-images-20261006/`.
Original photographs, the SHA-pinned current metadata export and visual review
sheet use `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-fng-native-images-20261006/`;
locked preimages use the matching `backups/local-fng-native-images-20261006/` directory.
Source ownership, artist identity comparisons, a narrower source date range and
one monochrome qualification remain in the evidence. Existing catalogue metadata
and holdings were preserved. The [SMK native review](research/local-smk-native-image-20261006/README.md)
retains metadata and four 404 image findings; it created no local image files.

## Local Walters image recovery — 6 October 2026

The combined report lists twelve Walters operations with 290 active attachments.
Their application JPEGs use `apps/web/public/assets/artworks/imported/<operation>/`.
Original images and contact sheets use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/<operation>/`;
locked preimages use the matching `backups/<operation>/` directories.
The latest operation directories are `local-walters-authority-followup-images-20261006`,
`local-walters-authority-later-images-20261006` and
`local-walters-asset-concordance-images-20261006`, plus
`local-walters-authority-next-images-20261006` and
`local-walters-reviewed-panel-image-20261006`, plus
`local-walters-authority-modern-images-20261006`. The latter retains an explicitly
labelled album-cover view, a complete open Russian triptych and an exact-photo
download fallback with its original empty response preserved privately. The
`local-walters-authority-final-images-20261006` operation adds five further
Brödel/Burroughs images using the same source and backup directory pattern. The separately documented
[creator-qualification correction](research/local-walters-creator-qualification-20261006/README.md)
retains its own correction preimages. The failed empty Bonvin response remains
private in the later-authority operation's source archive; its verified replacement
has a separate hash and receipt.

## Reviewed Byzantine icon face — 6 October 2026

The [independent icon photograph](research/local-byzantine-reviewed-face-image-20261006/README.md)
uses `apps/web/public/assets/artworks/imported/local-byzantine-reviewed-face-image-20261006/`.
Original bytes and its review sheet use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-byzantine-reviewed-face-image-20261006/`;
locked preimages use the matching `backups/` directory. The exact photographed
face and photographer credit are retained, while the catalogue date remains unknown.

## Further Commons and priority review — 6 October 2026

The [further Commons review](research/local-commons-next-images-20261006/README.md)
adds one archival monochrome Fabritius reproduction from 100 new records.
Its JPEG uses `apps/web/public/assets/artworks/imported/local-commons-next-images-20261006/`.
Original bytes and the review sheet use
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-commons-next-images-20261006/`;
locked preimages use the matching `backups/` directory. The source's monochrome
limitation and RKD credit remain in the database. The
[native priority audit](research/local-open-museum-priority-images-20261006/README.md)
and [Byzantine review](research/local-byzantine-commons-image-review-20261006/README.md)
retain metadata-only evidence for 26 further artworks; no images were downloaded for them.

The [later Commons review](research/local-commons-later-images-20261006/README.md)
adds one full-frame archival monochrome Dou reproduction from 80 further records.
Its JPEG uses `apps/web/public/assets/artworks/imported/local-commons-later-images-20261006/`.
The original and contact sheet use `source-images/local-commons-later-images-20261006/`
and locked preimages use `backups/local-commons-later-images-20261006/` within the
Artline Application Support root. The separate
[Cleveland source review](research/local-cleveland-commons-images-20261006/README.md)
retains metadata-only evidence for four held records and downloads no images.

## Local Warsaw image recovery — 6 October 2026

The [current-inventory Commons review](research/local-commons-multiple-images-20261006/README.md)
adds two Warsaw portraits, and the [native self-portrait review](research/local-commons-warsaw-followup-20261006/README.md)
adds one. Their JPEGs use `apps/web/public/assets/artworks/imported/` with operation
names `local-commons-multiple-images-20261006` and `local-commons-warsaw-followup-20261006`.
Originals, contact sheets and validation controls use those names under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/`; locked
preimages use the matching `backups/` directories. Native policy and current
inventory crosswalk captures remain with the linked reports. An old numeric
Warsaw link now points to another object, so only exact current inventory matches
were accepted. File/database checks passed; recent HTTP verification remains incomplete.

## Local Academy Vienna image recovery — 6 October 2026

The [Academy image report](research/local-academy-images-20261006/README.md)
records 26 verified local attachments from 80 reviewed missing-image artworks.
The [follow-up](research/local-academy-followup-images-20261006/README.md) adds
thirteen images; the [reconciled cases](research/local-academy-reconciled-images-20261006/README.md)
add eight; the [person-reference review](research/local-academy-person-review-20261006/README.md)
adds ten more from already reviewed records. The [identity and date review](research/local-academy-identity-followup-20261006/README.md)
adds another nineteen. The [inventory/date review](research/local-academy-inventory-review-20261006/README.md)
and [self-portrait reverse](research/local-academy-verso-image-20261006/README.md) add twelve.
Across these operations, 101 distinct artworks were reviewed and 88 pictures attached. Follow-up and reconciled files, originals and backups
use the corresponding `local-academy-followup-images-20261006` and
`local-academy-reconciled-images-20261006`, `local-academy-person-review-20261006`
and `local-academy-identity-followup-20261006`, plus
`local-academy-inventory-review-20261006` and `local-academy-verso-image-20261006`,
operation names in the directories below.
Each photograph has exact native museum CC BY 4.0 evidence and photographer
credit. Catalogue metadata and review status remain unchanged. The JPEGs live
in `apps/web/public/assets/artworks/imported/local-academy-images-20261006/`.
Originals and visual review sheets are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/local-academy-images-20261006/`;
locked transaction preimages use the matching `backups/` directory. Source
captures and verification receipts remain in the linked report directories. Recent
HTTP checks timed out; the latest attachments have complete file/database checks.

## Local missing-image recovery — 5–6 October 2026

The [Commons recovery report](research/local-commons-recovery-20261005/README.md)
preserves the earlier eleven-image checkpoint. A further 120 Commons reviews
added one picture, while three earlier attachments were withdrawn after an
additional source-policy review. The current Commons contribution is twelve
pictures across 600 distinct reviewed artworks, with further
alternate-file revisits. One additional Warsaw artwork first checked on Commons
was resolved with the museum's native image, described above.
Files, database links and source rights were verified. Earlier local HTTP checks
passed; the latest checks timed out on the existing Next.js server. All artworks
retain review status; production was not changed. Eight initially attached
museum-source images have been withdrawn in total. Their evidence and bytes are
preserved privately and they are excluded from the twelve-image Commons count.

Application JPEGs use `apps/web/public/assets/artworks/imported/` with the
`local-commons-recovery-20261005`, `local-commons-alternates-recovery-20261006`
and `local-commons-followup-recovery-20261006` directory names, plus
`local-commons-priority-followup-20261006` for the latest Commons picture. Original
reproductions and visual review sheets use the same operation names under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/`.
Locked preimages and correction recovery snapshots use the corresponding
`backups/` directories. The rejected KHM-set reproduction remains private under
`source-images/local-commons-khm-recovery-20261006/`.

## Local Wien Museum image recovery — 6 October 2026

The [exact photograph recovery](research/local-wien-native-image-20261006/README.md)
and [native follow-up](research/local-wien-followup-images-20261006/README.md), plus
the [identity reconciliation](research/local-wien-reconciled-images-20261006/README.md), attach
eleven museum photographs with exact CC BY 4.0 photographer credits. Application
JPEGs, source-image archives and locked preimage backups use the operation names
`local-wien-native-image-20261006`, `local-wien-followup-images-20261006` and
`local-wien-reconciled-images-20261006` under
the same roots described above. Public source captures and individual decisions
remain in the linked research directories; the shared discovery metadata is at
`docs/research/local-commons-wien-native-leads-20261006/`. Database and file checks
passed; recent HTTP delivery checks remain incomplete because the existing
local Next.js server timed out.

## Local NGA image recovery — 6 October 2026

The [NGA image report](research/local-nga-native-images-20261006/README.md) records
seven CC0 images from exact current native downloads. Application JPEGs, source
archives and locked preimage backups use `local-nga-native-images-20261006`
under the roots above. The [metadata audit](research/local-nga-open-image-audit-20261006/README.md)
preserves the discovery findings and fresh native captures; the immutable official
image index remains in `docs/research/museum-gaps-20261005/open-images-01/metadata/nga/`.
Database, source rights and file verification passed; HTTP delivery checks remain
incomplete because the existing local Next.js server timed out.

## Africa, Asia and Cyprus expansion — 5 October 2026

The [selected regional expansion](research/africa-asia-cyprus-20261005/README.md)
added 177 local review artworks, 14 artist profiles and 43 visually inspected
WikiArt public-domain-labelled pictures: 50 African works, 112 Asian works and
15 Cyprus-related works. Thirty-seven missing, sourced artist-country links
were added. The same batch was delivered to production on 5 October 2026;
all new records remain in review, available through the existing research preview.

The validated pre-import dump (782,000,069 bytes), pinned plan and transaction
preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/africa-asia-cyprus-20261005/`.
The 44 downloaded originals, including one rejected advertising composite,
are in the matching `source-images/africa-asia-cyprus-20261005/` directory.
The 43 served JPEGs are each under 100,000 bytes and live in
`apps/web/public/assets/artworks/imported/africa-asia-cyprus-20261005/`.
Source captures, rights labels, the complete artwork list and successful
database/API verification receipts remain in the linked research directory.
Production Cloud SQL backup `1791221858401`, transaction preimages and archived
delivery scripts are recorded under the backup directory's `production/`
subdirectory. Production plan, import, storage and successful live verification
receipts are in the research directory's `production/` subdirectory.

## All-category artwork coverage — 25–26 September 2026

The [preset review](research/preset-clarity-review-20260925/README.md) now finds
illustrated artworks in all 30 default categories. This pass added 26 selected
local review records and images across three bounded operations:

- `arab-world-images-20260925`: 12 objects from Egypt, Syria and Iraq;
  validated pre-import dump 641,447,127 bytes.
- `preset-artwork-gaps-20260925`: 12 Met objects for early cities, classical
  antiquity, Buddhism and the Sahel; dump 641,509,275 bytes.
- `digital-art-roots-20260925`: two public-domain paintings with documented
  influence on computer art; dump 641,546,594 bytes.

Each recovery dump, pinned plan and operation snapshot is under
`/Users/vadimdulub/Library/Application Support/Artline/backups/<operation>/`.
Original reproductions and receipts use the matching `source-images/<operation>/`
directory. Full-frame served JPEGs are under
`apps/web/public/assets/artworks/imported/<operation>/`, each at most 100,000 bytes.
Research evidence remains in the matching `docs/research/<operation>/` folder;
disposable browser proof images are in `/tmp`. All 26 records remain in review.
No publication or production upload was performed.

## Further Islamic-world images — 25 September 2026

The [second selected set](research/islamic-world-more-20260925/README.md) added
20 local review artworks and images, bringing the Islamic-world preview to 32.
This includes new origin coverage for Samarkand/Uzbekistan and Afghanistan.
The first 12 artworks remain unchanged; no records were published or uploaded
to production.

Recovery dump (641,318,685 bytes), exact preimages, pinned plans, operation
snapshots and visual review evidence are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/islamic-world-more-20260925/`.
Original downloaded reproductions and receipts are in the matching
`source-images/islamic-world-more-20260925/` directory. Served full-frame JPEGs
are under `apps/web/public/assets/artworks/imported/islamic-world-more-20260925/`;
the largest new derivative is 99,664 bytes. Research evidence is preserved in
the linked research directory; browser proof images remain in `/tmp`.

## Islamic-world images — 25 September 2026

The [selected Islamic-world import](research/islamic-world-images-20260925/README.md)
added 12 local review artworks and 12 visually reviewed CC0 museum images: tiles,
ceramics, calligraphy, illustrated manuscripts, metalwork and carved architecture.
All remain in review; no production publication or upload was performed.

The validated 641,247,621-byte recovery dump, pinned selection and locked preimages
are under `/Users/vadimdulub/Library/Application Support/Artline/backups/islamic-world-images-20260925/`.
Downloaded originals and receipts are under the matching
`source-images/islamic-world-images-20260925/` directory. Full-frame application
JPEGs are in `apps/web/public/assets/artworks/imported/islamic-world-images-20260925/`;
the largest is 99,096 bytes. Source captures and application/verification receipts
remain in the research directory. Disposable browser proofs are in `/tmp`.

## Japanese artwork expansion — 24 September 2026

The [Japan expansion](research/japan-expansion-20260924/README.md) added 36 local
review artworks (29 paintings and seven prints), 23 named creator profiles and
36 visually reviewed CC0 museum images. Seven existing creator profiles gained
sourced Japanese cultural-affiliation links; existing profile fields and
artworks were preserved. The artworks were subsequently published locally and in production on 25 September; see the publication record below.

The validated 640,969,822-byte pre-import dump, exact locked preimages, operation
scripts and visual review sheets are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/japan-expansion-20260924/`.
Downloaded source reproductions and receipts are in the matching
`source-images/japan-expansion-20260924/` directory. Application JPEGs are under
`apps/web/public/assets/artworks/imported/japan-expansion-20260924/`; the largest
is 98,871 bytes. Source captures, selection, identity decisions and verification
receipts remain in the research directory. The initial 24 September operation was local only.

## Japanese artwork publication — 25 September 2026

The [publication operation](research/japan-publication-20260925/README.md)
published the 36 Japanese artworks in the local and production catalogues and
uploaded their CC0 derivatives. Recovery data is under
`/Users/vadimdulub/Library/Application Support/Artline/backups/japan-publication-20260925/`:
a validated 641,238,814-byte local dump, the pinned plan and exact preimages.
Cloud SQL backup `1790320988908` completed before the production write.
All 36 public API records and served image checksums passed verification.
The [Edo museum scan](research/edo-japanese-museums-20260925/README.md)
retains 35 official page captures and a candidate list; no images or records
from that separate scan were imported.

## Russian icon image research — 21 September 2026

The [Russian icon image delivery](research/russian-icon-images-20260921/README.md)
attached 217 selected museum reproductions to existing local review records.
Recovery baselines and exact artwork/relationship preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/russian-icon-images-20260921/`.
Source originals are under the matching
`source-images/russian-icon-images-20260921/originals/` directory. Derivatives
are at most 100,000 bytes and live in
`apps/web/public/assets/artworks/imported/russian-icon-images-20260921/`.
Research captures, selection, visual decisions and verification receipts remain
in `docs/research/russian-icon-images-20260921/`. After the user's explicit upload
instruction, the [production delivery](research/russian-icon-images-20260921/production/README.md)
copied these 217 review artwork records and their evidence to production and
uploaded the matching GCS derivatives. Its exact export, production preflight,
locked recovery snapshot and post-import snapshot are in the backup directory's
`production/` subdirectory. Other image candidates remain local research records.

## General locations

The real database is PostgreSQL `artline` on localhost. Read-only audits query it directly. Never point fixture/destructive integration tests at this database; never create a test database as part of the collection workflow.

Authentic artwork files remain in `apps/web/public/assets/artworks/`, with database media associations and source/rights evidence. Research captures, pinned selections and application receipts are real provenance, not disposable test data.

Larger source-image evidence, when retained separately from the <=100,000-byte
application derivative, belongs under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/`.
The first such archive is `athens-icon-20260912/`: one original photograph and
its capture receipt, both hash-verified after relocation. It is not a test image
or an extra served web asset.

## Backups moved out of Documents

On11 September2026, the22 individually inspected top-level `Documents/artline-…backup…` directories were relocated, not deleted, to:

`/Users/vadimdulub/Library/Application Support/Artline/backups/`

Each original folder name and dump filename is retained. Historical reports retain their original paths for audit: replace the leading `/Users/vadimdulub/Documents/` with the backup root above to find the same dump. The relocation journal contains original/new paths and before/after SHA256 verification:

`output/data-collection-20260911-2016/backup-relocation.jsonl`

Future backups go under this dedicated folder, never scattered at the top of Documents. Keep the pre-mutation safety requirement; these are recovery snapshots, not extra live databases. This relocation does not reclaim disk space, and no backup was deleted.

## First GCP migration backup (12 September 2026)

The PostgreSQL archive used to populate project `artline-508319` is retained at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/gcp-migration-20260912/artline.dump`

SHA256: `1100961ded54f74b8ddda765fc7bdb49b2f098e5c9eabbb8ca0bc475e9a45837`.

The local catalogue and 644 original application images remain in their existing
locations. Cloud Storage contains copies in `gs://artline-508319-images/assets/`.
This initial migration does not establish ongoing replication. See
`docs/deployment-20260912.md` for deployment and migration validation.

## Armenian/Georgian research and Women artists filter (13 September 2026)

Recovery dump, selected original reproductions and the verified completion archive:

`/Users/vadimdulub/Library/Application Support/Artline/backups/armenian-georgian-women-20260913/`

The pre-mutation local dump is `local-before.dump`; the successful Cloud SQL
backup is `1789326954000`. Research, application receipts, image credits and
verification are in `docs/research/armenian-georgian-women-20260913/`.
The completed pass added 271 review artworks, 41 artist profiles and 38 images
to both databases. No existing records, backups or artwork assets were removed.

## Overnight country research (13–14 September 2026)

Recovery dumps and per-change preimages:

`/Users/vadimdulub/Library/Application Support/Artline/backups/overnight-countries-20260913/`

The initial `local-before.dump` and final `local-after-20260914.dump` are retained.
Final dump SHA-256: `7d45f811ebee2d69fc322758916e19c52eeb6e77abdcc9d63503d303ee2e8d24`.
Its archive directory was verified without restoring it or creating a test database.
The successful pre-import Cloud SQL backup is `1789326339640`.

Selected originals are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/overnight-countries-20260913/`;
served derivatives remain in `apps/web/public/assets/artworks/`.

The report, exact receipt membership, CSV package and pending production differences
are documented in [the research index](research/overnight-countries-20260913/README.md).
Later local updates await Cloud reauthentication; this is not a fully synchronized
post-run production backup. Historical facts, archived duplicates and assets were preserved.

### Resumed production delivery — 14 September 2026

The post-delivery local recovery dump is `local-after-resumed-20260914.dump` under the overnight backup directory above (399,013,814 bytes; SHA-256 `e578e736fdd08a69689aa931deb0a41424ef1016dc15df2859bc99e0820adf59`). Its archive directory was validated without a restore. Post-delivery Cloud SQL backup `1789364642427` completed successfully. Both receipts are linked from [the current research index](research/overnight-countries-20260913/README.md); earlier backups and handoffs remain preserved.

## Cypriot painters (14 September 2026)

The pre-import local recovery dump, selected originals and completed research archive are retained under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-painters-20260914/`

Cloud SQL backup `1789369991390` completed successfully before import. The bounded pass added 7 painter profiles (6 Cypriot, plus one explicitly active in Cyprus), 36 review artworks and 3 verified images to both databases. See the [research report and verification receipts](research/cypriot-painters-20260914/README.md). No existing catalogue records or artwork assets were deleted.

## Cypriot expansion (14 September 2026)

The next selected pass added 13 artist profiles, 31 review artworks and 19 licensed images to local and production. Recovery dump, selected originals and completed research archive are under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-expansion-20260914/`

Cloud SQL backup `1789372089497` completed before delivery. Combined Cyprus coverage is 20 artists, 67 artworks and 22 images. See the [expansion report and verification receipts](research/cypriot-expansion-20260914/README.md), including the preserved date disagreement and superseded image selection.


### Cypriot further expansion — 14 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-more-20260914/`.
- Contains validated local pre-import dump, selected image originals (including two rejected Venice views), cloud backup request and completed research archive.
- Cloud SQL pre-import backup: `1789376146123` (successful).
- Evidence and receipts: `docs/research/cypriot-more-20260914/`.
- Delivered to local and production: 7 new artists, 26 artworks, 11 licensed images. Existing Minas and Goul identities reused; all new records remain in review.


### Cypriot and Greek artist portraits — 14 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/cyprus-greece-portraits-20260914/`.
- Validated local pre-import dump, target-specific artist preimages, selected source originals and completed evidence archive.
- Cloud SQL pre-import backup: `1789379855575` (successful).
- Research, coverage inventory, gallery and verification: `docs/research/cyprus-greece-portraits-20260914/`.
- 22 artist portraits stored locally in `apps/web/public/assets/artists/imported/cyprus-greece/` and in GCS `artline-508319-images` under matching asset keys; attached in both databases. Private bucket access preserved; public images delivered through Artline.

### Spanish painters deep expansion — 17 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/spain-deep-20260916/`.
- Contains a validated pre-import local dump, exact preimages for the 74 existing artworks enriched in each target, and the successful pre-import Cloud SQL backup receipt.
- Research, selection, rights review, transaction receipts, post-delivery audit and verification: `docs/research/spain-deep-20260916/`.
- Delivered identically to local and production: 69 new artist profiles, 906 new review artwork records, evidence enrichment for 74 existing artworks, and 79 licensed images. All 79 served image files were checksum-verified; no records were published and no current-display claims were added.

### Spanish paintings image follow-up — 17 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/spain-images-followup-20260917/`; selected source originals are under the corresponding `source-images` directory.
- Cloud SQL pre-attachment backup `1789632648328` completed successfully. The local full dump and exact target preimages were validated before delivery.
- Evidence, visual review, transaction receipts, API smoke checks and public-file verification: `docs/research/spain-images-followup-20260917/`.
- Attached 27 additional licensed images to the same records in local and production. Twelve prepared alternatives were held because an existing primary image was present; no existing media or catalogue metadata was replaced.

### Japanese painters deep expansion — 17 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/japan-deep-20260917/`.
- The validated local pre-import dump is `local-before.dump` (SHA-256 `87e0631a01dea092a5cfee744ea7b357639ab6a9ebf421d3f83b2c8465fc2663`). Cloud SQL backup `1789640581717` completed successfully before delivery.
- Research, bounded discovery, authority evidence, visual review, per-record receipts, API smoke checks and public checksum verification: `docs/research/japan-deep-20260917/`.
- Delivered identically to local and production: 19 new named artist profiles, 27 new review paintings, 27 CC0 images, and source enrichment for eight existing Met objects. No records were published and no current-display claims were added.

## Marc Chagall painting additions (19 September 2026)

The verified pre-import archive and exact selected preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/chagall-paintings-20260919/`.
The local catalogue gained 10 sourced review paintings, bringing Chagall’s
painting count to 87. No images, publication or production delivery were included.
See [the selection and verification report](research/chagall-paintings-20260919/README.md).

## WikiArt collection and image-size delivery (19–20 September 2026)

Exact target preimages, migration recovery states and personal collection membership backups are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/wikiart-selected-images-20260919/`
and `.../backups/wikiart-artist-coverage-20260920/`.
Downloaded originals are under the corresponding `.../source-images/` campaign directories.
The follow-on backup directory's `existing-image-size-cap/` subdirectory preserves all 161 original oversized catalogue images and their database preimages.

Reports and delivery receipts: [initial selected images](research/wikiart-selected-images-20260919/README.md) and [artist-first expansion](research/wikiart-artist-coverage-20260920/README.md).
Served derivatives are at most 100,000 bytes; the separate original archives are not subject to that delivery limit.

The [next artist follow-up](research/wikiart-artist-followup-20260920/README.md) added 2,144 image attachments and 2,119 artwork records in both local and production catalogues after Google Cloud authentication was renewed. It also reconciled 23 earlier production image attachments and added owner-collection membership for 133 existing local and 129 existing production artworks. Its exact preimages and originals use the corresponding `wikiart-artist-followup-20260920` directories under `backups/` and `source-images/`, including `earlier-target-reconciliation/`, `existing-selection-coverage/` and archived `operation-scripts/`. Public-file, database and collection API verification passed; all three WikiArt passes now total 7,219 production image attachments.

## Frida Kahlo and women artists — 20 September 2026

Exact recovery preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/women-wikiart-20260920/`;
source originals use the corresponding `source-images/women-wikiart-20260920/`
directory. Research evidence and the complete 682-artist CSV are in
[the women-artists report](research/women-wikiart-20260920/README.md).

Delivered to both databases: 1,555 image attachments, including 1,534 new review
artworks and 21 existing-record image gaps, across 189 artists. Added 147 sourced
women-filter memberships and 275 artist review citations. Frida now has ten
illustrated works. All 1,556 uploaded files passed public checksum verification;
one duplicate reproduction remains unattached and its extra source identifier
is linked to the existing artwork. Artist metadata, review states, original
assets and prior provenance remain preserved.

## Armenian painter expansion — 20 September 2026

The [verified catalogue report](research/armenian-painters-20260920/README.md)
records 505 new active artist profiles, 1,027 new artwork records and 134 new
image attachments in both local and production databases. The collection now
contains 559 active Armenian-linked profiles and 1,485 linked artwork records.
All 137 uploaded image files are at most 100,000 bytes, including three public
alternate views that did not create additional artwork records.

Exact preimages, source-identity corrections, collection recovery states and
final operation scripts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/armenian-painters-20260920/`.
WikiArt originals use the matching `source-images/armenian-painters-20260920/`
directory; Commons originals are in the backup directory's
`museum-images/selected-originals/` subdirectory. Captures, per-record receipts,
full painter/artwork lists and successful final verification remain in the
research directory. New records retain review status and unknown fields.

## Byzantine and Russian icons and frescoes — 20 September 2026

The [verified research report](research/byzantine-russian-icons-frescoes-20260920/README.md)
records 804 new local review artworks: 777 icons and 27 fresco records, including
seven ensembles. Eight selected CC0 images are attached; 18 existing records
were preserved. This pass did not change production or publication state.

The validated 589,142,267-byte pre-import dump and exact batch, image and
date-correction preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/byzantine-russian-icons-frescoes-20260920/`.
Nine source originals are under the corresponding
`source-images/byzantine-russian-icons-frescoes-20260920/originals/` directory.
Eight approved application images and one retained, unattached panel view are
in `apps/web/public/assets/artworks/imported/byzantine-russian-20260920/`;
all nine derivatives are at most 100,000 bytes.

The [follow-up expansion](research/byzantine-russian-more-20260920/README.md)
added another 727 local review artworks: 616 icons and 111 fresco records,
with 23 verified CC0 image attachments. Across these two passes, the exact
receipts total 1,531 new works and 31 image attachments. Both passes remain
local and unpublished.

The follow-up's validated 620,943,496-byte pre-import dump and exact batch/image
preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/byzantine-russian-more-20260920/`.
Its 23 source originals use the corresponding
`source-images/byzantine-russian-more-20260920/originals/` directory.
Application JPEGs are in
`apps/web/public/assets/artworks/imported/byzantine-russian-more-20260920/`;
each is at most 99,579 bytes. The research directory retains the full selection,
all eight successful batch receipts, visual review and final verification.


## WikiArt 1000–1500 review — 20 September 2026

The [period review](research/wikiart-1000-1500-20260920/README.md) audited all
501 years and 1,175 dated WikiArt highlights across 100 creator/tradition
profiles. It added 450 review artworks with images to both databases, including
63 works dated wholly before 1300. All 451 delivered or already-attached image
associations passed public-file, database and provenance verification; the
largest derivative is 99,976 bytes. Nineteen prepared candidates remain held.

Exact preimages, five creator-kind corrections, operation scripts and visual
review evidence are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/wikiart-1000-1500-20260920/`.
Source originals use the corresponding
`source-images/wikiart-1000-1500-20260920/` directory. Research receipts include
the complete year-by-year audit, delivered artwork list and concurrent changes
outside this campaign. New records remain in review and belong to the personal
owner collection, without invented museum holdings.

## Top 100 painter expansion — 20 September 2026

The [complete cohort review](research/wikiart-top100-20260920/README.md)
audited all 100 selected painters and 29,628 WikiArt index entries. It added
1,037 review artworks and 1,093 image attachments to both local and production
databases, filling 56 existing image gaps across 97 painters. All uploaded
images passed public checksum verification and are at most 99,953 bytes.
Sixty-three prepared candidates remain held for duplicate or identity review.

Exact target preimages, thirteen existing production-ID reconciliations,
personal collection snapshots, visual review evidence and operation scripts
are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/wikiart-top100-20260920/`.
Source originals use the corresponding
`source-images/wikiart-top100-20260920/` directory. The research directory
contains the full 100-painter audit, delivered artwork list, source captures
and verification receipts. The Top 100 membership and ranking were preserved.

## Cyprus painter images — 20 September 2026

The [Cyprus coverage review](research/cyprus-images-20260920/README.md)
audited all 27 existing Cyprus-linked painters and delivered 57 image
attachments to both local and production databases: 22 existing image gaps
and 35 new review artworks across nine painters. The cohort now contains
128 artworks and 90 images. All 57 public image checksums and artwork API
responses passed verification; the largest derivative is 99,850 bytes.

Exact artwork/media preimages, personal collection snapshots, visual review
evidence, operation scripts and completion receipts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/cyprus-images-20260920/`.
Source originals use the corresponding
`source-images/cyprus-images-20260920/` directory. Application derivatives
are in `apps/web/public/assets/artworks/imported/cyprus-images-20260920/`.

One prepared attribution/title candidate remains unattached, with its original
and evidence preserved. The research report lists all 38 remaining image gaps:
26 later works, 11 unresolved dates and one missing exact-object photograph.
New records remain in review; source restrictions and credits were preserved
under the user's explicit Cyprus museum/artist source policy extension.

## Greek painter images — 20–21 September 2026

The [Greek coverage review](research/greek-images-20260920/README.md) audited
all 43 existing Greek-linked painter profiles and delivered 242 image
attachments to local and production: 93 existing image gaps and 149 new
review artworks across 41 profiles. Both catalogues now contain 609 artworks
and 444 images in this cohort. All 242 public image checksums and artwork API
responses passed verification; the largest derivative is 99,965 bytes.

Exact preimages, personal collection snapshots, five reconciled target-ID
mappings, visual review, operation scripts and completion receipts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/greek-images-20260920/`.
Original reproductions use the corresponding
`source-images/greek-images-20260920/` directory. Application derivatives are
in `apps/web/public/assets/artworks/imported/greek-images-20260920/`.

The research directory preserves source captures, per-painter coverage and
all 165 remaining image gaps: 106 unresolved dates, 10 works after the 1955
image cutoff, and 49 dated works needing source access or identity review.
Thirty-eight selected candidates remain held; one staged reproduction remains
unattached after its qualified creator attribution was identified. No existing
records or assets were removed. Actual rights labels and photographer credits
were retained, and 15 sourced icons use the existing object-form field.


## UK painters and selected artworks — 20–21 September 2026

The [UK coverage report](research/uk-painters-20260920/README.md) surveyed
10,514 source painter identities and resolved 327 named painters in WikiArt’s
British directory. This pass added 8,545 painter profiles, 18,882 artwork
records and 9,217 image attachments to both local and live catalogues.
All 9,284 uploaded files are public and at most 100,000 bytes; the largest
is 99,999 bytes. New records retain review status and unknown source fields.
The research directory includes full painter/artwork indexes, public alternate
links and unresolved identity/date decisions.

Artist/artwork preimages, selected Commons originals, six namesake correction
snapshots, receipt chains and archived operation scripts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/uk-painters-20260920/`.
Original WikiArt downloads are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/uk-painters-20260920/`.
Earlier artist baselines preserve alias text, not full alias-table row IDs.
Corrections preserve older artist records and their artworks; eight newly
created artworks retain their images on the corrected artist identities.

Final verification completed with zero errors across both databases, source
identities, review states, collection membership, image hashes and public APIs.
Forty-seven offline tests passed. No test databases or fixtures, commits,
Terraform changes or deployments were made for this pass.


UK production synchronization follow-up (21 September 2026): all 9,284 batch images were already present and matched their checksums. Added 37 missing personal-collection links in production. Recovery snapshots are under the UK backup root at `production-sync/collection-memberships/`; the production synchronization receipt is retained in the [UK research directory](research/uk-painters-20260920/README.md).

## Book languages and context — 22 September 2026

The [language audit](research/book-languages-20260922/README.md) covers all
10,000 existing books and records 170 confirmed corrections in local and
production, including 98 previously empty values. Exact baseline and transaction
preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/book-languages-20260922/`.

The [book and author context pass](research/book-context-20260922/README.md)
adds attributed Wikipedia introductions to 9,594 books and 3,782 creators.
Before/after checks preserve the language corrections, dates, creator links,
discovery memberships and review states. Full catalogue preimages, private
Cloud Run configuration snapshots, exact isolated release sources and build
receipts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/book-context-20260922/`.
Retained research responses and decisions remain in the two research directories.
Disposable browser screenshots and test outputs remain under `/tmp/`.

## Historical-period images — 26 September 2026

The [all-period review](research/period-images-20260926/README.md) adds 70 selected
Cleveland/NGA works and [two Pippin paintings](research/pippin-images-20260926/README.md)
to the local review catalogue. Originals and validated PostgreSQL recovery dumps
are respectively under `source-images/` and `backups/` within
`/Users/vadimdulub/Library/Application Support/Artline/`, in the campaign folders
`period-images-20260926/` and `pippin-images-20260926/`.
Source captures, pinned plans and verification receipts remain in the research
folders. Disposable browser screenshots and query-plan outputs are under `/tmp/`.


## Complete catalogue production release — 27 September 2026

The [release evidence](research/production-release-20260927/README.md) records the
full local catalogue comparison, selected image delivery, production transfer,
and application release. Private recovery/configuration/source archives are at
`/Users/vadimdulub/Library/Application Support/Artline/backups/production-release-20260927/`.
Cloud SQL backup `1790509197914` preserves the immediately preceding Women’s rights
publication. Disposable build sources, browser screenshots, and test logs are
under `/tmp/artline-release-20260927/`; catalogue research receipts remain in the
release evidence directory.


## Historical books and images — 4 October 2026

The [selected book expansion](research/books-5000bce-1850-20261004/README.md) added 29 review books and 15 creator profiles to local and production, plus 19 historical title-page images and 21 creator portraits. Exact target parity and all 40 public image checksums passed. Existing publication states and highlights were preserved.

Recovery dump, target preimages, release source manifests and Cloud SQL backup `1791141438127` receipts are under `/Users/vadimdulub/Library/Application Support/Artline/backups/books-5000bce-1850-20261004/`. Selected source reproductions are under the matching `source-images/books-5000bce-1850-20261004/` directory. Served JPEGs are at most 96,209 bytes and remain in `apps/web/public/images/{books,authors}/selected-20261004/`. Source captures and image-gap decisions are preserved in the research directory. No fixtures or test databases were created.

## Prado WikiArt production images — 6 October 2026

The [Prado delivery record](research/prado-wikiart-20261006/delivery/README.md)
documents 53 added image attachments: 47 new media assets and 6 reused,
verified WikiArt assets. Production Prado coverage increased from 183 to 236
images across 548 existing artworks. Their review states and metadata are preserved.

Recovery backup `1791275823126`, exact production preimages, the pinned plan,
after-images and operation scripts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/prado-wikiart-images-20261006/`.
Originals, visual-review contact sheets, held images and superseded derivatives
are under the matching `source-images/prado-wikiart-images-20261006/` directory.
Applied new derivatives are under
`apps/web/public/assets/artworks/imported/prado-wikiart-images-20261006/`;
reused assets retain their original paths. Research and verification receipts
remain under `docs/research/prado-wikiart-20261006/`. The local database was not changed.

The [subsequent deep research pass](research/prado-wikiart-20261006/deep-research-20261006/README.md)
added six more images, bringing coverage to 242 of 548 artworks. Recovery backup
`1791277486204`, exact preimages, after-images and operation scripts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/prado-wikiart-deep-20261006/`.
Selected originals, the visual contact sheet and the held Hiepes source image
are under the matching `source-images/prado-wikiart-deep-20261006/` directory.
The six served derivatives are under
`apps/web/public/assets/artworks/imported/prado-wikiart-deep-20261006/`.

The [Prado conflict-resolution pass](research/prado-wikiart-20261006/resolution-20261006/README.md)
added 11 further images, bringing coverage to 253 of 548 existing artworks.
Recovery backup `1791281469954`, exact preimages, after-images, the pinned plan
and operation scripts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/prado-wikiart-resolution-20261006/`.
Selected originals, the reviewed contact sheet and four additional identity-review
images are under the matching `source-images/prado-wikiart-resolution-20261006/`
directory. The 11 served derivatives are under
`apps/web/public/assets/artworks/imported/prado-wikiart-resolution-20261006/`.
The 53 additional artwork leads are metadata-only research records in the
research directory; they created no new database rows or image downloads.
All 548 records, all 11 public images and all 11 artwork API responses were verified.

The [random low-count painter expansion](research/low-count-200-painters-20261008/README.md)
added 8,926 production artwork records for 200 painters, each with 0–10 active
artworks at sampling time and 20–100 additions. All additions were verified in
PostgreSQL and through 282 bounded live catalogue API pages. This was a metadata
delivery; no new images were attached. The real local catalogue was never connected
to or changed. Cloud SQL backup `1791493265929`, per-painter preimages, final
snapshots, version-review evidence and execution logs are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/low-count-200-painters-20261008/`.
The fixed sample, source captures, plans, citations and per-painter CSV report are
preserved in the research directory linked above.

The [second random low-count painter expansion](research/low-count-200-painters-round2-20261009/README.md)
added 6,854 production artwork records for 200 additional painters, excluding the
previous batch. Each painter had 0–10 active artworks and received 20–76 additions.
All additions passed database verification and 239 bounded live catalogue API
pages, with no missing records. The additions remain in review; 3,220 dates are
explicitly unknown. No catalogue images were attached. Seven additional uncertain
creator records remain unlinked in review, and five new records from this operation
were archived during identity reconciliation; neither group counts toward the 6,854.
The original catalogue records and the real local database were unchanged.
Cloud SQL backup `1791526517310`, per-painter preimages, correction snapshots,
final snapshots and final operation code are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/low-count-200-painters-round2-20261009/`.
The cohort, immutable source plans, pinned amendments, source receipts and final
per-painter and per-artwork CSV reports remain in the research directory linked above.
