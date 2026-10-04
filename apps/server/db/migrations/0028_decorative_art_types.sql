-- Islamic material culture includes objects beyond paintings. Keep each
-- museum's actual type instead of misclassifying tiles, vessels and calligraphy.
ALTER TABLE artworks DROP CONSTRAINT artworks_work_type_check;
ALTER TABLE artworks ADD CONSTRAINT artworks_work_type_check CHECK
 (work_type IN ('painting','fresco','manuscript_illumination','drawing',
               'watercolor','print','ceramic','metalwork','sculpture',
               'calligraphy','unknown'));
