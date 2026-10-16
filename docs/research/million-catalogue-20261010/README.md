# One-million-artwork expansion — completed 11 October 2026

**The target is achieved: 1,011,720 active artworks count toward the goal**
after the final independent exclusions. The consistent production snapshot at
**11:28:13 UTC on 11 October 2026** contains **1,013,006 active artwork records,
41,089 active artists and 180,596 illustrated artworks**. Other authorized jobs
also contribute to these global totals.

The final audit subtracts the union of **1,158 explicit Rijksmuseum verso-view
records and 128 records with known dates outside or crossing 1970**. Confirmed
duplicate aliases have already been archived and do not receive another
subtraction. This is a catalogue-record target, not a claim of one million images
or a fully resolved date and attribution for every object. Unknown dates and
uncertain attributions remain explicit review data.

[Independent final audit](goal-audit-final.json) is authoritative for these
counts; the earlier controller marker `target-reached.json` did not yet subtract
the 128 date exclusions. There are **no committed, unverified import phases**.
Both campaign controllers finished. AIC ingestion was not needed or started.

## Production additions and connections

The campaign baseline was 427,414 active artworks, 24,073 active artists and
152,981 illustrated artworks. The following figures describe this campaign's
source batches, separately from simultaneous authorized work:

| Source | Records inserted | Active after identity review | Artists added | Creator links created at import | New image files |
| --- | ---: | ---: | ---: | ---: | ---: |
| National Gallery of Art | 44,271 | 44,264 | 3,549 | 40,903 | 239 |
| Metropolitan Museum of Art | 84,726 | 84,726 | 1,641 | 34,247 | 63 |
| Rijksmuseum | 398,016 | 398,016 | 10,110 | 232,340 | 450 |
| Museum of Modern Art | 19,854 | 19,854 | 1,289 | 17,202 | 0 |
| WikiArt enrichment of existing objects | 0 | 0 | 0 | 0 | 175 |

In total, these sources inserted **546,867 records**, of which **546,860 remain
active** after seven NGA duplicate consolidations. The active subtotal retains
the 1,158 legacy verso-view records that are excluded from the goal. Every new
museum object has a source citation, native identity and documented holding;
none of those holdings establishes current display. The import created **324,692
creator links**. Later individual reviews withdrew 86 unsupported Met primary
links and two unsupported MoMA secondary primary links, and corrected the Frey
and Sharpe namesake links. The original links remain in audit evidence.

The source batches added 16,589 artists. One further individually verified
Charles William Sharpe record brings this campaign's artist additions to
**16,590**. All 16,590 records were checked against their reviewed birth/death,
activity and timeline fields, including subsequent corrections; zero field
mismatches remain. Artist and artwork records remain in review and are available
through the unified active catalogue.

Seven NGA painting aliases were consolidated with older records, with redirects,
source identities and holdings preserved. Qualified circle/workshop labels were
retained; two previously unknown dates were resolved from explicit museum dates.
Two reused NGA images are not counted as newly delivered files. A further pair
of English/Spanish Antoniazzo Romano records described the same painting; the
Spanish duplicate was archived and redirected, and the canonical English record
received its WikiArt image. No extra artwork was created for that image.

## Images delivered

**927 authentic image files** were delivered in this million-catalogue campaign:
**923 primary images and four alternate reproductions**. This continuation
completed **406 files: 231 Rijksmuseum images and 175 WikiArt images**. The earlier
Cesi/Top 100 campaign's 1,426 delivered images is a separate subtotal.

The 175 new WikiArt images cover **109 distinct artists**. Matching used the
native artwork ID, creator profile, title/version and explicit date evidence.
Every delivered reproduction was visually inspected, attached in production,
and checked against its public file hash. Full frames and proportions are
preserved; derivatives are at most 100,000 bytes. Source originals are retained
under the Artline Library directories. Source labels and credits are preserved;
107 WikiArt labels say public domain and 68 say restricted. The user's source
approval is recorded separately, and no rights label caused a further approval
request or exclusion.

The WikiArt deliveries comprise 156 first-pass images, 16 Kmetty János images,
a legible Eric Gill emblem at its native 150 × 144 pixels without enlargement,
one George Romney portrait, and the reconciled Antoniazzo painting. The Romney
image matches National Trust object 1535162; its documented creation before 1789
supports eligibility, while WikiArt's conflicting 1759 date remains explicit.
The catalogue's unknown creation date was preserved.

Undated source leads and 13 Guanxiu reproductions that appear to be later
monochrome rubbings remain unresolved. They were not silently matched to original
paintings. The independent 500-painter WikiArt campaign was excluded from this
selection to avoid concurrent image changes.

Evidence: [WikiArt delivery summary](wikiart/delivery-summary-20261011.json),
`wikiart/images-001/` through `images-005/`,
[Antoniazzo verification](wikiart/antoniazzo-reconciliation/verification.json),
[NGA images](nga/images-001/verification.json),
[Met images](met/images-verification.json), and Rijks
[first](rijks/images-001/verification.json) and
[second](rijks/images-002/verification.json) image passes.

## Lifetime and attribution review

The earlier [all-painter lifetime review](../lifetimes-review-20261010/README.md)
audited 24,073 artists and applied 644 source-backed corrections. Paolo Uccello's
incorrect 1475–1475 placement was corrected to **c. 1397–1475**. Dates outside a
creator's life were retained for object/version review rather than automatically
clamped, since impressions, casts and later interventions can be posthumous.

