# Book cover research — 17 September 2026

The requested UI keeps covers only in the book details drawer. The title index
and timeline do not request any reproduction images. Every book retains an
original Artline text-cover fallback, explicitly labelled as a new design rather
than an edition cover. A historical edition image cannot be promised for every
work, particularly recent books with copyrighted covers.

Final selection: **801** source-declared public-domain covers/title pages,
including **30 of the Top 100**. **9,199** works use original Artline typography.
All **4,498** unique candidate file records were fetched; no fetch failures remain.
This is not complete historical-edition cover coverage for all 10,000 books.

## Scope and source evidence

The audit checks the retained records of all 10,000 catalogue works, including
their non-deprecated Wikidata P18 image claims. It checks each unique linked
Commons file for identity, image type, rights metadata, credit, source URL and
warnings. Additional edition candidates have explicit work/edition evidence in
`additional-candidates.json`. This is a complete audit of the retained direct
image claims, **not** an exhaustive search of every possible edition.

`book-audit.json` records a result for every work. `candidates.json` retains the
work-to-image identity and source-response checksum. Compressed Commons API
responses under `sources/` retain the per-file permission/credit metadata;
`commons-index.json` is a derived lookup. `cover-decisions.json` records both
selections and held alternatives. `selection-summary.json` has the final counts.
Missing or insufficient evidence stays explicit; no work dates or creator
lifespans are invented to justify an image.

## Reuse checks

- The image must be identified as a cover or title page, not just an illustration,
  author portrait, manuscript fragment or image of a book adaptation.
- The underlying design needs an explicit public-domain basis: an ineligible
  text/simple design, or an old-work declaration supported by pre-1931 publication
  or an expired-US declaration. The photo's PD-self/CC license alone is insufficient.
- The reproduction must have an explicit public-domain, CC0, CC BY or CC BY-SA
  declaration. License restrictions, disputes and deletion warnings are held.
- The reproduction's origin must be recorded. The existing
  [commercial image-use policy](../../ARTLINE_IMAGE_USE.md) applies. BnF/Gallica
  scans and identifiable Italian public-custodian sources remain held for
  separate commercial-use permission review; a Commons PD declaration does not
  resolve those additional conditions. Other explicit noncommercial/study-only
  source conditions are also held. These are source-specific checks, not an
  exclusion of French or Italian books.
- Attribution and source/license links are carried into the drawer as text.
  An unidentified creator is preserved as unknown only when the source explicitly
  declares public domain without required attribution. No source HTML is executed.
- Source edition dates remain separate from the work's composition/publication
  interval. A title page is labelled as a title page, not a first edition unless
  that additional claim is independently supported.

These checks follow [Commons' book-cover guidance](https://commons.wikimedia.org/wiki/Commons:Copyright_rules_by_subject_matter#Book_covers)
and [reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia).
Availability through Open Library, Wikipedia or a cover API is not treated as
permission. The file's source declaration is the recorded evidence; there is
no blanket claim that every edition or every jurisdiction permits reuse.
The source-specific holds are supported by [BnF's commercial-reuse terms](https://www.bnf.fr/fr/faire-une-utilisation-commerciale-dune-reproduction)
and [Italy's cultural-property reproduction guidance](https://docs.italia.it/italia/icdp/icdp-pnd-circolazione-riuso-docs/it/v1.0-giugno-2022/acquisizione-circolazione-e-riuso-delle-riproduzioni-dei-beni-culturali-in-ambiente-digitale/tipologie-duso-delle-riproduzioni-di-beni-culturali.html).

## Application and update behavior

`ops/research-book-covers.py` fetches only metadata, in URL-length-bounded batches,
with caching, rate-limit backoff and retained error records. It can resume after
an interrupted fetch. `ops/select-book-covers.py` applies the checks and produces
`apps/server/internal/books/cover-selection.json`. No database records, migration
state or publication status are changed by these operations.

Go validates and loads the immutable manifest once. It attaches a cover only to
an already-visible, bounded book response with matching book ID and Wikidata work
ID. It ignores raw/unreviewed imported cover fields. The complete manifest is
never sent to the browser; images load only when a user opens the drawer.

This local preview remains subject to the existing review/publication policy.
Source declarations can be corrected or withdrawn: refreshing source metadata,
reviewing changed decisions, regenerating the manifest and rebuilding the API
are explicit operations. No permanent freshness guarantee or automatic publication
is implied. Production-scale refresh/invalidation and editorial cover changes
would require maintained backend projections; this versioned static selection
does not establish that future infrastructure.

Only selected images are requested on demand. No bulk book-image download is
performed. Local browser screenshots/tests are kept under `/tmp`, while source
research evidence stays here. Real catalogue checks use read-only connections.
