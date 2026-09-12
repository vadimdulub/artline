# Priority: Russian icons, Greek artists and Byzantine art

Explicit owner priority, 10 September 2026: these traditions are very important.
Prioritize them in the next collection pass; European coverage must not default
to Western European oil paintings and named modern artists alone.

## Official-source starting points checked on 10 September

- [Byzantine and Christian Museum, Athens — collections](https://www.byzantinemuseum.gr/en/21/collections):
  icons, wall paintings, manuscripts and other media; links to its digital museum.
- [Benaki Museum — Byzantine Art](https://www.benaki.org/index.php?id=63&lang=en&option=com_collections&view=collection):
  Byzantine and post-Byzantine icons.
- [Benaki — Valadoros collection](https://www.benaki.org/index.php?id=51&lang=en&option=com_buildings&view=building):
  a focused icon collection to review as a collection/venue, not automatically
  a separate physical museum or duplicate of Benaki holdings.
- [Russian Museum — ancient Russian art](https://app.rusmuseum.ru/collections/ancient-art/):
  collection overview and links to object records on the Virtual Russian Museum.
- [Tretyakov Gallery — history of its early Russian painting collection](https://www.tretyakovgallery.ru/about/history/p-m-tretyakov-priobretaet-ikony-iz-sobraniya-i-l-silina/):
  discovery context; individual object records and current custody still needed.

These are reviewed discovery routes, not completed catalogue captures, image
licences or new database imports. Respect previously recorded access/rate-limit
failures; do not evade them through alternate infrastructure.

## Required modelling and ingestion review

1. Audit current anonymous/workshop support before importing icons. The current
   continuation selector intentionally requires an existing named artist QID;
   therefore it is insufficient for broad icon coverage. Do not fabricate an
   “anonymous painter” biography or merge unrelated anonymous masters.
2. Keep culture/tradition, school/workshop, creator attribution, place of
   production and today's holding country separate. A Greek artist can work
   outside Greece; a Byzantine icon can be held outside Europe. Regional museum
   filtering must not determine a work's cultural identity.
3. Record icons as an appropriate work/form classification without losing their
   actual medium: painted panel, mosaic, fresco, manuscript etc. Do not classify
   every religious object as a painting. Review UI filters and API coverage.
4. Preserve century/range dates, anonymous/attributed/workshop qualifiers,
   iconostasis panels, multi-panel objects and recto/verso relationships. Unknown
   creation dates stay unknown, with clear timeline coverage messaging.
5. The current importer lower bound is 1100; earlier Byzantine material needs
   an explicit date-range/model/UI decision, not silent exclusion or altered
   source dates. The owner-confirmed upper creation cutoff remains 1970.
6. Check current holding/custody against dated evidence. Museum ownership,
   church loans, repository locations and current display are separate claims.
7. Metadata first; selected per-image rights review and local ≤100,000-byte
   reproductions only where permitted. Public-domain age alone is not a grant
   to copy a museum's photographs.
8. Keep validation, visibility, taxonomy, date grouping and paging in Go/Postgres.
   Test bounded museum and artist queries; do not claim 10-million-row readiness
   from the current small/100k-row fixtures.

No new Russian/Greek/Byzantine objects were imported by the Normandy batch.
No commits, publication, cloud deployment or Terraform application authorized.

## First follow-up completed, 10 September

The [icon batch report](research/icons-20260910/research-log.md) records 22 new
review-only works: 15 Athens icons and seven Kremlin icons, including one
tentative attribution linked to Theophanes the Greek. Source-level unlinked
creator labels now work in museum lists and details without invented artist
profiles. Form and cultural context are separate from medium and holding country.
No photographs were downloaded. Pre-1100/multi-phase works, mosaics and broad
Greek/Russian coverage remain explicit follow-up work, not completed features.
