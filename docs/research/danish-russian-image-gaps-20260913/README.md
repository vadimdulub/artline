# Danish and Russian artwork image gaps — 13 September 2026

Completed bounded pass; verified at **18:17:50 UTC**. **893 new image gaps** were
filled in both databases: **840 Danish and 53 Russian**. Another **12 Danish
images already present locally were restored in production**, making 905
verified associations across the two environments. All prepared files are
attached successfully; no prepared image remains pending application.

| Image source | New local attachments | New production attachments |
| --- | ---: | ---: |
| Selected SMK public-domain images | 831 | 831 |
| Wikimedia Commons | 62 | 62 |
| Existing local images synchronized | 0 | 12 |
| **Total** | **893** | **905** |

The new images cover **53 existing painter profiles** and **61 paintings,
719 drawings and 113 prints**. The Commons subset includes eight Danish
paintings, one Krøyer drawing and 53 Russian paintings. Examples include
Repin's *Reply of the Zaporozhian Cossacks*, *Sadko* and *Ceremonial Sitting of
the State Council*, Kuindzhi's *Moonlit Night on the Dnieper*, and works by
Hammershøi, Anna Ancher, Jørgen Roed and Janus la Cour.

**174 reviewed Russian Commons candidates remain undownloaded.** The image
provider returned HTTP 429 with Retry-After 600 on three passes, at 17:32:53,
18:03:49 and 18:16:34 UTC. Both earlier intervals were honored before resuming;
the final pass stopped on the third pause. Nothing is still running in the
background. The pending list, exact URLs, rights evidence and safe resume
commands are preserved. This is not a claim that all catalogue gaps are fixed.

`final-verification.json` checks all 905 associations, all local image files
and cloud copies, required source and credit evidence, unchanged artwork
metadata and representative local/production delivery. It records **zero
verification errors**, 82,429,050 total bytes and a maximum derivative size of
99,990 bytes. Both databases contain the 236 Commons candidate citations.

Within the fixed, broadly associated pre-pass audit cohort, both environments
now have 3,120 Danish-associated and 253 Russian-associated works with images.
Eligible gaps remain 8,708 and 6,947 respectively. These broad-cohort figures
include pre-existing geographic associations; the new attachment counts above
exclude the identified nationality mismatches.

The owner authorized resolving Wikipedia/Commons image gaps and applying the
results to both the real local and production databases. This pass enriches
existing artwork records; it does not publish them or alter dates, titles,
creator attribution, museum holdings or current-display claims.

## Evidence and selection

`local-before.json` and `production-before.json` preserve read-only audits of
the existing Danish/Russian artist associations and the two preceding museum
imports. The broad audit also includes geographic country associations; these
alone are insufficient evidence of an artist's nationality. Six image
candidates by German Lovis Corinth and French Jean Béraud are explicitly
excluded in `nationality-exclusions.json`. Existing country data is preserved.

Wikidata discovery was scoped to 536 existing creator authority IDs, in batches
of 20, with at most 3,000 result rows per batch. One group of 20 creators timed
out after 90 seconds and was deferred. Captures, request URLs, retrieval dates,
response hashes, pauses and the deferred group are retained. The discovery
does not authorize an exhaustive image download.

The image selection combines:

- Previously verified Russian Museum–Wikidata–Commons identity chains, checked
  against detailed museum accession, object title and creator authority.
- 110 additional exact matches from the bounded discovery. A match requires an
  existing artwork QID, or the same creator and museum accession, or a unique
  exact multilingual title with matching creator, date and museum collection.
  Commons file identity is checked independently before reuse.
- 831 additional dated SMK images from the pinned Danish import, each with an
  exact museum object number, `public_domain=true`, and Public Domain Mark.
- 12 already verified local SMK images missing in production. Their original
  bytes and media IDs are preserved; no additional download is needed.

`wikipedia-image-confirmation.json` checks 27 linked Wikipedia articles and
confirms seven exact P18 files in their returned image lists. Absence from that
list is not treated as a negative artwork identity decision. Wikipedia itself
does not establish the reuse license: individual Commons file rights do.

