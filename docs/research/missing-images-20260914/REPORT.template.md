# Missing artwork images: follow-up research

14 September 2026 · Artline existing catalogue · Final read-only audit: {{AUDIT}}

**{{CANDIDATES}} artwork records still without images have source-supported image candidates.** This pass assessed 2,191 distinct records: 1,949 fresh records and 242 explicit follow-ups. {{NEW_CANDIDATES}} candidates belong to the fresh cohort. The follow-ups include all 238 previously failing Minneapolis image endpoints, now responding through the museum’s current image service, and four Greek or Byzantine identity questions. {{DEFERRED}} records remain deferred and {{SUPERSEDED}} were superseded by a concurrent catalogue change.

The result is a research handoff, with object identifiers, image URLs, source evidence, rights statements and review notes. It is not an image import. The files have not been attached to artwork records or approved for publication. Eleven selected research specimens decoded successfully and were visually inspected; most candidate images received only an HTTP HEAD check. The distinction is recorded per object rather than hidden behind one “verified” label.

Start with [verified-candidates.jsonl](verified-candidates.jsonl). [Deferred candidates](deferred-candidates.jsonl) preserve restrictions, missing images, identity discrepancies and transport failures. [summary.json](summary.json) contains the final counts; [all-decisions.jsonl](all-decisions.jsonl) provides one outcome per assessed UUID.

## Coverage and the meaning of “missing”

{{TABLE}}

The main fresh cohort comprised 750 Finnish National Gallery records, 400 Minneapolis records, 500 Smithsonian American Art Museum records and 250 Walters records. A separate, bounded Russian-priority query selected 49 additional records at the National Gallery of Art, Metropolitan Museum of Art and Art Institute of Chicago. The Greek follow-up covered Saint Marina, Madre della Consolazione, Stavrakis’s Deposition and Doxaras’s Assumption. These four were explicitly revisited because the previous pass left specific identity questions; they are not counted as fresh research.

The selection excluded UUIDs already present in the previous campaign inventories and the entire previous 1,234-record overnight cohort. The fresh Russian-priority supplement also excluded the newly reserved main cohort. These exclusions reduce duplication with other agents; they cannot prevent another thread from independently selecting an unannounced record. A final scoped database audit therefore rechecked every UUID for image attachments, status and creation eligibility.

At 05:38 UTC the local catalogue held 231,643 artworks, including 211,645 non-archived records without a primary image. This is a dated baseline, not an estimate of the final catalogue: other agents were actively changing it. A separate scoped audit found no secondary image links on the 2,187 main and fresh-priority records before finalisation. The final audit also checks secondary links on the four Greek follow-ups. Thus “missing” is not merely an assumption that a null primary pointer means no other images exist.

All initial selections used the existing backend creation classifier and the artwork creation cutoff of 1970. Source dates, local dates and qualified creator labels remain separate. A newly found photograph does not justify inventing a year, assigning an unknown artist, changing an attribution, or converting a source museum connection into an accepted Artline holding. **{{SELECTION_REVIEW}} candidates still lack the backend’s required catalogue selection evidence.** Their source material is preserved for editorial review.

## The Minneapolis recovery

The largest practical improvement is the recovery of a broken delivery assumption. The earlier pass confirmed valid Public Domain image metadata for 238 objects but could not retrieve images from the legacy `api.artsmia.org/images/{id}/large.jpg` route. This pass inspected the live collection website’s JavaScript and found the image path it actually uses. The current website derives its image URL from the live object’s `Cache_Location` and `Primary_RenditionNumber`, with a requested size suffix.[^mia-code]

For example, Jawlensky’s *Mama in Heller Mondnacht*, object 143745, resolves to `https://img.artsmia.org/web_objects_cache/143000/700/40/143745/mia_8030766_800.jpg`. Its 636 × 800 image decoded and was visually inspected. The complete stylised face, dark border and narrow outer margin are visible. This is direct evidence that the current route works on a previously failing priority record, rather than a guessed substitute URL.[^mia-object]

