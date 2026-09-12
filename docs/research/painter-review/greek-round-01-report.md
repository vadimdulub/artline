# Greek painter research — first bounded round, 10 September 2026

## Result and scope

Added **nine painter records and ten artworks**, reusing the existing Nikolaos
Gyzis authority without changing its fields. Totals are now **5,324 painters,
105,953 artworks and 403 pictures**. No Greek photographs were downloaded.

The full index includes all existing painters and artworks, not just this selection.
The ten completed artwork decisions below concern factual source review and the
attempt to establish reusable imagery. Nine painter decisions are complete for
their current one-work database scope plus the bounded source search; Economou's
biography is blocked. This is **not** a completed full-catalogue round, nor ten
repetitions of the requested research. Rounds 2–10 remain unstarted.

## Individually reviewed selection

| Painter | Work added | Date / accession | First-pass result |
|---|---|---|---|
| Nikolaos Gyzis | [The Glory](https://www.nationalgallery.gr/en/artwork/the-glory/) | 1898 · Π.1701 | Source review done; photograph permission unresolved |
| Georgios Iakovidis | [Children’s Concert](https://www.nationalgallery.gr/en/artwork/childrens-concert/) | 1900 · Π.475 | Source review done; photograph permission unresolved |
| Nikephoros Lytras | [Funeral Flowers](https://www.nationalgallery.gr/en/artwork/funeral-flowers-6505/) | 1901 · Π.48 | Source review done; photograph permission unresolved |
| Konstantinos Volanakis | [Collecting the Nets](https://www.nationalgallery.gr/en/artwork/collecting-the-nets/) | 1871 · Π.10380 | Source review done; photograph permission unresolved |
| Konstantinos Maleas | [Aswan](https://www.nationalgallery.gr/en/artwork/aswan-1291/) | 1924 · Κ.1232 | Source review done; E. Koutlidis Foundation credit preserved |
| Michael Economou | [Brittany](https://www.nationalgallery.gr/en/artwork/brittany-1509/) | 1924 · Κ.461 | Artwork review done; painter birth-date conflict unresolved; foundation credit preserved |
| Konstantinos Parthenis | [Christ](https://www.nationalgallery.gr/en/artwork/christ-2/) | ca. 1900 · Π.522 | Source review done; approximate artwork date and uncertain birth date retained |
| Fotis Kontoglou | [Saint Matthias](https://www.nationalgallery.gr/en/artwork/saint-matthias-5351/) | 1956 · Π.2992 | Source review done; egg tempera on hardboard retained |
| Vasileios Chatzis | [The Harbour of Kavala](https://www.nationalgallery.gr/en/artwork/the-harbour-of-kavala/) | 1913 · Π.453 | Source review done; photograph permission unresolved |
| Theodoros Rallis | [Lady in the Countryside](https://www.nationalgallery.gr/en/artwork/lady-in-the-countryside-3278/) | 1893 · Π.1821 | Source review done; photograph permission unresolved |

The pastel *The Glory* uses the local drawing category with the literal medium
preserved. No new museum-highlight or owner-selection labels were assigned.
These are selected museum-catalogued works, not ten museum-designated masterpieces.

## Source and identity decisions

- Artist pages and individual object pages were checked separately, including
  exact artist hyperlinks, accession identifiers, literal dates and collection credits.
  Museum-listed spelling is retained in the source manifest. New authority keys
  are museum artist URLs, not invented Wikidata IDs or approximate name merges.
- [Parthenis's museum biography](https://www.nationalgallery.gr/en/artist/parthenis-konstantinos/)
  gives 1878/1879. The numeric birth year stays null and the timeline is explicitly
  estimated. The approximately dated *Christ* remains `circa`, not an exact 1900 date.
- [Economou's museum biography](https://www.nationalgallery.gr/en/artist/economou-michael/)
  gives 1884, while the [Greek Ministry of Culture's Averoff exhibition account](https://www.culture.gov.gr/el/Information/SitePages/view.aspx?nID=4729)
  gives 1888. This conflict is not resolved by guessing; numeric birth year remains
  null and the painter review remains blocked. The separately dated 1924 work is eligible.
- New GR links mean cultural affiliation in the Greek art catalogue, not inferred
  citizenship or Greek birthplaces. Constantinople, Aivali and Alexandria must not
  be silently converted to modern Greek places.
- The [museum's terms](https://www.nationalgallery.gr/oroi-chrisis/) permit limited
  personal/educational/research use but do not establish unrestricted republication
  rights for these photographs. Only selected factual pages were captured privately
  for research; no images, API crawl, social-share URLs or pagination were fetched.
- The official pages sometimes state “On view” and name an annex. This batch does
  not create display assertions, room assignments or an ownership claim. Foundation
  collection credits remain in the object descriptions and holding evidence.
- Kontoglou broadens the Greek/icon-painting research direction, but a work dated
  1956 is not an ancient Byzantine object. Its literal medium is retained; this batch
  does not replace the separate Russian/Greek/Byzantine priority queue.

## Further discovery, still pending

The [National Gallery's artist directory](https://www.nationalgallery.gr/en/artists/)
is a source for future bounded selections, not evidence that its entire collection
has been imported. Continue with less-represented Greek artists, including women:
Sophia Laskaridou, Flora-Karavia Thaleia, Aglaia Pappa, Spyros Papaloukas, Theofilos,
Theophrastos Triantafyllidis and Rallis Kopsidis. Confirm individual identities and
eligible object records before creating entries. Cypriot painters and anonymous
post-Byzantine workshops also remain priorities.

Several reviewed artist pages expose many more works than this selection. Those
are discovery leads, not silently marked finished objects. Later passes should
use new eligible additions, alternate collections and individually licensed images.

## Verification and receipts

- `go test ./...` and `go vet ./...`: passed (ordinary suite; opt-in scale tests
  are not included). The previously observed European identity query-plan failure
  remains documented in the programme README.
- `ops/verify-painter-review.mjs`: checked all **5,324 painter Markdown pages**,
  all **105,953 unique artwork inventory rows**, every linked artwork entry and
  **21 unlinked creator records**. All **105,943 pre-existing artwork fingerprints**
  and all **5,315 pre-existing artist rows** are preserved.
- **36 local API checks** passed: museum paging, individual work fields, no fake
  display/highlight/image labels, authenticated preview and public 404s, and
  estimated timeline treatment for the two uncertain biographies.
- Preview rolled back; apply added only the selected records and source evidence;
  replay reported all 20 artist/artwork matches preserved without duplicate additions.
- Museum-highlight items remain 569; owner-selection items remain 5; published
  artworks remain 0. Image assets remain 403.
- Verification receipt: `output/painter-review-verification-v1.json`.
- Import receipts: `output/greek-painter-review-{preview-v2,apply-v1,replay-v1}.json`.
- Approved selection SHA256:
  `b91b869d01d13e8889182b77f99b2867298cc0ca22637b3b253a0966b56eadc0`.
- Pre-import backup:
  `/Users/vadimdulub/Documents/artline-greek-review-backup-20260910.xGJWei/before-greek-review.dump`.
  SHA256 `6817a29daf0e0545f222e86ef2e6b2fcbf71a95f4179bb58d500b5069530c719`.
  `pg_restore --list` read the archive successfully; a full restore was not tested.

No commits, publication, external writes, cloud deployment or Terraform changes.
