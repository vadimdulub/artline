# Popular painters’ painting images — 17 September 2026, round 4

**7 additional licensed images for 6 popular painters** were attached to local and production, uploaded to Google Storage and verified through the public application. Every artwork remains in review.

## Current coverage

| Database | Popular painters’ paintings | With usable images | Still missing | Coverage |
|---|---:|---:|---:|---:|
| Local | 5,241 | 2,292 | 2,949 | 43.73% |
| Production | 5,241 | 2,292 | 2,949 | 43.73% |

The fresh baseline at the start of this round was **2,285** pictured paintings in each database; this round increased that by exactly seven. Nine additional pictured records were already present compared with the preceding round’s report, and are not counted as this round’s additions.

The date-eligible, supported subset now has **2,178 of 4,157** paintings pictured, with **1,979** gaps remaining.

## Delivered images

| Painter | New images |
|---|---:|
| Anthony van Dyck | 1 |
| Honoré Daumier | 1 |
| Jean-François Millet | 1 |
| Paul Cézanne | 1 |
| Peter Paul Rubens | 2 |
| Pierre-Auguste Renoir | 1 |

The additions include Rubens’s *Miracle of Saint Ignatius of Loyola* and *The miracles of St. Francis Xavier, Modello*; van Dyck’s portrait of Filippo Francesco d’Este with his dog; Millet’s *Le repos des faneurs*; Daumier’s *Les voleurs et l’âne*; Cézanne’s *Rochers près des grottes au-dessus du Château-Noir*; and Renoir’s *Portrait de Joseph le Coeur*. Four are held in French museums and three in Vienna’s Kunsthistorisches Museum.

## Research and corrections

- **105 distinct existing paintings** received selected research, with **136 source-route attempts** including retries. Seven received approved images; 98 did not receive a new image in this round.
- Seventy-three French national catalogue paintings received alternate photograph searches using exact existing Joconde identifiers. An additional 25 paintings received new full-text and alternative-title searches.
- The alternate-photo workflow had incorrectly required a single Wikidata main image before searching. This dependency was removed from alternate discovery and subsequent attachment/audit checks. Exact artwork identity, museum, creator, dates and file rights still remain mandatory. Twenty-three selected records were researched through this corrected path.
- Twenty-five cached mixed-licence leads were examined separately; none passed the preliminary original-photo/rights checks, so no images were downloaded for that group.
- Three prepared files were held before any database attachment or cloud upload: a Courbet photograph with conflicting historical licensing, a retouched van Dyck copy and a Rubens detail whose upload history also required rights review. Their bytes and receipts were moved into the designated backup directory.
- A different, original van Dyck photograph passed the exact-file checks and was delivered. Separate attempts for Courbet and the full Rubens painting did not establish a suitable photograph. The Rubens modello remains a separate physical artwork.
- Two inherited image holds were resolved only for different independently verified photographs. Old rejected source files remain rejected.

## Source interruptions and safeguards

Wikidata reported replication lag. The workers respected cooldowns. Research continued where an intact public artwork-metadata response less than 48 hours old was available; the original source URL, timestamp and checksum are retained. This fallback validates the extraction against the complete original response and is limited to artwork metadata. Commons file identity and photographic rights use their own exact-file evidence. Eleven records without a sufficiently recent capture subsequently completed a fresh API retry.

The original-photograph checks now distinguish a named photographer and an explicit own-photograph statement from a transferring or retouching account. Previously rejected filenames are carried into subsequent selected rounds. Missing, conflicting or noncommercial image rights remain held. Every delivered image carries CC BY or CC BY-SA terms with its exact version, source, photographer credit and attribution. See [Wikimedia’s reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia).

## Verification

- All seven source/file checks and database associations passed independently in each target.
- All seven Google Storage objects passed checksum, size and provenance checks.
- All 14 anonymous image and museum-artwork API requests passed.
- All seven artwork, creator-link and identifier preimages were checked in both targets. Only the image association and revision audit fields changed; review status and artwork metadata were preserved.
- No new approved rendition hash was shared with another artwork’s primary image in either database. No artwork was merged or removed.
- Sixty-four popular-image synthetic tests and 67 Commons regression tests passed. The suites overlap; their counts should not be added as unique tests. No test database or real-catalogue test fixtures were created.

Only selected, cleared images were downloaded. Existing image fields and writers were reused. Proportional resizing and JPEG compression preserve the full source photograph within the existing 100 KB display limit. Some visitor photographs retain frames or reflections.

## Evidence

- [Approved image manifest](approved-image-manifest.jsonl): artworks, source URLs, exact licences, photographer credits, source timestamps, file revisions and public image URLs.
- [Aggregate report](final-aggregate-report.json) and [coverage snapshot](coverage-both-final.json).
- [Local audit](local-final-audit.json), [production/storage audit](production-final-audit.json), [public checks](public-all-images-final.json), [preimage/duplicate audit](final-preimage-and-duplicate-audit.json) and [artifact scan](artifact-safety-scan-final.json).
- [Held prepared files](newly-rejected-commons-files.json) and [verified different-source replacements](verified-source-replacements.json).

Backups remain under the designated Artline Application Support directory. This round required no schema migration, deployment, publication or commit.
