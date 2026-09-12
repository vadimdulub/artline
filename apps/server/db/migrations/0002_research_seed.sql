INSERT INTO countries (code, name, region_code) VALUES
  ('DK', 'Denmark', 'northern-europe'),
  ('FR', 'France', 'western-europe'),
  ('IT', 'Italy', 'southern-europe'),
  ('JP', 'Japan', 'eastern-asia'),
  ('NL', 'Netherlands', 'western-europe'),
  ('NO', 'Norway', 'northern-europe'),
  ('SE', 'Sweden', 'northern-europe')
ON CONFLICT (code) DO NOTHING;

INSERT INTO movements (slug, name, start_year, end_year, color_hex, status) VALUES
  ('early-renaissance', 'Early Renaissance', 1300, 1490, '#55705e', 'review'),
  ('northern-renaissance', 'Northern Renaissance', 1400, 1550, '#55798f', 'review'),
  ('high-renaissance', 'High Renaissance', 1490, 1530, '#234e9a', 'review'),
  ('baroque', 'Baroque', 1580, 1750, '#873d48', 'review'),
  ('ukiyo-e', 'Ukiyo-e', 1603, 1868, '#79629a', 'review'),
  ('impressionism', 'Impressionism', 1860, 1890, '#b56c3f', 'review'),
  ('skagen-painters', 'Skagen Painters', 1870, 1910, '#3f7180', 'review'),
  ('symbolism', 'Symbolism', 1880, 1910, '#6b557c', 'review'),
  ('modernism', 'Modernism', 1890, 1970, '#a14f55', 'review')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO sources (slug, name, source_type, base_url, priority) VALUES
  ('national-gallery-london', 'The National Gallery, London', 'collection_page', 'https://www.nationalgallery.org.uk', 10),
  ('louvre', 'Musée du Louvre', 'collection_page', 'https://www.louvre.fr', 10),
  ('rijksmuseum', 'Rijksmuseum', 'museum_api', 'https://www.rijksmuseum.nl', 10),
  ('british-museum', 'The British Museum', 'collection_page', 'https://www.britishmuseum.org', 10),
  ('musee-orsay', 'Musée d’Orsay', 'collection_page', 'https://www.musee-orsay.fr', 10),
  ('moderna-museet', 'Moderna Museet', 'collection_page', 'https://www.modernamuseet.se', 10),
  ('skagens-museum', 'Skagens Museum', 'collection_page', 'https://skagensmuseum.dk', 10),
  ('munch', 'MUNCH', 'collection_page', 'https://www.munch.no', 10)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO artists (
  slug, display_name, sort_name, normalized_name,
  birth_year, death_year, birth_display, death_display,
  timeline_start_year, timeline_end_year, timeline_display, timeline_basis,
  influence_review_state, movement_review_state, geography_review_state, status
) VALUES
  ('giotto', 'Giotto', 'Giotto', 'giotto', 1267, 1337, 'c. 1267', '1337', 1267, 1337, 'c. 1267–1337', 'life', 'not_reviewed', 'classified', 'classified', 'review'),
  ('jan-van-eyck', 'Jan van Eyck', 'van Eyck, Jan', 'jan van eyck', NULL, 1441, NULL, '1441', 1422, 1441, 'active 1422–1441', 'activity', 'not_reviewed', 'classified', 'classified', 'review'),
  ('leonardo-da-vinci', 'Leonardo da Vinci', 'Leonardo da Vinci', 'leonardo da vinci', 1452, 1519, '1452', '1519', 1452, 1519, '1452–1519', 'life', 'not_reviewed', 'classified', 'classified', 'review'),
  ('artemisia-gentileschi', 'Artemisia Gentileschi', 'Gentileschi, Artemisia', 'artemisia gentileschi', 1593, 1654, '1593', 'c. 1654', 1593, 1654, '1593–c. 1654', 'life', 'not_reviewed', 'classified', 'classified', 'review'),
  ('rembrandt', 'Rembrandt van Rijn', 'Rembrandt van Rijn', 'rembrandt van rijn', 1606, 1669, '1606', '1669', 1606, 1669, '1606–1669', 'life', 'not_reviewed', 'classified', 'classified', 'review'),
  ('katsushika-hokusai', 'Katsushika Hokusai', 'Katsushika Hokusai', 'katsushika hokusai', 1760, 1849, '1760', '1849', 1760, 1849, '1760–1849', 'life', 'not_reviewed', 'classified', 'classified', 'review'),
  ('claude-monet', 'Claude Monet', 'Monet, Claude', 'claude monet', 1840, 1926, '1840', '1926', 1840, 1926, '1840–1926', 'life', 'not_reviewed', 'classified', 'classified', 'review'),
  ('p-s-kroyer', 'P. S. Krøyer', 'Krøyer, P. S.', 'p s krøyer', 1851, 1909, '1851', '1909', 1851, 1909, '1851–1909', 'life', 'not_reviewed', 'classified', 'classified', 'review'),
  ('anna-ancher', 'Anna Ancher', 'Ancher, Anna', 'anna ancher', 1859, 1935, '1859', '1935', 1859, 1935, '1859–1935', 'life', 'not_reviewed', 'classified', 'classified', 'review'),
  ('hilma-af-klint', 'Hilma af Klint', 'af Klint, Hilma', 'hilma af klint', 1862, 1944, '1862', '1944', 1862, 1944, '1862–1944', 'life', 'not_reviewed', 'classified', 'classified', 'review'),
  ('edvard-munch', 'Edvard Munch', 'Munch, Edvard', 'edvard munch', 1863, 1944, '1863', '1944', 1863, 1944, '1863–1944', 'life', 'not_reviewed', 'classified', 'classified', 'review')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO artist_movements (artist_id, movement_id, role)