235 Commons files passed the initial rights/identity checks; six geographic
scope mismatches were then excluded. An independently licensed photograph of
*Moonlit Night on the Dnieper* was added separately. Its Commons description
and category identify the creator, title, 1880 date, Russian Museum and
accession Ж-4191. The photograph is self-published by Adavyd under CC BY-SA 4.0;
the initial museum-sourced P18 file remains deferred. The final bounded
selection was **1,073 artwork image associations**, including the 12 existing
local images to synchronize. A subsequent bounded search of 46 remaining
older Danish painting accessions selected six further Commons reproductions,
bringing the pinned total to **1,079 associations**. This second search requires
the exact accession in a Commons-cited official SMK source URL and an exact
creator label. A misleading KMS455/KMSst455 substring hit is excluded.

All **236** rights-reviewed, in-scope Commons candidates are recorded as
`image_candidate` citations in each database, under source
`danish-russian-commons-gap-research`. Candidate evidence does not claim that a
file has downloaded successfully or that the artwork is published.

19 initial Commons files were deferred for source-permission conflicts,
insufficient independent file identity or a detail reproduction. The alternate
Moonlit Night photograph resolves one of those work gaps without using its
deferred file. Unknown or cutoff-crossing creation dates are not made eligible.

## Storage, rights and application

The importer records image source pages, licenses, source file metadata,
photographer credits, transformation descriptions and checksums. Commons
thumbnails come directly from the Imageinfo API; an original-file SHA1 is not
applied to a resized thumbnail. Derivatives preserve the selected source frame
and are JPEG-compressed to at most 100,000 bytes.

New derivatives are under `apps/web/public/assets/artworks/open-museums/` in
`dk-smk-gap/` and `dk-ru-commons/`. Cloud uploads are conditional and checked by
size and MD5. Database attachments resolve exact source identifiers, preserve
existing images, and record per-file rights evidence. Prepared files,
application receipts and provider pauses are separate so that interrupted
downloads can resume without repeating successful attachments.

Commons' explicit 600-second Retry-After is honored across both Wikimedia
image hosts. No query-string changes, alternate endpoints or proxy routing
are used to evade an image-provider pause. Independent SMK work can continue.
The image request interval was increased from five to eight seconds after
the first pause. Isolated connection timeouts remain individually retryable;
successful files are never downloaded again.

## Recovery and verification

`backups.json` records the verified local PostgreSQL archive and successful
Cloud SQL backup **1789320267521**, both preceding this pass's database writes.
Recovery files are under:

`~/Library/Application Support/Artline/backups/danish-russian-image-gaps-20260913/`

The read-only verifier compares selected source identities, unchanged artwork
metadata and creator links, attached media, rights evidence, all prepared
derivative checksums and dimensions, cloud object checksums, and representative
local/production API and image responses. Cohort coverage uses the fixed
pre-pass artwork IDs to avoid crediting unrelated concurrent catalogue work.
The existing indexed source-ID lookup is inspected with EXPLAIN ANALYZE; no
backend pagination or filtering implementation is changed by this image pass.

## Commands

Run with the existing environment `/tmp/artline-images-venv/bin/python`:

```sh
python ops/apply-danish-russian-gap-images.py prepare --provider dk-smk-gap
python ops/apply-danish-russian-gap-images.py prepare --provider dk-ru-commons
python ops/apply-danish-russian-gap-images.py apply --provider dk-smk-gap
python ops/apply-danish-russian-gap-images.py apply --provider dk-ru-commons
python ops/apply-danish-russian-gap-images.py apply --provider dk-local-sync
python ops/verify-danish-russian-gap-images.py --label UNIQUE_RECEIPT_LABEL
```

Resume commands reuse pinned selections and prepared files. Do not re-create
the immutable before-audit or selection files after database application.

Primary source interfaces: [SMK collection](https://open.smk.dk/),
[Wikimedia Imageinfo API](https://www.mediawiki.org/wiki/API:Imageinfo),
[Commons licensing](https://commons.wikimedia.org/wiki/Commons:Licensing), and
the individual museum, Wikipedia, Wikidata and Commons links preserved in
each selection receipt.

## Observed source-image condition

Six derivatives were visually sampled in addition to all-file automated
verification. The Kuindzhi alternative is a licensed gallery photograph with
the physical frame and surrounding gallery retained, not a flat scan. The
selected N.P. Mols museum reproduction visibly contains conservation patches;
they are present in the source and were not digitally removed. These source
conditions are recorded in the visual-review receipts. Every enriched artwork
retains its previous review/publication state.
