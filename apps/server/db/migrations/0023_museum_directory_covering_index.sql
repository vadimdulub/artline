-- Counts and cover selection need only these narrow fields for a museum's
-- eligible works. Avoid fetching wide artwork rows for every directory card.
-- On an existing production catalogue deploy with CREATE INDEX CONCURRENTLY
-- outside a transaction, verify indisvalid, then record this filename. The
-- normal migration path below is suitable for transactional fresh installs.
CREATE INDEX IF NOT EXISTS artworks_museum_card_covering_idx
 ON artworks(current_institution_id, status, id)
 INCLUDE (title, creation_year_start, primary_media_id, unlinked_creator_label)
 WHERE status <> 'archived';
