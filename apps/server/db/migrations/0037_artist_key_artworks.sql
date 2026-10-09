-- An editorial opening work is independent of catalogue metadata and publication.
-- The composite FK preserves the exact object/creator/attribution relationship.
CREATE TABLE artist_key_artworks (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 artist_id uuid NOT NULL UNIQUE REFERENCES artists(id),
 artwork_id uuid NOT NULL,
 attribution_role text NOT NULL,
 selection_basis text NOT NULL CHECK (selection_basis IN
   ('notable_work','museum_highlight','curated_representative','editorial_representative')),
 source_urls text[] NOT NULL CHECK (cardinality(source_urls)>0),
 evidence_json jsonb NOT NULL CHECK (jsonb_typeof(evidence_json)='object'),
 selection_batch text NOT NULL,
 selected_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY (artwork_id,artist_id,attribution_role)
   REFERENCES artwork_artists(artwork_id,artist_id,attribution_role)
);
CREATE INDEX artist_key_artworks_artwork_idx ON artist_key_artworks(artwork_id);
CREATE TRIGGER artist_key_artworks_audit AFTER INSERT OR UPDATE OR DELETE
 ON artist_key_artworks FOR EACH ROW EXECUTE FUNCTION artline_audit_record('artist_key_artwork');
-- Artist detail is served with no-store. This table is not a dependency of any
-- cached directory/count query; selecting a key work changes neither membership
-- nor visibility. Those are still evaluated from the current artwork at read time.