All 638 selected Minneapolis objects were checked through the current exact-ID search API in bounded groups. A positive decision required the expected accession, the literal Public Domain rights category, a valid image, full display permission, no image copyright notice and concrete current image-path fields. The 400 fresh records produced 268 candidates and 132 deferrals. The 238 recovery records all produced responding candidates. All 506 proposed current endpoints returned HTTP 200 to HEAD requests. Three selected Minneapolis images were also downloaded, decoded and visually reviewed.

The archived metadata remains useful provenance, but it is not the current authority. Comparing the 400 fresh objects found 145 records with differences in the inspected fields: 141 had a different rights category, six a different image-copyright field, three a different image-validity field, and one a different accession. These categories overlap. The comparison is preserved in [mia-snapshot-current-differences.json](mia-snapshot-current-differences.json); it does not establish when or why the museum made each change.

Ten positive Minneapolis records also have different source date text from Artline. Some are shortened ranges or added precision; others are substantive, such as the Shōgitai warrior changing from 1868 locally to circa 1874 in the current source. Both statements are retained for review in [mia-current-date-differences.json](mia-current-date-differences.json). No candidate’s current date text supplied a numeric year after 1970, and no local date was rewritten.

One important deferral is *Landscapes of the Four Seasons: Spring, Summer, Autumn and Winter*, object 129457. Artline’s supplied accession is `VR.1`; the current museum record lists several accessions and reports an invalid image. The shared object ID and title do not erase that discrepancy. The original local metadata remains unchanged, with an explicit reconciliation task.[^mia-composite]

The museum distinguishes its Public Domain image category from other image-rights categories.[^mia-policy] The handoff preserves the literal museum statement. A generic Public Domain Mark reference in the structured data is explanatory; it does not imply that the museum supplied that specific licence URI. Current URLs appear in `recommended_image` and `images`; legacy leads are retained separately as `snapshot_image_candidates`.

## Other museum sources

The Finnish National Gallery snapshot supplied individually CC0-labelled media for 657 of the 750 fresh records. The remaining 93 had no explicitly eligible image in that source snapshot. Each positive candidate matched the museum object and accession and retained the photographer, source dimensions and concrete derivative path. All 657 recommended endpoints responded to HEAD requests. The four records prioritised through documented Russian cultural affiliations include Bogolyubov views and Kuznetsov’s *Harvester*. Two selected Russian-priority reproductions were decoded and inspected. General collection membership was not used as a substitute for an individual media licence.[^fng]

Smithsonian American Art Museum contributed 498 candidates from 500 fresh records. Each selected media entry itself carries CC0 usage information; the record’s open metadata label alone was insufficient. The source objects retain delivery identifiers and available alternative resources. Some HEAD responses lacked a useful image content type, and two initial endpoint checks failed; those are distinguished in the data. The selected *“My First Painting”* preview decoded, but a flower meets the left image boundary, so the full paper boundary remains a rendition-review question.[^saam]

Walters contributed {{WALTERS_CANDIDATES}} candidates from its 250-record cohort. Static object and media data were matched at the same pinned museum commit, followed by current page checks for exact object ID, accession and the CC0 link associated with the proposed image. The old persistent links initially encountered timeouts; current object URLs worked. Later interruptions required bounded recovery passes. Intermediate results remain preserved so that a temporary access failure is not mistaken for a museum rights decision. The museum’s API documentation and its broader reproduction policy must be read together because the latter describes exceptions.[^walters]

The first image on a current page is a research proposal, not necessarily the best final rendition. The Walters *Bacchus* caricature preview is monochrome. That observation concerns the reproduction; it does not establish that the original artwork is monochrome. Alternative current images remain available for editorial comparison.

## Russian-priority gaps and one additional open image

The supplementary query used documented cultural-affiliation relationships, not modern-country birthplace labels. It selected only records still missing images and outside the reserved prior cohorts. This matters for artists with transnational lives: a place of birth alone should not silently determine a new national label. Existing artist metadata was not rewritten.

