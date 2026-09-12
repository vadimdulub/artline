# European popular-painter research session

Started 11 September 2026, 12:48:18 UTC. Requested window: four to five hours of active research and implementation. Earliest elapsed-time target is 16:48:18 UTC; approval waits are not counted as active research. Work remains in progress.

Baseline: 100 popular painters, 22,232 linked artworks and 410 popular-work images; full catalogue 106,195 artworks and 608 images.

Verified checkpoint, 15:17 UTC: **102 new National Gallery paintings across 35 popular painters**, bringing the full catalogue to **106,297 artworks**. Images remain 608. All new objects remain in review, with holding evidence but no inferred current display or masterpiece designation. Permission approval waits have consumed substantial elapsed time and are not active research.

- Pre-mutation backup: `/Users/vadimdulub/Documents/artline-popular-europe-session-backup-20260911.l1B9ac/before-ng.dump`; SHA256 `908c0aec88f5f28d09d4687ca7287e838db44af9630be1cd6ca80679c1987c42`.
- Pinned batch: `ng-v2/manifest.json`, SHA256 `17c9659dc455168783bdeeafd0953f3e8399e9d4024cfae70c9c4608dbea6c55`. Earlier `ng-v1` is superseded and was not imported.
- Receipts: `output/popular-europe-session/ng-preview-v2/`, `ng-apply/`, `ng-replay/`; replay created nothing. `ng-before.json` / `ng-after.json` verify preservation of existing artwork rows, artists, popularity, museums, media, rights and curated selections.
- `output/popular-europe-session/ng-api.json`: 102 exact detail checks and two unpublished-access checks passed. The local API initially was offline; it was started locally, not deployed.
- Selection examined 589 source hits: 102 selected, 117 exact existing objects preserved, 117 dates deferred, 91 multiple/missing creators, 80 outside accessioned main paintings, 61 qualified/non-exact creators, 17 shared-custody cases, two medium and two same-title identity cases deferred. Successful queries are not painter completion.

## Evidence and work log

### Verified continuation checkpoint, 18:49 UTC

**135 artworks across 43 popular painters, 13 images and four museum records added.** Full catalogue: **106,330 artworks; 621 media**. Repin's five new paintings and one museum passed preservation and all five detail/API checks. `repin-v1` SHA256 `34c2ec816869cbd4bcf19602cd0450282ac5edf08516764f04a585b1aa6886cd`; backup `before-repin.dump` completed before mutation. All additions remain in review and existing editorial work is preserved. See [exact continuation state](CONTINUATION.md), including the unresolved coding-session Bad Request report and mandatory Monet image-visibility follow-up. No exact active-work-duration claim is made from elapsed wall time.


### Athens checkpoint, 18:35 UTC

- **106,325 artworks, 621 media**: session delta **130 artworks and 13 images**. Goulandris added five paintings and one museum; National Gallery Athens added St Peter. All six details and both batches' preservation/access-control checks passed. New records remain in review; no display or masterpiece changes.
- `goulandris-v2/manifest.json` SHA256 `d0af7c7823433f4011ba39e8121115a999795daa70e57fd04c0513031391da85`; `athens-national-v3/manifest.json` SHA256 `fbc5e9b88451b7d6da0a2063598b8e815f35145858c4c6b862abb3d881f77cda`. Earlier Goulandris v1 and Athens v1/v2 were not applied. Athens v2's preview safely rejected a single-year precision label for a circa interval; v3 preserves the source as `circa_range`.
- Before-mutation backups `before-goulandris.dump`, `before-athens-national.dump` completed. Receipts are under `output/popular-europe-session/`, with corresponding `*-before.json`, `*-after.json`, `*-api.json` and apply directories.
- [Cited findings and unresolved source conflicts](FINDINGS.md) now include Greek and Russian notices. Five selected Repin objects are queued, not yet counted as additions.
- [Fresh all-100 inventory](inventory-v1/PAINTERS.md) exported with 22,356 artwork links and 423 images before the Athens additions. These are inventory counts, not source-review completion.
- User-required next task saved in [continuation prompt](../../POPULAR_RESEARCH_CONTINUATION_PROMPT.md): audit actual picture visibility starting with Monet, after the current research task. The user reports no pictures despite stored image records; this remains unresolved.


