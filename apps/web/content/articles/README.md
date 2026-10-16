# Artline articles

File-backed editorial content lives here. There is no CMS or automated publication service.
Read ../../Art_Writing_Editorial_Manual_EN.md before writing or revising an article.

Museum guides use museum-guides/<slug>/en.json as the English source, separate
ru/it/de/zh/fr/es/pt/ja/ar.json translations, and a matching PDF for each edition.
index.json contains only completed editions. Keep research, source receipts,
object identity decisions and unresolved leads under docs/research, outside the
publication copy. Preserve source rights/credits, qualified attributions and
unknown dates. A guide's selection is Artline's editorial choice, not a museum's
ranking or a promise of current display. Changes to an English edition require
translation/PDF regeneration and review. Do not silently fall back to English
under another language label.

The portal uses bounded artwork_id filters, canonical painter slugs and an
explicit historical date range. Books and events provide period context, not
claims of documented influence. English titles can be editorial translations;
catalogueTitle preserves the original source label. Production object IDs are
intentionally retained: local catalogue snapshots may differ. Catalogue writes
are outside the article workflow.

When a guide identifies an existing artist before the catalogue has that creator
relationship, set the work's catalogueArtistSlug to null. Its artwork link then
uses the ID-based view, while artists still supplies the verified diagram
selection. Omit the field for existing catalogue-linked creators; do not create
an artist-scoped artwork URL from an article-only creator match.

Artist guides live in artist-guides/<slug>/ with the same ten JSON/PDF editions
and their own index.json. Set kind to artist, provide artist name, catalogue slug
and qualified lifeDates, and leave the legacy museum/city/country fields empty.
The shared reader, PDF route and sitemap resolve each indexed guide to its folder.
Keep guide slugs unique across both indexes. comparisonArtists adds verified
contemporaries to the lifespan view only; it does not broaden the exact artwork
selection or assert influence. About's museum section continues to use museum
guides. Source-backed article corrections are recorded separately from catalogue
metadata and do not write to the database.
