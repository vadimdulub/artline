# Native museum priority image audit — 6 October 2026

Checked 19 selected existing missing-image records linked to the Russian/Greek priority queue: thirteen Met objects, three Art Institute of Chicago objects and three Cleveland objects. The artists include Orłowski, Repin, Shishkin, Korovin, Bakst, Jawlensky and Kandinsky. Priority-queue membership is a discovery aid; no nationality or biography was rewritten.

All 19 native records matched their stored object ID and inventory, but none exposed an explicitly open primary image. Sixteen supplied no primary image; the three Chicago records supplied an image ID with copyright notices and `is_public_domain=false`. The Cleveland Kandinsky records specify copyrighted status, an ARS notice and no image. These API findings are retained individually in `events.jsonl` and checksum-pinned captures under `metadata/`.

No images were downloaded or attached. A final read-only comparison confirmed all 19 artwork records remained exactly unchanged, including their absent primary images. These are source-specific findings, not a declaration that no independent licensed photograph exists. Alternative sources remain future work.

- [Selected metadata and before-records](candidates.json)
- [Native source findings](events.jsonl)
- [Counts and unchanged-record verification](report.json)
