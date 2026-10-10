# NGA native open-image audit — 6 October 2026

Read-only screening joined 16,447 eligible local NGA artworks lacking a primary image to the museum's published-image metadata. The official CSV is preserved in `../museum-gaps-20261005/open-images-01/metadata/nga/nga-published-images.csv`. Its SHA-256 and immutable Git revision are retained in [discovery.json](discovery.json); a fresh upstream revision check matched that capture.

Thirteen open primary-image rows identify seven artworks. Six objects have two published primary images, so the image row alone is insufficient to choose a reproduction. Fresh native object pages identify the exact current public download for each inventory. These seven images were then individually reviewed and attached in the [NGA recovery](../local-nga-native-images-20261006/README.md).

The joined metadata also contains 13,608 primary and 73 alternate image rows marked `openaccess=0`. These counts describe image rows, not distinct artworks, and do not establish a general prohibition on independently sourced reproductions. No restricted image bytes were downloaded by this audit. The remaining objects still need other source or rights work.

Current source captures resolved an apparent conflict with an older indexed page saying that *Life on the East Side* had no download. The fresh page and current published-image record both provide its exact public image. [Page findings](page-findings.json) preserve all seven source captures and selected download IDs. The metadata screening count is separate from the combined report's count of individually reviewed artworks.
