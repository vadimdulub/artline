package main

import (
	"context"
	"flag"
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
	var cfg ingest.Options
	flag.IntVar(&cfg.Painters, "painters", 1000, "Bounded cohort size (maximum 1000)")
	flag.IntVar(&cfg.MaxWorks, "max-works", 5, "Maximum selected highlights per painter (maximum 10)")
	flag.StringVar(&cfg.Root, "root", "../..", "Artline project root")
	flag.StringVar(&cfg.Run, "run", "historical-1000-2026-09", "Snapshot/run name; reuse to resume")
	flag.StringVar(&cfg.OnlySource, "source", "all", "all (API museum adapters), pantheon, wikidata, met, cleveland, aic, prado, uffizi, mam (reviewed manifests)")
	flag.BoolVar(&cfg.Apply, "apply", false, "Write review records into local PostgreSQL")
	flag.BoolVar(&cfg.Images, "images", false, "Download selected rights-cleared images (requires apply)")
	flag.Parse()
	root, err := filepath.Abs(cfg.Root)
	if err != nil {
		log.Fatal(err)
	}
	cfg.Root = root
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	dbURL := config.Load().DatabaseURL
	dbConfig, err := pgx.ParseConfig(dbURL)
	if err != nil || (dbConfig.Host != "localhost" && dbConfig.Host != "127.0.0.1" && dbConfig.Host != "::1" && !strings.HasPrefix(dbConfig.Host, "/")) {
		log.Fatal("This importer is restricted to local PostgreSQL; remote imports require a separate deployment workflow.")
	}
	pool, err := database.Open(ctx, dbURL)
	if err != nil {
		log.Fatal(err)
	}
	defer pool.Close()
	if err = ingest.Run(ctx, pool, cfg, log.Print); err != nil {
		log.Print(err)
		os.Exit(1)
	}
}
