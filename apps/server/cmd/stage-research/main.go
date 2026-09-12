// Local-only, checksum-approved evidence staging; no network or publication.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"github.com/jackc/pgx/v5"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/database"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
	"log"
	"os"
	"strings"
)

func main() {
	path := flag.String("file", "", "Evidence JSON path")
	sha := flag.String("sha", "", "Reviewed SHA256")
	name := flag.String("name", "", "Snapshot label")
	apply := flag.Bool("apply", false, "Commit local staging; otherwise rollback")
	receipt := flag.String("report", "", "Exclusive new receipt path")
	flag.Parse()
	cfg, e := pgx.ParseConfig(config.Load().DatabaseURL)
	if e != nil {
		log.Fatal(e)
	}
	local := func(s string) bool {
		return s == "localhost" || s == "127.0.0.1" || s == "::1" || strings.HasPrefix(s, "/")
	}
	if !local(cfg.Host) {
		log.Fatal("local database only")
	}
	for _, f := range cfg.Fallbacks {
		if !local(f.Host) {
			log.Fatal("local database only")
		}
	}
	info, e := os.Stat(*path)
	if e != nil {
		log.Fatal(e)
	}
	if info.Size() > 128<<20 {
		log.Fatal("snapshot exceeds byte budget")
	}
	b, e := os.ReadFile(*path)
	if e != nil {
		log.Fatal(e)
	}
	var f *os.File
	if *receipt != "" {
		f, e = os.OpenFile(*receipt, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if e != nil {
			log.Fatal(e)
		}
		defer f.Close()
	}
	ctx := context.Background()
	pool, e := database.Open(ctx, config.Load().DatabaseURL)
	if e != nil {
		log.Fatal(e)
	}
	defer pool.Close()
	r, e := ingest.StageResearch(ctx, pool, b, *sha, *name, *apply)
	if e != nil {
		log.Fatal(e)
	}
	if f != nil {
		if e = json.NewEncoder(f).Encode(r); e != nil {
			log.Fatalf("applied=%v but receipt failed: %v", r.Applied, e)
		}
	}
	json.NewEncoder(os.Stdout).Encode(r)
}
