# Google Search Console setup — 3 October 2026

The owner requested setup through their signed-in browser and completed the
Google account reauthentication prompt. Google confirmed ownership of the
`https://artlines.org/` **URL-prefix property** using the HTML verification tag.
No DNS Domain property was created.

The [Sitemaps report](https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Fartlines.org%2F)
accepted `https://artlines.org/sitemap.xml`. The first attempt displayed
“Couldn't fetch”; Google's live URL test then confirmed crawl permission and a
successful fetch. A single resubmission returned **Success** for the index.
The XML index points to `/sitemap-pages.xml`, containing `/about`, `/artists`
and `/art-history-timeline`.

The child sitemap still reports **Couldn't fetch** and zero discovered pages.
It was also submitted directly and retried once after Google's live URL test
confirmed **Crawl allowed: Yes** and **Page fetch: Successful**. Direct HTTP
checks also returned valid XML with status 200. No server or XML fault was
identified, and no speculative sitemap code or robots changes were made.
Recheck the child's processing status on Google's next attempts; acceptance
of the index does not establish successful processing of its child or page
indexing. Search Console's overview was still processing the new property's
data.

Google's live URL test for `/art-history-timeline` reported that the page is
available to Google and can be indexed, with one valid breadcrumb item.
The subsequent **Request indexing** action was accepted and added the URL to
Google's priority crawl queue. Indexing itself remains pending.

The same-day follow-up found the index still successful and the child still
reporting a fetch error. Cloud Run request logs showed HTTP 200 responses to
Googlebot requests for the child at 06:43:20 and 06:44:08 UTC, as well as the
successful Google Inspection Tool requests. The child response remained valid
268-byte XML with no content-encoding mismatch. All three listed pages returned
200, allowed indexing and declared their corresponding canonical URL. Search
Console settings reported a valid `robots.txt`. These checks did not identify
an application fault requiring another deployment; Google's child-sitemap
processing status remains the follow-up item.

The initial verification used `dulubvadim@gmail.com`. The owner subsequently
directed that this account be removed and the work account used instead.
The HTML token was replaced with the token obtained while signed in as
`vadim@alingva.com`; Google confirmed ownership for that account. The Users and
permissions list then showed exactly one user: `vadim@alingva.com`, **Owner,
Verified**, with the personal account absent. Google's **Verify removal** check
confirmed that the personal account's HTML token was successfully removed and
could no longer be used to access this property. The unused-token count became
zero. Search Console was left open in the work Chrome profile.

## Production configuration

The initial configuration-only Cloud Run revision
`artline-web-searchconsole-1003` added `ARTLINE_GOOGLE_SITE_VERIFICATION` to the
existing layout's supported metadata configuration. The ownership transfer
replaced that value in revision `artline-web-searchconsole-work-1003`, which now
serves 100% of normal web traffic in project `artline-508319`, region
`europe-west1`. The work account's public token is also saved as
`google_site_verification` in the ignored `terraform/prod/terraform.tfvars` so
a later infrastructure update can preserve the correct ownership verification.

The immutable image is unchanged from the
[2 October SEO release](deployment-20261002-seo.md):

`europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:8a9481c1fd5c334949ce586117dea2a25290123a2d426b121223d0e60e421000`

Both candidates received zero normal traffic until their rendered HTML passed
verification. Live-domain checks confirmed the exact token in the document
head, the homepage's existing `noindex, follow`, the guide's `index, follow`,
and both canonical URLs. Final service checks confirmed readiness, traffic and
unchanged runtime settings apart from the token and revision. Robots discovery
and both sitemap XML documents returned HTTP 200 and passed XML/URL checks.
The transfer checks also confirmed that the personal token was absent from the
homepage and guide HTML. No application rebuild was needed to replace the token.

No rebuild, API release, database writes, publication changes, DNS changes,
Terraform apply or Git commit was needed. Google sign-in, production local-debug
safeguards and public research-preview settings remain as before. Review
records still require editorial validation and explicit publication.

## Evidence and rollback

Private service preimages, operations, local Terraform preimage, checks and
Google verification screenshots are stored under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/searchconsole-20261003/`

The transfer's service preimage, operations, Terraform preimage and browser
confirmation screenshots are in the sibling directory:

`/Users/vadimdulub/Library/Application Support/Artline/backups/searchconsole-work-20261003/`

These directories can contain private runtime configuration; keep them out of Git.
Disposable GUI helpers and checks are under `/tmp/artline-searchconsole-*` and
`/tmp/artline-search-console-*`.

The preceding revision is `artline-web-searchconsole-1003`, which contains the
removed personal account's token; `artline-web-seo-1002` contains no Google
verification token. A direct rollback to either would remove the work account's
verification, and the former would allow the personal account to reverify.
Preserve the work account's current token in any replacement revision. Use the
explicit project `artline-508319` and region `europe-west1` for service updates.

Troubleshooting followed Google's
[Sitemaps report guidance](https://support.google.com/webmasters/answer/7451001?hl=en),
including a live URL test of crawl permission and page fetch.
