package main

import (
	"context"
	"encoding/json"
	"flag"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
	"log"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	root := flag.String("root", "../..", "Project root")
	apply := flag.Bool("apply", false, "Explicit selected image download and local DB attachment")
	report := flag.String("report", "", "New receipt path")
	flag.Parse()
	if *report == "" {
		log.Fatal("-report required")
	}
	cfg, e := pgxpool.ParseConfig(config.Load().DatabaseURL)
	if e != nil {
		log.Fatal(e)
	}
	local := func(h string) bool {
		return h == "localhost" || h == "127.0.0.1" || h == "::1" || strings.HasPrefix(h, "/")
	}
	if !local(cfg.ConnConfig.Host) {
		log.Fatal("local only")
	}
	for _, f := range cfg.ConnConfig.Fallbacks {
		if !local(f.Host) {
			log.Fatal("remote fallback denied")
		}
	}
	b, e := os.ReadFile(filepath.Join(*root, ingest.NGAImagesPath))
	if e != nil {
		log.Fatal(e)
	}
	f, e := os.OpenFile(*report, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		log.Fatal(e)
	}
	defer f.Close()
	ctx := context.Background()
	pool, e := pgxpool.NewWithConfig(ctx, cfg)
	if e != nil {
		log.Fatal(e)
	}
	defer pool.Close()
	r, e := ingest.ImportNGAImages(ctx, pool, b, filepath.Join(*root, "apps/web/public/assets/artworks/imported"), *apply)
	if e != nil {
		log.Fatal(e)
	}
	if e = json.NewEncoder(f).Encode(r); e != nil {
		log.Fatal(e)
	}
	json.NewEncoder(os.Stdout).Encode(r)
}
