# Cyprus collection expansion — 21 September 2026

Applied to the real **local** Artline catalogue at 15:17 UTC. All new artist, artwork, institution and collection records remain in review. Nothing was published, deployed or committed; no museum was contacted. No reproductions were downloaded or attached.

## Saved records

| Change | Count |
| --- | ---: |
| New Cyprus-linked artist profiles, including the conventional Asinou Master attribution | 49 |
| Additional international artist for XeniArtSpace research: Lydia Masterkova | 1 |
| Existing artist profiles given a sourced Cyprus relationship | 5 |
| Cyprus-linked artist profiles after this review | 81 |
| New fresco records | 202 |
| New icon records | 106 |
| Other new works: four paintings, one watercolour, one drawing | 6 |
| Total new artwork records | 314 |
| New additions to the personal selection, including 71 existing works | 385 |
| Unique new/existing artworks covered by this review and selected | 442 |

The 321-work application plan includes seven icons already in the catalogue; these were reconciled, not duplicated. Of the 314 new artworks, 207 have creation dates within the cutoff and 107 retain unknown or unresolved dates. Date eligibility does not confer editorial approval. All 314 are research candidates with citations, no accepted holding/display assertions, no current holding institution, no media and no publication timestamp.

The artist list is in [ARTISTS.md](ARTISTS.md). The local [collection-review.csv](collection-review.csv) contains all 442 artworks, record IDs, creator labels, dates, review status and source URLs. Contemporary painter profiles are retained where documented; their inclusion does not make post-1970 works eligible.

## Coverage and evidence

This is a documented expansion, **not a complete inventory of every Cypriot painter, fresco or icon**. The audit began with 27 Cyprus-linked artist profiles and 128 related artworks.

