# Open-access follow-up — 19 September 2026

**3 more CC0 images uploaded to local and production. Combined with the preceding pass: 12 new images across 9 painters.**

| Painter | Artwork | Museum |
| --- | --- | --- |
| Conrad Laib | Adoration of the Magi | Cleveland |
| Henri-Jean Guillaume Martin | Woman in Profile | Cleveland |
| Luis de la Cruz | Princess María Francisca and her son — obverse view | Met |

These were existing artwork records with accepted museum links and accession numbers but no native museum identifier. Exact museum identifiers and source citations were added to those same records; no duplicate or new artwork was created. Existing titles, dates, artist links, holdings, research flags and review statuses remain unchanged.

All three images were visually reviewed, retain the full source view, and are under 100 KB (243,888 bytes total). [Storage, rights and database verification](native-id-gaps/delivery-verification.json) and [final public delivery / preservation checks](native-id-gaps/final-public-delivery.json) verify all three files and artwork APIs without errors.

## Editorial notes

- Cleveland's source date intervals for Laib and Martin are broader than the catalogue's existing precision. Both are retained in evidence; no dates were silently normalized.
- The Met's primary photograph shows the **obverse** of a two-sided miniature. Its [official page](https://www.metmuseum.org/art/collection/search/436059) explicitly identifies the obverse and reverse. Only the primary obverse image was downloaded. Museum and catalogue biographical dates differ, but the museum's explicit creator authority `Q1876555` matches the existing artist. No biography was changed.
- Chae Yong-sin's *Portrait of a Government Official* remains held: the source creator spelling and birth year differ, requiring individual authority reconciliation.
- Met metadata-only continuation examined 111 previously unattempted candidates: 79 lacked an explicitly open image, 31 returned access errors, and 1 source was missing. Workers paused on repeated errors; 684 candidates remain unattempted in that queue. No access controls were bypassed.

## Potential next additions — not imported

**Subsequent update:** The user approved adding new verified museum works. All ten leads below were freshly checked, visually reviewed, imported in review, and delivered with CC0 images. See the [completed new-artwork batch](../open-access-new-artworks-20260919/README.md). The discovery-stage account below is retained as historical evidence.

Read-only research found 70 Cleveland source leads without an existing native identifier. Duplicate checks held 60 and left **10 potential new works**: 7 paintings, 2 drawings and 1 print. They concern existing painters, including Ikkyū Sōjun, Iwasa Matabē, Kaigetsudō Ando, Miyagawa Chōshun, Cornelis Saftleven, Ishikawa Toyonobu and Lucas Velázquez.

These are metadata leads from a preserved museum capture, not completed uploads. Fresh object checks and image review remain required. No new records or images for these ten works were imported while the user's choice about expanding beyond existing records remains pending. Evidence: [selection report](cleveland-discovery/selection-report.json) and [duplicate-screened draft plan](cleveland-discovery/plan.json).

Recovery preimages for the three uploads are under `/Users/vadimdulub/Library/Application Support/Artline/backups/open-access-followup-20260919/native-id-gaps/`; their checksums are in [backups.json](native-id-gaps/backups.json). Draft discovery snapshots use the existing planner's historical backup tree, `backups/overnight-images-20260915/cleveland-discovery/`.

Seven offline image-clearance tests passed. No test databases, catalogue fixtures, artwork imports, status publication, deployment or commits. The initial `preservation-and-public-delivery.json` has correct checks/counts but inherited a hard-coded narrative from the earlier nine-image batch; the final linked report uses the corrected generic narrative. Both captures are retained.
