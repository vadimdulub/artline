# Painter influence research — 8 October 2026

**Third round completed:** [324 additional relationships and 326 citations](../painter-influences-round3-20261009/README.md) were added across 137 painter profiles and verified through the public API. Production now contains 7,087 relationships and 8,140 influence citations. Earlier figures below remain historical evidence.

**Second round completed:** [374 additional relationships and 377 citations](../painter-influences-round2-20261008/README.md) were added for 145 painters and verified through the public API. The production total at the end of that round was 6,763 relationships. The first-round figures and pinned artifacts below remain historical evidence.

**Production update, 8 October 2026:** the [authorized import](production-import.md) added **6,379 relationships and 7,427 citations** to production, initially in review. The user subsequently approved publication of both the relationships and their linked painter profiles. All 6,379 claims and their 3,745 linked profiles are now **published**, including **3,723 newly published painters**. No approved relationship remains blocked by painter review status. The [painter publication report](production-painter-publication.md) records the backup, transaction, source preservation and API display fix. The [earlier claim publication](production-publication.md) is retained as historical evidence. The 10 previously published claims were preserved, including the already-present Boudin → Monet influence. Publication approval does not establish independent historical verification; the research limitations below still apply.

The first library-wide source and identity pass covers **23,499 active catalogue records**: 23,409 local records plus production-only records, with both catalogues’ IDs retained. Every record has a documented lookup attempt. This is **not a completed historical review for every painter**: some records could only be searched by name, and most discovered biography passages still need interpretation.

The results contain **2,190 source-reported influence pairs for 1,061 painter identities**, after deduplicating supported shared identities. There are also **4,169 teaching pairs** and **8 documented-admiration pairs**, kept separate. These counts do not mean that every assertion is independently verified. Unresolved identities remain separate rather than being silently merged.

Start with [the readable painter-by-painter influence list](influences-by-painter.md). It supports multiple influences and links each result to its sources. [painters.jsonl](painters.jsonl) contains every library record, including painters for whom no relationship was established, together with source checks, relationships, evidence and remaining leads.

| Measure | Result |
|---|---:|
| Library records with a documented lookup attempt | 23,499 |
| Records checked for Wikidata influence/teacher statements | 20,307 |
| Additional name searches | 6,332 |
| Supported research identity bindings added, without changing the catalogue | 3,140 |
| Records matched to inspected WikiArt profiles | 2,539 |
| Identity-checked biography pages scanned across 19 languages | 14,433 |
| Biography passages discovered | 20,568 |
| Biography passages individually reviewed | 407 |
| Museum/scholarly documents individually reviewed | 19 |
| Distinct museum/scholarly-supported relationship pairs | 74 |
| Catalogue writes during the initial research pass | 0 |

At catalogue-record level there are 2,193 influence, 4,179 teaching and 8 admiration pairs. Small differences from the identity-level totals come from duplicate catalogue records that share supported identifiers. Of the records, 1,063 have a reported influence and 2,503 have a reported teacher. Teachers are never counted as artistic influences solely because they taught someone.

**What remains:** 3,096 records have unresolved identities after searching. Another 6,197 have biography leads but no retained relationship yet. In total, 20,161 discovered passages have not received individual review; some concern teaching, movements, literature or other people rather than the subject’s artistic influences. For 11,050 records, the checked sources supplied no retained relationship or pending keyword passage. That is not evidence that those painters had no influences. [follow-up-queue.jsonl](follow-up-queue.jsonl) retains the next research targets, including records already having some results.

The relationship direction is always **inspiring painter / teacher → library painter**. The readable report reverses the visual presentation to **library painter ← influence**. Friendship, shared movement membership, resemblance, admiration, collaboration and teaching are not automatically converted to influence. A source may support a particular work or period rather than a painter’s whole career. Painter biography research is not an assertion that the affected artworks satisfy Artline’s pre-1971 artwork cutoff.

Evidence has three different levels of review:

