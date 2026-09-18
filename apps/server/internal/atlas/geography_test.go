package atlas

import (
	"context"
	"net/url"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func TestGeographyValidationAndCursor(t *testing.T) {
	f := Filter{Range: Bounds, Limit: 30, Countries: []string{"france"}, Continents: []string{"europe"}}
	if err := f.Validate(); err != nil {
		t.Fatal(err)
	}
	raw := encodeCursor(Item{ID: "entry", StartYear: 1900}, f, "book")
	f.Countries = []string{"japan"}
	if _, err := decodeCursor(raw, f, "book"); err == nil {
		t.Fatal("cursor crossed country filters")
	}
	f.Countries = []string{"france"}
	f.Continents = []string{"asia"}
	if _, err := decodeCursor(raw, f, "book"); err == nil {
		t.Fatal("cursor crossed continents")
	}
	f.Continents = []string{"invented"}
	if f.Validate() == nil {
		t.Fatal("accepted unknown continent")
	}
	f.Continents = nil
	f.Countries = []string{" "}
	if f.Validate() == nil {
		t.Fatal("accepted empty country")
	}
}

// Compare global geography with the existing native layer filters, using only
// real records in enforced read-only connections.
func TestGeographyReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only audit DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	r := NewRepository(db)
	choices, err := r.Countries(ctx, true)
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, c := range choices {
		if c.Key == "france" {
			found = true
		}
	}
	if !found || len(choices) > 1000 {
		t.Fatalf("country choices missing or unbounded: %d", len(choices))
	}
	for kind, country := range map[string]string{"book": "Q142", "event": "France", "artwork": "FR"} {
		f := Filter{Range: Bounds, Limit: 30, Preview: true, Types: []string{kind}, Countries: []string{"france"}}
		global, err := r.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		f.Countries = nil
		f.Entities = map[string]url.Values{kind: {"country": {country}}}
		native, err := r.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		if global.Total != native.Total || global.Total == 0 {
			t.Fatalf("%s country mismatch: %d/%d", kind, global.Total, native.Total)
		}
		f.Entities = nil
		f.Continents = []string{"europe"}
		continent, err := r.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		regions := continentRegions["europe"]
		if kind == "event" {
			regions = []string{"Eastern Europe", "Northern Europe", "Southern Europe", "Western Europe"}
		}
		f.Continents = nil
		f.Entities = map[string]url.Values{kind: {"region": regions}}
		native, err = r.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		if continent.Total != native.Total || continent.Total == 0 {
			t.Fatalf("%s continent mismatch: %d/%d", kind, continent.Total, native.Total)
		}
		f.Entities = nil
		f.Countries = []string{"france"}
		f.Continents = []string{"europe"}
		intersection, err := r.List(ctx, f)
		if err != nil || intersection.Total > global.Total || intersection.Total > continent.Total {
			t.Fatalf("%s invalid intersection: %d %v", kind, intersection.Total, err)
		}
		f.Preview = false
		public, err := r.List(ctx, f)
		if err != nil || public.Total != 0 {
			t.Fatalf("review data exposed: %s %v", kind, err)
		}
		t.Logf("%s: France=%d Europe=%d intersection=%d", kind, global.Total, continent.Total, intersection.Total)
	}
}
