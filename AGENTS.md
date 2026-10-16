# Artline implementation constraints

- Continuous exhibition programme (13 October 2026): the user explicitly invoked
  `docs/INFINITE_EXHIBITION_RESEARCH_PROMPT.md`. Run a separate durable exhibition
  supervisor with bounded serial workers, its own queue/checkpoints/hourly reports,
  and shared production ingestion locks. Cloud SQL and Storage plus necessary
  authentication, secret/proxy/backup/public verification are authorized. No
  Translation, deletion, commits, pushes, deployments or infrastructure changes.
  Preserve the running artwork programme unchanged. Historical exhibitions remain
  1600–1989; main-catalogue works remain through 1970 with documented exceptions.
  Arthive is an additional permitted discovery source, not a blanket image licence.
  Appropriate review states and uncertain facts stay explicit. Continue until
  stopped, subject to configured account/storage limits, with bounded backoff and
  checkpointed infrastructure holds. See `docs/research/continuous-exhibitions-20261013/`.

- Production research resumed (13 October 2026): the user explicitly instructed
  “upload to prod, I allow it” after being asked to authorize Google Cloud SQL
  and Storage only. Resume the background research programme and its validated
  production catalogue/image deliveries. This permits Google Cloud SQL,
  Cloud Storage, and the authentication, secret access, proxy, backup and
  verification calls required by the established production workflow.
  Cloud Translation remains disabled and prohibited; do not enable it or use
  other Google services unrelated to production delivery. Reconcile interrupted
  batch 107 before new writes. The real local catalogue remains read-only.
  This supersedes the stopped-job and blanket prohibition below only within
  this explicitly authorized production workflow.


- Exhibition catalogue linking (13 October 2026): the user requests at least
  1,000 iterations of 10 exhibitions, adding and linking supported creators and
  artworks created before 1980 (through 1979 for this batch). This supersedes
  the through-1970 artwork cutoff for this exhibition reconciliation only.
  Preserve source/object/version identity, qualified attributions, unknown dates,
  historical participation distinctions and review states; no fabricated links
  or repeat checks counted as new coverage. The user explicitly approved
  “Allow database services for this batch” after being asked about Google Cloud
  SQL and Secret Manager. Those database services alone are authorized for this
  batch; the separate Google-service restriction otherwise remains in force.
  The real local catalogue remains read-only. Track results in
  `docs/research/exhibition-catalogue-links-20261013/README.md`.
  The user then explicitly requested direct additions without user review.
  The assistant verifies supported records and publishes new additions directly;
  no manual approval queue. Preserve factual uncertainty and do not fabricate
  resolutions. Existing unrelated record statuses are not bulk rewritten.
  The user additionally approved “Allow this API deployment” for the tested
  direct artwork-viewer fix, authorizing Cloud Build and Cloud Run for that
  release. This does not authorize unrelated Google-service usage.
  Completed and independently verified: 1,040 full iterations plus six events
  (10,406 exhibitions), 4,199 new published artworks, 1,043 new published creators,
  7,800 artwork-entry links and 16,759 added/resolved artist connections.
  Viewer revision `artline-api-exhibition-detail-1013-v1` is live. Remaining
  source gaps are documented; do not recount completed iterations as new work.

- No Google service usage (12 October 2026): the user explicitly instructed
  “don't do that! don't use google service!” after discovering Cloud Translation
  API usage. Do not invoke Google APIs, Google Cloud services, gcloud commands,
  or Google-backed translation workflows unless the user explicitly authorizes
  that service again after this instruction. Existing credentials, enabled APIs
  and earlier task authorizations are not permission to resume usage. Do not
  disable or delete existing hosted infrastructure as an inferred action. The
  continuous research job remains stopped. Use local processing or the current
  assistant for translation; do not substitute another paid service silently.


- Museum of Russian Impressionism exception (12 October 2026): the user
  explicitly answered “Include this museum’s exhibitions” and “Include all
  dated museum artworks”. These museum-specific exceptions supersede the
  1989 exhibition and 1970 artwork cutoffs for this delivery only. Retain
  photography/sculpture exclusions. Production now includes all 68 pictorial
  objects in the public collection index: 67 new review artworks and one
  existing Yuon match, 41 artists (23 new), and 68 authentic museum images.
  Five collection works postdate 1970. Fifty exhibitions/special projects are
  delivered: 48 held or underway and two announced; one has unresolved years.
  Seventy-four illustrated documentary entries include three exact collection
  links; 71 borrowed/source objects remain outside the main catalogue and are
  not assigned museum holdings. There are 71 additional exhibition images,
  nine canonical exhibition artist connections, and 26 documentary objects
  with exact creator links. Public checklists remain partial. Four offsite
  projects retain their actual hosts. Keep source conflicts, unknown image
  rights, review states and the existing Yuon primary image. The general
  timeline cutoff remains separate; museum gallery queries include all 68.
  The real local database remains read-only. No Cloud SQL backups created.
  See `docs/research/russian-impressionism-museum-20261012/README.md`.

