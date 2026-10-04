# Artline membership proposal

## Sixteen interactive concepts for review — 1 October 2026

Open **http://127.0.0.1:3000/membership-preview** while the local web server is
running. The development-only page has sixteen working mockups, a shortlist,
per-idea feedback and a downloadable review. It requires no Google account or
payment. Review feedback is saved in the current browser and origin; switching
between `localhost` and `127.0.0.1` uses different browser storage.

The page opens on **New ideas**, the second set of eight concepts. Use
**First ideas** to return to the original set. Existing shortlist selections and
feedback are preserved, and the review download includes all sixteen ideas.
Each selected concept has a direct URL, such as
`/membership-preview?idea=annotations`.

### New ideas

| Concept | Try in the mockup | Proposed paid value |
| --- | --- | --- |
| Presentation mode | Step through slides, hide captions, show speaker notes, use arrow keys | Reusable talks and classroom presentations |
| Shared study rooms | Add a sample member, choose a role, add a local comment | Private group collections and discussions |
| Personal discovery | Switch interests, inspect suggestion reasons, save a work for later | Explained recommendations and discovery queues |
| Topic watchlists | Follow topics and mark example updates as read | Personal catalogue update feeds and optional digests |
| Offline study packs | Select works/notes and preview a pack's contents | Rights-cleared, bounded collections for travel |
| Research citations | Build a reference basket, switch to BibTeX, copy references | Reusable bibliographies and structured reference exports |
| Detail annotations | Place a pin, edit an observation, remove a pin | Private observations attached to specific artwork details |
| Colour & composition boards | Switch palettes, change the image surround, copy CSS colours | Visual reference boards for creative work |

Shared-room members/comments and watchlist updates are explicitly illustrative;
no invitation, message or notification is sent. The offline concept previews
contents without downloading or caching a pack. Discovery suggestions use only
the four documented sample works and are not a live recommendation service.
The study palettes are approximate visual choices from the reproductions, not
measured pigment colours. Annotations remain personal interpretations.

### First ideas

| Concept | Try in the mockup | Proposed paid value |
| --- | --- | --- |
| Personal collections | Switch collections, create one, add a sample work | Unlimited organization and cross-device sync |
| A visual notebook | Edit an observation, add a tag, save the sample note | Private searchable notes alongside artworks |
| Saved explorations | Restore a saved filter view and save a new sample | Return to a period, place and creator selection |
| Your own timelines | Toggle books/history and add a personal annotation | Combine works, books, events and your interpretation |
| The comparison desk | Change the second work and use linked zoom | Study multiple works together |
| A daily study practice | Reveal the artist and complete three recall cards | Guided learning, spaced review and saved progress |
| Museum visit notebook | Check research tasks and edit a visit plan | Personal museum lists and visit notes |
| Beautiful study sheets | Toggle notes/images and print or save a sample PDF | Rights-cleared exports with citations and notes |

Recommended first release: **collections, notes, saved views and exports**.
Public catalogue browsing, ordinary search, source links and sign-in stay free.
Prices and free-plan limits remain proposals to validate after reviewing the
workflows. No checkout, subscriptions, emails or external sharing are connected.

Sample work details and existing images come from the documented starter
selection in `apps/server/db/migrations/0005_illustrated_selection.sql`. They
are UI examples, not newly published catalogue records. Museum holdings are
explicitly separate from unconfirmed display status. Notes are labelled as the
reader's interpretation. The preview sends no catalogue mutation requests.

Sample feature state resets when changing concepts. Only the review shortlist
and feedback persist locally; use **Download my review** to retain a portable
copy. Real collections, note sync, spaced-review scheduling and export jobs
remain future backend work. Local debug exposes `local_debug: true` and
`all_features: true` without creating database accounts. Future member gates
must honor that backend mode rather than introduce a local Google login step.

## Original idea bank — 28 September 2026

Prepared 28 September 2026. These are product proposals, not shipped features.
The Google account foundation is implemented separately; billing and paid
entitlements are not implemented by this change.

Artline's advantage is the connection between art, books, people, places and
historical events. A paid account should help someone build a lasting personal
study practice around that material. Keep browsing, sources, basic search and
Google sign-in free. Charge for organization, study tools, exports and sharing.

| # | Paid feature | What a member gets | Suggested phase |
|---|---|---|---|
| 1 | Unlimited private collections | Organize artworks, painters, books and events into collections such as “Icons I want to study” or “Paris in the 1890s.” | First release |
| 2 | Personal notes and tags | Attach notes and searchable tags to records, synchronized across devices. | First release |
| 3 | Saved searches and timeline views | Save a period, geography, creator set and filters; return to exactly that view. | First release |
| 4 | Collection exports | Export a study sheet or PDF with selected records, notes, dates, citations and eligible images. | First release |
| 5 | Custom timelines | Assemble a personal timeline combining paintings, artists, books and events; add clearly labelled personal annotations. | Next |
| 6 | Side-by-side comparison | Compare two to four works with synchronized zoom, dates, materials and historical context. | Next |
| 7 | Guided learning paths | Curated sequences such as Byzantine to post-Byzantine painting or Japanese art before 1900, with progress tracking. | Next |
| 8 | Recall practice | Turn a collection into image-recognition quizzes and spaced review sessions. | Next |
| 9 | Museum visit planner | Build a museum checklist, group selected works and save visit notes. Holding records and dated on-view evidence remain separate. | Later |
| 10 | Follow artists and topics | An in-app feed of newly added or improved records for selected creators, museums, places and traditions. Email delivery would be opt-in. | Later |
| 11 | Presentation mode | A distraction-free slideshow of a collection with captions, sources and presenter notes for teaching or personal study. | Next |
| 12 | Offline study packs | Download a bounded set of selected records and permitted reproductions for travel or unreliable connections. | Later |
| 13 | Research citation tools | Export source lists in useful formats and inspect recorded attribution, date uncertainty and provenance together. | Later |
| 14 | Shared study spaces | Invite friends or students to a private collection, with explicit viewer/editor permissions. | Later |
| 15 | Personal discovery suggestions | Suggest related works, books and events from saved interests, with a short explanation and source-backed connections. | Later |

Start with collections, notes, saved views and exports. They share the same
underlying saved-record model and give subscribers something useful to keep.
Offer a small number of collections free so the value can be experienced before
payment. Validate the limits and price through user feedback; no price is claimed
here to be researched or validated.

An initial implementation sequence:

1. Google accounts and a clear account-deletion/support process.
2. Private collections, notes and saved views, with ownership enforced in Go.
3. Billing checkout, customer portal and signed, idempotent subscription webhooks.
4. Backend entitlement checks and limits, then exports.
5. Custom timelines, comparisons and learning tools based on actual usage.

Billing must reference the stable Artline member ID, not an email or a browser
flag. A Google login never grants a paid plan or editor access. Subscription state
must be recorded by the backend from verified billing events, including expiry,
cancellation and failed-payment behavior. Choose a billing provider and operating
entity before implementing payment collection.

Image downloads and exports need item-level rights checks; a subscription does
not create reproduction rights. Do not promise higher resolution where the
source asset is unavailable. Personal selections must remain distinguishable
from museum highlight designations. Suggested visit lists must not claim a work
is on display without fresh evidence. New user features must not publish or alter
review records in the shared catalogue.

All list operations remain bounded and indexed by member and collection IDs.
Collections store references to catalogue records, not copied global datasets.
Exports and offline packs are limited background jobs with explicit rights and
visibility checks. Full catalogue downloads, speculative catalogue claims and
unrestricted AI generation are outside the proposed paid offering.
