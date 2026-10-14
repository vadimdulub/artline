package atlas

import (
	"context"
	"errors"
	"net/url"
	"strings"
	"testing"

	"github.com/jackc/pgx/v5"
)

type geographyPageDB struct {
	atlasDB
	aggregate, page string
	total           int
}
type geographyPageRow struct{ total int }

var errGeographyPageCaptured = errors.New("page captured")

func (r geographyPageRow) Scan(values ...any) error {
	if r.total == 0 {
		return errGeographyPageCaptured
	}
	*values[0].(*int) = r.total
	*values[3].(*[]byte) = []byte("[]")
	return nil
}
func (d *geographyPageDB) QueryRow(_ context.Context, sql string, _ ...any) pgx.Row {
	aggregate := strings.HasPrefix(sql, "WITH date_groups")
	if aggregate {
		d.aggregate = sql
		return geographyPageRow{d.total}
	} else {
		d.page = sql
	}
	return geographyPageRow{}
}

func TestPeriodPagesSeekGeographyWithoutChangingAggregates(t *testing.T) {
	for _, tc := range []struct {
		name  string
		date  Range
		seek  bool
		total int
	}{
		{"renaissance-years", Range{1300, 1650}, true, 200},
		{"boundary", Range{1000, 1600}, true, 200},
		{"wide-window", Range{999, 1600}, false, 200},
		{"full-discovery", Bounds, false, 200},
		{"sparse-selection", Range{1300, 1650}, false, 5},
	} {
		t.Run(tc.name, func(t *testing.T) {
			db := &geographyPageDB{total: tc.total}
			f := Filter{Range: tc.date, Limit: 150, Types: []string{"artwork"}, Countries: []string{"italy"}, Continents: []string{"europe"}, Entities: map[string]url.Values{"artwork": {"image_only": {"true"}}}}
			_, err := (&Repository{db: db}).List(context.Background(), f)
			if !errors.Is(err, errGeographyPageCaptured) {
				t.Fatal(err)
			}
			if strings.Contains(db.aggregate, "OFFSET 0") {
				t.Fatal("aggregate plan was changed to per-candidate lookups")
			}
			if strings.Contains(db.page, "OFFSET 0") != tc.seek {
				t.Fatal("wrong page geography strategy")
			}
			if tc.seek && (strings.Contains(db.page, "artwork_geography AS MATERIALIZED") || strings.Contains(db.page, "artwork_native_scope AS MATERIALIZED")) {
				t.Fatal("page still materializes whole-period geography")
			}
			for _, required := range []string{"artwork_atlas_projection", "artline_atlas_browse_rows", "artwork_places", "artist_countries", "LIMIT $"} {
				if !strings.Contains(db.page, required) {
					t.Fatalf("lost required scope %q", required)
				}
			}
			if strings.Contains(db.page, "'italy'") {
				t.Fatal("filter interpolated instead of parameterized")
			}
		})
	}
}
