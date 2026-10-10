# Catalogue lifetime review — 10 October 2026

Audited all **24,073 active production artist records** for birth/death evidence, timeline placement, and dates of their **303,209 distinct active artworks** (303,211 creator links). Applied and verified **644 source-backed production corrections**. This is a complete catalogue audit with selected factual corrections, not a claim that every biography or artwork date has received independent historical validation.

The user confirmed all three checks. The real local database remained read-only: **23,409 active local artists** and **224,986 associated active artworks** were audited separately. All local artist records and catalogue table counts were verified unchanged. There are [600 local correction proposals](local-readonly-correction-proposals.json.gz), explicitly not applied.

## Results

| Change | Records/fields |
|---|---:|
| Artist records updated | 644 |
| Missing birth dates supplied | 558 |
| Missing death dates supplied | 273 |
| Unsupported birth endpoints removed | 30 |
| Unsupported death endpoints removed | 31 |
| Existing numeric birth years corrected | 3 |
| Artists with a timeline change | 338 |
| Artists receiving at least one circa qualification | 128 |
| New source citations and audit entries | 644 each |
| Artwork dates, images, holdings, publication statuses changed | 0 |

Counts overlap. The updates preserve the previous 527 review and 117 published statuses. The initial 20 implausibly short lifespans, two implausibly long lifespans and two inconsistencies between complete life dates and timeline endpoints no longer occur after the reviewed corrections. That does not resolve every other source disagreement.

