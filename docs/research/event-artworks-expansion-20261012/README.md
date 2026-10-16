# More event illustrations from the Artline catalogue — 12 October 2026

The user requested more event pictures from existing Artline artworks, including
suitable contextual paintings where a direct depiction is unavailable. This
continuation adds 367 reviewed event selections using 229 existing illustrated
artworks. It preserves the previous 70 event selections. The API update is deployed and verified in production.
Release receipt: `docs/deployment-20261012-event-artworks-expansion.json`.

## Coverage

- 10,026 active historical events included in the discovery inventory.
- 303,706 illustrated artwork titles searched using a narrow research export;
  candidate details were enriched only for the discovered artwork IDs.
- 367 additional event selections: 127 depictions, 34 artistic/historical context,
  198 views of associated places, and 8 related portraits.
- 183 previously unillustrated events gain a picture; 184 independent event
  pictures are replaced by suitable catalogue works.
- 437 events now have a selected internal artwork link, including the prior 70.
- 3,668 independent illustrations remain; 5,921 events still lack a verified
  selected illustration. This pass does not claim complete event coverage.
- No new catalogue records, image uploads, publication changes or database writes.

Examples include World War I, the Battle of Grunwald, the French Revolution,
the Salt March, the Industrial Revolution, the Spanish Civil War, the
Reformation and the Treaty of Delft.

## Selection and image review

Title searches generated leads, not automatic approvals. The final event–work
choices were reviewed for subject, event year, city identity and creator/sitter
identity. Place views and portraits are contextual editorial choices, explicitly
labelled as such. Their creation dates remain separate from event dates.
Country names occurring in the event `people` field were not treated as sitters.

All 233 candidate reproductions were viewed on labelled contact sheets; 229
unique works are in the final additional selection. Every selected local file
was decoded and checked against its catalogue SHA-256. Public delivery and
internal destinations are checked separately in the release receipts. Source
reproductions were preserved without cropping, retouching or enlargement.
One selected Famagusta harbour image is a small existing source reproduction;
that limitation is recorded in the image review ledger.

Final review rejected Athens, Tennessee/Greece; Córdoba, Mexico/Spain;
Portsmouth, New Hampshire/England; and the Ravenna/Rimini event discrepancy.
The Buffalo AKG record identifies Marc's *The Wolves* with the First Balkan War,
so the separate Second Balkan War candidate was held. The Ypres picture is an
allegory, and its caption was corrected accordingly. An alternative Copenhagen
picture avoids a reproduction with a calibration strip. The Famagusta choice
uses an existing harbour painting instead of a heavily watermarked reproduction;
the source images themselves were not edited.

Primary museum pages support the Delacroix/Missolonghi, Picasso/Guernica,
Bose/Salt March, Menzel/industrialization and Marc/Balkan War relationships.
Other selections retain their existing museum, WikiArt or source-file citations.
This does not claim that every source page was fetched again during this pass.
Unknown artwork metadata, dates, credits, rights labels and review states remain
unchanged. Allegories and later interpretations are not presented as eyewitness
records. Museum ownership is not treated as current display.

## Implementation

Only three API files change: the event artwork selection manifest, its Go
resolver, and its tests. New selections can supply an explicit relationship,
caption and HTTPS evidence URL without needing a legacy event-image entry.
Validation requires the event/source pair to agree. The existing resolver fetches
current catalogue media and internal artwork destinations for the bounded event
page, using indexed artwork slugs and one SQL query. Selected works with missing,
archived, unsafe or excluded media remain omitted. No schema or web change is
needed. Existing event pictures and captions already link to the artwork page
or the existing artwork drawer for records without an active artist link.

The tests cover new selections without legacy images, required contextual
metadata, source mismatches, explicit captions overriding old captions, current
media, withdrawal and scope. All 437 selections resolved in a production
read-only transaction; its query plan used the artwork slug index. Events and
member suites passed. The HTTP suite passed excluding the previously reproduced
baseline failure `TestBooksAcceptLegacyParametersAndValidBounds`, unrelated to
these changes. No stored fixtures or test databases were created. This is not a
10-million-row load test. Existing study snapshots were not rewritten.

## Evidence

Full research, the 10,026-event coverage ledger, candidate details, rejected
matches, source URLs, image checks, visual review sheets and scripts:

`~/Library/Application Support/Artline/source-metadata/event-artworks-expansion-20261012/`

Production source preimages, generation-pinned three-file overlay, build and
verification receipts, browser screenshots and rollback revision:

`~/Library/Application Support/Artline/backups/event-artworks-expansion-20261012/release/`

The real local catalogue is unchanged. No commit or Terraform apply was made.

## Delivered release

Revision `artline-api-event-artworks-expansion-1012-v1` serves 100% of API traffic. The source
was reconstructed from the previous production build and changed only by the
three-file reviewed overlay. The web service was not redeployed. Before and
after promotion, all 437 event links returned the expected artwork, caption and
current image; every public image matched its local SHA-256. Five event cases
were checked at desktop and mobile widths: French Revolution, Salt March,
Treaty of Delft, Reformation and World War I (previously without an image).
Image/caption navigation, keyboard activation, Back navigation, image loading,
layout overflow and axe checks passed. No new-revision ERROR logs were found.
The in-app browser could not initialize; standalone Playwright was used.
