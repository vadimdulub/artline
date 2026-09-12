# Internal evidence and gap ledger

Accessed 2026-09-09. Canonical claim-to-source mapping for object claims is
inventory.json: each work title identifies the source title; institution identifies
publisher unless overridden; source_updated_on is optional; url/access/notes contain
the exact source and qualification. Missing source update dates are unknown, not
the access date. Each institution's data_url/rights_url supports its access/rights
claim, with the page's visible policy name as source title. Workers supplied compact
primary-evidence records; coordinator checked consequential claims listed below.

| Claim / gap | Evidence, source title, publisher | Confidence / conflict | Follow-up and disposition |
| --- | --- | --- | --- |
| 59 candidate works, 26 institutions, 12 countries | Counts derived from unique inventory records, not a museum assertion | High arithmetic; bounded sample | JSON validation checks counts, unique object URLs and institution references |
| NG metadata/prose/image licences differ | Data licences, National Gallery, n.d.; https://www.nationalgallery.org.uk/documentation/ngacuk/licences ; parent turn178view0 | High; CC0 / CC BY / CC BY-NC-ND | Images remain link-only under existing accepted-image rules |
| Louvre JSON route | JSON Documentation, Louvre, n.d.; https://collections.louvre.fr/en/page/documentationJSON ; parent turn178view1 | High, successful direct retrieval | Append .json; no operational adapter built |
| Ghent attribution dispute | Christ Carrying the Cross, MSK, n.d.; https://www.mskgent.be/en/collection/1902-h ; parent turn178view2 and turn179view4 | High confidence that disagreement exists, not that attribution is settled | Preserve disputed status; consortium research is corroborating evidence |
| Orsay title aliases/display conflict | Côte Saint-Denis à Pontoise, Orsay, n.d.; French/English URLs in inventory | Holding and identity high; display contradictory | Parent retrieved French record turn178view3; follow-up text search errored. Worker directly checked both; keep conflict, no display import |
| Rijksmuseum data routes | Documentation of Data Services, Rijksmuseum, n.d.; https://data.rijksmuseum.nl/docs/ ; parent turn179view1 | High documentation; not a tested integration | API and IIIF selection stage pending |
| Städel PD-image policy | Bildnachweise, Städel, n.d.; https://www.staedelmuseum.de/de/bildnachweise ; parent turn179view2 | High policy; per-file audit still needed | OAI registration prerequisite recorded; no registration |
| Nationalmuseum mixed image rights | View over the Sea / Rights and reproductions, Nationalmuseum, n.d.; inventory URLs | Worker direct observation; parent policy open failed turn179view0 | Keep asset-specific decision; not approved for download |
| Belvedere conflicting reuse language | Path in Monet's Garden in Giverny, Belvedere, n.d.; current object URL in inventory; parent turn179view3 | Current restrictive notice versus historical 2024 press statement | Restrict pending exact licence resolution; IIIF viewer is not permission |
| Borrowed holdings | Prado Garden / Boijmans Flood / Thyssen Carmen records, publishers as listed, n.d. except recorded dates | High catalogue custody evidence; not full provenance adjudication | Preserve owner/custodian distinct; no automatic live display |
| Subject genres missing | Local schema and current API inspection | High implementation finding; no source labels fabricated | Clarification asked; no reply. Movements/work types implemented, subject taxonomy future |
| Pissarro classification missing | Local GET timeline?painter=claude-monet&painter=camille-pissarro-q134741 on 2026-09-09 | Current Pissarro countries=[], movement=unclassified | UX caveat and report; database not silently repaired during research |
| 10m scale unproven | Local query inspection; scoped 100k temporary fixture | Bounded payload != bounded global query cost | Preserve scoped lookups; summary projections/full-scale benchmarks deferred explicitly |

## Search waves and stop

### Authorized import follow-up, 2026-09-09

- National Gallery, *Camille Pissarro*, n.d., accessed 2026-09-09:
  https://www.nationalgallery.org.uk/artists/camille-pissarro . Direct official
  biography supports Impressionism and work mainly around Paris. Import a French
  **active-in** relationship, not citizenship or birthplace. Fill empty review
  classifications once; preserve later editorial edits.
- Nationalmuseum, *View over the Sea*, n.d., accessed 2026-09-09:
  https://collection.nationalmuseum.se/en/collection/item/19182/ . Direct record's
  date field is explicitly a signed date. Keep "Signed 1882" but leave numerical
  creation dates unknown. It also confirms different rights on different photos;
  no photo is selected or downloaded by this metadata import.
- MSK, *Christ Carrying the Cross*, n.d., accessed 2026-09-09:
  https://www.mskgent.be/en/collection/1902-h . Direct record reconfirms that
  attribution is disputed. Use attributed_to plus explicit dispute note.
- National Gallery, *Saint Jerome as Cardinal*, n.d., accessed 2026-09-09:
  https://www.nationalgallery.org.uk/paintings/possibly-by-el-greco-saint-jerome-as-cardinal .
  Direct record reconfirms possible attribution, NG1122 and 1590–1600.
- Italian Ministry of Culture, *Altarolo per un Miles Christi*, catalogue compiled
  2018, accessed 2026-09-09:
  https://catalogo.beniculturali.it/detail/HistoricOrArtisticProperty/0800675920 .
  Official indexed full record reconfirms attribuito, 1567–1568 and Modena holding;
  newly found inventory RCGE n. 8095 is now recorded separately from national ID
  0800675920. Metadata licence is CC BY 4.0; publisher credit retained. Earlier
  direct access failure remains documented, not bypassed.
- Official institution-site crosscheck: Gallerie Estensi English homepage
  https://gallerie-estensi.beniculturali.it/en/ and Academy Paintings Gallery,
  https://www.kunstsammlungenakademie.at/en/paintings-gallery/about/ . Both official
  indexed records; n.d.; accessed 2026-09-09. Institution venue links are not
  current exhibition assertions.

Stop: exact identity, three qualifications, signed-date handling and Pissarro
classification are resolved sufficiently for review-only metadata import. No
new broad discovery wave or unbounded image download is needed to apply this batch.

### Original discovery waves

First wave: exact painter+official museum catalogue searches, split Bosch/El Greco
and Monet/Pissarro. Second wave: aliases, attributions, permanent versus historic
loans, object identifiers and institutional rights/data documentation. Focused
geographic gap wave: Ordrupgaard, Nationalmuseum and Belvedere added six exact
records. No recursive worldwide crawling. Excluded drawing, forgery, transient loan
and unverified exact-object leads; retained unknown accessions as null. Persistent
access failures were not bypassed. Stopped after supported representative breadth
with all material disagreements explicitly bounded.