SELECT a.id, m.id, 'primary'
FROM (VALUES
  ('giotto', 'early-renaissance'),
  ('jan-van-eyck', 'northern-renaissance'),
  ('leonardo-da-vinci', 'high-renaissance'),
  ('artemisia-gentileschi', 'baroque'),
  ('rembrandt', 'baroque'),
  ('katsushika-hokusai', 'ukiyo-e'),
  ('claude-monet', 'impressionism'),
  ('p-s-kroyer', 'skagen-painters'),
  ('anna-ancher', 'skagen-painters'),
  ('hilma-af-klint', 'modernism'),
  ('edvard-munch', 'symbolism')
) AS seed(artist_slug, movement_slug)
JOIN artists a ON a.slug = seed.artist_slug
JOIN movements m ON m.slug = seed.movement_slug
ON CONFLICT (artist_id, movement_id) DO NOTHING;

INSERT INTO artist_countries (artist_id, country_code, relationship_type, is_primary)
SELECT a.id, seed.country_code::char(2), 'cultural_affiliation', true
FROM (VALUES
  ('giotto', 'IT'),
  ('jan-van-eyck', 'NL'),
  ('leonardo-da-vinci', 'IT'),
  ('artemisia-gentileschi', 'IT'),
  ('rembrandt', 'NL'),
  ('katsushika-hokusai', 'JP'),
  ('claude-monet', 'FR'),
  ('p-s-kroyer', 'DK'),
  ('anna-ancher', 'DK'),
  ('hilma-af-klint', 'SE'),
  ('edvard-munch', 'NO')
) AS seed(artist_slug, country_code)
JOIN artists a ON a.slug = seed.artist_slug
ON CONFLICT (artist_id, country_code, relationship_type) DO NOTHING;

INSERT INTO citations (entity_type, entity_id, field_name, source_id, source_url, evidence_note, retrieved_at)
SELECT 'artist', a.id, 'timeline_dates', s.id, seed.source_url, 'Starter authority link; record remains in review.', '2026-09-07T00:00:00Z'::timestamptz
FROM (VALUES
  ('giotto', 'national-gallery-london', 'https://www.nationalgallery.org.uk/artists/giotto'),
  ('jan-van-eyck', 'national-gallery-london', 'https://www.nationalgallery.org.uk/artists/jan-van-eyck'),
  ('leonardo-da-vinci', 'louvre', 'https://www.louvre.fr/en/explore/the-palace/leonardo-da-vinci-at-the-louvre'),
  ('artemisia-gentileschi', 'national-gallery-london', 'https://www.nationalgallery.org.uk/artists/artemisia-gentileschi'),
  ('rembrandt', 'rijksmuseum', 'https://www.rijksmuseum.nl/en/stories/rembrandt-van-rijn'),
  ('katsushika-hokusai', 'british-museum', 'https://www.britishmuseum.org/collection/term/BIOG3622'),
  ('claude-monet', 'musee-orsay', 'https://www.musee-orsay.fr/en/ressources/artists-personalities-catalog/claude-monet-1840-1926'),
  ('p-s-kroyer', 'skagens-museum', 'https://skagensmuseum.dk/en/artists/p-s-kroyer/'),
  ('anna-ancher', 'skagens-museum', 'https://skagensmuseum.dk/en/artists/anna-ancher/'),
  ('hilma-af-klint', 'moderna-museet', 'https://www.modernamuseet.se/stockholm/en/exhibitions/hilma-af-klint/'),
  ('edvard-munch', 'munch', 'https://www.munch.no/en/edvard-munch/')
) AS seed(artist_slug, source_slug, source_url)
JOIN artists a ON a.slug = seed.artist_slug
JOIN sources s ON s.slug = seed.source_slug;

