# Athens icons — exact image review, 12 September 2026

## Crucifixion, ΒΧΜ 01354 — image attached

- [x] Existing artwork `de1c163d-25b8-4772-9de7-f0987ae92525`; no duplicate artwork.
- [x] [Official notice](https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=33): Workshops of Constantinople, 14th century, double-sided icon, 103 × 84.5 × 4.5 cm. Accession ΒΧΜ 01354. Existing 1301–1400 century interval preserved.
- [x] [Exact-object Commons category](https://commons.wikimedia.org/wiki/Category:Double-side_icon_with_Crucifixion_and_Hodegetria_(14th_century,_Byzantine_museum)) links that official notice and accession. Category rounds width to 85 cm; not used to overwrite catalogue dimensions.
- [x] [Photograph](https://commons.wikimedia.org/wiki/File:Double-side_icon_with_Crucifixion_and_Hodegetria_(14th_century,_Byzantine_museum)-.jpg): Yair-haklai's own photograph, CC BY-SA 4.0. Full front/Crucifixion side visually inspected. Mounts, perspective and existing damage remain; no extra crop, retouching or invented detail.
- [x] 96,550-byte JPEG attached; 704 × 900, SHA256 `4a3883366b3238c640c33ef915434159b2c69480834a55ae2c368dc9104af45f`. Full decode, served hash, source/credit/licence, museum discovery and access-control checks passed.
- [x] Photographer credit and share-alike licence retained in API. Workshop creator remains an unlinked label; no fake person or popular-painter flag created.
- [ ] Reverse/Hodegetria photograph is a separately licensed lead, not attached. Do not create a second artwork for the reverse side.
- [ ] Broader icon research remains open.

Local application file:
`apps/web/public/assets/artworks/imported/icons-athens-commons-study-4a3883366b3238c640c33ef915434159b2c69480834a55ae2c368dc9104af45f.jpg`.

Image selection v2 SHA256 `ef9274c7a9a2db7799049fba14d1c89d8126661c6868799bce126fc465eeeff7`.
Receipts `output/data-collection-20260911-2016/athens-icon-{selection-v2,preview,apply,before,after,api}.json`.
Four API checks, one full decode/served hash, whole-DB preservation passed. First
selection was superseded before application to clarify exactly what was visually
checked. No ownership, display, publication or masterpiece assertion added.

Backup `before-athens-icon-image.dump`, in the relocated backup folder;
SHA256 `175a5992efe7633281e2eb1d8a43556941d083f7a3306a1544b2b82571bf8606`.

The 357,246-byte source photograph used for visual inspection is provenance, not
a web asset. It and its receipt were moved out of Documents, without changing
their hashes, to `/Users/vadimdulub/Library/Application Support/Artline/source-images/athens-icon-20260912/`.
Source SHA256 `4229a75b03274beba52ed4e110d92c1383ed1c134fcebe5fdb3827c82f12e417`.
Only the <=100,000-byte derivative is served by the app. Commons API capture and
official museum HTML remain in the research evidence directories.

## The Hospitality of Abraham, ΒΧΜ 01544 — deferred

Existing artwork `5db99379-dca7-4108-95ec-c206a1ecf172` remains unchanged.
The [official notice](https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=43)
identifies an early 15th-century Cretan-workshop icon, 97 × 71.5 cm.

A search for this accession also returns [Tribute to the Eucharist, attributed to
Michael Damaskinos](https://commons.wikimedia.org/wiki/File:Tribute_to_the_Eucharist_Michael_Damaskinos.png),
with different subject, century and dimensions. That Commons/Wikidata accession
is conflicting evidence, **not a match**. No photo or artist link imported from it.

The [matching Hospitality file](https://commons.wikimedia.org/wiki/File:Hospitality_of_Abraham_(Zakynthos,_15th_c.,_Byzantine_museum).jpg)
lists the right object but lacks the requested United States public-domain tag
and points to the museum's photograph. Rights/provenance remain deferred; no
image downloaded. Mirrors do not solve that gap.

## Nativity, ΒΧΜ 01099 — search incomplete

Rechecked [official notice](https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=248):
24 × 34 cm, third quarter of the 14th century, qualified Venetian/Greek-Venetian
workshop attribution. Exact-accession Commons search did not return a verified
image candidate. This is not proof that no reusable image exists. No mutation.

## Backend safeguard

The prior image selector required a named primary painter. A closed, exact-ID
path now accepts this one reviewed workshop icon while requiring no existing
artist links, the exact attribution/date/accession, an active source and an
accepted museum holding. Existing hidden/archived artists cannot be bypassed.
Negative offline tests reject identity, image URL, licence, credit and source
changes. No fixture database was created or used. General anonymous-image
coverage and additional qualified attributions still need separate review.
