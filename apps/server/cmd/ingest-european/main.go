package main

import (
	"context"
	"encoding/json"
	"flag"
	"io"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"

	"github.com/jackc/pgx/v5"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/database"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

func main() {
	apply := flag.Bool("apply", false, "Commit the reviewed batch to local PostgreSQL (default: rollback preview)")
	root := flag.String("root", "../..", "Project root")
	batch := flag.String("batch", "v1", "Reviewed snapshot: v1, deep-v2, catalogue-v3, nga-v1, pushkin-v1, or brera-v1")
	reportPath := flag.String("report", "", "Optional new JSON receipt file; existing files are never overwritten")
	flag.Parse()
	dbURL := config.Load().DatabaseURL
	cfg, err := pgx.ParseConfig(dbURL)
	if err != nil {
		log.Fatal(err)
	}
	local := func(host string) bool {
		return host == "localhost" || host == "127.0.0.1" || host == "::1" || strings.HasPrefix(host, "/")
	}
	if !local(cfg.Host) {
		log.Fatal("European importer is restricted to local PostgreSQL")
	}
	for _, fallback := range cfg.Fallbacks {
		if !local(fallback.Host) {
			log.Fatal("Remote PostgreSQL fallbacks are not allowed")
		}
	}
	path := "docs/research/european-paintings/inventory.json"
	importer := ingest.ImportEuropean
	switch *batch {
	case "v1":
	case "deep-v2":
		path = ingest.EuropeanDeepPath
		importer = ingest.ImportEuropeanDeep
	case "catalogue-v3":
		path = ingest.EuropeanCataloguePath
		importer = ingest.ImportEuropeanCatalogue
	case "nga-v1":
		path = ingest.NGACataloguePath
		importer = ingest.ImportNGACatalogue
	case "pushkin-v1":
		path = ingest.PushkinCataloguePath
		importer = ingest.ImportPushkinCatalogue
	case "brera-v1":
		path = ingest.BreraCataloguePath
		importer = ingest.ImportBreraCatalogue
	default:
		log.Fatal("Unknown reviewed batch; see -help for supported snapshots")
	}
	data, err := os.ReadFile(filepath.Join(*root, path))
	if err != nil {
		log.Fatal(err)
	}
	var output io.Writer = os.Stdout
	if *reportPath != "" {
		f, e := os.OpenFile(*reportPath, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if e != nil {
			log.Fatal(e)
		}
		defer f.Close()
		output = io.MultiWriter(os.Stdout, f)
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	pool, err := database.Open(ctx, dbURL)
	if err != nil {
		log.Fatal(err)
	}
	defer pool.Close()
	report, err := importer(ctx, pool, data, *apply)
	if err != nil {
		log.Fatalf("Import not committed: %v", err)
	}
	encoder := json.NewEncoder(output)
	encoder.SetIndent("", "  ")
	if err = encoder.Encode(report); err != nil {
		log.Fatalf("Database applied=%v; receipt write failed: %v", report.Applied, err)
	}
}
