package exhibitions

import (
	"context"
	"os"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func TestLocationFilterValidation(t *testing.T) {
	for _, f := range []Filter{{Limit: 40, Country: "France", City: "Paris"}, {Limit: 40, Country: "日本", City: "京都"}} {
		if err := f.Validate(); err != nil {
			t.Fatal(err)
		}
	}
	for _, f := range []Filter{{Limit: 40, Country: strings.Repeat("a", 201)}, {Limit: 40, City: strings.Repeat("a", 201)}} {
		if err := f.Validate(); err == nil {
			t.Fatal("unbounded location accepted")
		}
	}
}

// VALUES are query-local examples, never tables, migrations or stored fixtures.
// Exercise the actual SQL predicates in an explicitly read-only connection.
func TestLocationsReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only PostgreSQL DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	const corpus = `WITH exhibitions(id,status) AS (VALUES (1,'review'),(2,'review'),(3,'archived'),(4,'review')),
 exhibition_occurrences(exhibition_id,institution_id,country_label,country_code,city_label) AS (VALUES
 (1,'00000000-0000-0000-0000-000000000001'::uuid,'France','FR','Paris'),
 (1,'00000000-0000-0000-0000-000000000002'::uuid,'United Kingdom','GB','London'),
 (2,'00000000-0000-0000-0000-000000000003'::uuid,'United States','US','Paris, Texas'),
 (3,'00000000-0000-0000-0000-000000000001'::uuid,'France','FR','Paris'),
 (4,NULL::uuid,NULL,'FR',NULL)) SELECT e.id`
	for _, tc := range []struct {
		name string
		f    Filter
		want []int
	}{
		{"country", Filter{Country: "France"}, []int{1}},
		{"country code", Filter{Country: " fr "}, []int{1, 4}},
		{"city case and partial name", Filter{City: "pAR"}, []int{1, 2}},
		{"same venue", Filter{Country: "France", City: "paris"}, []int{1}},
		{"different touring stops", Filter{Country: "France", City: "London"}, []int{}},
		{"institution at another stop", Filter{Institution: "00000000-0000-0000-0000-000000000002", Country: "France", City: "Paris"}, []int{}},
		{"literal wildcard", Filter{Country: "%"}, []int{}},
		{"bound input", Filter{City: "Paris' OR true --"}, []int{}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			where, args := scope(tc.f)
			rows, err := pool.Query(ctx, corpus+where+" ORDER BY e.id", args...)
			if err != nil {
				t.Fatal(err)
			}
			defer rows.Close()
			got := []int{}
			for rows.Next() {
				var id int
				if err = rows.Scan(&id); err != nil {
					t.Fatal(err)
				}
				got = append(got, id)
			}
			if err = rows.Err(); err != nil || !reflect.DeepEqual(got, tc.want) {
				t.Fatalf("got %v, want %v: %v", got, tc.want, err)
			}
		})
	}
}
