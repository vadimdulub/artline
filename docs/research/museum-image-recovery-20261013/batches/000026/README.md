# Museum image recovery — iteration 26

Checked 10 previously unchecked existing Cleveland museum-held artworks without primary images. Official museum pages and supported API records returned HTTP 200 and agreed on native ID, accession and title for all ten. All 250 previous campaign IDs were excluded. The campaign now has 260 distinct checked IDs; this does not complete the 1,000-iteration programme.

Two authentic museum CC0 images were attached and independently verified:

- Guan-Shaped Vessel with Floral Scroll, accession 2022.227 / native 447790 / internal 0b8ed2ba-b5e0-59e8-b649-9d85bd01f6f9. Complete primary viewpoint, 88,484-byte derivative. The underside mark and storage box are not shown.
- Various Ships and Views of Amsterdam, Part II: Launching a Ship, accession 1944.27.12 / native 123745 / internal 0ba289fd-b6b2-53c6-9b8e-70f9a0318c90. Full composition and caption retained, 99,917-byte derivative. Artist Reinier Nooms and publisher Clement de Jonghe remain distinct roles. Source state, edition and dimensions remain unspecified.

Both originals and both final derivatives were actually viewed. Originals are archived under Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000026. Museum filesize metadata differs from actual downloaded bytes; actual bytes, hashes and matching dimensions are recorded. Nooms's museum creator display and structured death year conflict; the capture preserves both and no creator metadata was changed.

Eight records remain imageless on rights holds. Their museum pages supply images labelled Copyrighted, without an established reusable image licence. No museum-page unavailable or no-image-at-source outcome occurred in this iteration. Page structured metadata, primary/alternate image routes and IIIF presence were inspected; no access restriction or Retry-After was encountered and no search API was used.

Batch107's completed recovery checkpoint, its pinned evidence, all prior campaign completion pins and the preceding delivery were confirmed before selection. Production proxy target and active transactions were inspected. The transaction used the shared artline-curated-ingestion advisory lock, locked target rows, captured exact preimages and rechecked NULL primary IDs. Independent read-only database/audit verification confirms two attributable null-to-primary changes; metadata, creators, holdings, editorial status and the other eight records are unchanged. Both storage objects were independently downloaded and checksum-verified. Public image GETs returned HTTP 200 with matching bytes and decoded dimensions, and artwork API responses reference the internal image paths.

Exact row backups and checksum-pinned plans are under Application Support/Artline/backups/museum-image-recovery-20261013/batches/000026. These are affected-row recovery snapshots, not a full database backup; no Cloud SQL backup was created. The real local catalogue was not connected to or changed. Existing programmes and supervisor were not modified. No workers, deployment, infrastructure changes, deletion, commits or pushes occurred.

Continue after Cleveland cursor 0bbbbe60-4748-5bc1-9878-639fcf4d61ed or switch museums. Exclude all 260 campaign checked IDs and preserve all source holds recorded by the linked prior queue receipts.

Evidence: checked-artworks.json, source-queue.json, prerequisites.json, required-inputs.json, visual-review.json, delivery-plan.json, plan-pin.json, transaction-preimages.json, transaction-postimage.json, independent-verification.json and completion-pin.json.
