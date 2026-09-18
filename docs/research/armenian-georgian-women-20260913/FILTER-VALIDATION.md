# Women artists filter: implementation and validation

The timeline control appears before “Only popular painters.” `women=true` selects source-backed women artist identities; omitted or `women=false` preserves the previous scope. Popularity defaults are unchanged. Both enabled means an intersection. Query values must be a single literal `true` or `false`; malformed and duplicated values return `INVALID_WOMEN` on timeline, facet and painter-option routes.

Go/PostgreSQL own the predicate and apply it to timeline totals, individual nodes, density periods, suggested filters, country/movement/region facets, and bounded painter search options. Explicitly selected painter identities remain available to remove even when they do not match the current filter. The browser stores the choice in the URL and renders bounded API results.

Migration `0019_artist_gender_evidence.sql` stores positive identity evidence separately from artist publication and popularity: artist ID, source record/URL, basis, source checksum, structured statements, source check time and update time. A partial index supports women membership. Unknown identity is represented by missing evidence. The research scripts do not infer identity from names, pictures or nationality, and do not automatically overwrite conflicting evidence. Future identity corrections require source review and an explicit evidence update; this session does not install a scheduled refresh job.

Validation completed:

- Go catalog and HTTP API tests, including invalid values before database access.
- Real local catalogue queries in read-only, repeatable-read transactions: women totals compared with independent SQL, item membership, visibility/popularity combinations, facet counts, bounded options, and density/suggestion count consistency.
- Query plans captured for the real catalogue and the existing 20,000-painter in-query density fixture. No test database or catalogue fixtures were created. This is not a 10-million-artwork load certification; that load test remains outstanding.
- URL-state unit tests and TypeScript checking.
- Browser tests for control order, independent popularity combination, reset/clear, reload/back and 1440/390/320-pixel widths; screenshots visually inspected.
- Local artist-scoped artwork API and image checksum smoke checks after ingestion.

The Browser skill connection failed during bootstrap because of a tool-environment error. The existing project Playwright setup provided the fallback verification. Disposable screenshots and logs stayed under `/tmp`; relevant evidence was copied into this research package.

The migration and identity evidence were applied to local and production databases. Feature code was built and exercised locally during the research session. Following the user’s subsequent authorization, the API and web application were deployed, and the browser tests and artwork/image checks passed against production. See the [production release evidence](production-release/README.md). No commit was created.
