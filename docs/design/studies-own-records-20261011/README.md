# Personal research records · 11 October 2026

The Add dialog now labels its personal-entry tab **Your own**. Cards use the same
label, and their source action says **Open your source** when a URL exists.

The form asks for a title and year. An optional end year turns that date into a
closed interval, e.g. 1875–1880. The URL and creator are optional. No source link
or source evidence is fabricated when the URL is blank. The API requires dates,
rejects reversed ranges and year zero, and retains the existing limits of 12000
BCE through 2000, or through 1970 for artworks. Previously saved undated records
and uncertain catalogue dates are preserved.

The API accepts `year` and optional `end_year` inside the existing personal-record
payload. Timeline placement, date filters and exports use the resulting interval.
Personal records without URLs remain distinct; an empty URL is no longer treated
as a duplicate identity. Personal entries stay in the member's study and do not
enter the shared catalogue.

Validation: nine browser scenarios, five study web unit tests, Go member/catalogue/
HTTP race checks in the workspace, type checking and scoped lint. Additional
screenshots and axe checks cover this form at 1440, 390 and 320 pixels. A record
without a URL was saved with a range, plotted on the timeline and exported.

The isolated release uses the currently deployed sources with only the Studies
files and navigation hooks overlaid. Its member and catalogue race tests pass.
One inherited Books HTTP test still expects the old 150-item limit; deployed Books
already accepts 300. The remaining release HTTP tests pass with that stale test
excluded. The Books runtime was preserved, and its endpoint is checked live.

The production deployment receipt is recorded separately in
[`../../deployment-20261011-studies.json`](../../deployment-20261011-studies.json).
Both production services now serve 100% of traffic on the Studies revisions. The earlier preview on port
3111 and its in-memory research remain running; this revision was independently
verified on port 3114 with a read-only catalogue connection and ephemeral studies.
