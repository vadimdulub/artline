# Local exhibition review — 11 October 2026

The [12 October artwork continuation](../exhibition-artworks-local-20261012/README.md)
adds local pages for all 9,936 source objects, bidirectional exhibition histories,
and stronger participation evidence. The figures below describe the original
11 October delivery; consult that continuation for the updated evidence counts.

The user requested Exhibitions in the account menu, a UI/UX rework, and fuller
coverage of 500–1,000 exhibitions to inspect locally. This continuation is local
only. No production deployment, production database writes, real local catalogue
writes, migrations, test databases or database fixtures were made.

Open **http://127.0.0.1:3107/exhibitions**. Membership uses the existing loopback
local-debug implementation; accounts, sessions, bookmarks and studies remain
ephemeral. The catalogue fallback connection forces PostgreSQL read-only mode.

## Delivered research

| Measure | Verified result |
| --- | ---: |
| Distinct local exhibition records | 700 |
| Exhibitions with complete available public online lists | 699 |
| Source online lists behind those 699 events | 700 |
| Documented artwork participation entries | 10,506 |
| Distinct provider artwork identities / already matched catalogue works | 9,936 |
| Artist participation connections | 6,427 |
| Other participant connections | 1 organizer |
| Artist connections to existing Artline identities | 2,397 |
| Distinct existing Artline artists linked | 1,021 |
| Records with a source description or source-backed editorial overview | 700 |
| Records with indexed reading topics | 557 |
| Certified complete physical exhibition checklists | 0 |

The selection contains 699 Artsy exhibition histories featuring at least one
already matched artist born by 1930, plus the illustrated museum study
**Picasso and Paper**. Exhibition dates span 2020–2025. This first selection is
not representative coverage of every period, institution, country or tradition.
The full 108,969-record active archive remains accessible through “Entire archive”.

Source selection examined 1,015 candidates and retained 700 qualifying source
listings. Each retained listing has at least three artworks, an available source
text, artists, explicit historical dates, a closed event state, no GraphQL field
errors, no duplicate artwork IDs, and returned artwork count equal to the provider
total with `hasNextPage=false`. Two “SUMMER '22” source listings were already
reconciled to one catalogue exhibition. Their artwork and participant unions are
preserved locally, with both source identities, and count as one exhibition.

**Completeness has a specific scope.** All available public online entries have
been collected for those 699 events. Artsy listing completeness does not establish
a final physical installation checklist. The museum study contains all 33
associated Cleveland entries available in the collected dataset, including eight
existing illustrated records, and remains explicitly partial relative to the
whole exhibition. No certified-complete-checklist claim is made. Work loans,
physical installation, ownership and current display remain separate facts.