The continuation individually corrected seven imported short-range biographies.
Johann Otmar, J. Erxleben, Francesco de Nanto and Benjamin Recknagel now have
source-backed activity timelines. Baye M. Yancey, Domenico de Rossi and William
Grotecloss retain unresolved lifespans and explicitly estimated documented-work
spans. All related artworks and creator links were preserved. See
[seven-artist verification](lifetime-followup-20261011/activity-review/verification.json).

Two confirmed namesake errors were corrected without changing artwork dates:
the Met's 1731 *Burial of Saint Petronilla* now links to Jakob Frey (1681–1752),
and Rijks RP-P-OB-73.047, dated 1854, now links to Charles William Sharpe
(1818–1899). The later Sharpe (1881–1955) and the conflated Rijks person authority
remain intact; only the evidenced object link changed. See
[Frey evidence](lifetime-followup-20261011/frey-evidence.json) and
[Sharpe verification](lifetime-followup-20261011/sharpe-review/verification.json).

The Met CSV wrongly associated a group of later drawings with Giovanni Larciani
(1484–1527). **86 unsupported primary links were withdrawn**: two current official
pages establish anonymous eighteenth-century Italian creators, and 84 others
retain explicitly unresolved original CSV labels. One pre-existing qualified
attribution remains unchanged. All 87 artworks, dates, images, holdings and
review states were retained. See
[Met review verification](lifetime-followup-20261011/met-larciani-review/verification.json).

MoMA's final five chronology flags received individual review. Two prints by
Jacques Villon explicitly say “after Cézanne” or “after Modigliani.” The two
unsupported secondary primary links were removed; Villon remains the printmaker,
and qualified composition-source names remain in titles, object labels and
citations. The current schema has no separate `after` role. Three other source
chronology cases remain explicit: a Coles Phillips photograph with a museum
date after his death, a possible posthumous Cézanne lithograph, and Josephie
Pootoogook's 1959 print with a documented cooperative/workshop printer. No
replacement dates were invented. See
[MoMA chronology review](moma/002/chronology-editorial-review.json) and
[qualified attribution verification](moma/002/qualified-review/verification.json).

The final global structural check found no active person with a fully specified
lifespan shorter than 15 or longer than 125 years. That is a consistency check,
not proof that every biography is settled. The snapshot contains 32,015 artists
with both life endpoints, 2,532 activity timelines and 3,955 estimated timelines.
Of all artwork records, 65,673 have an incomplete creation-date endpoint; these
remain explicit review records. The 947,554 records with an end date through
1970 overlap with that incomplete-date count when the start endpoint is unknown.

## Validation and recovery

- All **36 source phases** passed independent scoped production checks for
  metadata/state, native identities, citations, holdings and search documents.
  These comprise NGA, Met, 33 Rijks windows and MoMA.
- **32 offline tests pass**: six NGA, eleven source-boundary, six MoMA and nine
  AIC tests. Regression coverage includes qualified attributions, reused native
  authority IDs, approximate life dates, posthumous prints, pre-birth conflicts,
  short ambiguous biographies, multipart inventories and verso views.
- Source-date checks now also compare matched catalogue artist lifetimes, so a
  wrong namesake authority cannot bypass chronology validation merely because
  its upstream birth date is missing.
- All 927 delivered image files passed public byte-hash verification. Public
  artwork routes and corrected artist timelines were checked. Four final MoMA
  artwork routes returned HTTP 200 in 0.171–0.276 seconds. Bounded requests for
  larger artist collections were also checked; these are not a ten-million-row
  load test.
- The real local database remained read-only and unchanged: 23,479 artists,
  310,209 artworks, 225,366 creator links and 103,860 media assets. No catalogue
  fixtures or test database was created.
- Production transactions used the shared `artline-curated-ingestion` advisory
  lock, snapshot preconditions, deterministic identities, audit citations and
  batch receipts. Search/count invalidation is maintained by database triggers.
- Cloud SQL recovery backup **1791660971061** was verified before writes.
  Transaction preimages and source files remain under
  `~/Library/Application Support/Artline/{backups,source-metadata,source-images}/million-catalogue-20261010/`.
- No commit, deployment, Terraform apply or bulk image dump was performed.

Rijks harvesting captured all 16,943 pages, including seven pages beyond the
initial reported feed size. MoMA's data was pinned to one repository commit.
The Art Institute of Chicago's official archive was prepared as a fallback:
139,747 object records, 17,017 agents and 41,108 selected candidates before
reconciliation. **No AIC records or images were ingested in this campaign**
because the independently verified target had been exceeded.

Source access holds remain recorded: direct Met collection API 403, Met website
429, direct NGA website 403, NPG full pages 403 and Government Art Collection
full page 403. No denied surface was bypassed. Selected NGA images came from
its separately documented image API; Met follow-up images used captured data.

[Historical progress notes](progress-before-final-20261011.md) retain earlier
checkpoints and superseded resumption instructions. Source selections, plans,
pins, batch receipts, image decisions, transaction backups and individual
correction evidence remain immutable. Catalogue expansion has completed this
target; unresolved dates, images and source discrepancies remain documented.

## Primary sources

- [NGA official open data](https://github.com/NationalGalleryOfArt/opendata)
- [Met official open data](https://github.com/metmuseum/openaccess)
- [Rijksmuseum OAI documentation](https://data.rijksmuseum.nl/docs/oai-pmh/)
- [MoMA official collection data](https://github.com/MuseumofModernArt/collection)
- [WikiArt](https://www.wikiart.org/), with individual artwork-page evidence in each image phase
- [National Trust Romney object](https://www.nationaltrustcollections.org.uk/object/1535162)
- [Wellcome Sharpe authority](https://wellcomecollection.org/concepts/bsef73s2)
- [National Trust Sharpe attribution](https://www.nationaltrustcollections.org.uk/object/286689)