- Historical exhibition correction (12 October 2026): the user stopped the
  recent-exhibition direction and requested historical exhibitions from 1600
  through 1989, excluding photography and sculpture. Stop the 700-event
  2020–2025 deployment; its production builds were cancelled before release
  and its research objects were not imported. Audit and remove out-of-scope
  exhibition records, then research old catalogues, books and web archives.
  Keep paintings, drawings, prints and icons. The user confirmed main-catalogue
  deletion is limited to recent selected museum additions, not the entire
  photography/sculpture corpus. Remove those photographs and source-confirmed
  modern sculptures; preserve unrelated older and uncertain records. Delete
  Cloud SQL backups only, keeping local backups and database exports.
  Preserve source research and the real local catalogue read-only rule.
  Cleanup is committed: 100,795 date-excluded and 620 medium-excluded events,
  546 reviewed recent museum artworks, and all 170 existing Cloud SQL backups.
  The first historical batch adds 1,547 review events; checklist completion and
  worldwide coverage remain ongoing. The 1769 Royal Academy continuation has
  reviewed all 136 catalogue numbers: 119 entries retained, 11 non-pictorial
  exclusions, six unresolved designs, and three illustrated exact-work links.
  One of those links adds West's RCIN 405416 as a new illustrated review work.
  The Berlin Academy continuation adds 163 historical events from 218 reviewed
  bibliography rows, with 183 publication references and 18 artist connections.
  It adds no artwork entries or images; catalogue contents remain outstanding.
  Historical campaign additions now total 1,710 events; production has 9,282
  active exhibitions, including 154 undated legacy records, at verification.
  The Cleveland continuation attaches 234 verified images to existing works
  (187 paintings, 47 prints), illustrating 506 existing connections across 88
  historical exhibitions. It adds no events, artworks or participation claims.
  Eleven closed covers and four calligraphy-only primary views remain held;
  five source-dimension discrepancies were individually reviewed and recovered.
  Original Academy minutes now support four additional Paris events in 1664,
  1667, 1669 and 1671, with eight documented prize paintings and two named
  artists; exact surviving-object/image matches remain unresolved. Historical
  campaign additions total 1,714 events. Review of the 154 undated legacy rows
  removed 97 source-dated modern events, four excluded-medium exhibitions and
  four empty duplicate/sample records, and recovered 15 explicit historical
  years. Production now has 9,181 active events, 34 still undated. Original
  source periods, date conflicts and held records remain preserved; this pass
  made no further main-artwork deletions or real local database writes.
  The Byzantine continuation adds two anonymous painted leaves, dated
  1057–1063, with two full-frame museum images and 13 exact existing entry
  links across nine shows. The 1989 Cleveland-only Holy Image, Holy Space row
  was removed after museum sources established its full 1988–1990 tour,
  including Richmond in April 1990. Production now has 9,180 active events,
  8,996 confirmed held and 34 undated; historical additions remain 1,714.
  The 1931 Phanar Gospel reference does not securely identify the detached
  Luke/Matthew leaves. European Byzantine tour identities remain under review.
  The existing Whistler's Mother painting now links to Royal Academy 1872,
  Paris Salon 1883 and Cleveland 1933, with three artist connections. Its
  missing type/medium are resolved; image, dates, holding and review status
  remain unchanged. Its current WikiArt reproduction is cropped and remains
  a recorded full-image gap. The similarly titled drypoint is a separate work.
  Chicago 1933 now has 221 linked artworks, 152 illustrated: this continuation
  adds 220 entries, 108 artist connections, one original catalogue reference and
  five reviewed WikiArt images, without creating events or main-catalogue works.
  Museum object histories are matched by native ID and accession; three wrong
  catalogue numbers were corrected against the original scan. Benton's 1945
  Cotton Pickers and Henri's merely discussed Himself remain unlinked. The
  1934 exhibition is distinct. Full catalogue OCR remains unreviewed; 134 native
  objects need further reconciliation and 69 linked works still need pictures.
  Museum publications and image routes are held after HTTP 403; the independent
  University of Illinois scan and approved WikiArt sources remain usable.
  The official AIC archive also yields 819 additional historical review events,
  plus a Chicago occurrence for the existing Seurat 1958 tour. There are 121
  new exact artwork links across 22 events, 74 already illustrated, and 55
  canonical artist connections (54 new rows and one existing Seurat label
  reconciled). No new main artworks or images were created in this archive pass.
  Production has 9,999 active events, 9,815 confirmed held and 34 undated;
  historical campaign additions total 2,533. Original checklists remain partial
  or unknown. Five event date conflicts retain years but withhold disputed day
  fields; tours, duplicate source records, long date ranges and unmatched image
  versions remain recorded review gaps. See the AIC section in the research log.
  The NGA open object-history continuation adds 132 historical review events,
  enriches 13 existing exhibitions and adds 3,238 exact connections to 2,435
  existing artworks. Of these, 2,879 connections are already illustrated;
  359 connections covering 319 works still need images. It adds 1,108 artist
  connections across 520 existing artists, with no new main artworks, artists
  or images. Production has 10,131 active events, 9,947 confirmed held and
  34 undated; historical campaign additions total 2,665. All new links and
  image availability were checked through the API. Native IDs, accessions,
  recto/verso distinctions, limited display periods and title aliases were
  reviewed; 511 unmatched object histories and unresolved event identities
  remain held. Original checklists remain partial, and unknown closing years
  remain unknown. See `nga-histories-delivery.json` in the research directory.
  Philadelphia's Free Library Whistler exhibition of 1931 now adds one event
  with 390 illustrated exact-work connections (379 prints and 11 drawings),
  two artist connections and one bibliographic catalogue reference. Beatrix's
  two after-Whistler impressions retain her attribution. Eleven unmatched
  native objects remain held; autograph letters are excluded. All 390 image
  assets returned HTTP 200. No main artwork/image records were changed.
  Production has 10,132 active events, 9,948 confirmed held and 34 undated;
  historical campaign additions total 2,666. The original checklist and exact
  dates remain incomplete. Library access is held after HTTP 403.
  One residual Cleveland 1932 Cotton Textile Institute display was then removed
  as textile-only, with no main artwork deletions. Production is 10,131 active,
  9,947 confirmed held and 34 undated; campaign additions remain 2,666. Original
  Carnegie Mellon newspaper/bulletin scans now support the Carnegie 1933
  Rosenwald exhibition dates, 6 April–21 May; its object delivery is pending.
  Carnegie 1933 is subsequently delivered with 201 exact print connections,
  177 verified public image assets, 94 artist connections and three original
  periodical references. Grouped catalogue numbers retain independent sheet
  identities; after-model relationships do not replace printmaker authorship.
  There are 39 unmatched native objects and 24 image gaps. No main artworks,
  artists or images were created or changed. Production has 10,132 active
  exhibitions, 9,948 confirmed held and 34 undated; campaign additions are
  2,667. Its original checklist remains partial.
  The Moscow 1913 continuation adds one year-dated event and 11 catalogued
  painted-icon entries from selected RSL public text-layer pages, with one
  publication and nine source records. All entries are API-verified but have
  no canonical artwork/image links yet. Individual artists, exact dates and
  venue remain unknown; historical catalogue attributions are preserved as
  historical labels. This is a partial checklist and not a visual scan review.
  Production totals are 10,133 active, 9,949 held and 34 undated; historical
  campaign additions are 2,668. No main-catalogue or real-local writes occurred.
  Philadelphia Art Alliance 1930 adds one event with 190 existing-work links
  (186 prints, four drawings), 180 verified internal images and a BnF catalogue
  reference. Three objects remain unmatched; ten links lack images. Studio and
  joint source labels are preserved; the six-page checklist and relation to the
  Pennsylvania Museum show remain open. Production has 10,134 active events,
  9,950 held and 34 undated; campaign additions total 2,669. Main artworks and
  the real local DB are unchanged. A Philadelphia Museum archive discovery
  captures 871 folder leads, not confirmed exhibitions, requiring reconciliation.
  The first PMA archive wave subsequently adds 18 explicitly dated painting,
  drawing and print events from the first 100 folders, with all API details
  verified. It adds no entries/images/artists; 15 object-history candidates
  remain unlinked. Production has 10,152 active, 9,968 held and 34 undated
  records; campaign additions total 2,687. Exact folder-source evidence and
  unresolved compound/mixed/proposed events remain preserved.
  Two subsequent exact-object links connect Pascin's Rape of Europa to Speiser
  1934 no. 50 and Gauguin's Words of the Devil to Post-Impressionists 1935.
  Both artist connections and API entries are verified; Gauguin's existing
  internal image is verified, Pascin remains unillustrated. Two checklists
  become partial. Twelve Piranesi histories and one Vlaminck history remain
  unlinked; no main artwork or image records were changed.
  PMA archive wave two adds six dated 1937–1954 exhibitions, no entries or
  images. All API details verified. The Toulouse-Lautrec 1955 candidate was
  excluded before writing because its exact Philadelphia stop already exists
  with Chicago in the touring event. Production has 10,158 active events,
  9,974 held and 34 undated; campaign additions total 2,693. Conflicting dates
  and the mixed circulating Russian Arts exhibition remain under research.
  The existing Toulouse-Lautrec 1955–1956 tour now has 21 additional exact
  NGA artwork links, all with verified internal images, attached to the
  Philadelphia occurrence. Its previous Laundress entry remains (22 total);
  dates, tour occurrences and main artworks are unchanged. One artist link
  added; one after-Toulouse print remains unmatched. Checklist remains partial.
  No new events, image files or real-local database writes occurred.
  Philadelphia Masters of Spanish Painting 1937 now has four illustrated
  exact-work links, including Goulandris's Veil of Saint Veronica and three
  NGA paintings. All links and image assets verified; native IDs and source
  creator labels retained. Checklist becomes partial; event dates and main
  artworks are unchanged. No new image or canonical artist records created.
  Blake Philadelphia 1939 now has four illustrated exact NGA object links
  (catalogue nos. 148, 173, 175, 204) and the original catalogue reference;
  all API links and images verified. Nos. 173 and 174 remain distinct versions.
  Four OCR-missed headings recovered visually; 182 was not found in inspected
  pages and was not invented. Checklist remains partial; main records untouched.
  A subsequent original-catalogue review adds 24 catalogued paintings/drawings
  from nos. 151–176, excluding existing 173/175. Blake 1939 now has 28 entries,
  four illustrated; all API entries verified. New rows retain historical labels
  and distinct versions but have no canonical artwork/image matches yet. Main
  artwork and real-local records remain unchanged; checklist is still partial.
  Subsequent Cleveland reconciliation securely links no. 155, St. Matthew,
  using native ID 294155/accession 2017.4, explicit 1939 catalogue citation
  and matching Emerson provenance. Blake now has five illustrated entries
  among 28; API and image asset verified. Historical labels are preserved.
  A third PMA archive cohort adds nine dated 1959–1964 exhibitions plus two
  exact illustrated NGA objects and artist connections (Courbet and Cassatt).
  Production now has 10,167 active events, 9,983 held, 34 undated; campaign
  additions total 2,702. Potential tours and mixed-media shows remain held
  for reconciliation. Full checklists remain incomplete; main artworks and
  the real local database were unchanged. All additions and assets verified.
  A fourth PMA cohort adds ten 1964–1970 events and 15 illustrated print links
  to Master E.S. 1967. Other makers and follower attributions remain explicit;
  two unmatched objects, including a facsimile, are held. Production now has
  10,177 active events, 9,993 held and 34 undated; campaign additions 2,712.
  Main artworks/local DB unchanged; events, links and all 15 assets verified.
  Existing Manet 1966–1967 and Romantic Art 1968 tours gain seven and three
  illustrated NGA links respectively (nine/five total entries). The Dead
  Toreador is Philadelphia-only; other new links remain tour-level. Five
  unmatched impressions are held. All ten assets/API links verified; event
  dates, occurrences, prior entries, main artworks and local DB unchanged.
  Fifth PMA cohort: eight dated 1971–1981 events and seven illustrated
  Gauguin monotype links. A related verso shares catalogue no. 64 and is
  not counted as another artwork. Production now has 10,185 active events,
  10,001 held and 34 undated; campaign additions total 2,720. All eight
  details and seven images verified; main artworks and local DB unchanged.
  Washington Sears galleries 1932 adds one year-only Rembrandt exhibition,
  185 exact print links, 175 verified images and one artist connection.
  Three native impressions remain unmatched; studio/joint labels preserved.
  All entries/paging/assets verified; main artworks/local DB unchanged.
  Production: 10,186 active events, 10,002 held, 34 undated; campaign 2,721.
  PMA final inventory title review is recorded; fiscal accounts and rejected
  proposals are not imported as held shows. Full historical coverage pending.
  Chicago First Century of Printmaking (30 Jan–2 Mar 1941) adds 126 exact
  NGA print entries, 111 verified images, 17 artist links and a bibliographic
  catalogue record. Anonymous/qualified creators preserved; seven objects
  unmatched. Full catalogue unread. All links/assets checked; local and main
  artwork records unchanged. Production: 10,187 active, 10,003 held, 34 undated;
  historical campaign additions 2,722.
  Six regional NGA-history exhibitions (Indianapolis, Peoria, Ithaca,
  Baltimore, Baton Rouge, Notre Dame; 1929–1973) add 379 exact artwork
  entries, 366 illustrated connections and 124 artist connections. All
  links and 335 distinct assets verified. One repeated source history
  deduplicated; 66 unmatched histories held; missing dates/numbers explicit.
  No main-artwork or real-local writes. Production: 10,193 active events,
  10,009 held, 34 undated; campaign additions 2,728. Checklists partial.
  Regional second cohort adds five events (1931–1967), 261 entries, 237
  illustrated and 44 artist connections. All links/234 assets verified;
  48 source histories unmatched. Main/local records unchanged. Production:
  10,198 active, 10,014 held, 34 undated; campaign additions 2,733. Historical
  Los Angeles venue identity and exact dates remain explicit unknowns;
  1947 Hals/Rembrandt painting-title versus print/drawing lead held.
  Third regional cohort: six 1956–1970 exhibitions, 260 entries, 251
  illustrated and 38 artist connections. Ten histories unmatched; exact
  dates/full checklists pending. All API links/247 assets verified; main
  artwork and local records unchanged. Production: 10,204 active, 10,020
  held, 34 undated; historical campaign additions 2,739.
  Fourth regional cohort: five events, 189 entries, 185 illustrated and
  28 artist connections; all entries/180 assets verified. Eleven histories
  unmatched. Princeton institution conflict, exact dates and complete
  checklists pending. Main/local records unchanged. Production: 10,209
  active, 10,025 held, 34 undated; historical campaign additions 2,744.
  International collection cohort adds London 1987, San Francisco 1961,
  Mexico City 1945 and Turin 1968: 178 entries, 166 illustrated and 88
  artist connections. All links/assets and country labels verified; 28
  histories unmatched. Turin institution conflict unresolved; historical
  venue retained. Main/local records unchanged. Production: 10,213 active,
  10,029 held, 34 undated; historical campaign additions 2,748.
  1986 NGA Impressionist Soviet tour adds one event/two historical venues,
  37 paintings, 34 illustrated and 20 artist links. Leningrad/Moscow and
  Soviet Union labels retained; dates unknown; entries tour-level. Pushkin
  institution conflict unresolved. All links/34 images verified; main/local
  records unchanged. Production: 10,214 active, 10,030 held, 34 undated;
  campaign additions 2,749. Full tour checklist remains incomplete.
  Venice–Milan NGA Impressionists 1989 adds one tour/two venues, 45 painting
  links, 43 images and 19 artist connections. Unnumbered catalogue and
  tour-level participation retained. Exact stop dates have conflicting
  leads; no dates invented. All entries/venues/assets verified; main/local
  records unchanged. Production: 10,215 active, 10,031 held, 34 undated;
  campaign additions 2,750. Full catalogue and two image gaps remain.
  Corcoran cohort: six 1940–1981 shows, 172 entries, 170 illustrated and
  42 artist links. All entries/109 distinct assets verified; three objects
  unmatched and two cut-paper works held. Recurring Hassam shows retain
  separate years; historical Corcoran venue not equated with current holdings.
  Main/local records unchanged. Production: 10,221 active, 10,037 held,
  34 undated; campaign additions 2,756. Dates/checklists remain partial.
  Corcoran second cohort adds five shows, 185 entries, 134 illustrated and
  90 artist links. All entries/129 assets verified; 15 histories unmatched.
  Existing 1966 Past and Present is not duplicated; exact enrichment lead
  saved. Main/local records unchanged. Production: 10,226 active, 10,042
  held, 34 undated; campaign additions 2,761. Full coverage remains pending.
  Existing Corcoran Past and Present 1966 now has 35 entries: 34 new NGA
  painting links, 31 illustrated and 28 artist connections. All verified;
  original Cleveland entry, dates, occurrence and main artwork records
  preserved. One source object unmatched. No new event or real-local writes.
  Unpublished/unnumbered checklist evidence retained; completeness pending.
  Fifth regional cohort adds six shows, 179 entries, 173 illustrated and
  50 artist links. All entries/170 distinct assets verified; 12 histories
  unmatched. Pasadena historical identity retained; no current museum
  succession assumed. Main/local records unchanged. Production: 10,232
  active, 10,048 held, 34 undated; campaign additions 2,767. Full coverage pending.
  Catlin Brussels 1870 and New York 1871 add two events and 60 illustrated
  painting connections (31 distinct image assets), all verified. Brussels
  venue variants reconciled; original labels/numbers retained. Smithsonian
  1872 display remains a lead. Main/local records unchanged. Production:
  10,234 active, 10,050 held, 34 undated; campaign additions 2,769.
  The Manet 1867/1884 and Stuart 1880 continuation adds three events, 22
  illustrated painting entries and four artist connections; 20 distinct existing
  assets verified. Current von Breda attribution is preserved for the Stuart-show
  portrait; source 42as is catalogue 42, not 42a. Exact dates and full checklists
  remain unresolved. No main artwork/image additions or real-local writes.
  Latest totals: 10,237 active, 10,053 held, 34 undated; campaign additions 2,772.
  The Lawrence 1836 fifth/sixth and Washington 1853/1857 continuation adds four
  events, 22 illustrated entries and eight artist connections; 17 distinct assets
  verified. One source object remains unmatched; full checklists and exact dates
  unresolved. No main artwork/image additions or real-local writes.
  Latest totals: 10,241 active, 10,057 held, 34 undated; campaign additions 2,776.
  Manchester Art Treasures 1857 adds one reconciled event with 20 illustrated
  entries and 14 artist connections; all assets verified. Catalogue sections
  are one event; triptych reverse surfaces are not separate entries. Original
  catalogue OCR captured; full transcription and exact dates remain open.
  No main artwork/image additions or real-local writes. Latest totals: 10,242
  active, 10,058 held, 34 undated; campaign additions 2,777.
  Nineteenth-century wave 3 adds nine events, 38 illustrated artwork entries
  and nine artist connections; 31 distinct assets verified. Cassatt/Morisot,
  Ingres/Corot, Grosvenor and early New York histories retain historical labels.
  Exact dates/checklists and three honorific-name artist matches remain open;
  no main artwork/image additions or real-local writes. Latest totals: 10,251
  active, 10,067 held, 34 undated; campaign additions 2,786.
  Van Dyck honorific reconciliation adds one verified participant connection to
  Grosvenor 1887; the three previous name holds are resolved. Fitzwilliam discovery
  captures 3,231 reference URLs over 65 pages and 42 selected JSON details;
  none imported yet. Loans, medium/date conflicts, modern dates and duplicate
  events need review. PEIB Manchester references are photography, excluded.
  Event totals unchanged; no main catalogue or real-local writes.
  Fitzwilliam five-show Rembrandt review captures 235 reciprocal exhibition/object
  connections across 105 distinct prints, none matched by current native IDs.
  Preserve posthumous/reworked qualifications on 48135/81182 and five explicit
  creation ranges. Original month dates conflict with derived fields for 1966
  and 1969; venue/duplicate review and import remain outstanding. No production
  additions in this discovery pass; see fitzwilliam-rembrandt-discovery.json.
  The subsequent Fitzwilliam release adds five Cambridge events with 235 exact
  native-impression entries and five artist connections, all API-verified.
  1966/1969 retain month precision; venue institution unresolved. Plate dates and
  reworked impressions remain qualified. Entries are unillustrated and not yet
  linked to main artworks; original checklist completeness remains unresolved.
  No main artwork/image additions or real-local writes. Latest totals: 10,256
  active, 10,072 held, 34 undated; campaign additions 2,791.
  Fitzwilliam catalogue integration adds 105 reviewed native print impressions,
  105 supported holdings and 103 unqualified Rembrandt artist links, attaching
  all 235 exhibition entries to internal works. Two reworked/posthumous prints
  retain qualified creator labels and unknown impression dates. All API links
  verified; no images added, no real-local writes. Exhibition totals unchanged.
  See fitzwilliam-print-catalogue-delivery.json; same-impression images remain open.
  Further Fitzwilliam discovery captures 537 pictorial-medium title details:
  306 historical-date candidates, 114 outside scope, 117 date-unresolved and
  72 date-field conflicts. Six exact title/year existing-event leads require
  venue/tour reconciliation; source duplicate pairs are tracked. No imports in
  this expansion. Commons AD.12.39-14 is a candidate for native 46647 only;
  other same-title accessions are not interchangeable. Image/access holds remain.
  Early London continuation adds Turner 1833, Lawrence tenth 1836 and medieval
  paintings 1896: three events, five documented entries, two existing main-work
  links; all API-verified, currently unillustrated. Recto/verso and shared panel
  numbering retained. No new main works/images or real-local writes. Latest
  totals: 10,259 active, 10,075 held, 34 undated; campaign additions 2,794.
  Fitzwilliam pair review supports one Ruskin/Turner London1878 candidate from
  references1110/1117; source catalogue numbers2/14/119 retained. Tonbridge native
  13896 has a Turner/Girtin attribution conflict; no forced artist link. Steer
  1894 pair975/985 remains unresolved. Production duplicate query recovered after
  transient DNS failure, no matching events found; no writes in this pass.
  The subsequent Ruskin1878 release adds one reconciled event and three drawing
  entries, both source event aliases retained. All API identities verified;
  Turner/Girtin conflict explicit, internal images/work links still unresolved.
  No main catalogue or real-local writes. Latest totals: 10,260 active,
  10,076 held, 34 undated; campaign additions 2,795.
  Cambridge drawing discovery captures25 references,942 reciprocal object links
  and748 unique objects:618 drawings,93 prints,21 paintings/miniatures and16 bound
  volumes held for leaf review.470 have no creation-date field. One exact native
  catalogue match;1959/1960 title variants need reconciliation. No imports or
  real-local writes in this pass; see fitzwilliam-cambridge-drawings-discovery.json.
  See
  `docs/research/historical-exhibitions-20261012/README.md`.

