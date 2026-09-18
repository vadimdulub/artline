# Denmark and Switzerland — selected catalogue expansion

17 September 2026. Implements the user's approval to add artworks and find
pictures after the [coverage audit](../denmark-switzerland-museum-gaps-20260917/README.md).
This is a bounded first batch, not completion of either country's museum coverage.

**18 September follow-up:** [nine more pictures](../denmark-switzerland-more-images-20260918/README.md)
were delivered, including independent Commons reproductions for six of the seven
Basel image gaps below. The original denied download route was not retried.
The counts below describe the original 17 September batch, not cumulative totals.

## Delivered data

Local and production catalogue targets receive the same selected changes:

| Museum | New artwork records | Other change |
| --- | ---: | --- |
| Hirschsprung Collection, Copenhagen | 15 | Country/city repaired; 9 selected images |
| Kunstmuseum Basel | 19 | Country/city repaired; evidence added to 1 existing Paula Modersohn-Becker work |
| MCBA, Lausanne | 11 | Country/city repaired |
| Ny Carlsberg Glyptotek, Copenhagen | 1 | New, distinct institution record |
| Kunstmuseum Bern | 0 | Country/city repaired |
| Sammlung Oskar Reinhart “Am Römerholz”, Winterthur | 0 | New institution, distinct from Reinhart am Stadtgarten |
| **Total** | **46** | **1 existing artwork enriched; 4 geography repairs; 2 new institutions; 6 review venues** |

All 46 new works are actual database records in **review**, with research-candidate
status, no publication timestamp and no current-institution pointer. Each has a
source-backed **review holding assertion**, not an accepted holding or current
display claim. The existing Paula record and image are preserved unchanged;
only evidence and the source identifier are added.

Twelve works retain unresolved named-creator labels without invented artist
profiles. Five retain unknown numeric dates: Rodin's original/cast date notation,
Vivian Suter's undated work, Sari Dienes's decade notation, Cézanne's slash-separated
date, and Bertha Wegmann's undated Hanna Lucia Bauck portrait. Source wording is
preserved. They are not automatically classified as eligible or published.

The batch includes Anna Ancher, Bertha Wegmann, Catharina van Hemessen,
Marguerite Burnat-Provins, Sophie Taeuber-Arp, Hedda Sterne, Helen Frankenthaler,
Sari Dienes and Vivian Suter. Museum geography is not artist nationality.

## Source selection and reconciliation

