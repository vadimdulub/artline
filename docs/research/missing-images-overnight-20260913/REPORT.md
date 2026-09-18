# Missing artwork images: overnight research

13–14 September 2026 · Artline existing catalogue · Final catalogue audit: 14 September, 05:03 UTC

**980 existing artworks still without an image have a source-verified image candidate.** The review covered 1,234 distinct artwork records. Another 247 remain deferred; seven acquired images through concurrent catalogue work and are excluded from the candidate queue. These are research findings, not completed image imports.

“Source-verified” means that the recorded object identity and an explicit reproduction-rights statement support the proposed image. It does **not** mean every image has been downloaded, inspected, compressed, attached or approved for publication. Of the 980 candidates, 739 returned HTTP 200 to an image-endpoint HEAD request. The remaining group comprises 238 Minneapolis candidates whose legacy image endpoint timed out and three independently licensed Byzantine-icon photographs. All nine selected previews subsequently decoded and were visually inspected, including the three icon photographs. Thus 742 candidate endpoints have a successful HEAD or decoded-preview check; 238 remain unverified. The sample is recorded in [visual-review.json](visual-review.json).

The machine-readable handoff is [verified-candidates.jsonl](verified-candidates.jsonl). Each row retains its Artline artwork UUID, museum identifier, source evidence, proposed image URL, rights, credit and remaining review requirements. [Deferred candidates](deferred-candidates.jsonl) preserve negative findings and concurrent changes. No catalogue records, publication states, production services or storage objects were changed by this research.

## Coverage and results

| Source | Reviewed | Candidates still missing an image | Deferred | Filled concurrently |
|---|---:|---:|---:|---:|
| Finnish National Gallery | 250 | 245 | 1 | 4 |
| Minneapolis Institute of Art | 250 | 238 | 12 | 0 |
| Smithsonian American Art Museum | 250 | 247 | 3 | 0 |
| Walters Art Museum | 250 | 247 | 3 | 0 |
| SMK, National Gallery of Denmark | 200 | 0 | 200 | 0 |
| Greek and Byzantine priority records | 34 | 3 | 28 | 3 |
| **Total** | **1,234** | **980** | **247** | **7** |

These figures describe a fixed, deliberately bounded cohort. They are not estimates of each museum’s complete digitisation rate. The main cohort excluded 20,790 artwork identifiers found in previous image-campaign candidate inventories. The Greek supplement separately checked thirteen anonymous or workshop-associated Athens icons and twenty-one works linked to named Greek artists. Rechecking the selected UUIDs at the end prevented concurrent additions from being counted as new opportunities.

The baseline contained 229,000 artworks, including 210,918 non-archived records without a primary image. That baseline was captured at 19:54 UTC on 13 September. Catalogue-wide totals can move while other agents import or enrich records; the fixed-cohort results above are the appropriate measure of this research. The baseline, selection SQL and exclusion inventory remain available alongside this report.

**977 candidates still require catalogue selection review.** They belong to newer museum-linked metadata records for which the backend selection-evidence gate was false at the final audit. A source museum’s object number, title and accession provide useful evidence for review, but an image match does not itself change Artline’s editorial state. The three Byzantine icon candidates already had selection evidence. All candidates still require the applicable image-quality and attachment checks.

The initial main-cohort ranking included existing Russian or Greek country associations. Some associations are explicitly birthplace records rather than cultural affiliation. The final audit preserves those relationship types: Jean Béraud, Lovis Corinth and Eero Järnefelt must not be described as Russian artists merely because their records include a modern-country birth association. The separate named-Greek supplement used cultural-affiliation relationships specifically. No artist’s country metadata was changed.

## Where the useful images are

### Finnish National Gallery

The preserved official object dataset contains individual multimedia records with CC0 labels, photographer names, display-image flags, dimensions and concrete JPEG asset paths. These fields support direct object-to-image matching without a title-based image search. The museum’s photographic service distinguishes copyright-free images from images subject to copyright; a general collection membership was therefore insufficient.[^1]

Of 250 selected objects, 249 supplied a CC0 image in the snapshot. Four have since acquired images in Artline, leaving 245 candidates. Every proposed Finnish image endpoint returned HTTP 200. Some responses identified the content as `application/octet-stream`, while others used `image/jpeg`; the generic MIME type alone is not evidence that a source-labelled JPEG is unavailable. Full decoding remains a separate check.

The proposed derivative is the museum-supplied 1,000-pixel JPEG path, with the designated display image preferred where available. Photographer credits are retained even where CC0 does not require attribution. The dataset was retrieved on 13 September and its stored SHA-256 was checked before extracting the selected objects. A snapshot retrieval date is not a claim that every object’s description or photograph was updated that day.

### Minneapolis Institute of Art