- Exhibition deployment (12 October 2026): the user explicitly requested
  “nice, deploy it” after accepting the 700-exhibition gallery. Deploy its
  reviewed images, exact object connections, production persistence and UI.
  This supersedes the local-only restriction for this accepted delivery.
  Keep the real local database read-only; preserve main-catalogue date scope,
  source/rights evidence, review statuses and participation distinctions.
  See `docs/research/exhibitions-gallery-20261012/README.md`.

- Exhibition pictures and navigation (12 October 2026): the user clarified
  “Exhibited artwork images first”, and requests missing pictures in our system
  with no external links. Lead exhibition pages with authentic full-frame work
  images, keep navigation in the Artline catalogue, and preserve source URLs,
  actual rights labels and image receipts in the underlying evidence. Continue
  the local 700-exhibition preview; do not deploy or write to either catalogue
  database. See `docs/research/exhibition-images-local-20261012/README.md`.

- Exhibition artwork connections (12 October 2026): the user asks to add the
  artworks exhibited in each exhibition. Continue within the local 700-event
  review: exact source object identities, local artwork pages and bidirectional
  exhibition links. Distinguish object-history participation from public-list
  entries; do not infer physical installation or every touring stop. Preserve
  edition/version identities and source evidence. No production or real local
  catalogue writes for this continuation. See
  `docs/research/exhibition-artworks-local-20261012/README.md`.

