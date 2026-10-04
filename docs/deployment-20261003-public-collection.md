# Reviewed public collection — 3 October 2026

The user approved preparing ten artist profiles and launching their reviewed collection. New guides and outreach were deferred. This release publishes existing records only: ten artists, five representative works per artist, and ten sourced influence claims. No artwork or media records were imported, no images were replaced, and the local catalogue was audited read-only.

## Published selection

Giotto; Leonardo da Vinci; Sandro Botticelli; El Greco; Artemisia Gentileschi; Rembrandt; Johannes Vermeer; Katsushika Hokusai; Claude Monet; Vincent van Gogh.

Each profile has an original 80–300-word biography, reviewed geography and primary movement, primary-source citations, and five dated works with existing verified image rights. The exact IDs, changes and sources are in `research/public-launch-20261003/publication-plan.json`. Museum API rechecks, before-images and publication gate reports are preserved alongside it. All ten profiles passed the existing Go publication gate with no issues before their publication through the editor API.

Artemisia's exact death year remains unknown: the National Gallery documents her alive in August 1654. Her numeric death year is cleared, the displayed endpoint says “1654 or later”, and the timeline uses a labelled estimate without inventing an active year. Her Allegory of Painting is identified with Royal Collection RCIN 405551, with the museum's approximate date and medium. Previous attribution notes and citations remain available. Giotto's chapel dates refer to the institution's 1303–1305 cycle date, not an invented exact date for each scene. Two Botticelli date labels follow the current Art Institute ranges.

Rublev and Theophanes remain in review pending stronger object-level evidence; their records were not deleted or filtered out of the research catalogue. Greek and Byzantine connections are represented through El Greco. Museum holdings are distinguished from current display; this release makes no new on-view assertions.

## Public browsing and search discovery

`/artists` links the published collection with a bounded server-rendered directory. Published artist pages render their full biography, influences and selected works immediately. Each selected artwork has a canonical page with artwork/image structured data. Published pages carry `index, follow`, and the root sitemap exposes artist and artwork shards during research preview.

Explicit API reads with `preview=0` enforce published visibility even when public research preview is enabled. Published profiles use that scope, including artwork detail reads. A review artwork under a published artist returns 404 instead of falling back to research visibility. Unpublished artist previews remain available with `noindex`. The interactive research homepage and museum previews remain `noindex` and excluded from their respective public sitemap entries. The work-account Google verification token is preserved.

## Validation and release isolation

- Seventeen focused web tests passed, covering metadata, sitemap routing, public/review visibility and failure handling. ESLint and TypeScript passed.
- Go HTTP tests passed for preview visibility, editor access and request validation.
- Production API checks returned exactly ten published profiles and fifty selected works. Explicit public requests for a review artist and review work returned 404; research access remained available.
- Read-only `EXPLAIN (ANALYZE, BUFFERS)` for each selected artist used the scoped representative query; observed execution was 0.16–0.39 ms against the existing catalogue. These checks do not establish performance at ten million artworks; representative large-scale load testing remains outstanding.
- Cloud SQL backup `1791015323248` completed successfully before writes. Scoped database preimages, Cloud Run runtime preimages, source archives and release operations are stored under `/Users/vadimdulub/Library/Application Support/Artline/backups/public-launch-20261003/`.
- Release sources were reconstructed from the exact live API and web archives, then patched narrowly. Unrelated workspace changes were excluded. No commits or Terraform apply were performed.

## Live result

Both Cloud Run services are ready and serving 100% of production traffic:

- API: `artline-api-public-1003`, image `sha256:81739a460431985d9b62b9666947d43c0d06e10ff908009ee6f01bd46ce1407d`; build `f1271f1a-bafa-4936-8e8b-0badc40c3317`.
- Web: `artline-web-public-1003`, image `sha256:dd04f495f8d66e528e56c7efdd8f34b217402e72762a338a4f5e2f3c2721f96c`; build `815e1087-40f2-4bd8-8f2e-4a96d3a84eeb`.

The release candidate passed browser checks for all ten artist pages, fifty artwork pages and fifty existing images with JavaScript disabled. Canonicals, robots directives, profile/artwork structured data, crawlable links, review exclusions and all 63 sitemap URLs passed. Interactive artwork selection and biography controls passed. Desktop and mobile screenshots were inspected; the directory and profile fit the 390-pixel mobile viewport.

After promotion, the canonical domain passed directory, representative artist/artwork, review exclusion and all-sitemap checks. The live HTML retains the work account's Google verification value. Cloud Run checks confirm that runtime configuration other than the image/revision was preserved. The ignored Terraform image references were synchronized without running Terraform.

Automated browser reports, query plans and screenshots are in the private backup's `verification/` directory, outside Documents. Primary editorial sources and publication receipts remain in the repository research directory. Google indexing of the new pages is not yet confirmed; the existing Search Console sitemap subscription can discover the updated root sitemap. No new indexing request, guide or outreach was performed during this release.
