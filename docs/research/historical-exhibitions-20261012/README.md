# Historical exhibitions, 1600–1989

## Authorized scope

The user replaced the recent 700-exhibition direction with historical exhibitions
from 1600 through 1989. Keep paintings, drawings, prints and icons. Main-catalogue
deletion was explicitly limited to recent selected museum additions, not the
entire photography/sculpture corpus. Delete existing Cloud SQL backups only.
The real local catalogue remains read-only.

## Latest verified state

Production has **10,406 active exhibition records**, including **10,220 confirmed-held
records** and **35 undated records**. This historical campaign has documented
**2,891 additions** in its tracked deliveries. The earlier London release started from
10,330 active records and added 25; 50 other active records appeared since this
log's previous 10,280 snapshot and are not attributed to this release.
Uncertain records do not count as confirmed-held progress toward 100,000.
The totals are catalogue records, not a claim that every checklist is complete
or that all events have confirmed dates. Worldwide coverage remains unfinished.

The Byzantine continuation adds two illustrated painted manuscript leaves and
connects them to 13 existing entries across nine historical exhibitions. It also
removes one truncated tour record after establishing that the full event ran
through 1990. Three further entries connect the existing Whistler painting to
London 1872, Paris 1883 and Cleveland 1933. Earlier phase counts remain receipts
for their respective deliveries.

### Philadelphia Museum archival dates: 18 exhibitions

Selected review of the first 100 source folders delivered **18 dated painting,
drawing and print exhibitions**, 1923–1936. All 18 public API detail responses
and stored dates were verified. This delivery adds no artwork entries, images
or artist claims: checklists remain unknown. No main-catalogue or real-local
writes occurred. The existing Cleveland *Modern Drawings* event in 1935 is
separate from the Philadelphia 1934 exhibition.

Dates come from explicit exhibition date pairs in the archive descriptions,
not trailing correspondence/folder dates. Excluded media, proposals, duplicate
folders, mixed collections and compound event descriptions remain outside this
selection. Museum object histories provide 15 candidate connections for four
shows, saved in `wave1-object-history-leads.json.gz`; these have not been linked.
The Piranesi-only histories in particular need reconciliation against the
combined Rosenwald Piranesi/Blake/van Leyden exhibition.

Procedure: `ops/historical_exhibitions_pma_archive_20261012.py`;
receipt: [pma-archive-wave1-delivery.json](pma-archive-wave1-delivery.json).

### William Blake 1939: original catalogue recovered

The museum's open [Internet Archive catalogue](https://archive.org/details/williamblakedesc00phil)
is now preserved as an 11.6 MB PDF with its OCR and source receipts under
`blake-philadelphia-1939`. Initial OCR segmentation identifies 278 distinct
catalogue numbers out of the sequence through 283; 11, 41, 87, 118 and 182 need
manual recovery. These are candidate catalogue entries, not imported artworks
or a completed checklist. Bound books, letters, ephemera and multi-plate sets
require separate scope and object-identity review.

Three original pages were rendered and visually inspected: PDF 123/printed 97,
PDF 150/printed 124, and PDF 172/printed 146. They confirm no. 148 *Job and His
Three Daughters* (Rosenwald), no. 173 *Great Red Dragon and the Woman Clothed
with the Sun* (Newton), and no. 204 *Day of Judgment* (Rosenwald). No. 174 is a
**different Brooklyn version** of the Dragon composition. No. 175 begins on
printed page 124, with its continuation still to inspect. Four NGA object
histories supply matching catalogue references for 148, 173, 175 and 204.
No production links or images were added in this research pass.

