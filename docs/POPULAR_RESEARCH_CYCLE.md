# Popular-painter research cycle

The backend command processes **every painter currently selected as popular**, including painters with no works. It produces individual Markdown checklists and machine-readable per-artwork assessments. It does not set editorial review-complete flags, import unreviewed objects, or download images automatically.

[First executed cycle: all 100 painters](research/popular-cycle-20260911/PAINTERS.md)

## Run and resume

From `apps/server`:

```sh
DATABASE_URL='postgres://localhost/artline?sslmode=disable' go run ./cmd/review-painters \
  -mode cycle-popular -root ../.. -out ../../docs/research/popular-cycle-YYYYMMDD
```

Use the same output directory to resume an unchanged database cohort. The manifest pins the popular cohort, aliases, database metadata/associations/media/citations fingerprint, and inventory SHA-256. Checkpoints are matched against the frozen inventory and captured raw source facts. Successful captures are reused without another network request. Derived assessments and Markdown are regenerated; original execution checkpoints remain unchanged.

Changes to fingerprinted database facts require a **new cycle directory**. Old reports remain dated evidence, not current truth. Source/institution configuration changes are not comprehensively fingerprinted: use a new directory after such changes as well. A crashed process may leave `run.lock`; first confirm no runner remains before manually removing that exact lock. An interrupted initial export without a manifest should be retained for diagnosis and restarted in a fresh directory.

## What one automated pass means

1. Snapshot every linked artwork: identity, creation date, holding evidence, exact source links, image path/size/rights checks.
2. Check existing NGA objects against the pinned published-image metadata feed. Cached leads still require fresh permission/identity checks.
3. Run one official Cleveland painting query per popular painter: exact display-name search, at most 20 results, no automatic pagination.
4. Compare returned creators against explicit local names/aliases; reject workshop/qualified or multiple creators. Match existing records only by exact source identity, then check accession/title/eligible dating.
5. Save candidate additions, image leads and unresolved museum/source/date gaps separately. Never interpret zero search results as an empty oeuvre.
6. Continue source-specific object review and small image batches separately. A full review is still pending until each required decision has evidence.

Cleveland is the currently implemented **live discovery adapter**, not a claim to have searched every European museum. Existing European museum object links form each painter's follow-up queue. Queries can miss alternate names and exclude works catalogued outside “Painting.” More results, attribution conflicts, uncertain dates and image permission gaps remain open.

The [official Cleveland API](https://openaccess-api.clevelandart.org/) supplies object metadata and per-image licensing. Its general open-data status is not permission for every image. The [NGA open-data repository](https://github.com/NationalGalleryOfArt/opendata) supplies the additional cached image leads.

## Safety and operating limits

This is an offline Go research tool, not a public request handler. Current guards are 200 popular artists, 50,000 attribution links, 128 MB inventory and 4 MB per catalogue response; requests are spaced at least 1.5 seconds apart with a 25-second timeout. HTTP 401/403/429 pauses the source; three consecutive failures also pause it. Redirects are not followed. Existing Chicago/Nationalmuseum image blocks, Orsay access restrictions and unresolved Marmottan permissions remain explicit; do not route around them.

The runner deliberately retains a bounded cohort in memory. It is **not a ten-million-artwork ingestion engine**. Larger research jobs require database-backed work queues, keyset batches and persisted per-source scheduling; do not raise these guards and assume production scalability.

Summary artwork totals count painter-artwork links (shared attributions may appear under more than one painter); the frozen inventory contains distinct artwork IDs. Legacy summary decision keys can combine work-level and discovery-level date gaps; inspect individual assessments for the affected records.

## Reviewed image batch

`review-masterpieces -mode stage-popular-cycle` selects an explicit, reviewed subset, rechecks exact official object metadata and CC0 image evidence, and defers local/source date conflicts. Stage/preview do not download images. Apply requires the SHA-256-pinned selection and rechecks database fingerprints. Existing media, metadata, holdings and masterpiece selections are preserved.

Use a database backup and the before/after verification scripts for each apply. Newly selected authentic reproductions are stored on local disk at no more than **100,000 bytes**, without cropping. Image availability does not imply masterpiece status or current display. New artwork candidates require a separate reviewed import; this cycle does not publish anything.

