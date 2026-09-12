-- Additive museum foundation. No source is enabled and no record is published.
ALTER TABLE institutions ADD COLUMN slug text;
UPDATE institutions SET slug='collection-'||id::text WHERE slug IS NULL;
ALTER TABLE institutions ALTER COLUMN slug SET NOT NULL;
ALTER TABLE institutions ADD CONSTRAINT institutions_slug_key UNIQUE(slug);
ALTER TABLE institutions ADD COLUMN kind text NOT NULL DEFAULT 'museum' CHECK(kind IN ('museum','historic_site','foundation'));
ALTER TABLE institutions ADD COLUMN status text NOT NULL DEFAULT 'review' CHECK(status IN ('draft','review','published','archived'));
ALTER TABLE institutions ADD COLUMN description text NOT NULL DEFAULT '';

CREATE TABLE institution_venues (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  institution_id uuid NOT NULL REFERENCES institutions(id),
  slug text NOT NULL UNIQUE,
  name text NOT NULL,
  place_id uuid NOT NULL REFERENCES places(id),
  visit_url text NOT NULL CHECK(visit_url ~ '^https://'),
  source_url text NOT NULL CHECK(source_url ~ '^https://'),
  checked_at timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'review' CHECK(status IN ('draft','review','published','archived')),
  UNIQUE(id,institution_id)
);
CREATE INDEX institution_venues_institution_idx ON institution_venues(institution_id,status);
CREATE INDEX institution_venues_place_idx ON institution_venues(place_id);

CREATE TABLE source_institutions (
  source_id uuid NOT NULL REFERENCES sources(id),
  institution_id uuid NOT NULL REFERENCES institutions(id),
  PRIMARY KEY(source_id,institution_id)
);
CREATE TABLE source_connector_config (
  source_id uuid PRIMARY KEY REFERENCES sources(id),
  registry_id text UNIQUE,
  enabled boolean NOT NULL DEFAULT false,
  metadata_policy text NOT NULL DEFAULT 'manual_review',
  image_policy text NOT NULL DEFAULT 'manual_review',
  -- Adapters are not part of this milestone. Removing this guard needs a migration.
  CHECK(NOT enabled)
);

CREATE TABLE artwork_location_assertions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  artwork_id uuid NOT NULL REFERENCES artworks(id),
  claim_type text NOT NULL CHECK(claim_type IN ('holding','display')),
  institution_id uuid NOT NULL REFERENCES institutions(id),
  venue_id uuid,
  display_state text CHECK(display_state IN ('on_view','not_on_view','unknown')),
  context text CHECK(context IN ('collection','loan','storage','exhibition','unknown')),
  gallery text,
  source_id uuid NOT NULL REFERENCES sources(id),
  source_url text NOT NULL CHECK(source_url ~ '^https://'),
  evidence_note text NOT NULL,
  checked_at timestamptz NOT NULL,
  source_updated_at timestamptz,
  effective_from timestamptz,
  effective_to timestamptz,
  review_state text NOT NULL DEFAULT 'review' CHECK(review_state IN ('review','accepted','conflict','rejected')),
  superseded_by uuid REFERENCES artwork_location_assertions(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY(venue_id,institution_id) REFERENCES institution_venues(id,institution_id),
  CHECK(superseded_by IS NULL OR superseded_by<>id),
  CHECK(effective_from IS NULL OR effective_to IS NULL OR effective_from<=effective_to),
  CHECK((claim_type='holding' AND display_state IS NULL AND venue_id IS NULL) OR
        (claim_type='display' AND display_state IS NOT NULL AND (display_state<>'on_view' OR venue_id IS NOT NULL)))
);
CREATE UNIQUE INDEX artwork_one_current_holding ON artwork_location_assertions(artwork_id)
  WHERE claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL;
CREATE UNIQUE INDEX artwork_one_current_display ON artwork_location_assertions(artwork_id)
  WHERE claim_type='display' AND review_state='accepted' AND superseded_by IS NULL;
CREATE INDEX artwork_location_history_idx ON artwork_location_assertions(artwork_id,checked_at DESC);
CREATE INDEX artwork_display_venue_idx ON artwork_location_assertions(venue_id,display_state,checked_at)
  WHERE claim_type='display' AND review_state='accepted' AND superseded_by IS NULL;
CREATE INDEX artworks_institution_idx ON artworks(current_institution_id,status,id);