- The Cyprus University of Technology's [APSIDA archive](https://apsida.cut.ac.cy/) supplied 349 metadata records across six relevant icon/mural tags, with no failed item captures. Relevant material includes the Enkleistra and monastery of Saint Neophytos, Asinou, and icons associated with Cypriot churches and museums. Seven duplicate photographic records were reconciled. Twenty-seven overview/detail, non-artwork or out-of-scope records were held out; two decisions preserve separate panels with similar titles.
- [Cypria's artist directory](https://cypriaauctions.com/artists) supplied 150 captured biographies for identity review. Selected additions also use [Psatharis biographies](https://www.psatharis-auctions.com.cy/biographies.htm), artists' own sites and XeniArtSpace's exhibition catalogue. The resulting identities and sources are listed individually in ARTISTS.md.
- The [Bank of Cyprus Cultural Foundation collection page](https://www.boccf.org/en-gb/homepage/museums-collections2/sulloge-sugkhrones-kupriakes-tekhnes/sulloge/) documents Loukia Nicolaidou's *Cypriot Woman from the Countryside* (1935), added as a watercolour. Listed later works remain outside the cutoff.
- Review institution records were added for XeniArtSpace, the Bank of Cyprus Cultural Foundation, the Monastery of Saint Neophytos and the Museum of Kykkos Monastery. Institution existence or an archival contribution does not establish an accepted holding for every associated object.

The 567 locally preserved capture receipts include original metadata/page content, source URL, retrieval time and SHA-256. Archive photographic dates, photographers, donors and digitisation staff were not substituted for artwork creation dates or painters. Restoration dates remain separate. Conflicting dates remain unknown, including the 1806/1856 icon discrepancy and conflicting late-thirteenth-century/1332 Asinou description. Century-level bounds preserve the uncertainty of the source rather than assign an exact year.

Anonymous works use object-level creator labels. “Style of” is not converted into a primary named attribution. An icon's museum location does not become its production country. Only documented in-situ fresco locations received production-place links in this batch.

## XeniArtSpace permanent-collection review

The [official collection overview](https://xeniartspace.com/collection) describes the foundation collection but does not expose a complete object-level permanent inventory. Its exhibition material therefore supports a **five-work owner research collection**, not a claim that all five are permanent holdings:

| Artist | Work | Date | Documented connection |
| --- | --- | --- | --- |
| Leonor Fini | Sphinge | 1969 | [CHANNELLED guide](https://xeniartspace.com/guidechanneled) |
| Lydia Masterkova | Metaphysical Abstraction | 1969 | [CHANNELLED guide](https://xeniartspace.com/guidechanneled) |
| Lynne Drexler | Celestial Division | 1966 | [CHANNELLED guide](https://xeniartspace.com/guidechanneled) |
| Renos Loizou | Blue landscape | 1966 | [Cyprus Orbits catalogue](https://xeniartspace.com/cyprusorbits) |
| Christoforos Savva | Blue Nude | Unknown | [Cyprus Orbits catalogue](https://xeniartspace.com/cyprusorbits) |

CHANNELLED is dated 22 September 2026–5 March 2027; it had not opened on this review date. Cyprus Orbits ran 17 May–26 July 2025 and included works offered for sale. Neither connection is recorded as current display or permanent ownership.

A [gallery acquisition announcement](https://cyprus-mail.com/2025/02/26/xeniartspace-gallery-exhibits-two-works-by-famed-sculptor-anish-kapoor) explicitly identifies Anish Kapoor's *Untitled* (2007) and *Spanish and Pagan Gold to Cobalt Blue* (2019) as permanent acquisitions. Both are preserved as institution-level research leads, not artwork imports, under the existing 1970 cutoff. The apparent 1966 date for Tracey Emin's *Naked Photos* in the exhibition text is held as a source discrepancy, not accepted.

The XeniArtSpace research collection ID is `6b1d2184-07af-5365-b125-2c86f41cf1df`. The institution ID is `9c273ebf-e7b5-54cb-8348-f75f8488a8ee`.

For a complete collaboration catalogue, the remaining input is an object-level inventory from the foundation/museums: stable object IDs, titles, creators/attributions, creation dates, medium/dimensions, acquisition or holding evidence and separately dated display information. Reproduction permissions would be a separate workflow. No correspondence was sent.

## App behaviour and remaining visibility limits

Cyprus filters in All now include documented artwork production places as well as creator-country relationships, so dated anonymous frescoes are discoverable without inventing artists. Existing creator-specific filters retain their shared-creator semantics. Exhibition presence does not become Cypriot origin.

Dated selected records are available in the local research timeline. Unknown-date records are saved in the collection but cannot be plotted on a dated timeline. Savva's undated *Blue Nude* is available through his artist artwork endpoint. Anonymous undated records can be reviewed through the saved manifest/database.

The existing Museums endpoint requires holding or accepted display evidence. XeniArtSpace's research association alone does not meet that policy, so its museum page still returns 404; this batch does not publish it or fabricate holdings to make the page appear. The four dated Xeni works are accessible through the All artwork endpoints. A dedicated research-collection browsing interface remains separate product work.

## Validation

- 21 Python evidence/parser/plan tests pass, including date conflicts, photographic/restoration dates, duplicate reconciliation, anonymous/qualified attributions, production versus custody, and Xeni exhibition versus permanent evidence.
- Read-only post-apply verification confirms all 314 new works, all 50 new artists, all 442 selected IDs, and all five Xeni research items. A separate audit confirms zero holding/display assertions, current holdings or publication timestamps on the new artworks.
- `go test ./...` passes with database environment variables unset; fixture-dependent tests skip. The installed toolchain requires `env -u GOROOT`.
- Targeted read-only discovery, geography, entity-filter, bounded-query and explicit-selection regression checks pass: 24 test/subtest results. The new production-geography checks pass: 16 test/subtest results, including review-record invisibility in public mode, country unions, continent intersections, native/global filter agreement and foreign Xeni artists not acquiring Cypriot origin.
- Thirteen direct HTTP checks pass against the rebuilt local API. They include 25 anonymous/detailed fresco results in both global/native Cyprus filters for 1190–1200, country combinations, artwork details, Savva's undated artist detail and the expected exclusion of unsupported museum membership.
- A broader exploratory read-only run found an existing failing assumption in `TestPersonalCollectionReadOnly`: *Rebecca and Eliezer* (`001d3fb8-6e9b-5330-9fe2-0dc2eab3616a`) already had a **review** holding assertion from `spain-deep-research-20260916`, created 16 September UTC. That test expects no assertion at all. This Cyprus batch did not create/change that record or assertion. The full exploratory read-only suite is therefore not reported as green.
- Visual Browser verification was unavailable because the Browser tool failed before execution with `codex/sandbox-state-meta: missing field sandboxPolicy`. HTTP checks are not a replacement for a visual claim.

Tests used read-only connections to the real catalogue; no test database or fixtures were created. Disposable outputs are in `/tmp/artline-cyprus-qa/`. Representative EXPLAIN checks on approximately 296,849 real artwork rows measured a bounded page at 163 ms, a picked-work check at 14 ms and a single detail at 0.072 ms. These checks do not establish performance at ten million artworks; that load test remains outstanding.

The backend changes add country/place lookup indexes and scope geographic candidates before eligibility/enrichment. The local migration runner applied `0027_artwork_production_geography.sql` and the already-pending `0026_search_discovery_indexes.sql`; both add indexes. No production migration was run.

## Audit and recovery

- Pinned application plan: `application-plan.json`, SHA-256 `a77ea6759fbca72ad6f5cce7e0d0833eef995e40cba209049d7dadf53d24d187`.
- Application receipt: `applied.json`; read-only verification: `verification.json`. Re-running verification preserves the original receipt. Rebuilding/reapplying an already applied plan is guarded.
- Personal collection: `42c83e94-d1f2-539a-accb-b4e9ded61f06`.
- Full pre-apply backup: `/Users/vadimdulub/Library/Application Support/Artline/backups/cyprus-collections-20260921/local-before.dump`, 632,476,803 bytes; archive listing verified. SHA-256 `12d055349f0b3aa3d5f21a261647cb015611a4278a8f7099de20b8045e71f328`.
- Transaction preimages are retained in that same backup directory. Earlier unsuccessful apply attempts rolled back before the successful transaction.
- Review CSV SHA-256: `5047d562ec5007ea39aad4418c9c56d4dcf61f3621aed9c3275e8e5da3a79619`.
- Scripts: `ops/cyprus-collections-20260921.py`, `ops/cyprus-collections-20260921-review.py`, `ops/cyprus-collections-20260921-apply.py`, `ops/test_cyprus_collections_20260921.py`.
- Python environment used: `/tmp/artline-cyprus-20260921-venv/bin/python` with requests, BeautifulSoup and psycopg. Evidence is intentionally local and ignored by Git; Markdown reports remain versionable.