Minneapolis supplies a particularly important distinction: its collection metadata can be open while an individual image has different rights. Its image-access policy explicitly describes Public Domain images as reusable and distinguishes them from other rights categories.[^2] The official search infrastructure also documents exact single-object and multiple-object retrieval.[^3]

The pinned GitHub archive contains duplicate object JSON files in different directories. For some objects, their rights labels differ. The documented object path was used for the initial record, then 249 of the 250 selected IDs were retrieved from the current museum search API. Current records supported 238 valid Public Domain images with full image display. Eleven current objects lacked a valid image, and one selected ID was not returned. Those twelve remain deferred.

All 238 positive records remain valuable source-verified leads, but **their image delivery needs recovery**: the documented legacy `api.artsmia.org/images/{id}/large.jpg` endpoint timed out during this pass. This result does not establish that the museum lacks an image; the current museum records explicitly report valid images. It establishes that the proposed legacy transport was not verified. Their rows preserve current rights, accession and image dimensions so that a current delivery URL can be resolved without repeating the identity research.

The live data also demonstrates why identity, nationality and descriptive metadata should remain separate. Jawlensky’s *Mama in Heller Mondnacht* retains accession 2022.64.6 and its Public Domain image, while the current source has updated artist wording and contextual fields. No corresponding changes were inferred for Artline’s attribution or date.

### Smithsonian American Art Museum

Smithsonian distinguishes open metadata from open media: the CC0 designation must apply to the asset itself. Its Open Access FAQ explicitly discusses records with open metadata but restricted or absent media.[^4] The review therefore required the selected `online_media` entry’s own usage field to be CC0, rather than relying on the record-level metadata licence.

247 of the 250 selected records supplied such an image; three did not. All 247 proposed delivery endpoints returned HTTP 200 to HEAD requests. Most supplied no image MIME type in those responses, so HTTP reachability should not be confused with successful image decoding. The original media records retain exact Smithsonian image identifiers, download alternatives and available dimensions. No high-resolution TIFFs were downloaded.

The cohort is weighted towards earlier paintings, including numerous works by George Catlin. It is a selected backlog sample, not a representative survey of all SAAM artists or periods. Historical titles remain source metadata; this research neither rewrites them nor supplies new claims about the people depicted.

### Walters Art Museum

Walters makes static API data and images available under CC0, but its broader policy also notes exceptions, including some loaned or otherwise protected works.[^5] The static release alone was therefore followed by a current object-page check.

The object and media CSVs were matched at the same pinned museum commit using object ID, accession and filename. Current pages then had to confirm the object ID and accession and associate the proposed image with an explicit CC0 link. This matters because current pages can contain newer photographs and a different primary image from the snapshot.

247 current objects supplied an explicitly CC0 image and a responding image endpoint. Three supplied no image meeting that live-page condition and remain deferred. The live page’s primary view is preferred, with other listed images retained as alternatives. A photograph’s presence on the page without the image-level rights link was insufficient.

### SMK

All 200 selected SMK objects were returned by exact object number, but their museum API records reported no image. Their public-domain status did not supply a missing photograph. These are therefore **source-image gaps**, rather than failed downloads or a claim that their artworks are in copyright.

This sample consisted of the earliest remaining eligible, previously unreserved records. It should not be extrapolated to the entire SMK collection or to earlier successful Danish image campaigns. The negative records are useful for preventing repeated automated attempts against the same unavailable images. A later museum digitisation update or a separately verified photograph could change an individual decision.[^6]

## Greek and Byzantine priorities

The museum object pages were used for identity and dating; independently licensed photographs were evaluated separately. The Byzantine and Christian Museum’s website terms limit reuse of its own website material. Copying one of those images to Commons with a public-domain artwork label does not, by itself, resolve the source-policy question.[^7]

Three candidates remain ready for image-quality review:

| Existing artwork | Museum accession | Image evidence | Required credit/licence |
|---|---|---|---|
| *The Raising of Lazarus* | ΒΧΜ 00980 | Independent photograph explicitly names BXM 980; museum confirms the twelfth-century Mount Athos icon | George E. Koronaios; CC BY-SA 4.0 |
| *The Apostles Peter and Paul* | ΒΧΜ 00999 | Independent photograph explicitly names BXM 999; museum confirms the late-fourteenth-century object | George E. Koronaios; CC BY-SA 4.0 |
| *The Hospitality of Abraham* | ΒΧΜ 01544 | Independent photograph explicitly names BXM 1544; museum confirms the early-fifteenth-century Cretan-workshop icon | George E. Koronaios; CC BY-SA 4.0 |