- Museum and scholarly texts were read and annotated. Interpretive or qualified statements retain that qualification in their evidence notes.
- Selected Wikipedia passages were read for the named people and direction. Their underlying references were not all independently consulted. Attribution, revision links and retrieval information are retained.
- WikiArt fields and Wikidata statements are explicit source assertions. Wikidata statement IDs, ranks, qualifiers and references are preserved. A supplied reference does not itself mean that the reference was verified. Unreferenced assertions remain visibly unreferenced.

For example, the [National Gallery’s Bellini biography](https://www.nationalgallery.org.uk/artists/giovanni-bellini) supports Jacopo Bellini and Andrea Mantegna as formative influences; its tentative Antonello statement was not made definite. [Alpatov’s Rublev study](https://www.icon-art.info/book_contents.php?book_id=115&chap=6) supports Theophanes as an artistic example while rejecting a direct pupil relationship. The conflicting Wikidata teaching statement is held, not presented as settled. [The Prado’s Spanish exhibition text](https://www.museodelprado.es/actualidad/exposicion/historia-de-dos-pintoras-sofonisba-anguissola-y/5f6c56c8-e81a-bf38-5f3f-9a2c2f5c60eb) supplies several influences for Sofonisba Anguissola and Lavinia Fontana; a subject error in its English translation was not propagated.

Checks also caught collective traditions in WikiArt’s influence fields, impossible chronology, posthumous personal-teaching claims, and non-painter sources. They remain in [identity-and-evidence-holds.json.gz](identity-and-evidence-holds.json.gz), not in the individual-painter totals. Unnamed traditions are not discarded from research, and no individual painter is invented to represent them. A missing painter occupation in an authority file is a scope-review hold, not proof that the person never painted.

Useful structured files:

- [source-reported-relationships.json.gz](source-reported-relationships.json.gz): directed pairs, source evidence and review state.
- [painter-research-register.json.gz](painter-research-register.json.gz): one row per library record, including negative and unresolved outcomes.
- [reviewed-source-notes.json](reviewed-source-notes.json), [reviewed-biography-decisions.json](reviewed-biography-decisions.json) and [reviewed-source-constraints.json](reviewed-source-constraints.json): editorial decisions and counterevidence.
- [research-identity-bindings.json](research-identity-bindings.json): source-backed research identity resolutions and conflicts; no catalogue merges.
- [biography-leads.json.gz](biography-leads.json.gz): unaccepted passage pointers, candidate entities and unresolved link titles. Named co-occurrence is not a relationship.
- [summary.json](summary.json), [validation.json](validation.json) and [live-readonly-verification.json](live-readonly-verification.json): totals and verification receipts.

The research script is [ops/research-painter-influences-20261008.py](../../../ops/research-painter-influences-20261008.py). It is resumable and has no catalogue mutation command. Pinned snapshots are checksum-protected. Do not rerun `export` over them or rebuild `crosswalk` over the later name-resolution bindings. Rebuild derived reports with `assemble`, then run `validate`. This research format is not a database-import payload; evidence vocabularies and unresolved identities require an explicit import mapping.

Raw full biographies and passage contexts are kept under `/Users/vadimdulub/Library/Application Support/Artline/research/painter-influences-20261008/`. The project retains retrieval manifests, revision URLs, hashes and research decisions. Existing WikiArt captures are dated 19–20 September 2026; the additional profile receipts are dated 8 October. Cached pages are not described as freshly fetched. Wikipedia excerpts and adaptations are attributed to Wikipedia contributors under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), with page/revision links in the manifests and review queue; Wikidata is CC0. No artwork images were downloaded for this task.

Fourteen consistency checks passed across all 23,499 records and 6,380 relationship rows. These check coverage, IDs, citations, direction, chronology, disputed teaching, source grouping and report consistency; they do not establish historical truth for every assertion. At the end of the initial research pass, read-only checks found the same baseline influence-claim counts: local 0, production 10. The subsequent authorized import increased the production total to 6,389. Following the user's publication approval, all 6,389 claims have published status, including the 10 preserved prior claims. The follow-up painter publication removed all profile-status barriers for the approved relationships. Factual painter metadata, research qualifications, citations, artworks and the real local database were preserved. A scoped API ordering fix ensures each painter's own influences and teachers appear before their outgoing relationships within the bounded response. No Git commit was made.
