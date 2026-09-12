-- Install before bulk import. The migration runner uses a transaction; on a
-- populated production catalogue, build these indexes CONCURRENTLY in a separate
-- approved maintenance step first. IF NOT EXISTS then avoids a blocking rebuild.
CREATE INDEX IF NOT EXISTS artwork_artists_artist_work_idx
 ON artwork_artists(artist_id,artwork_id) INCLUDE(attribution_role,representative_order);
