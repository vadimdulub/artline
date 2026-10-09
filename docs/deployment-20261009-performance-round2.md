# Second performance release — 9 October 2026

The API and web performance changes are live at https://artlines.org. Both
revisions serve 100% of their service's public traffic. The API was promoted
first at 11:32 UTC, followed by the web at 11:34 UTC.

Source commit: `5f749385a12398ca0f1d3d51990ece4408ed67d8`
(`perf: streamline artwork pages and author timeline reads`), based on `e17e22c`.
Cloud Build source archives came from this committed tree; unrelated local
member-access and research changes were excluded and preserved in the main
working tree. No database migrations, catalogue writes, fixture creation,
Terraform apply or infrastructure resizing formed part of this release.

## Artifacts

| Service | Cloud Build | Serving revision |
| --- | --- | --- |
| API | `968e41c2-58eb-4514-91d7-7430adaeeaaf` | `artline-api-performance2-1009-0850` |
| Web | `bab0ed5c-a739-4a9a-bed0-22748b5fb42c` | `artline-web-performance2-1009-0850` |

- API: `europe-west1-docker.pkg.dev/artline-508319/artline/api@sha256:de30d9b20d2c6b2eec8d565cb84aafbb5c863ed48a472a7479700d7f13e7d4a7`
- Web: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:3f709fc706882aa0443656c690da4eb0f8b6eb4d34853f4e013e40093243d69e`

The rollout changed container images, revision identifiers and traffic only.
Before/after runtime comparisons confirmed environment variables, secret
references, service accounts, scaling, concurrency, resources and networking
were preserved. IAM was not changed. The ignored local production Terraform
image pins were updated to the deployed digests without applying Terraform.

## Verification

Predeployment correctness, query comparisons, unit/race tests, build and lint
results are in [the measurement report](performance-round2-20261009.md).

- Candidate API creator identities, canonical aliases, archived exclusions,
  review-artwork visibility and anonymous production sessions were checked.
  Fresh health, readiness, creator and review-artwork reads passed before promotion.
- Candidate and public-domain browser checks passed at 1440 px and 390 px:
  loaded images, zoom opening/closing, painter navigation, no horizontal overflow
  and no automatic full-painter/gallery request. Screenshots were inspected.
- Public artwork content renders without JavaScript, with canonical URLs,
  indexing metadata and artwork structured data. Both sampled artwork pages
  returned 200, a missing artwork returned 404 and obsolete catalogue/preview
  parameters redirected with 308. Anonymous production access remained intact.
- Final author requests returned 200 for the full timeline, highlights, women,
  an empty result and a second cursor page. Women and empty results were identical
  to the old API baseline; other predeployment response comparisons are recorded
  in the measurement report. The second page had no duplicate author IDs and
  preserved the total. The full timeline reported 3,436 authors.

The final five author requests took 0.150–0.564 seconds through the public web
proxy. These are sequential spot checks under uncontrolled cache and database
load, not a latency benchmark or sustained-capacity result.

## Remaining limitation

Earlier rollout checks encountered eight-second author-read deadlines on both
the previous API and candidate, unchanged painter-chronology timeouts, and one
transient readiness failure. The candidate's rewritten author query was also
observed waiting for a database data-file read. Concurrent catalogue inserts,
long-running research queries and maintenance were observed; this is evidence
of contention, not proof of the cause of every failure. Other jobs were not stopped.

The API promotion was qualified: its verification receipt retains `passed: false`
and the failed requests, alongside `readyToPromote: true`, successful behavior
proofs and fresh core checks. Later candidate and public-domain checks passed;
they do not establish that the earlier timeouts are resolved. Cold museum and
full painter reads, broad search counts, sustained concurrency and representative
10-million-artwork tests remain follow-up work.

## Rollback and evidence

Previous web: `artline-web-unified-catalogue-1008-1955`.
Previous API: `artline-api-performance-1009-0730`.
If rolling back both services, restore the web first because the new web needs
the new identity endpoint. No database rollback is needed. No rollback was run.

Machine-readable receipt: [deployment-20261009-performance-round2.json](deployment-20261009-performance-round2.json).
Private build, service, failure, request and browser evidence is retained under
`/Users/vadimdulub/Library/Application Support/Artline/backups/performance-round2-deploy-20261009/`.