- Local exhibition review (11 October 2026): the user requests Exhibitions in
  the account menu, a UI/UX rework, and 500–1,000 richer exhibition records to
  inspect locally. Keep this continuation local: no production writes or
  deployment, and no writes to the real local catalogue. Source-backed research
  files live under Application Support/Artline/source-metadata. Preserve exact
  artist/object identities and distinguish a complete public online list from
  a certified final exhibition checklist. See
  `docs/research/exhibitions-deep-local-20261011/README.md`.

- Exhibition target (11 October 2026): after approving the source guide, the
  user explicitly requested adding 100,000 exhibitions. This authorizes
  source-backed production exhibition ingestion and its necessary schema work.
  Research all years and support exhibitions without museums. Preserve source
  identifiers, date precision, historical venue labels, qualified attributions
  and unresolved checklist entries; distinguish artwork participation from
  ownership/current display. Count distinct documented exhibitions, reconciling
  source duplicates and touring stops; do not count books, entries, reviews or
  planned/cancelled events as completed exhibitions. Existing artwork scope
  remains separate. The real local catalogue remains read-only. See
  `docs/exhibition-sources.md` and `docs/research/exhibitions-100k-20261011/`.

- Continued illustrated expansion (11 October 2026): the user instructs
  “ok, go ahead find more and more”. Continue source-backed production artworks
  and authentic images, beginning with fresh reconciliation of the 188 reviewed
  French reserve prints and a selected American printmaking survey, 1800–1970.
  The 188 reserve works and their images are now delivered and verified.
  The American batch subsequently delivered 2,369 new review artworks and
  2,369 verified primary images across 578 artists (170 new), all within the
  supported 1800–1970 scope. This continuation totals 2,557 new illustrated
  works; earlier Soviet and French deliveries do not count toward that total.
  Three source-dated ca. 1935 Gavarni prints retain added physical-date review
  citations; their dates and review state are unchanged.
  Prior deliveries never count as new additions. Preserve date-boundary review,
  actual source labels, qualified creator and impression identities, provider
  holds and review status. The real local database remains read-only. See
  `docs/research/printmaking-continuation-20261011/README.md` and
  `docs/research/american-printmaking-20261011/README.md`.