The three image records retain the Commons file revision, file checksum, photographer, original URL and thumbnail URL, together with the museum evidence.[^8][^9][^10] The photographer is not substituted for the medieval maker. Anonymous and workshop-associated creators remain supported explicitly, and no current-on-view claim is inferred from a museum photograph’s date.

An additional exact match was found for Volanakis’ *Collecting the Nets*, accession Π.10380. The file distinguishes the old painting from Tilemahos Efthimiadis’ CC BY 2.0 photograph; its exported short licence label alone would have missed that photographic attribution requirement. The museum confirms the accession, 1871 date and dimensions.[^11] Another agent attached an image to this artwork during the research, so it is retained as evidence but excluded from the remaining-image queue.

Several promising leads remain deliberately unresolved. The Cyprus *Hodegetria* and *Dormition of Saint Ephraim* have exact accession matches on museum-derived files, but their reproduction-rights basis needs further review. An independent photograph of *Saint Marina* matches subject, origin and period, while a different book scan supplies the accession; those records should not be joined without confirming the exact depiction. *Madre della Consolazione* has a licensed photograph with a matching subject but no explicit accession, and its qualified connection to Tzafouris must not become an unqualified new attribution.

Other icon searches returned similarly named works, documents and unrelated objects. Those results are discovery evidence, not accepted matches. In particular, a generic Nativity photograph must not replace the museum’s small landscape-format Venetian or Greek-Venetian panel simply because both titles describe the Nativity.

## A concrete version conflict

The *Children’s Concert* case demonstrates the cost of title-only matching. The National Gallery identifies its object as **1900**, accession Π.475, and explicitly explains that Iakovidis painted two versions. The Commons leads found here describe an 1894 painting or an 1884–1890 interval. Similar subject, artist and dimensions therefore do not settle which version a reproduction depicts.[^12]

This object acquired an image through concurrent work before the final audit. The research preserves the conflict and the attached-media provenance in [concurrent-greek-media.json](concurrent-greek-media.json); it does not claim that the concurrent image is wrong. The question requiring review is whether the image depicts the later National Gallery version despite inconsistent secondary metadata. No catalogue date was changed to fit a convenient image.

The four named post-Byzantine works initially represented through Wikidata also retain their broad date statements and qualifications. Their Commons leads point towards Benaki or National Gallery objects, but missing accessions, different date intervals and unresolved reproduction evidence prevent automatic attachment. A creator’s lifespan is never a substitute creation year.

## Evidence strength and remaining work

The strongest immediate handoff consists of current Walters object-level CC0 images, Finnish object-linked CC0 assets, Smithsonian individually designated CC0 media and the three accession-confirmed independent icon photographs. Minneapolis contributes a substantial, separately identifiable group with current rights and identity evidence but an unverified legacy image endpoint.

The remaining checks differ by record: establish a working image URL where needed; decode and inspect the selected reproduction for completeness, orientation, legibility and unwanted borders; preserve the exact licence and credit; and review catalogue selection evidence where the backend gate remains false. A successful HEAD request proves neither visual quality nor readiness for publication. The nine-preview sample is not a quality audit of all 980 candidates. It exposed concrete quality questions: the Finnish Venice view includes a substantial frame, the Catlin scene is soft in its delivered derivative, and the Walters *Head of an Old Man* is a black-and-white reproduction. These remain candidates with quality notes, not automatic primary-image choices. The three icon previews show their full panels; warm lighting and existing paint losses were preserved without correction.

The research does not establish copyright clearance for every artwork created before 1970. Creation eligibility, object identity, photographic rights, editorial acceptance and current display status remain separate questions. No museum presence was used to infer current display, no creator was invented, and no artwork was published as part of this work.

The searches were bounded. Category and search responses preserve continuation markers, including cases where only the first results were inspected. A Commons rate-limit response stopped that search stream; subsequent follow-up used a slower pace after its recorded cooldown. Unsearched files, spelling variants and later source updates may still provide valid images. “Deferred” means not confirmed by this evidence, not that an image cannot exist.

## Evidence files

| File | Purpose |
|---|---|
| [summary.json](summary.json) | Counts at the final fixed-cohort audit |
| [verified-candidates.jsonl](verified-candidates.jsonl) | 980 remaining source-verified image candidates |
| [deferred-candidates.jsonl](deferred-candidates.jsonl) | 247 deferrals and seven concurrent changes |
| [all-decisions.jsonl](all-decisions.jsonl) | One result per reviewed artwork UUID |
| [final-catalogue-audit.json](final-catalogue-audit.json) | Read-only final image/status check and country relationship evidence |
| [selection.sql](selection.sql), [selection.json](selection.json) | Fixed main cohort and selection logic |
| [exclusions.json](exclusions.json) | Previous campaign inventory and excluded identifiers |
| [icon-file-details.json](icon-file-details.json), [greek-followup-files.json](greek-followup-files.json) | File-level rights, revisions and discovery evidence |
| [preview-receipts.json](preview-receipts.json) | Small selected preview sample; original bytes unchanged |
| [source-register.json](source-register.json), [evidence-manifest.json](evidence-manifest.json) | Source register and evidence integrity inventory |

