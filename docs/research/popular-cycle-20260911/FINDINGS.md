# All-popular cycle — 11 September 2026

[All 100 painter checklists](PAINTERS.md) · [Method and limitations](../../POPULAR_RESEARCH_CYCLE.md)

The first automated pass processed all **100 popular painters** and **22,232 existing artworks**. All 100 official Cleveland catalogue queries completed. Every painter retains a separate museum queue and every linked artwork has a machine-readable assessment, including records with unresolved dates or missing images. Zero-artwork painters are retained.

The source search found **54 existing CC0 image candidates** and **11 possible new artwork candidates**. Candidates are not imported automatically. A successful source search is not an exhaustive museum review: this pass searches the first 20 paintings per painter in one live catalogue, plus cached NGA image leads for existing objects. No painter's worldwide research is marked complete.

The frozen starting inventory has 383 popular-artwork pictures, 275 passing file/size/rights checks, 107 legacy files over 100 KB and one legacy rights-evidence issue. It is intentionally not rewritten after image attachment.

## Evidence

- [Official Cleveland API and filtering/licensing documentation](https://openaccess-api.clevelandart.org/).
- [Cleveland open-access policy](https://www.clevelandart.org/open-access); object-level CC0 status is checked independently.
- [Official NGA open-data repository](https://github.com/NationalGalleryOfArt/opendata); cached image leads are not treated as fresh clearance.
- Exact requests, timestamps, raw JSON and SHA-256 are retained under `captures/`; each painter's derived assessment preserves exact object notices.

## Image follow-up

A bounded subset selected one missing image per painter for 28 painters. Fresh object checks found one source/local date conflict: Corot's *Pond at Ville-d'Avray*, Cleveland object 124078, local 1860–1869 versus source 1865–1869. It remains unchanged and deferred. **The other 27 images were successfully attached**, each at 60,912–99,682 bytes. No images were substituted, no existing pictures overwritten, and no masterpiece labels added.

Current totals: **106,195 artworks and 608 pictures**, with **410 pictures** across popular painters. Monet has **298 works and 31 pictures**. [Updated complete inventory](../popular-artists-20260911/inventory-v6/PAINTERS.md).

Verification: all 100 source captures and 22,232 inventory records checked; 27 local file hashes/full decodes and 83 API checks passed; existing artwork metadata, artists, attributions, holdings, media and selections preserved. All Go tests and targeted vet passed. Replaying the unchanged cycle reused captures; attempting to replay after image attachment correctly rejected the stale database fingerprint.

Receipts are in `output/popular-cycle-images/`: `cycle-verification.json`, `before.json`, `after.json`, `api.json`, `inventory-verification.json`, and `apply.json`. Pre-apply database backup: `/Users/vadimdulub/Documents/artline-popular-cycle-backup-20260911.Aw17ht/before-images.dump`, SHA-256 `a58df0afb70507f7c1f292a7bff8560383d44b719e45f0540ee1077137fda2a0`.

Original 28-item selection and preview are retained for audit and superseded by `output/popular-cycle-images/selection-v2.json`. No masterpiece labels or new artworks are inferred from this selection.

[Previous detailed research findings](../popular-artists-20260911/FINDINGS.md) · [Previous Nationalmuseum follow-up](../popular-artists-20260911/NATIONALMUSEUM-FOLLOWUP.md)