- [Hirschsprung collection](https://www.hirschsprung.dk/en/collection/art): museum-authored thematic pages and individual work captions, including women artists, Hammershøi, Krøyer and Funen painters.
- [Basel highlights](https://kunstmuseumbasel.ch/de/sammlung/schwerpunkte): selected native [collection records](https://sammlung.kunstmuseumbasel.ch/en/collection/item/1077), retaining inventory numbers, dates, media, foundation/deposit credits and image-rights labels.
- [MCBA collection](https://www.mcba.ch/en/collection/): 11 individual object pages with museum inventories and exact source dates.
- [Ny Carlsberg Foundation's Monet record](https://ny-carlsbergfondet.dk/da/skygger-paa-havet-klipperne-ved-pourville): 1882 work, Glyptotek inventory M.IN. 1753, museum connection and medium.
- Official museum address pages underpin geography. [Römerholz](https://www.roemerholz.ch/en/the-collection) is not merged with the existing Stadtgarten institution.

The plan reconciles source URLs, museum inventories, existing reproduction
identities and artist-scoped title/date leads. It examined 6,895 scoped existing
works per target; additional Bocion and duplicate Holbein authority scopes were
checked separately. No global catalogue download or browser-side collection
filtering was added.

Of 51 parsed candidates, four were held: Picasso's *Les deux frères* and
Eckersberg's Trekroner view require duplicate/version reconciliation; a Martha
Rosler work crosses the 1970 cutoff; a Louise Bourgeois work is post-cutoff.
No existing records were removed. Unknown dates are retained in review, not
invented to make a work eligible.

## Pictures and permission decisions

Nine exact Hirschsprung reproductions were selected from the public selection
linked by the museum's [photo page](https://www.hirschsprung.dk/en/the-museum/photos).
Each file's own licence and photographer/origin evidence was reviewed; the
website footer's text/data licences were deliberately excluded.

- Anna Ancher's *The Maid in the Kitchen*: digital reproduction CC BY 3.0, with credit, source/licence links and resize/compression notice.
- Krøyer's *Summer Evening at Skagen Beach* (1899): digital reproduction CC0; Hirschsprung/Statens Museum for Kunst photo credit retained.
- Seven other selected reproductions: individual public-domain statements, collection and reproduction-origin evidence preserved.

The museum's paid photo-order terms were not treated as an open licence for
its whole site. These are existing publicly released files, not commissioned
or ordered photographs. No contact forms, messages, orders or payments were sent.
Wegmann's Jeanna Bauck and Hanna Lucia Bauck image leads remain held because
their Commons dates conflict with or overstate the museum's dating.

Seven Basel images have exact per-image public-domain labels and explicit
[museum reuse terms](https://download.kunstmuseumbasel.ch/app/snippets/infoClaim.html)
covering commercial use. Nevertheless, the first selected catalogue image
returned HTTP 403. That route was stopped without retry or access-control
workaround; **no Basel images were downloaded or uploaded in this batch**.
The links and rights evidence remain saved for a permitted future workflow.
An earlier Commons API HTTP 403 was also not retried; publicly accessible normal
file-description pages supplied the separately reviewed Hirschsprung evidence.

The nine served derivatives are faithful, full-frame JPEGs, each at most 100,000
bytes. Source bytes are preserved outside Documents under:
`/Users/vadimdulub/Library/Application Support/Artline/source-images/denmark-switzerland-museums-20260917/`.
Derivative assets use the existing image-serving route; no deployment or bucket
access-policy change is needed. Image attachment does not publish an artwork.

## Safeguards, evidence and verification

Recovery backups were verified before any database change:

- Local custom-format PostgreSQL dump and preimage files: `/Users/vadimdulub/Library/Application Support/Artline/backups/denmark-switzerland-museums-20260917/`.
- Cloud SQL backup `1789675309278`, verified `SUCCESSFUL` for `artline-postgres` in `artline-508319`.

All source captures, hashes, parsed records, plan/review files, per-record
application receipts, image preparation/upload receipts and verification results
remain in this research directory. These machine-generated evidence files follow
the repository's existing git-ignore rules; they remain on disk, not in a commit.

Important receipts:

- `metadata-plan.json`, `metadata-review.json`, `metadata-applied/{local,cloud}/`: exact selected records and pinned approval.
- `geography-plan.json`, `geography-review.json`, `{local,cloud}-geography-applied.json`: exact geographic changes.
- `image-selection.json`: 16 rights-reviewed image candidates; `image-download-holds.json`: seven Basel holds.
- `image-download-selection.json`, `image-visual-review.json`, `images-prepared/`, `image-upload-summary.json`: nine downloaded/visually checked derivatives and uploads.
- `verification.json`: scoped read-only database checks, unchanged legacy record, date/creator preservation, review states, geography and local/cloud parity.
- `public-verification.json`: live JPEG response size/checksum checks and museum geography responses. This verifies delivery, not publication or current display.

Automation lives in `ops/denmark-switzerland-museums.py`, reusing the existing
guarded upload workflow. The Go image preparer has a separate opt-in DK/CH
host/rights adapter; previous Dutch/German rules remain unchanged. Offline
tests cover source-date uncertainty, excluding footer licences, pinned metadata
selection, approved hosts/licences, duplicates and bounded full-frame JPEGs.
No test database or fixtures were inserted into the real catalogue.

Final verification passed for both databases: 46 new review records, one
unchanged legacy artwork with added evidence, nine image attachments, all six
museum geographies, preserved dates/creator labels and local/cloud parity.
All nine production JPEG responses passed content-type, byte-size and SHA-256
checks. The 11 offline Python museum tests and four Go image-preparer tests passed.

## Remaining scope

Bern and Römerholz need object-level expansion; Glyptotek has only a first
selected work. Louisiana, ARoS, Kunsten, Zentrum Paul Klee and the other regional
targets in the audit remain a research queue, not implied completed coverage.
MCBA and Basel still need more reusable image delivery. The wider geography
backlog is not closed by these four repairs.

Russian, Greek, Byzantine and post-Byzantine collection leads remain priorities
regardless of museum country; this batch neither filters them out nor invents
named creators for anonymous/workshop material. Their institution-level leads
still need object-level evidence and the supported attribution workflow.

No commits, deployment, Terraform changes, automatic publication, accepted
holdings, current-display assertions, exhaustive ingestion or national-coverage
claims were made. Offline tests and this bounded audit are not evidence of
10-million-row performance; representative query-plan/load testing remains open.