The 49-record supplement found one positive image candidate: Vincent G. Stiepevich’s *Proposed Wall Decoration No. 2, Old Corcoran Gallery of Art*, dated 1880, accession 2015.19.2436. Its National Gallery object page explicitly marks the media as public domain and supplies a download link. The linked museum policy releases qualifying open images under CC0. The 550 × 800 preview decoded and shows the complete mounted sheet, outer margins and inscriptions.[^nga-work][^nga-policy]

Among the other National Gallery records, 38 pages explicitly withheld media downloads and five reported unavailable media. Two source checks failed. A displayed thumbnail and even a zoomable endpoint do not override the page’s download restriction. The policy lists several possible reasons for an image not being open; the research does not guess which applies to each object. Automatically generated visual descriptions found on these pages were preserved only as part of the captured source, and were not used to prove object identity.

The Art Institute of Chicago’s *Spanish Dancer* by Natalia Goncharova has a current `is_public_domain: false` value and an explicit copyright notice. The two selected Met records by Léon Bakst likewise have false public-domain flags and no primary image returned by the museum API. These are specific negative findings, not a general conclusion about all works by those artists or all pre-1970 art.[^aic][^met]

The broader local priority count remains heavily weighted toward the Russian museum-session import. That count is recorded in [priority-gap-counts.json](priority-gap-counts.json), but it was not treated as authority to download thousands of images. This pass concentrated on a bounded set with identifiable source records and preserved the remaining research frontier.

## Resolving the Saint Marina identity

The new positive Greek follow-up is **Saint Marina, ΒΧΜ 01546**. The museum records its origin at the Church of Hagios Gerasimos in Argostoli, dimensions of 115 × 78 cm, and a late-fourteenth- or early-fifteenth-century date. Its description relates the unnamed maker to workshops of Constantinople. That qualification remains intact.[^marina-museum]

An independently licensed photograph by George E. Koronaios agrees with the museum’s subject, origin and period but does not state the accession. A separate, accession-labelled book scan provided a reference depiction. Visual inspection of both files found corresponding inscriptions, the ornamented cross, the diagonal damage across the face and the vertical board join to the right of centre. **The exact-image match is a documented researcher inference from those distinctive features and the accompanying metadata**, not a claim that the independent photographer supplied an accession he did not provide.[^marina-photo][^marina-reference]

The recommended photograph is explicitly CC BY-SA 4.0. Its credit identifies the photographer separately from the medieval maker. The complete board is visible, but strong warm illumination affects colour; it remains subject to rendition review. The book scan is an identity reference rather than the recommended delivery asset. Neither image’s capture or upload date establishes that the icon is currently on view.

Three other Greek follow-ups remain deferred, but now have more concrete next steps:

| Work | New primary evidence | Remaining issue |
|---|---|---|
| Stavrakis, *Deposition from the Cross* | Benaki ΓΕ 3053; signed maker; eighteenth-century object; 38.3 × 23.5 cm | The 1729–1786 text accompanies the maker. Preserve an eighteenth-century source date separately. The candidate file could not be inspected after rate/access failures, and its aspect ratio needs comparison. |
| Doxaras, *Assumption of the Virgin* | National Gallery Π.150; named artist; oil on canvas; 45 × 34 cm | Current museum page provides no artwork creation date. Reconcile accession and date provenance before treating the record as validated. The licensed image is only 586 × 765 pixels. |
| *Madre della Consolazione with Saint Francis* | ΒΧΜ 01550; 60 × 52 cm; shortly before 1501 | The independently licensed photograph still needs exact visual/accession confirmation. Preserve the museum’s qualified stylistic connection to Tzafouris. |

The source pages and file revisions are preserved together.[^benaki][^doxaras][^madre] No additional creator, accession, date or accepted holding was written into the database. Failure to finish an image match is not a reason to delete a named-creator record or erase its supplied provenance.

