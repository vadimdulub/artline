# Museum coverage follow-up — 8 September 2026

## Outcome

Ten sourced artwork records were added, filling nine previously empty popular
painter profiles. The selection did not depend on image availability.

| Collection | Works added | Newly represented painters | Images added |
| --- | ---: | --- | ---: |
| Uffizi, Florence | 9 | Botticelli (2 works), Cimabue, Piero della Francesca, Fra Angelico, Paolo Uccello, Bronzino, Perugino, Ghirlandaio | 0 — permission pending |
| Museo de Arte Moderno, Mexico City | 1 | Frida Kahlo: *The Two Fridas*, 1939 | 0 — permission pending |

The [reviewed manifests and source notes](../content/curation/README.md) retain
official URLs, dates, inventory crosswalks and the basis for every selection.
Five records are sourced museum designations; five are personal picks of documented
holdings. Personal choices are not represented as the museum's ranking.

The [Uffizi](https://www.uffizi.it/en/professional-services/publications) describes
a separate image-use authorization process. This pass did not treat a Commons
copyright label as complete permission. Frida's official
[highlight record](https://mam.inba.gob.mx/destacadas.html) likewise does not establish
an open image licence. Both adapters fail closed for downloads; permission notes
are visible under Artwork sources. No permissions were requested from third parties.

## Verified totals

- 1,001 active painters; the imported candidate cohort remains 1,000.
- 100 popular painters; **84 have artworks**, up from 75. **60 have images**,
  unchanged. Sixteen still have no artwork records; forty still have no images.
- 387 artworks, 211 illustrated; 372 imported artworks, 196 verified imported
  images occupying 39,419,832 bytes. Original seed images are preserved.
- Eleven museum/holding collections (direct SQL/API count); 194 cohort painters
  have imported artworks. This corrects the earlier report's museum baseline;
  no existing institutions were removed.
- No published painters, new display assertions or creation-scope violations.
  The earlier six source identity conflicts remain unresolved, not silently fixed.
- Replay of both imports added zero artworks and zero images.

## Backend safeguards added and tested

- Explicit source-host/path allowlists and bounded manifests; no exhaustive scrape.
- Whole-batch identity/source preflight before writes. Approximate museum dates
  remain approximate; depicted event dates do not replace creation dates.
- Museum versus owner selection kind is carried through Go into SQL collections.
- Collection insertions share the editor's row-lock/revision protocol. Replays
  preserve changed titles and do not reinstate removed owner selections.
- Country records are provisioned for a fresh database; city identities include
  the country so identically named cities do not share an import identifier.
- A shared museum highlights URL cannot merge distinct artworks. Authority IDs
  identify each work; the shared URL remains a citation.
- No new frontend data-processing logic, migrations or remote infrastructure.

## Verification

- Go suite passed with isolated PostgreSQL integration fixtures, including replay,
  editorial preservation, collection-kind separation, fresh geography, shared-page
  identity, source conflicts, post-1970 rejection and denied image attachments.
- Ten Playwright scenarios passed: six discovery regressions plus four coverage
  scenarios for Botticelli chronology, Uffizi selections, Frida, source permissions,
  no invented on-view claims, keyboard focus and mobile rendering.
- Automated axe checks passed at 1440, 390 and 320 pixels for the new museum page
  and right drawer. Screenshots: `screenshots/uffizi-record-{width}.png`; the
  390-pixel drawer was also visually inspected.
- Twenty frontend unit tests, ESLint and Next.js production build passed.
- The in-app browser connection failed at bootstrap; the existing local Playwright
  runner was used. No claim that the older seed-specific full browser suite passes.
- Read-only asset/data audit passed. No 10-million-row load benchmark was performed.

## Remaining work

Popular painters still missing artwork records: Pieter Bruegel the Elder,
Masaccio, Tintoretto, Alphonse Mucha, Paolo Veronese, Giuseppe Arcimboldo,
Andrea del Verrocchio, Giorgione, Kazimir Malevich, Ilya Repin, Alfred Sisley,
Gustave Doré, Bob Ross, Vittore Carpaccio, Paul Signac and Sofonisba Anguissola.

Next batches should continue painter-to-museum coverage research, not broaden into
exhaustive downloads. Joint or qualified attributions need a reviewed multi-artist
crosswalk, not a forced single creator. Image clearance is still needed for these
ten records and for earlier modern-art gaps (including Picasso, Dalí and Matisse).
This is not completion of the 1,000-painter illustrated catalogue.

No commits, publication, Terraform apply, deployment or existing-content deletion.
