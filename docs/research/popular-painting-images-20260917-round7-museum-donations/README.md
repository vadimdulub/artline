# Museum-donated photographs — round 7, 17 September 2026

Added **19 verified images to both local and production**, including **3 paintings by popular painters**. Google Storage contains the same 19 checked JPEGs. No artworks or artists were created, no catalogue facts were changed, and all 19 artwork records remain in review.

The productive route was the museum's own Wikimedia donation account. Reims [explicitly links its institutional uploads](https://musees-reims.fr/fr/musee-numerique/article/culture-libre-le-projet-wikipedia). Its older donated photographs have exact-file **[CC BY-SA 2.0 France](https://creativecommons.org/licenses/by-sa/2.0/fr/)** releases. Current museum photographs may be by a different photographer. Credits and licences from those newer images were not transferred to the donated files.

The Commons API's aggregate public-domain label describes a different rights layer. This batch preserves the explicit photograph licence, French jurisdiction, version, photographer, source page, modification notice and ShareAlike condition. The underlying paintings also have separate public-domain evidence. Full-frame resizing and JPEG compression were the only output transformations.

| Painter | Added images |
|---|---:|
| Stanislas Lépine | 3 |
| Antoine-Louis Barye | 1 |
| Henri Fantin-Latour | 2 |
| Eugène Boudin | 7 |
| Alexandre-Gabriel Decamps | 1 |
| Ary Scheffer | 2 |
| Gustave Courbet | 2 |
| Pierre-Auguste Renoir | 1 |

The three popular-painter additions are Courbet's **Le sculpteur Marcello (Duchesse de Castiglione-Colonna)** and **Rochers, sapins, ruisseau**, and Renoir's **Marine ; Marine normande**. These resolve the three photo-variant holds from round 6. The remaining popular Reims gap is Courbet's **Sous-bois**; its earlier permission draft is still a possible route. No outreach was sent.

| Popular paintings, both databases | Before | After |
|---|---:|---:|
| All popular-painter paintings | 5,266 | 5,266 |
| With a usable image | 2,318 | 2,321 |
| Missing an image | 2,948 | 2,945 |
| Eligible, supported paintings missing an image | 1,964 | 1,961 |

The catalogue had grown by five popular paintings since round 6's snapshot. Compare this batch's own before/after reports when measuring progress. Local now has 80,111 usable images overall; production has 80,109. The pre-existing two-record/two-image difference was preserved. The remaining 984 popular-painting gaps outside the eligible supported subset need separate date or selection/holding review.

Research examined metadata from the museum's 558 donated files and matched it to 52 existing eligible missing-image painting records. Only 28 exact-inventory candidate file records were examined in detail; only 19 selected, cleared photographs were downloaded and attached. Eight candidate records were held for title/creator/source or underlying-artwork rights checks, and one historical museum object URL returned 404. Index metadata includes other object types; those were not downloaded. Several current museum dates are more precise than the database's existing ranges; they were required to fall wholly within those ranges, and the database values were preserved.

Validation: **140 synthetic unit tests passed**; all eight round-6 direct-source receipts still validate. Both databases passed all 19 source, scope, licence and image checks. All 19 storage objects passed checksum, byte-size and provenance checks. All **57 anonymous live-site requests** passed (image, museum artwork detail and artist artwork detail for each image), including the displayed licence and attribution. Preimage comparisons found no creator, identifier, title, date, holding or publication-state changes, and no same-byte image attached to another artwork.

Evidence and outputs:

- `approved-image-manifest.jsonl`: independent source URLs, exact image licences and delivered file checksums.
- `reims/candidates.json`, `reims/pages/`, `reims/rendered-selected/`, `museum-donation-source.json`: selected identities and primary-source evidence.
- `reims/visual-review-completed.json` and `reviewed-images.json`: source and final image checksums reviewed before attachment.
- `local-final-audit.json`, `production-final-audit.json`, `public-all-images-final.json`, `final-preimage-and-duplicate-audit.json`: delivery and preservation checks.
- `coverage-both-before.json`, `coverage-both-final.json`, `final-aggregate-report.json`: measured results.
- `backups.json`: integrity references to preimages in the designated Artline backup directory, outside the repository.
- `selection-report.json`: retained holds; `initial-selection/` and `selection-before-*/` preserve earlier read-only selections, not additional imports.

Implementation reuses the existing media, rights-evidence and artwork-association schema. `ops/popular-reims-donations.py` adds an institution-specific verifier; `ops/popular-reims-images.py` shares strict object-identity checks and independently scoped museum facts. The established local writer, production uploader and read-only auditor register this verifier. No schema migration or deployment was required.

The approved receipts can be resumed through `ops/apply-night-prepared-local.py` with `--reviewed-images`, followed by `ops/upload-overnight-prepared-images.py`, using this directory as `--run` and a current future Unix `--deadline`. Existing completion receipts prevent duplicate attachments. Audit again with `ops/audit-overnight-local-images.py --target local` and `--target cloud --verify-gcs`.
