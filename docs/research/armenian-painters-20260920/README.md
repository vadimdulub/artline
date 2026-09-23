# Armenian painters and selected artworks — 20 September 2026

Delivered to both the real local catalogue and live Artline collection.

[Open Armenian painters](https://artline-web-lpuqqlugnq-ew.a.run.app/?country=AM&popular=false) · [Full painter list](ARTISTS.md) · [Artworks and public images](ARTWORKS.md) · [Unresolved research and alternate images](REVIEW.md)

| Verified result | Local | Live |
| --- | ---: | ---: |
| New active artist profiles | 505 | 505 |
| Active Armenian-linked profiles after this pass | 559 | 559 |
| New artwork records | 1,027 | 1,027 |
| Existing museum-source records enriched | 37 | 37 |
| New image attachments | 134 | 134 |
| Total Armenian-linked artwork records | 1,485 | 1,485 |
| Total Armenian-linked artworks with images | 220 | 220 |

## Coverage

Surveyed 578 source identities: an uncapped Wikidata discovery of 567 Armenian-affiliated painter authorities, supplemented by WikiArt directory identities. All 48 profiles in [WikiArt’s Armenian nationality directory](https://www.wikiart.org/en/artists-by-nation/armenian) were reconciled. This is source coverage, not a claim that every Armenian painter in history has a complete catalogue.

The museum-source discovery captured 14,855 initial rows plus 61 supplemental rows. Selected at most eight further museum-connected records per painter and up to twelve further featured historical WikiArt works per matched profile. Existing earlier catalogue works and images were preserved.

Added 930 museum-source artwork records and 97 WikiArt artwork records. 362 new records have unknown creation dates and remain review metadata. Broad source object types, manuscripts and graphic works retain `unknown` catalogue types where mapping is unresolved. Source collection statements remain citations, not accepted holdings or on-view claims.

Eleven medieval source identities use documented activity centuries or decades. The timeline bounds describe those supplied periods; no birth or death years were invented. 18 further named source identities and one nonhuman list item remain in the research queue. Two possible duplicate artist-authority pairs are explicitly flagged.

## Images and public delivery

Uploaded 137 public image files: 99 selected WikiArt files, one alternate for an already represented artwork, and 37 Commons files. Attached 97 WikiArt and 37 Commons images to artwork records. Two public Kochar views remain unresolved as separate objects; their direct image links are in the review report.

All added image dates end by 1955. Every uploaded derivative is at most 100,000 bytes; the largest is 99,795 bytes. Public files were checked against their local SHA-256 digests. Original downloads remain separately archived. Actual source rights labels and credits are retained; 26 WikiArt files still carry the source’s restricted label.

## Identity and preservation checks

- Reconciled the Mher Abeghyan/Abeghian duplicate through its explicit WikiArt identifier; archived only the newly created empty duplicate profile, preserving the established artist and artwork records.
- Preserved the Marcos Grigorian 1924/1925 and Gregorio Sciltian 1900/1898 source birth-date disagreements as review citations without replacing existing dates. [MoMA’s Grigorian authority](https://www.moma.org/artists/2341-marcos-grigorian) and [Getty’s Sciltian authority](https://www.getty.edu/vow/ULANFullDisplay?find=&nation=&role=&subjectid=500104961) supplied identity cross-checks.
- Separated repeated titles when distinct museum accession numbers establish different source objects. Six provisional same-title matches were corrected with exact recovery records; existing artwork metadata and images were preserved.
- Linked three existing Hovsep Pushman records and three Sargis Pitsak records to reconciled named-creator profiles while preserving their original object-level labels.
- Kept all newly created artists and artworks in review. Added owner collection selections separately from museum designations. No deployment, commit, accepted holding or current-display claim was made.

## Verification and recovery

Final verification: `final-verification-1789909414.json` — zero errors. Includes exact database/receipt comparisons, authority and creator references, accession checks, review states, personal collection membership, backup hashes, public image checks and artwork API checks. The public Armenian timeline returned HTTP 200 with 556 profiles in its supported range and filters. Full source-profile count above also includes records outside the timeline’s range.

Whole-catalogue image-size metadata audits found zero oversized or unknown-size images in both databases (local 89,769; live 89,651). Existing WikiArt identity/date/compression tests: 20 passed in the project’s prepared Python environment. No fixture data or test database was created.

Exact per-target preimages, collection revisions, identity corrections and source originals:

- `/Users/vadimdulub/Library/Application Support/Artline/backups/armenian-painters-20260920/`
- `/Users/vadimdulub/Library/Application Support/Artline/source-images/armenian-painters-20260920/`
- Selected Commons originals: the backup directory’s `museum-images/selected-originals/` subdirectory.

Source captures, immutable selection evidence and individual transaction receipts remain alongside this report. The phase runner is `ops/armenian-painters-20260920.py`; final operation scripts are archived with their SHA-256 digests under the recovery directory. Earlier unsuccessful verification receipts remain preserved beside the successful final receipt.