CREATE FUNCTION artline_sync_holding() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target uuid := COALESCE(NEW.artwork_id,OLD.artwork_id);
BEGIN
  IF TG_OP='UPDATE' AND NEW.artwork_id<>OLD.artwork_id THEN
    RAISE EXCEPTION 'assertion artwork identity is immutable';
  END IF;
  IF COALESCE(NEW.claim_type,OLD.claim_type)='holding' OR (TG_OP='UPDATE' AND OLD.claim_type='holding') THEN
    UPDATE artworks SET current_institution_id=(
      SELECT institution_id FROM artwork_location_assertions WHERE artwork_id=target
      AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL
    ) WHERE id=target AND current_institution_id IS DISTINCT FROM (
      SELECT institution_id FROM artwork_location_assertions WHERE artwork_id=target
      AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL
    );
  END IF;
  RETURN COALESCE(NEW,OLD);
END $$;
CREATE TRIGGER sync_holding AFTER INSERT OR UPDATE OR DELETE ON artwork_location_assertions
  FOR EACH ROW EXECUTE FUNCTION artline_sync_holding();
CREATE TRIGGER location_assertion_audit AFTER INSERT OR UPDATE OR DELETE ON artwork_location_assertions
  FOR EACH ROW EXECUTE FUNCTION artline_audit_record('location_assertion');

CREATE TABLE curated_collections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  institution_id uuid NOT NULL REFERENCES institutions(id),
  curator_kind text NOT NULL CHECK(curator_kind IN ('owner','museum')),
  title text NOT NULL,
  status text NOT NULL DEFAULT 'review' CHECK(status IN ('draft','review','published','archived')),
  revision integer NOT NULL DEFAULT 1 CHECK(revision>0),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(institution_id,curator_kind)
);
CREATE TABLE curated_collection_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  collection_id uuid NOT NULL REFERENCES curated_collections(id),
  artwork_id uuid NOT NULL REFERENCES artworks(id),
  position integer NOT NULL CHECK(position BETWEEN 1 AND 100000),
  reason text NOT NULL DEFAULT '' CHECK(length(reason)<=2000),
  source_id uuid REFERENCES sources(id),
  source_url text CHECK(source_url ~ '^https://'),
  checked_at timestamptz,
  UNIQUE(collection_id,artwork_id)
);
CREATE INDEX curated_items_order_idx ON curated_collection_items(collection_id,position,artwork_id);
CREATE INDEX curated_items_artwork_idx ON curated_collection_items(artwork_id,collection_id);
CREATE FUNCTION artline_require_highlight_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF (SELECT curator_kind FROM curated_collections WHERE id=NEW.collection_id)='museum'
     AND (NEW.source_id IS NULL OR NEW.source_url IS NULL OR NEW.checked_at IS NULL) THEN
    RAISE EXCEPTION 'museum highlights require designation evidence';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER highlight_evidence BEFORE INSERT OR UPDATE ON curated_collection_items
  FOR EACH ROW EXECUTE FUNCTION artline_require_highlight_evidence();
CREATE TRIGGER curated_collection_audit AFTER INSERT OR UPDATE OR DELETE ON curated_collections
  FOR EACH ROW EXECUTE FUNCTION artline_audit_record('curated_collection');
CREATE TRIGGER curated_item_audit AFTER INSERT OR UPDATE OR DELETE ON curated_collection_items
  FOR EACH ROW EXECUTE FUNCTION artline_audit_record('curated_item');

INSERT INTO countries(code,name,region_code) VALUES('US','United States','northern-america') ON CONFLICT(code) DO NOTHING;
INSERT INTO institutions(id,slug,name,normalized_name,kind,website_url,description)
SELECT md5('artline-museum-'||slug)::uuid,slug,name,lower(name),kind,url,description FROM (VALUES
 ('scrovegni-chapel','Scrovegni Chapel','historic_site','https://cappelladegliscrovegni.it/', 'Giotto’s fresco cycle in Padua. A historic site, not a movable museum collection.'),
 ('national-gallery-of-art','National Gallery of Art','museum','https://www.nga.gov/', 'The Washington collection represented here by Jan van Eyck and Leonardo da Vinci.'),
 ('uffizi','Uffizi Galleries','museum','https://www.uffizi.it/en/', 'The Florence collection, including Artemisia Gentileschi’s Judith.'),
 ('the-met','The Metropolitan Museum of Art','museum','https://www.metmuseum.org/', 'Explore the works currently catalogued in Artline, including two museum-designated highlights.'),
 ('skagens-museum','Skagens Museum','museum','https://skagensmuseum.dk/', 'Works by the painters associated with Skagen, including Anna Ancher and P. S. Krøyer.'),
 ('hilma-af-klint-foundation','Hilma af Klint Foundation','foundation','https://hilmaafklint.se/', 'A holding collection. No permanent public visiting venue is established in this atlas; check the foundation for exhibition information.'),
 ('national-museum-oslo','National Museum, Oslo','museum','https://www.nasjonalmuseet.no/en/', 'The Norwegian collection represented here by Edvard Munch’s 1893 Scream.')
) AS seed(slug,name,kind,url,description);

