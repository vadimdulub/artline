# Women artists production release — 15 September 2026

Application commit: `f30681bffe477c948cdb1272c949ae4ba1dcf109`.
Release tag: `20260915-f30681b`.
Project: `artline-508319`; region: `europe-west1`.

This release adds an evidence-backed Women artists discovery filter. Gender
membership is stored separately from artist publication and popularity, and
missing evidence remains unknown rather than being inferred. The filter scopes
the timeline, facets and painter options consistently and composes with the
existing popular-painters filter. Existing review/publication states were not
changed by this application deployment.

The application commit was pushed to `origin/master` before the build. Both
images were built from a clean archive of that exact commit, excluding unrelated
research files in the active workspace.

| Service | Cloud Build ID | Live revision | Image digest |
| --- | --- | --- | --- |
| API | `8cd1b0c7-b89a-477c-848c-8e54585710d1` | `artline-api-00013-8hw` | `sha256:98489f08f60ea7731e7913e90bbf2788d75d90e3140c2ae9cda7745986477cfd` |
| Web | `8a2ada86-5922-4479-9918-3670fc82d74f` | `artline-web-00013-l98` | `sha256:1d41781aebce937133c503876aabe8bece03d7c1945481126f980403c870061b` |

Both revisions receive 100% of service traffic. Terraform applied only the API
and web image changes: zero additions, two in-place changes and zero removals.
The final detailed plan reported no changes.

## Verification

- All Go package tests passed with an isolated Go 1.25.7 toolchain/cache.
- Read-only catalogue integration checks passed against the real local database,
  including women-only facets/options and repeated timeline count/suggestion
  checks. No fixtures or writes were used.
- All 34 web unit tests, ESLint and the Next.js production build passed.
- All 128 research-tool unit tests passed in the existing project environment.
- Both women-filter browser regressions passed locally and in production. They
  cover independent women/popularity state, URL/history persistence, reset and
  clear behavior, and viewport fit at 1440, 390 and 320 pixels.
- Production `/health` and `/ready` returned success. The live combined filter
  returned an individual timeline with 5 popular women and explicitly reported
  `women_only=true` and `popular_only=true`, confirming the evidence table is
  queryable by the new API revision.
- The post-release Cloud Run error-log query returned no entries.

These checks do not establish 10-million-row capacity or publish review records.
The unrelated research/import workspace remains uncommitted and was not included
in the release images.

Live site: https://artline-web-lpuqqlugnq-ew.a.run.app