- Further topic expansion (11 October 2026): after the 2,500-work Soviet Realism
  delivery, the user requested another assistant-selected topic covered in the
  same way, followed by further additions. Continue selected source-backed
  production artworks and authentic images, retaining the through-1970 cutoff,
  exact object/version checks, source labels, review state and provider holds.
  The current topic is French printmaking, beginning with nineteenth-century
  works and extending through 1970, an editorial subject survey rather than
  a new movement classification. This batch delivered 3,002 new production
  review artworks and 3,002 verified primary images across 248 artists (31 new).
  Exactly 3,000 works meet creation-date criteria; two source-dated “ca. 1970”
  records remain explicitly flagged for date review and are excluded from that
  minimum. Its 188 prepared reserve works were subsequently delivered by the
  separately recorded continuation, bringing French printmaking to 3,190 works.
  The real local database remains read-only. See
  `docs/research/french-printmaking-20261011/README.md`.

- Illustrated-artwork target (11 October 2026): the user requests at least
  300,000 illustrated artworks and asks to find pictures. Continue selected
  production primary-image enrichment of existing catalogue gaps, using exact
  native museum object/image identities and verified WikiArt matches. Count
  distinct active artwork records with usable primary media; alternate pictures
  and already illustrated records do not advance the target. Preserve source
  labels, credits, unknown fields, object/version distinctions, provider holds,
  existing date scope and review states. Technical checks cover every file;
  record visual samples and individually review flagged cases without claiming
  that unsampled files were viewed. The real local catalogue remains read-only.
  See `docs/research/illustrated-300k-20261011/README.md`.

- South America minimum (11 October 2026): the user requested coverage across
  all South America and at least 1,000 additional artworks. This batch delivered
  1,057 distinct new production review artworks: 1,056 across all twelve
  independent countries and one in French Guiana. An existing Venezuelan work
  received a documented museum link and one verified primary image; it is not
  counted as new. All 1,057 new works still have image gaps, and nationwide
  museum holdings coverage remains incomplete. Preserve the directory and
  object-source ledgers, exact inventory/version identity, qualified creators,
  date/loan/casting ambiguities, actual rights evidence and provider holds.
  The real local database remains read-only. See
  `docs/research/south-america-1000-20261011/README.md`.

- Soviet Realism (11 October 2026): the user requests adding this movement and
  2,000–3,000 eligible artworks, with all selected authentic images approved
  regardless of source rights labels. This batch delivered 2,500 new production
  review artworks and 2,500 verified primary images (1,876 SOVCOM / 624 Socrealizm),
  spanning 1918–1970 and 448 artists (426 new / 22 existing).
  Research the Soviet tradition of Socialist
  Realism, preserve object-level movement evidence, the through-1970 creation
  cutoff, exact object/version reconciliation and review status. This batch's
  image approval includes eligible 1956–1970 works; preserve actual rights labels
  and credits separately from user approval. Do not infer movement from Soviet
  nationality alone, fabricate museum holdings, or bypass provider access holds.
  The real local database remains read-only. See
  `docs/research/soviet-realism-20261011/README.md`.

