# Library pictures — 10 October 2026

The user requested a picture for every book and event, preferred usable covers or recognisable related images, and authorised continued research rounds without approval prompts.

**Work in progress.** This directory retains discovery, source evidence, rights decisions, visual reviews and local delivery. A candidate is not an accepted image. Existing selections are preserved. Database access remains read-only; new pictures are attached through Artline’s existing versioned image manifests.

| Catalogue | Existing pictures | New local pictures | Other records |
|---|---:|---:|---:|
| Books | 837 | 4,774 | 4,525 |
| Events | 16 | 3,206 | 6,804 |

Updated: 2026-10-10T14:49:31.322148+00:00

- `picture-coverage-index.json.gz`: one record for each of the 20,162 active books and events, including selected picture, source link, preparation state and unresolved evidence.
- `coverage-summary.json`: current counts. `selected-local.json.gz`: exact new manifest entries and visual-review receipts.
- `delivery/`: immutable drafts, prepared-file hashes, contact-sheet review decisions and per-file errors. Author images are reused only for the same verified creator and identical reviewed image bytes; captions identify them as author images.
- `standard-ebooks/`: exact edition identity, CC0 cover-design statement, underlying artwork/source evidence and separate territorial/artist-term checks.
- `captures/`: retained source responses with retrieval receipts and SHA-256 hashes. Search results and imported Wikidata claims remain discovery evidence until reviewed.
- `next-article-*` and `search-*`: additional source rounds for unresolved records. A search hit never establishes identity by itself.

Images preserve the full supplied frame and are proportionally resized/JPEG-compressed to at most 100,000 bytes. Source originals and backups live under `~/Library/Application Support/Artline/`, outside Documents. Original catalogue dates, statuses, creator links and existing images are not rewritten.

New local selections need the normal web/API release before they appear on production. No commit or deployment has been performed by this campaign.
