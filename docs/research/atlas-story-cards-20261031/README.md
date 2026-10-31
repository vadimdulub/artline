# Atlas story cards — published 31 October 2026

All 33 then-existing history topics use the large illustrated card layout under **Start with a story**. **Women’s rights** comes first. Search, era buttons, full-frame artwork fitting and existing navigation remain available. The first four covers load eagerly; subsequent covers load lazily.

Commit `851eb25157631be89fbdb2ca7e24e35fe73f33b2` was pushed to `map-research`. The exact-serving frontend was deployed as `artline-web-story-cards-1031-v1` at 100% traffic. All 44 previous image layers and runtime settings were preserved. The isolated runtime changes were `AllStartingPoints.tsx` and `AllStoryCards.css`; unrelated workspace edits were excluded.

Validation: 47 existing tests, ESLint, TypeScript, Linux Next build, and 36 HTTP responses in each of candidate and production. All 72 saved bodies and 1,192 source files were rehashed. The in-app browser bridge was unavailable; no browser visual pass is claimed.

An initial staging precondition stopped before any service mutation because publication had not yet produced its receipt. The unchanged production service was reconciled, publication finished once, and staging then succeeded. The local audit is `stage-precondition-reconciliation.json`. The release is complete and must not be replayed.

The subsequently requested WWII companion is a separate release documented in [its research folder](../wwii-asia-africa-20261031/README.md).
