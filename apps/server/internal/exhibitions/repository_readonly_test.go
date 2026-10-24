package exhibitions

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type observedQuery struct {
	SQL  string
	Args []any
}
type queryTrace struct{ Queries []observedQuery }

func (t *queryTrace) TraceQueryStart(ctx context.Context, _ *pgx.Conn, d pgx.TraceQueryStartData) context.Context {
	if strings.HasPrefix(d.SQL, "SELECT") || strings.HasPrefix(d.SQL, "WITH") {
		t.Queries = append(t.Queries, observedQuery{d.SQL, append([]any{}, d.Args...)})
	}
	return ctx
}
func (*queryTrace) TraceQueryEnd(context.Context, *pgx.Conn, pgx.TraceQueryEndData) {}

// Explicit opt-in reads the actual exhibition corpus. Never creates a database,
// runs migrations, changes rows or supplies fixtures to the local catalogue.
func TestExhibitionsReadOnlyCorpus(t *testing.T) {
	dsn := os.Getenv("ARTLINE_EXHIBITIONS_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("Set the explicitly read-only exhibition database URL")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal("invalid readonly DSN")
	}
	trace := &queryTrace{}
	cfg.ConnConfig.Tracer = trace
	cfg.MaxConns = 1
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	var readonly string
	if err = pool.QueryRow(ctx, "SHOW default_transaction_read_only").Scan(&readonly); err != nil || readonly != "on" {
		t.Fatalf("readonly connection required (setting %q): %v", readonly, err)
	}
	repo := NewRepository(pool)
	first, err := repo.List(ctx, Filter{Limit: 20})
	if err != nil {
		t.Fatal(err)
	}
	if first.Total < 1000 || !first.HasMore || len(first.Items) != 20 {
		t.Fatalf("full corpus missing: total=%d", first.Total)
	}
	next, err := repo.List(ctx, Filter{Limit: 20, After: first.NextCursor})
	if err != nil {
		t.Fatal(err)
	}
	seen := map[string]bool{}
	for _, raw := range append(first.Items, next.Items...) {
		var v struct{ ID string }
		if json.Unmarshal(raw, &v) != nil || seen[v.ID] {
			t.Fatal("invalid or overlapping keyset pages")
		}
		seen[v.ID] = true
	}
	for _, f := range []Filter{{Limit: 40}, {Limit: 10, Country: "France"}, {Limit: 10, City: "Paris"}, {Limit: 10, Country: "France", City: "Paris"}, {Limit: 10, Theme: "Abstraction"}, {Limit: 10, Person: "5b12c0e1-96db-5487-a9a2-624e865f158a"}, {Limit: 10, Source: "moma"}, {Limit: 10, Query: "Picasso"}, {Limit: 10, Institution: "729385eb-92b0-4cc8-9229-1ac3a46aee1f"}, {Limit: 10, Format: "online", State: "held"}} {
		page, err := repo.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		if f.Country != "" || f.City != "" {
			for _, raw := range page.Items {
				var row struct {
					Venues []struct{ Country, City string }
				}
				if err = json.Unmarshal(raw, &row); err != nil || len(row.Venues) == 0 {
					t.Fatal("matching venue missing", err)
				}
				venue := row.Venues[0]
				if (f.Country != "" && !strings.Contains(strings.ToLower(venue.Country), strings.ToLower(f.Country))) || (f.City != "" && !strings.Contains(strings.ToLower(venue.City), strings.ToLower(f.City))) {
					t.Fatalf("matching venue must lead the displayed stops: %+v, %+v", f, row.Venues)
				}
			}
		}
	}
	var id, artwork, artist string
	err = pool.QueryRow(ctx, "SELECT exhibition_id::text,artwork_id::text FROM exhibition_entries WHERE artwork_id IS NOT NULL LIMIT 1").Scan(&id, &artwork)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = repo.ByID(ctx, id); err != nil {
		t.Fatal(err)
	}
	entries, err := repo.Entries(ctx, id, "", 10)
	if err != nil || len(entries.Items) == 0 {
		t.Fatalf("entries unavailable: %v", err)
	}
	if _, err = repo.List(ctx, Filter{Limit: 10, Artwork: artwork}); err != nil {
		t.Fatal(err)
	}
	if err = pool.QueryRow(ctx, "SELECT artist_id::text FROM exhibition_participants WHERE artist_id IS NOT NULL LIMIT 1").Scan(&artist); err != nil {
		t.Fatal(err)
	}
	if _, err = repo.List(ctx, Filter{Limit: 10, Artist: artist}); err != nil {
		t.Fatal(err)
	}
	var historical string
	if err = pool.QueryRow(ctx, "SELECT id::text FROM exhibitions WHERE title='Royal Academy Summer Exhibition 1769' AND status<>'archived'").Scan(&historical); err != nil {
		t.Fatal(err)
	}
	leading, err := repo.Entries(ctx, historical, "", 2)
	if err != nil || len(leading.Items) != 2 || !leading.HasMore {
		t.Fatalf("historical painting page unavailable: %v", err)
	}
	following, err := repo.Entries(ctx, historical, leading.NextCursor, 20)
	if err != nil {
		t.Fatal(err)
	}
	entryIDs := map[string]bool{}
	previousRank := -1
	for i, raw := range append(leading.Items, following.Items...) {
		var entry struct{ ID, Image, Participation string }
		if err = json.Unmarshal(raw, &entry); err != nil || entryIDs[entry.ID] {
			t.Fatal("overlapping historical entry pages", err)
		}
		entryIDs[entry.ID] = true
		rank := 0
		if entry.Image == "" {
			rank += 2
		}
		if entry.Participation != "exhibited" {
			rank++
		}
		if (i < 2 && rank != 0) || rank < previousRank {
			t.Fatal("illustrated exhibited works must lead across page boundaries")
		}
		previousRank = rank
	}

	queries := append([]observedQuery{}, trace.Queries...)
	trace.Queries = nil
	report := []map[string]any{}
	for _, q := range queries {
		if !strings.Contains(q.SQL, "exhibition") {
			continue
		}
		var plan json.RawMessage
		if err = pool.QueryRow(ctx, "EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) "+q.SQL, q.Args...).Scan(&plan); err != nil {
			t.Fatal(err)
		}
		report = append(report, map[string]any{"sql": q.SQL, "args": q.Args, "plan": plan})
	}
	if dir := os.Getenv("ARTLINE_EXHIBITIONS_PLAN_OUTPUT"); dir != "" {
		if err = os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
		b, _ := json.MarshalIndent(map[string]any{"total": first.Total, "held": first.HeldTotal, "queries": report}, "", "  ")
		if err = os.WriteFile(filepath.Join(dir, "readonly-query-plans.json"), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	t.Logf("Verified %d exhibitions; %d exact query plans; keyset and relationship reads only", first.Total, len(report))
}
