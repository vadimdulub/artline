# Ensor / Nicholson image audit and catalogue interface — 13 October 2026

The request covers missing-image messages, the artwork viewer, the Ensor-to-MoMA
museum link, James Ensor and Ben Nicholson image research, consistent catalogue
controls, and museum loading. The catalogue UI release is deployed and verified
at https://artlines.org from commit `e7004edc`. See
[the deployment receipt](../../deployment-20261013-catalogue-ui.json).
Unreleased museum-studio publication/streaming work remains local and is excluded
from this release; the current production member-access rules remain in place.

## Delivered production images

| Artist | Active works | Illustrated before | Illustrated after | New images |
| --- | ---: | ---: | ---: | ---: |
| James Ensor | 244 | 79 | 130 | 51 |
| Ben Nicholson | 40 | 21 | 21 | 0 |

All 51 additions are existing Ensor print records with an exact Rijksmuseum native
object ID. The official EDM object/aggregation/primary-image relationship and
Public Domain Mark evidence were checked. All derivatives were visually inspected
in five numbered contact sheets. Separate impressions, full paper margins and
source framing remain intact; derivatives are 59,831–99,846 bytes. Cloud Storage
uploads and public HTTP downloads were SHA-256 checked for every file.

Production attachments used the shared ingestion locks and checked current object
identity, source ID, revision and missing primary image before writing. Existing
metadata, creation dates, attribution, holdings and review states were independently
verified unchanged. The real local catalogue received no writes. Recovery snapshots
are local Application Support files; no Cloud SQL backup was created.

## Museum investigation and remaining images

The repository's read-only museum query returns **48 Ensor artworks and zero
illustrated works** for `wikimedia-museum-q188740?artist=james-ensor-q158840`.
The missing images are absent from those records, rather than discarded by the
frontend. The baseline contained 55 MoMA objects across both requested artists
(48 Ensor and 7 Nicholson). “Death of Jezebel” is a different record, held at the
Art Institute of Chicago, accession 1960.156 / native ID 11826.

The official Chicago API identifies an image for “Death of Jezebel” but labels it
copyright-controlled. Similar holds exist for selected Chicago, NGA, Met and
Cleveland records. A request to extend the user's WikiArt approval to these two
artists' official museum reproductions is pending. No such approval has been
assumed. The existing MoMA website/image access hold also remains in effect;
previously captured official CSV metadata supplies 42 Ensor and seven Nicholson
image URL leads without new requests to that held surface. One Nicholson catalogue
record is classified as sculpture and remains outside this pictorial-image pass.

The current WikiArt HTML indexes yielded 46 Ensor and 22 Nicholson entries.
Artist profiles and targeted web searches were cross-checked. All 21 through-1970
Nicholson entries in those indexes already have catalogue images; the additional
1979 work is outside the general creation-date scope. Indexed site summary counts
(49 and 27) exceed the currently enumerated HTML lists; they are not treated as
proof that every listed reproduction was found.

An apparent candidate for MoMA's “Masks Confronting Death” was **not** attached:
the existing WikiArt “Masks Mocking Death” image has incompatible proportions and
an apparent 1897 signature, while the MoMA object is dated 1888. Title similarity
is insufficient to establish the same work. No image from another museum's print
impression was copied to fill MoMA gaps.

See `catalogue-image-audit.csv` for every baseline object and its current image
state. Image discovery is not complete worldwide; the remaining source and access
holds are explicit.

## Interface changes

- Shared artwork images show “Image not available” for absent/invalid/failed
  images, including the main artwork directory and artist artwork views. The
  old symbol/number placeholder is removed. Mixed illustrated/unillustrated cards
  align at the top even when their titles wrap differently. A failed source no longer suppresses
  a different image after navigation.
- Unillustrated full-screen records keep a centered message and compact Details
  control, without an empty zoom toolbar. Details, Escape, close and retry remain
  usable. Artist directory entries that have no portrait field remain text cards.
- Museum official-site links use a small accessible link icon beside the name.
  The “Exhibition information” disclosure is removed.
- Catalogue search, selection, layout, sort, page-size and pagination share
  control geometry and type. Existing page families and navigation icons remain.
- The authenticated museum directory renders the initial bounded page on the
  server and reuses it on hydration. Session cookies are allowlisted through the
  existing helper. A route loading state gives immediate navigation feedback.
  Publication streaming changes for the unfinished museum studio remain local.

## Validation and limits

- Root TypeScript and targeted ESLint checks pass.
- Optimized Next production build passes in the isolated preview; the standalone
  server passes the browser checks. Its bounded public directory mirrors deployment,
  where artwork assets are served separately; linking the entire local asset library
  exceeds Next’s startup directory-walk stack. Root TypeScript also checks the full
  test tree; the isolated production build excludes tests whose fixture imports live
  outside the copied web directory. Temporary browser fixtures live only under `/tmp`.
- Viewer tests cover absent images, load failures, recovery on a changed source,
  and usable full-screen details. Focused run: 23/23 passing.
- Full web suite: 577/579 initially passed. The connections focus test passed on
  rerun; the existing signed-out BackNavigation/member-access test still fails
  in the unrelated navigation changes. That code was not changed in this pass.
- Server-rendered directory cards verified in the initial HTML; zero duplicate
  museum requests on hydration and one request after changing search.
- Browser checks at 1440, 390 and 320 pixels: Details is approximately 81 × 44 px,
  no horizontal overflow, readable fallback, retry and Escape behavior. Museum
  toolbar controls are 44 px high with matching 4 px radii and 14 px desktop text.
- Read-only production-sized SQL audit: 1,961 nonempty museums, 24 bounded cards.
  Initial cold directory audit took 4.5 s; warm existing queries took roughly
  0.4–0.5 s. Experimental highlight SQL regressed filtered cases and was reverted.
  No database performance improvement is claimed from cache warming. The final
  loading changes remove browser/secondary-publication waits. Ten-million-row
  load testing and production latency validation remain separate work.

## Evidence locations

- Metadata, captures, source selection, visual decisions, upload receipts,
  delivery and independent verification:
  `~/Library/Application Support/Artline/source-metadata/ensor-nicholson-20261013/`
- Original reproductions:
  `~/Library/Application Support/Artline/source-images/ensor-nicholson-20261013/`
- Recovery snapshot:
  `~/Library/Application Support/Artline/backups/ensor-nicholson-20261013/`
- Disposable browser screenshots, query plans and test/build output:
  `/tmp/artline-catalogue-ui-20261013/`

## Production release verification

The exact release source passes TypeScript, an optimized local production build,
and 19 focused viewer/artist/connections tests. Candidate and live browser checks
cover artwork cards, missing-image details, the Ensor fullscreen viewer at 1440,
390 and 320 pixels, exhibition search/reset and aligned fields, museum sign-in
with retained destination, and unchanged English/Russian Louvre guide text.
Signed-in museum controls and initial directory rendering were checked locally
against captured read-only API responses, with zero duplicate hydration requests.
The API, real local database and production catalogue were not changed by this
application release. The previous 51-image delivery remains a separate operation.
