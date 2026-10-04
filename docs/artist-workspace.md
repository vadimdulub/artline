# Artists as a research workspace

## Design plan

Keep Artline's established palette: paper `#f2efe8`, stone `#e8e3d9`, ink
`#1b1916`, charcoal `#12110f`, muted text `#625d55`, and the existing dark
red `#8f3a29` for readable active controls. Georgia remains the artist-name,
biography and artwork-title face; Avenir/system sans carries metadata and filters.
This preserves the biography treatment the owner explicitly asked to keep.

The directory is an index for finding people: names, recorded life/activity dates,
country affiliations, movements, and exact counts of visible works. Filter by name,
country, movement, ranked cohort and women artists. Alphabetical and popularity
orders are distinct, with the latter clearly described as discovery, not quality.

Every artist uses the same page and the same bounded artwork browser:

```
Artist name / recorded dates / classification
Artworks | Biography | Museums | Sources
Biography with expandable source-attributed reference text
Search works / year / work type / museum / pictures
Recorded total / matching total / 24-work page
Artwork gallery / first, previous, next
Documented museum holdings with counts and collection links
Sources and research notes
```

The gallery and its catalogue controls are the main visual feature. Real artwork
images, dates, museum names and attribution are the content; no decorative stats,
quality rankings or invented metadata. The brief review removed the old split
between a five-work published profile and a paginated research profile. Publication
state must control visibility, never the usefulness or layout of the artist page.

## Data rules

Go/PostgreSQL own discovery, counts, filtering, keyset pagination and holdings.
Queries scope by the selected artist or returned artist IDs before artwork work.
Museum lists use accepted holding evidence; holding does not assert current display.
The local database is read-only throughout. Source reference biographies supplement
existing records without changing database biographies, facts or publication state.

## Implementation and validation

The new `/api/v1/artists` directory returns 24 profiles (maximum 60), with
scope-bound keyset cursors. Country/movement, ranked-cohort, women-artist and
name/alias predicates are applied in PostgreSQL before paging. Artwork counts
are batched for only the returned artist IDs. The published SEO discovery API
is preserved; the expanded research-preview directory is not indexable.

Every full artist page now uses `ArtistChronologyRecord`, including published
artists. The representative selection remains intact for editorial/publication
rules and no-JavaScript canonical links, but no longer limits the interactive
catalogue. Title/accession search, work type and museum filters apply before date
summaries, paging and previous/next artwork navigation. The museum list aggregates
only the artist's associated visible records, requires accepted active-source
holding evidence and excludes conflicts. It returns at most 100 institutions with
an explicit total and a link to the wider museum directory. No on-view claim is
inferred from holding information.

All 1,000 artists in the existing Pantheon cohort have source-attributed reference
biographies in the release bundle (minimum 400 characters). Six authority redirects
were verified explicitly from Wikidata responses. The original catalogue and
canonical authority IDs, exact Wikipedia revisions, attribution and CC BY-SA 4.0
licence are recorded. Existing longer editorial biographies remain the primary
reading; the reference biography is supplementary. Short authority descriptions
remain stored unchanged while fuller source text becomes the main reading.

Source policy: [Wikimedia Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use/en).
The redistributable text and licence live beside the Go reference-data reader.
The capture script honors source rate limits and reuses retained responses. Raw
source evidence is retained under the Artline backup directory, with a compact
report in `docs/research/artist-biographies-20261004/report.json`.

Enforced read-only checks on the actual local catalogue confirm 1,386 Rembrandt
works / 23 sourced collections and 126 Van Gogh works / 17 collections. Directory
pages, artwork pages, scoped counts, title/type/museum filters, visibility, cursor
scope rejection and filtered next/previous navigation pass. Actual first-page
plans use the painter attribution index and artwork primary keys: 2.18 ms for
Rembrandt and 0.47 ms for Van Gogh in the sampled core SQL execution. Those figures
exclude transport, summaries and enrichment; they are not ten-million-row capacity
proof. Representative large-catalogue, cold-cache and concurrent load tests remain
outstanding. No real-catalogue fixtures or database writes were made.

The production catalogue has only five **published** works for each of Rembrandt
and Van Gogh; their additional records remain in review and were already accessible
through the configured public research preview. The directory and painter-drawer
links open `?catalogue=all` for that complete recorded view. These pages and their
shared artwork links are explicitly noindex and require existing preview access.
The canonical published pages retain narrow visibility and their indexable metadata,
using the same layout and an explicit “Browse the full recorded catalogue” link.
The workspace flag alone cannot enable research access when preview is disabled.
This preserves the SEO/publication boundary instead of silently publishing records.

Final local validation: all Go packages, 203 frontend unit tests, lint and TypeScript
passed. Browser coverage includes artist discovery, Rembrandt/Van Gogh catalogues,
combined filters, source attribution, 320/390/1440px layouts, accessibility, shared
artwork pages without JavaScript, Account navigation, sticky headers and Full view.
The existing public-record unit tests still pass; two added tests cover explicit
full-catalogue access and rejection of that flag when preview is not configured.

Candidate validation found one local/production UUID difference for Domenichino.
The production catalogue’s Louvre consolidation citation and NGA authority both
identify Q320118 and the same canonical slug. One explicit additional UUID binding
is retained with evidence in `ops/artist-biography-identity-bindings.json`; the
reader still requires the exact slug and an enumerated database ID. Rebuilding the
source bundle can preserve it with the capture script’s `--identity-bindings` flag.

## Painter pop-up: pictures before controls

Keep the established paper #f2efe8, stone #e8e3d9, ink #1b1916,
charcoal #12110f, muted #625d55 and dark red #8f3a29. Georgia names and
artwork titles remain paired with the existing Avenir/system metadata type.
The drawer is a compact viewing space: artist name, large selected image,
caption and previous/next arrows, then a two-column thumbnail collection.
A single Filters button reveals search, year, type, museum and picture controls.
Artwork details, biography and sources stay available through disclosures.

The opening view uses the existing server-side picture filter; Show all records
remains available, and the full artist page keeps its research controls and
complete recorded view. Pages stay bounded, and previous/next navigation remains
scoped to the active filters. The artwork is the visual focus; no new decoration,
fonts or palette are introduced. This follows the owner's explicit request for
pictures first while retaining the established biography treatment.
