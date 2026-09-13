# Retired Met painting ID — selected recovery

Sisley’s *The Seine at Bougival* is an existing artwork with old Met ID
437681 and accession **1992.103.4**. The museum’s current API ID **901617**
returns that same accession, title, artist, and 1876 date, with explicit
public-domain status, no rights-conflict text, and a primary image URL.

`identity-reconciliation.json` records the read-only local identity check.
The current museum API response and its URL/hash capture are in `metadata/`.
The [current museum page](https://www.metmuseum.org/art/collection/search/901617)
also identifies the accession and marks the image Public Domain.

**Pending:** download, compress, upload and attach this one selected image
after the active Met painting worker finishes. The existing artwork and its
old external identifier must be retained; the image evidence should document
the exact accession-based match to the museum’s current API ID. Recheck the
existing local/cloud identities and primary-image guards before attachment.
This folder currently contains metadata evidence only.

## Queued application

The exact accession/title/eligibility checks passed in both local and cloud
databases. `attachment-selection.json` records their actual artwork IDs and
empty primary-image slots. A frozen one-image `candidates.json` and rights
snapshot in `selected/met/` are now ready. The current API’s object ID is
retained separately in `current_museum_object_id`; the attachment key remains
the existing museum identifier 437681.

A waiting coordinator was started against the confirmed live main coordinator
PID 54051. It waits for all Met IDs in the painting supplement to reach
terminal outcomes before starting this single image, preserving the source
request gap. It does not treat an observation timeout as completion.

```sh
caffeinate -i /tmp/artline-images-venv/bin/python ops/continue-painting-images.py \
  --after docs/research/image-expansion-20260912-paintings \
  --run docs/research/image-expansion-20260912-retired-met \
  --predecessor-pid 54051
```

Do not launch another copy while this coordinator is live. Image upload and
final verification are still pending.

## Coordinator ended; local file prepared

The waiting coordinator ended after its predecessor exited with unattempted
Met painting IDs. It did not start the Sisley download. On 13 September,
a local-only preparation pass completed the remaining Met metadata checks;
all selected Met IDs now have an outcome. After that source worker finished,
Sisley was downloaded and compressed with `--prepare-only`, using the saved
exact-accession rights selection. Its file is **prepared**, not uploaded or
attached. Application and cloud verification remain pending reauthentication.

## Completed and verified

After Google Cloud authentication was restored, the saved **99,174-byte**
Sisley derivative was uploaded and attached in both databases.
`verification-final.json` passed all local/GCS checks and both database
metadata, rights and exact artwork-link checks, including the fresh 1876
museum date. The image was visually inspected. This one-artwork recovery is
complete; the original external identifier remains unchanged.

`verification-accession-match.json` additionally rechecked the actual current
accession and media link in both databases against the fresh museum API
record. Both still match **1992.103.4**, with the old external identifier
retained. `verification-live-assets.json` confirms that the production web
URLs for both Sisley and the recovered Romney painting return HTTP 200 and
the exact saved hashes/sizes.
