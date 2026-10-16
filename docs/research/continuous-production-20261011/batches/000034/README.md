# Batch 34 — verified Carnavalet image

Delivered **one newly illustrated existing artwork**, with zero new painters,
artworks, alternate images or museum links. The 87,858-byte CC0 reproduction is
Amélie Burdin's *Portrait d'Alphonse Karr*, inventory P1515, Paris Musées object
320026898, reconciled to Joconde M1104320026898 and production artwork
0350edf0-95b3-424c-8bd5-f3111333aff5.

The live French reserve audit found all 188 objects already imported and
illustrated by the previous campaign. None was replayed or counted. Its original
plan remains unchanged. The previous six Warsaw additions were also reconciled
without counting them again.

The 25-row Carnavalet gap page yielded 24 checksum-verified archived Joconde
reference crosswalks. One native object and its unique CC0 canvas were verified
against title, creator, inventory, dimensions, production and acquisition dates.
The prepared image was actually viewed individually; its full canvas and
inscription are visible. The original was decoded and hash checked but was not
separately visually inspected. Unknown catalogue fields, the historical creator
lifespan label, review status and existing holding assertion were preserved.

The registry's older terms URL returned 404. Current footer terms were captured
successfully. Sections 1.3.1.a/1.4 permit this explicitly selected CC0 download;
sections 1.6/1.10 require a different established access route for broader
automated discovery. That discovery was stopped, including an in-flight second
object request. No GraphQL authentication was bypassed. One identity crosswalk
and 23 other native-image candidates remain unresolved or unresearched.

Production attribution is established by the locked null-primary preimage,
persisted selection/source/visual checksums, matching audit event and storage
operation. Independent checks verified source evidence, every file, storage
association, public image checksum and public artwork API response. All 24
unselected production records remained unchanged. An actual resumed delivery
made zero additional writes.

See `batch-verification-receipt.json`, `final-checkpoint-verification.json` and
`CHECKPOINT.json`. Source queue changes preserve the other 108 registry entries.
The next route is National Palace Museum Taiwan public open-data painting and
calligraphy gaps, with exact inventory and per-image rights checks.

Resume tools, using the established `/tmp/artline-cyprus-venv/bin/python`:

- `ops/continuous-paris-images-000034.py deliver` reconciles and resumes the
  existing pinned attachment; it does not generate another batch.
- `ops/continuous-paris-images-000034-verify.py` independently checks delivery.
- `ops/continuous-paris-000034-finalize.py` verifies idempotent resume and saves
  this bounded checkpoint.

Originals and transaction recovery preimages are outside Documents under the
corresponding `source-images/continuous-primary-images-20261011-b000034/` and
`backups/continuous-primary-images-20261011-b000034/` Application Support roots.
The real local catalogue was not connected to. No supervisor, schedule,
LaunchAgent, deployment, commit or infrastructure change was made.
