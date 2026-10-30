# Remaining guide-linked museum profiles — 30 October 2026

The owner requested deployment, commit and push of the museum interface changes,
then continued research into other museum and gallery details. The interface is
live; this pass reviews the 63 remaining institution records in the published
86-guide / 88-institution mapping. Together with the previous 28 profiles, this
covers 91 existing institution records, including three outside that mapping.
It is not a complete editorial review of the entire institution inventory.

Each reviewed profile receives two short, original English paragraphs and source
references. Research used official museum pages, public institutional publications,
municipal visitor information and, for Chicago, Wikipedia alongside the museum’s
published shop address. No native museum HTTP captures or full-page reading claims
are implied by web-tool research. The Art Institute’s main website returned 403;
it was not retried through native HTTP. Two inaccessible page paths at Auckland
and Rietberg were not retried; independently indexed institutional or tourism
sources supplied the required information. The previous AGNSW restriction remains.

Twelve location links are reviewed: ten country-level placeholders become specific
cities in the same country, and the missing primary locations for the Dresden
museum group and Tate are filled. Eight city records are necessary; these carry
no guessed coordinates. Shared country place rows and existing venues are not
renamed. The other recorded primary cities are retained.

The Dresden guide now links to the existing Staatliche Kunstsammlungen Dresden
record, rather than Kassel’s similarly named Old Masters gallery. Dresden’s new
introduction identifies it as a museum network, with the Old Masters gallery as
one part. Tate, Getty, the Royal Museums of Fine Arts of Belgium and the National
Museum in Kraków likewise retain their institution and branch distinctions.
Duplicate existing SAAM and Picasso institution records are not merged, and no
artworks or holdings are moved.

The write is limited to existing institution descriptions/place links, new city
rows, a reference source, citations and atomic audits. It uses three shared
transaction locks, checks exact fresh preimages and records every resulting row.
Artwork facts, images, makers, holdings, display assertions, identity links,
review statuses and all existing venues remain outside the write scope.

A shared instruction change stopped the first apply before any database connection
opened. The entire instruction delta was read: it finalized an unrelated image
pass. The original plan and guard stop are retained; a fresh plan rechecked the
unchanged museum preimages before dispatch. No dispatched transaction is replayed.

Curated copy and sources are in [profiles-reviewed.json](profiles-reviewed.json).
Exact plans, database preimages and full public response bodies stay outside
Documents in the matching source-metadata and backups directories under
`~/Library/Application Support/Artline/`.

The delivery is complete for these 63 profiles. Transaction **1072428** (backend
**1364682**) retained all three locks before writes and after **135 atomic audits**.
Fresh read-only verification checked all 135 resulting rows and audits. All 63
production detail responses contain the exact reviewed copy and city/country.
The previous 28 profiles and all 71 parent records/audits are unchanged; 54 existing
venues and 105 pre-existing citations are preserved. Never replay the transaction.

The closing inventory contains **2,665** active canonical institution records
(one more than the earlier frozen census due to concurrent catalogue work).
**2,574 profiles remain outside this independent editorial review**, and **1,278
still lack a country** across their primary place and active venues. Missing data
has not been replaced by guessed locations or generic descriptions.

See [RESULT.json](RESULT.json) for the compact delivery and remaining-work record.
The production interface deployment is recorded in
[the deployment receipt](../../deployment-20261030-museum-pages.json).

The deployed repository also passes both production read-only regressions with
the 63-profile inventory: exact copy/location projection, word-order search,
country intersection and the Armenia country facet. An initial test harness used
libpq’s password-omitting diagnostic DSN and failed authentication before queries;
the existing configured credential was then passed in-memory and both tests pass.
No credential or session token is stored in the test log.
