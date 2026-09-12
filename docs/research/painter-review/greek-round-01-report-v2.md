# Round 1 — second Greek cohort, 11 September 2026

Added **four painters and eight artworks** to local PostgreSQL, all in review.
The catalogue now contains **5,328 painters, 105,961 artworks and 403 pictures**.
No photographs were added in this cohort. Nothing was published or committed.

## Painter-by-painter results

| Painter | Current database works reviewed | Round-1 painter decision |
|---|---:|---|
| [Sofia Laskaridou](https://www.nationalgallery.gr/en/artist/laskaridou-sofia/) | 2 | Blocked: birth-date conflict |
| [Thaleia Flora-Karavia](https://www.nationalgallery.gr/en/artist/flora-karavia-thaleia/) | 2 | Done for this bounded first-pass scope |
| [Spyros Papaloukas](https://www.nationalgallery.gr/en/artist/papaloukas-spyros/) | 2 | Done for this bounded first-pass scope |
| [Theophilos (Chatzimichael)](https://www.nationalgallery.gr/en/artist/theophilos-chatzimichael/) | 2 | Done for this bounded first-pass scope; approximate birth retained |

Each author page was inspected for additional catalogue entries, then the eight
selected object pages were checked individually. The four author pages list
9, 13, 10 and 6 works respectively; those lists were not exhaustively imported or
individually researched. New biographies are short paraphrases of the museum's
account, not copied essays. Country links mean Greek cultural affiliation, not
inferred birthplace or citizenship. Papaloukas's engagement with Byzantine art
does not turn these twentieth-century paintings into ancient Byzantine icons.

## Exact object selection

| Painter | Work / official record | Literal date | Accession |
|---|---|---|---|
| Laskaridou | [La Belle Epoque](https://www.nationalgallery.gr/en/artwork/la-belle-epoque/) | 1910 - 1915 | Π.10508 |
| Laskaridou | [Boats on the Lido Canal](https://www.nationalgallery.gr/en/artwork/boats-on-the-lido-canal/) | 1908 - 1912 | Π.3510 |
| Flora-Karavia | [Water-Carriers on the Nile](https://www.nationalgallery.gr/en/artwork/water-carriers-on-the-nile/) | c. 1909 | Π.2110 |
| Flora-Karavia | [Boy Reading](https://www.nationalgallery.gr/en/artwork/boy-reading/) | ca 1906 | Π.4166 |
| Papaloukas | [Guest Quarters at Lavra Monastery on Mt. Athos](https://www.nationalgallery.gr/en/artwork/guest-quarters-at-lavra-monastery-on-mt-athos/) | 1924 | Π.3941 |
| Papaloukas | [Boy with Suspenders](https://www.nationalgallery.gr/en/artwork/boy-with-suspenders/) | 1925 | Π.3300 |
| Theophilos | [The Beautiful Adriana of Athens](https://www.nationalgallery.gr/en/artwork/the-beautiful-adriana-of-athens/) | 1930 | Π.6829 |
| Theophilos | [Adam and Eve](https://www.nationalgallery.gr/en/artwork/adam-and-eve-2/) | 1932 | Π.10169 |

All dates end before 1971. Ranges retain separate start/end years. Materials,
dimensions, accession numbers and named creator links were checked against the
captured object pages. Adriana's uncertain medium retains the source question
mark. The Laskaridou and Benakis bequest credits remain distinct from ownership
and current display. Museum highlight and owner masterpiece selections were
not inferred or changed.

## Conflicts and deferred records

- Laskaridou: the [online museum biography](https://www.nationalgallery.gr/en/artist/laskaridou-sofia/)
  gives 1876; [SearchCulture's authority record](https://www.searchculture.gr/aggregator/persons/-1625244741?language=en)
  and the museum's [From the Hidden Collections catalogue](https://www.nationalgallery.gr/wp-content/uploads/2021/10/adyta_gr.pdf)
  give 1882. The database keeps an estimated timeline, explicit conflicting
  display text and a NULL numeric birth year; the painter checkbox stays open.
- [Messolonghi Lagoon](https://www.nationalgallery.gr/en/artwork/messolonghi-lagoon-7672/),
  Π.3943, was captured but **not imported**. The object page gives 1905 and oil on
  cardboard; the same-accession printed catalogue entry gives 1906 and oil on
  canvas mounted on pasteboard. Resolve the catalogue/version discrepancy first.
- Theophilos: the online artist page states 1873; the museum's
  [Four Centuries catalogue](https://www.nationalgallery.gr/wp-content/uploads/2021/10/4centuries_en.pdf)
  qualifies it with a question mark. Display is approximate and numeric birth
  remains NULL. No unrelated Theophilos/Theophanes creator was merged.

## Image research — open, not downloaded

All eight museum object pages contain reproductions. Their presence is not a
reuse grant. The [museum's terms](https://www.nationalgallery.gr/oroi-chrisis/)
were checked again on 11 September: selected private research capture is distinct
from publishing the photographs, and third-party rights remain relevant.
Raw HTML evidence is outside public assets; no original museum photographs were
downloaded, generated, cropped or substituted.

Bounded exact-title/artist searches for all eight works did not establish a
sufficiently verified unrestricted exact-object image for this app's ingestion
workflow. Specific follow-ups:

- SearchCulture lists Laskaridou's selected works with a **CC BY-NC-ND** label.
  This is a restricted-licence lead, not a claim that no permission exists. Verify
  the item-level file/licensor and decide whether the app can meet noncommercial
  and no-derivatives conditions before acquisition. Do not relabel it CC0.
- [WikiArt's Boy Reading page](https://www.wikiart.org/en/thalia-flora-karavia/boy-reading-1906)
  labels the image public domain in the US; that alone does not establish the
  required source-file permission and geographic scope for this app.
- [WikiArt's Papaloukas portrait](https://www.wikiart.org/en/spyros-papaloukas/boy-wearing-suspenders-1925)
  is labelled fair use; it was not treated as an open licence.
- The museum's [Google Arts & Culture record for Adam and Eve](https://artsandculture.google.com/asset/adam-and-eve-theophilos-chatzimichael/uQG8xUsKAKrsOA?hl=en)
  corroborates the museum/object connection, not a licence to download its image.
  Search results for Adriana also included commercial reproductions; these were
  not used as authentic object photographs.

Each artwork now has an explicit completed factual/image-availability research
decision, but its **image-file checkbox remains unchecked**. Image permission and
acquisition stay as follow-ups, not silently completed downloads.

## Local implementation and verification

- Go importer accepts only the checksum-pinned second selection in addition to
  the original pin. New dated captures and receipts never overwrite old evidence.
- Fixed the artist-death cutoff error: 1970 applies to creation dates. Added
  strict literal-date/range validation and range-preserving insertion. Tests
  cover post-1970 artist deaths, eligible ranges, mismatched dates, reversed and
  cutoff-crossing ranges, tampered manifests and stale evidence.
- Rollback preview succeeded and left zero cohort artist rows. Local apply
  created 12 records; replay preserved all 12 IDs and created no duplicates.
- A new full Markdown snapshot includes all **5,328 painter pages**, every one
  of **105,961 distinct artworks**, and the **21 unlinked/anonymous records**.
  All prior **5,324 painter fingerprints and 105,953 artwork fingerprints** match
  the previous snapshot, including existing media and attribution data.
- **40 API checks passed**: bounded museum and artist paging, exact metadata,
  range endpoints, uncertain birth representation, image/curation absence,
  editor preview, unauthenticated preview rejection and public-record exclusion.
- `go test ./...` and `go vet ./...` passed. The previously documented opt-in
  European identity query-plan issue was not fixed or reclassified as passed;
  this is not a 10-million-row performance benchmark.
- Existing media count remains 403; 241 pass the file/rights-evidence audit.
  The 161 oversized legacy pictures and one rights-evidence gap remain unchanged.
  Museum selections remain 569 and owner selections 5; no new publication.

Backup: `/Users/vadimdulub/Documents/artline-greek-round1-batch2-backup-20260911.xi7XwI/before-batch2.dump`.
SHA256: `410fc722671d7fd6f6dce6f5e9905a7803b514307522d5e5ec5284b3c76d3e74`.
`pg_restore --list` read 256 entries/lines; a full restore was not attempted.

Evidence and receipts:

- [Pinned selection](greek-round-01-selection-v2.json), SHA256
  `415a0504ab5f7fd3ca4683687943e7f75e48c7e60088c137bb853b03ddc2f900`.
- [Retained and new review decisions](round-01-decisions-v2.json).
- [Verified full snapshot](snapshots/round-01-greek-review-v2/PAINTERS.md).
- [Rollback receipt](../../../output/greek-painter-review-batch2-preview-v1.json),
  [apply receipt](../../../output/greek-painter-review-batch2-apply-v1.json),
  [replay receipt](../../../output/greek-painter-review-batch2-replay-v1.json),
  [verification results](../../../output/painter-review-verification-v2.json).

## Programme status and next research

Round 1 now records **12 bounded painter reviews and 18 artwork reviews done**;
Economou and Laskaridou have unresolved painter-date reviews. **Zero complete
catalogue rounds are finished. Rounds 2–10 have not started.**

Continue image permission research on these exact objects and review further
individual catalogue entries, especially underrepresented Greek/Cypriot women,
post-Byzantine painters and Russian/Greek icons. SearchCulture's restricted image
licences need per-item review; new evidence must not overwrite previous findings.
Do not describe another small cohort as a new completed full-catalogue round.
