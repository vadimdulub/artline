# Artline country research handoff — 2026-09-14

The final handoff contains country-scoped CSVs, the 100k-row artwork identity index, selected-image evidence, canonical redirects, and `RESEARCH_PROMPT.md` for the next ChatGPT enrichment run.

## Delivery

- 220 country rounds completed and verified on both databases (20 each for DE, SE, CZ, PL, NO, HU, GB, CH, US, and AT, plus the existing campaign rounds).
- 4,376 new review artworks and 1,161 new review artists are present in production; 3,143 selected image assets are verified in production. The local receipt index contains two additional recoverable Woodville orphan artworks/images because the earlier importer created rows without a creator link; these are recorded in `final-audit/final-1759/semantic-parity.json` and are not silently counted as production parity.
- Production snapshot: 235,681 active review artworks and 13,218 artists. No new records were published and no current-display claims were inferred.
- Austria rounds include held records for uncertain copies, framed/glare reproductions, and unresolved creator or date evidence. Unknown dates remain review cases.

## Duplicate review

Confirmed duplicate identities were consolidated through canonical redirects and archived rows, preserving citations and media. The final read-only audit still reports 1 same-institution accession lead, 8 same-image leads, and 8,452 same-title/creator/institution leads per database; these are leads for editorial review, not automatic deletions.

## Validation

`final-audit/final-1759/production.json` passed the production delivery audit. Public verification checked 3,143 image bytes and 20 unauthenticated timeline/detail endpoints. Local and production semantic snapshots differ only in the two documented Woodville orphan rows and their images.

Use the CSVs with the prompt in `RESEARCH_PROMPT.md`. Preserve `status=review`, provide source URLs and evidence for every enrichment, and leave unknown dates or creator identities unresolved when sources do not establish them.
