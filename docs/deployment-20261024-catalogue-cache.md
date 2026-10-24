# Catalogue caching and exhibition browsing — 24 October 2026

This release adds portrait/key-artwork illustrations to exhibition participants, removes the expanded-study/archive selector, and adds country and city filters. Combined location filters must match the same exhibition occurrence. Museum exhibition history follows the highlights selection and appears only after a successful count finds at least one exhibition.

Static catalogue API responses and non-museum facets now last up to 24 hours in bounded, process-local caches. Every request checks the committed catalogue revision; updates invalidate cached bodies immediately. Migration `0060_catalogue_cache_dependencies.sql` registers the exhibition dependencies with the existing transactional invalidation mechanism. Existing artist, artwork, book, event, museum and related dependencies remain registered. No catalogue records are changed by this migration.

Access checks execute before the shared response cache. HTTP responses remain private with no browser storage. Current-display claims and museum facets retain their one-minute clock expiry. Museum-directory pages containing positive current-display counts also retain that shorter expiry. The authenticated server-rendered first directory page has a 30-second content cache keyed by its member cookie; session verification still executes on each page request. A bounded, one-minute browser directory cache speeds return navigation and clears on session expiry. These short client caches cannot mask database revision changes for a day.

The museum directory renders its first page on the server, retains cards during filter transitions, reserves image space and prioritizes its first two covers. Directory covers use responsive image optimization; the existing direct artwork delivery remains available elsewhere.

## Deployment source

The release is isolated from the `map-research` checkout. Application changes are committed on top of master. Production runtime artifacts merge this focused change onto the saved source of the exact currently serving `pictures-1024-v1` release, following the existing runtime-overlay procedure. This preserves the deployed authentication, consent, guides, mobile controls, assets and runtime configuration; unrelated museum-studio code present on master is not newly deployed. The API embeds only the previously deployed migrations and the new invalidation migration. Original image layers and Cloud Run runtime settings are preserved.

## Validation

- All 646 frontend tests pass; TypeScript and production webpack build pass. ESLint has no errors (eight existing image warnings in guides).
- Affected Go HTTP, catalogue, exhibition, atlas, books, events and member packages pass. Full repository ingestion tests depend on research fixtures outside the isolated checkout.
- Cache tests exercise 23-hour reuse, revision invalidation, 24-hour expiry, size bounds and short expiry for display evidence.
- Location predicates and artist image lookups were exercised with read-only PostgreSQL sessions; production corpus checks cover 45 query plans and bounded indexed participant lookups.
- Deployment candidates and public-site verification are recorded in the accompanying JSON receipt after rollout.
