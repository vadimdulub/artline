package catalog

import (
	"context"
	"encoding/json"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"strings"
	"testing"
	"time"
)

// Read-only comparison against the local catalogue. This is not a 10M-row
// capacity claim. Keep the plan evidence alongside the bounded fixture test.
func TestMuseumDirectoryLivePlan(t *testing.T) {
	db := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if db == "" || os.Getenv("ARTLINE_TEST_QUERY_PLANS") != "1" {
		t.Skip("opt-in local plan inspection")
	}
	pool, e := pgxpool.New(context.Background(), db)
	if e != nil {
		t.Fatal(e)
	}
	defer pool.Close()
	for _, variant := range []struct{ name, cte string }{{"materialized", strings.Replace(museumCTE, "visible_works AS NOT MATERIALIZED (", "visible_works AS (", 1)}, {"inline", strings.Replace(museumCTE, "visible_works AS (", "visible_works AS NOT MATERIALIZED (", 1)}} {
		var b []byte
		e = pool.QueryRow(context.Background(), `EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) `+variant.cte+`SELECT `+museumJSON+` FROM institutions i WHERE `+museumVisible+` ORDER BY i.normalized_name,i.id LIMIT 25`, true).Scan(&b)
		if e != nil {
			t.Fatal(e)
		}
		var plan []map[string]any
		if e = json.Unmarshal(b, &plan); e != nil {
			t.Fatal(e)
		}
		var materialized int
		var walk func(map[string]any)
		walk = func(n map[string]any) {
			if n["Relation Name"] == "artworks" {
				t.Logf("%s artwork node: %s, rows=%v loops=%v time=%v removed=%v", variant.name, n["Node Type"], n["Actual Rows"], n["Actual Loops"], n["Actual Total Time"], n["Rows Removed by Filter"])
			}
			if n["Node Type"] == "CTE Scan" && n["CTE Name"] == "visible_works" {
				materialized++
			}
			if children, ok := n["Plans"].([]any); ok {
				for _, c := range children {
					walk(c.(map[string]any))
				}
			}
		}
		walk(plan[0]["Plan"].(map[string]any))
		t.Logf("%s: %.3fms, materialized artwork scans=%d", variant.name, plan[0]["Execution Time"], materialized)
	}
	var b []byte
	query := `WITH museum_page AS MATERIALIZED(SELECT i.id,i.slug,i.normalized_name FROM institutions i WHERE ` + museumVisible + ` ORDER BY i.normalized_name,i.id LIMIT 25)
 SELECT detail.data FROM museum_page page CROSS JOIN LATERAL (` + strings.ReplaceAll(museumScopedCTE, "$2", "page.slug") + ` SELECT ` + museumJSON + ` AS data FROM institutions i WHERE i.id=page.id) detail`
	if e = pool.QueryRow(context.Background(), `EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) `+query, true).Scan(&b); e != nil {
		t.Fatal(e)
	}
	var p []map[string]any
	if e = json.Unmarshal(b, &p); e != nil {
		t.Fatal(e)
	}
	t.Logf("page-scoped: %.3fms", p[0]["Execution Time"])
	t.Logf("page-scoped JIT: %v", p[0]["JIT"])
}

type museumTimedDB struct {
	*pgxpool.Pool
	t *testing.T
	n int
}
type museumTimedRows struct {
	pgx.Rows
	t     *testing.T
	n     int
	start time.Time
}

func (r *museumTimedRows) Close() {
	r.Rows.Close()
	r.t.Logf("query %d rows: %v", r.n, time.Since(r.start))
}

type museumTimedRow struct {
	pgx.Row
	t     *testing.T
	n     int
	start time.Time
}

func (r museumTimedRow) Scan(v ...any) error {
	e := r.Row.Scan(v...)
	r.t.Logf("query %d row: %v", r.n, time.Since(r.start))
	return e
}
func (d *museumTimedDB) Query(ctx context.Context, q string, args ...any) (pgx.Rows, error) {
	d.n++
	start := time.Now()
	r, e := d.Pool.Query(ctx, q, args...)
	if e != nil {
		return nil, e
	}
	return &museumTimedRows{r, d.t, d.n, start}, nil
}
func (d *museumTimedDB) QueryRow(ctx context.Context, q string, args ...any) pgx.Row {
	d.n++
	start := time.Now()
	return museumTimedRow{d.Pool.QueryRow(ctx, q, args...), d.t, d.n, start}
}

func TestMuseumDirectoryLiveTimings(t *testing.T) {
	db := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if db == "" || os.Getenv("ARTLINE_TEST_QUERY_PLANS") != "1" {
		t.Skip("opt-in")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()
	pool, e := pgxpool.New(ctx, db)
	if e != nil {
		t.Fatal(e)
	}
	defer pool.Close()
	r := &Repository{db: &museumTimedDB{Pool: pool, t: t}}
	for _, regions := range [][]string{nil, {"northern-europe", "northern-america"}} {
		t.Logf("regions=%v", regions)
		page, e := r.Museums(ctx, MuseumFilter{Limit: 24, Regions: regions}, true)
		if e != nil {
			t.Fatal(e)
		}
		t.Logf("total %d items %d", page.Total, len(page.Items))
	}
}

func TestMuseumLargeCardLivePlan(t *testing.T) {
	db := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if db == "" || os.Getenv("ARTLINE_TEST_QUERY_PLANS") != "1" {
		t.Skip("opt-in")
	}
	ctx := context.Background()
	pool, e := pgxpool.New(ctx, db)
	if e != nil {
		t.Fatal(e)
	}
	defer pool.Close()
	var b []byte
	if e = pool.QueryRow(ctx, `EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) `+museumScopedCTE+`SELECT `+museumJSON+` FROM institutions i WHERE i.slug=$2 AND `+museumVisible, true, "the-met").Scan(&b); e != nil {
		t.Fatal(e)
	}
	var p []map[string]any
	json.Unmarshal(b, &p)
	var walk func(map[string]any, int)
	walk = func(n map[string]any, depth int) {
		ms, _ := n["Actual Total Time"].(float64)
		loops, _ := n["Actual Loops"].(float64)
		if n["Node Type"] == "CTE Scan" && n["CTE Name"] == "selections" && loops > 100 {
			t.Error("selection rows rescanned per artwork")
		}
		if n["Node Type"] == "Seq Scan" && n["Relation Name"] == "artworks" && loops > 1 {
			t.Error("whole artwork table rescanned for a museum card")
		}
		if ms*loops > 20 {
			t.Logf("%s%s rel=%v cte=%v subplan=%v rows=%v loops=%v ms=%v removed=%v", strings.Repeat(" ", depth), n["Node Type"], n["Relation Name"], n["CTE Name"], n["Subplan Name"], n["Actual Rows"], loops, ms, n["Rows Removed by Filter"])
		}
		if children, ok := n["Plans"].([]any); ok {
			for _, v := range children {
				walk(v.(map[string]any), depth+1)
			}
		}
	}
	walk(p[0]["Plan"].(map[string]any), 0)
	t.Logf("total=%v", p[0]["Execution Time"])
}
