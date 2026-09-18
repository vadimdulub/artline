# Italy: image research findings

This report concerns the existing Italy catalogue: Italian museum holdings, plus Italian artists held abroad. It is an image enrichment campaign, not a new artwork import or publication decision. The final duration and attachment totals are recorded in [status.json](status.json); every retained image is listed in the [credit ledger](image-credit-ledger.json).

After the user confirmed public or potentially commercial app use, **10 uploaded images remain attached** in both databases: **five privately owned Poldi Pezzoli works and five Italian artists' works abroad**. An additional **49 images were withdrawn pending commercial cultural-property reuse clearance**. The original four-hour completion reported 59; its timestamp and evidence are preserved in the [commercial follow-up](commercial-use-review-20260917/README.md). The selected Italian holdings include works by artists from other countries; origin and holding location are separate facts. No artwork title, creation date, creator relationship or publication status was changed.

The campaign advanced 715 distinct existing artwork targets through 63 selection rounds. Its bounded photographic searches preserved 729 queries and 1,178 distinct file-metadata leads; these are research results, not approved or downloaded images. Repeated targets and alternative photographs are counted separately from final attachments. [Scope definitions and counts](research-scope-counts.json).

## What the audit actually measures

The initial Italy-related scope contained 11,212 records, including Italian artists abroad. Its 4,894 eligible, selected image gaps included 1,048 paintings, 1,934 drawings, 1,911 prints and one fresco. These are catalogue counts, not a proposed download target. [Initial audit](local-audit.json).

The narrower Italian-holdings audit contains 2,557 records across 54 institution identities. Of those, 2,526 were eligible and selected at the start. Read-only queries against those original IDs, in pages of 500, found the same results in local and production databases after the commercial-use correction:

| Measure in the original Italian-holdings cohort | At start | After attachments |
|---|---:|---:|
| Eligible selected records with images | 84 | 89 |
| Painting image gaps | 683 | 678 |
| Drawing image gaps | 1,736 | 1,736 |
| Print image gaps | 22 | 22 |
| Fresco image gaps | 1 | 1 |

This cohort is strongly shaped by existing Lombardy catalogue imports. It is not a census of Italian art or all Italian museums. A separate [Italy museum research report](../italy-museums-deep-20260916/README.md) addresses wider national coverage. [Current read-only cohort recheck](commercial-use-review-20260917/italian-holdings-recheck.json), [remaining gaps by collection and medium](REMAINING-GAPS.md).

## Retained images

| Holding collection | Images retained |
|---|---:|
| Museo Poldi Pezzoli | 5 |
| Academy of Fine Arts Vienna, Italian artists | 3 |
| Metropolitan Museum, Italian artists | 2 |

The Academy of Brera and Pinacoteca di Brera are distinct institutions. Likewise, the Castello's paintings collection and its graphic collections require distinct object and source checks. Generic regional-catalogue website fields were resolved only in research evidence where an institutional source was established; database institution metadata was preserved.

## Why available pictures did not all become attachments

**Source terms.** A public-domain painting, a Commons file label, a museum photograph and a website's reuse conditions are different pieces of evidence. Conflicting terms remain unresolved rather than being discarded. During this campaign, 100 provisional image attachments were withdrawn after further source review. One old Titian reproduction was replaced with the Academy of Fine Arts Vienna's explicitly licensed native photograph. Those 99 artworks stayed held at four-hour completion. The subsequent commercial-use review added 49 holds, so 148 artworks now have withdrawn campaign images (149 old media files, including the replaced Titian file). The [original withdrawal recheck](withdrawn-media-recheck-20260917T0035.json) confirms that all 100 obsolete media records have unknown rights, no primary artwork references and no remaining campaign copy in public storage. The [commercial withdrawal verification](commercial-use-20260917-rights-hold/verification.json) separately covers the added 49 holds. Original evidence and private backups remain available.

For example, Carrara's visitor and image-request terms, Ambrosiana's image-distribution process, and KHM's noncommercial conditions require source-specific resolution for this application. These are operational clearance decisions; they do not determine the validity of copyright claims in the underlying paintings. The exact sources and access limitations are preserved under [institution-rights-holds](institution-rights-holds/).