**Paolo Uccello:** corrected birth and timeline from **1475–1475** to **c. 1397–1475**, following the [National Gallery, London](https://www.nationalgallery.org.uk/artists/paolo-uccello). The approximation is retained in `birth_precision`, `birth_display`, the timeline label and biography. All **34 existing works** now fall within the recorded lifetime without changing their creation dates. The original Pantheon import itself supplied `birthyear=1475`; this was not a swapped database column. The original import is retained in [the source capture](uccello-original-import-records.json.gz).

Other individually reviewed cases:

| Artist/record | Before | After and evidence |
|---|---|---|
| Laura Leroux-Revault | Life 1872–1936, timeline ending 1930 | Timeline 1872–1936; [Musée Henner](https://musee-henner.fr/repertoire-des-eleves). Conflicting authority death 1930 did not override the museum. |
| Alfred Philippe Roll | Birth 1846, timeline starting 1845 | Timeline 1846–1919; [Louvre](https://collections.louvre.fr/ark:/53355/cl020215563). |
| Niccolò Rondinelli | Life 1495–1502 | Documented activity 1495–1502; [Walters](https://art.thewalters.org/object/37.517A/madonna-and-child-35/). Life dates remain unknown. |
| George Beare, William Jones and 13 other Tate artists | Museum activity columns imported as life dates | Restore literal activity labels from [Tate’s artist dataset](https://raw.githubusercontent.com/tategallery/collection/master/artist_data.csv). John Hayls retains his explicitly documented death, without treating it as an activity endpoint. |
| Bezzi Giovanni Francesco | Birth 1558, death 1571 | First documented 1558; died 1571. [POP’s author clarification](https://www.pop.culture.gouv.fr/notice/joconde/03790000278) distinguishes the events. No Nosadella identity merge was inferred. |
| Six SMK creators | Object/acquisition/activity estimates treated as life dates | Native creator histories identify the estimates. Life dates are cleared; explicit working periods or qualified object-date placement are retained. |
| Hew Locke | Life 1959–1959 | Born 1959; the [representing gallery](https://www.ppowgallery.com/artists/hew-locke) documents current activity. Timeline 2026 is a dated observation endpoint, not a death year. |
| Norma Jameson | Death 1941 | Unsupported death removed; [gallery biography](https://www.baronfineart.co.uk/paintings/summer-bouquet-norma-jameson/) documents education and work after that year. No current living status inferred. |
| William Beardmore | Life 1822–1826 | Floruit 1822–1826; [Christie’s](https://www.christies.com/en/lot/lot-4563394). |
| Helena Roouers | Life 1663–1663 | Active c. 1663; [Getty ULAN](https://www.getty.edu/vow/ULANFullDisplay?find=&role=&nation=&subjectid=500042114). |
| James Thom, subject painter | Life 1808–1815 | Born c. 1785, documented exhibitions 1808–1816; death unknown. [DNB](https://en.wikisource.org/wiki/Dictionary_of_National_Biography,_1885-1900/Thom,_James) explicitly distinguishes him from the sculptor. |
| Stephen Briggs Carlill | Life 1903–1903 | 1859–1903; [bibliographic creator authority](https://www.gutenberg.org/browse/authors/c), with [V&A work evidence](https://api.vam.ac.uk/v2/museumobject/O1070717). |
| Aztec Art, Viking art, The Game of Marseille | Individual people with life dates | Collective/tradition or project records with their qualified source periods. All artwork links retained. |

## Remaining chronology questions

The [completed artwork register](production-completed-artwork-chronology.csv) contains **1,488 records for object-level review**:

| Disposition | Artworks |
|---|---:|
| Creation interval may have inherited the artist’s lifespan | 791 |
| Possible posthumous print, edition or cast | 320 |
| Other before-birth, after-death or very-early-childhood conflict | 287 |
| Approximate/open/qualified date boundary | 90 |

These are triage classifications, not 1,488 proven errors. Physical production after an artist’s death can be valid. Approximate dates, broad intervals and qualified attributions must retain their meaning. No dates were clamped to fit a life. A further 35,239 linked works lack assessable creation dates and 6,563 lack assessable creator life dates; broad overlapping intervals are reported separately.

Examples requiring object or identity research include Jacques Bellange’s drawing catalogued in the first quarter of the sixteenth century, Giulio Carpioni’s *Atlas* dated 1550–1600, Jean-Baptiste Lallemand’s Chantilly view dated 1867, and the Elder/Younger distinction for Jean Cousin. Their original titles, dates, source labels and attributions remain intact.

**Identity conflicts:** Pietro Giacomo Palmieri, Carl Albert Walters and Hans Collaert the Elder have authorities whose dates suggest a different person or generation. Julia Rogers’s NGA birth label of 1962 conflicts with all three linked NGA prints dated c. 1935–1943; that proposed date addition was [held](held-corrections.json.gz). These require reconciliation, not a mechanical replacement of dates.

**Open life dates and source alternatives:** 1,748 active person records have unknown birth dates; 4,223 have unknown death dates or may be living. The 2,681 incomplete life timelines retain their explicit open endpoint labels; a point at a known birth/death year is not proof of a zero-length life. The review retains alternative years, chronology disagreements, event qualifiers, calendar evidence and source precision. The source-availability flags do not by themselves authorize importing a date.

## Coverage and evidence

- [Production artist register](production-completed-artist-review.csv): one row for every active and archived artist; 70 archived artists are excluded from active review counts.
- [Local artist register](local-completed-artist-review.csv) and [local artwork register](local-completed-artwork-chronology.csv): read-only findings.
- [Timeline and activity review](timeline-and-activity-review.json.gz): all 24,073 active artists, existing placements and current captured activity statements. Includes 95 source-activity/life conflicts requiring review.
- [Production summary](production-completed-summary.json) and [full machine-readable review](production-completed-review.json.gz): overlapping flag counts, uncertainty and source coverage.
- [Primary museum comparison](primary-artist-comparison.json.gz): exact existing source IDs compared with NGA, Tate and MoMA artist datasets for 5,782 distinct artists; 278 comparison decisions retain conflicting evidence.
- [Fresh date coverage](fresh-date-coverage.json): 20,393 authority IDs scheduled in 204 batches; 156 captured, two failed, 46 held. Requests stopped after HTTP 429; no retry/bypass. One earlier request also failed. Fresh captures cover 14,201 production artist identities; retained earlier authority captures cover another 4,385. These counts overlap museum coverage. A returned query is not independent historical validation.
- 4,556 artists have neither a matched bulk museum comparison nor captured date-authority comparison in this pass. They still received all structural, timeline and applicable artwork checks. Selected manual source corrections are additional to these bulk-comparison coverage counts.
- [Source evidence for flagged objects](flagged-object-source-evidence.json.gz): 2,820 existing citations and native identifiers, fetched only for 1,489 scoped IDs. This includes every final flagged object; one earlier flag was resolved by the final four artist corrections.
- Raw primary pages/datasets, full statement ranks, precision, calendars, qualifiers, references, timestamps and checksums are retained beside the reports. Museum numeric search bounds were never assumed to be birth/death dates. In particular, NGA `endyear` can be a search estimate even when the literal label says only “born …”.

## Application and verification

The [complete execution manifest](complete-execution-plan.json.gz) and [digest](complete-execution-plan-digest.json) contain every preimage, changed field, evidence receipt and reason. [Main application](applied.json) and [four-record supplement](supplement-applied.json) record the two transactions. Both use artist locks, preimage equality, status preservation, source citations and before/after audit rows. Re-running either completed phase performs zero writes.

Recovery backup **1791659656643** completed successfully before changes. Locked preimages and transaction postimages are under `~/Library/Application Support/Artline/backups/lifetimes-review-20261010/`, not in Documents.

Verified:

- [644 database records, citations and audit rows](database-verification.json), with all unedited artist fields and publication states preserved; artist/artwork/creator-link/media counts unchanged.
- [644 public API timelines](public-verification.json.gz), including Uccello’s corrected public detail page.
- [Final review register equality](review-register-verification.json) against database postimages; every final flagged object has retained source evidence.
- Six offline chronology tests: activity/search bounds versus life dates, circa/open dates, Uccello’s works, posthumous/qualified attribution, and non-person/unknown dates. No test database or local fixtures.
- Actual production `EXPLAIN (ANALYZE, BUFFERS)` for Uccello: artist-scoped index-only creator lookup plus artwork primary-key lookups, 34 rows, 0.275 ms execution in that snapshot. This is not a ten-million-row load test; that performance work remains separate.

No application deployment, publication changes, commits, image downloads, or local catalogue mutations were performed in this lifetime pass. The importer’s historical Pantheon input and all intermediate research manifests are retained; the `completed` reports are the final findings.
