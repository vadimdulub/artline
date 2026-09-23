# Russian icon image research — 21 September 2026

**217 images are now in both local and production catalogues:** 100 from the State
Russian Museum, 77 from the Andrei Rublev Museum, and 40 from the Icon Museum and
Study Center. All 217 local and production artwork detail responses and image
files passed verification. The initial local delivery attached images to existing
records; the subsequent owner-authorized [production upload](production/README.md)
imported those 217 records and their evidence. No creator changes, publication or
application deployment.

The read-only baseline found **1,550 icon records, 67 illustrated and 1,483
without images** across all traditions. After this delivery, **284 are illustrated
and 1,266 remain without images**. These are catalogue-wide icon counts, not
Russian nationality counts.

## Research and selection

The largest gaps came from the two metadata-first Byzantine/Russian expansions
on 20 September. Most objects have anonymous or object-level creator labels, so
an artist-only image search misses them. Research reused their checksum-verified
museum captures and exact accessions, then checked current museum pages and
selected image resources. All research evidence is retained.

Across four source groups, the inventory records 1,244 existing image gaps:
**988 records with exact primary museum image candidates** and 256 held for
further review. The 988 are catalogue-record matches, not a claim of 988 distinct
physical objects or 988 downloaded images. Two duplicate-object record pairs were
subsequently identified during visual review.

| Source | Exact, dated image candidates | Attached |
| --- | ---: | ---: |
| [State Russian Museum](https://rusmuseumvrm.ru/collections/iconography/index.php) | 540 | 100 |
| [Andrei Rublev Museum](https://www.rublev-museum.ru/collection/icons/) | 325 | 77 |
| [Icon Museum and Study Center](https://www.iconmuseum.org/country/russia/) | 123 | 40 |
| **Total** | **988** | **217** |

The bounded selection took the earliest securely dated objects with exact image
matches: at most 100 Russian Museum, 80 Rublev Museum and 40 Icon Museum records.
All were created by 1955 and have documented museum connections. This is an
editorial/owner selection, not a newly asserted museum masterpiece designation.
No exhaustive museum image download was performed.

Examples include the Russian Museum's [Angel with Golden Hair, ДРЖ-2115](https://rusmuseumvrm.ru/data/collections/ikonopis/drzh_2115/)
and [Belozersk Mother of God, ДРЖ-2116](https://rusmuseumvrm.ru/data/collections/ikonopis/drzh_2116/).
Related Byzantine material remains distinguishable: ДРЖ-2110 is explicitly
catalogued as Constantinople, 1387–1395. Its Russian museum custody does not
establish Russian origin, and no nationality was assigned.

## Identity and visual decisions

All 219 successfully prepared images were inspected on 11 contact sheets.
The complete supplied frames, source watermarks, oklads, historic damage and
separately catalogued iconostasis components were preserved.

- **КП 994 / КП-994:** two Rublev catalogue records depict the same Apostle Paul
  icon. The fuller selected image was attached to one existing record; attachment
  to the other remains held. Both artwork records and their differing source
  date descriptions remain for metadata reconciliation.
- **КП 679 / КП-679:** the same Saint Matthew icon appears in two source cards.
  One image association was selected; the duplicate record was retained.
- **КП-549:** the museum explicitly identifies a double-sided icon. Its Saint
  Nicholas face is attached with an explicit view label. The combined artwork
  title and single physical-object record remain; the image is not represented
  as showing both faces.
- **КП-1958:** the supplied image failed the minimum-dimension check and remains
  unattached. Its source original and research evidence were preserved.

The database verification confirms that the only artwork changes are the 217
primary-image associations and their revision/audit fields. Creator links,
unknown creator labels, dates, titles, identifiers, holdings, owner collection
membership, review status and publication state are unchanged. One image-identity
citation and a full media-rights evidence record were added per attachment.

## Rights and files

The user explicitly answered **“Apply the same policy”** to extending the
Cyprus/Greek workflow to this Russian museum selection: works created by 1955,
source links and actual rights labels retained. See
[the collection policy](../../ARTLINE_IMAGE_USE.md#explicit-russian-museum-extension--21-september-2026).

All 217 museum reproductions remain **`restricted`** with the actual museum
copyright labels, source credits and links. `verified_at` and `verified_by` remain
null. This records the owner's collection instruction, not permission from a
copyright holder. In particular, the [Russian Museum's terms](https://rusmuseumvrm.ru/terms/index.php?lang=en)
require a request for images and publication rights; those terms are retained in
the source evidence. No museum outreach was performed.

Derivatives total **17,359,564 bytes**; the largest is **99,998 bytes**. Each
preserves the supplied frame and was proportionally resized and JPEG-compressed.
Original reproductions are archived outside Documents.

## Remaining work

**771 of the 988 matched records remain unattached**, including the two duplicate
record holds and the undersized-image hold. The others were outside the bounded
220-record download selection. Their exact source/image links are retained in
[the remaining-match index](remaining-source-matches.md).

The separate discovery holds are:

| Reason | Records |
| --- | ---: |
| Unknown/unresolved date or outside the established image cutoff | 145 |
| Missing or multiple primary images requiring component/view review | 84 |
| V&A origin and image-rights review outstanding | 25 |
| Explicit double-sided/reverse-specific titles needing view matching | 2 |

The older six Kremlin image gaps also remain unresolved. Exact-identifier web
searches did not supply usable matches in this pass. Prior source access holds
were respected; private museum API routes were not accessed. Commons accession
API research was stopped at its robots exclusion; no alternate host or route was
used to bypass it. A public Commons search independently located the Angel with
Golden Hair category, but no additional Commons file was downloaded or attached.

This delivery improves the collection; it does not claim complete Russian
icon image coverage.

## Local/production boundary and verification

A read-only production lookup checked all 1,550 local icon slugs in bounded
100-slug batches. It found 51 counterparts overall and **none of the 988 museum
candidate records**. The initial delivery therefore remained local-only. The user
then explicitly requested “ok, upload them to production.” The subsequent
[production delivery](production/README.md) uploaded the 217 approved derivatives,
imported the corresponding review artwork records, and added two missing review
museum entries and six provenance sources. The remaining unselected records
were not imported. Existing production dependencies and all local data were
preserved; no artwork was published.

The active local app at `http://localhost:3000` successfully served all 217 image
files and artwork detail responses with the expected checksums, rights labels,
source links and review state. The separate older production-mode preview on
port 3100 still has its startup public-file inventory; it was not interrupted.
Use the current local app on port 3000 to review this delivery.

- [Delivered image/source index](image-index.md)
- [Database and file verification](verification.json)
- [Local application HTTP verification](http-verification.json)
- [Unselected-record preservation check](scope-verification.json)
- [Visual review and duplicate decisions](visual-review.json)
- [Source candidate inventory](museum-image-candidates.json)
- [Current source-rights captures](museum-rights-research.json)
- [Production comparison](cloud-baseline.json)

Recovery preimages: `/Users/vadimdulub/Library/Application Support/Artline/backups/russian-icon-images-20260921/`.
Source originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/russian-icon-images-20260921/originals/`.
Application images: `apps/web/public/assets/artworks/imported/russian-icon-images-20260921/`.
The two visually held duplicate derivatives remain unassociated research files;
no old assets were removed. This campaign used no test database or fixtures.
