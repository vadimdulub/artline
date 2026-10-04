package books

import (
	"context"
	"os"
	"reflect"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/timeline"
)

func TestMatchedExtentReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_BOOKS_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue audit not requested")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	f := Filter{Range: Bounds, Authors: []string{"Leo Tolstoy"}, Preview: true, Limit: 1}
	first, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if !first.HasMore {
		t.Fatal("expected more than one matching book")
	}
	var earliest, latest *int
	err = db.QueryRow(ctx, `SELECT min(b.start_year),max(b.end_year)`+predicate, f.Start, f.End, f.Preview, "", f.Authors, false, false, []string{}, []string{}, []string{}).Scan(&earliest, &latest)
	if err != nil {
		t.Fatal(err)
	}
	want := timeline.FitExtent(earliest, latest, f.Start, f.End)
	if !reflect.DeepEqual(first.MatchedRange, want) {
		t.Fatalf("extent must include all matches: got %+v, want %+v", first.MatchedRange, want)
	}
	f.After = first.NextCursor
	second, err := repo.List(ctx, f)
	if err != nil || !reflect.DeepEqual(first.MatchedRange, second.MatchedRange) {
		t.Fatalf("extent changed with cursor: %+v %v", second.MatchedRange, err)
	}
	for _, book := range append(first.Items, second.Items...) {
		for _, creator := range book.Creators {
			if creator.ID == "Q7243" && creator.Portrait == nil {
				t.Fatal("reviewed Tolstoy portrait absent from book detail creators")
			}
		}
	}
	t.Logf("%d matching Tolstoy books; one-record pages retain extent %+v", first.Total, *first.MatchedRange)
}
