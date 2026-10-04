# Decolonisation — live delivery confirmed, 28 September 2026

The user requested publication of the completed research batch. All **18 new
records**, **10 new images**, and **5 existing thematic selections** are now
available on the canonical production site:

[Open Decolonisation](https://artline-web-lpuqqlugnq-ew.a.run.app/all?preset=decolonization).

The separately authorised [starting-point release](../production-starting-points-20260928/README.md)
had already transferred this batch and deployed the updated API when this
publication request was checked. No duplicate import or additional deployment
was needed. The newer period expansion is preserved: the live gallery now has
**104 illustrated artworks**, nine books and nine events. This is larger than
the 29 illustrated works at completion of the original research task.

## Live verification

- All 18 new artwork detail endpoints returned HTTP 200 with the expected
  titles, creation dates and source citations. Eight remain metadata-only.
- All ten new image responses returned HTTP 200 and matched the exact SHA-256
  hashes of the visually reviewed local files. Rights labels are unchanged.
- All five reused works resolve to their correct production records. The
  independent local and production UUIDs for *Collective Suicide* are handled
  by the existing stable-slug identity map; no duplicate artwork was created.
- All 23 selections are included in the live period configuration.
- Desktop (1440 px) and mobile (390 px) checks confirmed the live 104-work
  gallery, a new Orozco image and working detail drawer, no “In review” labels,
  no horizontal page overflow and no browser errors.
- Current production traffic and the canonical service URLs are recorded in
  `live-services.json`. Verification used the canonical site, not a candidate
  deployment URL.

“Live” here means available through the site's existing personal research
preview. Internal editorial review states remain unchanged, including incomplete
records; publication does not invent missing metadata or upgrade image rights.
No database writes, permissions changes, commits, or deployment were necessary
in this turn. The prior release's backup and create-only image upload receipts
remain the recovery evidence.

Detailed receipts: `completion.json`, `live-details-images.json`,
`existing-selection-live.json`, `live-browser.json`, `live-atlas-before.json`,
`live-preset-before.json`, and `live-services.json`. Screenshots are stored under
`/tmp/artline-decolonization-live-*`. The in-app browser setup was unavailable;
the checks used local Chrome automation against the live site.

The [original research report](../decolonization-deep-20260928/README.md)
retains the historical analysis, object sources, image decisions and exclusions.
