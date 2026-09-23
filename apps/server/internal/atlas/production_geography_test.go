package atlas

import (
	"context"
	"net/url"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func TestProductionGeographyKeepsCreatorFacetsTogether(t *testing.T) {
	for _, tc := range []struct {
		name   string
		values url.Values
		places bool
	}{
		{"country", url.Values{"country": {"CY"}}, true},
		{"region", url.Values{"region": {"western-asia"}}, true},
		{"fresco-country", url.Values{"country": {"CY"}, "work_type": {"fresco"}}, true},
		{"painter-country", url.Values{"country": {"CY"}, "painter": {"joseph-chourri"}}, false},
		{"women-country", url.Values{"country": {"CY"}, "women": {"true"}}, false},
		{"movement-country", url.Values{"country": {"CY"}, "movement": {"byzantine"}}, false},
		{"popular-country", url.Values{"country": {"CY"}, "popular": {"true"}}, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			args := make([]any, 8)
			predicate := entityPredicate("artwork", tc.values, &args)
			if strings.Contains(predicate, "artwork_places") != tc.places {
				t.Fatalf("unexpected production match: %s", predicate)
			}
			if strings.Contains(predicate, "institution") || strings.Contains(predicate, "'CY'") || strings.Contains(predicate, "%!") {
				t.Fatalf("custody used as origin or value not bound: %s", predicate)
			}
		})
	}
}

// Audit the requested imported records, never synthetic rows in the real DB.
func TestCyprusProductionGeographyReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var frescoID string
	err = db.QueryRow(ctx, `SELECT a.id::text FROM artworks a JOIN external_identifiers e
 ON e.entity_id=a.id AND e.entity_type='artwork'
 WHERE e.scheme='apsida-item' AND e.external_id='13510'
 AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id)`).Scan(&frescoID)
	if err != nil {
		t.Fatal("anonymous imported fresco missing", err)
	}
	repo := NewRepository(db)
	for _, tc := range []struct {
		name string
		f    Filter
		want int
	}{
		{"Cyprus", Filter{Countries: []string{"cyprus"}}, 1},
		{"France", Filter{Countries: []string{"france"}}, 0},
		{"multiple-countries", Filter{Countries: []string{"france", "cyprus"}}, 1},
		{"Asia", Filter{Continents: []string{"asia"}}, 1},
		{"Europe", Filter{Continents: []string{"europe"}}, 0},
		{"intersection", Filter{Countries: []string{"cyprus"}, Continents: []string{"europe"}}, 0},
		{"legacy-region", Filter{Region: "western-asia"}, 1},
	} {
		t.Run(tc.name, func(t *testing.T) {
			f := tc.f
			f.Range = Range{1190, 1200}
			f.Limit, f.Preview, f.Selection = 30, true, true
			f.Picks = map[string][]string{"artwork": {frescoID}}
			out, err := repo.List(ctx, f)
			if err != nil || out.Total != tc.want {
				t.Fatalf("total=%d want=%d err=%v", out.Total, tc.want, err)
			}
			f.Preview = false
			public, err := repo.List(ctx, f)
			if err != nil || public.Total != 0 {
				t.Fatalf("review fresco exposed: %+v %v", public, err)
			}
		})
	}
	f := Filter{Range: Range{1190, 1200}, Limit: 60, Preview: true, Types: []string{"artwork"}, Countries: []string{"cyprus"}}
	global, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	f.Countries = nil
	f.Entities = map[string]url.Values{"artwork": {"country": {"CY"}}}
	native, err := repo.List(ctx, f)
	if err != nil || native.Total != global.Total || native.Total == 0 {
		t.Fatalf("native/global country mismatch: %d/%d %v", native.Total, global.Total, err)
	}
	found := false
	for _, lane := range native.Lanes {
		for _, item := range lane.Items {
			found = found || item.ID == frescoID
		}
	}
	if !found {
		t.Fatal("anonymous fresco absent from native country discovery")
	}
	var xeniID string
	err = db.QueryRow(ctx, `SELECT a.id::text FROM artworks a JOIN external_identifiers e ON e.entity_id=a.id
 WHERE e.entity_type='artwork' AND e.scheme='cyprus-reviewed-object'
 AND e.external_id='xeniartspace-lydia-masterkova-metaphysical-abstraction'`).Scan(&xeniID)
	if err != nil {
		t.Fatal(err)
	}
	f = Filter{Range: Range{1960, 1970}, Limit: 30, Preview: true, Selection: true, Countries: []string{"cyprus"}, Picks: map[string][]string{"artwork": {xeniID}}}
	out, err := repo.List(ctx, f)
	if err != nil || out.Total != 0 {
		t.Fatalf("Xeni exhibition wrongly treated as Cypriot origin: %d %v", out.Total, err)
	}
}
