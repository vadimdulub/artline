# Local image recovery: production delivery — 8 October 2026

**All 1,214 recovered images are synchronized with production and verified.**
The user requested “push to prod”, restored Google Cloud authentication, and
then requested verification. Production delivery completed on 8 October 2026;
the final read-only database and live API checks passed at 10:06:18 UTC.

| Delivery result | Artworks |
| --- | ---: |
| New primary image | 1,024 |
| New alternate image, existing primary preserved | 44 |
| Identical existing image reused with recovery evidence added | 146 |
| Total verified | 1,214 |
| Held or pending delivery | 0 |

The operation created 1,068 image objects and media records and retained all 190
existing primary images. All 1,214 public image responses were checked against
the prepared JPEG SHA-256 checksums. Fresh database reads verified every media
record, rights record, attachment and artwork state; live artwork API checks
passed for samples from all 46 represented museums with a current institution.
Another 117 records have no current institution and are covered by the complete
database and public-image checks. All 1,214 image-identity citations are present.

All 1,214 application JPEGs and their archived originals were verified against
the live local database. The JPEGs total 100,412,640 bytes and each is at most
100,000 bytes. The package preserves 93 explicit view labels and all actual
rights: 632 CC0, 345 public domain, 99 CC BY, one CC BY-SA, one separately licensed
photograph and 136 restricted WikiArt images. User approval remains separate from
source rights and independent verification. No local catalogue data was changed.

All production objects were matched against explicit object identifiers,
titles, dates, types, institutions and creator roles. The reviewed creator
crosswalk reconciles 130 authorities for 258 artworks whose local and production
creator UUIDs differ, using exact names and shared native or Wikidata identifiers
without conflicting Wikidata identities. No creator records were rewritten.
The first identity-only preflight is preserved under `history/`.

The preparation checks passed 1,214 positive identity cases and eleven rejected
identity changes. The final transport checks passed another 1,235 controls:
1,214 production identities, three valid delivery states and eighteen rejected
altered states. These used in-memory copies; no test database or catalogue
fixtures were created.

Catalogue metadata, identifiers, creator links, holdings and publication states
were compared against locked production preimages and preserved. For twelve
reused images, inspected view qualifications were added to view labels and alt
text, with supplemental source attribution; their image bytes and prior rights
evidence were retained. Existing local/production catalogue differences were
preserved. This delivers the complete recovery selection; the broader local
report's 1,107 unresolved image candidates remain unresolved.

Evidence:

- [Production authorization](authorization.json)
- [Pinned delivery package](local-package-pin.json)
- [Local file, rights and identity verification](package-verification.json)
- [Reviewed creator crosswalk](creator-crosswalk-review.json)
- [Production plan checksum](production-plan-pin.json)
- [Transport guard verification](transport-guard-verification.json)
- [Successful Cloud SQL backup](cloud-sql-backup.json)
- [Committed database receipt](production-applied.json)
- [Complete database and live API verification](production-verification.json)
- [Final synchronization receipt](sync-receipt.json)
- [All 1,214 delivered images](synced-images.csv)
- [Local recovery report](../local-image-recovery-20261006/README.md)

The exact package is `local-delivery-package.json.gz` in this directory. Its
recovery copy is under
`/Users/vadimdulub/Library/Application Support/Artline/backups/production-local-image-recovery-20261008/`.
Cloud SQL backup `1791453150679` completed before production writes. Locked
preimages and committed after-state snapshots use the backup directory above.
Original image archives and local application JPEGs remain in their original
operation directories. Production images use the corresponding paths in the
`artline-508319-images` bucket and are delivered through `https://artlines.org`.
Per-image public HTTP receipts are under `uploads/` in this report directory.

The procedure was `ops/promote-local-image-recovery-20261008.py`: `prepare`,
`preflight`, `backup`, `upload`, `apply`, `verify`. Uploads used create-only
object writes. Database changes committed in one transaction after checking
locked preimages. Do not repeat the apply phase. Final procedures and logs are
archived under the matching `source-images/` directory in `procedures/completed/`;
the earlier authentication-blocked preparation remains preserved separately.
Queries were bounded to the selected IDs; these checks do not establish
10-million-artwork performance. No application deployment or git commit was
needed for this image delivery.
