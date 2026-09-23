# Jackson Pollock image research — 19 September 2026

Result: authentic reproductions located, but **0 images cleared, downloaded or
uploaded** in this pass. The checked sources require permission or have
conflicting rights evidence. No database, storage, publication or display-status
changes were made.

Artline's [image-use policy](../../ARTLINE_IMAGE_USE.md) requires evidence for
public/potentially commercial use. Finding a museum image URL is not clearance.

## Local catalogue audit

Read-only queries against the real local `artline` database, scoped to artist
`6911af96-dfd1-40df-8b93-a781b794b42d` / `jackson-pollock-q37571`, found:

- 112 artwork records; 0 attached primary images.
- 34 paintings, 66 drawings, 10 prints and 2 records with unknown work type.
- Source connections: Met 62, NGA 19, MoMA 19, Chicago 5, Tate 4, Cleveland 1;
  two records have no external object identifier. Duplicate identifier schemes
  for a Met and a Chicago object do not represent additional artworks.

[Exact local inventory](local-inventory.json) preserves IDs, titles, dates,
accessions, review state and source identifiers. This is a catalogue inventory,
not a claim that all 112 images received independent rights review. Production
was not independently audited in this pass.

## Verified source findings

| Work / source | Current evidence | Decision |
| --- | --- | --- |
| Chicago: The Key, Greyed Rainbow and three Untitled records | All five exact object API records set `is_public_domain=false` and credit Pollock-Krasner Foundation / ARS. [Captured response](chicago-rights.json). | Hold pending permission. |
| Met: Autumn Rhythm: Number 30, 1950 | `isPublicDomain=false`, empty image fields, explicit 2026 Foundation / ARS rights notice. [Captured response](met-autumn-rhythm-rights.json). | Hold pending permission. |
| Met: Number 28, 1950 | Same restricted status and empty image fields. [Captured response](met-number-28-rights.json). | Hold pending permission. |
| Cleveland: Number 5, 1950 | `share_license_status=Copyrighted`; image dictionary empty; Foundation / ARS copyright. [Captured response](cleveland-rights.json). | Hold pending permission. |
| NGA: Number 1, 1950 (Lavender Mist) | [Current museum page](https://www.nga.gov/artworks/55819-number-1-1950-lavender-mist) disables image download and directs users to request image usage. | Hold; conflicting third-party rights labels described below. |
| MoMA: One: Number 31, 1950 | [Museum object page](https://www.moma.org/collection/works/78386) directs image reproduction requests to Art Resource or Scala Archives. No open image licence was established. | Hold pending permission. |
| Met: Untitled, 1982.147.31 | [Museum object page](https://www.metmuseum.org/art/collection/search/482452) explicitly credits 2026 Foundation / ARS rights. Local title retains its supplied qualifier, Untitled (Figure Composition). | Hold pending permission. |

Additional lead: Whitney's [Number 17, 1950 / Fireworks](https://whitney.org/collection/works/12163)
also has an explicit Foundation / ARS reproduction notice. Its site-wide Open
Access link is not an object-specific licence. No new artwork was imported.
Tate's Yellow Islands page could not be fetched in this pass; no new clearance
conclusion is asserted for it.

### Lavender Mist: conflicting evidence

[Google Arts & Culture](https://artsandculture.google.com/asset/number-1-1950-lavender-mist/UwGSV9KKMohFmA)
labels the reproduction CC0. However, NGA's current exact object page does not
offer an open-access download and directs image-use requests to the museum.
The [Commons reproduction](https://commons.wikimedia.org/wiki/File:Lavande_Mist,_Pollock,_NGA_Washington_1950.png)
uses a life-plus-60-years rationale and explicitly requests a United States
public-domain tag. This does not resolve clearance for Artline's intended use.
The conflict is retained for clarification, not silently converted into an
approved public-domain record.

## What unlocks the upload

The [Pollock-Krasner Foundation's current resources page](https://www.pkf.org/about/resources/)
directs Pollock reproduction/licensing requests to Artists Rights Society and
states that ARS does not supply high-resolution images. Artwork permission and
the exact supplied reproduction therefore need to be resolved together.

A practical initial selection is Autumn Rhythm, Greyed Rainbow, Number 5, 1950,
Lavender Mist and One: Number 31, 1950. These already have catalogue records.
Obtain permission covering Artline's public/potentially commercial web use and
the chosen image files, including territory, duration, credits and resizing
terms. Once evidence is available, prepare the normal bounded derivatives,
preserve licence/source provenance, attach to the existing records and verify
served bytes. Catalogue review state must remain unchanged.

On 19 September 2026, the user confirmed that no existing licence or permission
is available. The checked images remain held pending documented clearance for
Artline's use. No licensing request was sent, fee incurred or permission assumed;
no images were uploaded and no catalogue records were changed.
