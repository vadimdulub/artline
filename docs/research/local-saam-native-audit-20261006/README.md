# Smithsonian American Art Museum native audit — 6 October 2026

**Fourteen existing missing-image paintings were reviewed; no image was attached.** Exact native IDs were first located in the prior public Smithsonian metadata export. All fourteen relevant metadata shards had changed ETags, so only those fourteen shards were refreshed from their documented public export URLs. Each current object remains uniquely identifiable by its existing native ID and matches the catalogue's inventory, title, creator, type and creation facts under the source validator.

All fourteen current object records omit image resources entirely. The older validator's shared “multiple or absent” result is resolved here as zero media entries in every current native record. These are current source-specific availability findings, not claims that no independently licensed photograph exists elsewhere. No image bytes were downloaded and no database records were written. A final read-only comparison confirmed all fourteen catalogue records remained unchanged.

The reviewed artists include Charles Peale Polk, Ezra Winter, Mabel Hooper La Farge, Cass Gilbert, George Elbert Burr, Douglas Volk, Hermann Stieffel, Peter Baumgras, Henry Inman, Lucien W. Powell and Elliott Daingerfield. Current full object evidence is retained under `objects/`; only the relevant metadata shards and checksum receipts were saved under `metadata/`.

- [Prior exact-source discovery](prior-source-discovery.json)
- [Current shard response headers](current-shard-heads.json)
- [Current individual findings and source receipts](current-findings.json)
- [Catalogue snapshots](candidates.json)
- [Counts and unchanged-record verification](report.json)
- [Combined recovery report](../local-image-recovery-20261006/README.md)
