package catalog

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func TestArtistIdentityReadOnly(t *testing.T) {
	dsn, dir := os.Getenv("ARTLINE_READONLY_DATABASE_URL"), os.Getenv("ARTLINE_PERFORMANCE_DIR")
	if dsn == "" || dir == "" {
		t.Skip("opt-in read-only identity comparison")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.MaxConns = 1
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly, IsoLevel: pgx.RepeatableRead})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	db := &performanceDB{Tx: tx}
	repo := &Repository{db: db}
	for _, slug := range []string{"rembrandt", "giotto"} {
		db.reads = nil
		started := time.Now()
		full, err := repo.ArtistBySlug(WithPublicRead(ctx), slug)
		if err != nil {
			t.Fatal(err)
		}
		fullMS := float64(time.Since(started).Microseconds()) / 1000
		fullReads := len(db.reads)
		fullJSON, _ := json.Marshal(full)
		db.reads = nil
		started = time.Now()
		identity, err := repo.ArtistIdentity(ctx, slug)
		if err != nil {
			t.Fatal(err)
		}
		identityMS := float64(time.Since(started).Microseconds()) / 1000
		identityJSON, _ := json.Marshal(identity)
		if identity.ID != full.ID || identity.Slug != full.Slug || identity.DisplayName != full.DisplayName || identity.EntityType != full.EntityType {
			t.Fatal("identity differs from public artist")
		}
		if len(db.reads) != 1 {
			t.Fatalf("identity performed %d queries", len(db.reads))
		}
		t.Logf("%s full=%0.2fms %d queries %d bytes; identity=%0.2fms %d query %d bytes", slug, fullMS, fullReads, len(fullJSON), identityMS, len(db.reads), len(identityJSON))
	}
	for _, status := range []string{"draft", "review", "published", "archived"} {
		var slug string
		if err = tx.QueryRow(ctx, "SELECT slug FROM artists WHERE status=$1 LIMIT 1", status).Scan(&slug); errors.Is(err, pgx.ErrNoRows) {
			continue
		}
		if err != nil {
			t.Fatal(err)
		}
		_, err = repo.ArtistIdentity(ctx, slug)
		if status == "archived" {
			if !errors.Is(err, ErrNotFound) {
				t.Fatal("archived identity exposed")
			}
		} else if err != nil {
			t.Fatal(err)
		}
	}
	var oldSlug, canonical string
	err = tx.QueryRow(ctx, "SELECT r.old_slug,a.slug FROM slug_redirects r JOIN artists a ON a.id=r.entity_id WHERE r.entity_type='artist' AND a.status<>'archived' LIMIT 1").Scan(&oldSlug, &canonical)
	if err == nil {
		identity, e := repo.ArtistIdentity(ctx, oldSlug)
		if e != nil || identity.Slug != canonical {
			t.Fatalf("alias did not resolve: %v", e)
		}
	} else if !errors.Is(err, pgx.ErrNoRows) {
		t.Fatal(err)
	}
	if _, err = repo.ArtistIdentity(ctx, "missing-perf-20261009"); !errors.Is(err, ErrNotFound) {
		t.Fatal("missing identity exposed")
	}
	var plan []byte
	if err = tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+artistIdentityQuery, "rembrandt").Scan(&plan); err != nil {
		t.Fatal(err)
	}
	if err = os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(dir, "artist-identity-after.json"), plan, 0600); err != nil {
		t.Fatal(err)
	}
}
