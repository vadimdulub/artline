# Four-hour creator research and delivery — 10 October 2026

Research window: 2026-10-10T19:30:43Z–2026-10-10T23:30:43Z. Final delivery verification: 2026-10-10T23:50:12Z. The last reviewed Buchet selection was delivered and checked during closeout immediately after the research window.

Production result: **84 new artworks and 94 authentic images**, including ten supplementary images on previously added Tvorozhnikov records. Five creators received 11–23 new works each. New works remain in review and are visible in the unified catalogue. No publication, current-display claims, local database connection, commit or deployment was performed.

| Creator | Linked works at selection | New artworks | Images added | Linked total verified |
| --- | ---: | ---: | ---: | ---: |
| Arthur Streeton | 5 | 16 | 16 | 21 |
| Gustave Buchet | 2 | 15 | 15 | 17 |
| Hans Holbein the Elder | 5 | 19 | 19 | 24 |
| Harry Clarke | 2 | 23 | 23 | 25 |
| Ivan Tvorozhnikov | 2 | 0 | 10 | 27 |
| Yov Kondzelevych | 2 | 11 | 11 | 13 |

The initial counts above are linked active works. Additional raw-label and alternate-profile records were searched and compared before adding objects. These comparison records are not included in the linked totals. Existing linked and raw-label objects were preserved; ambiguous duplicate profiles were held rather than merged.

The additions carry 117 supplementary research citations and 33 documented museum links. Collection credits remain distinct from current display. WikiArt image rights labels remain separate from the user’s source approval.

## Object-level decisions

- Streeton: 16 additions; museum catalogues and the 2020 AGNSW exhibition labels distinguish repeated landscape titles, sketches, later acquisitions and private collection credits. Existing Templestowe and Sirius Cove variants were compared and excluded where appropriate.
- Holbein the Elder: 19 additions; individual Grey Passion and Saint Sebastian panels were distinguished from ensemble photographs, alternate faces, details and duplicates. Historic loans are not treated as ownership transfers.
- Clarke: 23 distinct full-page illustrations matched to the 1920 primary edition of The Year’s at the Spring. The publication year does not invent an original drawing execution date, and a museum library copy does not establish ownership of an original drawing.
- Kondzelevych: 11 icons; four creator links remain attributed-to. Museum publications resolve individual panels, inventories, inscriptions and provenance; seven numeric dates remain unknown. The Bobly mounted Saint George is distinguished from the standing Okorsk saint. Lviv National Art Gallery is not substituted for the National Museum in Lviv.
- Buchet: 15 works; nine exact primary museum/auction matches. Two double-sided canvases are represented once each with the selected face stated. Two Frauenakt compositions with identical titles/dates remain distinct. Framed and image-opening measurements are not imported as object measurements. Two MCBA acquisitions have verified accession numbers.
- Tvorozhnikov: ten images supplement the preceding 25-work metadata pass; those earlier metadata additions are excluded from this campaign’s new-artwork total.

## Holds and limitations

- Nikitin: duplicate creator profiles and a possible icon-painter homonym; no new records.
- Russell: extra raw-label works exceed the intended small-collection target; a suspected British/Australian creator conflict and source login redirect remain unresolved.
- Ushakov: two linked plus five raw-label objects; no additional records. Repeated faces and details excluded.
- Ghikas: duplicate Nicolas Ghika profile already contains thirteen works; no additions. Bauernfeind already has twenty linked works.
- Unknown dates, uncertain attributions, unverified auction leads and unselected works remain documented in each frozen reviewed plan. The pass is selective, not an exhaustive catalogue raisonné.
- Denied source endpoints, TLS failures and the unusable black comparison image were retained as research limitations and not bypassed. All delivered images are authentic selected WikiArt reproductions; full supplied frames were preserved.

## Evidence and verification

- `final-audit.json`: fresh production snapshots for every delivered image target and preserved pre-existing records.
- `progress.json`: per-creator totals and completion time.
- `creators/*/reviewed-plan.json.gz`: immutable metadata selection, exclusions, object decisions, source receipts and checksums.
- `creators/*/visual-review.json`, `images-verified.json`, `creator-verified.json`: visual decisions, live image byte verification and bounded public API verification.
- Source registry: `source-registry-review.json`; source captures remain with each creator. Original images, PDF research documents and transaction backups are kept under the designated Artline Library directories.

All 94 image deliveries passed full-frame visual review, the 100,000-byte limit, source identity checks, database attachment checks and public SHA-256 checks. A transient Buchet verification timeout was retried without repeating mutations. Production mutations used the shared advisory lock, create-only asset upload and saved transaction preimages.
