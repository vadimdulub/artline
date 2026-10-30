# Museum pages, locations and guides — 30 October 2026

The interface and filter changes are implemented and locally verified. The
all-museum content review is **incomplete**. A complete structural inventory
covers 2,664 active canonical institution records, including empty collections
and historic sites. Only 28 existing museum profiles received independent
source review and new two-paragraph English introductions in this pass.

The production data transaction updated those 28 descriptions and added 27
missing institution-to-place links, reusing existing cities where possible
and adding 14 city records with no invented coordinates. The National Gallery
of Armenia now has **Yerevan, Armenia**, supported by its official
[visitor information](https://www.gallery.am/en/visit) and
[museum history](https://www.gallery.am/en/about).

Transaction **1071746**, backend **1362060**, retained all three shared ingestion
locks before its writes and after all 71 atomic audits. Fresh read-only checks
verified every resulting record and audit. All 28 revised descriptions and
locations were independently fetched from the existing production museum API.
Never replay this transaction. Its plan and exact before/after records are under
`~/Library/Application Support/Artline/backups/museum-page-review-20261030/`.

The closing census still finds **1,280 institutions without a country in either
their primary place or their active venues**; 1,282 lack a primary country.
The remaining 2,636 institution profiles have not received independent editorial
review in this pass. Existing copy and recorded locations are not automatically
classified as verified. Missing facts were left unresolved.

The page changes put city and country below museum names, retain correct
city/country pairs when using venues, and show descriptions as separate
paragraphs. A dedicated guide section precedes the collection, with clear
reading actions. Museum-authored published guides are included on detail pages.
Directory cards link directly to existing editorial guides using the same
86-guide/88-museum mapping as museum pages. No-picture cards use the available
width, and guide actions remain within each card.

Location filters appear first. Go returns countries alphabetically and searches
each word across museum names and recorded locations, allowing “Armenia national
gallery” to find the canonical record. Country/region filters and bounded
pagination retain their existing rules. The collection action also activates
the collection tab from other museum sections without discarding filters.

The web and API code changes **have not been deployed**. The data corrections
are live. Existing artwork facts, images, makers, holdings, display assertions,
review states, museum identities and venues were preserved. There were no image
requests, Storage uploads, agents, jobs, commits, pushes or infrastructure
changes. No real local catalogue or member fixtures were written.

Validation includes 20 focused web tests, TypeScript, focused ESLint, Go catalog
and HTTP API tests, and two production read-only repository regressions. The
browser checks cover 1440, 1024, 768, 390 and 320 pixels, filter application,
reload, clearing, guide presence/absence, location display and tab navigation.
They use an isolated GET-only in-memory API fixture. Axe reports no violations
on tested museum details at all five widths and on the directory at 1440, 390
and 320 pixels. The desktop directory and phone detail screenshots were visually
inspected; an initial card overlap was corrected and checked again. The original
functional-only report and the QA findings remain available.

The anonymous production directory request returned `401 AUTH_REQUIRED`, as
required by the membership policy. An authenticated production browser session
was not exercised. Armenia's country facet and filtered result were verified
through the current repository using a read-only production transaction.
No full production build or release artifact is claimed.

Evidence:

- [Inventory and review dispositions](all-institutions-audit.csv)
- [Initial structural audit](audit-summary.json)
- [Reviewed copy and individual sources](profiles-reviewed.json)
- [Applied transaction](applied.json)
- [Database verification](database-verification.json)
- [Production detail API verification](public-api-verification.json)
- [Repository profile and country verification](repository-profile-verification.json)
- [Word-order search regression](search-regression-verification.json)
- [Closing location census](closing-location-census.json)
- [Browser verification](browser-verification.json)
- [Directory accessibility](directory-accessibility-verification.json)
- [Source access limits](source-access-note.json)
- [Result and remaining work](RESULT.json)

Source metadata, response bodies, screenshots and the browser harness are outside
Documents under the matching `source-metadata/`, `backups/` and
`research-proofs/` directories in `~/Library/Application Support/Artline/`.
