# Seven bounded image research rounds — 13 September 2026

The user requested five to seven further rounds, proceeding to the next round
after each finishes. This campaign plans seven disjoint selections of 200
existing artworks each. It does not enumerate or download entire collections.
Only selected, explicitly reusable reproductions are downloaded.

| Round | Museum | Scope | Selection ceiling |
| --- | --- | --- | ---: |
| 1 | Cleveland Museum of Art | Drawings | 200 |
| 2 | Metropolitan Museum of Art | Drawings | 200 |
| 3 | National Gallery of Art | Drawings | 200 |
| 4 | Art Institute of Chicago | Drawings | 200 |
| 5 | Cleveland Museum of Art | Prints | 200 |
| 6 | Metropolitan Museum of Art | Prints | 200 |
| 7 | National Gallery of Art | Prints | 200 |

Each round starts from an SQL selection of existing artworks missing an image,
with eligible creation dates and recorded museum/selection evidence. Previously
selected artworks from earlier image campaigns and preceding rounds are
excluded, including earlier rights/availability skips. Ordering prioritizes
recorded Russian/Greek creators, then existing popular-creator selections.
Anonymous or unresolved creator records are not categorically excluded.

The separate Russian/Greek/Byzantine priority audit also found missing-image
records under Finnish, Greek, French and other source schemes. Those schemes
need additional exact-object image adapters and per-file rights research;
existing documented restrictions on Athens/Kremlin photographs remain in force.
Their absence from these four museum adapters does not establish ineligibility
or permission to replace their images with generic icons.

The [focused icon review](priority-icon/README.md) subsequently added an exact
Athens Archangel Michael image from an independent CC BY-SA 4.0 photographer.
That one additional priority image has its own source evidence and complete
local/cloud verification, separate from the seven 200-work museum selections.

Fresh source checks use the museums' official open-data resources and explicit
per-image flags. Policies reviewed during this pass:

- [Cleveland open access](https://www.clevelandart.org/open-access): use the object's CC0 designation, not the availability of metadata alone.
- [Met open access](https://www.metmuseum.org/hubs/open-access): exact museum object identity, public-domain flag and an available image without a conflicting rights notice.
- [NGA free images](https://www.nga.gov/artworks/free-images-and-open-access): pinned published-image index with open-access primary-view flags.
- [Chicago open-access images](https://www.artic.edu/open-access/open-access-images): exact object/image IDs, explicit public-domain flag and no conflicting copyright notice.

Rights evidence is saved before downloading. For Cleveland, the Met and Chicago,
current museum date endpoints must also be known and no later than 1970; a
contradiction is retained for editorial review. No catalogue dates are changed.

The existing image pipeline saves full-frame JPEGs at most 100,000 bytes locally,
uploads create-only Google Storage objects, verifies their MD5 and size, and
attaches media through exact museum identifiers in both databases. The writer
changes only primary media and revision/update audit fields. Each round compares
all other artwork fields and creator links with its original local/cloud
snapshots and verifies every saved image, cloud object, media row and rights row.

The next round starts only after those checks pass. Museum HTTP 403/404 responses
are recorded as unavailable research results without alternate access routes.
A museum image read timeout gets at most one further bounded retry batch,
recorded before execution; an unresolved timeout is then retained as unavailable.
Cloud-upload/database failures cannot enter that source-timeout path.
Unfinished processing and unexpected errors stop the coordinator for inspection.
Every round retains candidates, metadata, selection evidence, image receipts,
events, verification results and a final `round-complete.json`.

New full backups were created before this campaign under
`/Users/vadimdulub/Library/Application Support/Artline/backups/image-research-seven-rounds-20260913/`.
The local archive is 345,958,111 bytes; Cloud SQL backup `1789301546300` completed
successfully at 12:13:57 UTC. `backups.json` records the local checksum and paths.

Reproducible/resumable command:

```sh
python ops/run-selected-image-rounds.py --root docs/research/image-research-seven-rounds-20260913 --rounds 7 --per-round 200
```

The fresh-date guard has offline tests in `ops/test_selected_image_rounds.py`.
No test database or real-catalogue fixtures are used. Existing indexed and bounded
query checks are not a substitute for the outstanding 10-million-row load tests.
