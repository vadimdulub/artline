package atlas

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// RefreshBrowseBatch only writes derived browse rows. Claim markers first, then
// read sources in a NEW READ COMMITTED statement. A source writer that collides
// with these markers must leave a new marker after we commit, never lose it.
func RefreshBrowseBatch(ctx context.Context, pool *pgxpool.Pool, limit int) (int, error) {
	if limit < 1 || limit > 5000 {
		return 0, fmt.Errorf("browse refresh batch must contain 1–5000 IDs")
	}
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.ReadCommitted})
	if err != nil {
		return 0, err
	}
	defer tx.Rollback(context.WithoutCancel(ctx))
	// One production refresher at a time, even when Cloud Run has several
	// instances. Readers never wait for this maintenance lock.
	var locked bool
	if err = tx.QueryRow(ctx, "SELECT pg_try_advisory_xact_lock(202610120054)").Scan(&locked); err != nil || !locked {
		return 0, err
	}
	rows, err := tx.Query(ctx, `SELECT artwork_id::text FROM artwork_atlas_dirty ORDER BY artwork_id FOR UPDATE SKIP LOCKED LIMIT $1`, limit)
	if err != nil {
		return 0, err
	}
	ids := []string{}
	for rows.Next() {
		var id string
		if err = rows.Scan(&id); err != nil {
			rows.Close()
			return 0, err
		}
		ids = append(ids, id)
	}
	err = rows.Err()
	rows.Close()
	if err != nil || len(ids) == 0 {
		return 0, err
	}
	if err = refreshClaimedBrowse(ctx, tx, ids); err != nil {
		return 0, err
	}
	if err = tx.Commit(ctx); err != nil {
		return 0, err
	}
	return len(ids), nil
}

func refreshClaimedBrowse(ctx context.Context, tx pgx.Tx, ids []string) error {
	_, err := tx.Exec(ctx, `WITH current_rows AS MATERIALIZED (
 SELECT * FROM artline_atlas_browse_rows($1::text[]::uuid[])
), removed AS (
 DELETE FROM artwork_atlas_projection p WHERE p.id=ANY($1::text[]::uuid[])
 AND NOT EXISTS(SELECT 1 FROM current_rows c WHERE c.id=p.id)
)
INSERT INTO artwork_atlas_projection SELECT * FROM current_rows
ON CONFLICT(id) DO UPDATE SET start_year=excluded.start_year,end_year=excluded.end_year,
gallery_priority=excluded.gallery_priority,primary_media_id=excluded.primary_media_id,
work_type=excluded.work_type,cultural_context=excluded.cultural_context,is_highlight=excluded.is_highlight`, ids)
	if err != nil {
		return err
	}
	if _, err = tx.Exec(ctx, "DELETE FROM artwork_atlas_dirty WHERE artwork_id=ANY($1::text[]::uuid[])", ids); err != nil {
		return err
	}
	return nil
}

// Called only by the production Cloud Run entry point. Local/read-only previews
// never start maintenance. CPU throttling may delay a batch; the live dirty
// overlay keeps reads correct even if this worker is stopped indefinitely.
func MaintainBrowse(ctx context.Context, pool *pgxpool.Pool) {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			batchCtx, cancel := context.WithTimeout(ctx, 4*time.Second)
			_, err := RefreshBrowseBatch(batchCtx, pool, 500)
			cancel()
			if err != nil && ctx.Err() == nil {
				slog.Warn("atlas browse refresh deferred", "error", err)
			}
		}
	}
}
