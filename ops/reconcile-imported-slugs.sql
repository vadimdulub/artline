-- The API proxy accepts ASCII route components. Preserve source display names.
-- Only seven automatically imported review slugs need this normalization;
-- the existing slug-history trigger preserves their previous URL identities.
BEGIN;
SELECT pg_advisory_xact_lock(hashtext('artline-curated-import'));
UPDATE artists SET slug=translate(slug,'øł','ol'),revision=revision+1,updated_at=now()
WHERE created_by='local-curated-import' AND status='review'
AND slug IN ('zdzisław-beksinski-q169246','roman-opałka-q451015',
 'vilhelm-hammershøi-q380706','marie-krøyer-q273933','aleksander-orłowski-q937911',
 'władysław-strzeminski-q2471547','christen-købke-q381458');
COMMIT;
