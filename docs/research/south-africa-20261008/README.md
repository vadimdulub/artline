# South African collection expansion — 8 October 2026

Published **342 new artwork records, 49 artist profiles and 7 institution records**
to production at 16:01 UTC. South Africa now has **352 visible works across 9
museum/collection pages**. This is a selected expansion, not an exhaustive national
museum inventory. All new works have source-backed creation dates no later than
1970 and accepted collection holdings; none assert current display.

User authorization: “nice, let's cover South Africa”, continuing the explicit
instructions to publish directly, add painters as needed, and keep entries while
showing known information only. No additional approval phase was required.

[Browse South Africa](https://artlines.org/museums?country=ZA).

| Collection | City | New artworks | Visible total |
| --- | --- | ---: | ---: |
| [Rupert Art Foundation](https://artlines.org/museums/south-africa-rupert-foundation) | Stellenbosch | 189 | 189 |
| [Rembrandt van Rijn Art Foundation](https://artlines.org/museums/south-africa-rembrandt-foundation) | Stellenbosch | 9 | 9 |
| [Nelson Mandela Metropolitan Art Museum](https://artlines.org/museums/south-africa-mandela) | Port Elizabeth | 52 | 52 |
| [University of Pretoria Museums](https://artlines.org/museums/south-africa-up) | Pretoria | 78 | 78 |
| [South African National Gallery](https://artlines.org/museums/wikimedia-museum-q1419469) | Cape Town | 2 | 12 |
| [Johannesburg Art Gallery](https://artlines.org/museums/africa-jag) | Johannesburg | 2 | 2 |
| [Tatham Art Gallery](https://artlines.org/museums/south-africa-tatham) | Pietermaritzburg | 8 | 8 |
| [Wits Art Museum](https://artlines.org/museums/south-africa-wits) | Johannesburg | 1 | 1 |
| [Oliewenhuis Art Museum](https://artlines.org/museums/south-africa-oliewenhuis) | Bloemfontein | 1 | 1 |

## Sources and decisions

- **Rupert-managed collections:** the [official catalogue](https://rupertmuseum.org/collections/)
  names the holding foundation on each object. The two foundations are separate
  institution records, both described as managed by Rupert Museum; no assertion
  is made that every object is housed or displayed in that building. Selection
  used 1,305 distinct metadata records from these two collections, an explicit
  work-date field, supported media and a maximum of 30 works per artist, followed
  by individual object-page checks. Collection ownership, inventory numbers,
  Afrikaans titles, original materials and dimensions are preserved.
- **Pagination correction:** `/collections/page/N/` silently repeats page one.
  The initial non-v2 Rupert files are superseded diagnostics and must not be
  imported. The `*-v2.json.gz` files use the same read-only AJAX search action
  as the public collection form and verify page numbers and distinct native IDs.
  No WordPress publication/update date was used as artwork creation.
- **Mandela:** [official municipal collection search](https://www.artmuseum.co.za/SearchCollection.aspx?pageID=5)
  and individual object pages. Fifty historical creator queries provided bounded
  discovery; object IDs, accession, work-date and material fields were checked
  against the individual page. Sub-accessions distinguish series items. The
  Edward Orme/Clarke and Dubourg record retains both qualified publisher and
  printer labels without making the publisher a primary painter. Port Elizabeth
  is the city label used by the source.
- **Museum-authored Google Arts & Culture:** [Pretoria](https://artsandculture.google.com/partner/university-of-pretoria-museums)
  and [Iziko](https://artsandculture.google.com/partner/south-african-national-gallery)
  partner pages, their public facets and individual object records. Provider,
  creation date, materials, dimensions and gallery-specific links were checked.
  Private collections, courtesy loans and Ditsong-owned material appearing under
  the Pretoria provider were excluded. Iziko's broader provider name alone was
  insufficient: an explicit National Gallery link was required.
- **Medieval African art:** six distinct Mapungubwe gold objects, including the
  rhinoceros, were selected from Pretoria's dated records. They use `metalwork`
  and the documented cultural context, with no invented named creator. The
  archive credit stays in the citation; it is not a medieval artist. A separate
  close-up of the rhinoceros was excluded as an alternate view.
- **Johannesburg:** the [gallery's official Art Handbook](https://arts-culture-heritage.joburg/wp-content/uploads/2022/06/JAG-Art-Hand-Book-2022.pdf),
  printed page 4 / PDF page 5, establishes Gerard Sekoto's *Yellow Houses: A Street
  in Sophiatown* (1940) and *Beyond the Gate* (c.1940), with collection credits,
  materials and dimensions. Captions were rendered and visually inspected. The
  online feed's unrelated/default dates were not imported or silently repaired.
- **Tatham:** [Hua Yang's 2004 collection catalogue](https://researchspace.ukzn.ac.za/items/2ffd4da9-497e-4c3f-8310-4f363857c44b)
  was prepared with gallery access, inventory documentation and the author's
  2003 photographs. Eight records use explicit composition dates and inventory
  numbers, not acquisition years or artist lifespans. Caption pages were rendered
  and inspected, including continuations across pages. Accent/italic OCR errors
  were transcribed from the visible originals. These are historical documented
  holdings; subsequent movement was not independently established. Confidence
  is 0.88 as an editorial assessment, not a calibrated probability.
- **Wits:** the [official collections page](https://www.wits.ac.za/wam/collections/)
  identifies *Black Hair*, Gerard Sekoto, charcoal on paper, 1949, and documents
  the Sekoto Collection's donation to WAM. The original caption is preserved.
- **Oliewenhuis:** the [National Museum's exhibition archive](https://nationalmuseum.co.za/oliewenhuis-temporary-exhibitions/)
  explicitly identifies Eduardo Villa's *Torso* (1968), bronze, as a permanent
  collection purchase. The 2023–2024 exhibition does not establish current display.

## Unknowns, duplicates and limits

All 342 new records are `published`, with `research_candidate=false`. Metadata
unknown to the sources remains null. This pass attached no images and did not
claim rights clearance for future reproductions. Actual source rights labels
remain in the captured records and citations.

The immutable plan records 40 further exclusions from the preliminary selected
set, including 8 already-existing Iziko works. Other exclusions cover obvious
Iziko default/lifespan date conflicts, a Wilhelmina plate's suspect 1850 date,
private loans, an unresolved duplicate Google plate entry, edition-numbered
bronzes without a confirmed physical casting date, and Portway's conflicting
*Palma '62* / 1961 catalogue entry. Earlier selection files also preserve unknown,
post-1970 and unsupported-type candidates. Nothing was deleted from production.

The 49 new named artists use museum creator authority pages and documented work
activity, explicitly labeled as such. Birth/death dates and biographies remain
unknown. Initial-only or surname-only creators, the ambiguous Paul du Toit name,
manufacturers and qualified contributors retain object-level labels. Named people
were not inferred from museum location or nationality.

An additional artist spelling was reconciled before publication: Rupert's
“Gerrit Van Vught” is an explicit alias of Wikidata Q18516533, already attached to
the existing Gerrit van Vucht profile. The source spelling and corroboration are
retained in the artwork citation. A duplicate artist was not created. The draft
plan has 50 new artists; `publication-plan-final.json.gz` supersedes it with 49.

The full institution directory, artist names and aliases, native object IDs,
canonical source URLs, museum-scoped accessions/titles and 3,371 existing works
scoped to matched artists were checked. Generic titles belonging to different
creators, clearly different dated versions and separately held print impressions
were not merged. Existing artist profiles, institution records, the ten earlier
South African artworks and their images, citations and publication states were
compared before and after the transaction and preserved.

Additional sources were assessed without manufacturing catalogue records:
William Humphreys' visible pages lacked usable creation dates and many individual
pages explicitly withheld public viewing; Sanlam's `year` appears to be an
acquisition year and contradicts dated titles; Irma Stern Museum and the direct
UP collection site returned 403; Durban's current overview supplied no selected
dated object catalogue; Tshwane's direct site had TLS failures. Access controls
were not bypassed. The unavailable current Tatham website was not treated as
evidence of closure. Empty or unsupported institutions were not added merely to
make them appear in browsing.

## Verification and audit

- Nine offline tests passed, including corrupted captures, unsafe dates,
  duplicate IDs, private loans, edition uncertainty, contributor roles, activity
  versus lifespan, source ownership and false current-display claims.
- Every selected artwork was revalidated against the pinned source evidence.
- One transaction used the shared curated-ingestion advisory lock, checked
  protected records and identity conflicts, inserted bounded batches and verified
  every intended field and relationship before commit.
- Production readback confirms all **342** records are `eligible` under the
  database creation policy and have accepted selection evidence.
- Live HTTP pagination found all **342** new IDs across **352** visible works in
  the nine collection pages. Pages were bounded to 60 records. Nine individual
  detail responses confirmed published status and source citations.
- **14 live browser checks passed:** nine artwork drawers, two mobile drawers,
  two new artist pages with loaded artworks, and the South Africa directory.
  No page errors, review labels or empty-detail wording were observed. Desktop
  and mobile screenshots were visually inspected. The in-app browser failed
  before execution (`sandboxPolicy` metadata); headless Chrome was the fallback.
- The artist lookup's production query plan is recorded. This data-only task
  made no backend query or frontend changes; no claim of 10-million-row load
  verification is made.

Key artifacts:

- `publication-plan-final.json.gz`, SHA-256
  `97d052c89b017c94430a6b81af186399d85209c78b107359c78b91ed846cd3f2`.
- `production-publication-receipt.json`, `production-readback.json`.
- `publication-register.csv`: all source and public artwork links.
- `live-api-verification.json`, `live-browser-verification.json`.
- `captures/`: immutable HTTP receipts and compressed bodies with checksums.
- `production-baseline.json.gz`, duplicate audits, selection files and holds.

Private baseline, plan and full postimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/south-africa-20261008/`.
Disposable PDF renders and browser screenshots are under
`/tmp/artline-south-africa-20261008/`. No local catalogue fixtures, commits,
infrastructure changes or frontend redeployment were needed.

Implementation: `ops/south-africa-20261008.py` captures selected source evidence;
`ops/south-africa-publish-20261008.py` prepares and applies the immutable plan;
`ops/test_south_africa_20261008.py` contains offline safety tests; the two
`ops/south-africa-live-20261008.*` scripts perform read-only live checks.
