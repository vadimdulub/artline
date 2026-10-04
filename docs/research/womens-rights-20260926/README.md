# Women’s rights — global history, including Japan

Published to the live site on 27 September 2026: see the
[publication report](../womens-rights-publication-20260927/README.md) for the final
publication states, production identity mapping, checks and release receipts.
The implementation notes below preserve the original pre-publication audit.

Implemented locally on 26–27 September 2026. Open
[Women’s rights in Artline](http://localhost:3000/all?preset=womens-rights).
The preset appears in both the starting cards and Historical period picker.

## What is available

| Material | Selected records | New database records | Visible in the combined timeline |
|---|---:|---:|---:|
| Artworks | 50 | 8 | 44 with images |
| Books | 34 | 0 | 34 |
| Events | 32 | 26 | 32 |

The eight new artwork records comprise two Met works with selected CC0 images
and six London Museum suffrage prints with sourced metadata. The London images
have restricted or noncommercial terms; none were downloaded. Those six records
are available in the local museum catalogue, whose API reports six holdings and
zero current-display claims. The combined illustrated timeline intentionally
keeps its existing image requirement, so it shows 110 entries rather than 116.

All new records remain in review. No new material was published or deployed.
The local preview shows eligible review records without an “In review” badge.
No creator biography, unknown date, image permission or on-view claim was invented.
The 42 existing artworks, 34 books, six events and 30 other preset definitions
were compared with their saved preimages and remain unchanged.

See the [complete selected works and events](catalogue-selection.md),
[selection reasons and stable IDs](selection.json), and
[26 additional institutional leads](further-research.md).

## Editorial approach

The main historical window is 1780–2000, with 1400–2000 context for earlier
writing and women’s artistic practice. The end is the existing book/event
catalogue boundary, not a suggestion that the movement ended in 2000. Artworks
retain the pre-1971 creation cutoff.

Direct advocacy is distinguished from broader context about work, education,
marriage, self-representation and access to artistic careers. Individual works
are selected explicitly; neither the artist’s gender nor a country tag admits
an entire oeuvre. Personal/editorial choices have not become museum highlight
designations. Multiple impressions of the same print were not added merely to
increase the count.

Examples of the institutional evidence:

- The Met discusses artistic education in [Labille-Guiard’s self-portrait with
  pupils](https://www.metmuseum.org/art/collection/search/436840). Its related
  [preparatory drawing](https://www.metmuseum.org/art/collection/search/335183)
  is a new illustrated record. The museum’s API range of 1780–1790 and display
  date “ca. 1785” are both preserved.
- [Edward Skill’s newspaper engraving after Emily Mary Osborn](https://www.metmuseum.org/art/collection/search/626348)
  adds printmaking and illustrated publishing to the story of women’s
  professional exclusion. The engraver and source artist remain distinct.
- [The Gilded Cage](https://www.demorgan.org.uk/collection/the-gilded-cage/)
  supplies a direct connection between confinement and women’s freedom.
  Conflicting dates across De Morgan material were not used to overwrite the
  catalogue’s existing broad date range.
- [London Museum’s Suffrage Atelier records](https://www.londonmuseum.org.uk/collections/v/object-967741/the-prehistoric-argument/)
  document art made for the voting campaign. Collective makers remain named
  object-level credits; no fictitious individual artist was created.
- The National Diet Library documents [women’s literary networks](https://www.ndl.go.jp/portrait/e/pickup/011)
  and [Japan’s electoral reforms and 1946 election](https://www.ndl.go.jp/modern/e/cha5/description05.html).
  Four new Japanese events connect Seitō, Nyonin geijutsu, electoral reform and
  the first election in which women voted. Edo works by Ōi and Yukinobu supply
  professional-history context, without attributing modern suffrage activism.
- [UN Women](https://interactive.unwomen.org/multimedia/timeline/womenunite/en/index.html),
  [New Zealand History](https://nzhistory.govt.nz/politics/womens-suffrage/brief-history),
  [UK Parliament](https://www.parliament.uk/about/living-heritage/transformingsociety/electionsvoting/womenvote/unesco/),
  and [the US National Archives](https://www.archives.gov/milestone-documents/19th-amendment)
  support the wider sequence. Citizenship and racial exclusions are retained
  where relevant; a franchise milestone is not described as universal equality.

This is a substantial selected starting point, not an exhaustive global census.
The image selection remains strongest in European, American, Indian and Japanese
collections; the events broaden coverage to Africa, Latin America and the Pacific.
More African, Latin American and Asian campaign imagery remains a useful research
priority. Unknown-date books already in the catalogue were not assigned invented
publication dates to make them appear here.

## Evidence and reproducibility

- `captures/` preserves bounded museum searches, HTTP receipts, and primary-source
  web captures. Failed HTTP pages are retained as failed responses; they are not
  represented as successful metadata captures. The labelled web captures supplied
  the London Museum evidence when its direct HTTP responses failed.
- `images/` contains the exact two Met API records, policy evidence, selected image
  plan, SHA-256 checksums and visual review. Each final derivative is under 100 KB.
  Original downloads reside under Artline’s Application Support source-images area.
- `events.json` holds the 26 sourced events. `events-initial-sha256.json` records a
  subsequent copy edit removing publication-workflow wording from the selection
  explanation; database review status was unchanged.
- `posters-plan.json` retains the six accession numbers, creator roles, date ranges,
  materials, source pages and reason for omitting the images.
- `existing-records.json`, `presets-before.json` and `verification.json` document
  the unchanged prior records and other presets.
- The validated pre-import `pg_dump` and copy-edit preimage are under
  `/Users/vadimdulub/Library/Application Support/Artline/backups/womens-rights-20260926/`.
  `backup.json` records the dump checksum; no restore or test database was created.

The three `ops/add-womens-rights*-20260926.py` scripts separate read-only planning,
selected image preparation and transactional insertion. They are local-only and
never publish. Plans reject duplicate museum accessions/source URLs and preserve
creator roles and source date uncertainty. The preset uses exact IDs and no broad
country/creator defaults; all filtering and pagination stay in Go/PostgreSQL.

## Validation

- Go `atlas` and `httpapi` tests passed with the installed Go 1.26.6 toolchain.
  The shell’s Go 1.24 executable initially conflicted with its 1.26 GOROOT; using
  the matching installed executable resolved the environment mismatch.
- Read-only preset audits passed for highlights, context/main date windows,
  publication visibility, country intersections and source-record existence.
- The dedicated read-only test verifies 44/34/32 records, seven-entry keyset
  pagination without omissions or duplicates, four Japanese events, and the
  artwork date/image rules. Database-enforced read-only transactions prohibit
  test fixtures or accidental writes.
- Saved EXPLAIN ANALYZE plans measured approximately 12.14 ms for artworks,
  0.73 ms for books and 0.21 ms for events in the current local catalogue.
  The artwork plan scopes 50 selected IDs before media/detail lookups. It still
  scans the existing 32,323-row curated-item relation for selection evidence.
  These measurements are not evidence of ten-million-artwork performance;
  representative load testing of that existing evidence path remains outstanding.
- TypeScript checking passed. Desktop (1440 px) and mobile (390 px) browser tests
  passed for the new preset, loaded images, artwork/event details, Japanese source
  attribution, absence of review labels, and absence of API writes. Two existing
  starting-list layout/accessibility tests also passed with all 31 choices.
- The event drawer now avoids duplicate source links and labels non-Wikidata
  sources correctly. A National Diet Library page is no longer called a Wikidata
  record. Initial browser failures from that old assumption/test locator and a
  cold development compile were resolved; the final runs passed.
- `git diff --check` passed. No commit, deployment or production ingestion occurred.

Browser screenshots and disposable test outputs remain in `/tmp`, outside Documents.
