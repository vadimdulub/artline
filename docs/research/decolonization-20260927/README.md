# Decolonization expansion — 27 September 2026

Completed in the real **local** catalogue and local app. No production data,
image upload, deployment, publication, or commit was performed.

The period now selects **26 artwork records**, of which **15 have images** and
appear in the illustrated timeline (previously 4). All 9 books and 9 events are
retained. Seven artwork records are new; two existing El-Salahi records now have
verified museum object details. All nine remain in internal editorial review.
The app does not show “In review” labels.

## New records and reconciliations

| Creator | Work | Museum creation date | Action / museum source |
| --- | --- | --- | --- |
| Abanindranath Tagore | Bharat Mata [Mother India] | 1905 | New, illustrated; [national museums portal](https://museumsofindia.gov.in/repository/record/vmh_kol-RBS27ANT-16706), accession RBS27ANT |
| Uche Okeke | Ana Mmuo (Land of the Dead) | 1961 | New; [Smithsonian National Museum of African Art](https://africa.si.edu/collection/object/nmafa_97-3-1), accession 97-3-1 |
| Hendra Gunawan | War and Peace | c. 1950s | New; [National Gallery Singapore](https://www.nationalgallery.sg/sg/en/visit/tours/audio-guide.stop.html/between-declarations-and-dreams-audio-tour/3.html), accession 1997-02155 |
| Ibrahim El-Salahi | The Mosque | 1964 | Existing record enriched; [MoMA](https://www.moma.org/collection/works/78385), accession 7.1965 |
| Ibrahim El-Salahi | No Shade but His Shade | 1968 | Existing record enriched; [MoMA](https://www.moma.org/collection/works/450851), accession 81.2024 |
| Ibrahim El-Salahi | By His Will, We Teach Birds How to Fly No.13 | 1969 | New; [MoMA](https://www.moma.org/collection/works/280148), accession 192.2018 |
| Malangatana Valente Ngwenya | Madness of Maria Chissano III (Loucura de Maria Chissano III) | 1965 | New; [MoMA](https://www.moma.org/collection/works/420295), accession 71.2021 |
| Malangatana Valente Ngwenya | PIDE's Punishment Room (Sala de castigo da PIDE) | 1965 | New; [MoMA](https://www.moma.org/collection/works/420294), accession 72.2021 |
| Malangatana Valente Ngwenya | Untitled | 1965 | New; [MoMA](https://www.moma.org/collection/works/420293), accession 73.2021 |

These connect the theme to Swadeshi, Nigerian Natural Synthesis, Indonesian
independence, Sudanese modernism, and Portuguese colonial repression in
Mozambique. Cultural context is distinguished from depictions of political
events. See [MoMA’s Malangatana research](https://post.moma.org/malangatana-as-anti-colonial-subject-1959-74/)
and [The Short Century](https://www.moma.org/calendar/exhibitions/4749).

The 15 illustrated entries comprise the previous four Lam works; Bose’s
*Gandhi March (Bapuji)*; seven existing Sher-Gil works (*Hill Women*, *Three
Girls*, *Brahmacharis*, *Bride’s Toilet*, *South Indian Villagers Going to a
Market*, *Village Scene*, *Ancient Storyteller*); two existing Tagore works
(*The Passing of Shah Jahan*, *Asoka’s Queen*); and the new *Bharat Mata*.
Sher-Gil’s selection is grounded in [NGMA’s collection and chronology](https://www.ngmaindia.gov.in/virtual-tour-of-amrita-sher-gil.asp)
and concerns cultural self-representation rather than political activism.

The other 11 selected records have no attached image: eight records in the table
above plus existing *Oyoyo*, *Women Riot*, and *Blue Composition*. They remain
real sourced database records but do not appear in the image-only timeline.

## Scope and provenance

- Main period remains 1945–1980; context begins in 1900 to include three earlier
  Bengal School works. Artwork creation still ends by 1970.
- Exact artwork IDs replace broad creator/country defaults. The existing
  indexed slug resolution preserves the local/production identity of *Ibaye*.
  Only the Decolonization preset changed relative to `presets-before.json`.
- *War and Peace* retains the museum’s “c. 1950s”, represented as an approximate
  decade interval, 1950–1959. No invented exact year.
- Existing CSV citations survive the two reconciliations. No new artist
  profiles or biographies; unresolved named makers remain object-level labels.
- Nine holding assertions are supported by museum records. No display claims.
  *Bharat Mata* retains Rabindra Bharati Society provenance; Victoria Memorial
  Hall is the museum named by the national portal, not a newly inferred owner.
- Works after 1970, including Malangatana’s *Cry for Freedom* (1973) and
  El-Salahi’s *Prison Notebook* (1976), were excluded from this batch.

## Image and recovery

Only one new reproduction was downloaded, after the exact selection and source
captures were pinned: [Bharat Mata on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Bharat_Mata_by_Abanindranath_Tagore.jpg).
The file explicitly carries PD-Art / Public Domain Mark; the painting dates to
1905 and Tagore died in 1951. Museum metadata and Commons image rights are
preserved separately. The full-frame derivative is 650 × 1200, 89,756 bytes,
visually inspected. Modern copyrighted reproductions were not downloaded.
Existing images and their rights labels were retained unchanged.

Validated pre-change dump:
`/Users/vadimdulub/Library/Application Support/Artline/backups/decolonization-20260927/local-before.dump`.
Selected source image and HTTP receipt are under the corresponding
`Artline/source-images/decolonization-20260927/` directory. Raw research remains
in this directory under the repository’s existing ignore policy.

## Verification

- Go atlas and HTTP API package tests passed.
- `TestDecolonizationReadOnly` and the Decolonization case of
  `TestStartingPointsReadOnly` passed against the real catalogue in enforced
  read-only transactions. No test database or fixtures were created.
- Verified 15 / 9 / 9 illustrated artworks, books and events; exact membership,
  three historical-context artworks, cutoff, and seven-item keyset pagination
  without duplicates or omissions.
- Captured real-data EXPLAIN ANALYZE plans: artwork query about 23 ms, book query
  0.29 ms, event query 0.20 ms in this run. Artwork candidates use the primary
  key index for 26 selected IDs. This is not a 10-million-row load test; that
  capacity test remains outstanding.
- All 15 local artwork images returned HTTP 200. Desktop (1440 px) and mobile
  (390 px) browser checks passed for selection, three lanes, the new image and
  detail drawer, no review labels, no page overflow, and no browser errors or
  write requests. Screenshots are under `/tmp/artline-decolonization-*`.
- Database verification confirms seven new records, two reconciliations, one
  new image, preserved source provenance, no publication, and no display claims.

Reproducible batch: `ops/add-decolonization-20260927.py`. Plans, hashes,
preimages, image evidence, application receipt, API response, browser results,
and query plans are preserved alongside this report.
