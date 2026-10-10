# SMK native image review — 6 October 2026

**One existing print was reviewed; no image was attached.** A read-only comparison of 8,715 eligible missing-image SMK records with the previously captured open-image metadata index identified this lead. Only the single current source review counts toward recovery totals.

The [current SMK record for KKS1959-54](https://api.smk.dk/api/v1/art?object_number=KKS1959-54) identifies Honoré Daumier's *Une partie de campagne pendant le joli mois de mai...*, a lithographic print dated 1856. Its exact object number, native maker ID `1394_person`, title and date match the existing artwork `b82537d1-57d7-5b4d-9b5e-7416dfab1532`. The current metadata marks the image public domain and contains two image records.

The primary and alternate IIIF image requests both returned HTTP 404. Both published thumbnail URLs also returned HTTP 404. These findings and current metadata receipts are retained in [image-endpoint-findings.json](image-endpoint-findings.json). No image bytes were archived, no application image was created and the artwork remained unchanged. A usable source image is still needed.

This review does not establish the current image availability of every other SMK gap: discovery used the earlier completed open-image index, and only this candidate's native record was refreshed.

- [Discovery and current source facts](discovery.json)
- [Operation report](report.json)
- [Combined recovery report](../local-image-recovery-20261006/README.md)
