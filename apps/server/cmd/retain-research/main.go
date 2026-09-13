// Preserve incomplete named entries as actual review artworks. Planning uses
// read-only queries; applying requires a checksum-pinned plan and explicit flag.
package main

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/database"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
	"github.com/vadimdulub/artline/apps/server/internal/migrate"
)

func run() error {
	dir := flag.String("dir", "", "New plan directory, or existing checksum-pinned plan to apply")
	apply := flag.Bool("apply", false, "Apply the reviewed plan to artline")
	start := flag.Int("start", 1, "First chunk (inclusive)")
	end := flag.Int("end", 100000, "Last chunk (inclusive)")
	flag.Parse()
	if *dir == "" {
		return fmt.Errorf("-dir is required")
	}
	ctx := context.Background()
	pool, err := database.Open(ctx, config.Load().DatabaseURL)
	if err != nil {
		return err
	}
	defer pool.Close()
	var name string
	if err = pool.QueryRow(ctx, "SELECT current_database()").Scan(&name); err != nil {
		return err
	}
	if name != "artline" {
		return fmt.Errorf("expected artline database")
	}
	if !*apply {
		m, err := ingest.PlanReviewArtworks(ctx, pool, *dir)
		if err != nil {
			return err
		}
		return json.NewEncoder(os.Stdout).Encode(m)
	}
	b, err := os.ReadFile(filepath.Join(*dir, "manifest.json"))
	if err != nil {
		return err
	}
	var m ingest.ReviewManifest
	if err = json.Unmarshal(b, &m); err != nil {
		return err
	}
	if m.InputSHA != "210a729ead48d12b0f228eb9e1fe0c5a6708750b196be38ddfbbb270aa1355c8" || len(m.Chunks) == 0 {
		return fmt.Errorf("unexpected input manifest")
	}
	// Check every selected file before any migration or catalogue write.
	for i, c := range m.Chunks {
		if i+1 < *start || i+1 > *end {
			continue
		}
		if c.File != filepath.Base(c.File) {
			return fmt.Errorf("unsafe chunk name")
		}
		b, err = os.ReadFile(filepath.Join(*dir, c.File))
		if err != nil {
			return err
		}
		if fmt.Sprintf("%x", sha256.Sum256(b)) != c.SHA {
			return fmt.Errorf("chunk checksum mismatch")
		}
		var records []ingest.ReviewArtwork
		if err = json.Unmarshal(b, &records); err != nil {
			return err
		}
		if len(records) != c.Records {
			return fmt.Errorf("chunk count mismatch")
		}
	}
	if err = migrate.Run(ctx, pool); err != nil {
		return err
	}
	for i, c := range m.Chunks {
		if i+1 < *start || i+1 > *end {
			continue
		}
		b, err = os.ReadFile(filepath.Join(*dir, c.File))
		if err != nil {
			return err
		}
		result, err := ingest.ApplyReviewArtworks(ctx, pool, b, c.SHA)
		if err != nil {
			return fmt.Errorf("%s: %w", c.File, err)
		}
		if err = json.NewEncoder(os.Stdout).Encode(map[string]any{"chunk": i + 1, "sha256": c.SHA, "result": result}); err != nil {
			return err
		}
	}
	return nil
}
func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
