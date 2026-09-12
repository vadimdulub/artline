# Legacy records are real catalogue data, not test fixtures

Read-only follow-up, 12 September 2026. The eleven artworks without external
identifier rows all exist, have primary images, and retain source citations.
Their exact slugs trace to the real catalogue migrations below. Do not delete
them as test data or insert another copy to obtain an import receipt.

| Exact artwork slug | Original catalogue migration | Evidence and remaining distinction |
|---|---|---|
| giotto-kiss-of-judas | `0004_giotto_review_selection.sql` | Scrovegni Chapel cycle source; Commons panel image |
| giotto-lamentation | `0004_giotto_review_selection.sql` | Same cycle source; individual panel chronology remains under review |
| giotto-last-judgement | `0004_giotto_review_selection.sql` | Same cycle source; distinct wall composition |
| giotto-massacre-of-the-innocents | `0004_giotto_review_selection.sql` | Same cycle source; distinct panel |
| giotto-meeting-at-the-golden-gate | `0004_giotto_review_selection.sql` | Same cycle source; distinct panel |
| anna-ancher-sunlight-blue-room | `0005_illustrated_selection.sql` | Skagens Museum partner record on Google Arts & Culture; Commons image |
| artemisia-judith-beheading-holofernes | `0005_illustrated_selection.sql` | Uffizi notice, accession 1890 no. 1567; not the Naples version |
| hilma-ten-largest-childhood-2 | `0005_illustrated_selection.sql` | HAK103; Guggenheim educational source records the work, not Guggenheim ownership |
| hokusai-great-wave | `0005_illustrated_selection.sql` | Met 45434, impression JP1847; do not merge other impressions on title |
| kroyer-summer-evening-skagen | `0005_illustrated_selection.sql` | Skagens Museum partner record on Google Arts & Culture; Commons image |
| munch-the-scream-1893 | `0005_illustrated_selection.sql` | National Museum NG.M.00939; not another Scream version |

Migrations live in `apps/server/db/migrations/`. Images were added or associated
by `0005_illustrated_selection.sql`; factual selection is also retained in
`content/artworks/selection-2026-09.json`. Existing media were included in the
639-file full disk audit, which is not a renewed manual identity/rights review.

Outcome: **11 legacy origins reconciled**, zero database changes or fabricated
identifiers. Keep missing structured rights evidence, oversized legacy files,
panel dating and exact version review separately queued. The remaining 150 works
outside recognized metadata receipts retain source identifiers/citations; their
other importer formats are still a separate receipt-reconciliation task.
