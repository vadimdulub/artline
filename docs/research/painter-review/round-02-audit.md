# Round-2 local implementation audit

11 September 2026. No commit, publication, deployment or Terraform apply.

## Applied changes

- Added 15 new selected authentic museum reproductions to disk and local PostgreSQL: 13 SMK and 2 Cleveland; 34,736–99,681 bytes each, 1,215,401 bytes total.
- Kept all 105,961 artwork metadata records, all 5,328 artists, all artist links, all holding assertions, all existing media and all existing curated selections unchanged. Only the 15 target primary-image references/revisions and new media/evidence rows changed.
- Pictures/media: 403 → 418. Museum-highlight items remain 569; owner-selection items remain 5. Published artworks remain zero.
- Go staging mode `stage-round2` validates fresh exact-object source captures, checksums, source creator authorities, title/date identity and image-specific reuse permission. It uses the existing pinned preview/apply and per-work transactions, rather than a separate unreviewed write path.
- The SMK metadata date parser now defers notes based on artist years or museum accession. Regression tests cover both phrases, case variation and an ordinary accepted creation year. This guards future selection; it does not silently repair old DB values.
- Expanded the local API image verifier to recognize SMK routes.

## Backup

Pre-change database snapshot:
`/Users/vadimdulub/Documents/artline-round2-images-backup-20260911.sxrkHo/before-images.dump`

SHA-256: `56765495d92a6b86ebe6e07bd2fe5062f532a53badbd06a83f16c0e144b5e260`.

Custom-format dump completed and its table of contents was readable with `pg_restore -l`. A restoration into a separate test database was not performed. No restore was applied to the user's database.

## Immutable selection and receipts

Selection: [round-02-image-selection.json](round-02-image-selection.json)

SHA-256: `9b739312caf9d68238bdaa161f4a96144b4f019e28a29c72a7f60293fe6f637c`.

| Evidence | Result |
|---|---|
| [Preview](../../../output/round-02-images-preview.json) | 15 ready, no DB writes or image downloads |
| [Apply](../../../output/round-02-images-apply.json) | 15 attached, no failed downloads |
| [Replay](../../../output/round-02-images-replay.json) | Existing media preserved; no duplicate images |
| [Before](../../../output/round-02-images-before.json) / [after](../../../output/round-02-images-after.json) | All record/relationship/selection preservation checks passed |
| [API/image verification](../../../output/round-02-images-api.json) | 49 API checks, 15 full JPEG decodes, 15 served hashes passed |
| [Ledger verification](../../../output/round-02-ledger-verification.json) | 5,328 painter pages, 105,961 unique works, all 54 matching review decisions; prior 32 retained |

API checks covered authenticated preview detail, unauthenticated record exclusion, unauthorized preview rejection, and two bounded image-only pages per museum with non-duplicate cursors. No access token was written to a receipt. This is not a browser-interaction or responsive-layout test.

`go test ./...` and `go vet ./...` passed. New round-two tests check all sixteen permitted source objects, altered creator/date rejection and rejection of deferred identities. Existing rights/selection tests still pass. The known opt-in 100k-row institution/accession query-plan issue remains unresolved; these checks do not establish 10-million-row performance.

## Research ledger

[round-02-decisions.json](round-02-decisions.json) retains all 32 earlier decisions unchanged and adds 22 explicit decisions:

- 14 completed artwork reviews;
- 5 blocked artwork reviews;
- 2 blocked painters;
- 1 painter in progress.

No full research round or painter in this cohort was marked complete. The new immutable inventory is [round-02-smk-cleveland](snapshots/round-02-smk-cleveland/PAINTERS.md). Existing snapshots remain unchanged.

The deep-research skill informed the separate cited research report, explicit disagreement handling and distinction between verified facts and discovery leads. No full-catalogue completion was inferred from a script run or an image being present.
