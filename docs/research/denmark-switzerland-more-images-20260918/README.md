# Denmark and Switzerland — more pictures, 18 September 2026

Follow-up to the user's request to find more pictures for the
[selected museum batch](../denmark-switzerland-museums-20260917/README.md).
Scope: the same 47 artwork identities; no new artwork or artist imports,
publication, accepted holdings, display assertions, commits or deployment.

## Selected delivery

Nine additional reproductions, attached to the same existing review records
in local and production catalogues:

| Museum | Artist and work | Reproduction basis |
| --- | --- | --- |
| Basel | Catharina van Hemessen, *Self-portrait at the Easel*, 1548 | Photographer Paradise Chronicle, CC BY-SA 4.0; inventory 1361 |
| Basel | Hans Holbein the Younger, *The Dead Christ in the Tomb*, 1521–1522 | Individual Yorck Project reproduction explicitly public domain; inventory 318 |
| Basel | Paul Klee, *Senecio*, 1922 | Photographer Sizzlipedia, CC BY-SA 4.0; inventory 1569 |
| Basel | Claude Monet, *La passerelle sur le bassin aux nymphéas*, 1919 | CC BY-SA 4.0 file; exact museum inventory G 1986.15 and primary public-domain permission |
| Basel | Ernst Ludwig Kirchner, *Stafelalp, Return of the Animals*, 1919 | Public-domain museum reproduction, independently available on Commons; inventory G 2017.10 |
| Basel | Franz Marc, *Fate of the Animals*, 1913 | Public-domain museum reproduction, independently available on Commons; inventory 1739 |
| Glyptotek | Claude Monet, *Shadows on the Sea. The Cliffs at Pourville*, 1882 | Public-domain Google Art Project / museum partner reproduction; MIN 1753 |
| Hirschsprung | Vilhelm Hammershøi, *An Old Woman*, 1886 | Public-domain Google Art Project / museum partner reproduction |
| Hirschsprung | Viggo Johansen, *Silent Night / Glade jul*, 1891 | Public-domain museum-register reproduction; inventory 205; file linked from museum-directed public selection |

This adds six Swiss and three Danish museum pictures. Combined with the prior
nine uploads, the two passes add **18 pictures**. The original 47-work scope has
one pre-existing picture and 28 remaining image gaps. Counts are media attachments,
not publication counts or a claim of nationwide completeness.

## Exact sources and rights

