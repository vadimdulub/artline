# Marc Chagall: selected painting additions — 19 September 2026

Added **10 paintings** to the real local catalogue, increasing Marc Chagall’s painting records from **77 to 87** (738 to 748 total artwork records). All additions remain in review and unpublished. All 738 prior artwork rows were compared inside the import transaction and remained unchanged.

## Selection

| Painting | Date | Documented collection | Primary evidence |
|---|---|---|---|
| Paris Through the Window | 1913 | Solomon R. Guggenheim Museum | [Museum source](https://www.guggenheim.org/wp-content/uploads/2025/05/Faith-Ringgold-Press-Kit-Full.pdf) |
| Green Violinist | 1923–1924 | Solomon R. Guggenheim Museum | [Museum source](https://www.guggenheim.org/wp-content/uploads/2025/05/Faith-Ringgold-Press-Kit-Full.pdf) |
| The Promenade | 1917–1918 | State Russian Museum | [Museum source](https://rusmuseumvrm.ru/data/collections/painting/19_20/zhb_1726/index.php?lang=en) |
| The Yellow Room | 1911 | Fondation Beyeler | [Museum source](https://www.guggenheim-bilbao.eus/en/press-room/images/chagall-the-breakthrough-years-1911-1919) |
| The Cattle Dealer | 1912 | Kunstmuseum Basel | [Museum source](https://www.guggenheim-bilbao.eus/en/press-room/images/chagall-the-breakthrough-years-1911-1919) |
| The Flying Carriage | 1913 | Solomon R. Guggenheim Museum | [Museum source](https://www.guggenheim-bilbao.eus/en/press-room/images/chagall-the-breakthrough-years-1911-1919) |
| Self-Portrait | 1914 | Kunstmuseum Basel | [Museum source](https://www.guggenheim-bilbao.eus/en/press-room/images/chagall-the-breakthrough-years-1911-1919) |
| Jew in Black and White | 1914 | Kunstmuseum Basel | [Museum source](https://www.guggenheim-bilbao.eus/en/press-room/images/chagall-the-breakthrough-years-1911-1919) |
| The Newspaper Vendor | 1914 | Musée National d'Art Moderne | [Museum source](https://www.guggenheim-bilbao.eus/en/press-room/images/chagall-the-breakthrough-years-1911-1919) |
| The Soldier Drinks | 1911–1912 | Solomon R. Guggenheim Museum | [Museum source](https://www.guggenheim-bilbao.eus/en/exhibition/modernidad-y-tradicion) |

The new works are personal Artline selections in the owner’s review collections; they are not represented as museum-designated highlights. Source collection credits establish holding associations only. No current-display assertions were added. The two Im Obersteg works retain their permanent-loan context, distinct from ownership.

## Dates and missing fields

- The Russian Museum object page gives *The Promenade* as 1917; its collection overview and the Bilbao checklist give 1917–1918. The complete documented interval and discrepancy are retained in the record and source evidence.
- *Paris Through the Window* uses the Guggenheim 2025 checklist’s dimensions; the older Philadelphia exhibition’s slightly different measurements are retained in the evidence note.
- *The Yellow Room* has no imported accession number. The direct Beyeler collection page returned 404; its metadata and collection credit are supported by the captured official Bilbao checklist.
- Existing similarly titled prints, drawings and unresolved records were preserved. Deduplication checked the artist’s full scoped inventory, matching title/date intervals, accession numbers, exact IDs, slugs and target museum accessions.

## Images

No image assets were downloaded or attached. The selected sources do not establish a reusable image licence for this app. The [Bilbao image page](https://www.guggenheim-bilbao.eus/en/press-room/images/chagall-the-breakthrough-years-1911-1919) limits its offered permission to non-commercial editorial use with the relevant museum information and requires written approval for other uses. Copyright notices and the raw captures are preserved; photographs were not assigned invented public-domain or Creative Commons labels.

The Stedelijk object response was empty, the Commons rights API request returned 403, and the Beyeler direct collection routes returned 404. These were not bypassed or used as verified metadata. Additional research captures do not imply inclusion in the selected batch.

## Validation and recovery

- `preflight.json`: read-only check passed for all 10 additions. No fixtures or test databases were created.
- `selected.json` and `selection-manifest.json`: exact 10-record selection and SHA-256; all used source bytes match their capture receipts.
- `local-applied.json`: transaction receipt; review state, pre-1970 eligibility, selection evidence, absence of display assertions and preservation of previous works checked before commit.
- `verification.json`: independent read-only counts plus successful native Painter and All detail endpoints for all 10 paintings. All 10 are returned with the All Highlights filter enabled for 1900–1930.
- Hidden Chrome check opens *Paris Through the Window* and verifies its title, date, creator lifespan and museum information. Screenshot remains in `/tmp/artline-chagall-new-painting.png`.

Recovery archive and exact preimages:

`/Users/vadimdulub/Library/Application Support/Artline/backups/chagall-paintings-20260919/`

The `local-before.dump` archive was listed and checksum-verified before mutation; `backup.json` retains its path, size and checksum. No restore was performed.

This delivery is **local only**. No cloud import, image upload, publication, deployment, schema migration or commit was performed. The bounded import tool is `ops/import-chagall-paintings.py`; its default invocation is a read-only preflight and applying an already present selection is refused.