The Blake continuation now delivers **four illustrated exact-work links** to the
[1939 exhibition](https://artlines.org/exhibitions/5c64ef50-18f0-5cf3-8a19-e86adf45c299):
NGA objects 30221/no. 148, 11502/no. 173, 11499/no. 175 and 11525/no. 204.
An original-catalogue publication reference and captured source were added.
All four API links and internal image assets were verified; main artwork records
and event dates are unchanged. No new images were created. Checklist is partial.
Receipt: [blake-1939-links.json](blake-1939-links.json); procedure:
`ops/historical_exhibitions_blake_1939_20261012.py`.

Visual continuation recovered headings 11 (PDF 35), 41 (52), 87 (78) and 118
(104). These bring identified candidate headings to 282, but are not automatically
eligible artwork entries. No. 118 is a published book engraved by Schiavonetti
**after** Blake. PDF 153/printed 127 confirms the Rosenwald lender for no. 175.
PDF pages 154–159 run from entry 181 through four illustrations to entry 183;
no heading 182 was found in the inspected sequence, and none was invented.
The remaining checklist still requires medium, copy and component review.

The next Blake checklist wave adds **24 catalogued paintings/drawings** from
numbers 151–176, excluding the already linked 173 and 175. There are now **28
entries**, including the existing four illustrated exact-work matches. All 28
API entries were verified. The added records preserve distinct same-title
versions, historical creator/medium/lender labels and explicitly stated dates
where reviewed; no current holding or canonical artwork match is invented.
No main artwork, artist or image records were created. Review used original
catalogue OCR and the earlier selected visual checks, not visual review of every
new entry. Bound books, letters and multi-work sets remain outside this batch.
Receipt: [blake-checklist-wave1.json](blake-checklist-wave1.json); procedure:
`ops/historical_exhibitions_blake_checklist_20261012.py`. The full eligible
checklist and the 24 new entries' object/image matches remain outstanding.

### Spanish painting 1937: four illustrated object connections

The Philadelphia *Masters of Spanish Painting* exhibition now has four
exact existing-work entries: *The Veil of Saint Veronica* from the Goulandris
Foundation and NGA's *The Marriage at Cana*, *Christ among the Doctors* and
*Victor Guye*. The Goulandris work matches its exact native museum URL and ID,
51 × 66 cm dimensions and historical exhibition reference. NGA objects match
native IDs, accessions and institution; their shorter *Spanish Paintings*
history names the same museum and 1937 year. No catalogue numbers were invented.

All four API artwork links and existing internal image assets were verified.
Source creator labels are retained; no canonical artist links were invented for
unlinked creators. The exhibition checklist changes from unknown to partial;
dates and main artwork records remain unchanged. No new images or real-local
writes occurred. Procedure: `ops/historical_exhibitions_spanish_1937_20261012.py`;
receipt: [spanish-1937-links.json](spanish-1937-links.json).

### Toulouse-Lautrec 1955–1956 tour: 21 illustrated connections

The [existing Toulouse-Lautrec tour](https://artlines.org/exhibitions/bc23eb3d-e9d3-5e56-a188-4f631a5f0f6e)
now has **22 entries**, retaining its previous Cleveland *Laundress* link and
adding **21 exact NGA object connections**, all with verified internal images.
The new entries attach specifically to the Philadelphia occurrence in 1955;
Chicago 1956 participation is not inferred for other objects. Native object IDs,
accessions and source catalogue numbers distinguish paintings and print states.
One source print attributed *after* Toulouse-Lautrec (NGA native 33958) remains
unmatched. The artist/printer/publisher labels on *Miss Loïe Fuller* are preserved.

All 21 new API artwork links and all 21 public image assets were checked. The
existing tour record, both dated occurrences, prior entry and all main artwork
records are unchanged. One named artist connection was added. No new events,
artworks or image files were created; the real local database remains untouched.
The checklist is still partial. Procedure:
`ops/historical_exhibitions_toulouse_1955_20261012.py`; receipt:
[toulouse-1955-delivery.json](toulouse-1955-delivery.json).

### Philadelphia archive second wave: six exhibitions, 1937–1954

Review of folders 101–180 adds six dated exhibitions: *Masters of Spanish
Painting*, Benjamin West, William Blake, *Paintings of Asiatic Costumes*,
*Popular Favorites: Paintings Selected from the Permanent Collection*, and
Van Gogh. All six API details and stored dates were verified. This wave adds
no entries, artists or images; original checklists remain outstanding.

The initially planned Toulouse-Lautrec 1955 event was excluded before writing:
production already contains its Philadelphia occurrence, **29 October–11
December 1955**, plus Chicago **2 January–15 February 1956**, under existing
event `bc23eb3d-e9d3-5e56-a188-4f631a5f0f6e`. No duplicate was created.
`wave2-plan.json` is an unexecuted research artifact; `wave2-plan-v2.json` is the
six-event delivered plan. The 1953 Homer–Eakins–Cassatt date conflict, inverted
1937 Constitution dates and the mixed circulating Russian Arts show remain held.

A captured Goulandris museum object page independently identifies El Greco's
*La Santa Faz* in Philadelphia's 1937 Spanish painting show; object matching is
pending. PAFA's special-exhibition guide was captured as a further source lead,
but its retrieved page does not expose the advertised decade links. Neither
lead is counted as a delivered artwork or exhibition. Procedure:
`ops/historical_exhibitions_pma_archive_wave2_20261012.py`; receipt:
[pma-archive-wave2-delivery.json](pma-archive-wave2-delivery.json).

### Philadelphia object links: Pascin and Gauguin

Two of the 15 candidate histories are now linked to existing catalogue works:
Jules Pascin's *Enlèvement d'Europe (Rape of Europa)*, NGA 2015.19.2616,
Speiser exhibition 1934 no. 50; and Paul Gauguin's *Parau na te Varua ino
(Words of the Devil)*, NGA 1972.9.12, Post-Impressionists exhibition 1935,
recorded historically as *At the Edge of the Forest*. Both native IDs and
accessions match existing objects. The Pascin work remains classified as a
drawing despite the exhibition's painting title; no medium was overwritten.

Both entries and their artist connections are delivered. Gauguin's existing
internal image was verified by HTTP 200 and image content type; Pascin remains
unillustrated. The two events now have partial checklists; dates and all other
metadata were preserved. No main artwork, image or real-local writes occurred.
Twelve Piranesi histories and Vlaminck's *The River* remain unlinked while the
exhibition title variants are reconciled. Procedure:
`ops/historical_exhibitions_pma_links_20261012.py`; receipt:
[pma-object-links-wave1.json](pma-object-links-wave1.json).

### Philadelphia Art Alliance 1930: 190 artwork connections

The [1930 Art Alliance exhibition](https://artlines.org/exhibitions/67f416ec-55c8-5253-8fbb-a58d79c75ef0)
now connects **190 existing works** (186 prints and four drawings), with **180
internal images**. NGA histories identify 193 distinct objects; three unmatched
objects remain held. Native IDs, accessions and institutions preserve exact
impression identity. Studio/joint/after-model labels remain on entries; five
qualified primary-link cases are held from additional named-participant claims.
One verified Rembrandt participant and one catalogue reference were added.

[BnF FRBNF45409188](https://catalogue.bnf.fr/ark:/12148/cb45409188j) confirms
the venue address, 1930 year and six unnumbered catalogue pages. Full contents
remain unread. An archival October folder date was not made an opening date.
The Pennsylvania Museum 1930 display remains a separate lead pending tour or
co-host reconciliation; no second Philadelphia event was imported.

All 190 API links were checked across two pages, plus two reverse-link checks.
All 180 distinct public image assets returned HTTP 200 with image content types
after a transient DNS failure interrupted the first asset pass. Ten works lack
images. No main artwork, artist, image or real-local database writes occurred.
Procedure: `ops/historical_exhibitions_rembrandt_art_alliance_1930_20261012.py`;
receipt: [rembrandt-art-alliance-1930-delivery.json](rembrandt-art-alliance-1930-delivery.json).

The captured [Philadelphia Museum Director's Exhibition records](https://findingaids.library.upenn.edu/records/PMA_PMA.EXH)
also yield **871 archive-folder leads**, including 22 proposed/cancelled markers.
These are not event counts: multiple folders can cover one show, folder dates
can describe correspondence, and excluded media are present. Source IDs and
folder titles are saved in `philadelphia-museum-archive/finding-aid-discovery.json.gz`.
No exhibitions were imported from this discovery list.

### Philadelphia 1931: 390 illustrated Whistler connections

The [Free Library of Philadelphia exhibition](https://artlines.org/exhibitions/1201d917-3dab-5f87-9984-dcb672e2fe4a)
is now a distinct historical review event with **390 illustrated existing
artworks: 379 prints and 11 drawings**. These are individual impressions and
objects, not plate-title deduplications. Of 402 selected museum history rows,
one native-object reference is repeated; 401 distinct native objects are
represented. Eleven lack an existing native-ID or accession match and remain
held. No autograph letters, photographs, sculpture or placeholder artworks were
added. No main artwork, artist or image file was created or changed.

The two participant connections preserve present source attributions: James
Abbott McNeill Whistler and Beatrix Godwin Whistler. Two impressions of *Count
Robert de Montesquiou* are attributed to Beatrix after James; they are not
reassigned to James because the exhibition used his name. An unmatched drawing
attributed to a follower remains unresolved. All creation intervals, media,
accessions, primary images and review/publication states remain intact.

The library's [bibliographic record](https://catalog.freelibrary.org/Record/150798)
identifies a 1931 exhibition catalogue of 14 pages (OCLC 8881811). It is added
as a publication reference, not as a digitized or fully read checklist. The
public search reader exposed that metadata before the direct library request
returned HTTP 403. The hold is recorded; no retry or bypass followed. The NGA's
independently published object histories supply the participation evidence.
Exact opening/closing dates and catalogue numbers remain unknown. Nearby
1932–1934 Whistler exhibitions at Cleveland, Chicago and MoMA remain distinct.

All 390 artwork links and image presence passed API checks across four pages,
including two reverse connections and the public detail page. All **390 distinct
image assets also returned HTTP 200 with image content types** from Artline's
own asset route. The held accession lookup used
`artworks_institution_accession_idx` and found no additional existing matches.
See `whistler-philadelphia-1931-delivery.json` and
`ops/historical_exhibitions_whistler_philadelphia_20261012.py`; full evidence is
under `whistler-philadelphia-1931` in the Application Support research directory.

The same comparison found one remaining textile-only legacy event, *Cotton
Prints Assembled by the Cotton Textile Institute, Manhattan, Kansas*, Cleveland
1932. The exact museum source identifies the textile institute; both its public
artwork array and Artline artwork entries are empty. That event and its source,
venue and organizer rows were removed, with preimages retained locally. No main
artworks were deleted. This offsets the new Philadelphia event in the active
total, while historical campaign additions remain 2,666. See
`cotton-prints-scope-correction.json`.

The [Carnegie 1933 Rosenwald exhibition](https://artlines.org/exhibitions/2ce93325-c5a5-5544-961f-51f8343fd984)
is now delivered with **201 exact existing print connections**, **177 working
images**, **94 canonical artist connections** and three contemporary publication
references. There are 24 remaining image gaps and 39 unmatched native objects.
No new main artworks, artists or image files are counted. Original date evidence is
the [11 April Carnegie Tartan](https://iiif.library.cmu.edu/file/TAR_1933_027_024_04111933/TAR_1933_027_024_04111933.pdf),
page 1, reports an opening on 6 April and closing on 21 May 1933. Faculty
bulletins of 19 April and 17 May independently repeat the closing date. All
three pages were rendered and visually inspected; the May bulletin's OCR
misread 1933 as 1923. The newspaper describes roughly 240 prints spanning the
fifteenth through twentieth centuries and several printmaking processes.
NGA histories identify 240 native objects, including print series sharing a
catalogue number. This is not proof of a complete 240-number checklist.
The 201 linked objects span 177 catalogue labels. Shared numbers retain separate
sheet identities: Solis's seven Liberal Arts engravings and 23 decorated initials
by Lützelburger after Holbein are series, not duplicate works. Printmakers remain
distinct from the artists whose designs they reproduce. Two unmatched, undated
objects have source numeric bounds matching their artists' lifetimes; those
bounds are not used to invent creation dates or force new object matches.
All 201 links passed three API pages and reverse-link samples; all 177 distinct
image assets returned HTTP 200 with image content types. Main artwork records
remain unchanged. Evidence is in `carnegie-1933`, with the phase receipt at
`carnegie-1933-delivery.json` and delivery code in
`ops/historical_exhibitions_carnegie_1933_20261012.py`. Engineering open-house
events elsewhere in these newspapers are not automatically art exhibitions.

### National Gallery object histories: 132 events and 3,238 connections

The NGA's independently published [open dataset](https://github.com/NationalGalleryOfArt/opendata)
includes 67,656 object exhibition/lifetime-history rows. The pinned
`objects_text_entries.csv` contains 227,528 rows across all text categories;
bibliography rows are not counted as exhibitions. This continuation reviews
217 title groups that explicitly name the NGA venue and an event year. It adds
**132 historical review exhibitions**, enriches **13 existing identities**, and
adds **3,238 exact artwork connections across 145 exhibitions**. The new events
start in 1943–1988; explicitly documented longer periods and tours are retained.

The connections cover **2,435 existing artworks**: 1,727 print connections,
1,014 painting connections and 497 drawing connections. **2,879 connections
are illustrated**, representing 2,116 distinct works with existing primary
images. The remaining **359 connections, covering 319 works**, still need
pictures. There are **1,108 artist connections across 520 existing artists**.
This phase creates no main-catalogue artworks, artists or image files and changes
none of the 2,435 main artwork records. Object accession, native ID, institution,
creation interval, medium and view identity were checked before attachment.

Examples are [Callot, 1975](https://artlines.org/exhibitions/15b408c0-da36-5a6b-8304-5bd3a4f1994f)
(190 works, 186 illustrated), [Rembrandt, 1969](https://artlines.org/exhibitions/b695e474-93fe-5805-990d-c775dbeda7d6)
(111, 107 illustrated), [Mary Cassatt, 1963](https://artlines.org/exhibitions/fd2da10a-742b-5ca5-babc-655a53ebae6b)
(31, all illustrated), and the [Chester Dale Bequest, 1965](https://artlines.org/exhibitions/ebb20a32-f1cf-51ea-b912-c3178e021c4e)
(225, 165 illustrated). The existing Daumier 1979 event gains 79 illustrated
works; William Blake 1957 gains 29. Every reconstruction remains partial.

Source spelling and subtitle variants are reconciled instead of counted as
separate events. The two existing Dürer 1971 identities, a possible 1953–1954
display continuation, long collection displays, permanent loans, supplementary
installations and unresolved title errors remain held. Three verso records are
excluded from recto-only participation claims; five works retain limited-duration
display notes. “Not in the catalogue” is preserved and is not misread as “not
exhibited.” **511 selected histories lack a unique existing native-object match**
and remain reconciliation leads. Range-only and other-venue histories are still
largely outstanding; this is not all NGA historical coverage.

There are 138 new occurrences, including six additional tour venues. Italian
Renaissance Prints spans 1973–1974, Titian's Venetian Woodcut exhibition spans
1976–1977, and Watteau spans 1984–1985. Connections from NGA-only histories remain
attached to that occurrence; no work is assumed to have reached every touring
stop. Seventeen new events have explicit ending years; 115 retain an unknown
closing year. Exact days are not manufactured from years. Existing event dates
and child records remain intact. Dallas and Iowa historical venue labels are
linked to the existing institutions using their official history/publication
evidence; original labels and unknown stop dates are retained.

All 3,238 new links and their image availability passed public API checks,
including keyset pagination for the larger exhibitions and two reverse-link
samples. The measured 101-row scoped query uses
`exhibition_entries_exhibition_idx` and takes 0.503 ms; it is not a future-scale
load test. At this verification, 1,546 active exhibitions have entries, 413 have
at least ten, 173 have at least fifty and 57 have at least one hundred. Entry
counts do not establish complete checklists: no active exhibition currently
carries a `complete` checklist state. The 100,000-event and 500–1,000 fully
covered-checklist goals remain unfinished.

See `nga-histories-delivery.json` and
`ops/historical_exhibitions_nga_histories_20261012.py`. Full immutable source
captures, reviews, plan, preimages and verification live under the
`nga-object-histories` evidence directory in Application Support. NGA main-site
and image access holds remain in force; the GitHub metadata route is a separate
official publication and supplies no image licence.

The next 100 other-venue title groups are staged in
`other-venue-next-cohort.json.gz`, with native-object matches and potential
existing-event duplicates. They are discovery leads, not imported events.
The largest, the Free Library of Philadelphia's 1931 Whistler exhibition,
has subsequently been delivered as documented above; the original catalogue
contents remain unread. Other strong leads include Rosenwald prints at Carnegie in
1933, Rembrandt exhibitions in Philadelphia and Washington, and the Chicago
1941 printmaking exhibition. No approximate-title match is automatically merged.

### Art Institute archive: 819 additional historical events

The pinned official archive also contains **6,259 exhibition records**. Of these,
4,065 have source date intervals within 1883–1989. Title/media screening, date
audits and comparisons against existing exhibitions support **819 new review
events**, spanning 1885–1970. One existing event receives an additional venue:
Seurat's 1958 Chicago exhibition and the later MoMA presentation are one tour.
The Chicago stop is added to the existing identity, with the overall start moved
to 16 January 1958; MoMA's source occurrence and its intermittent-date note remain
preserved. Cézanne's 1952 Chicago–Metropolitan Museum tour is likewise one event,
with two documented occurrences and an overall end of 18 May.

**121 exact artwork connections** across 22 exhibitions link **114 existing
works**. **74 connections are illustrated** using existing catalogue images;
47 connections, representing 45 distinct works, still need pictures. There are
**55 new canonical artist connections**: 54 new participant rows and one
reconciled existing Seurat label. Its original “Georges-Pierre Seurat” wording,
role and MoMA source remain intact; a redundant row from this batch was removed.
No new main-catalogue artworks, artists, images or publications are counted here.
Original document IDs remain evidence leads, not automatically typed catalogues.

Examples now include [Monet, 1957](https://artlines.org/exhibitions/c23f3e96-cef8-5c58-8dd4-b595b5896188)
(25 exact works), [Cézanne, 1952](https://artlines.org/exhibitions/acd3f895-d9d9-56ec-8f02-c7d7c431c251)
(nine), [Homer, 1944](https://artlines.org/exhibitions/bf148759-3864-5919-8048-dcdc60769395)
(20), and [Margaret Day Blake's drawing gifts, 1970](https://artlines.org/exhibitions/e425c88b-a9f9-551d-8fe2-782f74850c41)
(26). These are partial object-history reconstructions, not complete checklists.
The other 798 new events still have no imported artwork entries from this phase.

Known conflicts remain explicit. Five new events with conflicting exact date
reports retain supported years and withhold disputed day fields. Cézanne's
isolated April/March conflict is preserved alongside the event index and eight
consistent histories. A Davies work dated 1915 is not linked to a 1911 show;
Monet's *Stacks of Wheat* history says “Possibly” and remains unlinked. A Deering
collection article and earlier exhibition references are not mistaken for the
October 1928 event. Photography, miniature rooms, a sculptural Ferrucci portrait,
unclear student/design shows, unusually long date ranges and unresolved duplicate
or tour records are held. Post-1970 historical exhibitions still require eligible
object-content review; they are not rejected merely because their show date is
later than the artwork cutoff.

The remaining 201 candidates from the narrower pictorial pass and 46 native
objects without a unique existing-catalogue match are retained for further work.
WikiArt title-list and page research found no secure new image matches in this
phase: Sargent's similarly named olive-tree and Carrara works differ in dimensions
or medium, and Severini's drawing must not receive an image of a painting or later
replica. Museum image/publication access holds remain respected.

Every new artwork entry and its available image was checked through the public
API; reverse artwork-to-exhibition samples also passed. All 114 main artwork
records remain unchanged. The scoped 26-entry drawing-show query used
`exhibition_entries_exhibition_idx` and took 0.075 ms in the measured sample;
this is not a future-scale load test. Full plans and review decisions live in the
`aic-exhibitions` evidence directory under Application Support. See
`aic-archive-delivery.json` for the final phase receipt and the two
`ops/historical_exhibitions_aic_*20261012.py` scripts for preparation/delivery.

### Chicago 1933: original catalogue and exact object histories

The existing **Century of Progress: Exhibition of Paintings and Sculpture**
record now has **221 linked artworks, 152 illustrated**. This continuation adds
**220 artwork entries, 108 canonical artist connections, one catalogue reference
and five primary images**. It creates no exhibition, artist or artwork records.
The five new pictures come from independently matched WikiArt pages for Bellows's
*Love of Winter*, El Greco's *Assumption*, Twachtman's *Icebound*, Picasso's
*Old Guitarist* and Glackens's *At Mouquin's*. All five derivatives were visually
reviewed, uploaded and verified by public checksum. Original catalogue metadata,
artist links and review states remain unchanged, including El Greco's unresolved
creation-date fields. Source date, support and dimension differences stay in the
image evidence.

The pinned official Art Institute metadata archive contains 139,747 object
records. A bounded historical selection found 408 records mentioning a Century
of Progress exhibition and 370 with a 1933 reference. Exact native IDs and
accessions resolved 222 existing catalogue works. Two connections were held:
the museum history places Benton's 1945 *Cotton Pickers* in 1933, and Henri's
*Himself* is only discussed beside *Herself* in the original catalogue. Of the
other source candidates, 134 need further internal-catalogue reconciliation and
14 concern excluded media or a different World's Fair exhibition.

The independent University of Illinois library scan on Internet Archive is the
**third edition, fifth printing** of the 1933 catalogue, edited by Daniel Catton
Rich. Its title page gives 1 June–1 November 1933. These agree with the existing
event dates; varying May/October dates in some museum object histories are
preserved as conflicting evidence. The 1934 exhibition and its different numbers
remain separate. Paintings occupy printed pages 1–85; drawings, watercolours and
pastels occupy 86–105. Sculpture starts at no. 1095 on page 106 and is excluded.

Visual inspection corrects the museum's catalogue references for Goya's shooting
scene (**166e**, not repeated 166d), Homer's *Tynemouth Priory* (**907**, not 901)
and Matisse's *Girl with a Cat* (**1032**, not 1033). The scan supplies missing
numbers for *The Herring Net* (460), *The Storm* (467) and Whistler's studio
painting (488). Historical titles and attributions remain separate from modern
object labels. The six Goya panels remain distinct objects.

**The full checklist is not complete.** Two-column OCR produced 1,084 draft
candidates, covering 1,063 base numbers with 31 sequence gaps; lettered groups,
split creator headings and historical attributions still need review. None of
these OCR drafts was automatically imported. The 220 new entries instead use
explicit museum object histories and the individually reviewed corrections.
Sixty-nine linked works still need images. Both the museum publications host and
its image route returned HTTP 403 and are held; no alternative museum route was
attempted. The five delivered images use the independently approved WikiArt source.

Every new entry ID, catalogue number and participation value was checked through
the paginated public API; reverse artwork links were sampled. The scoped entry
query uses `exhibition_entries_exhibition_idx` and took 0.403 ms in the recorded
production plan. This is evidence for the bounded lookup, not a ten-million-row
load test. No real local database writes occurred. See
[`chicago-1933-delivery.json`](chicago-1933-delivery.json),
[the original catalogue](https://archive.org/details/catalogueofcentu00arti) and
[the live exhibition](https://artlines.org/exhibitions/2cd58f72-a7e7-5e46-8018-5b208f0c70e4).

Raw captures, OCR drafts, pinned plans, originals, review sheets and receipts:
`~/Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/chicago-1933/`.
Preimages remain in the approved Artline backups directory. Procedures:
`ops/historical_exhibition_chicago_{1933,aic,images,wikiart}_20261012.py`.

## Production cleanup completed

| Action | Verified result |
| --- | ---: |
| Known out-of-range exhibition records deleted, including follow-ups | 100,893 |
| Clearly excluded-medium exhibitions deleted, including undated and Cotton Prints follow-ups | 625 |
| Empty duplicate/sample exhibition records removed in follow-up | 4 |
| Excluded entries removed from retained mixed exhibitions | 7,701 |
| Additional entries removed with excluded-medium events | 710 |
| Recent museum photographs deleted from main catalogue | 312 |
| Source-confirmed modern sculptures deleted from main catalogue | 234 |
| Older/uncertain selected sculpture candidates preserved | 280 |
| Existing Cloud SQL backups deleted | 170 |
| Active Cloud SQL backups remaining after verification | 0 |

Both catalogue deletion passes used pinned plans and atomic transactions. A
missing self-referencing FK index initially caused the main-catalogue transaction
to time out and roll back. Supporting migrations 0050 and 0051 were applied before
successful retries; audit and catalogue-invalidation triggers stayed enabled.
No artist became an orphan within the selected deletion plan. Unrelated artists,
media, local backups, exports and original research assets were preserved.
Automatic backup settings were not changed.

### Undated-source follow-up

All **154** originally undated records were checked against **164 source rows**;
all original hashes matched 46 retained raw captures. Missing parsed dates did
not mean the sources lacked event years. The review removes **97** further
out-of-range events: 75 Art Platform Japan, 18 Artsy and four Cleveland records.
The decisions use event-period fields, excluding artwork dates, artist lifespans,
publication years and retrieval timestamps. Invalid days, reversed dates and
multiple periods remain in the evidence.

Four additional exhibitions explicitly concern photographs, porcelain or glass.
Two Cleveland records are explicitly labelled duplicates; two other empty records
are titled `sample exhibition` and `x`. They have no dates, venue, organizer or
artworks. These 105 removals also remove 78 exhibition
entries, 1,617 participant relationships, 93 venue occurrences, three publication
links and 106 source rows. Their complete preimages and original research remain
in the approved local archive. No main-catalogue artwork, artist or image was
deleted by this follow-up.

**15 existing Japanese exhibitions** now have explicit historical years recovered
from their source period. No missing day was filled in, and original source
payloads, review status, event state and artwork participation remain unchanged.
The 1982 Arakawa source has a reversed range; its closing year remains unresolved.
The 1955 Oguiss source describes two display periods, not one continuous interval.
The Takayama retrospective belongs in 1987; the 1917–1982 years in its title are
not used as event dates.

**34 undated records remain unchanged.** These include conflicting Cleveland
dates, incompletely dated tours, unknown exhibitions and unresolved physical
media. An exhibition naming sculptors is not automatically treated as an
exclusively sculpture checklist. The five-stop Japanese-art tour has one dated
1958 stop; that does not establish the full tour's opening or closing date.

Evidence: `undated-legacy/reviewed-plan.json`, `delivered.json`, `verified.json`
and `public-verification.json`. All retained entries and original source payloads
were verified unchanged; six removed API samples return 404 and all 15 recovered
years were checked through the public API. The repository summary is
[`undated-review-summary.json`](undated-review-summary.json).

The 2020–2025 gallery deployment was cancelled before Cloud Run release. Its
research objects were never imported. The 9,193 files uploaded by the interrupted
image job were removed from the current production object prefix, with generation
checks and batch metadata verification. Its local original images remain intact.
The retired uploader/importer now refuses to run.

## Historical additions committed

**1,547 new review exhibition records:** 221 Royal Academy annual exhibitions
(1769–1989) and 1,326 selected events from the Musée d’Orsay historical index
(1673–1961). Each has a source identity, captured evidence and historical venue/date
labels. No artwork creation years or opening days were invented.

At the first post-import audit, production contained **9,119 active exhibitions**:
8,965 dated within 1600–1989 and 154 undated records retained for research. There
were zero known out-of-range records. These totals describe event records, not
complete artwork checklists or exhaustive worldwide coverage.

The Orsay PDF has 2,800 data rows. Preparation held 1,464 rows for media, dates,
event identity or insufficient scope evidence, excluded two exact duplicate rows,
and held eight further rows with PDF column-overflow problems. The remaining
1,326 rows had no exact title/year match in the existing archive. A supplement is
not counted as a separate event. Source-country conflicts and uncertain dates are
preserved in the held queue.

Each Royal Academy year was checked against its own page and linked IIIF
catalogue. IIIF `navDate` values are navigation metadata, not opening dates.
The institutional link identifies the Royal Academy as organizer; it does not
assign every year to the current building or imply ownership of displayed works.

### Berlin Academy continuation

The Academy's own [32-page catalogue index](https://adk.de/files/archiv/PDFs/Preussische_Ausstellungskataloge_Uebersicht_nach_Reihen.pdf)
supports **163 further historical review events, 1786–1943**, now committed and
verified. This brings this historical campaign to **1,710 new events** and the
active production archive to **9,282 events**: 9,128 dated within scope and 154
undated legacy records. There are zero known out-of-range active events.

All 218 index rows have a recorded decision: 163 new events, five additional
publications for the same events, five excluded photography/sculpture/ceramic
exhibitions, 16 non-event chronicle volumes and 29 held rows. The holds include
the probable existing 1883 *Salon de Berlin*, architecture with unresolved
physical media, uncertain special-exhibition scope and a possible section of
the 1926 show. Large-format and revised catalogue editions are not new events.
The [German Historical Museum's 1893 chronology](https://www.dhm.de/lemo/jahreschronik/1893)
also explicitly distinguishes the *Freie* counter-exhibition already in the
archive from the newly added *Große Berliner Kunstausstellung*.

The delivery includes **168 source rows, 183 publication references, 165 venue
occurrences and 18 named artist connections**; 16 connections resolve to existing
artists. Paul Meyerheim and Josef Scheurenberg remain source labels. No artist
record was invented. Posthumous exhibitions are valid and do not require a
painter to have been alive during the event.

The 1917 Great Berlin exhibition is correctly located in Düsseldorf. The 1918
city remains unknown in this source. The 1929 Leibl tour is one exhibition with
three documented stops; exact stop dates remain unresolved. An organizer's name
does not assign an unknown venue to a current museum building. Cross-year
closing dates are preserved for the 1897 Böcklin, 1908 Chinese painting and 1940
Great Berlin exhibitions. Catalogue titles, source spellings and original date
labels remain in evidence, including the apparent `1941` URL label for the
index's 1908 English-art large-format catalogue.

These are event and bibliography records: **no new artwork checklist entries or
images** were added in this Berlin batch. Full catalogue retrieval and exact
object matching remain outstanding. All text rows were reviewed; PDF pages 1,
13, 16, 22, 26 and 28 were also inspected as rendered images. The source guide is
accessible, but the Heidelberg digitized viewer returned an Anubis access denial
and remains held without bypass. Independent Academy index retrieval succeeded.

Evidence lives under `berlin-academy/` in the source archive. The immutable
`import-plan-v2.json` corrects venue preparation before the sole production
transaction; the earlier plan was never applied. `delivered.json`,
`verified.json` and `live-page-verified.json` record the successful delivery,
database checks, six public API detail samples and rendered live HTML. No new
application deployment, main-catalogue write or real local DB write was needed.
`all-record-fields-verified.json` checks every imported event's title, dates,
series and status against the plan, plus all 168 source hashes and parent links.

### Cleveland historical exhibition images

**234 primary images are delivered and verified on existing catalogue works:**
187 paintings and 47 prints. They illustrate **506 existing artwork connections
across 88 historical exhibitions**, without adding events, artworks or new
participation claims. The [1987–1988 Japanese-screen exhibition](https://artlines.org/exhibitions/09a6130d-8301-5078-8983-08e6c3d0e6d5)
is one live example. Exhibition navigation and image paths remain internal.

The frozen audit found 1,275 linked works lacking images. Metadata was retrieved
for all 1,256 selected by medium and creation date; the other 19 were outside
that discovery selection. Exact native identifiers, inventory numbers, titles,
media, source ownership and source dates were checked before image selection.
Only 249 had an available primary image with explicit, unconflicted per-object
CC0 evidence. The other 998 lacked that image evidence and nine lacked a primary
image. These gaps remain open to further exact-source research, including the
approved WikiArt workflow; metadata access alone does not establish image terms.

All 243 initially prepared images were visually reviewed across 22 sheets.
Fourteen primary views were held: 11 closed covers and three calligraphy-only
leaves. Six further files initially failed the API dimension comparison.
Individual review recovered five exact pictorial files using measured dimensions
and pinned original-file hashes; the sixth depicts another calligraphy-only page.
The five recovered derivatives were also reviewed. Final disposition is **234
delivered and 15 held**, leaving 1,041 gaps in the original scope. Source dimension
values, initial hold receipts and their resolutions are retained.

Long scrolls preserve their full compositions, inscriptions and mountings.
Complete screen pairs, individual panels and separate leaves remain distinct
objects; no duplicate artwork was created to add an image. A museum primary view
showing one leaf or print from a group is labelled representative. No generated
picture, closed book cover or unrelated version fills a gap.

Four production transactions delivered 94, 91, 44 and five images. Every public
file's hash was verified at upload; a final database audit checks all 234 media,
source records, rights evidence, catalogue fields and creator attributions.
Seven exhibition API samples verified 190 newly illustrated connections; two
live HTML pages rendered the images with internal links, and four canonical
artwork reverse-link samples passed. No application deployment or real local
database write was needed.

Evidence is under `cleveland-image-gaps/`; the repository summary is
[`cleveland-image-delivery.json`](cleveland-image-delivery.json).
`delivery-audit-v2.json` also clarifies the unchanged exhibition totals: 9,128
records have an in-scope start year, comprising 7,820 explicit start/end intervals
and 1,308 without a separate end year. Another 154 legacy records are undated.
No closing date was invented; there are zero known out-of-range active events.

### Paris Academy minutes, 1664–1671

The [original minutes, volume I](https://archive.org/details/procsverbauxde01acaduoft),
published by Anatole de Montaiglon in 1875, support **four new events**: the 1664
public display of prize paintings and the Academy exhibitions of 1667, 1669 and
1671. Nine rendered original pages were visually checked alongside the OCR.
The publication year is distinct from the historical meeting and exhibition years.

The [1664 exhibition](https://artlines.org/exhibitions/e7a539ea-7621-573e-abc3-ba78ab3ecffc)
has **eight painting entries**, identified by competition marks A–H. The minutes
explicitly distinguish them from the excluded bas-reliefs J and L. A and E won
the first and second prizes: *La Conqueste de la Toison d’or* by Meunier and
*La fable de Danaée* by Corneille. Six titles and creators remain unknown; their
labels explicitly identify them as unresolved documented paintings. Competition
marks have not been presented as printed catalogue numbers.

The Beaux-Arts de Paris authority biographies identify the two painters as
Pierre Monier and Jean-Baptiste Corneille. Corneille links to the existing
1649–1695 artist; Monier remains a named exhibition participant without a new
canonical artist record. Meeting signatories, lecturers and judges were not
silently imported as exhibitors. Louvre INV 2622 is a potential surviving Golden
Fleece painting, but its object history conflicts with the 1664 identification;
no exact artwork link or image was attached. The biography pages depict later
reception paintings and do not establish those pictures as 1664 exhibits.

The minutes confirm public display in 1667, a special display in April 1669,
and paintings around the Hôtel de Richelieu courtyard in March 1671. Exact
opening/closing days remain null. The 1671 continuation through the following
week is retained in the date label, without inventing a closing date. Raphael's
*Saint Michael*, discussed at a separate lecture, is not an exhibition entry.

This delivery includes four venue labels, six source records, six publication
references, two named participants and one canonical artist link. It adds no
main-catalogue artworks or images. All four records and all eight entries were
verified in production and through the public API; the live 1664 page renders.
See [`early-paris-delivery.json`](early-paris-delivery.json) and `early-paris/`
in the source archive. Coverage before 1664 and the intervening years remains open.

### Byzantine painted leaves delivered

Two anonymous Constantinopolitan painted leaves, **1057–1063**, are now new
review artworks: Cleveland **1942.1511**, *St. Luke*, and **1942.1512**,
*St. Matthew*. Their medium is tempera and gold on vellum, with ink also recorded
for Luke. They are classified as manuscript illuminations; no painter identity
or icon-panel format was invented. Museum holdings are supported independently
of current display. Both native museum CC0 images were inspected at source and
delivery sizes, kept full frame, uploaded and verified byte-for-byte publicly.

Their native object and event IDs resolve **13 existing exhibition entries
across nine shows**, 1949–1982. No new participation claim was inferred from an
illustration or generic subject. All 13 gallery entries and both reverse artwork
histories passed public API verification. The 1964 Athens participation is also
independently confirmed by [the original museum loan list](https://archive.org/details/cmapr1237),
whose single scan page was inspected. Its silver vase is excluded. The 1931
Paris reference concerns the Phanar Gospel with Mark and John; it is not used
to attach these two detached leaves. Conflicting 1957/1980 day labels remain
preserved for separate original-catalogue review.

See [`byzantine-painted-leaves-delivery.json`](byzantine-painted-leaves-delivery.json)
and `byzantine-historical/leaves/` in the source archive.

### Byzantine icon catalogue leads

A visually inspected scholarly study of the composite icon at Vlatadon Monastery
identifies five historical catalogue references: Athens 1964 no. 199, Athens
1985–1986 no. 83, Florence 1986 no. 36, London 1987 no. 21 and the 1988 American
tour no. 23. The 1964 event already exists and must not be duplicated. The
fourteenth-century insert and fifteenth-century surrounding panel have separate
dates; another Vlatadon composite icon must not be substituted.

The American *Holy Image, Holy Space* tour continued through **Richmond in April
1990**, beyond the current cutoff. The earlier library itinerary stopped at
Detroit; a later Cleveland press release and the Walters' retrospective object
history establish the longer tour. The previously stored Cleveland-only 1989
record has now been removed, together with four publications, one participant,
one venue and one source row. It contained no artwork entries. Its complete
preimage and sources remain archived; no main artwork or image was deleted.
The removed API detail returns 404. The original press-release page was inspected
visually; the VMFA chronology's direct endpoint returned a 202 challenge and is
held without bypass.

The public 1987 catalogue preview suggests an Athens–Florence–London European
tour, with additional British loans for London. Event/occurrence identity,
original checklist pages, the exact composite icon and a suitable image still
need reconciliation. The Vlatadon leads have **zero new records or images counted**.
See [`byzantine-exhibition-leads.json`](byzantine-exhibition-leads.json).

### Whistler's Mother: three historical connections

The existing 1871 painting now has exact exhibition entries for **Royal Academy
1872, no. 941**, **Paris Salon 1883, no. 2441**, and **Cleveland 1933**. The
University of Glasgow catalogue raisonné identifies it as YMSM 101 / RF 699;
Cleveland's retrospective history and two visually inspected original letters
confirm the Louvre loan in 1933. The drypoint with the same short title is a
different object. Paris is distinguished from the identically titled Nice Salon.
The 1892 Goupil photograph and uncertain 1887 Manchester appearance are excluded.

Three artist connections were added. The main painting's previously unknown
type and missing medium are now `painting` and `Oil on canvas`, supported by its
exact WikiArt page and scholarly record. Its date, holding, review status and
existing image remain unchanged. The WikiArt reproduction is cropped; a full
reproduction remains an explicit image gap, and no new image is counted here.
The 1933 advance letters announce November 29/30 closing dates, but the later
museum history records December 10 for the full show and December 7 for the
painting. Those distinct facts are preserved without rewriting event dates.
All three internal-image entries and reverse connections passed verification.

See [`whistler-mother-delivery.json`](whistler-mother-delivery.json). The wider
press archive search returned **737 files** matching the pre-1990 exhibition
query; the first 50 metadata rows are captured. Repeated publicity, lectures,
excluded media and forecast dates require review before any event counting.

### Further archive discovery

The Metropolitan Museum's 1870–2011 exhibition chronology is discoverable through
its library archive, but the direct PDF request returned 403 and remains held.
The MoMA 1941 collection-display page supplied an opening date through the public
web reader before its direct request also returned 403. No blocked request was
bypassed; the reversed CSV closing date remains unresolved. Both holds are recorded
for subsequent source work.

Exeter's official retirement notice links directly to its [preserved Salon
database](https://web.archive.org/web/20230525121120/http://humanities-research.exeter.ac.uk/salonartists/works).
The inspected snapshot displays 81,476 **submissions**, not 81,476 exhibited
works. It includes `Admis`, `Refusé` and revised jury decisions. Titles often
require the underlying register scan. The original database's non-commercial
licence and incomplete snapshot coverage remain recorded; no bulk records were
copied into the catalogue. Original registers and Salon livrets are the next
source for exact accepted/exhibited work identities.

For Russian icons, the Moscow 1913 catalogue was traced through bibliography to
the [Russian State Library viewer](https://dlib.rsl.ru/01003801904), which labels
online viewing public but requires sign-in for downloading. No download gate
was bypassed. Tretyakov inventory 14278, a fifteenth-century *Annunciation*, has
specific published 1913 and 1976–1977 exhibition references. It is **not** the
already-catalogued twelfth-century *Annunciation of Ustyug*. Primary scan review,
source-backed event/object preparation and a suitable exact image remain open.

The current public reading route is
`https://viewer.rsl.ru/rsl01003801904`. Its public document-info endpoint
explicitly permits unauthenticated reading of all 262 digital pages and reports
an available text layer; downloading and printing are disabled. The public
client's own `/api/v1/document/rsl01003801904/page/{page}/word-coords`
endpoint was used to read selected pages, without requesting the full PDF.
Receipts and text are preserved under `moscow-icons-1913` in the approved
source-metadata directory. Browser connection initialization failed, so these
are text-layer readings, **not visual scan reviews**. The table-of-contents
endpoint points to digital page 13, which actually begins section I, icon
painting; it must not be mistaken for an exhaustive contents list.

Digital page 9 distinguishes icon painting, manuscripts, textiles/embroidery
and silver/other objects. Selected pages 13, 14, 19 and 20 identify icon entries
1–11. No. 4 is *Archangel Michael*, described as late-fourteenth-century
Novgorod painting from S. P. Ryabushinsky's collection; no. 7 is *Annunciation*,
early-fifteenth-century Novgorod painting from M. N. Tyulin's collection. These
are historical catalogue descriptions, not silently adopted modern
attributions. Fractional dimensions and OCR around illustrations need visual
verification. Read-only production lookup found no exact Tretyakov accession
match for 12869 or 14278; this does not exclude differently catalogued duplicates.
The [Moscow 1913 event](https://artlines.org/exhibitions/f282e770-ad8b-5554-b4c5-020ad938179d)
is now delivered with **11 catalogued icon entries**, one publication reference
and nine captured source records. All entries were verified through the public
API. They remain unmatched to canonical artworks, with no images or named-artist
claims. The original anonymous collection label remains unknown; named historical
collections are retained as catalogue lender labels, not current holdings.
The event has year precision, no invented exact dates and no inferred museum
venue. Section I alone is represented; manuscripts, textiles and metalwork are
excluded. No main artwork, artist, image or real-local-database writes occurred.
Exact event dates, the rest of the icon checklist, object reconciliation and
images remain open. Procedure: `ops/historical_exhibitions_moscow_1913_20261012.py`;
receipt: [moscow-1913-delivery.json](moscow-1913-delivery.json).

Francis Cotes's *William and Penelope Welby Playing Chess* is identified as Louvre
Abu Dhabi inventory LAD 2013.007. The source history gives Royal Academy 1769
no. 26 and the **1881 winter Old Masters exhibition**, no. 49; the latter is not
the 1881 summer show. The museum's direct endpoint returned 403 after public
web-reader facts, and the Commons image host returned 429. Those requests remain
held without retries or alternate-host workarounds. The Commons file-page capture
and object facts are preserved, but no image, artwork or connection is counted
as delivered from this lead. Louvre Abu Dhabi must remain distinct from the
Musée du Louvre institution.

## Artwork transcription and images

The first 1769 catalogue has 16 captured transcription/annotation pages. All
numbered-entry pages have now been inspected visually. The first 15-entry delivery
was followed by 104 further entries: **119 catalogue entries and 46 participant
labels** are committed. All 136 catalogue numbers are accounted for: 11 sculptures,
casts, medallions or wax models are excluded; six architectural designs remain
held until their physical medium is resolved. No. 49 is explicitly a drawing and
is retained. Anonymous contributors remain source labels, with no invented artist
records. Twenty-four additional participant labels link to existing artists; the
John Russell match uses the 1745–1806 painter, excluding the 1858–1930 namesake.

Two Kauffman paintings are matched to existing illustrated catalogue works using
the original catalogue numbers, National Trust object histories, dates and visual
identity. The later 1786 Achilles composition was explicitly not substituted for
the 1769 catalogue entry. Unresolved portraits retain their original labels.

Benjamin West's *The Departure of Regulus* (Royal Collection RCIN 405416) is now
one new review artwork with one authentic primary image and an exact link to
catalogue no. 120. The Commons file's PD-Art label and embedded Royal Collection
copyright credit are both preserved. The full-frame derivative is 1,000 × 734 px,
97,284 bytes; the original remains in the source archive. The original and
derivative were inspected visually. This brings the sample to **three securely
identified illustrated works**; it does not make the remaining 116 entries
illustrated or independently identified objects.

The Chronicle's explicit dates, **26 April–27 May 1769**, and historical Pall Mall
venue now enrich this event. These dates came from its year summary, not the IIIF
navigation date. The Royal Academy institution link continues to identify the
organizer, without assigning the show to the present building.

Catalogued participation is distinct from independently documented exhibition
history. Complete checklists, new object images and most artist reconciliation
remain outstanding. No generic painting or artist portrait fills an image gap.
The Molyneux portrait's two existing WikiArt records and multiple versions of
Russell's *Micoc and Tootac* remain identity-review leads, not new exhibition
connections. The original catalogue is fully reviewed by number; the eligible
artwork selection and installed checklist are still marked partial.

## Sources and remaining coverage

- [Royal Academy Chronicle](https://chronicle250.com/1769): individual annual
  catalogues, page coordinates, transcriptions and named-artist annotations.
- [Musée d’Orsay index](https://www.musee-orsay.fr/sites/default/files/2022-06/SalonsExpositions_1673-1961_v1_20220707.pdf):
  50 pages of historical event dates/venues; not an artwork checklist.
- [Internet Archive](https://archive.org/advancedsearch.php): 1,457 discovery hits
  for the initial bounded historical-paintings query; none counted as an event
  merely because a book/search result exists.
- [Getty Research Institute's bound Royal Academy catalogues on Internet Archive](https://archive.org/details/exhibitionofroya22roya):
  metadata and public OCR retrieved. The volume covers 1769–1786, despite a single
  1769 metadata date. It contains multiple editions and bound accompanying texts;
  these are additional evidence for already known events, not 18 new events.
- [National Trust 872173](https://www.nationaltrustcollections.org.uk/object/872173)
  and [872178](https://www.nationaltrustcollections.org.uk/object/872178): exact
  painting identities and Royal Academy 1769 histories. The second direct request
  returned a captcha after an earlier web-reader response; the hold is recorded
  and no challenge bypass was attempted.
- The Salons database returned HTTP 403 and DoME presented a challenge. Their
  catalogue leads remain useful; direct retrieval is held.
- [Royal Collection RCIN 405416](https://www.rct.uk/collection/stories/george-iii-joseph-farington-and-the-royal-academy/the-departure-of-regulus):
  the public web-reader response supplied the exact painting's 1769 history before
  a later direct HTTP request returned 403. The access hold is retained and no
  retry/bypass followed. The successful Commons capture and primary catalogue
  provide separate object evidence; the 403 body is not treated as a source page.
- National Museums Liverpool's Molyneux object endpoint returned 403; direct
  retrieval is held. Portrait-version reconciliation remains open.

Next work: original Salons catalogues, Internet Archive/Gallica/INHA catalogue
matching, the 1472 held Orsay rows, early seventeenth-century evidence, and wider
museum/geographic coverage. Russian icons, Greek artists, Byzantine and
post-Byzantine exhibition archives retain priority. Forums and criticism indexes
provide leads; factual imports require traceable event/object evidence.

## Evidence, code and verification

Small receipts and coverage summaries are in this directory. Full immutable
plans, source captures, classification decisions and cloud deletion operations:

`~/Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/`

The dated `ops/historical_*20261012.py` scripts preserve preparation, pinned
deletions and import logic. `historical_exhibitions_20261012.py plan` is read-only;
its explicit `apply` writes the authorized production event batch. No local
catalogue or test database was created or modified.

The historical browsing release is prepared from exact deployed API/web build
sources plus an allowlisted overlay. It defaults to the full archive; the retired
700-event selection is not its default. Build, candidate and live verification
receipts belong under:

`~/Library/Application Support/Artline/backups/historical-exhibitions-release-20261012/`

The historical API and web revisions are now at **100% production traffic**.
[Browse exhibitions](https://artlines.org/exhibitions) or inspect the
[1769 Royal Academy sample](https://artlines.org/exhibitions/c4d90cd2-4774-52d1-b986-7c00ce220c35).
The concurrent artist-connections and compact-palette releases were detected and
preserved by rebuilding against their exact source/configuration. Earlier builds
were never promoted. Runtime settings and rollback revisions are recorded in
`release-receipt.json`.

Nineteen API candidate checks and four Chrome browser tests passed before web
promotion. They cover historical filters, keyset paging, exact artwork links,
illustrated-first ordering, internal-only exhibition navigation, mobile account
menu access, and signed-out museum sign-in behavior. Desktop/mobile screenshots
were inspected; the checked widths have no horizontal overflow and the selected
pages have zero Axe WCAG2A/AA and WCAG21AA violations. Live-domain HTTP checks
returned 200 for the directory, Royal Academy source and 1769 detail routes.
All four browser checks also passed on the public domain. One assertion needed
its text locator scoped to the main element because streamed hidden content
duplicated the same phrase; the targeted retry passed without an app change.
After the 1769 continuation, all four live checks passed again, now exercising
the 50-entry page boundary, internal painting link and three illustrated works.
The paging test needed to wait for the new page's first entry before comparing
IDs. The API separately verified all 119 distinct entries across three pages,
ordered images first, exact event dates and the new painting's reverse exhibition
connection. The one-artwork transaction initially rejected the exhibition-style
date-precision value and rolled back; the corrected artwork value `exact` was
then committed and verified. No partial catalogue import resulted.

The read-only production suite passed against the actual corpus, including
illustrated-first keyset boundaries. Fifty measured query plans had a maximum
observed execution time of 16.69 ms in this sample. This is not a future
10-million-artwork load test. Web TypeScript and targeted lint checks passed on
the isolated deployed-source overlay, including the newer connections and palette
release baseline.

### Blake 1939: St. Matthew reconciliation

Cleveland's official object API for native ID 294155, accession 2017.4, explicitly
lists the Philadelphia 1939 exhibition and catalogue no. 155. Its provenance
places the painting with Mrs. William Emerson from 1893–1958, matching the
original catalogue lender. The existing catalogue entry now links to the existing
illustrated St. Matthew artwork. Original title, creator, lender, participation
and date labels remain unchanged; the additional source record preserves the
museum evidence. The museum's unrelated 1886 event has an inconsistent structured
1930 date; neither value was imported into this exhibition.

Verification confirms 28 API entries, now five illustrated, and HTTP 200 image
delivery. No new artwork/image was created and no main artwork or real-local
database record changed. The checklist remains partial. See
`blake-matthew-match.json` and
`ops/historical_exhibitions_blake_matthew_20261012.py`; immutable source capture,
plan and production preimage are retained under Application Support/Artline.

### Philadelphia archive: third selected historical cohort

Nine independently dated exhibitions from the archive's 1959–1964 folders were
added: Gustave Courbet, Mary Cassatt, Thomas Eakins retrospective, England and
France Observe Each Other in Prints and Drawings, Edward Hopper’s Complete
Graphic Work, Graphik: German Prints at Mid-century, Franklin C. Watkins
retrospective, Tuscany in the 19th Century, and Whistler's Mother. Each museum
occurrence and event detail was verified through the production API. Archival
folder duplicates were collapsed and explicit parenthetical exhibition dates
were used. Full checklists have not been established.

Two exact NGA objects were then linked, with two canonical artist connections:
Courbet's *La Bretonnerie in the Department of Indre* (native 53126, accession
1972.9.8, exhibition catalogue no. 25), and Cassatt's *Eddy Cassatt (Edward
Buchanan Cassatt)* (native 165887, accession 2015.41.1). The original historical
titles remain in the evidence. Both existing internal image assets returned
HTTP 200; main artwork records and the real local database were unchanged.

Possible touring counterparts for American Prints Today, Baskin's Iliad,
Garbisch paintings and Correr drawings remain unresolved and were not duplicated.
The Courbet contemporaries print exhibition is distinct from the retrospective.
Mixed-media collection displays need further object-level scope checks. Coverage
and these decisions are retained in `wave3-editorial-review.json` under the
Philadelphia source-evidence directory in Application Support/Artline.
See `pma-archive-wave3-delivery.json`, `pma-object-links-wave3.json`, and the
corresponding `ops/historical_exhibitions_pma_*wave3_20261012.py` scripts.

### Philadelphia archive: fourth selected historical cohort

Ten dated exhibitions from 1964–1970 were added: Curator’s Choice (painting),
Alfred Bendiner lithographs, Piet Mondrian, Lasansky's Nazi Drawings, Hurd/Wyeth
paintings, Master E.S., Ben Shahn graphics, Benton Spruance's Moby Dick
lithographs, Eakins portraits from St. Charles Seminary, and van Gogh paintings.
All ten API event details were verified. Existing Manet, Degas, Romantic Art
and Bibiena events were not duplicated; apparent date errors and possible tours
are tracked in `wave4-editorial-review.json` in the source evidence directory.

The Master E.S. exhibition (5 September–3 October 1967) now has 15 exact NGA
print links with catalogue numbers and verified internal image assets. The
museum histories include Israhel van Meckenem, Baccio Baldini and followers of
Master E.S.; these source creator labels are preserved, rather than assigning
all prints to the exhibition's titular artist. No new canonical artist links
were asserted. Unmatched native objects 4536 and 46386 remain unresolved; the
latter is specifically classified as a facsimile. These 15 links do not imply
a complete checklist. Main artwork records and the real local DB were unchanged.

Receipts: `pma-archive-wave4-delivery.json`, `master-es-1967-delivery.json`.
Scripts: `ops/historical_exhibitions_pma_archive_wave4_20261012.py` and
`ops/historical_exhibitions_master_es_1967_20261012.py`.

### Existing Philadelphia tours: ten illustrated checklist additions

The Manet 1966–1967 retrospective now has nine entries, including seven newly
matched NGA objects. Romantic Art in Britain 1968 now has five entries, including
three newly matched drawings by William Blake and John Hamilton Mortimer. All ten
new links use exact NGA native IDs and accession numbers; their internal images
returned HTTP 200. Existing event dates, occurrences, entries and main artwork
records were verified unchanged. The real local database was not written.

The Dead Toreador is restricted to the Philadelphia occurrence because its
museum history explicitly says “Philadelphia only.” Other new entries are linked
at tour level, without assuming that every object appeared at every stop. Original
catalogue numbers, including Manet no. 79a, and museum creator/date labels remain
in evidence. Five unmatched native objects (8685, 8687, 8688, 40138, 40139) remain
held; no substitute impressions were selected. Both checklists remain partial.

During preflight review an initial human comparison confused 1860s creation dates
with 1960s exhibition dates; the numeric check correctly showed these works predate
the events. The plan was corrected before any write. No date conflict or erroneous
hold was persisted for the matched prints.

Receipt: `pma-tour-links.json`. Script:
`ops/historical_exhibitions_pma_tour_links_20261012.py`. Immutable source evidence,
plan and production preimages are under Application Support/Artline/pma-tour-links
within the corresponding source-metadata and backups campaign directories.

### Philadelphia archive: fifth selected historical cohort

Eight dated 1971–1981 exhibitions were added: Whistler and His World, Yokohama
woodcuts, Gauguin monotypes, Osaka prints, Violet Oakley, Copley from Boston,
Lucas van Leyden and Drawings from van Gogh to Matisse. All eight API event
records were verified. Existing events were reconciled by title, venue and year;
Géricault/Dutch eighteenth-century date discrepancies and a possible Crosscurrents
tour are held for further research. The source-specific review is saved as
`wave5-editorial-review.json` under the Philadelphia source directory.

Gauguin's 23 March–13 May 1973 exhibition now has seven exact illustrated NGA
print links, all with catalogue numbers and verified HTTP 200 image assets.
Native 93055 is an unmatched verso record sharing catalogue no. 64 with matched
recto 93054; it was not counted as a separate artwork or exhibition entry.
No new artwork/image or artist record was created. Existing artwork records,
event dates, occurrences and the read-only real local database remain unchanged.
The checklist is partial.

Receipts: `pma-archive-wave5-delivery.json`, `gauguin-1973-delivery.json`.
Scripts: `ops/historical_exhibitions_pma_archive_wave5_20261012.py` and
`ops/historical_exhibitions_gauguin_1973_20261012.py`.

### Washington Sears galleries, 1932: Rembrandt etchings

The NGA's official native-object exhibition histories document 188 distinct
impressions at *Etchings by Rembrandt van Rijn (1606–1669) from the Collections
of Lessing J. Rosenwald*, Sears, Roebuck, and Co. Art Galleries, Washington, D.C.,
1932. Exact native ID/accession matching connected 185 existing prints, including
175 with internal images. Three unmatched impressions remain held. No opening or
closing day, catalogue number, catalogue publication or museum identity was
invented. The separate Chicago Rembrandt shows were reviewed and not conflated.

One canonical artist connection is supported by unqualified Rembrandt source
attributions. Qualified studio/joint/after labels remain explicit at object
level. The checklist remains partial; the original exhibition catalogue has not
been read. A web-search lead to the NGA Rosenwald archival finding aid is saved
for later research, without bypassing the existing main-host access hold.

Verification covered all 185 entry IDs across two API pages, two reverse artwork
lookups, the public exhibition page, all 175 image assets (HTTP 200 and image
content type), and unchanged main artwork records. No new artwork, image or
artist record was created, and the real local database remained read-only.
Receipt: `rembrandt-sears-1932-delivery.json`; source/preimage/asset evidence is
under Application Support/Artline in the `rembrandt-sears-1932` campaign folders.
Script: `ops/historical_exhibitions_rembrandt_sears_1932_20261012.py`.

The final PMA inventory segment (651–872) was also reviewed. Fiscal accounts and
rejected proposals were not imported as held exhibitions. Two Picasso display
leads and three apparent date errors remain unresolved. This is folder-title
review, not complete archive-content or historical museum coverage; decisions
are in `remaining-inventory-review.json` under the Philadelphia evidence folder.

### Chicago 1941: The First Century of Printmaking

The Art Institute's exhibition of 30 January–2 March 1941 was added with 126
exact NGA print links, 111 existing internal images and 17 supported canonical
artist connections. Museum histories supply catalogue numbers; the Paris Musées
library record independently supplies the venue, dates and 152-page catalogue
edited by Elizabeth Mongan and Carl O. Schniewind. The catalogue itself has not
been read and the checklist remains partial. Seven native objects lack unique
existing matches. Anonymous regional, workshop, attributed and after labels are
preserved; named artist participation is added only for matching unqualified
source/current primary attributions.

The 126 entries were verified across two API pages, along with reverse artwork
connections, the public event page and all 111 image assets. Main artwork records
were verified unchanged; no new artwork/image/artist records and no real-local
DB writes. Event dates and the Art Institute museum link are source-backed.
Receipt: `first-century-chicago-1941-delivery.json`; script:
`ops/historical_exhibitions_first_century_1941_20261012.py`. Immutable source
capture, plan, preimages and asset checks are retained under the corresponding
`first-century-chicago-1941` Application Support/Artline campaign directories.

Bibliographic source:
https://parismuseescollections.paris.fr/en/node/263980

### Six regional print exhibitions, 1929–1973

Official NGA native object histories establish six additional events. Exact
opening/closing dates remain unknown; years and historical venue labels are
retained without invented dates or successor-institution identities.

| Historical venue | Year | Exact artwork entries | Illustrated connections |
| --- | --- | --- | --- |
| John Herron Art Institute, Indianapolis | 1945 | 91 | 90 |
| Lakeview Center for the Arts and Sciences, Peoria | 1966 | 67 | 63 |
| Herbert F. Johnson Museum of Art, Cornell, Ithaca | 1973 | 67 | 66 |
| Baltimore Museum of Art | 1929 | 64 | 63 |
| Louisiana State University Library, Baton Rouge | 1960 | 43 | 38 |
| University of Notre Dame Art Gallery | 1965 | 47 | 46 |

Total: 379 exact artwork entries, 366 illustrated connections and 124 canonical
artist connections across six events. The 335 distinct referenced image files
all returned HTTP 200 with image content types. All entry IDs and image presence
were verified through bounded API pages, and main artwork records were verified
unchanged. No new artworks, images, artist records or real-local DB writes.

Sixty-six source histories lack unique existing object matches and remain held.
One exact repeated Cornell history for native 7773 was deduplicated, retaining
its source row indexes. Native 3731 and 6594 have incomplete catalogue-number
fields, retained as unknown. Repeated catalogue group numbers remain attached
to distinct native objects; group labels are not fabricated as unique numbers.
Qualified/anonymous creators are preserved; named participation is added only
where source and existing unqualified primary creator labels agree. The Baltimore
source includes a drawing despite its title referring to engravings; the actual
object classification is retained. All six checklists remain partial.

Receipt: `regional-prints-delivery.json`; script:
`ops/historical_exhibitions_regional_prints_20261012.py`. Immutable plan,
source/preimage evidence and asset verification are retained in the
Application Support/Artline `regional-prints` campaign directories.

### Five further regional exhibitions, 1931–1967

| Historical venue and exhibition | Year | Exact entries | Illustrated |
| --- | --- | --- | --- |
| Westmoreland County Museum, American Artists as Print Makers | 1963 | 65 | 55 |
| Pennsylvania State University, Selected 15th Century Prints | 1965 | 66 | 62 |
| Print Club of Philadelphia, Five Centuries of Print Making | 1931 | 48 | 42 |
| Virginia Museum of Fine Arts, William Hogarth | 1967 | 52 | 48 |
| Los Angeles County Museum, Jacques Callot | 1957 | 30 | 30 |

These five NGA-object-history exhibitions add 261 exact entries, 237 illustrated
connections and 44 canonical artist connections. Forty-eight unmatched source
histories remain held. All entry IDs and image presence were checked through
the API, and all 234 distinct image assets returned HTTP 200 with image content
types. Main artwork records were verified unchanged. No new artworks, images,
artists or real-local database writes. Exact opening/closing dates remain
unknown and the checklists are partial. Historical Los Angeles County Museum
was not automatically mapped to its modern successor institution.

The 1947 Hals/Rembrandt painting-titled event remains a research lead: its NGA
object histories refer to prints and drawings. This discrepancy needs independent
catalogue reconciliation before import. Similarly worded Cleveland and NGA
shows were checked and not conflated with the five selected venue-specific events.
Receipt: `regional-prints-wave2-delivery.json`; script:
`ops/historical_exhibitions_regional_prints_wave2_20261012.py`. Immutable plans,
preimages and asset checks are retained under Application Support/Artline in the
`regional-prints-wave2` campaign directories.

### Six further regional exhibitions, 1956–1970

| Historical venue / exhibition | Year | Exact entries | Illustrated |
| --- | --- | --- | --- |
| University Gallery, Minnesota / Toulouse-Lautrec | 1965 | 48 | 47 |
| Andrew Dickson White Museum, Cornell / William Blake | 1965 | 45 | 44 |
| North Carolina Museum of Art / Rembrandt and His Pupils | 1956 | 45 | 41 |
| Rhode Island School of Design / Jacques Callot | 1970 | 44 | 43 |
| Allentown Art Museum / George Catlin Paintings | 1970 | 43 | 43 |
| Brown University / Old Master Prints | 1959 | 35 | 33 |

The third regional cohort adds 260 exact artwork entries, 251 illustrated
connections and 38 canonical artist connections across six year-only events.
Ten source histories remain unmatched. Source statements of “no cat.” do not
receive invented catalogue numbers. Named, qualified and workshop creator labels
remain distinct. Historical Cornell and Minnesota venue names were retained
without inventing successor-institution links.

All API entries and 247 distinct internal image assets were verified; image
assets returned HTTP 200 and image content types. Main artwork records were
verified unchanged; there were no new artworks, images, artist records or
real-local database writes. Exact event dates and complete checklists remain
unresolved. Receipt: `regional-prints-wave3-delivery.json`; script:
`ops/historical_exhibitions_regional_prints_wave3_20261012.py`. Plans, production
preimages and image checks remain in the Application Support/Artline
`regional-prints-wave3` campaign directories.

### Five further regional exhibitions, 1930–1971

| Exhibition and historical venue | Year | Exact entries | Illustrated |
| --- | --- | --- | --- |
| Schongauer etchings, Art Alliance Philadelphia | 1930 | 36 | 35 |
| Catlin paintings/lithographs, Tennessee Fine Arts Center | 1971 | 41 | 41 |
| Good and Bad Angels, Notre Dame | 1968 | 35 | 34 |
| Dürer's Early Graphic Works, Princeton | 1971 | 39 | 38 |
| Toulouse-Lautrec lithographs, Southeast Arkansas Arts and Science Center | 1970 | 38 | 37 |

This fourth regional cohort adds 189 exact entries, 185 illustrated connections
and 28 artist connections. All API entries and 180 distinct internal image assets
were verified. Main artwork records remain unchanged; no real-local writes or
new artwork/image/artist records. Eleven source histories remain unmatched.
All five events retain year-only dates and partial checklists.

The Schongauer source's historical label “St. James the Less” is preserved in
evidence. Good and Bad Angels explicitly says “no catalogue”; no catalogue numbers
were invented. Princeton's competing institution records remain unresolved, so
its historical venue is stored without an arbitrary institutional link. Atlanta
1956 and Santa Fe 1971 leads are held for possible tour reconciliation.
Receipt: `regional-prints-wave4-delivery.json`; script:
`ops/historical_exhibitions_regional_prints_wave4_20261012.py`. Evidence, preimages
and asset checks are in Application Support/Artline `regional-prints-wave4` folders.

### Four collection exhibitions in Britain, Mexico, Italy and the United States

| Exhibition / venue | Year | Exact entries | Illustrated |
| --- | --- | --- | --- |
| Woodner drawings / Royal Academy, London | 1987 | 61 | 61 |
| Mellon Bruce French paintings / Legion of Honor, San Francisco | 1961 | 58 | 49 |
| French prints / Biblioteca Benjamin Franklin, Mexico City | 1945 | 30 | 28 |
| L'Incisione Europea / Galleria Civica d'Arte Moderna, Turin | 1968 | 29 | 28 |

Four exact-venue/year events add 178 artwork entries, 166 illustrated connections
and 88 artist connections. All entries, city/country labels and all 166 internal
image assets were verified. Twenty-eight source histories remain unmatched.
Works marked “hors de catalogue” in the Woodner history retain that evidence
and no invented catalogue number. Actual object media remain authoritative even
when the event title is broader or narrower. Creation-date scope is checked
separately from exhibition year; all checklists remain partial and exact opening
and closing dates remain unknown.

Turin's competing institution identities remain unresolved, so the historical
venue label is retained without an arbitrary institution link. No new artworks,
images or artist records were created. Main artwork records were verified
unchanged and the real local database was not written. Receipt:
`international-collections-delivery.json`; script:
`ops/historical_exhibitions_international_collections_20261012.py`. Source plans,
preimages and asset checks remain in Application Support/Artline under
`international-collections` campaign folders.

### Leningrad and Moscow, 1986: NGA Impressionist paintings

One touring exhibition, *Impressionist and Post-Impressionist Masterpieces from
the National Gallery of Art, Washington*, was added with two source-documented
venues: the State Hermitage Museum, Leningrad, and the State Pushkin Museum of
Fine Arts, Moscow. Historical city and Soviet Union labels are retained. Exact
stop dates remain unknown; no modern country code was substituted for the
historical country. The Moscow venue is not arbitrarily linked to either of two
competing Pushkin institution records.

Thirty-seven exact NGA painting identities were linked, 34 illustrated, with
20 supported canonical artist connections. The source histories identify the
tour, so entries are linked at tour level rather than asserting separately
confirmed participation at each stop. This is distinct from the reciprocal
Soviet works exhibition shown in the United States. The 37 matched histories
do not establish a complete tour checklist.

All 37 API entries, both historical venues and all 34 image assets were verified.
Main artwork records remain unchanged; no new artworks/images/artists or real-local
DB writes. Exact dates, the full catalogue, three missing images and the Pushkin
institution conflict remain research gaps. Receipt:
`soviet-impressionists-1986-delivery.json`; script:
`ops/historical_exhibitions_soviet_impressionists_1986_20261012.py`. Immutable
source/preimage and asset evidence is retained in Application Support/Artline
`soviet-impressionists-1986` campaign directories.

### Venice and Milan, 1989: NGA Impressionist paintings

One tour, *Impressionisti della National Gallery of Art di Washington*, now has
45 exact NGA painting links, 43 illustrated connections and 19 canonical artist
connections. Its two documented venues are Ala Napoleonica e Museo Correr,
Venice, and Palazzo Reale, Milan. Work links remain at tour level; appearance at
each individual stop is not independently asserted. Source histories specify
an unnumbered catalogue, and no entry numbers were invented.

All entry links, both Italy venue records and all 43 internal images were verified.
Main artwork records remain unchanged; no new artwork/image/artist records and
no real-local writes. The full catalogue is unread, so the checklist remains
partial despite all 45 selected museum histories having matches. Two works lack
images. Exact stop dates are held: indexed bibliographic and annual-report leads
disagree on venue assignment and a 22/23 September opening date. Those leads and
the need to inspect original catalogue editions are retained in
`date-research-leads.json`; no access holds were bypassed.

Receipt: `italian-impressionists-1989-delivery.json`; script:
`ops/historical_exhibitions_italian_impressionists_1989_20261012.py`. Immutable
plans, preimages and image verification remain under Application Support/Artline
in the `italian-impressionists-1989` campaign folders.

### Six Corcoran exhibitions, 1940–1981

| Exhibition | Year | Exact entries | Illustrated |
| --- | --- | --- | --- |
| Etchings by Childe Hassam | 1940 | 30 | 30 |
| Lithographs by Childe Hassam | 1940 | 30 | 30 |
| Lithographs by Childe Hassam | 1948 | 30 | 30 |
| Lithographs by Childe Hassam | 1955 | 29 | 29 |
| Sketches by Contemporaries of Frederic E. Church | 1979 | 27 | 27 |
| Early America on Paper: Prints and Drawings, 1750–1850 | 1981 | 26 | 24 |

Six source-documented Corcoran Gallery events add 172 exact entries, 170
illustrated connections and 42 artist connections. All API entries and 109
distinct internal image assets were verified. The 1940 Hassam etching and
lithograph cohorts have no overlapping objects and source media agree with their
distinct titles. The later lithograph shows retain separate source years even
where they exhibited the same impressions.

Three unmatched objects and two cut-paper works remain held. No Corcoran
institution record was found, so the historical venue label is retained without
mapping it to the current holding museum of its dispersed collection. Exact
opening/closing dates and full checklists remain unknown. Main artwork records
were verified unchanged; no new artwork/image/artist records or real-local
writes. Receipt: `corcoran-histories-delivery.json`; script:
`ops/historical_exhibitions_corcoran_histories_20261012.py`. Immutable source,
plan, preimage and asset checks are under Application Support/Artline in the
`corcoran-histories` campaign directories.

### Five further Corcoran exhibitions, 1963–1983

| Exhibition | Year | Exact entries | Illustrated |
| --- | --- | --- | --- |
| American Master Drawings from the Collection | 1983 | 48 | 28 |
| Progress of An American Collection | 1963 | 36 | 19 |
| American Lithographs from the Corcoran's Collection | 1977 | 33 | 19 |
| Selections from the Gift of J. Williams Middendorf, II | 1978 | 34 | 34 |
| Whistler’s World: The Master’s Etchings | 1982 | 34 | 34 |

These five shows add 185 exact entries, 134 illustrated connections and 90
artist connections. All entry links and 129 distinct image assets were verified;
main artwork records remain unchanged. No new artwork/image/artist records or
real-local writes. Source objects were checked for the separate artwork-date
cutoff; no creation dates after 1970 appear in the selected cohorts. Fifteen
histories remain unmatched. Historical title “Design of Leaping Deer” remains
in evidence. Dates remain year-only and all checklists partial.

The existing 1966 *Past and Present* Corcoran exhibition, currently one entry,
was not duplicated. Its 35 NGA object-history leads and current event/occurrence
snapshot are saved as `past-present-next-lead.json.gz` for subsequent exact
checklist enrichment. Receipt: `corcoran-histories-wave2-delivery.json`; script:
`ops/historical_exhibitions_corcoran_histories_wave2_20261012.py`. Evidence,
preimages and asset checks are retained under Application Support/Artline in
`corcoran-histories-wave2` campaign directories.

### Corcoran 1966: enrich the existing Past and Present exhibition

The existing event now has 35 entries: its original Cleveland Burchfield work
plus 34 newly linked NGA paintings. The new links provide 31 illustrated
connections and 28 supported canonical artist connections. One native source
object remains unmatched. No second event was created and the existing
14 April–15 September 1966 dates, occurrence and original entry were preserved.

All new entry IDs, 31 image assets, 28 artist connections and unchanged main
artwork records were verified. Unpublished/unnumbered checklist references and
historical titles (including Woman with a Dog, The Pathetic Song, The Earring,
and Autumn on the Hudson) remain in source evidence. No catalogue numbers were
invented. The checklist remains partial; no new artworks/images/artists or
real-local DB writes. Receipt: `corcoran-past-present-1966-delivery.json`; script:
`ops/historical_exhibitions_corcoran_past_present_1966_20261012.py`. Source plans,
preimages and asset checks are retained under Application Support/Artline in the
`corcoran-past-present-1966` campaign folders.

### Six further regional exhibitions, 1946–1974

| Exhibition / venue | Year | Exact entries | Illustrated |
| --- | --- | --- | --- |
| French Prints / University of Pittsburgh | 1951 | 32 | 29 |
| Europe in Torment / Rhode Island School of Design | 1974 | 34 | 34 |
| Mary Cassatt and her Parisian Friends / Pasadena Art Institute | 1951 | 33 | 33 |
| Rosenwald Prints / Cayuga Museum, Auburn | 1946 | 24 | 23 |
| The Apocalypse / University of Maryland, College Park | 1973 | 28 | 28 |
| Toulouse-Lautrec Lithographs / Phoenix Art Museum | 1961 | 28 | 26 |

This fifth regional cohort adds 179 exact entries, 173 illustrated connections
and 50 artist connections. All entry links and 170 distinct image assets were
verified. Twelve source histories remain unmatched. Source media and creation
dates were checked independently of event titles and years. Exact dates and full
checklists remain unresolved. Pasadena's historical institution was not silently
mapped to the Norton Simon Museum; Cayuga's event was not conflated with NGA's
1946 Music in Prints or acquisition displays.

Main artwork records were verified unchanged; no new artwork/image/artist records
or real-local writes. Receipt: `regional-prints-wave5-delivery.json`; script:
`ops/historical_exhibitions_regional_prints_wave5_20261012.py`. Immutable evidence,
preimages and image checks remain in Application Support/Artline under
`regional-prints-wave5` campaign directories.

### Catlin exhibitions in Brussels 1870 and New York 1871

Two nineteenth-century events now have 30 exact illustrated painting entries
each: *Indiens des deux Ameriques* at the Salle du Jardin Botanique, Brussels,
1870, and *Catlin's Indian Cartoons* at the Somerville Gallery, New York, 1871.
The 60 exhibition connections reference 31 distinct illustrated artworks, all
verified by HTTP 200 image checks and exact API entry matching. One existing
Catlin artist connection is added to each event; no new artist was created.

Three Brussels venue variants (Salle/Salon du Jardin Botanique and shortened
Salle du Jardin) were reconciled under the same title, city and year; original
labels and differing catalogue numbers remain in the source records. New York
has its own historical title and numbering. Exact dates and full original
catalogues remain unresolved, so both checklists are partial. The nonspecific
Smithsonian 1872 display lead was not imported as a distinct exhibition.

Main artwork records were verified unchanged; no new artworks/images/artists
or real-local writes. Receipt: `catlin-1870-1871-delivery.json`; script:
`ops/historical_exhibitions_catlin_1870_1871_20261012.py`. Source grouping,
preimages and asset checks are under Application Support/Artline in the
`catlin-1870-1871` campaign directories.


### Manet 1867/1884 and Stuart 1880

Three additional nineteenth-century exhibitions have exact illustrated painting
links: Manet at Avenue de l'Alma, Paris, 1867 (five); Stuart at Museum of Fine
Arts, Boston, 1880 (nine); and Manet at the Ecole des Beaux-Arts, Paris, 1884
(eight). All 22 API entry links and 20 distinct existing image assets passed
verification. Four event/artist connections reflect current NGA attribution.
Mrs. William Hartigan is currently attributed to Carl Fredrik von Breda; the
Stuart exhibition title does not override that attribution. Historical source
labels are retained. Native object 52180's concatenated source text “42as” was
interpreted as catalogue number 42 followed by “as”, not 42a.

Title and venue variants were reconciled; all existing events in the three years
were reviewed for duplicates. The 1867 private Manet exhibition remains distinct
from the Paris Salon and Universal Exhibition. The historical Ecole venue was not
automatically assigned to its collection museum. Exact dates and complete
checklists remain unresolved. Bibliographic research found an Internet Archive
1867 catalogue (cataloguedestabl00mane) and BnF 1884 photographic documentation
(cb42276330r); these are follow-up leads, not claimed original-catalogue review.

No new main-catalogue artworks, images or artists; main artwork snapshots remained
unchanged and no real-local writes occurred. Receipt:
`manet-stuart-nineteenth-century-delivery.json`; script:
`ops/historical_exhibitions_manet_stuart_20261012.py`. Immutable `plan-v2.json.gz`
and its matching preimage are the delivered plan; the earlier plan was not
executed. Evidence and asset checks remain in Application Support/Artline under
`manet-stuart-nineteenth-century`.


### Lawrence Gallery 1836 and Washington exhibitions 1853/1857

Four additional events now link 22 illustrated works: the Lawrence Gallery's
sixth exhibition (four drawings) and fifth exhibition (two drawings), London,
1836; the Washington Exhibition at the American Art-Union Gallery, New York,
1853 (eight paintings); and the Washington Art Association first annual,
Washington, DC, 1857 (eight paintings). Eight event/artist connections were added.
All API entries and 17 distinct existing image assets passed verification.

The fifth and sixth Lawrence shows are separate numbered exhibitions, despite
sharing a year and collection. The New York Washington Exhibition is distinct
from the Washington, DC, association event. Native object 53384 remains unmatched;
no placeholder artwork was created. Catalogue numbers and historical attribution
qualifiers, including “as Annibale”, remain in original source histories; current
creator labels do not purport to reproduce historical attribution. Exact dates
and full checklists remain unresolved. Soane b7509, Huntington lib-105000 and PAFA's
Lambdin pamphlet finding aid identify relevant catalogues for further research;
this batch does not claim to have read their full contents.

No new main-catalogue artworks/images/artists or real-local writes. Receipt:
`lawrence-washington-nineteenth-century-delivery.json`; script:
`ops/historical_exhibitions_lawrence_washington_20261012.py`. Source grouping,
bibliographic leads, immutable preimages and asset checks remain in Application
Support/Artline under `lawrence-washington-nineteenth-century`.


### Manchester Art Treasures 1857

One reconciled Art Treasures event now has 20 illustrated exact artwork links
and 14 artist connections. Ancient/Modern Masters and other catalogue sections
remain one exhibition. All 20 API entries and existing internal image assets
passed verification. The catalogue 501 triptych is linked once through assembled
native object 102628; reverse-surface objects 102629/102630 are preserved as
related evidence, not additional exhibited objects. Watson and the Shark remains
unnumbered, with source page 82 retained. Current creators and historical
attributions remain distinguishable in source evidence.

Internet Archive metadata and OCR for `catalogueofarttr00artt` were captured.
Selected OCR search exposes numbering repeated between catalogue sections and
an unnumbered Copley entry. This is discovery, not full transcription or visual
verification. The National Portrait Gallery Scharf database is an additional
route for original hang and catalogue research; preparatory collection visits
must not be treated as final exhibition participation. See source EXS-058.

Exact dates and full checklist remain unresolved. No new main artworks/images
or artists and no real-local writes. Receipt:
`manchester-art-treasures-1857-delivery.json`; script:
`ops/historical_exhibitions_manchester_1857_20261012.py`. Grouping, immutable
preimages, original OCR receipts and image checks remain in Application
Support/Artline under `manchester-art-treasures-1857`.


### Nineteenth-century wave 3

Nine events add 38 exact illustrated entries and nine artist connections:
Grosvenor Van Dyck 1887 (four), Grosvenor Gainsborough 1885 (three), Cassatt New
York 1895 (five), Cassatt Paris 1893 (three), Morisot Paris 1896 (four), Corot
centenary Paris 1895 (three), Ingres Paris 1867 (six), Stuyvesant New York 1838
(five), and Artists' Fund Society New York 1862 (five). All API entry identities
and 31 distinct existing image assets passed verification.

Same-year titles and relevant venue aliases were reviewed. Existing Durand-Ruel
Orientalist/Japanese print/group shows are distinct; Chicago's Collection of 15
Pastels is a different venue and city. Original title variants were retained.
Historical creator claims remain distinguishable from current attributions,
including Gainsborough Dupont and attributed-to Jan Boeckhorst. Three Van Dyck
primary-artist candidates remain held by exact-name matching because the native
label includes “Sir”; artwork records and their existing artist links remain
unchanged. Two source entries without catalogue numbers retain blank numbers.

Morisot bibliographic records conflict on March 21 versus March 23 closing;
year-only dating remains pending original evidence. Louvre's indexed January 1
through December 31 span for Ingres is not imported as exact event dates.
Original catalogues and full checklists remain outstanding. No new main-catalogue
works/images/artists and no real-local writes. Receipt:
`nineteenth-century-wave3-delivery.json`; script:
`ops/historical_exhibitions_nineteenth_wave3_20261012.py`. Immutable evidence,
preimages, date leads and asset checks are under Application Support/Artline in
`nineteenth-century-wave3`.


### Fitzwilliam discovery and Van Dyck participant reconciliation

All 65 public Fitzwilliam exhibition-index pages were captured, yielding 3,231
unique reference URLs. Forty-two detail records selected around Rembrandt,
Byzantine/Greek/Russian subjects and iconography were captured through the public
JSON links. This is a research queue, not an ingestion count: references include
long-term loans, modern shows, unknown displays and excluded media. Rembrandt
1952/1956/1966/1969/1983, Byzantine Edinburgh 1958, Tatlin 1974 and Hogarth Venice
1989 need medium, object, venue/tour and duplicate review. Numeric date fields in
some records are corrupt relative to their original ISO strings. The authenticated
API route returned HTML; public JSON is separately advertised on detail pages.

The PEIB lead was reviewed and excluded: De Montfort University's database
contains photographic exhibitions, including Manchester's 539 photography
entries. These must not enrich the painting checklist. See EXS-059/060 and
`fitzwilliam-discovery.json`. Source captures and detailed review are in
Application Support/Artline under `fitzwilliam-exhibitions`. Scripts:
`ops/historical_exhibitions_fitzwilliam_discovery_20261012.py` and
`ops/historical_exhibitions_fitzwilliam_selected_20261012.py`.

The prior Van Dyck honorific hold is resolved. Three securely matched works have
current primary creator Anthony van Dyck, agreeing with native “Sir Anthony van
Dyck”. One participant connection was added to Grosvenor 1887 and verified in the
public API. The tentatively attributed Boeckhorst work remains separate. No event,
artwork, image or artist records added; no real-local writes. Receipt:
`vandyck-participant-delivery.json`; script:
`ops/historical_exhibitions_vandyck_honorific_20261012.py`. Earlier wave receipts
remain historical, unchanged; this is an additional artist connection.


### Fitzwilliam five-show Rembrandt object review

Complete pagination of selected 1952, 1956, 1966, 1969 and 1983 exhibition
references yields 50, 40, 47, 47 and 51 connected objects respectively. All 235
connections have reciprocal references in captured public object JSON, including
source catalogue numbers where supplied. The 105 distinct native objects are
prints; none currently matches the `fitzwilliam-native-object` identifiers in the
main catalogue. This is not a licence to substitute another museum's impression.

Source 48135 is explicitly a posthumous reworked impression; 81182 also names an
unknown reworker and additions not executed by Rembrandt. Their qualifications
are preserved. Five other objects have explicit creation ranges, not unknown
years (42448, 44060, 81505, 81654, 81785). Event date metadata still needs careful
handling: 1966 and 1969 original month strings conflict with malformed derived
numeric year fields. Exact venue/institution, duplicate review and source-backed
entry import remain next steps. No production events, main works or images were
added in this discovery pass; no real-local writes.

Receipt: `fitzwilliam-rembrandt-discovery.json`. Captured evidence lives under
Application Support/Artline `fitzwilliam-exhibitions/rembrandt-five-shows`.
Scripts: `ops/historical_exhibitions_fitzwilliam_rembrandt_discovery_20261012.py`
and `ops/historical_exhibitions_fitzwilliam_rembrandt_objects_20261012.py`.


### Fitzwilliam five-show Rembrandt delivery

The reviewed Cambridge exhibition references are now five production events with
235 documented exhibited-print entries (50/40/47/47/51), covering 105 distinct
native impressions and five Rembrandt artist connections. Every API entry ID,
missing internal image/work link, artist identity and event date was verified.
Dates are 20 May–20 October 1952; 14 March–1 July 1956; January–March 1966;
July–October 1969; and 1 November 1983–28 February 1984. Original ISO strings
are retained; 1966/1969 retain month precision with no invented day boundaries.
Contradictory derived date fields remain in immutable source JSON.

No same-period Cambridge/Fitzwilliam events were found; Washington and Raleigh
Rembrandt exhibitions are distinct. The source establishes Cambridge but not an
exact building or museum, so venue is explicitly unresolved and no institution
link is forced. Native accessions, individual print-state notes, source catalogue
numbers and qualified unknown reworkers are preserved. For 48135/81182 the source
plate date is not presented as an established impression date.

These are unillustrated exhibition entries, not newly created main-catalogue
artworks. Exact internal impression matches and approved image delivery remain
outstanding. Complete source web pagination is not a complete original exhibition
checklist. Receipt: `fitzwilliam-rembrandt-delivery.json`; script:
`ops/historical_exhibitions_fitzwilliam_rembrandt_release_20261012.py`. Immutable
plan/verification remain in the discovery directory's `release` subdirectory;
preimage is in the campaign backup directory `fitzwilliam-rembrandt-five-shows`.
No real-local writes, new main artworks, new images or new artist records.


### Fitzwilliam print catalogue integration

All 105 selected native impressions now exist as review artwork records and all
235 exhibition entries link to them. Native-ID audit, accession comparison of the
314 existing Fitzwilliam works and a bounded institution/Rembrandt-artist duplicate
audit found no matching impression. Each new work retains its native accession,
source citation, print techniques, component dimensions, creation precision and
state evidence. Five original ranges remain ranges. Museum ownership plus
acquisition dates (1816, 1876, 1912 or 1933) support 105 accepted holdings, without
current-display claims. Source captures were hash-verified before the transaction.

103 unqualified works link to the existing Rembrandt artist. The two explicitly
reworked/posthumous impressions retain qualified creator labels and unknown
impression dates; source plate dates remain textual evidence. No new artist,
image or exhibition records were created. All 235 public API artwork links were
verified and existing entry titles, catalogue numbers, participation and source
labels remain unchanged. Exact same-impression images are still missing for all
105 works; another museum's impression must not be substituted.

Receipt: `fitzwilliam-print-catalogue-delivery.json`; script:
`ops/historical_exhibitions_fitzwilliam_print_catalogue_20261012.py`. Immutable
plan/verification are under the Fitzwilliam discovery `rembrandt-five-shows/
catalogue-release` directory; preimage is under the campaign backup directory
`fitzwilliam-rembrandt-five-shows/catalogue-release`. The real local catalogue
remains untouched. Exhibition totals remain 10,256 active, 10,072 held and 34
undated; campaign additions remain 2,791 events.


### Fitzwilliam pictorial-media discovery expansion

A bounded cohort of 537 index titles explicitly naming paintings, drawings,
prints, etchings, watercolours or icons now has captured public JSON detail
records. Source event-date strings yield 306 historical-date candidates, 114
outside-date-scope records and 117 without usable explicit event dates. Seventy-two
records contain inconsistent parsed date fields. These are discovery categories,
not approved events: absent endpoints, unknown venues, tours, medium/object scope
and duplicate identities remain to be reviewed. Title years were not treated as
event dates. Six historical records have exact normalized-title/start-year matches
to existing catalogue events; they are duplicate leads, not automatic merges.

Steer 1894 records 975/985 and Ruskin's Turner 1878 records 1110/1117 are specific
possible source-duplicate pairs. Early catalogue leads include Turner drawings
1833 and the Lawrence Gallery tenth exhibition 1836; none was imported in this
pass. Native JSON and receipts remain under `fitzwilliam-exhibitions/
medium-title-details`; aggregate review and duplicate leads are alongside them.
Receipt: `fitzwilliam-medium-title-discovery.json`; script:
`ops/historical_exhibitions_fitzwilliam_medium_cohort_20261012.py`.

A separate selected Commons search found accession-specific print-image leads.
Of four candidates, only AD.12.39-14 (native 46647, Large Lion Hunt) matches the
105 selected print records. The other accessions must not be substituted for
same-title impressions. Full source/identity/image review remains outstanding;
the existing Commons upload-host access hold remains. Search leads are stored in
`catalogue-release/commons-image-leads.json`; no image downloaded or attached.
No production or real-local mutations in this discovery expansion. Exhibition
totals remain 10,256 active, 10,072 held and 34 undated.


### Early London Fitzwilliam continuation

Three events are delivered: Turner drawings, London, June–July 1833 (one entry);
the Lawrence Gallery tenth exhibition, 1836 (one Michelangelo sheet); and English
Medieval Paintings and Illuminated Manuscripts, 1896 (three painting entries).
All five API entries and two exact existing main-work links passed verification.
The existing works remain unchanged; all five entries currently lack images.

Turner's source month strings override malformed derived numerical years without
inventing days. Lawrence tenth is distinct from the fifth/sixth 1836 exhibitions;
its sheet has recto/verso subjects and is counted once (native 7589, catalogue 66).
Medieval native 785/786 share catalogue 22 and remain distinct panels; 784 is
catalogue 11, with British School and uncertain saint identification preserved.
No anonymous creator is forced to a named artist. Native 784/786 match existing
works by native ID, accession and holding. Three internal object matches remain
open. Exact venues remain unresolved; source London location is preserved.

The 1894 Ferrara/Bologna lead remains pending reconciliation with the exhibition's
original-artwork and photographic-reproduction sections; no event was created
for it. Original full catalogues remain unreviewed, and all checklists are partial.
No new main artworks/images/artists or real-local writes. Receipt:
`fitzwilliam-early-london-delivery.json`; script:
`ops/historical_exhibitions_fitzwilliam_early_london_20261012.py`. Source evidence
and immutable release are under `fitzwilliam-exhibitions/early-london-release`;
preimage is in campaign backups under `fitzwilliam-early-london`.


### Fitzwilliam duplicate-pair and attribution review

Four candidate exhibition references and five reciprocal object records were
captured for Steer London 1894 (975/985) and Ruskin's Turner drawings London 1878
(1110/1117). The Turner pair now has supporting shared catalogue evidence:
native 13978 and 13896 cite publication-1193, the Fine Arts Society 1878 catalogue;
13913 cites Ruskin Works p.422. Indexed volume XIII text matches catalogue 14
(Fortified Pass), 119 (Sallanches) and the numbered Tonbridge reference (2).
Treat the pair as one candidate event; preserve all native source identifiers.
The old Lancaster PDF link returns 404, so this is not a claimed scan review.

The independent Paul Mellon Centre Girtin catalogue indexes Tonbridge Bridge and
Castle as the same London1878 no.2 object historically attributed to Turner.
This conflicts with the current Fitzwilliam creator label. Preserve that label
as source/historical evidence; do not silently relink the work to Turner or Girtin.
The independent catalogue page timed out when opened; indexed attribution and
bibliography evidence remain a review lead, not a complete page capture.

The Steer pair has separate works and compatible 1894 titles, but no direct
shared catalogue evidence yet. Goupil February1894 is an auction-history lead;
same city/year alone does not justify merging. Native 3953 is catalogue11 and
3955 catalogue3. Further original-catalogue review remains required.

A transient Secret Manager DNS failure initially prevented production review.
DNS recovered and a fresh read-only 1878/1894 creator/venue query found no matching
existing events. No production mutation occurred. Receipt:
`fitzwilliam-duplicate-pair-review.json`; its initial failed-access observation is
superseded by `duplicate-pair-review/production-duplicate-audit.json` in Application
Support/Artline. Source JSON, HTML captures and decisions remain in that directory.
Exhibition totals remain 10,259 active, 10,075 held and 34 undated.


### Reconciled Ruskin–Turner 1878 delivery

One London1878 event now represents Fitzwilliam references1110 and1117, retaining
both original exhibition source records. Three drawings have documented entries:
Sallanches (native13978, no119), Tonbridge Castle (13896, no2), and Fortified Pass
in the Val d'Aosta (13913, no14). The Fine Arts Society Galleries venue is supported
by the museum-linked 1878 publication; no modern institution identity is forced.
Year-only dating remains; exact exhibition dates and full checklist are open.

Tonbridge's Turner/Girtin conflict is explicit in the entry creator label and
source evidence, with no named artist link forced. All three API entry identities
were verified. None has an internal artwork or image match yet. Existing1878
exhibitions were reviewed before insertion; no competing Ruskin/Turner event was
found. No main artwork/image additions or real-local writes. Receipt:
`fitzwilliam-ruskin-1878-delivery.json`; script:
`ops/historical_exhibitions_fitzwilliam_ruskin_1878_20261012.py`. Immutable plan,
preimage and verification remain in the Fitzwilliam `ruskin-1878-release` and
campaign backup `fitzwilliam-ruskin-1878` directories.


### Cambridge drawing-exhibition discovery

Twenty-five additional Cambridge drawing-exhibition references now have complete
public connected-record pagination and metadata captures for 748 unique native
objects. All 942 exhibition/object connections have reciprocal references in the
object JSON. Source types comprise 618 drawings, 93 prints, 20 miniature paintings,
one painting, 15 albums and one sketchbook. The 16 bound volumes account for 16
connections and are held pending individual-leaf review, rather than imported as
single pictorial artworks. 470 object records have no creation-date field; none
has an explicit parsed end date after1970. Missing dates remain unknown, not
eligible by inference from creator lifetimes or collection titles.

Two existing Rembrandt events were excluded from discovery, and Frink's mixed
sculpture/drawing/print/book show was held. The similar1959 Italian drawing
references1570/1567/1562 and1960 Venetian references1587/1601 need event identity
review despite having no overlapping object IDs. Reference1601 has no connected
objects. Native3785, Lilium Superbum, is the only exact current native-ID artwork
match; its catalogue work type is preserved. No exact normalized-title catalogue
candidates were found; this does not establish absence of aliases or tour records.

No production or real-local mutations. Receipt:
`fitzwilliam-cambridge-drawings-discovery.json`; scripts:
`ops/historical_exhibitions_fitzwilliam_cambridge_drawings_20261012.py` and
`ops/historical_exhibitions_fitzwilliam_cambridge_objects_20261012.py`. Captures,
object review, production match audit and summary are under Application Support/
Artline `fitzwilliam-exhibitions/cambridge-drawings-review`. Medium/date/attribution,
venue and duplicate review remain required before import. Exhibition totals
remain10,260 active,10,076 held and34 undated.

### Cambridge Broughton and flower drawings: eight exhibitions

Delivered eight source-backed exhibitions from 1973–1984 with 454 documented
entries, verified through the production API. One entry matches an existing
main-catalogue artwork by native object ID and accession; 453 remain source
entries awaiting internal artwork reconciliation. No new main artworks or
images were added. Fifteen bound albums remain held for individual-leaf review.

Seven shows retain their exact source dates; the 1984 show retains year precision.
The source represents that year as a range with only an end value; its equal
earliest/latest years corroborate 1984 without supplying exact dates. Cambridge
is documented, but no exact building or institutional assignment is inferred.
Unknown artwork creation dates and qualified creator labels remain explicit.
These are partial source checklists, not claims of full exhibition coverage.

Implementation: `ops/historical_exhibitions_fitzwilliam_broughton_20261012.py`.
Receipt: [fitzwilliam-broughton-delivery.json](fitzwilliam-broughton-delivery.json).
Source captures and production preimages remain in Artline Application Support.
The real local database was not modified. Verified totals: 10,268 active,
10,084 confirmed held, 34 undated; campaign additions 2,803.

### Cambridge drawing and print continuation: twelve exhibitions

Added twelve exhibitions from 1957–1988 with 416 source-backed entries. All event
dates and all entries, including the paginated 125-entry Romney show, were verified
through the production API. No new main-catalogue artworks, artist links or images
were added; these entries require internal artwork reconciliation and image work.

The source covers Italian and Venetian drawings, French and Flemish drawings,
Romney, Griggs, Segonzac, Augustus John, Brangwyn, and the Clarke collection.
Original date values preserve month/year precision where appropriate; malformed
derived year bounds remain in the source evidence rather than becoming dates.
Cambridge is established, but exact buildings remain unresolved. Five references
(1570, 1562, 1567, 1587 and 1601) remain held for possible duplicate-event review.
Unknown creation dates and qualified makers remain explicit; partial checklists
are not represented as complete.

Implementation: `ops/historical_exhibitions_fitzwilliam_cambridge_remaining_20261012.py`.
Receipt: [fitzwilliam-cambridge_remaining-delivery.json](fitzwilliam-cambridge_remaining-delivery.json).
Production preimages and source captures are retained in Artline Application
Support. Real local database unchanged. Verified totals: 10,280 active, 10,096
confirmed held, 34 undated; campaign additions 2,815.

### Griggs, Segonzac and Augustus John: 92 main-catalogue prints

Added 92 native Fitzwilliam print impressions in review: 16 Griggs, 31 Segonzac
and 45 Augustus John. Each has an exact native-object identifier, museum accession,
accepted holding assertion and primary artist link. All 92 existing exhibition
entries now link to these internal artwork records; every API link was verified.
No images were attached. Exhibition totals remain 10,280 active and 10,096 held.

The bounded duplicate audit inspected 1,004 works associated with the museum or
the three artists. Nine title matches belong to separately accessioned NGA/MoMA
impressions; their images were not reused. Publisher Henri Petiet remains explicit
in the original maker-role evidence and is not linked as a primary artist. The
separate Fabri/Passarotti/Michelangelo attribution record is held for further review.

23 works retain unknown structured creation dates: one undated object and 22 with
source date notes requiring distinction between publication and creation. Source
labels and notes remain preserved. Other records retain exact/range/circa precision.
The first transaction rolled back completely on a missing date-display constraint;
the successful transaction uses “Date unknown” for the genuinely undated object.
No real-local database writes occurred.

Implementation: `ops/historical_exhibitions_fitzwilliam_print_catalogue_two_20261012.py`.
Receipt: [fitzwilliam-print-catalogue-two-delivery.json](fitzwilliam-print-catalogue-two-delivery.json).
Plans, source captures, duplicate decisions and preimages are in Artline Application
Support. Exact-impression image research remains outstanding for all 92 works.

### George Romney 1977: 125 drawings and four exhibition artist links

Added 125 independently accessioned Fitzwilliam drawings in review and connected
all 125 entries in the 1977 Romney exhibition to their internal artwork pages.
Each has a source-backed holding assertion and primary George Romney link.
The full paginated API response was checked against every expected entry/work pair.
No images were added. 75 source records lack dates and another 15 explicitly
question their dates; these 90 works retain unknown structured creation years.
The questioned source labels and notes remain visible. Known dates retain their
exact, range or circa precision without inference from the artist's lifespan.

A bounded 768-work duplicate audit found two same-title candidates: a painting
with a generic landscape title, and a separately accessioned NGA drawing. Neither
is the documented Fitzwilliam sheet. All 125 new museum accessions are distinct.

Also added and API-verified four exhibition-level artist participants: Romney,
Griggs, Segonzac and Augustus John. Their links are supported by 217 exact native
objects already attached to the corresponding exhibitions.

Receipts: [Romney drawings](fitzwilliam-romney-catalogue-delivery.json) and
[four artist participants](fitzwilliam-four-participants-delivery.json).
Scripts: `ops/historical_exhibitions_fitzwilliam_romney_catalogue_20261012.py` and
`ops/historical_exhibitions_fitzwilliam_four_participants_20261012.py`.
Source captures, duplicate decisions and production preimages remain in Artline
Application Support. Exhibition totals are unchanged at 10,280 active and 10,096
confirmed held; real local catalogue unchanged. Exact-object images remain a gap.

### Remaining Cambridge drawings: 146 objects, 198 internal links

Added 144 drawings and two painted miniatures as 146 distinct review artworks,
with source-backed Fitzwilliam holdings and 198 exact exhibition-entry links.
All 198 links were verified through the production API. The source labels retain
qualified and historical attributions; no primary artist assignments were made
in this pass. 136 structured creation dates remain unknown, with original date
labels and notes preserved. Source ownership does not establish current display.

The institution-scoped audit found 11 title matches to other accessioned paintings
or prints, not the selected drawings. No accession duplicates exist among the
146 selected objects or against existing museum records. Exact native identifiers
were checked before insertion. Fifty-two repeated exhibition connections reuse
the same internal object rather than creating another artwork.

All 146 objects have museum-linked media references; 63 contain object-level legal
metadata. These are image leads, not verified attached reproductions. No images
were downloaded or added. The immutable image-evidence review is stored alongside
the release plan under Artline Application Support. Image selection and artist
identity reconciliation remain outstanding.

Implementation: `ops/historical_exhibitions_fitzwilliam_oldmaster_drawing_catalogue_20261012.py`.
Receipt: [drawing catalogue delivery](fitzwilliam-oldmaster-drawing-catalogue-delivery.json).
Source captures, duplicate audit and production preimages are preserved. Real local
database unchanged. Exhibition totals remain 10,280 active and 10,096 held.

### Cambridge drawings: 68 primary creator links

Reconciled 68 previously unlinked drawings with 29 existing artist identities.
Only single, unqualified museum maker records were selected using explicit name
order/conventional-name equivalences. Each link has a source citation preserving
the original creator label, native object ID, captured source hash and mapping
basis. All 68 exact artwork/artist pairs were verified in production queries;
artwork rows are unchanged, including dates, status, holdings and original labels.
This verification is database-level, not a claim of rendered UI testing.

78 objects remain unresolved. Qualified attributions remain unlinked as primary
creators, and Raphael/Sanzio has two catalogue artist identities requiring separate
reconciliation. Neither artist record was merged or removed in this pass.
No new works, images or exhibitions were added; real local database unchanged.

Script: `ops/historical_exhibitions_fitzwilliam_drawing_creators_20261012.py`.
Receipt: [drawing creator links](fitzwilliam-drawing-creators-delivery.json).
The complete artist candidates, mapping and preimages are preserved in Artline
Application Support. Exhibition totals remain 10,280 active and 10,096 held.

### Drawing exhibitions: 56 artist navigation links

Added 56 exhibition/artist participant links across five historical Cambridge
shows. They are supported by 105 exact exhibition entries representing 68 distinct
artworks with verified unqualified creator identities. The API artist set for each
of the five events was checked for exact equality with the expected set.

Qualified and unresolved source creators remain excluded from these primary
participant mappings. Source object records and original labels remain preserved;
no artwork dates, holdings, images or publication states were changed. No new
exhibitions or artwork objects were added. Real local database unchanged.

Receipt: [drawing exhibition participants](fitzwilliam-drawing-participants-delivery.json).
Implementation: `ops/historical_exhibitions_fitzwilliam_drawing_participants_20261012.py`.
Production preimages remain in Artline Application Support. Catalogue totals remain
10,280 active exhibitions, 10,096 confirmed held and 34 undated.

### Early London continuation: 34 exhibition references researched

Captured 34 selected public London exhibition references dated before 1930,
excluding previously delivered or separately reviewed early references. Public
object lists yield 67 connections to 63 distinct objects; every connection was
verified against the reciprocal museum object history. These are not yet 34
deduplicated production events. Same-year shared-object matching found no overlaps,
but title variants and production duplicates still require reconciliation.

60 connections have drawing/painting/print/painted-miniature object types. Six
manuscript-cutting records all share catalogue number 104 in the 1923 British
Primitive Paintings show and need physical-object/leaf grouping review. One
Frank Dobson record has the generic type “figure” and needs medium review. These
seven connections are held, not automatically rejected or counted as eligible.
Source dates, venues, media, existing catalogue identities and image availability
remain to be evaluated before release. No production or real-local changes.

Receipt: [early London discovery](fitzwilliam-london-early-discovery.json).
Scripts: `ops/historical_exhibitions_fitzwilliam_london_early_discovery_20261012.py`
and `ops/historical_exhibitions_fitzwilliam_london_early_objects_20261012.py`.
Immutable event pages and object JSON captures are preserved under Artline
Application Support in `fitzwilliam-exhibitions/london-early-discovery`.

### Early London release selection and medium audit

The follow-up read-only production audit identified 12 existing native Fitzwilliam
object identities. Source medium evidence establishes object 13403 as cast bronze
(sculptor Frank Dobson), so it is excluded from the pictorial release. The six
MS 330 leaves are illuminated with pigments, ink and gold, not photographs or
sculpture; their shared catalogue number 104 requires grouping review.

Selected 25 references with 47 connections for the next release plan. Held nine
references: the manuscript show, the sculpture-only linked lead, two Sickert 1912
variants, two Herbert Horne 1916 variants, two 1860-period 1923 variants, and
the generic 1927 Exhibition of Drawings. Same-year production title similarities
were reviewed as leads, not automatic matches. Existing native IDs are candidates
for exact internal linking; image status and all release invariants still require
verification. No production changes in this audit.

Receipt: [early London audit](fitzwilliam-london-early-audit.json).
Script: `ops/historical_exhibitions_fitzwilliam_london_early_audit_20261012.py`.
Detailed production candidates and selected source records remain in Artline
Application Support.

### Early London: 25 exhibitions delivered

Delivered 25 reviewed London exhibitions dated 1878–1929 with 47 reciprocal
object-history entries. Thirteen entries link to existing catalogue objects by
exact native ID and accession. All event dates, entry sets and artwork links
were verified through the production API. No new main artworks or images were
added; all 47 entries remain unillustrated. Exact buildings remain unresolved
where only London is documented. Checklists remain partial.

The nine previously held references remain excluded from this release. Source
captures, duplicate decisions, unknown facts and attribution qualifiers are
preserved. Real local database unchanged.

Receipt: [early London delivery](fitzwilliam-london_early-delivery.json).
Implementation: `ops/historical_exhibitions_fitzwilliam_london_early_release_20261012.py`.
Verified baseline 10,330 active; after delivery 10,355 active, 10,169 held,
35 undated. This delivery accounts for exactly 25 added records.

### Herbert Horne 1916: original catalogue reconciliation

Captured Internet Archive metadata and the original catalogue OCR for
`exhibitionofherb00burl` (90,665 bytes). The title page identifies the Burlington
Fine Arts Club, London, 1916. Catalogue entries 80 and 82 corroborate the two
Blake-related Fitzwilliam objects in exhibition reference 1235. Entry 80 credits
Catherine Sophia Blake, not William Blake. Entry 111 is Cliffs and Harbour by
Turner; reference 1109 supplies a tentative ?111 for Dover, harbour and shipping,
which must remain tentative rather than being promoted to an exact catalogue match.

The two museum references can be reconciled as one named-collection event while
preserving both source identities and the Turner uncertainty. Exact opening and
closing dates remain unknown. No production changes yet. OCR reviewed; page scans
not visually reviewed.

Evidence: [Horne 1916 reconciliation](horne-1916-reconciliation.json). Original
metadata/OCR captures and selected entry excerpts are preserved in Artline
Application Support. The 1923 Tate and 1912 Sickert pairs remain unresolved.

### Herbert Horne 1916 delivered as one event

Added one 1916 Burlington Fine Arts Club exhibition with three museum-documented
entries. Both museum exhibition references (1235 and 1109) remain attached to the
same event, along with the original catalogue reconciliation evidence. Catalogue
80 retains Catherine Blake as creator; 82 retains William Blake. Turner's entry
retains the tentative catalogue label ?111. Exact opening/closing dates remain
unknown; year precision is retained. All three API entries and event date precision
were verified. No main-artwork or image additions.

Receipt: [Horne 1916 delivery](fitzwilliam-horne-1916-delivery.json).
Script: `ops/historical_exhibitions_fitzwilliam_horne_1916_20261012.py`.
Production preimages and source captures preserved; real local DB unchanged.
Verified totals: 10,356 active, 10,170 confirmed held, 35 undated.

### Tate 1923: reconciled 1860-period exhibition

Added one event for Fitzwilliam references 1377 and 773 with five exact object
histories and one existing main-artwork link. Tate archive TG92/13 corroborates
the event identity and loan-exhibition format. All five entries and year precision
were API-verified. No main-artwork or image additions; checklist remains partial.

The archive lists 27 April–29 June 1923; Fitzwilliam1377 lists 27 April–29 July.
The Tate Library search lead also says July, but its page returned 429, so no
retry or full-page capture was attempted. Both alternatives remain in evidence;
structured year precision avoids asserting an unresolved closing date.

Primary source: https://archive.tate.org.uk/Record.aspx?id=TG+92%2F13&src=CalmView.Catalog
Receipt: [Tate 1923 delivery](fitzwilliam-tate-1923-delivery.json).
Script: `ops/historical_exhibitions_fitzwilliam_tate_1923_20261012.py`.
Source captures/preimages preserved in Artline Application Support. Real local
database unchanged. Verified totals: 10,357 active, 10,171 held, 35 undated.

### Sickert hold and delivered chronology correction

Sickert references 912/2950 remain held. Native object215699 is dated circa1928
in its museum record but links to the 1912 exhibition; same-title search results
for other works are not substitutes for this drawing. Object3867 is circa1911
and chronologically plausible, but the event pair needs more venue/catalogue evidence.

A source chronology audit checked 1,168 delivered entries across eight Fitzwilliam
batches and found one further conflict: Clausen native210190 dated1934 was linked
to a 1912 show. Its production participation is now uncertain and was API-verified.
Original dates, catalogue labels, source relationships and metadata remain intact.
The audit tests whether a recorded earliest creation year exceeds the event's
last recorded year; it cannot validate undated works or prove every source correct.

Scripts: `ops/historical_exhibitions_fitzwilliam_chronology_audit_20261012.py` and
`ops/historical_exhibitions_fitzwilliam_clausen_chronology_20261012.py`.
Receipts: [Clausen correction](fitzwilliam-clausen-chronology.json) and
[Sickert hold](sickert-1912-review.json). Future releases must check object creation
against exhibition chronology as well as the 1970 artwork cutoff. No new events
or images; real local database unchanged.

### London Gallery Project: selected catalogue discovery

Captured the Bowdoin directory of 114 gallery-location records and 13 selected
location pages for Agnew, Carfax, Chenil, Dutch Gallery, Fine Art Society, Goupil
and Leicester Gallery. Location records are not unique institutions, and several
repeat the same exhibition lists. Collapsing those repetitions yields 30 distinct
National Art Library catalogue leads. These include questioned dates and mixed
media; no production events or artwork checklist entries were inferred from them.
Leicester's Year’s Art references require separate extraction.

The University of Glasgow related database describes more than3,000 exhibitions
and900 galleries for1878–1908, but direct search-page capture returned403. No
retry or alternate endpoint was attempted. Its stated dates represent documented
activity rather than necessarily full opening/closing spans; cancellation and
editorially reconstructed title caveats must be retained in any later use.

Sources: https://learn.bowdoin.edu/fletcher/london-gallery/gallery-list/index.html
and https://www.exhibitionculture.arts.gla.ac.uk/about.php .
Receipt: [London gallery discovery](london-gallery-discovery.json).
Script: `ops/historical_exhibitions_london_gallery_discovery_20261012.py`.
Captures and `nal-catalogue-leads.json` are under the existing source-metadata
run's `london-gallery-project` directory. No production or real-local writes.

### Getty Blake candidate: seven exhibition-history leads

The search-indexed Getty European Drawings1 entry for accession84.GC.49 names
seven historical shows (1904,1906,two1914 venues,1927,1957,1978). The1906 event
already exists and could receive catalogue34 after identity verification.
Existing WikiArt artwork431a00dd-30dc-5554-8d1e-6112b045c8e8 has an internal image
but no accession or holding; its dimensions differ from the Getty catalogue.
The catalogue discusses two versions, so title/year agreement is insufficient.

The legacy Getty PDF URL redirects to a JavaScript publication page; the captured
response is HTML, not a reviewed original catalogue. No artwork/exhibition links,
holdings, images or metadata were changed. Next action: obtain the published
entry and compare the exact Getty sheet against the existing illustration.
Receipt: [Blake Getty leads](blake-getty-exhibition-leads.json).

### Getty Blake catalogue: eight illustrated connections

Getty’s 1988 *European Drawings 1*, catalogue 146, printed page 324
(PDF pages 335–336), documents eight exhibitions of accession 84.GC.49,
*Satan Exulting over Eve* (1795). Visual comparison confirms our existing
WikiArt reproduction depicts Getty’s first pull rather than the distinct
Craxton second pull. Seven new events and one existing Carfax1906 event
now have exact internal artwork/image and William Blake participant links.
The Carfax venue is resolved. Imported artwork dimensions remain unchanged
and their discrepancy is recorded. No new image files or artwork records
were created; all eight connections and participants were verified through
the production API. Checklists remain partial.

The moved Getty publication was resolved through its public linked-data
work247HHN and PDF product2QWKT4 to the official freely available PDF;
source captures, checksum and preimages are retained.
See `getty-blake-delivery.json` and
`ops/historical_exhibitions_getty_blake_20261012.py`.

### Getty drawings source inventory

Column-aware extraction identified 147 object-history pages:74 with exhibition
leads and73 declaring none. These are source pages, not unique exhibitions;
the publication describes149 catalogue entries, so the two remaining sections
need extraction review. Rendered originals remain authoritative.
See `getty-drawings-inventory.json` for the source/checksum and full inventory.

El Greco catalogue145, accession82.GA.166, has five visually verified historical
exhibition references (1929–1955), preserved in
`getty-elgreco-reviewed-leads.json`. Existing similarly titled paintings and the
separate standing-figure drawing are rejected as matches. Exact object/image acquisition and production delivery are now complete; see
`getty-elgreco-delivery.json`.

### El Greco exact image recovered

Getty public linked data resolves object103QV5 to UUID
9ac27f38-d1f3-4431-951a-d4ff99ee506f, accession82.GA.166. Its IIIF manifest
explicitly grants CC0 for the main image. Original and full-frame derivative
under100,000 bytes are retained under Application Support; visual comparison
with catalogue145 passed. See `getty-elgreco-image-preparation.json`.
Production artwork creation, asset upload and five exhibition connections
are complete and API-verified. Five additional structured object activities date1993–2004
and are excluded from this historical campaign. The dates in their titles
are artist lifetimes or artwork periods, not exhibition dates.

### El Greco production delivery completed

Added one review drawing (Getty82.GA.166, about1600), its full-frame CC0 image,
one accepted Getty holding and primary El Greco creator link. Five new historical
events1929–1955 each have an illustrated exact-object entry and artist participant.
All five API entries, dates and participants passed verification; public image
bytes match the reviewed98,742-byte derivative. Real local catalogue untouched.
The first transaction rolled back on an HTTP rights-policy URL constraint; the
canonical HTTPS CC0 URL resolved it, while raw museum rights evidence is preserved.
See `getty-elgreco-delivery.json` and
`ops/historical_exhibitions_getty_elgreco_20261012.py`.

### Getty linked-data exhibition discovery

The official Royal Academy1953 activity provides11 exact drawing objects, all
with reciprocal exhibition references. Their179 venue references reduce to115
distinct activities:51 historical (1600–1989),64 later/outside, none undated
or boundary-crossing in this selected cohort. They are not yet unique or new
Artline exhibitions. Source activity/year bounds preserve original date labels.
Captured all115 activity records without errors; no images downloaded in this
metadata pass. See `getty-ra1953-discovery.json`, `getty-activity-scope-review.json`
and the Getty discovery scripts. Reconcile venue/tour identities and existing
events before releasing the historical candidates.

### Getty venue and tour reconciliation

The51 venue activities group into36 explicit Getty exhibition identities.
Six additional activities are parent tour spans with no physical venue;
they must not become six more exhibitions. Title/date and cross-year
subject audits identify34 new-event candidates, one existing Cleveland1963
Chatsworth event to extend as its documented1962–1963 tour, and one generic
Burlington Winter Exhibition1927–1928 held for catalogue disambiguation.
The existing Cleveland exact dates must survive any tour expansion.
No production changes in this reconciliation stage. See
`getty-editorial-reconciliation.json`.

### Eleven Getty image preparations

All11 selected drawings now have visually reviewed full-frame CC0 derivatives
under100,000 bytes and retained source files/manifests. Two interrupted full-size
responses were resolved using sizes explicitly advertised in Getty’s IIIF service;
these retained sources are labelled renditions rather than maximum originals.
No uploads or DB attachments yet. See `getty-ra1953-image-review.json`.

Exact-title Stag Beetle record515160f2 has Rijksmuseum accessionBC-0005016,
same1505 date and14.1×11.4cm dimensions as Getty83.GC.214. It may represent
a borrowed object; original Rijks EDM names only data provider, not owner.
Hold duplicate creation/image assignment pending direct object identity and
loan evidence. Jan Verbeeck II remains a source creator label; do not substitute
Pieter or François Verbeeck. Artist-scoped duplicate candidates are captured.

### Stag Beetle loan identity resolved and delivered

Rijksmuseum’s exactBC-0005016 record lists Crawly Creatures; its official
exhibition press text credits Getty for Dürer’s1505 drawing. Getty83.GC.214
reciprocally documents Onderkruipsels at Rijksmuseum. The matching title, maker,
date and14.1×11.4cm dimensions establish the same loaned object. Existing
artwork515160f2 is reused: one CC0 Getty image attached; erroneous accepted
Rijks holding superseded by accepted Getty holding. Original accession, title,
dates, medium, status, source identifiers and evidence remain preserved.
No duplicate artwork and no modern exhibition were added. Production holding
and public image checksum verified; real-local untouched. The other ten image
preparations and historical event release remain pending.
See `getty-stag-reconciliation-delivery.json`.

### Ten further Getty drawings delivered

The remaining ten native Getty drawings and ten reviewed CC0 primary images
are now in production, with accepted Getty holdings and nine primary artist
links. Jan Verbeeck II remains an explicit source creator label. Original
exact/circa/range dates and review statuses are retained. Recto primary views
do not imply that versos are illustrated. All ten public image checksums,
object dates, holdings and selection evidence were verified.
No real-local writes. The Stag Beetle remains its separately reconciled
existing artwork; historical exhibition links are the next pending stage.
See `getty-ten-drawings-delivery.json` and
`ops/historical_exhibitions_getty_ten_drawings_20261012.py`.

### Getty historical venues delivered

Committed34 new historical exhibitions, extended the existing Cleveland1963
Chatsworth record into its source-backed1962–1963 tour, and added49 venue
occurrences plus78 illustrated object/venue entries across35 events. Added50
artist participants, including the explicit unresolved Jan Verbeeck II label.
The reused11 artwork records already carry the verified images; this phase
adds no images or main works. All35 API detail/entry responses verified dates,
artwork IDs and images. Existing Cleveland occurrence remains byte-for-byte
unchanged, including Feb27–Mar31,1963 dates. Other dates retain source precision.
Checklists are partial and repeated venue entries are not unique artworks.
The Burlington1927–1928 winter show and its one connection remain held.
Totals10,403 active,10,217 held,35 undated. Real-local untouched. See
`getty-venue-delivery.json` and
`ops/historical_exhibitions_getty_venue_release_20261012.py`.

### Getty checklist expansion discovered

The delivered venues list41 additional native objects and154 references; all154
object/venue references are reciprocal. Medium/date review retains38 paintings
and drawings, excludes two decorative cabinet records, and holds one whole
manuscript for illustrated-leaf/object grouping review. No chronological
conflicts found among eligible references. New acquisition numbers (including
2022) are inventory dates, not artwork creation dates. The multi-creator
85.GB.218 record has attribution history; its2010 attribution period must not
replace its about1585 creation date. See `getty-checklist-expansion-discovery.json`
and `getty-checklist-expansion-scope.json`. Production expansion pending.

### Five existing Getty paintings: eight added connections

Added8 illustrated entries across7 existing historical exhibitions using5
exact Getty holding/accession matches. All eight API entries expose the correct
internal artwork and image; the five artwork records are unchanged. No new
exhibitions, works or image assets. These pre-existing paintings have no primary
artist links; source creator labels remain explicit and artist reconciliation
is pending. The rest of this expansion has33 eligible objects and138 source
connections still pending. See `getty-existing-five-delivery.json`.

### Getty expansion: image review and duplicate prevention

Prepared and visually inspected 32 full-frame primary Getty CC0 reproductions.
These assets remain in local source preparation; none has been uploaded or
attached by this stage. The Poussin 81.PA.43 image has a canvas-specific NoC-US
statement despite manifest-level CC0 and is excluded from this CC0 batch pending
separate review. See `getty-expansion-image-review.json`.

A deeper candidate audit confirmed that Getty 71.PA.15, Saint Bartholomew,
is already represented by internal artwork f78e3da8-9562-500c-bdef-c8f936ca7410
under The Apostle Bartholomew. Full composition, creator and 1661 date agree;
small source measurement differences are preserved. Reuse this existing artwork
and image for its three pending historical connections. Do not create a new
artwork from its Getty accession. Other title candidates still require review,
particularly Rubens's head studies. Detailed immutable evidence is under the
App Support checklist-expansion source directory. No production or real-local
catalogue writes occurred in this preparation stage.

### Getty checklist expansion completed: 38 works, 146 illustrated venue entries

The selected batch is delivered and verified in production: 32 new review
artworks with 32 authentic internal images, six existing artworks reused, and
146 source-backed artwork–venue entries across 24 existing historical
exhibitions. This finishes all 38 eligible paintings/drawings and all their
146 captured reciprocal references in this discovery batch. It does not assert
complete exhibition checklists or worldwide coverage. Active exhibition totals
remain 10,403, including 10,217 confirmed held events and 35 undated records.

The final audit checked exact native object/event/occurrence identities,
1600–1989 event bounds, pagination, every new entry's internal artwork/image,
and all supported artist participants through the live API. All 32 new image
assets passed public checksum verification and full-frame visual review.
New works remain in review. Source decades are ranges, about-dates retain
uncertainty, nested creator-attribution dates do not replace creation dates,
and museum holdings are not current-display claims. The real local catalogue
was not modified.

Thirty-one of the 38 works now have primary artist links, including five reused
paintings whose verified creator links were added in this pass. Seven retain
explicit labels pending duplicate/missing artist-profile resolution or
multi-creator attribution review. The five reused paintings retain their
original source-creator label fields as audit data even after receiving artist
links; consequently the receipt's raw `explicitUnlinkedCreatorWorks` field is
12, while the actual number without a primary link is seven. No artist records
were merged or invented. The two decorative cabinets remain excluded and the
whole manuscript remains held for leaf/object scope review.

Getty 81.PA.43, Poussin's Holy Family, was compared against eight candidate
reproductions and confirmed distinct. Its main canvas specifically states
No Copyright – United States; that label is preserved, alongside conflicting
manifest-level CC0 evidence, without calling its image CC0. The other 31 new
images carry object-specific Getty CC0 statements. Rembrandt 71.PA.15 reused
the existing illustrated Apostle Bartholomew record instead of creating a
duplicate. Getty/Met Carracci Triton sheets and Getty/Brussels Rubens head
studies were separately compared and are distinct objects.

Receipts: `getty-checklist-expansion-delivery.json`,
`getty-thirtyone-works-delivery.json`, `getty-thirtyone-connections-delivery.json`,
`getty-poussin-work-delivery.json`, `getty-poussin-connection-delivery.json`,
`getty-bartholomew-connections-delivery.json`, and
`getty-existing-creators-delivery.json`. Immutable source captures, derivative
files, plans and preimages remain under the established Application Support
source-metadata and backup directories. No deployment or commit was needed.

### Getty creator follow-up: five resolved links

Added and verified five primary artist links and 12 exhibition participants:
the two Pickenoy portraits, Holbein's scholar, Raphael's Saint Paul and
Nicolò dell'Abate's Saint Catherine. Getty's native person records support
these identities, including alternative names and source lifespan uncertainty.
The selected existing profiles carry museum/external identifiers; the competing
French-label profiles were preserved without merging or rewriting them. Existing
artwork metadata, images, source creator labels and status remain unchanged.
Thirty-six of this batch's 38 works now have primary artist links. See
`getty-resolved-creators-delivery.json` and the App Support `creators/` captures.

The remaining cases are Antonie Erkelens, whose Getty person record supplies
1774–1804 and needs a new profile after a broader variant-name check, and the
Carracci sheet with nested multiple-creator attribution. Neither is assigned
a fabricated or arbitrary artist identity. This resolves five of the seven
identity gaps recorded in the earlier batch receipt; that receipt remains an
immutable record of the initial delivery.

### Getty final creator cases: Erkelens and alternative Carracci attribution

Created one review artist profile, Antonie Erkelens, from Getty's native person
record, with its explicit 1774–1804 life dates and no invented biography. A
variant-name and matching-lifetime audit found no existing equivalent profile.
Linked the existing Windmills on a Canal drawing and its historical exhibition;
the live participant response and unchanged artwork record were verified.
See `getty-erkelens-delivery.json`.

The Carracci sheet's nested source description says **or Ludovico Carracci**.
Corrected its unlinked creator label and both exhibition entry labels to
**Annibale Carracci or Ludovico Carracci**, and added qualified, unlinked
participant labels to both affected exhibitions. Neither artist is presented
as confirmed or as a joint creator. The about1585 creation date, image,
holding and review status remain intact; nested 2010 attribution data does
not replace the creation date. Source evidence and previous labels are retained.
See `getty-carracci-attribution-delivery.json`.

The batch now has 37 of 38 works linked to specific artist profiles. The last
work has a faithfully represented alternative attribution, rather than an
unresolved data-processing omission. The real local catalogue remains read-only.

### Next historical lead: Rowlandson's Box-Lobby Loungers

Recorded Getty drawing 84.GG.645's catalogue histories for Royal Academy 1785,
Ellis and Smith 1948 (no.15), and Reading 1962 (no.65), plus a volume2 supplement
lead for Tate 1927–28 requiring original-page inspection. Royal Academy Summer
Exhibition 1785 already exists as 600d0b26-1995-58db-973f-4728999b5769; do not
create another event. A targeted accession/title audit found no matching original
artwork in production. No production changes were made in this research step.

The drawing must be distinguished from later etched versions. Preserve the
historical Wigstead attribution separately from Rowlandson's modern authorship;
Grego's conjectural association with an 1786 Opera House Gallery work does not
justify merging years or versions. The retired Getty Search Gateway redirects
to the Open Content FAQ and cannot supply a live native object identity.
See `getty-rowlandson-research.json` for source receipts, leads and audit data.

### Rowlandson native record and four histories verified

Resolved 84.GG.645 to Getty object 103QXP through the current collection site's
public search API, using an exact accession check. The reusable bounded resolver
is `ops/getty_selected_accession_search.py`; an unquoted accession query can
return fuzzy unrelated results and must not be accepted automatically.

The native object and activity records reciprocally confirm four historical
venues: Royal Academy 1785; Tate December1927–March1928; Ellis and Smith May1948;
and Reading March–April1962. Nine later venues are excluded. Source month/year
precision must be retained: numeric first/last days are bounds, not exact event
dates. Parent exhibition records and full source receipts are captured locally.
The original drawing's CC0 image is prepared, visually reviewed full-frame and
99,480 bytes. It has not yet been uploaded or attached to production. See
`getty-rowlandson-native-review.json`; reconciliation and delivery are next.


### Rowlandson delivery completed

Delivered Getty original drawing 84.GG.645, Box-Lobby Loungers (1785), with its
reviewed CC0 image, accepted museum holding and existing Thomas Rowlandson link.
Added three review exhibitions: Tate December1927–March1928, Ellis and Smith
May1948, and Reading March–April1962. Reused the existing Royal Academy1785
event and occurrence unchanged. All four entries expose the exact internal
artwork, image and artist; live API checks and public image checksum passed.
Source month/year precision is preserved without invented opening/closing days.
The1785 entry retains the historical title The Back of the Boxes at the Theatre,
Covent Garden. The Wigstead attribution lead remains explicit evidence rather
than a substituted modern artist attribution. Getty's1757 birth-year label is
preserved without overwriting the existing artist profile's1756. Nine modern
venues were excluded, and no later etched version was substituted.

Totals are now10,406 active exhibitions,10,220 confirmed held,35 undated.
Receipts: `getty-rowlandson-work-delivery.json` and
`getty-rowlandson-events-delivery.json`. Artwork ID:
752bd89c-f051-5032-a0a3-14e27933abdb. Real local database unchanged.