### Verified follow-up, 16:42 UTC

- Full catalogue: **106,319 artworks and 621 media**. Session delta: **124 artworks and 13 authentic images**, plus two museum records. Metadata additions span 36 popular painters. Existing editorial selections, published state and prior records remain preserved.
- National Gallery documented `Claude` alias: 11 additional direct Claude Lorrain paintings imported. `ng-aliases-v1/manifest.json` SHA256 `54473b21c76449a2fca0b7a4680c9025c51623136a684d047b1683e39820566e`. `ng-aliases-after.json` and `ng-aliases-api.json` passed. Giotto's two qualified records remain deferred, not imported as autograph works.
- Eight direct Dürer paintings added: five Alte Pinakothek, two documented permanent loans to Germanisches Nationalmuseum Nuremberg, one Staatsgalerie in der Katharinenkirche Augsburg. `durer-v1/manifest.json` SHA256 `b47d6629fdeae7be358c6591bc4898ed57f89f3aeda2678291e821625335fcae`; metadata preservation and eight API details passed. The two new institutions remain in review. Augsburg's [official branch guide](https://www.pinakothek.de/de/staatsgalerien) reports closure since 2022; affiliation is not current display or availability to visit.
- All eight selected Dürer object images attached with individually verified CC BY-SA 4.0 permission; 72,239–99,476 bytes, full composition retained. Image selection SHA256 `31bb1ceea045990c22eed9b9765b3d2891c291f203e07d6f2854d80d56c84727`. `durer-images-after.json` passed preservation, eight files and zero highlight changes; `durer-images-api.json` passed 28 API checks, eight complete image decodes and served-file hashes.
- Additional backups completed before each mutation: `before-ng-aliases.dump`, `before-durer.dump`, `before-durer-images.dump`, in the session backup directory. No commit, push, publication or deployment.
- Athens research underway: [National Gallery St Peter](https://www.nationalgallery.gr/en/artwork/st-peter/) provides exact accession Π.9027 and circa 1600–1607 dating. [Goulandris collection](https://goulandris.gr/en/collection/highlights) identifies a substantial cross-painter Athens gap, including Kandinsky and El Greco. Individual metadata/holding checks pending; no image reuse permission assumed from accessibility. Museum floor information will not be imported as current display.


### Verified follow-up, 15:47 UTC

- Three Caen paintings added and verified: Perugino's *Le Mariage de la Vierge* (1504, inv. 171), Veronese's *La Tentation de saint Antoine* (1552, inv. 6), Tintoretto's *La Descente de Croix* (1556–1558, inv. 17). National open-dataset facts are retained; exact museum notices resolve these three specific comma-form dates. No generic comma-to-range rule was introduced.
- Full catalogue now **106,300 artworks and 613 media**: session additions **105 artworks + five images** so far. Metadata additions span 35 painters; image additions span five painters, not five new artists. Museum-highlight and owner selections unchanged.
- Five individually CC BY-SA 4.0 Pinakothek images attached for Dürer, Pissarro, Rubens, Rembrandt and Van Gogh. File sizes 84,862; 91,190; 99,730; 96,802; 90,597 bytes. `pinakothek-after.json` verifies metadata/selection preservation; `pinakothek-api.json` verifies 17 API checks, five full decodes and five served hashes. The source is the exact primary museum image, with no URL transformation, cropping or generated content.
- Image backup SHA256: `a571490123aea1b4437c5adf6e24627c73181b868ff52217c18cd2e9a9bde9c5`, `before-pinakothek.dump` in the session backup directory. Image selection SHA256: `b6d24d0589c0ea0cb3bd1f82ff10e158f810d1c9c0596753d7224d00c1e3a6fd`.
- Caen batch `caen-v3/manifest.json` SHA256 `413201653d8e1eb845ed60b72979f6a0621293864727b95adf17d8ca20b2ba76`; preview three new, zero reused; `caen-after.json` preserved all previous records and verified three eligible popular-painter museum links. `caen-api.json`: three details and two access checks passed. Backup `before-caen.dump` completed before mutation. `caen-v1` was rejected on further source review and never imported; `caen-v2` has the same object payload as v3, whose crosswalk explanation is corrected.
- [All 100 painter source-check checklists](review-v1/PAINTERS.md) saved, including Hokusai without an external authority ID. This checkpoint predates the three Caen additions; painter supplements below record them. No painter is marked globally researched.
- National Gallery's [Giotto page](https://www.nationalgallery.org.uk/artists/giotto) and [Claude page](https://www.nationalgallery.org.uk/artists/claude) document alternate source names. Two new queries, not 99 repeated searches: Giotto's two records remain qualified; 11 direct Claude paintings are staged and awaiting import verification.
- Dürer's Pinakothek artist index has 44 linked records, many explicit copies/followers. Eight individually selected direct-attribution, non-multipart objects are being captured for exact detail review. The artist-page count is not a count of 44 autograph Dürers.

### Caen source conflicts retained

- [Judith et Holopherne, inv. 13](https://mba.caen.fr/oeuvre/judith-et-holopherne): museum explicitly says **with collaboration**, circa 1580; simpler Joconde creator list and broad 1576–1600 interval are insufficient for a primary-only import. Deferred.
- [Géricault study, D.75.1.8](https://mba.caen.fr/oeuvre/etude-preparatoire-pour-le-derby-depsom): exact accession matches, but museum dimensions 53.8 × 66.4 cm differ from Joconde 30 × 42 cm. [Louvre RF 220](https://collections.louvre.fr/ark:/53355/cl010055598) is a further deposited horse-race record (29 × 41 cm). Do not merge these by title or dimension proximity; resolve the deposit/accession crosswalk first. Deferred.
- Perugino *Saint Jérôme*, inv. 79: Joconde 1496–1502 versus museum 1498–1502 retained as differing source assertions; deferred.
- Tintoretto *La Cène*, inv. `16 ; Musées impériaux 499 MR (Ancien numéro)`: source date 1566, but inventory-alias reconciliation remains pending.
- Rogier van der Weyden, *La Vierge à l'Enfant*, M.91: Joconde calls the unit a diptych, while the museum presents a panel; object/ensemble reconciliation and precise date review remain pending.
- A Van Dyck catalogue entry is marked missing/destroyed and was excluded from current-holding additions.

- Read project constraints, prior cycle, complete popular inventory and Normandy research history. Existing snapshots preserved.
- Verified the National Gallery's [documented metadata API](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api) and [separate data/image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). Implemented a bounded Go popular-painter collector and candidate selector. It collects factual metadata only, not narrative essays or image binaries.
- Collector started with 99 popular painters having stored Wikidata identifiers. **Katsushika Hokusai lacks that identifier locally** and remains an explicit authority-review item, not an omitted or completed painter. The full 100-painter inventory remains the scope.
- National Gallery source queries start with low local coverage: Verrocchio, Cimabue, Masaccio, Uccello, Piero della Francesca and Artemisia Gentileschi. Query success and candidates do not mark a painter researched completely.
- Regional follow-up: [Caen's official collection](https://mba.caen.fr/collections) supplies individual Perugino, Veronese, Tintoretto, Rogier van der Weyden and other popular-artist notices. These must be reconciled against existing Joconde accessions before import. Paid photograph ordering is not an open-image licence.
- [Pinakothek reuse guidance](https://www.sammlung.pinakothek.de/de/usage) permits reuse of works individually marked CC BY-SA 4.0. Exact objects, collection branch and per-image marks still need verification.

## Next executable steps

1. Record individual National Gallery decisions in painter checklists; investigate source-name and date-notation gaps separately without repeating unchanged queries.
2. Four selected Caen object notices captured for private research. Its website reserves database rights and has restrictive photograph terms: prefer matching permitted Joconde metadata; do not bulk extract the site or download its images. Reuse existing institution `joconde-m0657`, not a duplicate museum.
3. Select a geographically broader European image batch with exact-object, per-file permission evidence.
4. Continue through unresolved painters and regional museums; update this ledger and each painter's source-backed decisions after every verified batch.

Access blocks inherited from earlier sessions remain in force: Chicago image server, Nationalmuseum image links and Orsay direct route. Marmottan photographs have unresolved reuse permission. No bypasses, account creation, permission requests, commits, publication, deployment or Terraform application.