The Science Museum in Milan provides an especially useful caution. Its `/open-access` link is labelled “Oggetti con immagini”, meaning a catalogue filter for objects with pictures. Its linked art metadata dataset carries CC BY-SA 4.0, while the current collection-image terms specify a default CC BY-NC 4.0 licence with additional permission for other uses. Neither the URL nor the metadata licence cleared the two Monticelli pictures. No image bytes were downloaded for those candidates. [Primary museum terms](https://www.museoscienza.org/it/termini-condizioni-catalogo-collezioni), [saved source review](museoscienza-policy-review/decision.json).

**Exact physical work.** Similar titles and compositions are insufficient. Bianchi's *Ritorno dalla sagra* candidate showed a red umbrella, whereas the target GAM inventory has a blue umbrella and different figures. The selected native-origin *Laocoonte* reproduction was horizontally reversed relative to the exact catalogue sheet. Foppa's *Madonna del libro* had conflicting creation dates between the actual authority record and the native catalogue. Those candidates were held; their dates and identities were not silently repaired.

**Photographic suitability.** Other holds concern cropped details, labels, severe glare, perspective, low resolution or substantial colour differences. A larger independently documented *Odalisca nel sonno* replaced a 201 × 250-pixel lead before its initial attachment; that image is now held for commercial reuse clearance. Segantini's *Dea dell'Amore* remained held because the selected older reproduction differed substantially in colour from the catalogue; later conservation history makes an unsupported claim about current appearance inappropriate. No synthetic repair, recolouring or mirroring was performed.

**Access.** Selected Chicago and Minneapolis image requests returned HTTP 403. Those deliveries were held without alternate-user-agent or access-control workarounds. Some institutional policy pages were available only through indexed primary-source text; the evidence explicitly distinguishes that from a successful preserved HTTP capture.

## Two identity findings worth retaining

GAM inventory GRASSI 139, *Les bretonnes et le pardon de pont Aven*, is documented as a Van Gogh watercolour after an Émile Bernard painting. A photograph of Bernard's original would not match this physical object. The investigated visitor photograph identified the correct watercolour, but its oblique gallery framing and visible label made it unsuitable for attachment.

GAM inventory GRASSI 051 contains an unresolved conflict within its source metadata. It gives a date around 1870 and describes a young man with a beard and moustache, while an alternative title identifies Joaquín Sorolla y Bastida. The Museo Sorolla documents his birth in 1863. The resulting age conflict is an inference from primary sources, not a corrected sitter identification. Both supplied titles, the artist and the year remain unchanged. [Exact catalogue evidence and review](editorial-identity-followup/identity-review.json).

## Where the next useful effort lies

The largest remaining image gap is **drawings**. The Castello graphic collections account for 1,093 drawing gaps and the Academy of Brera for 572. Across Italian holdings, the largest named-creator groups are Appiani (403), Bison (399), Hayez (310), Mariani (219), Quarenghi (141) and Boccioni (61). These counts describe existing catalogue records; they are not a recommendation to download entire collections.

The Castello drawings department describes a written-request and approval process for supplied reproductions, with different conditions for research and commercial use. Eight existing records were retained as concrete examples for a small future review, with exact source IDs. The review records the failed direct policy capture and the blocked policy PDF; no image permission is inferred from those failures, and no museum was contacted. [Department information](https://www.milanocastello.it/it/archivi-e-biblioteche/gabinetto-dei-disegni/orari-e-contatti), [drawing review packet](drawing-gap-policy-review/review.json).

The next image workflow should retain exact sheet inventories, distinguish recto from verso and keep preliminary studies separate from their finished paintings. Establish suitable photographic rights and any required cultural-property commercial permission before selecting image bytes. An independent photographer's licence alone does not settle a public collection's commercial concession requirements.

## Verification and recovery

Every retained JPEG is at most 100,000 bytes, uses proportional full-frame compression and carries saved original-source and licence evidence. The final checks cover every retained image, rather than a sample: local bytes and dimensions, uploaded object checksums, both database media/rights links, original artwork and creator preimages, served image bytes and exact authenticated preview title, image URL, licence, attribution and status. Preview access does not publish an artwork.

The historical [source validation replay](source-proof-final-replay.json) checked all 59 source packages present at four-hour completion; it does not clear the subsequently held images for commercial use. The historical [archive verification](archives-recheck-20260917T0037.json) verified those 59 original downloaded files, the local database backup checksum and the successful production backup. Rejected local derivatives were moved into the dedicated private Artline backup directory after confirming they had no database media record or cloud storage copy. Their review evidence remains in this research folder.

The in-app browser connection was unavailable; no browser verification is claimed. No new artworks were imported, no commits or deployments were made, and review records were not published. [Current delivery and preservation checks](commercial-use-review-20260917/verification.json), [backup receipts](backups.json).
