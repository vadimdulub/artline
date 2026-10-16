# Artworks attached to the local exhibition collection — 12 October 2026

The subsequent [local image delivery](../exhibition-images-local-20261012/README.md)
illustrates every selected artwork, puts galleries first and removes external
navigation links. Its image counts supersede the eight-image starting state
recorded below.

The user asked to add the artworks that were exhibited to each exhibition. This
continues the selected **700-exhibition local review**. Every entry in that
selection now opens an artwork page with object details, artist connections,
participation evidence and links back to its documented exhibitions. These are
source-backed local research records, not new production/main-catalogue imports.
No production or real local database writes, migrations or deployment occurred.

Open http://127.0.0.1:3107/exhibitions.

## Delivered

| Measure | Result |
| --- | ---: |
| Exhibitions with local artwork records | 700 |
| Distinct provider object identities with local pages | 9,936 |
| Artwork-to-exhibition connections | 10,506 |
| Objects appearing in more than one selected exhibition | 508 |
| Maximum connections for one object | 4 |
| Objects with source/canonical artist links | 9,935 |
| Existing main-catalogue artwork links preserved | 16 |
| Newly supported object-history participation connections | 250 across 26 exhibitions |
| Existing museum participation connections rechecked against object histories | 33 |
| Total connections labelled “Recorded as exhibited” | 283 |
| Connections labelled “Listed in exhibition” | 10,223 |

The previous 10,506 exhibition entries were mostly external source links. They
now resolve to shared local object records: repeated appearances reuse the same
provider object identity. Counts of new local artwork pages must not be reported
as newly discovered exhibition entries or new main-catalogue artworks.

