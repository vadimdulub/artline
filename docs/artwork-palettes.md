# Artwork image palettes

The palette appears only when an artwork is opened in full view. Regular record
pages, record drawers and gallery thumbnails have no colors or palette analysis.
Full view shows a single compact row of eight colors, with no toggle, count
selector or explanatory paragraph. HEX values and approximate shares remain
available in accessible button names.
Selecting a color copies
its HEX value. A four-second notice appears at the viewport corner, with selectable
text in the same floating location when clipboard access is unavailable.
No membership is required.

Palettes describe the digital reproduction, including any photographed frame,
background or paper. They do not identify pigments or establish the original
object's colors. Percentages are approximate sampled image areas and rounded
independently; they may not sum to exactly 100. Images with fewer distinct colors
return fewer swatches rather than invented colors.

## Implementation

- Analysis starts when the full-view artwork dialog mounts. No catalogue queries,
  uploads, database writes, server analysis or palette persistence are added.
- Only the existing same-origin `/assets/…` image paths are accepted.
- The browser decodes the reproduction, then samples at most 160 × 160 pixels.
  The original image download and decode size still depend on the source file.
- Five-bit RGB histogram bins feed deterministic, area-weighted median cuts,
  splitting the channel with greatest weighted variance. Swatches are RGB means,
  ordered by sampled area. Pixels with alpha below 128 are omitted; black and
  white are retained. This is an approximate quantization, not colorimetry.
- An in-memory cache holds at most 12 small pixel samples. Reopening the enlarged
  viewer reuses the sample. Navigating to another image resets the palette and
  aborts pending work; late results cannot replace the new image's palette.
- Load failures have a retry action and a 20-second timeout. Unmounting the viewer
  cancels pending loading. Fullscreen controls retain zoom and image-fit behavior.
- Only the compact color row reserves space. Copy feedback and its manual
  fallback float outside layout and focus without scrolling. Escape dismisses
  manual copying and restores focus.
- Full view puts the title and creator in a compact header, and zoom, colors and
  Details in a bottom toolbar. Fit uses all available image space, including
  scaling small reproductions up, while preserving the full composition. The
  Details disclosure retains the full title, recorded date, metadata, credits and
  supplied source details. It overlays the viewer without resizing the image;
  Escape closes the disclosure first. Record pages use a wider image column and
  smaller image padding.

## Verification

`lib/artwork-palette.test.ts` checks exact solid colors, weighted proportions,
transparent pixels, deterministic counts and unsafe paths. Component tests cover
automatic loading, image changes, retries and clipboard fallbacks. Browser release
checks exercise actual canvas sampling at 1440, 768, 390, 320 and landscape 844px,
eight colors without a toggle or selector, clipboard copying, error recovery,
image geometry and scroll stability, zoom, overflow and accessibility.
`e2e/artwork-palette.spec.ts` keeps permanent desktop and phone regression checks
for copying in fit and zoomed views, preserved panning and manual-copy dismissal.
They also check long titles, credits, next-work navigation, full composition fit,
expanded image space, landscape layout and focus restoration.
