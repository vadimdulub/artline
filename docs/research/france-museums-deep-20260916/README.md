# Deep France museum and artwork research

16 September 2026. National source census, read-only local catalogue audit, focused museum/object research and image-reuse leads.

## Main result

The French gap is substantial and has both metadata and image causes. The local audit found **10,444 French-linked paintings with stored creation-end dates through 1970; only 670 have primary images attached (6.42%)**. These figures include review records and are not production-visible counts.

| Research output | Scope |
|---|---:|
| Official Muséofile directory records mapped | 1,216 |
| Art-interest museum entries in regional tables | 733 |
| Existing Joconde metadata rows scanned | 1,046,260 |
| Painting-domain source notices, all dates | 92,518 |
| Native/national/regional catalogue links indexed | 177 |
| Bounded artwork research candidates | 1,328 across 342 source museum codes |
| Selected object-level case studies | 28 |
| Painting records with explicit Paris Musées CC0 image labels | 8 |

This is national breadth plus selected deep dives, **not a claim to have individually verified every artwork in every French museum**. Exact-reference absence is not proof of a missing artwork: candidate checks already found 35 accession leads and 58 same-title leads against local museum-scoped records.

## Read the findings

- [Museum dossiers](museum-dossiers.md): Louvre, Pompidou, Paris municipal museums, Dieppe, MuMa, Nice, coastal neighbours, all-region priorities, image terms and open issues.
- [Measured catalogue coverage](coverage.md): local/source comparison for 24 priority museums, denominators, source receipts and identity caveats.
- [France region by region](regional-inventory.md): all 733 art-interest registry entries, source painting/image counts, local coverage and institutional links.
- [Catalogue routes](catalogue-routes.md): 177 official-directory links, including native collection systems that Joconde does not replace.
- [Object and image review](object-review.md): source-linked facts, inventories, dates, image labels, local duplicate leads and specific provenance traps.
- [Proposed follow-up batches](next-batches.md): bounded research/import-preparation sequence with unresolved access and rights requirements.

## Reusable evidence

`national-museum-inventory.json` retains the complete official directory, topics, named artists and source/local counts. `museum-review-queue.json` provides compact institution-level coverage with alias-unioned artwork counts. `bounded-candidates-with-local-leads.json` preserves 1,328 source candidates, supplied creator labels, dates, techniques, inventories, legal/deposit information and duplicate leads. `primary-objects-with-local-leads.json` contains the 28 selected cases. `audit-summary.json` and `validation.json` record reproducible counts and checks.

The local inventory files are **derived read-only research evidence, not a database backup**. Existing official exports were streamed in place and verified against pinned SHA256 receipts; they were not downloaded again. Research evidence stays in this directory. No unrelated research or product changes were touched.

## Method and reproduction

With the existing environment containing `psycopg`, `requests` and `beautifulsoup4`:

```sh
/tmp/artline-images-venv/bin/python docs/research/france-museums-deep-20260916/research.py --stage audit
/tmp/artline-images-venv/bin/python docs/research/france-museums-deep-20260916/research.py --stage routes
/tmp/artline-images-venv/bin/python docs/research/france-museums-deep-20260916/build_report.py
```

The audit opens `postgresql://localhost/artline` with `default_transaction_read_only=on`, uses a repeatable-read read-only transaction, resolves French museum identities, and scopes artworks by those institution IDs before collecting details. Source candidates are capped at 12 per priority-city museum and 4 elsewhere, with creator-diversity limits; these are review examples, not an exhaustive import manifest. Alphanumeric Joconde identifiers are retained. Approximate/ambiguous dates and attributions still require editorial review.

The catalogue-route stage checks robots policy and reads one Ministry directory page. Its 177 extracted links include supplementary resources and do not equal 177 museums or individually verified APIs. Individual web research distinguishes direct catalogue pages, indexed primary-page evidence, blocked PDF inspection and unvisited catalogue routes.

CSV analysis preserved source values and provenance; the spreadsheet skill informed that handling, while the large dataset was streamed to JSON/Markdown rather than loaded into a workbook. The PDF skill prompted direct caption/image inspection attempts for Nice; access was blocked, so those records remain explicitly marked as indexed evidence, not visually verified PDFs.

**Database writes: 0. Artwork image downloads: 0. Imports/publication/deployments/commits: none for this research.**
