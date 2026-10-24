# Artwork picture defaults — 24 October 2026

The artwork directory, museum artwork galleries and study artwork searches now start with pictures enabled. Their API defaults match the controls. Clearing or resetting filters restores pictures; explicit opt-outs use `image_only=false` for the artwork directory, `image_only=0` for museum galleries and `image=false` for study searches. Pagination scopes include the chosen image filter. The museum directory retains its previous cursor scope.

Painters and All already prefer illustrated artworks. Museum Studio catalogue pickers now enable their image option initially and when changing catalogue scope in the committed source; the existing unpublished Studio deployment boundary is preserved.

Large museum galleries omit missing-image candidate branches when the image filter is enabled. This avoids scanning unillustrated holdings only to reject every row. A read-only production-catalogue check verified 13,562 illustrated Met works among 110,720 recorded works and 66,953 illustrated directory works among 184,175, at verification time. These counts can change with ongoing research.

All 650 frontend tests, TypeScript and targeted ESLint pass. Affected Go catalogue, HTTP and member packages pass. Tests cover the initial defaults, explicit opt-outs, reloads, resets, API behavior and keeping book/event searches independent of the artwork image option. Linux API and web production builds pass. Real catalogue checks run with PostgreSQL read-only sessions and loopback-only development access.

The production artifact overlays this focused change onto the saved, pinned `catalogue-cache-1024-v1` runtime sources and images. Existing authentication, consent, mobile controls, guides, image delivery, 24-hour content caching and runtime settings are preserved. This release requires no database migration or catalogue data delivery. Candidate and public verification are recorded in the accompanying deployment receipt.
