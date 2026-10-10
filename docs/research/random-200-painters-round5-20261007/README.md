# Fifth random 200-painter batch

Completed and verified in production on 7 October 2026: **8,916 new artwork review records and 6,462 images**, covering another 200 painters. The research also records **1,049 related-work leads**.

- [Complete production report](report.html)
- [Selected 200 painters](selected-200-painters.csv)
- [Per-painter outcomes](painters.csv)
- [New artwork records](new-review-records.csv)
- [Uploaded images and source rights](uploaded-images.csv)
- [Every indexed source disposition](source-dispositions.csv)
- [Related-work leads](related-artwork-leads.csv)
- [Final production verification](final-verification.json)
- [Report cross-check](report-verification.json)
- [Completion receipt](completion-receipt.json)

The frozen random cohort excludes Otto Dix and the 800 individual creators covered by the preceding four rounds. Seed: `46ac8ca771e308ebf56c912e205da6a7`. Selection used no popularity or artwork-count weighting. The source pass accounts for all 12,690 indexed entries and preserves available translated indexes and original retrieval evidence.

Every uploaded image passed decoding, dimensions, aspect-ratio, byte-budget and checksum checks. Each public URL returned the expected image bytes. Review covered 46 contact sheets, eight duplicate pairs and 164 source notes; it does not claim manual viewing of every image. Final verification checked production records, source identifiers, media rights evidence, review notes and every delivered image in the live, bounded painter gallery API.

All new artworks remain in review in the personal owner collection. Existing images, catalogue metadata, creator links, accepted holdings, current-display assertions and publication states were preserved. Concurrent changes by other workflows are recorded separately. Actual WikiArt rights labels remain distinct from user approval. Thirty-nine images were deferred for unresolved object/version/date questions while their named source records were retained in review. Unknown creation dates remain unknown and their images are deferred.

Related-work entries include named subjects, copies, collaborations, existing object-level creator labels and unresolved attribution leads. These are research leads, not automatically validated creator links. The source coverage is not a claim to every artwork or relationship worldwide.

The successful pre-import Cloud SQL backup is `1791368721734`. Originals and recovery snapshots are under the Artline Library data locations, outside Documents; served derivatives retain the full supplied composition and are at most 100,000 bytes. The local database was not modified. The operation's dedicated loopback proxy has been stopped.

A temporary authentication pause was resolved by the user's sign-in confirmation; [the resumption receipt](authentication-resumed.json) preserves that history. [The preflight](production-preflight.json), [source-review decisions](reviewed-source-discrepancies.json), [image holds](manual-image-holds.json) and [identity holds](manual-identity-holds.json) remain available. Current query plans do not establish performance at ten million artworks; large-scale load testing remains separate backend work.
