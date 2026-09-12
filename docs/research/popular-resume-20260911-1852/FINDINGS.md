# Source decisions — resumed popular-painter cycle

## Paris Musées — access terms checked before automation

Manually reviewed Petit Palais leads: [Cézanne, Trois baigneuses](https://www.parismuseescollections.paris.fr/fr/petit-palais/oeuvres/trois-baigneuses),1879–1882,PPP2099; [Morisot, Jeune fille au décolleté, la fleur aux cheveux](https://www.parismuseescollections.paris.fr/fr/petit-palais/oeuvres/jeune-fille-au-decollete-la-fleur-aux-cheveux),1893,PPP488; [Courbet, Le Sommeil](https://www.parismuseescollections.paris.fr/fr/petit-palais/oeuvres/le-sommeil),1866,PPP3130. Each displays a CC0 image credit. However the [collection terms](https://www.parismuseescollections.paris.fr/fr/conditions-generales-d-utilisation) and [API documentation](https://apicollections.parismusees.paris.fr/en/documentation/20) condition automated API access on an account and acceptance of terms, and restrict automated extraction outside compliant use. These are leads only, NOT imported or downloaded. One public Cézanne manifest was read diagnostically before the terms check; no image binary/capture mutation. Continue a permitted source rather than bypassing account requirements.

## Athens and Poldi — identities and image-source disagreements

Athens Π.9979 Entombment added with explicit c.1568–1570 range; exact Commons image deferred pending missing US public-domain evidence. See [El Greco review](el-greco.md). Empty normalized translated-title collisions with Cyrillic icons were a query defect, not evidence of duplicates; NULLIF plus literal-title checks and read-only database regression now prevent those false matches. No icon records changed.

Poldi Pezzoli Saint Nicholas0445 and Imago Pietatis1587 added with museum dates and dimensions. Independent Commons full-frame PD-Art reproductions matched by accession, creator, collection and composition. Stale Commons dates and incorrect unit labels deliberately excluded from artwork facts. Both images <=100000 bytes and visually checked; preservation, decoding and delivery verification passed. See [Piero](piero-della-francesca.md) and [Bellini](giovanni-bellini.md). The museum reproduction permission form was not treated as an open grant; no museum-hosted image was downloaded.

Started 11 September 2026, 18:52:48 UTC. This file records source-backed decisions, not exhaustive painter completion. Earlier 135 artwork/13 image additions are excluded from this run's counts.

## Belvedere: Schiele and Klimt

- Reviewed [Schiele, The Embrace](https://sammlung.belvedere.at/objects/3232/die-umarmung): 1917, oil on canvas, 100 × 170 cm, inventory 4438, direct artist identity 1890–1918 and Belvedere collection credit. This is a verified research lead, **not imported** in this run.
- Reviewed [Klimt, Judith](https://sammlung.belvedere.at/objects/3492/judith): 1901, inventory 4737; already present locally, so not a new-work candidate. The primary photograph is credited to Johannes Stoll / Belvedere. Its object-level download language limits use to private/scientific purposes, with commercial uses requiring permission.
- The [Klimt authority page](https://sammlung.belvedere.at/people/1064/gustav-klimt) labels its Kiss illustration CC BY-NC-ND 4.0. Do not generalize that grant to other photographs. The Kiss is also already present locally.
- [Museum imprint](https://www.belvedere.at/impressum) expressly reserves text/data-mining use. Consequently no automated Belvedere collection capture/import or images were attempted. Its [robots file](https://sammlung.belvedere.at/robots.txt) additionally specifies a 30-second crawl delay and disallowed routes. Historical “open content” press announcements are not sufficient to override the current object terms.
- The [2018 Schiele exhibition](https://www.belvedere.at/egon-schiele) mixes collection works, former collection works and external loans. Exhibition inclusion must not become a current holding claim. Schiele's Austrian coverage remains an important unresolved gap.

## SMK: avoid repeating already-resolved access checks

The earlier exact-object capture `content/imports/popular-smk-20260911/facts.json` already records 41 checks. Gauguin's seven selected SMK works, Pissarro's three, Degas's Village Street, Sisley's Waterworks and Van Gogh's Saint-Rémy landscape have `has_image=false` in those snapshots. Several Van Dyck/Courbet records have `has_image=true` but no `image_iiif_id`. These are **source-image gaps**, not complete painter research; no unchanged requests were repeated.

The [official SMK API documentation](https://www.smk.dk/en/article/smk-api/) permits collection-data reuse and explains the per-object public-domain flag. The [SMK Open policy](https://www.smk.dk/article/smk-open/) separately explains its waiver for photographs of public-domain works. Generated enrichment fields are not used as historical evidence.

Three previously unreviewed Matisse exact-object responses were captured through the bounded Go collector, with hashes, timestamps, one-MiB limits, two-second pacing, no redirects or automatic retries:

| Object | Title | Source creation date | Decision |
|---|---|---|---|
| [KMSr171](https://api.smk.dk/api/v1/art/?object_number=KMSr171&lang=en) | Portrait of Madame Matisse. The Green Line | 1905 | Existing exact work; image permission verified |
| [KMSr73](https://api.smk.dk/api/v1/art/?object_number=KMSr73&lang=en) | Street at Arcueil | 1899 | Existing exact work; source says scholarly dating estimate, not invented career bounds |
| [KMSr75](https://api.smk.dk/api/v1/art/?object_number=KMSr75&lang=en) | Place des Lices, Saint-Tropez | 1904 | Existing exact work; image permission verified |

All three identify `897_person`, Matisse 1869–1954, a single unqualified creator, exact accession and matching local dates. All provide `has_image=true`, `public_domain=true`, Public Domain Mark 1.0 and a specific official IIIF image. Only `/full/!700,700/0/default.jpg` renditions are requested, without a client-side crop. Derivatives must decode and remain at or below 100,000 bytes. These are study selections, not museum masterpiece designations.

Selection SHA256: `8055129b316784e0aac3b64a38f7ecdede4a0c6c2e6f19d19b764ba5412fa8d8`.
Backup: `/Users/vadimdulub/Documents/artline-popular-resume-20260911-backup.xM3Mcm/before-smk-matisse.dump`, SHA256 `02651acc7fe47ef6b6faf334270aa923f258e1278fce569b0376fc3ac646c7d9`; archive table of contents verified.

## Service-error interruption

At approximately 19:05–19:07 UTC, the user asked whether `{"detail":"Bad Request"}` from “our service” can be retried. Read-only diagnostics inspected API routes, proxy and current logs. Health/readiness, timeline through Next and Monet works through Next each returned 200 twice. Unauthenticated direct Monet API queries returned the expected review-record visibility 404 in the app's structured `error.code/message` format; the development proxy supplies authorized preview access. No observed response reproduced the reported detail-only error. No automatic retry or mutation replay was added. Requested the precise failing URL/method/status with secrets removed; still unresolved. This diagnostic span is tracked separately from painter-research activity.
