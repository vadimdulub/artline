# Search Console audit — 11 October 2026

The user authorized the **Vadim (v-test)** Chrome profile. The existing work account
has access to the verified `https://artlines.org/` property. No new account or
connector is required for this completed check.

## Recorded baseline

The Web performance report had **28 days** selected. Its available chart spans
**30 September–8 October 2026**, with an update age of 65 hours: **1 click,
19 impressions, 5.3% CTR and average position 28.4**. The 3-month selection showed
the same totals and available chart dates. These are a small starting sample,
not evidence of a stable ranking or a traffic forecast.

The art-history timeline recorded 1 click and 13 page impressions. No museum guide
appeared in the six-row page performance table. The leading visible query was
“timeline of art history” (3 impressions). Country totals: United States 1 click /
8 impressions; Cyprus 0 / 3; United Kingdom 0 / 2; Russia, Australia, Ireland,
Germany, Italy and Spain each 0 / 1. Preserve Google's aggregate, page and query
counts separately: the visible query table does not explain all totals, and page
impressions total 22 while the property-level total is 19.

The Page indexing report is dated **4 October 2026**: **5 indexed, 36 not indexed**
(19 excluded by noindex, 16 discovered but not indexed, 1 crawled but not indexed).
It is delayed and does not represent all current site URLs. Sample noindex
exclusions include member-only museum pages and an old homepage crawl. The single
crawled exclusion is a Monet artwork; the first ten discovered examples are public
artist/artwork URLs. These catalogue exclusions remain follow-up items.

## Completed Google actions

Both `/sitemap.xml` and `/sitemap-pages.xml` already showed **Success**. The earlier
child-sitemap fetch error has cleared. Both were resubmitted on 11 October and
Google confirmed **Sitemap submitted successfully**. Last-read dates and counts
remained historical immediately afterward: main index 8 October / 1,679 discovered
pages; page sitemap 6 October / 3 discovered pages. The live page sitemap has 68
URLs including all 60 language editions, and its new processing is pending.

| URL | Google status before request | Live test | Indexing request |
| --- | --- | --- | --- |
| https://artlines.org/ | Excluded by noindex; last crawl 2026-10-03 | Available to Google | Accepted |
| https://artlines.org/guides | URL is unknown to Google | Available to Google | Accepted |
| https://artlines.org/guides/louvre | URL is unknown to Google | Available to Google | Accepted |
| https://artlines.org/guides/prado | URL is unknown to Google | Available to Google | Accepted |
| https://artlines.org/guides/leventis-gallery | URL is unknown to Google | Available to Google | Accepted |
| https://artlines.org/guides/national-gallery-armenia | URL is unknown to Google | Available to Google | Accepted |
| https://artlines.org/guides/munich-museums | URL is unknown to Google | Available to Google | Accepted |
| https://artlines.org/guides/muma-le-havre | URL is unknown to Google | Available to Google | Accepted |

The homepage's old noindex result came from 3 October. Its current live test allows
indexing. The guide hub and all six English guides were unknown to Google when
inspected. All eight live tests passed and all eight requests were added to
Google's priority crawl queue. **Accepted requests do not confirm actual indexing.**

Manual actions and Security issues both reported **No issues detected**. Google's
live test recognized valid guide breadcrumbs and image metadata. The MuMa sample
reported three valid ImageObjects with optional missing fields: copyrightNotice,
acquireLicensePage, creator, and license on one sampled item. These are non-critical;
unknown rights information must not be invented to remove warnings.

## Follow-up — 18 October 2026

1. Inspect the eight URLs again and record actual indexing and selected canonicals.
2. Check refreshed sitemap last-read dates and discovery of the guide editions.
3. Compare guide clicks, impressions and queries with this baseline.
4. Investigate persistent artist/artwork exclusions and the separate transient API
   503 issue. Improve useful content/internal discovery based on the actual reason.
5. Continue the planned two new English articles per week after assigning ownership.

This is a recommended review date; no scheduled automation was created. The 54
translated guide pages are covered by the sitemap submission but were not individually
inspected in Search Console. Fresh mobile visual QA and PageSpeed scoring remain
outside this completed account check. No code, deployment, catalogue, verification,
permissions or login-policy changes were made in this continuation.

Evidence: [structured baseline](baseline.json), sibling dated UI snapshots, and the
[earlier production verification](../production-verification.json). Browser UI was
read through macOS Accessibility after the in-app connection failed; browser
security settings, cookies and profile stores were not changed or copied.

Google explains that crawling may take days to weeks and that requests do not
guarantee inclusion: [recrawl documentation](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl).