- [Catharina van Hemessen photograph](https://commons.wikimedia.org/wiki/File:Self-Portrait_with_easel%E2%80%93Catharina_van_Hemessen.jpg): self-published photographer licence, Basel collection/inventory and native object link; not the Hermitage or Michaelis replica.
- [Holbein reproduction](https://commons.wikimedia.org/wiki/File:The_Body_of_the_Dead_Christ_in_the_Tomb_by_Hans_Holbein_d._J.-Kunstmuseum_Basel.jpg): the individual picture is public domain; the Yorck compilation licence is distinct.
- [Klee photograph](https://commons.wikimedia.org/wiki/File:Senecio_(Baldgreis),_Klee_1080998.jpg): exact inventory and original yellow frame; photographer attribution and ShareAlike retained.
- [Basel Monet](https://commons.wikimedia.org/wiki/File:Monet_-_La_passerelle_sur_le_bassin_aux_nymph%C3%A9as,_1919.jpg), [Kirchner](https://commons.wikimedia.org/wiki/File:Kirchner_-_Stafelalp,_R%C3%BCckkehr_der_Tiere,_1919,_Inv._G_2017.10.jpg), [Marc](https://commons.wikimedia.org/wiki/File:Marc_-_Tierschicksale_(Die_B%C3%A4ume_zeigten_ihre_Ringe,_die_Tiere_ihre_Adern),_1913,_Inv._1739.jpg): original museum provenance and exact inventory matches. Prior captured native object and per-image public-domain labels are supplemented by the [museum's explicit reuse terms](https://download.kunstmuseumbasel.ch/app/snippets/infoClaim.html). The Monet file's CC BY-SA terms and uploader credit are retained too.
- [Glyptotek Monet](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Shadows_on_the_Sea._The_Cliffs_at_Pourville_-_Google_Art_Project.jpg), [Hammershøi](https://commons.wikimedia.org/wiki/File:Vilhelm_Hammersh%C3%B8i_-_An_old_woman_-_Google_Art_Project.jpg), [Johansen](https://commons.wikimedia.org/wiki/File:Viggo_Johansen_-_Glade_jul_-_1891.jpg): individual file permissions and partner/museum reproduction origins, not website-footer licences.

No requests were made to the previously denied Basel image endpoint or Commons
API. These are separately public Commons files, not alternate routes into a
restricted server. Only nine preselected published JPEG renditions were
downloaded; large original museum files were not exhaustively downloaded.

Attribution includes creator, title, artwork date, photo/source credits, source
and licence links, access date and the proportional resize/JPEG-compression
notice. Three CC BY-SA derivatives retain that licence. No crop, AI-generated
content or replacement artwork is used. Photo timestamps are not creation years.

## Unresolved pictures retained in the research queue

- Taeuber-Arp: the promising independently licensed *Équilibre* photograph says
  1932; the selected museum object says 1934. No title-only attachment.
- Wegmann: prior Jeanna Bauck dating conflict remains; the undated Hanna Lucia
  Bauck record stays undated.
- Hammershøi's *Bedroom*: correct-work DR image has insufficiently established
  photo permissions; the similarly named Ordrupgaard work and private study
  are not substituted. The museum's [acquisition account](https://www.hirschsprung.dk/en/new-works/new-work-by-vilhelm-hammershoi)
  documents the particular 1890 painting and bequest.
- Syberg: no cleared exact reproduction found; the 1916 *Skovparti* is a different work.
- MCBA: Borgeaud's Commons file has an explicitly unknown photo source; the
  Biéler lead traces to Pinterest; Gleyre's museum-sourced photograph does not
  resolve the permission conflict. MCBA's [terms](https://www.mcba.ch/politique-de-confidentialite/)
  do not provide a blanket public/commercial image licence. No MCBA image was
  copied on artwork age alone.
- Five uncertain-date works and remaining protected modern works stay held.
  `held.json` records all 28 unresolved image gaps; existing records are not deleted.

## Recovery and verification

Before attachment, both targets were audited read-only and full backups verified:

- Local dump, SHA-256, scoped artwork/artist/location preimages:
  `/Users/vadimdulub/Library/Application Support/Artline/backups/denmark-switzerland-more-images-20260918/`.
- Cloud SQL backup `1789718130079`, `SUCCESSFUL`, project `artline-508319`.

`image-selection.json` is the preserved first draft. The applied plan is
`image-selection-v2.json`, which adds the explicit Commons uploader attribution
to the Basel Monet image. Its SHA-256 is
`30f5a0a13fe8326d6a6554347e102dae71696094fa1c351cf2871b453c2c0f7a`.
`image-visual-review.json` pins the nine visually inspected derivative hashes.

The uploader checks preimages under row locks, refuses to replace an existing
image, verifies bucket checksums and preserves non-image metadata. Rights evidence
is stored per media record. Derivatives are at most 100,000 bytes; originals of
the selected renditions remain under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/denmark-switzerland-more-images-20260918/`.
Temporary contact sheets are outside Documents.

Evidence files: `audit.json`, `file-evidence.json`, `extra-file-evidence.json`,
`captures/`, `images-prepared/`, `image-upload-summary.json`, `verification.json`
and `public-verification.json`. Generated evidence follows existing ignore rules
and is preserved on disk, not committed. Six offline Python DK/CH tests and five
Go image-preparer tests cover licence scope, bounded previews, eligible/missing
selection, host restrictions, ShareAlike, compression and denied-route exclusion.
No test fixtures or test databases were created. No scale/load-test claim is made.

Final checks passed: nine attachments in each database, all 47 artwork records'
non-image metadata and artist/location assertions preserved, and exact local/cloud
media parity. All nine production image URLs returned JPEGs with the expected
byte size and SHA-256. All records retain their prior review/publication states.
