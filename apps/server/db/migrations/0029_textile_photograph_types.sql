-- Selected museum textiles and photographs retain their actual classifications.
-- This does not change import eligibility, image rights or publication status.
ALTER TABLE artworks DROP CONSTRAINT artworks_work_type_check;
ALTER TABLE artworks ADD CONSTRAINT artworks_work_type_check CHECK
 (work_type IN ('painting','fresco','manuscript_illumination','drawing',
               'watercolor','print','ceramic','metalwork','sculpture',
               'calligraphy','textile','photograph','unknown'));
