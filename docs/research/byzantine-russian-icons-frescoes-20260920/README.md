# Byzantine and Russian icons and frescoes — 20 September 2026

Added **804 artworks to the real local catalogue**: **777 icons and 27 fresco
records**, including seven Russian fresco ensembles. Attached **eight visually
reviewed CC0 museum images**. All additions remain `review`, unpublished and
marked as research candidates. The user's requested scope is Byzantine,
post-Byzantine and Russian traditions; Italian fresco expansion and architecture
were outside this pass.

## Added records

| Official source | New artworks | Attached images |
| --- | ---: | ---: |
| State Russian Museum | 699 | 0 |
| Byzantine and Christian Museum, Athens | 69 | 0 |
| Museum of Byzantine Culture, Thessaloniki | 20 | 0 |
| Metropolitan Museum of Art | 2 | 2 |
| Cleveland Museum of Art | 3 | 3 |
| Walters Art Museum | 4 | 3 |
| Kirillo-Belozersky Museum / Museum of Dionisy Frescoes | 1 ensemble | 0 |
| Novgorod Museum-Reserve | 6 ensembles | 0 |
| **Total** | **804** | **8** |

The pinned selection contains 822 objects. Eighteen Athens records already
existed and were preserved, with no duplicate insertion. Of the 777 icons,
775 are paintings. A mosaic icon and a mixed carved/painted icon retain their
icon form, literal medium and `unknown` broad work type pending classification.
No invented anonymous artist profiles were created. Existing Rublev and
Theophanes authorities were reused only for explicit matching attributions;
other source names, workshops and attribution qualifiers remain object labels.

Seven ensembles are counted once each: Ferapontov Cathedral of the Nativity of
the Virgin; the churches at Volotovo, Ilyina Street, Theodore Stratilates on the
Brook, Kovalevo, Skovorodka and Gorodishche. Individual scenes were not invented
as additional objects. Museum documentation establishes their research sources,
not museum ownership of the churches or ensembles.

There are **797 source-backed holding assertions and zero display assertions**.
Owner selection is recorded in the personal collection, separately from any
museum masterpiece designation. The Thessaloniki museum was added as a review
institution with its official website; no location or country identifiers were
fabricated.

## Sources and scope