The [Cleveland museum description](https://www.clevelandart.org/exhibitions/picasso-and-paper)
supports the original editorial overview of paper, collage, studies and
construction. Missing creator/date/medium captions for securely linked museum
objects use their existing catalogue metadata, with original source captions and
local field evidence retained. This also connects Pablo Picasso and Françoise
Gilot through exactly matched documented works; artist names are not inferred
from the exhibition title.

For Artsy, the collector follows the source's
[public show schema](https://github.com/artsy/metaphysics/blob/main/src/schema/v2/show.ts).
Full captured descriptions/press releases remain in local source evidence. The UI
shows short attributed excerpts, a factual artwork/media overview, and links to
the full source. Reading topics are explicitly identified as text indexes rather
than curator-assigned categories or independently authored critical essays.
143 records have source text but no matched topic in the current vocabulary;
missing concepts are not invented. Artist biographies and exact source identities
remain separate from curatorial interpretation.

Post-1970 works are documentary exhibition entries only: no new main-catalogue
artworks were created. No source artwork was attached to an existing Artline work
through title-only matching. Existing exact museum-object links and approved
images are reused. Artsy image URLs and actual rights fields remain in source
evidence; unresolved images are not silently given licences or displayed as
approved catalogue reproductions. The new records have no exhaustive image batch.

## Interface

- Exhibitions is removed from the primary header. It remains in the desktop
  account sidebar and appears in the phone menu's Your account group.
- The opening museum study uses actual documented works with uncropped images,
  captions, credit disclosures and links to the exact entry anchors.
- The directory uses legible exhibition years, titles, venues, artwork counts and
  reading topics. Source/date/format/state filters and pagination retain URL state.
- Detail pages have Overview, Artworks, Artists & people, and Sources anchors;
  an explicit coverage panel; artwork checklists or illustrated grids; public
  artist links; related exhibitions based on exact artist identity; and sources.
- Museum destinations retain the member prompt and return destination. Artist
  and exhibition pages remain public. Local debug requires no Google sign-in.
- Source excerpts, unknown fields, qualified creators and incomplete checklists
  remain visible. Empty-image cases use readable checklists, not placeholders.

Artline's existing paper/ink/stone/rust palette and Georgia/Avenir typography are
retained. The illustrated museum opening is the visual focus; reading and
navigation use restrained rules and existing shared controls. No new fonts,
icon library, generated artworks or animated decoration were added.

## Local architecture and evidence

The source-backed corpus lives at:

```text
~/Library/Application Support/Artline/source-metadata/exhibitions-deep-local-20261011/
  candidates.json
  shows/<native-source-id>.json
  accepted.json
  review-corpus.json
  report.json
  audit-issues.json
  api-verification.json
```

Raw source captures and checksums reuse the exhibition campaign evidence store
under `exhibitions-100k-20261011/captures/`; each new show record contains its
exact receipt and retrieval time. Research is retained outside the real local
catalogue. No raw research corpus is bundled into the browser or committed as
application seed data.

The separate Go `cmd/exhibition-preview` service loads this bounded corpus, owns
validation/filtering/counts/sorting/pagination, and serves at most 100 records or
entries per request (40/50 in normal browsing). It binds only to loopback, accepts
GET only, and proxies unmatched exhibition reads to the read-only catalogue API.
It reconciles by canonical exhibition ID; archive records are never hidden by a
publication status. This is an explicitly selected local collection, not a
publication/research visibility distinction.

Next.js reads the service only when both development mode and an explicit
loopback `EXHIBITIONS_REVIEW_API_URL` are present. The ordinary production data
path is unchanged. Enrichment is not persisted to production by the preview.

Current running preview: web `3107`, research API `8098`, ephemeral-member
read-only catalogue API `8099`; the older read-only archive API on `8097` supplies
fallback exhibition reads for this running instance.

## Repeatable local launch

With the existing Cloud SQL loopback proxy on `55519`, gcloud read access, web
node_modules, Go and the research Python environment available:

```sh
/tmp/artline-cesi-venv/bin/python ops/exhibitions_local_preview.py
```

The launcher refuses occupied ports. To keep the current preview while starting
another one, specify three unused ports:

```sh
/tmp/artline-cesi-venv/bin/python ops/exhibitions_local_preview.py \
  --web-port 3127 --api-port 8199 --review-port 8198
```

It builds the API commands, creates an isolated web copy under `/tmp`, forces
read-only database transactions, skips migrations, enables the guarded ephemeral
local-debug member implementation, and starts the local review service. Ctrl-C
stops only its own processes. Source files remain in Application Support.

The launcher was exercised on the alternate ports above, including page loading
and the real ephemeral member session, then stopped. The main `3107` preview
remains running.

Research scripts:

- `ops/exhibitions_deep_local.py`: bounded, resumable source detail retrieval.
- `ops/exhibitions_deep_build.py`: canonical reconciliation, creator crosswalks,
  short excerpts, topic indexes and local corpus assembly; DB reads only.
- `ops/exhibitions_deep_verify.py`: complete real-corpus API pagination audit.
- `ops/exhibitions_local_preview.py`: repeatable isolated preview launch.

## Validation

- All 700 unique exhibition IDs and all 10,506 entry IDs traversed through bounded
  keyset pages; no duplicate or overlapping IDs within exhibition lists.
- Source counts and returned artwork IDs checked; no source/canonical exhibition
  date changes or artist-birth-after-exhibition conflicts in the selected records.
- Seven invalid query cases rejected; write requests rejected; only exhibition
  API paths exposed. Five topic/filter combinations verified, including source
  and archive combinations; topic filters cannot silently fall through upstream.
- Related records verified against shared canonical artist identities. All
  108,969 active archive records remain discoverable through the fallback.
- TypeScript and targeted ESLint pass. Exhibition validation and local-debug Go
  tests pass; the local command and ordinary API compile.
- Three real browser scenarios pass: account navigation and archive switching;
  source text/artwork/artist/topic browsing; and public museum-study browsing with
  preserved museum sign-in/focus return.
- Layouts checked at 1440, 1024, 768, 390 and 320px, including the signed-in sidebar.
  Desktop and phone WCAG A/AA axe checks pass. Long source titles wrap correctly.
- Source-driven API verification is at `api-verification.json`; browser screenshots
  and traces are under `/tmp/artline-exhibitions-deep-browser-final/`.

The in-app browser tool failed during bootstrap with a sandbox metadata error;
the established Chrome/Playwright project tests provided browser verification.
No ten-million-record performance claim is made for this bounded local corpus.