INSERT INTO places(id,name,normalized_name,country_code)
SELECT md5('artline-museum-place-'||name)::uuid,name,lower(name),code FROM (VALUES
 ('Padua','IT'),('Washington, DC','US'),('Florence','IT'),('New York','US'),('Skagen','DK'),('Oslo','NO')
) AS seed(name,code);
INSERT INTO institution_venues(id,institution_id,slug,name,place_id,visit_url,source_url,checked_at)
SELECT md5('artline-venue-'||v.slug)::uuid,i.id,v.slug,v.name,md5('artline-museum-place-'||city)::uuid,url,url,'2026-09-08T00:00:00Z' FROM (VALUES
 ('scrovegni-chapel','scrovegni-chapel-padua','Scrovegni Chapel','Padua','https://cappelladegliscrovegni.it/'),
 ('national-gallery-of-art','nga-west-building','West Building','Washington, DC','https://www.nga.gov/visit'),
 ('national-gallery-of-art','nga-east-building','East Building','Washington, DC','https://www.nga.gov/visit'),
 ('uffizi','uffizi-florence','The Uffizi','Florence','https://www.uffizi.it/en/the-uffizi'),
 ('the-met','met-fifth-avenue','The Met Fifth Avenue','New York','https://www.metmuseum.org/plan-your-visit'),
 ('the-met','met-cloisters','The Met Cloisters','New York','https://www.metmuseum.org/plan-your-visit'),
 ('skagens-museum','skagens-museum-skagen','Skagens Museum','Skagen','https://skagensmuseum.dk/'),
 ('national-museum-oslo','national-museum-oslo-building','The National Museum','Oslo','https://www.nasjonalmuseet.no/en/visit/locations/the-national-museum/')
) AS v(institution_slug,slug,name,city,url) JOIN institutions i ON i.slug=v.institution_slug;

-- Explicit object-to-institution mapping; original text/citations remain intact.
INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
SELECT aw.id,'holding',i.id,'collection',c.source_id,c.source_url,
 'Reviewed identity mapping from the existing sourced holding record. This does not assert current display or legal ownership.',aw.location_checked_at,'accepted'
FROM (VALUES
 ('giotto-lamentation','scrovegni-chapel'),('giotto-kiss-of-judas','scrovegni-chapel'),
 ('giotto-meeting-at-the-golden-gate','scrovegni-chapel'),('giotto-massacre-of-the-innocents','scrovegni-chapel'),('giotto-last-judgement','scrovegni-chapel'),
 ('van-eyck-annunciation','national-gallery-of-art'),('leonardo-ginevra-de-benci','national-gallery-of-art'),
 ('artemisia-judith-beheading-holofernes','uffizi'),('rembrandt-self-portrait-1660','the-met'),
 ('hokusai-great-wave','the-met'),('monet-bridge-over-a-pond-of-water-lilies','the-met'),
 ('kroyer-summer-evening-skagen','skagens-museum'),('anna-ancher-sunlight-blue-room','skagens-museum'),
 ('hilma-ten-largest-childhood-2','hilma-af-klint-foundation'),('munch-the-scream-1893','national-museum-oslo')
) AS mapping(artwork_slug,institution_slug)
JOIN artworks aw ON aw.slug=mapping.artwork_slug JOIN institutions i ON i.slug=mapping.institution_slug
JOIN LATERAL (SELECT source_id,source_url FROM citations WHERE entity_type='artwork' AND entity_id=aw.id
  AND field_name IN ('current_location','date_and_location') ORDER BY id LIMIT 1) c ON true
WHERE aw.current_institution_id IS NULL;

INSERT INTO source_institutions(source_id,institution_id)
SELECT DISTINCT source_id,institution_id FROM artwork_location_assertions;
INSERT INTO source_connector_config(source_id) SELECT DISTINCT source_id FROM source_institutions;
INSERT INTO curated_collections(institution_id,curator_kind,title)
SELECT i.id,k.kind,k.title FROM institutions i CROSS JOIN (VALUES ('owner','My must-see works'),('museum','Museum highlights')) AS k(kind,title);
INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
SELECT cc.id,aw.id,h.position,'Designated isHighlight=true by the Met Collection API; not a claim of current display.',s.id,h.url,'2026-09-08T00:00:00Z'
FROM (VALUES
 ('rembrandt-self-portrait-1660',1,'https://collectionapi.metmuseum.org/public/collection/v1/objects/437397'),
 ('monet-bridge-over-a-pond-of-water-lilies',2,'https://collectionapi.metmuseum.org/public/collection/v1/objects/437127')
) AS h(slug,position,url) JOIN artworks aw ON aw.slug=h.slug JOIN institutions i ON i.slug='the-met'
JOIN curated_collections cc ON cc.institution_id=i.id AND cc.curator_kind='museum' JOIN sources s ON s.slug='met-museum';
