-- The illustrated covering index needs a current visibility map. Waiting for
-- the default 20% dead tuples allowed tens of thousands of heap fetches per
-- discovery read after imports. These table-local settings require no restart.
ALTER TABLE artworks SET (
 autovacuum_vacuum_scale_factor=0.02,
 autovacuum_vacuum_threshold=1000,
 autovacuum_vacuum_insert_scale_factor=0.02,
 autovacuum_vacuum_insert_threshold=1000,
 autovacuum_analyze_scale_factor=0.02,
 autovacuum_analyze_threshold=500
);