## Quality, rights and evidence limits

Eleven successful specimen downloads were chosen only after reviewing their source rights: six from the main museum cohort, two additional priority/recovery specimens, and three Greek identity specimens, including the accession-linked reference scan. They are research samples, not a statistical quality audit. Preview receipts retain URL, retrieval time, dimensions and checksum; original bytes were left unchanged in the temporary research location. No colour correction, cropping, retouching or AI reconstruction was performed.

The visual checks exposed practical choices that a HEAD request cannot reveal: a large decorative frame around a Minneapolis painting, a monochrome Walters reproduction, strong warm illumination in the Saint Marina photograph, and uncertain paper boundaries in a Smithsonian rendition. Successful decoding also does not prove that a reproduction is complete, colour-accurate or the preferred view. These observations are attached to the relevant candidate UUIDs.

Some providers temporarily refused or timed out on requests. Streams paused after access/rate responses or repeated failures; selected later recovery attempts were bounded and retained their evidence. A failed request is not evidence of a missing physical photograph or a copyright restriction. Conversely, an HTTP 200 response is not permission to reuse a file. The final dataset separates the image-rights finding, endpoint result, visual review and catalogue gate.

The final audit removes records that acquired media concurrently, became archived or no longer met the current creation classifier. It does not prevent a subsequent change after the recorded audit time. Any later attachment workflow should recheck the selected UUIDs, validate the actual chosen bytes and credit, and apply the existing editorial gates. No current-display claim is inferred from a museum holding, a dated photograph, or an undated exhibition listing.

## Handoff and reproducibility

| File | Purpose |
|---|---|
| [verified-candidates.jsonl](verified-candidates.jsonl) | Remaining candidates, keyed by Artline UUID, with current proposed URLs and review requirements |
| [deferred-candidates.jsonl](deferred-candidates.jsonl) | Preserved negative findings, unresolved discrepancies and concurrent changes |
| [summary.json](summary.json) | Counts by source, batch, outcome, endpoint and licence |
| [final-catalogue-audit.json](final-catalogue-audit.json) | Scoped read-only image, status, creation-scope and selection-evidence check |
| [selection.json](selection.json), [selection.sql](selection.sql), [exclusions.json](exclusions.json) | Frozen main cohort and exclusion basis |
| [mia-current-records.json](mia-current-records.json), [mia-snapshot-current-differences.json](mia-snapshot-current-differences.json) | Current exact-ID evidence and archive differences |
| [priority-new-results.jsonl](priority-new-results.jsonl), [priority-followup-results.jsonl](priority-followup-results.jsonl) | Additional priority research and explicit revisits |
| [museum-visual-review.json](museum-visual-review.json), [supplement-visual-review.json](supplement-visual-review.json), [priority-visual-review.json](priority-visual-review.json) | Observations from all eleven inspected specimens |
| [evidence-manifest.json](evidence-manifest.json), [evidence-validation.json](evidence-validation.json) | Preserved-file inventory and integrity checks |

Scoped source objects live in `objects/`; network responses and dated receipts live in `captures/`. Large pre-existing museum snapshots remain at the provenance paths recorded in the receipts, rather than being copied again. `worker.py`, `priority_research.py` and `finalize.py` document the extraction and decision logic. They are research tools, not import jobs. The evidence inventory covers this directory; referenced earlier research and museum snapshot files remain explicit dependencies.

## Sources

Sources were consulted on 13–14 September 2026. Fresh object and transport receipts are dated 14 September; reused snapshot/policy evidence retains its original retrieval date. The links below identify the primary records and policies, while the structured handoff contains the individual source URLs for every candidate.

