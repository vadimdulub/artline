# Library and event illustrations — 1 October 2026

Added 58 selected reproductions: 17 book covers, title pages or title-page illustrations, 25 author portraits, and 16 event illustrations. The combined manifests now contain 818 book images, 42 author portraits and 16 event illustrations. Existing selections were preserved.

Every new served JPEG is at most 100,000 bytes; the largest is 99,738 bytes. Images retain the supplied composition with proportional resizing and JPEG compression. Sources, credits and public-domain declarations accompany each image in the API and detail drawer. Later paintings and historical maps are labelled as such, separately from event dates. The Book of Optics image is labelled a title-page illustration, not a complete title page.

## Selection and evidence

Research was bounded to 100 missing book images, 45 missing author portraits and 40 highlighted events. It yielded 187 image candidates. Only the explicit reviewed selection was downloaded. The selection script pins the candidate capture SHA-256; the research script prevents overwriting this completed campaign.

- `identities.json` retains catalogue identities before research.
- `candidates.json`, `review.json` and `captures/` retain the work/person/event P18 claims and Commons file metadata.
- `selected-images.json` records individual identity reviews, source and output hashes, credits, dimensions and byte sizes.
- `prepared-manifests.json` and `selection-summary.json` describe the exact manifest additions.
- Original selected downloads are preserved under `/Users/vadimdulub/Library/Application Support/Artline/source-images/library-illustrations-20261001/`.

The reviewed set includes Mrs Dalloway, Ulysses, Anna Karenina, Middlemarch, Frankenstein, The Faerie Queene and De velitatione bellica; portraits include Conan Doyle, Jules Verne, Gogol, Oscar Wilde, Gorky and García Lorca. Event pictures include the Peace of Westphalia, American Revolution, Scientific Revolution, the 1848 revolutions, the Berlin Conference and the 1918 influenza epidemic. No catalogue publication statuses were changed by image selection.

## Validation

Contact sheets were visually reviewed. All local image paths are bound to the corresponding reviewed identities, with imported unselected image data discarded by the API. Tests cover mismatched event identities and unsafe asset paths. Chrome loaded a new cover, portrait and event illustration through the real local API.

The associated UI checks verified same-line date handles at 1894–1895 and 1999–2000 in Painters, Books, Events and All at 1440, 390 and 320 pixels; pointer, keyboard and touch interactions; cancellation without changing the URL; and no page overflow. All 213 highlighted books and 176 highlighted authors were rendered in timeline mode. The 500-record highlight capacity remains separate from ordinary 150-record gallery pages.

Go package tests, 192 frontend unit tests, TypeScript, scoped ESLint and focused read-only catalogue audits passed. Disposable browser outputs are in `/tmp/artline-review-20261001/`. These are local changes, not a production release.

The follow-up artwork-size request was checked at 1440, 390 and 320 pixels. At desktop width, image height grows from about 130 px in a broad combined view to 224 px for a century, 306 px with Artworks isolated, and 348 px for a focused decade. On phones the corresponding heights are 140, 209, 268 and 299 px. All three Playwright regression cases pass; additional Chrome checks verified horizontal paging after resizing, full-composition rendering, reset sizes and no page overflow.

The local API was rebuilt and restarted on port 8080 with local-debug access, the existing local catalogue, migrations skipped, and a read-only connection. Member previews remain available without Google sign-in. No preview fixtures were created. Port 3000 serves the existing development frontend.