The public Artsy object API returned all 9,903 requested selected object IDs in
199 bounded batches. Of these objects, 976 include an exhibition-history field.
The 33 selected Cleveland objects were also fetched by their native museum IDs.
The source schema is documented in Artsy's
[artwork fields](https://github.com/artsy/metaphysics/blob/main/src/schema/v2/artwork/index.ts)
and [bounded artwork query](https://github.com/artsy/metaphysics/blob/main/src/schema/v2/artworks.ts).
This is a resumable, one-off research collector, not a runtime browser dependency.

## What the evidence establishes

An Artsy exhibition list already identifies a work by its exact native object
ID. Additional participation evidence requires the same object's exhibition
history to name the selected exhibition title, venue and event year together in
one line/semicolon-separated entry. Matching is restricted to held physical
events. Online, proposed, cancelled, withdrawn and explicitly not-exhibited
references do not qualify. The 26 groups of matching histories were inspected;
the matched source lines and capture receipts are retained in the evidence file.

This supports a **source-reported exhibition history**, not independent
installation or loan-return verification. A complete online list still does not
prove a complete final physical checklist. The remaining 10,223 listing
connections are retained with their weaker evidence label, not promoted merely
because the object has an unrelated exhibition history.

Cleveland object records explicitly link all 33 selected works to native
exhibition `317581`, *Picasso and Paper*. The API's `exhibitions.current` array is
a data field, not proof of present display: this is a historical 2024–2025 record.
Touring venues retain their own dates. Object participation in the exhibition
does not establish participation at every stop, and the artwork page says so.

Source date differences are preserved in the receipts rather than silently
rewriting event dates. Examples include the opening dates in the Alex Katz and
Stephen Antonakos: Pillows histories, and the closing date in the Sam Francis
history. These remain event-date review work. No current-display or ownership
claim is inferred from participation.

Examples in the preview:

- [Stephen Antonakos: Project Drawings, 1967–73](http://127.0.0.1:3107/exhibitions/71ff8e00-4566-5c73-834b-eeb9f8cc5033?participation=exhibited#artworks): all 47 listed objects have matching source exhibition histories; this is not certification of the final physical checklist.
- [Matisse, Le Lagon (Lagoon)](http://127.0.0.1:3107/exhibitions/artworks/26d15c6c-431c-5aa7-b234-7b60b85516ea): one exact source object with four exhibition-list connections.
- [Picasso and Paper](http://127.0.0.1:3107/exhibitions/cf8a5362-6ba5-5d02-9337-ee235a700cd2): 33 museum object histories, including eight existing illustrated objects.

## Identities, metadata and scope

Local artwork IDs are stable UUIDs derived from provider plus native object ID.
Different source IDs, editions, impressions, copies and studies are not merged
using artist/title alone. Existing canonical artwork links, dates, titles and
approved images are preserved. Object dimensions and source classifications are
added, and missing Cleveland date/medium/creator fields use its exact native
object record. Full original captions remain available.

Artist links use exact source identities or established catalogue identities.
Native Cleveland creator IDs extend verified Picasso/Gilot links to other works
by the same source creator. Dora Maar's native creator `11223` was reconciled
with the one existing catalogue candidate using her exact name and matching
1907–1997 life dates; the read-only query result is saved as evidence. Her two
works and exhibition participation now link to that artist. Nancy Baker's
*Hello Titty* retains its supplied creator label: the source returned no creator
ID, so an artist identity has not been invented.

Post-1970 and undated works remain documentary exhibition objects. Main-catalogue
date, museum-connection and review requirements are unchanged. The eight existing
approved artwork images are reused; this pass does not download new images or
assign licences to Artsy reproductions. The 108,969-record archive remains
accessible, but the new local artwork-page coverage applies to these 700 events.
Coverage of every exhibition in that larger archive remains unfinished.

## Interface and architecture

- Every selected exhibition entry links to a local artwork page. The original
  provider record stays available, and securely linked works can open in the
  ordinary Artline artwork catalogue too.
- Artwork pages show dates, media, dimensions, object classifications, creators,
  existing images/credits, and a bidirectional exhibition history with evidence.
- An exhibition's artwork list can be filtered to “Recorded as exhibited”. Counts
  and pagination reflect that filter; an empty evidence view retains access to
  the complete public list.
- Artwork/artist pages remain public. Museum destinations retain the member
  prompt. Exhibitions remains in the account menu.
- The separate loopback Go service owns ID validation, counts, filtering and
  pagination. Artwork detail excludes the appearance array; a separate endpoint
  returns at most 100 appearances (40 normally). Source records remain outside
  the browser bundle and databases. Startup validates cross-record references.
- The normal production API remains unchanged. This bounded local corpus is not
  evidence of ten-million-record performance or a replacement for production
  relational ingestion and indexed reverse lookups.

The existing local launcher still works:

```sh
/tmp/artline-cesi-venv/bin/python ops/exhibitions_local_preview.py
```

It refuses occupied ports; the current preview already uses `3107`, `8098` and
`8099`. Its read-only catalogue fallback and ephemeral local-debug membership
remain intact. The earlier `exhibitions_deep_build.py` now reapplies exact-object
enrichment when this research exists, so rebuilding cannot silently erase it.

## Evidence and reproduction

```text
~/Library/Application Support/Artline/source-metadata/exhibition-artworks-local-20261012/
  baseline.json.gz
  artsy-batches/0000.json.gz … 0198.json.gz
  cleveland/<native-object-id>.json.gz
  museum-creator-crosswalk-evidence.json
  participation-evidence.json
  review-corpus.json
  report.json
  api-verification.json
```

Raw captures retain URL, retrieval time and SHA-256 receipts in the existing
exhibition capture store. The updated corpus is also written to the previous
`exhibitions-deep-local-20261011/review-corpus.json` path used by the launcher.

```sh
/tmp/artline-cesi-venv/bin/python ops/exhibition_artworks_local.py collect
/tmp/artline-cesi-venv/bin/python ops/exhibition_artworks_local.py collect-museum
/tmp/artline-cesi-venv/bin/python ops/exhibition_artworks_local.py build
/tmp/artline-cesi-venv/bin/python ops/test_exhibition_artwork_evidence.py
/tmp/artline-cesi-venv/bin/python ops/exhibition_artworks_verify.py
```

The build fails if the selected Artsy object set has not been fully researched or
a museum object's exact exhibition-history ID is absent. Rebuilding requires
restarting the owned loopback research process to load the new immutable snapshot.

## Verification

- All 700 exhibition entry lists, all 9,936 artwork detail responses and all
  10,506 reverse appearances checked against the actual source-backed corpus.
- Evidence filters checked for all 700 events. Appearance pagination exercised
  with two-item pages, including 56 additional pages; no duplicate/lost entries.
- Original populated titles/dates/images/canonical artwork links preserved.
- Seven invalid artwork/filter requests rejected; POST rejected. The complete
  108,969-event archive remains reachable. No database fixtures were created.
- Four evidence-matching tests cover explicit matches, wrong dates/venues,
  unrelated adjacent histories, title boundaries, withdrawn/planned/online cases.
- Go command builds; TypeScript and targeted ESLint pass.
- Six Chrome/Playwright scenarios pass, including public artwork access, local
  object navigation, reverse exhibition links, four appearances of the same work,
  retained museum images and museum-login behavior. Updated artwork scenarios
  were rerun after preserving separate touring-venue dates in the history view.
- Desktop/phone axe checks pass. Layout checked at 1440, 768, 390 and 320px for
  the new artwork page; screenshots visually inspected. The in-app browser's
  previously reported bootstrap error required the project's Playwright fallback.

Final artwork browser artifacts are under
`/tmp/artline-exhibition-artworks-browser-final/`; the full six-scenario run is
under `/tmp/artline-exhibition-artworks-browser/`.
