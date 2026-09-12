# European museum data — applied and verified

Completed 9 September 2026 against local PostgreSQL database `artline`.

The researched batch contains 59 object records from 26 European institutions in
12 countries. **58 artworks and 25 institutions were added**, alongside **87 new
citations**. The existing Prado *Garden of Earthly Delights* record was matched and
given additional source evidence, not duplicated or overwritten.

| Painter | New works | Total now in Artline | Qualified attributions in total |
| --- | ---: | ---: | ---: |
| Hieronymus Bosch | 14 | 15 | 1 disputed |
| El Greco | 11 | 14 | 2 possible/attributed |
| Claude Monet | 22 | 30 | 0 |
| Camille Pissarro | 11 | 12 | 0 |

Whole catalogue: **445 artworks, 36 institutions, 211 existing media assets**.
Active painter count remains 1,001; no painters were created by this import.
These are Artline coverage counts, not counts of everything owned by each museum.

All 58 new artworks, 25 new institutions and new venues remain in **review**.
Nothing was published, committed, pushed, deployed or applied through Terraform.
No images were downloaded; no current-display assertions or new masterpiece /
must-see designations were made. Existing 374 selection items remain unchanged.

## Evidence decisions

- Pissarro already had associated Impressionism and Neo-Impressionism links but no
  primary movement. Promoted the unreviewed Impressionism link to primary, kept
  Neo-Impressionism associated, and added France as a place of **activity**, not
  nationality or birthplace. The [National Gallery biography](https://www.nationalgallery.org.uk/artists/camille-pissarro)
  supports the classification and Paris-area activity. Later editorial decisions,
  including deliberately clearing a classification, survive replay.
- [MSK's Christ Carrying the Cross](https://www.mskgent.be/en/collection/1902-h)
  remains `attributed_to` with an explicit disputed-authorship note.
- [Saint Jerome as Cardinal](https://www.nationalgallery.org.uk/paintings/possibly-by-el-greco-saint-jerome-as-cardinal)
  and the [Modena triptych](https://catalogo.beniculturali.it/detail/HistoricOrArtisticProperty/0800675920)
  retain possible/attributed authorship. The latter's RCGE 8095 inventory was found
  in the focused follow-up; national catalogue ID 0800675920 is stored separately.
- [Nationalmuseum's View over the Sea](https://collection.nationalmuseum.se/en/collection/item/19182/)
  lists a signed date. The literal “Signed 1882” is retained, but numerical creation
  dates remain null. It stays in the chronology's undated/review group, not
  automatically classified as eligible under the 1970 creation cutoff.
- Other source dates retain their exact/circa/range/decade/century precision. “Late”
  century/decade wording is preserved; full century/decade bounds are conservative
  indexing envelopes, not newly asserted exact dates. The other 58 batch records
  satisfy the known-date cutoff; one of these was already in the database.
- Owner, loan and collection-credit distinctions are retained in sourced notes.
  The two new Boijmans long-term loans have structured `loan` holding context.
  Existing Prado fields/assertions are preserved; the additional Garden citation
  records Patrimonio Nacional ownership and Prado custody. No legal title is
  independently adjudicated by this research.
- Orsay's Pissarro title aliases identify one work; the French/English display
  disagreement is recorded as a separate citation, not resolved by guessing.
  Orangerie's three-panel *Les Nuages* is one composition. Thyssen's two
  *Annunciations* remain distinct accession-linked objects.
- Institution image-policy notes and original source payloads are retained. A
  public collection webpage or high-resolution viewer is not image clearance.
  Indexed-only sources retain that access qualification. Unknown source update
  dates are not replaced with retrieval dates.

## Verification

- All Go packages pass `go test ./...` with isolated database-backed tests enabled.
- Four functional European importer tests pass, covering the entire 59-record source
  snapshot, date/attribution validation, rollback, stable-ID matching, ambiguity
  rejection, missing authority rejection, edit preservation and replay.
- A fifth, opt-in query-plan test adds 100,000 unrelated artworks, 100,000 identifiers
  and 100,000 citations in a disposable schema. Exact matching uses all three new
  identity indexes with **no sequential scan**. This is not a 10-million-row load
  benchmark; production-scale import throughput and operational index rollout
  still require dedicated testing.
- The final dry-run planned 58 new works / 25 new museums and rolled back. Live
  table counts were unchanged by the dry-run.
- Apply succeeded in one serializable transaction. The import job is
  `needs_review`: 86 accepted ingestion records (59 objects + 26 institutions +
  1 artist classification), zero rejected. Ingestion acceptance is not publication.
- An applied replay reused all 59 works / 26 institutions, added zero citations,
  changed zero classifications, and left checked data/audit counts unchanged.
- `go vet ./...` also passes.
- Live API checks returned HTTP 200 for all four painter chronologies, showing
  15 / 14 / 30 / 12 works respectively. Monet has one undated record; Bosch has
  one qualified attribution and El Greco two.
- London's National Gallery API returns eight researched works, zero imported
  on-view claims and zero new highlights. The combined Monet/Pissarro + France/UK
  museum filter returns eight institutions. Stockholm's unknown-date filter
  returns the signed-date Monet record.
- Public museum results remain empty for the unpublished catalogue; anonymous
  `preview=1` requests return HTTP 401. No frontend visibility bypass was added.

## Receipts and recovery

- [Applied receipt and exact artwork IDs](../output/european-import-applied.json)
- [Replay receipt](../output/european-import-replay.json)
- [Final dry-run receipt](../output/european-import-final-dry-run.json)
- [Source inventory](research/european-paintings/inventory.json)

Source snapshot SHA-256:
`4b2997fdc8403a9a65ad80e3fb77b14aea607d5dbe53f732fe8d70f5cc88da69`

Job ID: `70f1691c-fb7c-49b6-88be-49b32bd6f12d`.

Pre-import, pre-migration custom-format PostgreSQL backup:
`/Users/vadimdulub/Documents/artline-backup-20260909.Ln5ZKd/before-european-import.dump`

Backup SHA-256:
`a725bb9a6ac630a35ff77618a9432d68c72b3445742808bea5a23ff94528ad76`

The backup lives outside the repository in a private directory. Its archive table
of contents was checked and contains the public catalogue, not disposable test
schemas. A full restore rehearsal was not performed. Do not restore over later
editorial changes; use a separate database for comparison/recovery if needed.

## Backend implementation

`cmd/ingest-european` is local-only and offline, pinned to this reviewed source
snapshot. It is not a generic museum crawler. By default the complete transaction
is rolled back; `-apply` is required to persist. New receipt paths use exclusive
creation, so prior receipts cannot be silently overwritten.

Migration `0010_research_identity_indexes.sql` adds exact canonical-URL, citation-URL
and institution/accession indexes. It was applied locally only. Before applying
this index migration to a future large production database, plan an appropriate
maintenance or concurrent-index deployment; the small local migration is not
evidence of a nonblocking production rollout.

Image licensing/downloading, publication review, subject-genre taxonomy, and wider
European discovery are separate follow-ups; this bounded batch does not claim
exhaustive collection coverage.
