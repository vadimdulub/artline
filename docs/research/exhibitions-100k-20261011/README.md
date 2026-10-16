# Exhibition catalogue: 100,000-event collection

User authorization, 11 October 2026: “ok, now we have sources, go ahead add 100k exebitions”.

**Target achieved in production: 107,683 distinct exhibitions recorded as held.**
Independent read-only verification completed on 11 October 2026, 18:04 UTC,
after source delivery and identity reconciliation. No app deployment or commit
was performed; the new browsing code is implemented and tested locally.

| Verified measure | Total |
| --- | ---: |
| Active exhibition records | 108,969 |
| Held exhibitions counted toward the target | **107,683** |
| Uncertain / announced / cancelled records, excluded from target | 1,212 / 64 / 10 |
| Documentary artwork entries | 195,677 |
| Exhibitions with collected artwork entries | 40,596 |
| Distinct exhibition–artwork links | 19,540, involving 7,694 existing artworks |
| Distinct exhibition–artist links | 19,341, involving 3,447 existing artists |
| Participant records, including unlinked labels and organizations | 426,721 |
| Historical venue occurrences | 93,203 |
| Venue rows linked to existing institutions | 7,200, involving 163 institutions |
| Catalogue / installation / other bibliographic / press-release references | 624 / 1,299 / 2,019 / 1,589 |
| Observed held-exhibition date span | 1893–2026 |

Artwork entries include 48,220 marked exhibited, 147,233 catalogued, 222
proposed and two uncertain. These are source-entry counts, not newly created
artworks, complete checklists, or proof of current display. There are 19,550
source entry rows linked to artworks and 19,343 participant rows linked to
artists; the distinct connection totals above remove repeated pairs.

The institution research ledger covers all 2,240 active canonical institutions:
163 have collected venue records; the remaining 2,077 are explicitly not yet
researched by this campaign. This is not an all-years survey of every museum.

## Counting and evidence

The target is 100,000 distinct documented exhibitions recorded as held, across
all years. Museums are optional. Online shows, commercial galleries and other
independent venues remain identifiable. Future, cancelled, ambiguous event-type
and unresolved duplicate records remain available but do not count toward the
held target. Source-reported occurrence is distinguished from independent
installation verification. The evidence basis is stored on each event.

Touring stops are occurrences of one exhibition. Bibliographic records,
participant rows, catalogue entries and image files are not extra exhibitions.
Exhibition participation never establishes ownership or current display.
Artline's artwork creation cutoff remains separate: this campaign creates
documentary entries and links existing artwork identities; it does not import
post-1970 artworks into the artwork catalogue.

## Operational sources

