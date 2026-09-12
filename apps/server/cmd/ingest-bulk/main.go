package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

func main() {
	dir := flag.String("dir", "", "Reviewed manifest/chunks directory")
	apply := flag.Bool("apply", false, "Apply chunks locally; default rollback previews")
	reports := flag.String("reports", "", "New receipt directory; never overwrite files")
	flag.Parse()
	if *dir == "" || *reports == "" {
		log.Fatal("-dir and -reports required")
	}
	cfg, e := pgxpool.ParseConfig(config.Load().DatabaseURL)
	if e != nil {
		log.Fatal(e)
	}
	local := func(h string) bool {
		return h == "localhost" || h == "127.0.0.1" || h == "::1" || strings.HasPrefix(h, "/")
	}
	if !local(cfg.ConnConfig.Host) {
		log.Fatal("local DB only")
	}
	for _, f := range cfg.ConnConfig.Fallbacks {
		if !local(f.Host) {
			log.Fatal("remote fallback forbidden")
		}
	}
	b, e := os.ReadFile(filepath.Join(*dir, "manifest.json"))
	if e != nil {
		log.Fatal(e)
	}
	var manifest struct {
		Chunks []struct {
			File, SHA string
			SHA256    string `json:"sha256"`
			Works     int
		}
	}
	if e = json.Unmarshal(b, &manifest); e != nil {
		log.Fatal(e)
	}
	if len(manifest.Chunks) == 0 || len(manifest.Chunks) > 200 {
		log.Fatal("bounded manifest requires1..200chunks")
	}
	if e = os.Mkdir(*reports, 0700); e != nil {
		log.Fatal(e)
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	pool, e := pgxpool.NewWithConfig(ctx, cfg)
	if e != nil {
		log.Fatal(e)
	}
	defer pool.Close()
	for _, c := range manifest.Chunks {
		if c.File != filepath.Base(c.File) || !strings.HasSuffix(c.File, ".json") {
			log.Fatal("invalid chunk path")
		}
		b, e := os.ReadFile(filepath.Join(*dir, c.File))
		if e != nil {
			log.Fatal(e)
		}
		f, e := os.OpenFile(filepath.Join(*reports, c.File), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if e != nil {
			log.Fatal(e)
		}
		result, e := ingest.ImportBulkCatalogue(ctx, pool, b, c.SHA256, *apply)
		if e != nil {
			f.Close()
			log.Fatalf("chunk %s rolled back: %v; earlier applied chunks remain; rerun with a new receipt directory to resume", c.File, e)
		}
		e = json.NewEncoder(f).Encode(result)
		closeErr := f.Close()
		if e != nil || closeErr != nil {
			log.Fatalf("applied=%v receipt failure %v %v", result.Applied, e, closeErr)
		}
		fmt.Printf("%s applied=%v replay=%v created=%d reused=%d artists=%d\n", c.File, result.Applied, result.Replayed, result.CreatedWorks, result.ReusedWorks, result.CreatedArtists)
	}
}
