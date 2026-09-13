# Retired Met ID image recovery — 13 September 2026

Three existing works that returned HTTP 404 from the Met API were recovered
using museum-donated files retained by Wikimedia Commons:

| Existing Met ID | Artwork | Derivative bytes |
| --- | --- | ---: |
| 339404 | Tiepolo, Standing Man in a Turban, Holding a Sword | 97,625 |
| 339403 | Tiepolo, The Holy Family | 91,726 |
| 337105 | Fragonard, A Gathering at Wood’s Edge | 93,300 |

Each current Commons file response declares CC0 for the image. Its saved
wikitext includes original museum XML with the exact old object ID and
collection URL. The importer checks that identity, title, artist, donated
image filename, original public-domain flag, empty rights-conflict field, and
creation range ending before 1971. It also rejects current file restrictions
or a non-CC0 licence. This is image-level evidence; the general Commons
metadata licence is not used as permission.

Source files:

- [Standing Man](https://commons.wikimedia.org/wiki/File:Standing_Man_in_a_Turban,_Holding_a_Sword_MET_DP811975.jpg)
- [The Holy Family](https://commons.wikimedia.org/wiki/File:The_Holy_Family_MET_DP811972.jpg)
- [A Gathering at Wood’s Edge](https://commons.wikimedia.org/wiki/File:A_Gathering_at_Wood%27s_Edge_MET_DT628.jpg)

The original file SHA-1 must match the Commons image API before compression.
The shared importer then creates the <=100,000-byte full-frame derivative,
saves it locally, uploads it with GCS create-only/checksum checks, and attaches
it using the existing museum identifiers in both databases. No identifier,
painter, date, holding claim, or publication status is changed. Images and
attribution identify the Metropolitan Museum via Wikimedia Commons.

This supplement deliberately overlaps three **failed** IDs in the original
manifest. Those old HTTP 404 events remain in the historical campaign log;
they must not be counted as unresolved image gaps after this recovery. The
active Met worker has already passed those IDs and is processing a disjoint
painting batch. Only the Commons source is requested by this recovery worker.

`verification-final.json` independently verified all **3 images**, totaling
**282,651 bytes**, maximum **97,625 bytes**, against local files, GCS, database
metadata, rights evidence, and exact artwork links. Both databases passed
with no errors. All three images were visually inspected and show the
expected drawings with full-frame proportions. The file records preserve
historical donated museum dates; the report does not count those as fresh
Met API date checks. Thirteen offline tests pass across the shared importer
and this recovery adapter, including wrong-identity, date, and rights gates.

Reproduce or resume only after confirming no other recovery process is live:

```sh
/tmp/artline-images-venv/bin/python ops/recover-met-commons-images.py \
  --after docs/research/image-expansion-20260912 \
  --run docs/research/image-expansion-20260912-commons
```

The saved Commons API responses, response hashes/URLs, file revisions, source
rights snapshots, derivative receipts and events are retained in this folder.