Object-level captures retain titles, original date wording, accession numbers,
media, dimensions, attributions, provenance and retrieval times where supplied.
Relevant starting points include the [Russian Museum iconography catalogue](https://rusmuseumvrm.ru/collections/iconography/index.php),
[Athens digital collections](https://www.ebyzantinemuseum.gr/?i=bxm.en.collections),
[Thessaloniki wall paintings](https://www.mbp.gr/en/collections/wall-paintings/),
and [Thessaloniki wooden icons](https://www.mbp.gr/en/collections/wooden-icons/).
Ensemble evidence comes from the [Ferapontov museum record](https://kirmuseum.org/ru/exhibitions/freski-dionisiya-v-sobore-rozhdestva-bogorodicy),
[Volotovo museum record](https://novgorodmuseum.ru/muzei/cerkov-uspeniya-v-volotove)
and [Novgorod restoration centre](https://novgorodmuseum.ru/muzei/centr-restavracii-monumentalnoj-zhivopisi).
Exact per-object URLs and captured response hashes are in the pinned selection.

This is a bounded metadata expansion, not a complete inventory of these
traditions. Discovery included 739 captured Russian Museum object pages,
95 Athens records and 21 Thessaloniki records. Failed or unavailable discovery
routes remain evidence; access restrictions were not bypassed.

## Dates, identities and review holds

**666 new records have eligible creation bounds; 138 require date review.**
The latter comprise 122 unknown dates, one open-ended date, and 15 conservative
century/range envelopes crossing 1970. Source expressions such as early or late
century remain verbatim; a precise year was not invented. These 138 records
remain in the database and museum review views, outside the dated atlas.

The final audit corrected three records, preserving their original source
wording and preimages: two instances of the Cyrillic place name *Холуй* had
contributed a spurious Roman numeral, and one icon date had been combined with
the separately labelled date of its metal cover. The latter now has unknown
structured creation dates pending editorial separation. See the
[reviewed corrections](date-corrections-reviewed.json) and
[application receipt](date-corrections-applied.json). The initial, overly broad
`date-corrections.json` proposal was **not applied**; merely stating that an icon
has a cover does not invalidate its stated creation date.

**52 metadata candidates were held:** 25 need medium/type review; six are
textiles, banners or carvings; six are copies, tracings or studies; six need
separated-layer identity review; three are components of a separately selected
complete triptych; two official Russian Museum pages share the conflicting
accession ДРЖ-917; and four concern a multi-accession entry, a pre-Byzantine
Late Roman wall painting, a liturgical textile/print and a carved object.
Both conflicting accession records remain captured; neither was guessed or
merged. Accession punctuation is significant: ДРЖ-1-24 differs from ДРЖ-124.

## Images

Only nine selected museum CC0 reproductions were downloaded. Eight complete
object/fragment views passed visual inspection and are attached. The Walters
photograph for accession 37.568 shows only the Virgin Mary panel of a three-panel
Deesis; its image and provenance are retained unattached. See the
[visual review](image-visual-review.json) and [attachment receipt](images-attached.json).

Every attached application JPEG is at most 100,000 bytes, resized proportionally
without cropping. Image identity, exact source URLs, credits, CC0 evidence,
original/derivative hashes and transformations are retained. The remaining
**796 new artworks have no attached image**; source age alone was not treated
as photographic permission. Broader Russian, Greek and fresco image coverage
remains an explicit follow-up.

Application assets are in
`apps/web/public/assets/artworks/imported/byzantine-russian-20260920/`.
Nine source originals are archived separately under
`~/Library/Application Support/Artline/source-images/byzantine-russian-icons-frescoes-20260920/originals/`.

## Verification and recovery

The [final read-only verification](verification-135008.json) passed for all
804 exact receipt IDs, source citations, classification/date fields, review
state, selection evidence, holdings and image associations. It also passed
**76 bounded API checks** and **eight HTTP image checksum checks**. API cases
cover every source, date precision, named/anonymous creators, early Byzantine
records, ensembles, museum pagination, the three date corrections and media.
Eight offline parser/identity regression tests passed.

The existing local API on port 8081 has public research preview enabled; that
setting was preserved and does not publish database records. Image delivery was
checked through a fresh temporary instance of the existing Next build with the
shared real public-assets directory. That instance was stopped afterward.
An already-running production-mode preview must restart to discover newly added
public files; the running preview and other development processes were left
intact. No production database, deployment or cloud storage was changed.

The initial wider baseline contained 109 artwork records. All 18 matched
existing entries are unchanged. Seven other baseline records changed outside
this import's receipt IDs during the session; the final verification records
their changed fields without reverting them or attributing their changes to
this batch. Counts here derive from exact receipts, not global catalogue deltas.

The identity preflight used `external_identifiers_url_idx`; the final bounded
ID lookup has a recorded execution plan. These local checks are not a
10-million-artwork benchmark. Representative large-scale ingestion, query and
cache invalidation load tests remain separate backend work.

The validated pre-import PostgreSQL dump is:

`~/Library/Application Support/Artline/backups/byzantine-russian-icons-frescoes-20260920/local-before.dump`

Size: 589,142,267 bytes. SHA-256:
`fb7c65739b015a38f28e29b42ef7c72fcee2f82a7be54222445a057e2d372a50`.
Its archive directory was checked without restoring it or creating a test
database. Exact batch, image and date-correction preimages are beside it.
The first transaction failed an editor-account foreign-key check and rolled
back completely; all successful import batches and the three later corrections
have separate receipts. No existing records, real assets or backups were removed.

Evidence entry points:

- [Pinned selection](latest-selection.json), SHA-256
  `c900c5c08e50da7f99f64d5aef3aba2fb5df04b9fee2a3083791ea554d6380ed`.
- [Identity preflight](preflights/c900c5c08e50da7f99f64d5aef3aba2fb5df04b9fee2a3083791ea554d6380ed.json).
- [Import manifest](applied/selection-c900c5c08e50da7f99f64d5aef3aba2fb5df04b9fee2a3083791ea554d6380ed.json).
- [Backup receipt](backup.json), [final verification](verification-135008.json),
  [image contact order](image-contact-order.json).
- Workflow: `ops/byzantine-russian-expansion.py`; regression checks:
  `ops/test_byzantine_russian_expansion.py`.
