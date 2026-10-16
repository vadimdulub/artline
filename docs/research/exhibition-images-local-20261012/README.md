# Exhibition galleries and local images — 12 October 2026

The user clarified **“Exhibited artwork images first”**, asked to add missing
pictures into our system, and requested no external navigation links. The
700-exhibition local review now opens with the artwork gallery. Its artwork and
artist navigation stays inside Artline; source URLs remain in the evidence.

Preview: http://127.0.0.1:3107/exhibitions

## Delivery

| Measure | Result |
| --- | ---: |
| Local exhibitions with every listed work illustrated | 700 |
| Illustrated source artwork identities | 9,936 |
| Illustrated exhibition appearances | 10,506 |
| New local image attachments | 9,928 |
| Existing catalogue images preserved | 8 |
| New Artsy object images | 9,903 |
| New Cleveland museum object images | 25 |
| New derivative file bytes | 595,043,224 |
| Database writes / production deployments | 0 |

These are **image additions to existing local exhibition objects**. They are not
new artworks in the production/main catalogue. Artwork dates, attributions,
canonical links and participation evidence are unchanged. In particular, the
283 object-history participation connections and 10,223 public-listing connections
retain their different evidence levels. Images do not independently prove
physical installation, ownership, current display or every touring stop.

The larger 108,969-exhibition archive remains accessible. This complete image
coverage applies to the selected 700 events, not the entire archive.

## Images and evidence

Artsy images come from the exact native artwork/image associations already
collected for these exhibitions. No artist/title similarity search substitutes
an image from a different version, edition or source object. The bounded
selection was prepared before downloading; the eight existing images were
excluded from the download list.

The Cleveland API omitted images for 25 copyrighted records. Their exact public
museum object pages supplied the primary images. All were checked against the
object's accession number and image filename. For *Nude (Study for The Harem)*,
object `173643`, accession `1932.719`, the museum uses the legacy image filename
`435.1932_w.jpg`. Its exact page, primary image, title and visual description were
reviewed together; the exception has its own receipt. The nine progressive proofs
and the portfolio view of *Two Nude Women* retain their separate identities and
images. All 33 museum exhibition entries are now illustrated.

Originals are archived outside Documents. Derivatives preserve the full source
frame and proportions, with a maximum of 100,000 bytes per file. No generated
content, reconstruction or cropping was used. Four exceptional image dimensions
were reviewed individually: one narrow colour-stripe work and three long silk
compositions. The scrolls use the larger source versions returned by the same
native artwork records. Their limited source resolution and full composition
are preserved.

Actual supplied rights labels and credits are retained, including copyrighted
and unknown labels. The user's instruction authorizes this selected **local**
preview workflow; it is not recorded as an independently obtained licence or
production/public-commercial clearance. Images are served from our own local
`/assets/artworks/exhibitions-local/` paths, with no provider hotlinks in rendered
images. The API/source page and file URLs remain in the research evidence.

Fifteen groups share an identical original image across different provider
object IDs. All have the same recorded creator label; the objects remain separate
because an identical photograph does not establish identical editions/impressions.
They are recorded in `shared-source-images.json`.

## Interface

- Exhibition detail starts with the full-frame artwork gallery and its
  internal artwork links. About, venues, artists and research notes follow.
- Directory records include three actual exhibition artwork previews.
- Artwork pages display the saved image, metadata, internal artist links and
  documented exhibition history.
- Outbound object, artist, press-release and source-image links were removed
  from exhibition browsing. Credits, provider names, factual uncertainty and
  source notes remain as text/disclosures. Provenance data was not deleted.
- Existing member access controls are preserved: artwork and artist records
  are public, while museum navigation retains its sign-in prompt.
- Existing paper, ink and stone tokens, Georgia/Avenir typography, full-frame
  image treatment and bounded Go-owned pagination are retained.

## Storage and repeatability

```text
~/Library/Application Support/Artline/source-metadata/exhibition-images-local-20261012/
  baseline.json.gz
  selected.json.gz
  images/<local-artwork-id>.json
  museum-images/<local-artwork-id>.json
  reviewed-images/<local-artwork-id>.json
  originals/<sha256>.bin
  museum-image-legacy-filename-evidence.json
  handscroll*-image-research.json
  hundred-oxen-image-research.json
  visual-sample-*-pass.json
  shared-source-images.json
  review-corpus.json
  report.json
  verification.json
```

Derivatives live in the ignored local asset directory
`apps/web/public/assets/artworks/exhibitions-local/`. The updated corpus is also
written to the existing launcher's `exhibitions-deep-local-20261011/review-corpus.json`.
Both earlier local corpus builders reapply this image overlay on repeat builds.
No original source file or unrelated artwork asset was removed.

```sh
/tmp/artline-cesi-venv/bin/python ops/exhibition_images_local.py prepare
/tmp/artline-cesi-venv/bin/python ops/exhibition_images_local.py download
/tmp/artline-cesi-venv/bin/python ops/exhibition_images_local.py museum
/tmp/artline-cesi-venv/bin/python ops/exhibition_images_local.py build
/tmp/artline-cesi-venv/bin/python ops/exhibition_images_verify.py
/tmp/artline-cesi-venv/bin/python ops/exhibition_artworks_verify.py
```

The first three collection steps are resumable. Initial technical exceptions
remain in their immutable attempt records; reviewed outcomes take precedence.
Restart the owned loopback research API after rebuilding its corpus. The
existing `ops/exhibitions_local_preview.py` launcher remains usable.

## Validation

The automated image audit checks every new original and derivative hash, image
format, dimensions, aspect ratio, size cap and exact source object association.
It checks all 700 exhibition image counts and one served image per exhibition.
The artwork API audit traverses every object and all bidirectional appearances.

Both complete audits passed: 9,928 new image files, 700 served-image checks,
9,936 artwork responses and all 10,506 appearance connections. TypeScript,
targeted ESLint and all seven browser scenarios passed. Desktop and phone axe
checks reported no violations, and the final directory/gallery screenshots
were visually inspected.

Visual review covered 97 systematically sampled or museum images plus every
exceptional aspect ratio and the legacy museum filename case. Unsampled files
were technically verified, not claimed to have been individually viewed.

Browser coverage includes directory thumbnails, gallery-first ordering, internal
image clicks, same-origin image requests, absence of outbound exhibition links,
evidence filters, repeated artwork appearances and museum member prompts. Layout
and accessibility checks cover desktop/tablet/phone widths through 320px.
The in-app browser connection again failed during bootstrap, so the project's
Chrome/Playwright workflow was used. Browser artifacts are under
`/tmp/artline-exhibition-gallery-final/`.

This bounded local collection does not establish production ingestion or
ten-million-record performance. No account, session or catalogue fixtures were
created in either database.