- Additional 1,000 artworks for Switzerland and the Southern Cone (11 October
  2026): the user explicitly requested 1,000 new artworks and images across
  Switzerland, Argentina, Uruguay and Paraguay. This batch delivered 1,000 new
  production review records (900/35/50/15) and 98 verified primary images;
  902 image gaps remain explicit. Earlier additions do not count toward this
  batch. Continue exact object/version reconciliation and authentic source
  images without bypassing recorded provider access holds. Preserve separate
  India work and all date, attribution, rights and review safeguards. The real
  local database remains read-only. See
  `docs/research/switzerland-southern-cone-1000-20261011/README.md`.

- India production minimum (11 October 2026): the user now explicitly instructs
  “go ahead with India, add at least 300 artworks.” Resume India immediately for
  at least 300 new, distinct, source-backed production artworks, retaining the
  broad museum coverage preference. This supersedes deferral of India for this
  task; preserve the separate Southern Cone continuation. Existing date,
  attribution, version, source/image and review safeguards apply. Existing
  records enriched do not count toward the 300 new-artwork minimum. The real
  local catalogue remains read-only. See
  `docs/research/india-300-artworks-20261011/README.md`.

- Switzerland, Argentina, Uruguay and Paraguay (11 October 2026): the latest
  user instruction sets nationwide museum coverage in that order. Continue
  Switzerland first, then Argentina, Uruguay and Paraguay; this sequence takes
  priority over the earlier India continuation. Reuse completed Swiss research
  without treating directory coverage as artwork coverage. Reconcile national
  directories, institution identities and individual objects; deliver supported
  production catalogue records, holdings and approved authentic images, with
  every unresolved institution/object-source gap recorded. Preserve all existing
  date, attribution, version, source/image and review safeguards. The real local
  database remains read-only. See
  `docs/research/switzerland-southern-cone-museums-20261011/README.md`.

- Switzerland then India museum coverage (11 October 2026): the user requests
  nationwide museum coverage in that order, with broad coverage first and deeper
  collections afterward. Reconcile national directories and
  existing institutions, then add supported production artworks, museum links
  and authentic images under the existing source and image policies. Track
  every researched institution and unresolved object-source gap; directory
  entries are not artwork coverage. Preserve review status, unknown dates,
  qualified attributions, object/version identity and the distinction between
  holdings and current display. Do not invent works for empty museums. The real
  local database remains read-only. See
  `docs/research/switzerland-india-museums-20261011/README.md`.

- Million-artwork goal (10 October 2026): the user explicitly requests continued
  production expansion of painters, artworks and authentic images until the
  catalogue reaches one million artworks. This authorizes source-backed bulk
  catalogue ingestion toward that goal. Continue metadata selection, duplicate
  and version reconciliation, source/date/attribution checks, review status,
  selected image preparation and verification; do not inflate totals with
  placeholders or duplicate objects. Existing date scope and image policies
  still apply. The real local database remains read-only. This is an actual
  catalogue goal; the separate ten-million-row figure remains capacity headroom.

- Member access and bookmarks (10 October 2026): the user clarified that artist
  and individual artwork pages are public without a login prompt. Museum
  browsing and saving artists/artworks to private bookmarks require login.
  Prompt when a signed-out visitor uses a star or a museum link; retain the
  selected destination through sign-in. Local-debug bookmarks are ephemeral
  and must not write account, session, bookmark or catalogue fixtures to the
  real local database. Publication status is unrelated to this access policy.

- Unified catalogue (8 October 2026): the user explicitly removed the
  research/review browsing distinction: “Always show all that we have.” All
  active records are available through one catalogue, regardless of legacy
  draft/review/published status. Remove preview flags, status-based visibility
  gates and the `catalogue=all` option. This supersedes earlier instructions
  that required publication before visibility or search eligibility. Preserve
  historical statuses as audit data, archived exclusions, factual uncertainty,
  source/image evidence, date-scope rules and unrelated member access controls.
  Do not bulk rewrite statuses or mutate the real local database for this work.

- Greek museum coverage (8 October 2026): the user instructed “let's cover all
  greek museums and upload pictures and artworks.” Continue nationwide research,
  selected source-backed production catalogue additions, museum links and authentic
  image delivery under the existing Greek museum/artist and WikiArt policies.
  Keep new artworks in review, unknown dates and qualified creator labels explicit,
  reconcile object/version duplicates, and distinguish holdings from current display.
  Do not create placeholder artworks to make a museum visible. Track every researched
  institution and remaining object-source gaps; directory coverage is not complete
  artwork coverage. The real local catalogue remains read-only for this pass.
  See `docs/research/greek-museums-20261008/README.md`.

- Museum browsing (8 October 2026): the user requests supported collection
  additions where possible and asks not to show museums with no catalogue items.
  Require at least one visible artwork for museum browsing, counts and choices;
  keep empty institution records for research. Anonymous, undated and unillustrated
  review works still count. Do not invent items just to make a museum visible.
  See `docs/research/nonempty-museums-20261008/README.md`.

- Local image delivery (7 October 2026): the user instructed “I don't want to
  approve, just uplaod them.” Complete matching, image review, local file
  preparation and database attachments directly; do not request per-image or
  batch approval. The assistant resolves research decisions within the existing
  source policies and preserves artwork/version identity, source labels,
  catalogue metadata and publication state. See `docs/ARTLINE_IMAGE_USE.md`.

- Museum matching confidence (6 October 2026): the user accepts museum
  assignments at at least 80% editorial confidence and asks the assistant to
  verify and decide, including the 1,617 leads from the first random-5,000 pass.
  Apply supported production museum links without requesting manual review of
  each match. Record the evidence, confidence basis and remaining uncertainty;
  confidence is an editorial assessment, not a calibrated probability. Preserve
  object/version checks, actual source labels, dates, images and publication
  states. Holdings remain distinct from current display. This applies to museum
  matching and does not change the separate image-matching threshold.

- Le Havre, Rouen and Cyprus collection request (6 October 2026): the user
  instructed “check havre museum and ruan museums and cyprus museums, find and
  upload data.” This authorizes selected, source-backed production catalogue
  additions and enrichment for this museum pass. Keep artworks in review,
  preserve unknown fields and qualified creator labels, reconcile duplicate
  object identities, and distinguish documented holdings from current display.
  Continue the existing WikiArt and Cyprus image-source approvals. See
  `docs/research/havre-rouen-cyprus-20261006/README.md`.

- Louvre painter-link continuation (6 October 2026): the user instructed
  “go ahead link more painters.” Reconcile supplied unlinked creator labels
  with verified existing painter records and WikiArt profiles using exact
  object/creator evidence. Preserve original labels in citations and audit
  history, qualified attributions, existing images, dates, holdings and review
  status. Record unresolved identities and duplicate painter conflicts. See
  `docs/research/louvre-painter-links-20261006/README.md`.

