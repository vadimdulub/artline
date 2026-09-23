# New museum artworks — 19 September 2026

**10 new Cleveland artworks with verified CC0 images added to local and production catalogues, across 7 existing painters.** This batch contains 7 paintings, 2 drawings and 1 print. Together with the preceding two image passes, 22 images have been delivered.

| Painter | Artwork / official museum record |
| --- | --- |
| Ikkyū Sōjun | [Listening to the Wind in the Pines](https://www.clevelandart.org/art/1985.89) |
| Ikkyū Sōjun | [Reflections of Priest Foyen](https://www.clevelandart.org/art/2015.511) |
| Ikkyū Sōjun | [Calligraphy with Willow and Swallows](https://www.clevelandart.org/art/2015.463) |
| Iwasa Matabē | [Coastal Landscape](https://www.clevelandart.org/art/2015.507) |
| Kaigetsudō Ando | [Sanjo Kantaro II in the Role of Urashima Taro](https://www.clevelandart.org/art/1961.41) |
| Miyagawa Chōshun | [Entertainment Scene](https://www.clevelandart.org/art/1985.17) |
| Miyagawa Chōshun | [Spring Dancers (Manzai)](https://www.clevelandart.org/art/1985.252) |
| Cornelis Saftleven | [Horse Standing on a Mound](https://www.clevelandart.org/art/2019.12) |
| Ishikawa Toyonobu | [Courtesan Reading a Poem Slip Tied to Flowers in a Vase](https://www.clevelandart.org/art/1985.358) |
| Lucas Velázquez | [Figures](https://www.clevelandart.org/art/1952.12) |

## Checks and safeguards

- Refreshed all 10 exact museum objects before selection; verified object-level CC0, image identity, accessioned ownership, creator identity and source creation intervals ending before 1971.
- Duplicate and existing-painter authority checks passed against both catalogues before import. No existing artwork was replaced and no painter profile changed.
- All new records retain `status=review`, `research_candidate=true` and a null publication timestamp. Museum date wording, broad ranges and classifications are preserved, not converted to invented exact dates.
- Added source-supported collection holdings only; no current-on-view claims.
- Visually inspected every derivative. All are full-frame JPEGs below 100 KB: 811,124 bytes total, maximum 98,752 bytes. Only these selected reproductions were downloaded.
- Verified local files, storage checksums, rights evidence and attachments in both databases. All 10 public image responses matched their saved hashes; all 10 artwork API responses matched the expected title, image, source, licence and review status. Both verification reports have zero errors.
- Eighteen offline image-clearance tests passed. No test databases or catalogue fixtures, publication-status changes, deployment or commits.

Evidence: [pinned selection](cleveland/plan.json), [checksum-pinned visual review](cleveland/reviewed-images.json), [image/storage/rights verification](cleveland/delivery-verification.json), and [catalogue/public delivery verification](cleveland/catalogue-public-verification.json).

Recovery preimages are stored under `/Users/vadimdulub/Library/Application Support/Artline/backups/open-access-new-artworks-20260919/cleveland/`; selection checksums are recorded in [backups.json](cleveland/backups.json). Fresh API captures and receipts remain in `cleveland/fresh-api/`.

This is a completed bounded batch, not an exhaustive import of the three museums. Earlier Met access errors and unresolved creator matches remain held; no copyrighted Pollock images were added. Earlier results: [initial image pass](../open-access-image-gaps-20260919/README.md) and [three-image follow-up](../open-access-followup-20260919/README.md).
