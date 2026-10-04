# Artlines logo

Adapted on 3 October 2026 from the user-supplied
`8c3754a4-1a9b-4354-bb67-417abdcf0a46.png` in the repository root.
The reference spells the wordmark “Artlines”; its serif lettering, timeline
crossbar and terracotta dot are retained.

## Assets

- `artlines-wordmark.webp`: transparent 576 × 138 px lossless WebP, 28,230 bytes.
  Displayed at 144 px wide in the desktop header and 132 px on smaller screens.
  CSS inversion with a 180° hue rotation supplies light lettering and a warm
  red dot for the dark header.
- `../../app/icon.svg`: hand-drawn vector “A” adapted for small sizes, with
  stronger hairlines and a cream background for light and dark browser chrome.
- `../../app/favicon.ico`: 16, 32 and 48 px PNG frames rasterized from the SVG.
- `../../app/apple-icon.png`: 180 px rasterization of the same SVG.

Next.js file-based metadata exposes all three icons automatically.

## Image generation

The wordmark was redrawn using the built-in image generation tool, with the
user's image as the reference and `transparent_background: true`. The selected
output was trimmed, resized and losslessly encoded with Sharp. No API/CLI
fallback was used. The favicon is native SVG, not a generated raster image.

Final prompt:

> Create a clean, newly drawn flat logo asset from this reference, NOT a photo cutout. Only the exact word 'Artlines', spelled A r t l i n e s, in the reference's elegant high-contrast serif lettering. Retain its distinctive open capital A crossed by a thin horizontal timeline and one circular terracotta red dot #c85139. Render ALL LETTERS as pure solid black #111111; keep the red dot. Genuine transparent background. Absolutely no paper, no texture, no distressing, no grunge, no specks or scraps around the letters, no tiny label '01', no shadows, no outlines. All glyphs must have precise smooth clean vector-like edges and uniformly opaque solid fills. Slightly heavier hairlines for small website sizes. One horizontal wordmark filling the canvas width with a narrow margin, no additional elements or mockups.