- WikiArt source approval (6 October 2026): the user explicitly confirms that
  WikiArt is a good source from all policy perspectives. Treat WikiArt as an
  approved source across Artline's collection, image-use, rights-review and
  public/commercial-display policies. Independent source/rights clearance or a
  missing public-domain label must not by itself block selected WikiArt images
  or prompt repeated approval requests. Preserve actual rights labels, credits
  and source evidence; record user approval separately. Continue artwork/version
  identity, catalogue-scope and review/publication checks. This instruction
  supersedes earlier project policy holds on WikiArt source acceptance. See
  `docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026`.

- WikiArt image-enrichment preference (6 October 2026): WikiArt is the source
  of truth for artwork image matching in this workflow. Use its artwork pages,
  creator identities, titles/translations, dates, versions and per-image rights
  labels as the reference. The user authorizes production image updates for
  matches with at least 90% confidence and wants as many supported matches as
  possible. This museum pass excludes the Louvre and Prado. Preserve source
  dates as evidence when imported dates differ or are missing; review the
  same-work identity against WikiArt before deciding whether to attach its image.
  Do not silently rewrite catalogue dates during an image-only update. Preserve
  evidence and unresolved ambiguities; image enrichment does not authorize
  changing catalogue metadata, holdings, display claims or publication status.

- Louvre source preference (6 October 2026): WikiArt is the source of truth
  for artwork metadata and images when a catalogue record has been securely
  matched to the same work. Prefer WikiArt's explicit creation dates over
  conflicting imported dates; a date discrepancy alone must not block adding
  its image. Preserve the previous values and source evidence in the audit
  trail. Resolve titles, versions, details, studies and copies before matching;
  source precedence does not make different artworks interchangeable. Retain
  per-image rights evidence, unknown fields and existing review/publication
  safeguards. A WikiArt holding label does not establish current display.

- Local debug preference (1 October 2026): all member and paid-feature previews
  must be available without Google login or a paid subscription. Use the API's
  local-debug access mode; keep its production and loopback safeguards intact.
  Do not create catalogue or member database fixtures to preview these features.

- Explicit incomplete-data preference (12 September 2026): retain named-creator
  artwork entries as actual database records in review even when additional
  research finds no details. Preserve supplied provenance and unknown fields;
  do not invent types, dates, artist biographies or accepted museum holdings.
  Unresolved named creators may remain object-level labels until reconciled.
  Anonymous/unknown creators and held attributions remain excluded from this
  expanded CSV import. Missing metadata does not authorize publication.

- Local collection workflow (11 September2026): audit the real local `artline`
  database using read-only queries. Do not create test databases or insert test
  fixtures into it. Do not point `ARTLINE_TEST_DATABASE_URL` at the real catalogue.
  Keep disposable proofs/test outputs out of Documents; preserve research evidence.
  Backups belong under `/Users/vadimdulub/Library/Application Support/Artline/backups/`,
  not scattered across Documents. See `docs/LOCAL_DATA_LOCATIONS.md` for relocated
  historical backups. Do not remove unrelated databases or real artwork assets.

- Explicit collection priority (10 September 2026): Russian icons, Greek
  artists, Byzantine and post-Byzantine art are first-class priorities, including
  works held outside their region of origin. See
  `docs/russian-greek-byzantine-priority.md`. Do not filter these traditions out
  merely because creators are anonymous, workshop-attributed, or not yet mapped
  to a named painter; support those cases explicitly before importing them.

- Capacity-planning scale: approximately 20,000 painters and 10 million artworks.
  This is engineering headroom, not a requirement to ingest/download that many.
- Confirmed content scope: artworks created in or before 1970, selected as
  masterpieces/highlights or supported by a documented museum connection.
  The cutoff is on artwork creation, not a painter's birth/death year.
- No exhaustive artwork/image downloading. Select eligible metadata first;
  download only selected, rights-cleared reproductions in an approved workflow.
  Personal masterpiece choices and museum designations must remain distinguishable.
- Treat museum holdings and currently-on-view status separately. Museum presence
  needs source evidence; an on-view claim also needs a fresh dated display record.
- Unknown dates or ranges crossing 1970 need editorial review, not an invented
  year or automatic eligibility. Do not delete existing records to apply this policy.
- Go/PostgreSQL own visibility, validation, filtering, date classification,
  grouping, counts, sorting and pagination. Next.js renders bounded responses
  and manages interaction state; do not load full collections into the browser.
- Scope artwork queries by painter/institution/IDs before enrichment. Do not reuse
  a global artwork CTE for a single-painter lookup without inspecting its plan.
- Prefer bounded keyset pages and indexed foreign-key lookups. Batch details for
  the returned IDs; avoid per-work requests or joins over the entire collection.
- Verify query plans with representative fixtures. Small-seed correctness tests
  are not evidence of 10-million-row performance. Document remaining load tests.
- Treat bulk ingestion, summary projections, search indexes and caching as
  explicit backend work with invalidation/review semantics, not client workarounds.
- No commits, Terraform apply, deployment or bulk ingestion unless requested.
- Existing records remain in review until explicitly validated/published. Never
  invent creation years or infer current display from a holding institution.

- Cambridge Broughton flower drawings (12 October 2026): delivered eight
  exhibitions dated 1973–1984 and 454 source-backed entries; all API records
  verified. One existing main-artwork link, no new artworks or images. Fifteen
  albums held for individual-leaf review. Preserve unknown dates, qualified
  makers and unresolved exact venues. Latest totals: 10,268 active, 10,084 held,
  34 undated; campaign additions 2,803. Real local database unchanged. See
  `docs/research/historical-exhibitions-20261012/fitzwilliam-broughton-delivery.json`.

- Cambridge drawing/print continuation (12 October 2026): twelve exhibitions
  dated 1957–1988 and 416 source-backed entries delivered and API-verified,
  including pagination for 125 Romney entries. No main-work, artist or image
  additions. Five potential duplicate source references remain held. Preserve
  month/year precision, qualified makers and unknown artwork dates/venues.
  Latest totals: 10,280 active, 10,096 held, 34 undated; campaign additions 2,815.
  Real local database unchanged. See
  `docs/research/historical-exhibitions-20261012/fitzwilliam-cambridge_remaining-delivery.json`.

- Fitzwilliam three-printmaker catalogue pass (12 October 2026): added 92 review
  prints (16 Griggs, 31 Segonzac, 45 Augustus John), 92 accepted museum holdings,
  92 primary artist links and 92 API-verified exhibition-entry artwork links.
  No images. Nine same-title NGA/MoMA impressions remain distinct. Preserve
  publisher roles and publication/creation uncertainty (23 structured dates unknown).
  The Fabri/Passarotti/Michelangelo print remains unlinked pending attribution review.
  Exhibition totals unchanged; real local catalogue read-only. Receipt:
  `docs/research/historical-exhibitions-20261012/fitzwilliam-print-catalogue-two-delivery.json`.

- Romney exhibition catalogue links (12 October 2026): added 125 review drawings,
  125 source-backed museum holdings, 125 primary artist links and 125 verified
  internal links for the 1977 show. 75 undated and 15 questioned dates retain
  unknown structured years; preserve their source labels. No images. Also added
  four verified exhibition participants (Romney, Griggs, Segonzac, Augustus John),
  supported by 217 native objects. Exhibition totals unchanged; real local DB
  unchanged. See `docs/research/historical-exhibitions-20261012/README.md`.

