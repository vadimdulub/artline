// Package testdb isolates catalogue fixtures from the owner's growing catalogue.
package testdb

import (
	"context"
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/db/migrations"
)

func Open(t *testing.T, db string) (*pgxpool.Pool, error) {
	t.Helper()
	ctx := context.Background()
	admin, err := pgxpool.New(ctx, db)
	if err != nil {
		return nil, err
	}
	schema := fmt.Sprintf("artline_catalog_test_%d", time.Now().UnixNano())
	quoted := pgx.Identifier{schema}.Sanitize()
	if _, err = admin.Exec(ctx, "CREATE SCHEMA "+quoted); err != nil {
		admin.Close()
		return nil, err
	}
	t.Cleanup(func() {
		defer admin.Close()
		if _, err := admin.Exec(ctx, "DROP SCHEMA "+quoted+" CASCADE"); err != nil {
			t.Error(err)
		}
	})
	cfg, err := pgxpool.ParseConfig(db)
	if err != nil {
		return nil, err
	}
	cfg.ConnConfig.RuntimeParams["search_path"] = schema + ",public"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		return nil, err
	}
	t.Cleanup(pool.Close)
	entries, err := migrations.Files.ReadDir(".")
	if err != nil {
		return nil, err
	}
	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".sql") {
			continue
		}
		b, e := migrations.Files.ReadFile(entry.Name())
		if e != nil {
			return nil, e
		}
		if _, e = pool.Exec(ctx, string(b)); e != nil {
			return nil, fmt.Errorf("fixture migration %s: %w", entry.Name(), e)
		}
	}
	return pool, nil
}
