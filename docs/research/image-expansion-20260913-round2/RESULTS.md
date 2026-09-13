# Image expansion results — 13 September 2026

**400 additional artwork images** were saved locally, uploaded to Google Storage
and attached to the matching existing artworks in both databases.

| Source | Added images | Bytes |
| --- | ---: | ---: |
| Statens Museum for Kunst | 398 | 37,127,493 |
| Musée d'Orsay works via Wikimedia Commons | 2 | 131,322 |
| Total | **400** | **37,258,815** |

The largest image is **99,963 bytes**. All 400 files decode correctly; local
SHA-256, cloud MD5/size, exact artwork identity, media metadata and rights evidence
passed verification. A live-site asset request returned HTTP 200 with matching
bytes. Selected examples, including a painting's reverse side and both Monets,
were visually inspected.

Of 624 selected existing review artworks, 400 received images. The remaining
224 SMK records have no explicit public-domain permission (204) or no available
museum image (20). No source/download/attachment failures remain. A separate
Monet search lead was rejected for conflicting left/right identity metadata.

All artwork records remain in review. The image writer changes only primary
media and revision/update audit fields. Eight independent cloud-side creator
updates from the other import were identified and exactly reconciled with its
saved plan; every other non-media artwork field matched its original baseline.
No artworks, painters, accepted holdings or publication claims were created by
this image pass.

Verification evidence:

- [SMK final audit](verification-final.json)
- [Monet final audit](../image-expansion-20260913-joconde-commons/verification-final.json)
- [Skip reasons](source-outcomes.json)
- [Concurrent creator-update proof](verified-concurrent-creator-changes.json)
- [Live asset check](live-canary.json)
- [Workflow and reproducible commands](README.md)

Validation also included 22 offline unit tests across the image pipeline,
research identity guards and existing Commons recovery, plus six rejection
checks against copies of the captured Monet evidence. No test databases or
catalogue test fixtures were created. Large-scale load testing remains separate
from the indexed, bounded queries checked during this pass.
