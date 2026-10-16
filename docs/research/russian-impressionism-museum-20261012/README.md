# Museum of Russian Impressionism — 12 October 2026

Production delivery for the user's request to add this museum's artworks and
exhibitions, following the Wikipedia lead. The user explicitly selected
“Include this museum’s exhibitions” and “Include all dated museum artworks”.
These exceptions apply to this museum; the wider historical exhibition campaign
and general timeline retain their existing scope. Sculpture and photography
remain excluded. The real local catalogue was never written.

Browse the [museum collection](https://artlines.org/museums/museum-of-russian-impressionism)
and [all museum-source exhibitions](https://artlines.org/exhibitions?source=museum-of-russian-impressionism).
The museum's own exhibition-history link lists its 46 onsite projects; the
source-filtered link also includes four projects held at other museums.

## Delivered records

| Measure | Delivered |
| --- | ---: |
| Permanent-collection pictorial objects | 68 |
| New main-catalogue artworks | 67 |
| Existing artwork matched and linked | 1 |
| Artists represented | 41 |
| New artists / existing artists reused | 23 / 18 |
| New collection primary / alternate images | 67 / 1 |
| Post-1970 collection objects under explicit exception | 5 |
| Exhibitions and separately named special projects | 50 |
| Held or underway / announced | 48 / 2 |
| Exhibition entries, all illustrated | 74 |
| Entries with exact main-catalogue matches | 3 |
| Additional documentary exhibition objects | 71 |
| Additional exhibition images / collection images reused | 71 / 3 |
| Canonical exhibition artist connections | 9 |
| Documentary objects with exact creator links | 26 |

All new main records retain review status. Collection membership is an accepted
holding assertion, not a current-display claim. No movement classification was
inferred simply from membership in an Impressionism museum.

## Source coverage and reconciliation

The current [official website](https://www.rusimp.su/) was redesigned shortly
before this capture. Its former collection route redirects to a permanent
exhibition page without the object catalogue. The still-public legacy official
host, `https://ftp.rusimp.su`, supplies the bilingual collection, creator and
exhibition pages. Its TLS hostname mismatch is recorded as `tls_verified:false`
for public, credential-free reads; valid-TLS current pages were captured normally.

Both collection indexes were inspected: 70 distinct native objects, without
additional pagination. All 140 Russian/English object pages were captured.
Two bronze sculptures, native IDs 152 and 283, were excluded. The remaining
68 pictorial objects exhaust that public index, **not the museum's unpublished
physical inventory**. Four broadly dated twentieth-century objects preserve
their source date descriptions without invented numeric boundaries.

Five later works are retained under the explicit exception: Kim Britov's
*Winter in the Urals* (1972), Sergey Radyuk's *Bathers* (1990–1991), and
Vyacheslav Fyodorov's *Flooding at Talitsy* (1981), *Spring* (1972), and
*Fog* (1970s). Russian/English disagreements remain in the evidence, including
the erroneous English eighteenth-century date for native 78, corrected to the
Russian source's mid-twentieth-century description.

Reconciliation covered 41,362 existing artists and their aliases, then 1,714
works by the matched artists. Available images were compared, and flagged
pairs were viewed. Native 50 is the existing Yuon *The Rostov's Kremlin Gates*,
1906. The identical composition, signature and brushwork support the match;
the museum's 63 × 80 cm dimensions differ from the earlier 61 × 79 cm record.
Existing title, dimensions, date, status and primary image remain unchanged.
The new museum image is an alternate. Same-year Serov and Kuznetsov candidates
were inspected and rejected as different works.

The current archive and 58 legacy exhibition-language pages were inspected.
Repeated highlight cards were deduplicated; nine named special displays absent
from the redesigned archive were recovered. The permanent collection was not
counted as a dated temporary exhibition. Offsite events retain Novgorod, Tver,
Rostov Veliky and Zheleznogorsk as their actual venues.

The two future projects remain announced. The Fechin special display has no
secure years and remains explicitly undated. Conflicting Arkhipov/Nikiforov
opening days are withheld. Current Russian archive corrections and extensions
take precedence over stale English versions with both values retained. The
*Fragile Whims* card's 2025 typo is corrected using its explicit 2026 detail.

Seventy-four native object links under the source exhibition pages' exhibited
works sections support the documentary entries. All have authentic images and
internal artwork pages with return links. Three share permanent-collection
native IDs: Meshcherin 224, Esayan 14 and Lakhovsky 71. Other source objects are
kept as documentary exhibition records with unresolved main-catalogue matches.
No loan is assigned a holding at the organizing museum. **Full exhibition
checklists remain partial or unknown**; no catalogue publications were invented.

## Images and checks

All 139 new images retain complete source frames, margins and proportions, with
derivatives no larger than 100,000 bytes. All collection images and all 74
exhibition views were visually inspected. Three exhibition views reuse images
already delivered for the collection. Original downloads, image metadata,
checksums, captures, source URLs and credits are preserved under Application
Support. The museum offers image use by enquiry; no reuse licence was found.
Actual rights are recorded as unknown, separately from the user's selection.

The read-only museum repository verification checks the production museum,
all 68 artwork details and all three gallery pages, including image and artist
links and the later works. Live museum HTTP routes require a member session;
the browser tool was unavailable, so no authenticated browser check is claimed.
The general atlas retains its separate 1970 cutoff; these works are available
through the museum gallery.

Live exhibition verification checks all 50 details, paged entries, all 74
documentary artwork pages and reverse histories, the source and institution
filters, and the three canonical artwork filters. Every new image's publicly
served bytes were compared with its prepared checksum. See the machine-readable
delivery summary for completed check counts and production totals.

## Durable evidence and implementation

Source metadata and receipts:
`~/Library/Application Support/Artline/source-metadata/russian-impressionism-museum-20261012/`

Original images:
`~/Library/Application Support/Artline/source-images/russian-impressionism-museum-20261012/`

Local preimages and frozen plans:
`~/Library/Application Support/Artline/backups/russian-impressionism-museum-20261012/`

Important files include `collection-plan.json.gz`, `event-plan.json.gz`,
`collection-delivered.json`, `events-delivered.json`,
`collection-repository-verification.json`, `delivery-verification.json`,
the separate `object-creators-*` correction audit, and per-image upload receipts.
Source captures are immutable and checksum-addressed. Two legacy exhibition
microsite TLS failures remain recorded; accessible official archive/detail
evidence supports those events.

Implementation: `ops/rusimp_museum_20261012.py` and
`ops/rusimp_readonly_verify.go`. Production transactions are scoped and guarded
against replay. Images use the existing storage and application routes; no
application deployment or real-local database write was needed. No Cloud SQL
backup was created. Unrelated workspace changes were preserved.
