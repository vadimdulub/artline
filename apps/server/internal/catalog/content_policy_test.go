package catalog

import (
	"context"
	"os"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
)

func TestCreationScope(t *testing.T) {
	n := func(v int) *int { return &v }
	for _, tt := range []struct {
		name            string
		first, last     *int
		precision, want string
	}{
		{"inclusive", n(1970), n(1970), "exact", "eligible"},
		{"later", n(1971), n(1971), "exact", "excluded"},
		{"crossing", n(1960), n(1980), "range", "review"},
		{"open range", n(1960), nil, "range", "review"},
		{"undated", nil, nil, "unknown", "review"},
		{"unknown with values", n(1800), n(1900), "unknown", "review"},
		{"before inclusive cutoff", nil, n(1971), "before", "eligible"},
		{"before later", nil, n(1980), "before", "review"},
		{"after older", n(1800), nil, "after", "review"},
		{"after cutoff", n(1970), nil, "after", "excluded"},
		{"approx boundary", n(1970), n(1970), "circa", "review"},
		{"old approximate", n(1800), n(1800), "circa", "eligible"},
		{"reversed", n(1900), n(1800), "range", "review"},
		{"bad precision", n(1800), n(1800), "bogus", "review"},
	} {
		t.Run(tt.name, func(t *testing.T) {
			if got := CreationScope(tt.first, tt.last, tt.precision); got != tt.want {
				t.Fatalf("got %s want %s", got, tt.want)
			}
		})
	}
}

func TestCreationPolicyDatabaseParity(t *testing.T) {
	db := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if db == "" {
		t.Skip("database URL not set")
	}
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	values := []*int{nil}
	for _, n := range []int{1800, 1969, 1970, 1971, 1980} {
		v := n
		values = append(values, &v)
	}
	for _, first := range values {
		for _, last := range values {
			for _, p := range []string{"exact", "circa", "range", "circa_range", "unknown", "before", "after", "decade", "century", "bogus"} {
				var got string
				if err = pool.QueryRow(ctx, `SELECT artline_creation_scope($1,$2,$3)`, first, last, p).Scan(&got); err != nil {
					t.Fatal(err)
				}
				if want := CreationScope(first, last, p); got != want {
					t.Fatalf("SQL/Go disagreement for %v %v %s: %s/%s", first, last, p, got, want)
				}
			}
		}
	}
}
