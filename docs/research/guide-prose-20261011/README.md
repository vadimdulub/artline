# Museum guide prose revision — 11 October 2026

Requested scope: rewrite the existing articles to remove formulaic art writing,
update the English editorial manual, and revise the translations. The existing
six guides contain 135 works and have ten editions each. No catalogue database
was read or written for this editorial pass.

Every English description and “why it matters” paragraph was rewritten, along
with introductions, subtitles, visitor notes, selection/context notes and book
recommendations. Descriptions were checked against the existing artwork contact
sheets. The selection, object identities, painter filters, dates used by the
portal, source URLs, credits, image files and reading links were retained.

The manual is version 1.1. Its short house edit addresses stock vocabulary,
repeated conclusions, unsupported importance claims, unnecessary contrasts,
guide-specific book notes and translation mistakes. The independent selection
and display qualification remains in the guide notes. The Neue Pinakothek
visitor note was checked against https://www.pinakothek.de/en/neue-pinakothek.

The nine translated editions per guide were regenerated from the edited English
through the existing Cloud Translation service. An initial automatic pass was
rejected after review. The replacement pass used the Translation LLM; explicit
edits are in `editorial-overrides.json`. The review included passages in every
language, all translated artwork titles, and the Russian interpretations.
Corrections include the fish in Chardin's *The Ray*, an ordinary conversation
mislabelled as online chat, the gender of named sitters, and comparisons whose
direction had changed in translation. This is an assistant editorial review,
not a claim of independent native-speaker review. The AI translation label stays.

`date-wording-changes.json` records 24 display-label cleanups. The numeric dates,
uncertainty and portal ranges were retained; untranslated century prefixes were
removed where the source's explicit year range was already present. The separate
source-check date was not advanced merely because the prose changed.

`material-glossary.json` keeps materials consistent across ten languages,
including panel/canvas distinctions, mounted supports, wove/laid paper and an
unspecified binder. Existing source-language labels were translated; no missing
medium was invented. `material-wording-changes.json` records the first label
pass; the glossary is the final authority for the resulting display strings.
The original catalogue source records remain linked and unchanged.

Reproduction:

- `ops/rewrite-guide-translations-20261011.py` caches translation results, then
  applies the recorded edits and material glossary. `--editorial-only` reapplies
  the local edits without translation requests.
- `ops/build-museum-guide-pdfs.mjs` renders the same JSON into all 60 PDFs. Its
  context section now contains the two destinations retained on the website.
- `content-audit.json` records the frozen JSON hashes and confirms each work's
  description and importance changed while its identity/evidence were retained.
- `pdf-validation.json` records the final PDF hashes, page counts and links.
  Sixty editions contain 1,530 pages in total. Representative pages across all
  ten languages and six museums were rendered for visual review.

The existing twelve guide unit tests and nine browser tests passed locally,
including mobile layouts, Arabic direction, accessibility, downloadable PDFs
and the actual selected-artwork portal view. Production is released as an
isolated content overlay on the previously deployed guide-portal source.
Production verification passed for all 60 pages and matching PDFs. Release
`artline-web-guide-prose-1011-v1` serves 100% of traffic. The receipt is
`docs/deployment-20261011-guide-prose.json`.

Original content, deployment snapshots and release archives are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/guide-prose-20261011/`.
Temporary previews and review text are under `/tmp/artline-guide-prose-20261011/`.