| Source | Collected source records | Interpretation |
| --- | ---: | --- |
| [MoMA CSV](https://github.com/MuseumofModernArt/exhibitions) | 1,788 | ExhibitionSortOrder identifies events; ExhibitionID has blanks and repeated “No#”. 34,558 CSV rows are participant/role rows. One same-title/venue/date pair was conservatively consolidated, preserving both native exhibition numbers. The file is CP1252 in the retrieved version, despite the README's UTF-8 description. No artwork checklist is supplied. |
| [Cleveland API](https://openaccess-api.clevelandart.org/) | 5,718 | Complete retrieved API listing at this capture, including external exhibitions, touring venues and planned loans. Native object IDs securely link existing Artline works. Each event's artwork array is a partial list of Cleveland-associated objects, not necessarily a complete exhibition checklist. |
| [Art Platform Japan](https://artplatform.go.jp/exhibitions/) | 10,852 | Publisher's public download query includes tourStartExhibitionID, dates, organizers, artists and bibliography. Explicit tour IDs initially group these into 10,170 events, before cross-corpus duplicate reconciliation. No artwork checklist is supplied. |
| [Artsy public GraphQL schema](https://github.com/artsy/metaphysics) | 91,393 | Closed non-fair shows through the documented public API, with stable IDs, dates, presenting organizations, artists and at most five public artwork-list entries per show. No credentials or introspection. Bounded metadata retrieval only; 914 source pages, with seven blank-title rows excluded. Collection stopped after enough supported records were available for the target. |

Final source attribution: Art Platform Japan contributes 10,159 active events
(9,992 held), Artsy 91,339 (90,524 held), Cleveland 5,698 (5,469 held), and MoMA
1,787 (1,712 held). **These source subtotals overlap** where sources document
the same canonical exhibition; sum the canonical event table for the goal.

Artsy's query reported 153,151 available closed non-fair show records when
collection began. This is a provider total, not an Artline import count or a
deduplicated exhibition claim. Fair, auction, inventory and other suspicious
show titles receive event-type review; a provider's “show” label alone does not
make those candidates count. Blank titles are excluded without replacements.

The public Artsy artwork list is labelled **catalogued**, with its total,
retrieved sample size and has-more flag retained. It is not represented as a
complete or final checklist. Online status follows the provider field and is
not independently verified. Physical presenter/location evidence remains
separate from museum identity.

The first APJ normalization only recognized ISO ranges. The date review
recovered explicit dotted ranges and qualified ISO formatting from the
unchanged raw period text. Abbreviated and ambiguous ranges were not completed.
The amendment retains preimages, parser version, original text, occurrence
dates and event tour spans. It also reclassifies future/uncertain Cleveland
artwork associations as proposed/catalogued rather than exhibited.

Final identity reconciliation consolidated 26 additional exact duplicate pairs,
archiving the old identities while moving every source and relationship to the
canonical event. Earlier import plans had already reconciled repeated native
IDs, exact dated matches and explicit APJ touring stops. Another 110 identities
were held out of the target: 36 overlapping date-range candidates, 60 possible
tours, three possible festival/programme records and 11 possible administrative
loan or conservation records. These are uncertainty flags, not invented tour
relationships or claims that the source events never occurred.

Artsy artist reconciliation reviewed 3,618 unique full-name candidates. It
accepted 2,974 source identities and left 644 absent, qualified or conflicting
life-date identities unlinked. This produced 17,599 participant links; MoMA's
native-ID links add 1,744. No linked artist was born after the associated held
exhibition ended. Two Cleveland entries for the 1932 May Show—Stevan Dohanos's
*Pigeon Roost* (1934) and *The Pooch* (c. 1949)—contradict the creation dates in
their own source captions. Their participation is uncertain; the original
source association and artwork dates are retained.

## Delivery and data model

Migrations `0047_exhibitions_catalogue.sql` and
`0048_exhibition_browse_indexes.sql` were applied to production, with a recent
successful Cloud SQL backup and immutable delivery receipts. Tables separate:

- exhibitions and source records;
- venue occurrences, with nullable museum links;
- artists, organizers and other participants;
- documentary artwork entries, with nullable existing-artwork links;
- publications, including reviews/checklists/catalogues when identified;
- institution/source research coverage.

Records retain review status as audit data. All active records are browsable.
Exact native object IDs establish artwork links; titles alone do not. Artist
identity reconciliation requires a unique full-name candidate, an exact source
birth year and no conflicting known death year. Unresolved identities and date
conflicts remain recorded as research leads. Artist biographies and lifetime
metadata are not rewritten by this campaign.

The real local database is read-only throughout. No account/session/bookmark or
catalogue fixtures are created. Raw downloads and normalized batches live under
`~/Library/Application Support/Artline/source-metadata/exhibitions-100k-20261011/`.
Backup evidence lives under
`~/Library/Application Support/Artline/backups/exhibitions-100k-20261011/`.
This directory contains capture receipts, immutable plans, post-commit delivery
receipts and reviewed amendments. Machine evidence is retained locally and
ignored by Git; this report and the scripts document reproduction.

## Interface and verification

The new `/exhibitions` directory and `/exhibitions/[id]` pages show dates, source
and format filters, event uncertainty, venues, participants, documentary works
and citations. Artist, artwork and museum pages link to scoped exhibition
searches. Museum destinations preserve the existing sign-in policy; exhibition
records themselves are public. Go/PostgreSQL own filtering, counts, keyset
paging and bounded relationship enrichment. The client never loads the corpus.

Python evidence/date tests and Go package/HTTP tests pass. Browser checks cover
public search, source evidence, artwork pagination without overlap, malformed
filters, museum sign-in/focus restoration, mobile search and layout widths
1440, 1024, 768, 390 and 320. Accessibility checks cover desktop and phone.
The in-app browser connection failed before initialization; the project's
Playwright suite supplied the browser checks instead. Previews use an isolated
temporary web checkout and an API connection forced read-only, with migrations
disabled. The member sidebar was checked with an existing API's ephemeral
local-debug response and no stored account/session fixtures. App code has not
been deployed in this collection pass.

Independent SQL checks found no missing event sources, source/relationship
identity mismatches, reversed dates, held future starts, included fair/stub
flags, future events claimed as exhibited, blank titles, or artwork entries
absent from their captured source lists. The two creation-date conflicts no
longer claim exhibited participation. All 995 batch receipts verify their
source rows after commit. Final data receipts are `final-verification.json`,
`connection-counts.json`, `identity-review/final-delivered-v2/delivery.json`,
`chronology/delivery.json` and `coverage-delivery.json`.

The real local catalogue remains exactly 23,479 artists, 310,209 artworks and
1,599 institutions, with no exhibition table added locally. Production artist
and artwork rows were not created or rewritten by this campaign; unrelated
production catalogue changes are not counted as exhibition delivery.

Read-only integration checks exercised the complete 108,969-event corpus and
its links into the million-artwork catalogue, recording 18 exact PostgreSQL
query plans. A source-filtered MoMA page initially walked 100,835 global event
rows. Materializing matching IDs/years before selecting full page records
reduced its measured database execution from 601.632 ms to 61.962 ms, and buffer
hits from 403,930 to 6,029. The final sample's slowest query was 128.812 ms.
These are observed execution plans on the current database, not concurrent-load
benchmarks or proof of ten-million-artwork capacity. The original and improved
plans are retained in `performance/` and `performance-scoped/`.

The read-only local preview is available at
`http://127.0.0.1:3107/exhibitions` while the preview processes are running.
It uses the production exhibition corpus through a connection that cannot
write, and does not migrate the real local database.

## Remaining coverage limits

This is not a completed survey of every museum or every year. The large
commercial-gallery archive contributes most event volume. Historical checklist
and critics' archive extraction remain distinct, valuable follow-up work; a
large exhibition total does not establish complete object-level histories.

The Art Institute API returned a small successful response but repeatedly timed
out on bounded larger pages. Artfacts and ARTL@s access restrictions remain
respected; no alternate authenticated route was used. MoMA's CSV ends in 1989.
The source register in [exhibition-sources.md](../../exhibition-sources.md)
retains the additional museum, book, catalogue and criticism research routes.

## Commands

Use the environment containing `requests`, `beautifulsoup4` and `psycopg`:

```sh
python ops/exhibitions_collect.py moma
python ops/exhibitions_collect.py cleveland
python ops/exhibitions_apj.py
python ops/exhibitions_artsy.py --start-page 1 --pages 275
python ops/exhibitions_deliver.py plan --provider artsy
python ops/exhibitions_deliver.py apply --provider artsy
python ops/exhibitions_date_review.py
python ops/exhibitions_artist_links.py --run first --apply
python ops/exhibitions_reconcile.py --run reviewed-final --apply
python ops/exhibitions_chronology.py
python ops/exhibitions_verify.py --coverage
python ops/exhibitions_verify.py --report independent-verification
python -m unittest discover -s ops -p test_exhibitions.py
```

Captures and plans are immutable; changing interpretation requires a versioned
amendment, not overwriting evidence. Resume delivery from receipts. Final
identity consolidation must follow collection and delivery so later batches
cannot resurrect an archived duplicate identity.
Subsequent planning resolves native IDs through their current production
canonical identities, rather than reusing superseded IDs from historical plans.
