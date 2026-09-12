# European catalogue expansion

Prepared for the Artline owner on 9 September 2026. Scope: selected museum-connected paintings created by 1970, existing painter identities, local factual research only. This supplements the earlier European reports rather than replacing them.

## Result

Added 115 paintings by 24 existing painters: 85 National Gallery holdings, 29 Orsay-held works and one Pissarro deposited in Grenoble. Grenoble is the only new museum. The database now contains 715 artworks and 56 institutions, with 231 new citations. Every new artwork has a supported creation date, material and dimensions and remains in review. No duplicate works, images, publication, current-display assertions or masterpiece-list promotions were added. These are verified local import counts, not the museums’ total collections.

## What the catalogues unlocked

The National Gallery’s documented API supplied exact accession identities and structured object facts. Sixteen same-day responses were reused; only two corrected-name searches required new response snapshots. Across 18 bounded queries, 251 candidates produced 86 initial selections; one additional dating exclusion left 85 for import. The remaining 165 were prior records, qualified creators, loans, non-selected media or dates requiring review. No pagination or collection-wide download was performed. [National Gallery API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api).

Verified source-specific names recovered three Caravaggios, eight Degas oil paintings, nine Cézannes and seven Turners. Exact artist identities and current direct attributions remain required; the unrelated Polidoro da Caravaggio is not merged into Caravaggio. Official artist records: [Caravaggio](https://www.nationalgallery.org.uk/artists/michelangelo-merisi-da-caravaggio), [Degas](https://www.nationalgallery.org.uk/artists/hilaire-germain-edgar-degas), [Cézanne](https://www.nationalgallery.org.uk/artists/paul-cezanne), [Turner](https://www.nationalgallery.org.uk/artists/joseph-mallord-william-turner).

Orsay’s individual records add accession numbers, alternate titles, conservation institutions, assignment histories and selected bibliography references. Examples include Cézanne’s Card Players, Renoir’s Moulin de la Galette, Degas’s Dance Class and Van Gogh’s Rhône Starry Night. Full source links appear in the object catalogue; no museum essays were copied.

## Distinctions preserved

Orsay is responsible for Pissarro RF 1979 9, but the source explicitly records conservation in Grenoble and a deposit there from 1981. The artwork is therefore linked to Grenoble. Corot RF 3745 is held at Orsay on deposit while Louvre responsibility is retained in the evidence. These are holding/deposit records, not current room locations or museum ownership claims. [Pissarro record](https://www.musee-orsay.fr/fr/oeuvres/la-maison-de-la-folie-eragny-422), [Corot record](https://www.musee-orsay.fr/en/artworks/latelier-de-corot-234), [Grenoble institutional geography](https://www.museedegrenoble.fr/1931-informations-pratiques.htm).

Cézanne’s Card Players follows the current object date 1893-1896. Van Gogh’s Rhône Starry Night is the 1888 canvas, not the separate 1889 MoMA work; its 1975 donation and 1995 end of usufruct are not creation dates. Turner’s Fighting Temeraire was painted in 1839 even though its full title names the subject event in 1838. [Card Players](https://www.musee-orsay.fr/fr/oeuvres/les-joueurs-de-cartes-1312), [Rhône Starry Night](https://www.musee-orsay.fr/fr/oeuvres/la-nuit-etoilee-78696), [Fighting Temeraire](https://www.nationalgallery.org.uk/paintings/joseph-mallord-william-turner-the-fighting-temeraire/).

Poussin’s Eucharist exposed a parser issue: the first Overall measurement had no display text, hiding a later valid entry. The collector now selects the nonempty object measurement, 96 x 121.2 cm, corroborated by the museum’s 22 March 2024 announcement. The older 95.5 x 121 cm alternative remains noted. Titian’s Tribute Money is deferred because the literal date permits a possible start in the 1540s, outside the API’s 1560-1568 interval. [Eucharist acquisition record](https://www.nationalgallery.org.uk/about-us/press-and-media/press-releases-archive/the-national-gallery-acquires-poussin-s-eucharist-showing-the-last-supper-from-his-first-cycle-of-pictures-of-the-seven-sacraments), [Tribute Money](https://www.nationalgallery.org.uk/paintings/titian-the-tribute-money).

## Access and reuse limits

National Gallery structured metadata is CC0; narrative and image licences are different. Orsay’s legal notice does not establish an open metadata or image licence and includes private-use and publication restrictions. Its factual records remain in local review; public or commercial reuse needs a separate rights assessment. No images were fetched or cleared by this research. [National Gallery licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences), [Orsay legal notice](https://www.musee-orsay.fr/fr/mentions-legales).

Courbet’s Burial at Ornans has complete indexed primary technical evidence but direct access failed; that limitation is retained. Other Orsay records were directly verified, with a single alternate-language fallback where necessary. Olympia and another Corot remain excluded after bounded access failures. Reproductions, sculpture, drawings and previous inventory matches were excluded. This batch is not an exhaustive European survey. [Courbet official record](https://www.musee-orsay.fr/fr/oeuvres/un-enterrement-ornans-924).

## Import and verification

The Go importer accepts only the reviewed snapshot checksum and existing painter authorities. It uses indexed exact identities, a serializable transaction, a rollback preview and review-only inserts. A private PostgreSQL backup was taken before apply; its archive contents were checked, but a full restore rehearsal was not performed. All Go tests and vet pass. The unchanged identity query also passes a 100,000-row fixture plan check; this is not a ten-million-row performance certification.

The dry run changed none of the 17 recorded catalogue/audit counts. Applied replay of the new batch and both earlier batches added nothing and left those counts unchanged. Live authenticated API checks return National Gallery 143 local works, Orsay 32 and Grenoble one. Combined Monet/Pissarro and France/UK filters include Grenoble correctly. Anonymous preview is denied, and the unpublished catalogue stays out of public museum results. No commit, deployment or infrastructure change was made.