- Remaining Cambridge drawing catalogue pass (12 October 2026): 146 review
  objects (144 drawings, two painted miniatures), 146 source-backed holdings and
  198 API-verified internal exhibition links. Preserve qualified creator labels;
  primary artist reconciliation remains outstanding. 136 structured dates unknown.
  All 146 have source media leads, but no images were attached. No real local DB
  writes. Receipt: `docs/research/historical-exhibitions-20261012/fitzwilliam-oldmaster-drawing-catalogue-delivery.json`.

- Cambridge drawing creator links (12 October 2026): 68 exact primary creator
  links to 29 existing artists added and database-verified. Original creator labels
  and artwork rows unchanged. 78 objects remain unresolved, including qualified
  attributions and duplicate Raphael/Sanzio artist records; no artist merges.
  No new images/exhibitions or real local writes. Receipt:
  `docs/research/historical-exhibitions-20261012/fitzwilliam-drawing-creators-delivery.json`.

- Cambridge drawing exhibition participants (12 October 2026): added and
  API-verified 56 artist links across five shows, supported by 105 entries and
  68 exact artworks. Qualified/unresolved makers excluded from primary mappings.
  No artwork metadata/image/state changes or real-local writes. Receipt:
  `docs/research/historical-exhibitions-20261012/fitzwilliam-drawing-participants-delivery.json`.

- Early London release (12 October 2026): 25 exhibitions dated 1878–1929,
  47 entries and 13 exact existing-artwork links delivered and API-verified.
  No new artworks/images; all entries currently unillustrated. Nine source
  references remain held. Preserve unresolved exact venues and partial checklists.
  Verified totals: 10,355 active, 10,169 held, 35 undated. Release baseline was
  10,330; 50 other additions since the previous snapshot are not this batch.
  Real local catalogue unchanged. Receipt:
  `docs/research/historical-exhibitions-20261012/fitzwilliam-london_early-delivery.json`.

- Horne 1916 reconciliation delivered (12 October 2026): one Burlington Fine
  Arts Club exhibition, three API-verified entries; source refs 1235/1109 preserved.
  Retain Catherine Blake attribution for catalogue80 and tentative Turner ?111.
  Year precision only; no main-artwork/image additions or real-local writes.
  Latest totals: 10,356 active, 10,170 held, 35 undated. Receipt:
  `docs/research/historical-exhibitions-20261012/fitzwilliam-horne-1916-delivery.json`.

- Tate 1923 1860-period show (12 October 2026): references 1377/773 reconciled
  into one event, five API-verified entries and one existing-artwork link. Archive
  closing date June29 conflicts with Fitzwilliam July29; preserve year precision
  and both sources. Tate LibGuides returned429; do not retry during this pass.
  No main-work/image additions or real-local writes. Totals:10,357 active,10,171
  held,35 undated. See `docs/research/historical-exhibitions-20261012/fitzwilliam-tate-1923-delivery.json`.

- Exhibition/object chronology (12 October 2026): check creation lower bounds
  against exhibition end year before declaring participation exhibited. A 1,168-entry
  Fitzwilliam audit found Clausen210190 (1934) linked to1912; participation changed
  to uncertain and API-verified, metadata preserved. Sickert215699 (circa1928)
  also conflicts with held1912 ref912; refs912/2950 remain unmerged/unreleased.
  See `docs/research/historical-exhibitions-20261012/fitzwilliam-clausen-chronology.json`.

- Getty Blake historical delivery (12 October2026): seven new events and eight
  illustrated existing-artwork connections,1904–1983, from Getty1988 catalogue146
  accession84.GC.49. Exact version visually checked against PDF335–336; retain
  imported dimensions discrepancy. Carfax1906 venue resolved, eight participants
  API-verified. No new images/main works or real-local writes. Totals10,364 active,
  10,178 held,35 undated. See historical-exhibitions-20261012/getty-blake-delivery.json.

- Getty El Greco historical delivery (12 October2026): accession82.GA.166 added
  as review drawing about1600 with exact GettyCC0 image and accepted holding;
  five exhibitions1929–1955 and their illustrated entries/artist links API-verified.
  Public98,742-byte image checksum verified. Totals10,369 active,10,183 held,
  35undated; real-local database untouched. Do not repeat import. See
  `docs/research/historical-exhibitions-20261012/getty-elgreco-delivery.json`.

- Stag Beetle identity resolution (12 October2026): existing artwork515160f2
  (RijksBC-0005016) is the Getty83.GC.214 loan, corroborated by both museums’
  Crawly Creatures/Onderkruipsels evidence. Reused artwork; GettyCC0 image
  attached; prior Rijks holding superseded with audit preserved. No new work
  or modern exhibition. Preserve source accession; do not recreate duplicate.
  See `docs/research/historical-exhibitions-20261012/getty-stag-reconciliation-delivery.json`.

- Getty ten-drawing delivery (12 October2026): ten new review drawings, ten
  CC0 primary images, ten accepted Getty holdings, nine verified artist links.
  Jan Verbeeck II remains source label. All image checksums and source date
  precision verified; historical event connections pending. Stag Beetle reused
  separately; do not recreate it. Real-local untouched. See
  `docs/research/historical-exhibitions-20261012/getty-ten-drawings-delivery.json`.

- Getty historical venue delivery (12 October2026):34 new events, one existing
  Chatsworth tour extended,49 new occurrences,78 illustrated entries,50 artist
  participants. All35 event API responses verified. Existing Cleveland occurrence
  and its exact1963 dates preserved. Ten new drawings plus reused Stag Beetle
  images from preceding phases now connected. Burlington winter1927–1928 held.
  Totals10,403 active,10,217 held,35 undated. Real-local untouched. See
  `docs/research/historical-exhibitions-20261012/getty-venue-delivery.json`.

- Getty existing-five continuation (12 October2026):8 new illustrated entries
  across7 existing events, using5 exact Getty holding/accession matches. API
  verified; original artworks/images unchanged. These paintings have no primary
  artist links yet; retain creator labels until reconciled. Remaining expansion:
  33 eligible objects/138 references. See
  `docs/research/historical-exhibitions-20261012/getty-existing-five-delivery.json`.

- Historical Getty checklist expansion (12 October 2026): the selected batch is
  complete for 38 eligible objects and 146 captured reciprocal historical venue
  references across 24 existing exhibitions: 32 new review artworks/images and
  six existing artworks reused. Seven creator identities remain explicit labels;
  do not silently merge duplicate artist profiles. Getty Poussin 81.PA.43 retains
  canvas-specific NoC-US rights, not manifest-level CC0. Preserve the original
  Rembrandt Apostle Bartholomew identity and image. See
  `docs/research/historical-exhibitions-20261012/getty-checklist-expansion-delivery.json`.
  This batch completion does not mean complete historical exhibition coverage.
