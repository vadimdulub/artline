# Filter discovery and date fitting

Selecting a painter, movement, author, place, language, work type, topic or other discovery filter clears the editorial starting selection (Top 100 / Highlights). Search has the same behavior. Choice menus always include choices beyond the editorial selection, so a user can select a movement that is absent from Top 100. Users can explicitly re-enable an editorial checkbox after filtering.

A filter change clears the previous manual years and requests one automatic fit. The Go API computes `matchedRange` with the existing visibility/filter predicate before cursor pagination. The browser uses that range once, then removes the pending `fit` URL flag. Period selection fits within the chosen period context. Manual year edits and Zoom out cancel pending fitting. Painter lifespans, artwork creation, book publication/composition and author lifespan remain separate date meanings.

No match leaves the requested range unchanged. Unknown dates produce no invented extent, and Books/Events/Authors keep the full range when undated matches exist so those records remain reachable. Stale or failed responses cannot fit the current selection. Browser history retains the selected filters and fitted years.

The aggregation adds min/max to existing server counts rather than loading the catalogue into the browser. Books and Authors use a 150-entry timeline threshold for general discovery. Highlights have a separate bounded capacity of 500 so the complete editorial selection stays in the timeline (213 books and 176 authors in the 1 October local catalogue). Larger selections use cover/portrait galleries with bounded keyset pages and at most three pages mounted. Undated entries remain available below the timeline; an entirely undated selection uses cards. No new database indexes or migrations are required.

Close year handles remain on the same baseline, at least 32 pixels apart and inside the track endpoints. The separation changes only their visual positions: fields, keyboard steps and API queries retain the actual years. Pointer offsets preserve the initial year when a separated handle is grabbed. Touch and pointer drags preview locally and commit on release; cancellation restores the original range.

In All, artwork cards and their image areas grow as the selected date interval narrows. The artwork-only view starts with larger images and grows further with date zoom. Sizes remain bounded by the viewport; images use `object-fit: contain` to retain the complete composition. Restoring all types and all years restores compact cards. This is presentation sizing only: filtering, order, counts and keyset pagination remain on the server, and the gallery's existing bounded page window and proportional spacers remain in use.


## Period and theme review — 2 October 2026

All now offers 32 starting points, including Baroque art and its world. The period picker groups choices and shows their dates and scope; search matches names, dates, places and descriptions. It adds no height to the closed filter bar.

Scoped artwork, book and event filters have removable summary chips. Clear filters removes both these scoped fields and the shared filters, preserving layers and a manual year range. Selecting a new period resets scoped filters to that period’s starting selection, clears Highlights and fits the matching dates.

The researched connections, catalogue addition and validation are recorded in [the period review](research/period-connections-20261002/README.md).
