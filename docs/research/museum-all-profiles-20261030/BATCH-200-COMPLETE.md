# Resumed 200-profile batch complete — 30 October 2026

The owner asked to “finish 200 in this batch” after 196 profiles had been completed since research resumed. Added the final **four** reviewed profiles: Allen Memorial Art Museum in Oberlin, Kimbell Art Museum in Fort Worth, Des Moines Art Center in Des Moines, and McNay Art Museum in San Antonio, all in the United States. The resumed batch now contains **exactly 200 distinct profiles**.

Each addition has an original two-paragraph introduction and a source-verified city/country link. The four updates, four new city rows, four citations and one source record were committed once in production transaction **1077342**, with **13 atomic audits** and all three shared ingestion locks retained before the writes and after the audits. Existing identities, statuses, venue rows, citations, artwork holdings and images are preserved. The city rows contain no inferred coordinates.

Official museum and Oberlin College pages supply the history, collection scope and locations. The Kimbell press release was used only through its relevant published excerpt; no full-PDF reading is claimed. Four saved web research results are pinned in the batch's source evidence receipt. There were no new native museum/image requests or Storage uploads.

All four database/audit checks, serving projections and live detail responses pass. Every live response contains the exact reviewed description, city and country. No application or infrastructure release was needed for the production data updates.

The wider campaign now has **420 of 2,574 frozen targets completed**, leaving **2,154**. Its public checks comprise **374 available detail pages** and **46 empty collections** that remain hidden under the existing serving policy. Those 46 are verified as database profiles, not counted as live detail pages. The earlier 91 reviewed profiles remain outside the campaign count.

The fresh combined read-only verification confirms **511 profiles and 1,160 explicit atomic audits**, including all earlier work. The campaign alone now accounts for 954 atomic audits, 159 location-link corrections and 102 new city records. Previous receipts and checkpoints remain unchanged; the earlier [README](README.md) describes checkpoint v1, with 416 profiles. The current records are [checkpoint v2](checkpoint-v2.json), [combined database verification v3](cumulative-database-verification-v3.json) and [the four-profile delivery](batches/0012/applied.json).

The cumulative verifier now requires explicit expected campaign size and an unused report version, keeping older verification reports immutable. The successful invocation was:

```sh
python ops/museum-all-profiles-checkpoint-20261030.py --campaign-profiles 420 --version v3
```

Do not replay any completed writer or overwrite a verification report. Further research is outside this completed 200-profile batch. No agents, jobs, schedules or background research processes were started.
