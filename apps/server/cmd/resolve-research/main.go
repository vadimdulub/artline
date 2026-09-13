// Resolves a checksum-pinned directory of museum facts. Default is offline
// validation; --apply explicitly enables migrations and database writes.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/database"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
	"github.com/vadimdulub/artline/apps/server/internal/migrate"
	"os"
	"path/filepath"
)

func run() error {
	dir := flag.String("dir", "", "Reviewed source-match directory")
	apply := flag.Bool("apply", false, "Apply source evidence and schema migration")
	promote := flag.Bool("promote", false, "Promote eligible reconciled candidates into catalogue review records")
	explain := flag.Bool("explain", false, "Include read-only lookup plans for the actual import batch")
	start := flag.Int("start", 1, "First chunk number (inclusive)")
	end := flag.Int("end", 100000, "Last chunk number (inclusive)")
	flag.Parse()
	var m struct {
		Chunks []struct {
			File    string `json:"file"`
			SHA     string `json:"sha256"`
			Records int    `json:"records"`
		} `json:"chunks"`
	}
	b, e := os.ReadFile(filepath.Join(*dir, "manifest.json"))
	if e != nil {
		return e
	}
	if e = json.Unmarshal(b, &m); e != nil {
		return e
	}
	ctx := context.Background()
	runner := ingest.ResolutionImporter{Explain: *explain}
	// Validate every selected chunk before the first database transaction.
	for i, c := range m.Chunks {
		if i+1 < *start || i+1 > *end {
			continue
		}
		if c.File != filepath.Base(c.File) {
			return fmt.Errorf("unsafe chunk filename")
		}
		b, e = os.ReadFile(filepath.Join(*dir, c.File))
		if e != nil {
			return e
		}
		r, e := runner.Import(ctx, b, c.SHA, false, false)
		if e != nil {
			return fmt.Errorf("%s: %w", c.File, e)
		}
		if r.Records != c.Records {
			return fmt.Errorf("manifest count mismatch")
		}
	}
	if *apply {
		pool, e := database.Open(ctx, config.Load().DatabaseURL)
		if e != nil {
			return e
		}
		defer pool.Close()
		var name string
		if e = pool.QueryRow(ctx, "SELECT current_database()").Scan(&name); e != nil {
			return e
		}
		if name != "artline" {
			return fmt.Errorf("expected database artline")
		}
		if e = migrate.Run(ctx, pool); e != nil {
			return e
		}
		runner.Pool = pool
	}
	for i, c := range m.Chunks {
		if i+1 < *start || i+1 > *end {
			continue
		}
		b, e = os.ReadFile(filepath.Join(*dir, c.File))
		if e != nil {
			return e
		}
		r, e := runner.Import(ctx, b, c.SHA, *apply, *promote)
		if e != nil {
			return fmt.Errorf("%s: %w", c.File, e)
		}
		if e = json.NewEncoder(os.Stdout).Encode(map[string]any{"chunk": c.File, "report": r}); e != nil {
			return e
		}
	}
	return nil
}
func main() {
	if e := run(); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(1)
	}
}
