# Reviewed selections

`prado-highlights.json` is a bounded crosswalk of twelve original paintings, not
a scraper or a complete catalogue. Names, dates, media and accession identities
were checked against the linked official Prado records and public indexed
versions on 8 September 2026. Direct Prado HTML requests returned HTTP 403; no
image-bank assets were downloaded or restrictions bypassed. No museum prose is
copied. Object identity is independently checked against Wikidata P170/P195/P217
on each run; source date discrepancies are noted, not silently merged.

Designations come from two explicit Prado selections:

- [Fourteen masterpieces for Google Earth / the one-hour route (2009)](https://www.museodelprado.es/en/whats-on/new/14-masterpieces-from-the-museo-del-prado-in/220f2fe9-beec-44a2-afdb-8c67ff37256c).
- [Educational masterpiece reproductions (2018)](https://www.museodelprado.es/en/whats-on/exhibition/didactic-exhibition-the-prado-in-albuquerque/494d6f01-d05a-4263-86c5-ee6441dd05f7).

The 2018 event exhibited reproductions, not the originals. These are historical
selection claims, never on-view assertions. Museum holdings include permanent
loans; the application does not infer ownership from them.

Only the artwork's Wikidata-linked Commons image is considered, using the
Commons API's current file-specific public-domain status, no restrictions, and
PD-Art/PD-old evidence. Image permissions belong to that Commons file, not to all
Prado photography. Raw evidence, source links, dimensions and checksums are
retained. Only a web-sized thumbnail is downloaded. Review status is preserved.

Run from `apps/server`:

```sh
go run ./cmd/ingest-curated -source prado -run prado-highlights-2026-09-08
go run ./cmd/ingest-curated -source prado -run prado-highlights-2026-09-08 -apply -images
```

Use a new run name for source refreshes. Reusing a run replays cached evidence;
new image downloads fail closed when rights evidence is older than 24 hours.

## Uffizi and Mexico coverage follow-up

`uffizi-selection.json` contains nine works across eight previously empty popular
painter profiles. The official Uffizi object pages were reviewed and fetched on
8 September 2026. Before any writes, the adapter checks factual markers in cached
HTML, an exact single unqualified Wikidata creator, its collection identity and
the separately recorded authority inventories. Official dates take precedence;
approximate dates and ranges are preserved. Italian catalogue identifiers in
Wikidata are not silently substituted for the museum's 1890 inventories.

Four Uffizi works have specific museum masterpiece/icon evidence in their object
commentary or linked educational announcement: Cimabue, Piero della Francesca,
Fra Angelico and Bronzino. The other five are **personal research selections** of
documented holdings, stored in the owner's must-see collection, not relabelled
as institution-designated highlights. Their reasons and source URLs are in the
manifest. No location on a webpage is turned into an on-view assertion.

`mam-highlights.json` contains Frida Kahlo's *The Two Fridas* (1939), from the
[Museo de Arte Moderno's official highlighted works](https://mam.inba.gob.mx/destacadas.html).
The indexed official record was reviewed on 8 September 2026; direct HTML returns
403 and is not bypassed. The API cross-check verifies the painter and holding
collection; no missing accession number or dimensions are invented. The shared
highlights-page URL is evidence, never a unique artwork identity.

Both adapters are **metadata-only** for now, even with `-images`. The
[Uffizi publication policy](https://www.uffizi.it/en/professional-services/publications)
describes an image-use authorization process, including for applicants already
holding images. A Commons copyright label alone is not treated as clearing that
separate requirement. No explicit reusable-image permission was verified for
*The Two Fridas*. No permission requests have been sent and no image assets from
either source downloaded. Image-permission notes are stored as artwork citations,
visible in the app's source sections, not as invented media licences.

```sh
go run ./cmd/ingest-curated -source uffizi -run uffizi-coverage-2026-09-08
go run ./cmd/ingest-curated -source uffizi -run uffizi-coverage-2026-09-08 -apply
go run ./cmd/ingest-curated -source mam -run mam-coverage-2026-09-08
go run ./cmd/ingest-curated -source mam -run mam-coverage-2026-09-08 -apply
```

Each fixed manifest is capped at 25 objects, independent of `-painters` and
`-max-works`, and runs only when explicitly selected, not via `-source all`.
Replay preserves catalogue edits and does not reinstate an owner's removed pick.
Collection changes use row locks and revisions and remain in review.
