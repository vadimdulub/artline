# Wikimedia catalogue scan — 13 September 2026

Completed selected additions in **both local and production**. All records remain in review and are accessible through the public read-only research preview. No records were published, removed or automatically merged. No deployment or Terraform change was needed.

| Result | Local | Production |
| --- | ---: | ---: |
| New artworks | 864 | 864 |
| Existing artworks enriched | 90 | 90 |
| New painters, each with artworks | 270 | 270 |
| Images attached | 566 | 566 |
| New works with unknown dates retained in review | 165 | 165 |
| New works with unresolved/object-level creator labels | 77 | 77 |

Added four museum catalogue identities: Ashmolean Museum, Benaki Museum, Hermitage Museum and Tretyakov Gallery. Greek, Russian, Byzantine and post-Byzantine collections are represented; anonymous priority objects retain an object-level creator label rather than a fabricated painter.

## Coverage and bounds

- Audited all **342 existing institution entries**, all **403 source registrations**, artwork/image counts and the painter authority inventory (4,776 linked Wikidata identities at baseline).
- Matched **296 existing institution entries** through official website evidence or unambiguous Muséofile IDs. These collapse to **294 collection groups**. **46 institution identities remain unresolved**; their rows and reasons are preserved in `collection-coverage.json`.
- Queried those 294 groups plus the four additional collections: **8,661 unique discovery candidates**, **3,822 metadata entities fetched**, **967 selected collection entries / 961 unique artworks**.
- This was a catalogue-wide **bounded pass**, not an exhaustive harvest of every museum or artist. Main collections: inspect a maximum of 500 illustrated objects, filter for painting subclasses, retain up to 150 candidates, fetch up to 50 metadata records and select up to 12. Muséofile continuation: up to 20 directly classified painting candidates, fetch up to 10, select up to 2. The raw queries and per-collection counts are retained. A zero-result bounded sample (including the Met probe) is not proof that a collection has no Wikidata paintings.
- Only selected image files were downloaded. All attached images have explicit per-file Commons rights and credits, independent artwork-identity checks, saved source receipts and checksums. Prepared but deferred assets are not counted as attached images.

## Preserved uncertainty

- Unknown creation dates remain unknown, with research-candidate status. Unsupported date qualifiers, ambiguous ranges and incomplete attributions were not converted into invented facts. Known out-of-scope dates were excluded. Images were attached only for eligible dates.
- `77` new works retain object-level creator labels where a safe painter identity/timeline was unavailable. Missing details did not prevent an actual review record.
- `5` application candidates were deferred after accession/identity checks; see `summary.json` and the immutable batch plans. In particular, Q112754490 (Tribute to the Eucharist) conflicts with the older Hospitality of Abraham record at accession BXM01544; the existing record was preserved.
- Multiple-collection discoveries were resolved through an established existing catalogue connection where available. Unresolved collection conflicts were held for review. Previously prepared Tate discoveries preserve their captured museum connection. A P195 collection statement is not a fresh on-view, ownership or visitor-access claim.
- `30` possible matches to older unlinked CSV entries remain ambiguous because titles and painter names alone do not establish exact object identity. See `preexisting-unlinked-duplicate-leads.json`; no automatic merge or deletion occurred.
- Ten titles missing from the initial language selection were recovered from Portuguese, Norwegian or multilingual labels, with source receipts and narrowly scoped correction preimages. Original-language titles were preserved without inventing translations.

## Verification

`verification.json` confirms every committed batch record in both databases, review status, creator links/labels, date semantics, source citations, image rights and checksums, and unchanged existing catalogue content outside the intended image attachment fields. All new painters have artworks. The local and production additions match even though their pre-existing totals differ.

Every attached image (**566**) was decoded locally and fetched anonymously from the deployed web service; bytes and SHA-256 matched. Each JPEG is at most 100 KB. Public museum artwork details and painter lists were checked, including unknown-date records and new museums; the editor coverage endpoint still returns 401 without credentials. Visual QA is sampled: an initial 37-image review including all 12 selected Byzantine images, plus 12 images from the four new museums (`visual-review/`). One available historical reproduction, Zorah Standing, is monochrome. Browser integration was unavailable at bootstrap (`sandboxPolicy` missing), so no browser interaction test is claimed.

Seven pure safety tests cover date ambiguity/cutoff handling and conflicting accession identities. Real catalogue access for auditing/verification was read-only, without test databases or fixtures. Batch planning uses scoped institution/title/accession candidates and materialized returned-ID joins. Production I/O contention required per-collection caching; this pass is not a 10-million-row load benchmark, which remains outstanding.

## Evidence and recovery

- Local full backup: `/Users/vadimdulub/Library/Application Support/Artline/backups/wikimedia-catalogue-scan-20260913/local-before.dump`.
- Successful managed Cloud SQL backup: **1789312082635** (`production-managed-backup.json`).
- Existing-record and title-correction preimages are under the same backup directory.
- `captures/`, `entities/`, `selected/`, `ready/`, `batches/`, `applied/` and `batch-results/` preserve query receipts, reviewed inputs, SHA-pinned plans and committed outcomes. `global-unlinked-duplicate-leads.json` is the raw post-import lead scan; use the filtered `preexisting-unlinked-duplicate-leads.json` to exclude this pass's own records.
- Image originals/source thumbnails are under `/Users/vadimdulub/Library/Application Support/Artline/backups/wikimedia-catalogue-scan-20260913/selected-originals`; published-size files live in the local web assets and the private `artline-508319-images` bucket, delivered through the existing web proxy. The final archive receipt records a separate private evidence backup.

Sources: [Wikidata data access and CC0](https://www.wikidata.org/wiki/Wikidata:Data_access), [Sum of All Paintings](https://www.wikidata.org/wiki/Wikidata:WikiProject_sum_of_all_paintings), [Commons reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia). Individual artwork, Wikipedia and Commons URLs are in the stored citations and per-record evidence. Wikipedia prose was not copied.
