# Additional Russian Museum artist leads — 7 October 2026

A read-only, artist-scoped audit found **322 eligible missing-image review records** across eight existing artist authorities. Checksum-verified Russian WikiArt indexes supplied **71 exact normalized-title leads**. These are metadata candidates, not validated artwork versions or attachment approvals. No images were downloaded and no database records were changed in discovery.

| Artist | Eligible image gaps | Title leads |
| --- | ---: | ---: |
| Arkhip Kuindzhi | 59 | 23 |
| Ilya Mashkov | 14 | 8 |
| Isaac Levitan | 32 | 12 |
| Ivan Aivazovsky | 41 | 7 |
| Ivan Shishkin | 29 | 12 |
| Mikhail Vrubel | 111 | 1 |
| Vasily Polenov | 7 | 3 |
| Vasily Surikov | 29 | 5 |

Artist IDs, stored Wikidata identifiers and existing life fields were frozen. Mashkov's catalogue birth and death years remain null. A missing artist life field does not justify inventing a biography; current creator crosswalks and source evidence must be checked during individual object review.

The [query plan](scoped-query-plan.json) starts with the eight artist IDs through `artwork_artists_artist_work_idx`, then uses primary-key lookups for artworks, artists and institutions and an indexed identifier lookup. It contains no global artwork CTE. This checks the plan on the real current catalogue, not representative performance at ten million artworks.

Repeated titles, different years, paintings versus studies, and printed impressions require individual decisions. The earlier six-artist discoveries and unresolved records remain separate; this audit does not replace their queue.

[Discovery and pinned source indexes](discovery.json) · [Complete scoped gap snapshot](eligible-gaps.json) · [Combined recovery](../local-image-recovery-20261006/README.md)

The [sixteen-record Kuindzhi and Mashkov review](../local-wikiart-kuindzhi-mashkov-images-20261007/README.md) attaches fourteen images and holds two different mountain versions. That checkpoint reviewed sixteen of the 71 leads. The initial 322-record gap snapshot is historical and is not a current missing-image count.

The [fifteen-record Kuindzhi version review](../local-wikiart-kuindzhi-versions-images-20261007/README.md) adds seven images and holds eight different versions. At that checkpoint, 31 of 71 leads had received individual review: 21 attached, ten unresolved and forty pending. All 23 Kuindzhi exact-title leads have been reviewed (thirteen attached, ten held), as have the eight Mashkov leads (all attached). The [record-level recovery progress](recovery-progress.json) preserves each outcome and the next pending source leads. Broader non-exact-title gaps remain open.

The [twelve-record Levitan review](../local-wikiart-levitan-images-20261007/README.md) adds seven images and holds five different compositions. At that checkpoint, 43 of 71 leads had received individual review: 28 attached, fifteen unresolved and 28 pending. All twelve Levitan exact-title leads have been reviewed; the print reproduction retains its individual-impression limitation. Current record-level outcomes are in [recovery progress](recovery-progress.json).

The [twelve-record Shishkin review](../local-wikiart-shishkin-images-20261007/README.md) adds four images and holds eight different compositions. At that checkpoint, 55 of 71 leads had received individual review: 32 attached, 23 unresolved and sixteen pending. All twelve Shishkin exact-title leads have received individual review. That left seven Aivazovsky, one Vrubel, three Polenov and five Surikov leads for the next review.

The [fifteen-record four-artist review](../local-wikiart-russian-four-artists-images-20261007/README.md) adds five images and holds ten different versions. At that checkpoint, 70 of 71 leads had received individual review: 37 attached, 33 unresolved and one pending. Polenov’s Abbey at Redon has only a Wikidata object identifier; its [initial authority discovery](../local-polenov-abbey-image-review-20261007/README.md) preceded the separate visual review. The [record-level queue](recovery-progress.json) retains every reviewed outcome. Broader non-exact-title gaps remain open.

The [Polenov Abbey image review](../local-wikiart-polenov-abbey-image-20261007/README.md) matches the source to the exact authority-linked Commons photograph and attaches one image. Across six operations, **all 71 leads have received individual review: 38 attached and 33 unresolved, with none pending**. The source circa 1875 date remains separate from catalogue/authority 1911; all metadata and review states are unchanged. This completes individual review of this exact-title discovery, while broader missing-image recovery remains open.

The discovery procedure and artist-selection evidence are archived under `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-russian-additional-artists-20261007/procedures/`.
