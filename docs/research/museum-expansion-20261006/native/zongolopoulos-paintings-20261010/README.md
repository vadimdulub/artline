# Zongolopoulos painting-category review — 10 October 2026

This bounded pass reviewed 151 additional museum-supplied object records and proposes **150 physical works**, with **one source/image conflict held**. Combined with the preceding [49-work selection](../zongolopoulos-20261010/README.md), the foundation now has **199 pending candidates**. **Nothing in either batch has been added to production.** The last verified production counts remain 18 catalogue rows and 18 numerically date-eligible rows, from 9 October; those counts are stale, and some existing sculpture rows may duplicate physical objects.

The institution is `763803c5-3657-5d75-9cf8-9927a5c6a4de`, `greek-museum-sc-george-zongolopoulos-foundation`. Museum holdings are supported by explicit foundation publisher/provider/source fields and bequest descriptions. No current-display claim is made.

## Sources and selection

The public [SearchCulture collection](https://www.searchculture.gr/aggregator/portal/collections/ZoggopoulosF?language=en) supplied the observed Painting facet and its GET form controls. Six pages exposed 180 of 262 painting-category records: 151 new records with no index date, nine previously reviewed records, and 20 explicitly later than 1970. Only the 151 new object pages were fetched. The remaining 82 painting-category cards were not inspected. This is selected artwork research, not complete collection coverage.

All 151 object descriptions and thumbnails were reviewed, together with eight contact sheets, nine focused comparison sheets, one comparison against earlier pictorial works, and five selected preservation previews. There were no identical image hashes within the new selection or against the previous 128 thumbnails. Visual checks distinguished related landscapes, window scenes, maps, collages and geometric studies; hash differences alone were not treated as proof of distinct works.

The five preservation viewer pages were followed from links in the captured object HTML. Their visible preview images were retrieved for internal comparison. No large TIFF originals were downloaded, and no inaccessible foundation host or failed XML route was retried or bypassed. The web fetch tool separately returned cache misses for two object URLs; the successful direct public captures are preserved with response receipts and hashes.

## Editorial result

The 150 candidates comprise 57 paintings, 62 watercolours, 17 drawings, one print and 13 works with an unresolved controlled type. Collage, mixed media and unspecified physical media remain explicit in the source descriptions. The source's broad Painting category does not override an explicit lithograph, watercolour or pastel description.

- **149 unknown creation dates** remain null and require editorial review. Artist lifespans, style, depicted places, publication pages and inventory numbers do not establish creation years.
- [Source 64368](https://www.searchculture.gr/aggregator/edm/ZoggopoulosF/000041-64368) describes an oil painting signed `Ε. ΖΟΓΓ./1960`. The proposed year is 1960, qualified as an inscription transcribed by the museum; the thumbnail was not sufficient for independent signature verification.
- [Source 64290](https://www.searchculture.gr/aggregator/edm/ZoggopoulosF/000041-64290) describes a lithograph signed 1933, impression 17/20. Both details are preserved. The physical impression's printing date remains unknown; no exact creation year or image-date eligibility is invented.
- Sixteen records explicitly describe two-sided supports. Each counts once. The reused canvas in source 64458 also counts once. Multiple panels in a collage are not counted as separate artworks.
- Thirty-seven candidates retain anonymous creators. Source 64255's reverse is only *probably* by Helen; the anonymous front is not reassigned. Source 64360 is unsigned and from Helen's folder, so its catalogue attribution is qualified. Source 64479 has George in the creator field but an `Ε. Ζογγολόπουλος` signature in the description; both claims are retained and no accepted painter link is proposed.
- **Source 64218 is held:** its description says “Girl with an umbrella,” oil on wood, while both catalogue and preservation previews show a geometric abstract composition. No image swap, invented creator or additional work is proposed.
- Source 64480 has inconsistent descriptions of the reverse portrait and side ordering; the discrepancy is preserved on one physical support. Source 64355 has room/window text and imagery but conflicting torso subject tags, retained as source evidence only.

Every proposed record remains in review. Source titles, original creator fields, descriptions, rights labels, EKT enrichment and apparent doubled inventory strings are preserved. Canonical accession numbers and painter IDs remain null pending verification; exported digits are not silently halved.

## Images and delivery

The specific user-approved Greek museum/artist image workflow remains applicable; an NC/ND label alone is not a reason to block an otherwise supported image in that scope. This pass prepares **zero production images**, because no new candidate has a securely established physical creation date by 1955. All images here are internal review material. The prior batch's 19 prepared images remain unattached.

Production token refresh again failed with `Reauthentication failed. cannot prompt during non-interactive execution.` Restoring the existing Google session with `gcloud auth login` is required before fresh production reconciliation and delivery. There were no production mutation attempts, local database writes, fixtures, backups, commits or deployments in this pass.

Before delivery: refresh institution rows and bounded global source/title/creator comparators, reconcile qualified creators and reverse-side identities, protect prior records, prepare an exact-hash plan, complete a successful backup, apply, verify readback and prove zero-write replay. Pending candidates must not be reported as uploaded or as a verified museum threshold.

The next research institution is Chania from the last saved priority queue. Additional Zongolopoulos discovery can wait for live reconciliation of this 199-work selection; remaining source gaps and the existing sculpture duplicate flags are retained.

## Artifacts

- `review-ledger-001.csv`: every selected source, decision and qualification.
- `editorial-source-decisions-001.json.gz`: literal evidence and detailed decisions.
- `candidate-physical-units-001.json.gz`: 150 candidates, combined pending count 199.
- `physical-unit-review-001.json`: distinct-work comparisons, sides and the held mismatch.
- `checks-001.json` and `research-checkpoint-001.json`: integrity checks, prior checkpoint chain and unchanged production state.

Internal image proofs are under `~/Library/Application Support/Artline/research-proofs/zongolopoulos-paintings-20261010/`. The real local catalogue remains untouched.
