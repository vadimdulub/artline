package httpapi

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strconv"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/atlas"
	"github.com/vadimdulub/artline/apps/server/internal/books"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"github.com/vadimdulub/artline/apps/server/internal/events"
)

type readOnlyPerformanceStatement struct {
	SQL          string  `json:"sql"`
	Args         []any   `json:"args"`
	Milliseconds float64 `json:"milliseconds"`
	Error        string  `json:"error,omitempty"`
	started      time.Time
}

type readOnlyPerformanceTrace struct {
	statements []*readOnlyPerformanceStatement
	recording  bool
}
type readOnlyPerformanceKey struct{}

func (r *readOnlyPerformanceTrace) TraceQueryStart(ctx context.Context, _ *pgx.Conn, d pgx.TraceQueryStartData) context.Context {
	if !r.recording {
		return ctx
	}
	args := d.Args
	for len(args) > 0 {
		if _, ok := args[0].(pgx.QueryExecMode); !ok {
			break
		}
		args = args[1:]
	}
	s := &readOnlyPerformanceStatement{SQL: d.SQL, Args: append([]any(nil), args...), started: time.Now()}
	r.statements = append(r.statements, s)
	return context.WithValue(ctx, readOnlyPerformanceKey{}, s)
}
func (*readOnlyPerformanceTrace) TraceQueryEnd(ctx context.Context, _ *pgx.Conn, d pgx.TraceQueryEndData) {
	if s, ok := ctx.Value(readOnlyPerformanceKey{}).(*readOnlyPerformanceStatement); ok {
		s.Milliseconds = float64(time.Since(s.started).Microseconds()) / 1000
		if d.Err != nil {
			s.Error = d.Err.Error()
		}
	}
}

// Explicitly opted-in sequential query audit. Uses existing records with a
// read-only, single-connection pool; never migrates, seeds, or creates a database.
// Handler deadlines remain in force. EXPLAIN executes each successful query once
// more, so this is diagnosis, not a load test or an HTTP latency benchmark.
func TestCataloguePerformanceReadOnly(t *testing.T) {
	dsn, raw, dir := os.Getenv("ARTLINE_READONLY_DATABASE_URL"), os.Getenv("ARTLINE_PERFORMANCE_URL"), os.Getenv("ARTLINE_PERFORMANCE_OUT")
	if dsn == "" || raw == "" || dir == "" {
		t.Skip("read-only DSN, request URL and output directory required")
	}
	req := httptest.NewRequest(http.MethodGet, raw, nil)
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.MaxConns = 1
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	cfg.ConnConfig.RuntimeParams["application_name"] = "artline-performance-round2-readonly"
	trace := &readOnlyPerformanceTrace{}
	cfg.ConnConfig.Tracer = trace
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	if err = pool.Ping(ctx); err != nil {
		t.Fatal(err)
	}
	api := &API{db: pool, repo: catalog.NewRepository(pool), bookRepo: books.NewRepository(pool), eventRepo: events.NewRepository(pool), atlasRepo: atlas.NewRepository(pool)}
	var handler http.HandlerFunc
	switch req.URL.Path {
	case "/api/v1/timeline":
		handler = api.timeline
	case "/api/v1/books":
		handler = api.books
	case "/api/v1/events":
		handler = api.events
	case "/api/v1/atlas":
		handler = api.atlasTimeline
	default:
		t.Fatal("audit only supports public timeline list handlers")
	}
	if err = os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	save := func(name string, value any) {
		t.Helper()
		body, e := json.MarshalIndent(value, "", "  ")
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(dir, name), body, 0600); e != nil {
			t.Fatal(e)
		}
	}
	response := httptest.NewRecorder()
	trace.recording = true
	started := time.Now()
	handler(response, req.WithContext(catalog.WithPublicRead(ctx)))
	elapsed := time.Since(started)
	trace.recording = false
	save("trace.json", trace.statements)
	save("request.json", map[string]any{"url": raw, "status": response.Code, "milliseconds": float64(elapsed.Microseconds()) / 1000})
	if err = os.WriteFile(filepath.Join(dir, "response.json"), response.Body.Bytes(), 0600); err != nil {
		t.Fatal(err)
	}
	if response.Code != http.StatusOK {
		t.Fatalf("handler status %d: %s", response.Code, response.Body.String())
	}
	t.Logf("handler=%s elapsed=%s statements=%d", req.URL.Path, elapsed, len(trace.statements))
	for i, s := range trace.statements {
		if s.Error != "" {
			continue
		}
		var plan json.RawMessage
		args := append([]any{pgx.QueryExecModeCacheDescribe}, s.Args...)
		if err = pool.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,SETTINGS,FORMAT JSON) "+s.SQL, args...).Scan(&plan); err != nil {
			t.Fatal(err)
		}
		save("plan-"+strconv.Itoa(i)+".json", plan)
		t.Logf("query %d: %.2f ms including transport", i, s.Milliseconds)
	}
}