`objects/` contains scoped museum records. `captures/` contains request receipts and preserved responses, including unsuccessful requests. Large pre-existing official snapshots remain at the paths recorded in their provenance receipts; they were not duplicated into this report directory. The read-only research script is preserved for reproducibility, not as an unattended image-import job.

## Sources

All online sources below were consulted on 13–14 September 2026. Individual captured retrieval times and checksums are retained in the evidence files. Undated policy pages are identified by title rather than assigned an invented publication date.

[^1]: Finnish National Gallery, [Photographic service](https://kansallisgalleria.fi/en/photographic-service/); [collection API documentation](https://kokoelma.kansallisgalleria.fi/api/swagger/). Object snapshot: `content/imports/expanded-round2-20260913/fng-objects.json`, retrieved 13 September 2026; SHA-256 recorded in its `.snapshot.json` receipt.
[^2]: Minneapolis Institute of Art, [Copyright and Image Access and Use](https://new.artsmia.org/copyright-and-image-access); [official collection repository](https://github.com/artsmia/collection), snapshot commit `790eb625934680f2eeccb262391618d2ca948486`.
[^3]: Minneapolis Institute of Art, [collection search infrastructure and API endpoints](https://github.com/artsmia/collection-elasticsearch); current exact-object responses are preserved in `mia-live-records.json`.
[^4]: Smithsonian Institution, [Open Access FAQ](https://www.si.edu/openaccess/faq). Selected SAAM media records came from the official Smithsonian Open Access metadata distribution, with source URLs and hashes retained per shard.
[^5]: Walters Art Museum, [Open Data](https://api.thewalters.org/index.html); [Image Rights, Reproduction, and Terms of Use](https://thewalters.org/about/policies/rights-reproductions/); [official static data repository](https://github.com/WaltersArtMuseum/api-thewalters-org), commit `f7531ed751ac2c138eeb6f923a3b4fd325d78adf`.
[^6]: SMK, [Collection API](https://api.smk.dk/api/v1/art?object_number=KKS11258), representative exact-object request. All 200 selected responses and request URLs are preserved in `captures/` and `objects/smk/`.
[^7]: Byzantine and Christian Museum, [Terms of Use](https://www.ebyzantinemuseum.gr/?i=bxm.en.terms). The National Gallery’s separate [page labelled Terms of Use](https://www.nationalgallery.gr/en/terms-of-use/) mainly supplies a privacy policy; it was not treated as an open-image licence.
[^8]: Byzantine and Christian Museum, [The Raising of Lazarus, ΒΧΜ 00980](https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=233); George E. Koronaios, [independent photograph and CC BY-SA 4.0 statement](https://commons.wikimedia.org/wiki/File:The_Raising_of_Lazarus_(Byzantine_and_Christian_Museum_of_Athens,_1-15-2023).jpg).
[^9]: Byzantine and Christian Museum, [The Apostles Peter and Paul, ΒΧΜ 00999](https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=234); George E. Koronaios, [independent photograph and CC BY-SA 4.0 statement](https://commons.wikimedia.org/wiki/File:The_Apostles_Peter_and_Paul_(Byantine_and_Christian_Musuem_of_Athens,_1-15-2023).jpg).
[^10]: Byzantine and Christian Museum, [The Hospitality of Abraham, ΒΧΜ 01544](https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=43); George E. Koronaios, [independent photograph and CC BY-SA 4.0 statement](https://commons.wikimedia.org/wiki/File:The_Hospitality_of_Abraham_(Byzantine_and_Christian_Museum_of_Athens,_1-15-2023).jpg).
[^11]: National Gallery – Alexandros Soutsos Museum, [Collecting the Nets, Π.10380](https://www.nationalgallery.gr/en/artwork/collecting-the-nets/); [Commons file and separate photographic licence](https://commons.wikimedia.org/wiki/File:Κωνσταντίνος_Βολανάκης_-_Συλλέγοντας_τα_δίχτυα.jpg).
[^12]: National Gallery – Alexandros Soutsos Museum, [Children’s Concert, Π.475](https://www.nationalgallery.gr/en/artwork/childrens-concert/); [Commons 1894-labelled file](https://commons.wikimedia.org/wiki/File:Children%27s_Concert_by_George_Iakovidis.jpg); [Commons file describing an 1884–1890 painting](https://commons.wikimedia.org/wiki/File:George_Iakovidis_-_Children%27s_Concert.JPG).
