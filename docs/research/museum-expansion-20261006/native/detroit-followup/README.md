# Detroit: minimum 100 reached

The local catalogue now contains **100 linked Detroit artworks with eligible creation dates**. This pass added **92 review records** and reconciled **two existing Favanne holdings**, increasing the previous count of six by 94. Detroit needs another 100 eligible works for the preferred 200 target.

- [Individual decisions](editorial-reviewed-002.json.gz): 92 additions, two exact existing identities and 18 captured holds.
- [Pinned local write plan](detroit-reviewed-followup-001-plan.json.gz), SHA-256 `cd19ea5b78906b2f07270419d54d7c714f79a746f690076efa0d6ef771d8751d`.
- [Applied receipt](detroit-reviewed-followup-001-applied.json) and [test/replay evidence](checks-001.json).
- [Full campaign coverage](../../museum-coverage-after-wave-52.csv) and [verification](../../verification-after-wave-52.json).

The complete selected capture contains 117 official object pages. Five were delivered in the preceding priority pass; the remaining 112 received individual decisions here. One further selected object, Annunciatory Angel, timed out and remains uncaptured. No retry or alternate transport was used for it. Native HTML, HTTP receipts, index-to-object links, literal dates, current and former attributions, credit, dimensions, provenance and unknown rights remain preserved. Web-tool comparison extracts are separately labelled and are not represented as original HTTP bytes.

The final read-only identity scope contains 26,937 catalogue artwork records and 57,121 citations, with expanded historical creator names and title translations. Similar versions were distinguished using inventories, dimensions, support, composition and acquisition histories. An actual comparison of the primary DIA educational PDF and the selected existing WikiArt reproduction established that the two Judith compositions are different. The mixed existing record was preserved unchanged. The PDF and reference image were retained under Library for identity evidence; neither was attached to the catalogue.

Henri Antoine de Favanne’s Adoration of the Magi, 1984.36, and Rest on the Flight into Egypt, 1984.37, already existed. Their two pending museum assertions were superseded by accepted holding assertions. Existing exact 1715 dates, artwork metadata, images and artist links were preserved; the native circa dates remain citation evidence. No duplicate objects were inserted.

The 18 holds cover the missing Trinity, five creation ranges that repeat a creator’s lifespan or activity, the reverse of an existing Fuseli painting, a conflicting Gérôme object classification, and ten unresolved physical versions. School, workshop and attributed creators remain qualified object labels. The small triptych, perspective box and Four Continents canvas each count once. The jointly credited Bull in a City Street retains both creators. Apparent native dimension errors remain literal and explicitly noted, without invented corrections.

The transaction preserves all 26 scoped existing Detroit/comparison records except the exact two holding changes. Fresh table digests also show that all 6,099 earlier campaign artworks and their associated artist links, media links, media assets, identifiers, citations and assertions remain unchanged from the preflight. Replay performed zero writes. All **830 offline campaign checks pass**, including eight new checks against unintended date, image, publication, creator, old-evidence and display changes. These are correctness checks, not a ten-million-row load test.

Wave52 preserves the frozen wave51 full verification and verifies this explicit delta; it does not rerun obsolete total-count assertions against the new database state. Backups and raw test logs are under `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-expansion-20261006/`. No production database, publication, current-display assertions or catalogue images changed.

The overall goal remains active. Campaign totals are 5,426 new artworks and 767 existing-work museum links across 163 expanded institutions. There are still 1,197 canonical museums below 100 linked records. The unrelated minimum-100 job remains separate and unchanged. Baltimore’s official catalogue is the next research pass; its discovery has not supplied any additions to these totals.
