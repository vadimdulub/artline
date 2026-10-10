# Current SMK open-image metadata — 6 October 2026

A fresh read-only metadata audit captured 39,508 SMK open-image search results, ten more than the earlier 39,498-result snapshot. The [official API documentation](https://api.smk.dk/api/v1/docs/) permits selecting output fields and pages of up to 2,000 records. Twenty bounded requests captured only object numbers, public-domain flags and modification timestamps, with stable total counts, duplicate-inventory detection and checksum receipts. No artwork images were downloaded by this audit and no database records were changed.

Comparison against 8,715 eligible local missing-image identifier rows found three leads. Daumier's KKS1959-54 was already reviewed and its image endpoints returned 404; that historical finding remains in [its operation report](../local-smk-native-image-20261006/README.md). Lundstrøm's KMS9205 and Vige's KKS14704 received separate, current full-object identity and rights reviews and [image attachments](../local-smk-current-images-20261006/README.md).

The 39,508 metadata results and 8,715 local identifier rows are discovery counts, not individual artwork-review counts. Only the two new full-object reviews add to the combined distinct review total. The native index is a point-in-time finding, not a guarantee about future source availability.

- [Complete paging receipts and matched local leads](capture.json)
- [Captured official API schema](swagger-ui-init.js)
- [Read-only audit script](../../../ops/audit-local-smk-current-metadata-20261006.py)
