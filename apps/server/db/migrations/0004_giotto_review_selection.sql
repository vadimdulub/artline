-- A new, explicitly reviewed-in-progress selection. This is not the missing prototype export.
INSERT INTO sources(slug,name,source_type,base_url,priority) VALUES
 ('scrovegni-chapel','Scrovegni Chapel, Padua','collection_page','https://cappelladegliscrovegni.it',10),
 ('wikimedia-commons','Wikimedia Commons','collection_page','https://commons.wikimedia.org',50)
ON CONFLICT(slug) DO NOTHING;

UPDATE artists SET display_name='Giotto di Bondone',normalized_name='giotto di bondone',
 timeline_start_year=1265,birth_year=1265,birth_display='c. 1265',timeline_display='c. 1265–1337',
 biography_md='Giotto was an Italian painter whose figures have a sense of weight, emotion, and presence within architectural spaces. He worked mainly in Florence and also received commissions in Padua and Naples. His surviving fresco cycles include the Scrovegni Chapel in Padua and the Bardi and Peruzzi chapels in Florence. In Padua, Enrico Scrovegni commissioned the chapel decoration, which the institution dates to 1303–1305. Scenes from the lives of Mary and Christ cover the walls, while the Last Judgement occupies the entrance wall. His birth date is approximate; the National Gallery gives about 1265.',
 revision=revision+1,updated_at=now()
WHERE slug='giotto' AND revision=1 AND status='review' AND biography_md IS NULL;

INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at)
SELECT 'artist',a.id,v.field_name,s.id,v.url,v.note,'2026-09-07T00:00:00Z'::timestamptz
FROM (VALUES
 ('biography','national-gallery-london','https://www.nationalgallery.org.uk/artists/giotto','Original summary; editor review remains required. The authority gives a birth date of about 1265, whereas the initial seed and the supplied prototype screenshot used c. 1267.'),
 ('geography','scrovegni-chapel','https://cappelladegliscrovegni.it/index.php/en/la-cappella-di-giotto','The chapel in Padua dates its fresco decoration to 1303–1305.'),
 ('identity','national-gallery-london','https://www.nationalgallery.org.uk/artists/giotto','Museum artist authority record.')
) v(field_name,source_slug,url,note)
JOIN sources s ON s.slug=v.source_slug CROSS JOIN artists a WHERE a.slug='giotto';

INSERT INTO artworks(slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,creation_place_display,current_location_text,location_checked_at,status)
SELECT v.slug,v.title,lower(v.title),'1303–1305',1303,1305,'range','fresco','Fresco','Padua, Italy','Scrovegni Chapel, Padua','2026-09-07T00:00:00Z'::timestamptz,'review'
FROM (VALUES
 ('giotto-lamentation','Lamentation'),
 ('giotto-kiss-of-judas','The Arrest of Christ (Kiss of Judas)'),
 ('giotto-meeting-at-the-golden-gate','Meeting at the Golden Gate'),
 ('giotto-massacre-of-the-innocents','Massacre of the Innocents'),
 ('giotto-last-judgement','Last Judgement')
)v(slug,title) ON CONFLICT(slug) DO NOTHING;

INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,representative_order)
SELECT aw.id,a.id,'primary',v.position
FROM (VALUES ('giotto-lamentation',1),('giotto-kiss-of-judas',2),('giotto-meeting-at-the-golden-gate',3),('giotto-massacre-of-the-innocents',4),('giotto-last-judgement',5))v(slug,position)
JOIN artworks aw ON aw.slug=v.slug CROSS JOIN artists a WHERE a.slug='giotto'
ON CONFLICT DO NOTHING;

INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at)
SELECT 'artwork',aw.id,'date_and_location',s.id,'https://cappelladegliscrovegni.it/index.php/en/la-cappella-di-giotto','Date follows the institution''s range for the chapel cycle; individual panel chronology and selection remain under review.','2026-09-07T00:00:00Z'::timestamptz
FROM artworks aw JOIN artwork_artists aa ON aa.artwork_id=aw.id JOIN artists a ON a.id=aa.artist_id
CROSS JOIN sources s WHERE a.slug='giotto' AND aw.slug LIKE 'giotto-%' AND s.slug='scrovegni-chapel';

INSERT INTO media_assets(storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at)
VALUES('local','/assets/artworks/giotto-kiss-of-judas.jpg',
 'https://commons.wikimedia.org/wiki/File:Giotto_-_Scrovegni_-_-31-_-_Kiss_of_Judas.jpg',
 'Wikimedia Commons','image/jpeg',3371,3287,5582576,'af6833ade7c10c328df2abe1108ec7a9374c5b8b72093a7ac328221675376a77',
 'Judas in a yellow cloak embraces Christ amid a crowd carrying torches and spears, against a deep blue sky.',
 'public_domain','Public Domain Mark 1.0 / PD-Art','https://creativecommons.org/publicdomain/mark/1.0/',
 'Giotto di Bondone','Giotto di Bondone, The Arrest of Christ. Scrovegni Chapel, Padua. Reproduction via Wikimedia Commons (PD-Art).',
 '2026-09-07T00:00:00Z','2026-09-07T00:00:00Z') ON CONFLICT(storage_path) DO NOTHING;
UPDATE artworks SET primary_media_id=(SELECT id FROM media_assets WHERE storage_path='/assets/artworks/giotto-kiss-of-judas.jpg')
WHERE slug='giotto-kiss-of-judas' AND primary_media_id IS NULL;

INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at)
SELECT 'artwork',aw.id,'image_rights',s.id,
 'https://commons.wikimedia.org/wiki/File:Giotto_-_Scrovegni_-_-31-_-_Kiss_of_Judas.jpg',
 'File page labels this reproduction PD-Art / Public Domain Mark. Its object date is 1304–1306; the displayed range follows the holding institution''s 1303–1305 cycle date. Conflict retained for editor review.',
 '2026-09-07T00:00:00Z'::timestamptz
FROM artworks aw CROSS JOIN sources s WHERE aw.slug='giotto-kiss-of-judas' AND s.slug='wikimedia-commons';