[^mia-code]: Minneapolis Institute of Art, [live collection website bundle](https://collections.artsmia.org/bundle.js) and [official collection-search infrastructure](https://github.com/artsmia/collection-elasticsearch). Bundle bytes and hash are preserved in this directory.
[^mia-object]: Minneapolis Institute of Art, [current object 143745](https://search.artsmia.org/ids/143745) and [collection page](https://collections.artsmia.org/art/143745).
[^mia-composite]: Minneapolis Institute of Art, [current object 129457](https://search.artsmia.org/ids/129457).
[^mia-policy]: Minneapolis Institute of Art, [Copyright and Image Access and Use](https://new.artsmia.org/copyright-and-image-access); [official archived collection repository](https://github.com/artsmia/collection), commit `790eb625934680f2eeccb262391618d2ca948486`.
[^fng]: Finnish National Gallery, [Photographic service](https://kansallisgalleria.fi/en/photographic-service/) and [official object API](https://kokoelma.kansallisgalleria.fi/api/v1/objects). The 13 September object snapshot and its hash are identified in the per-object evidence.
[^saam]: Smithsonian Institution, [Open Access FAQ](https://www.si.edu/openaccess/faq). The selected SAAM records preserve their official Open Access distribution URLs and per-media usage fields.
[^walters]: Walters Art Museum, [Open Data](https://api.thewalters.org/index.html), [Image Rights, Reproduction, and Terms of Use](https://thewalters.org/about/policies/rights-reproductions/) and [official static data repository](https://github.com/WaltersArtMuseum/api-thewalters-org), commit `f7531ed751ac2c138eeb6f923a3b4fd325d78adf`.
[^nga-work]: National Gallery of Art, [Stiepevich, Proposed Wall Decoration No. 2, 2015.19.2436](https://www.nga.gov/artworks/169495-proposed-wall-decoration-no-2-old-corcoran-gallery-art).
[^nga-policy]: National Gallery of Art, [Terms and Notices, Open Access Policy](https://www.nga.gov/terms-and-notices).
[^aic]: Art Institute of Chicago, [current API record for Spanish Dancer, 37368](https://api.artic.edu/api/v1/artworks/37368).
[^met]: Metropolitan Museum of Art, current API records [489364](https://collectionapi.metmuseum.org/public/collection/v1/objects/489364) and [335000](https://collectionapi.metmuseum.org/public/collection/v1/objects/335000).
[^marina-museum]: Byzantine and Christian Museum, [Saint Marina, ΒΧΜ 01546](https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=28).
[^marina-photo]: George E. Koronaios, [Saint Marina photograph and CC BY-SA 4.0 declaration](https://commons.wikimedia.org/wiki/File:Icon_of_Saint_Marina_(14th_-15th_cent)_at_the_Byzantine_and_Christian_Museum_of_Athens_on_12_April_2019.jpg), Commons page 78032339, revision 809592816.
[^marina-reference]: [Saint Marina accession-linked reference scan](https://commons.wikimedia.org/wiki/File:Saint_Marina_icon.JPG), Commons page 7678483, revision 346498507. Used with the primary museum record and the independently licensed photograph.
[^benaki]: Benaki Museum, [Deposition from the Cross, ΓΕ 3053](https://www.benaki.org/index.php?option=com_collectionitems&view=collectionitem&Itemid=385&id=107739&lang=el); [Commons candidate file](https://commons.wikimedia.org/wiki/File:Stylianos_Stavrakis_Descent_from_the_Cross.png). The live museum page was retrieved successfully by the research client despite a separate search-browser fetch failure.
[^doxaras]: National Gallery, [The Assumption of the Virgin, Π.150](https://www.nationalgallery.gr/en/artwork/the-assumption-of-the-virgin-8847/); Tzim78, [Commons photograph and licence](https://commons.wikimedia.org/wiki/File:Nikolaos_Doxaras_Assumption_of_Mary.png).
[^madre]: Byzantine and Christian Museum, [Madre della Consolazione, ΒΧΜ 01550](https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=41); Francesco Bini, [Commons photograph and licence](https://commons.wikimedia.org/wiki/File:Grecia,_icona_della_madonna_madre_della_consolazione_con_san_francesco_d%27assisi,_1490_ca.jpg).
