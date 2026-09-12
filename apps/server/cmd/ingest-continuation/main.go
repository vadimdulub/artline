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
	dir := flag.String("dir", "", "Reviewed pinned manifest directory")
	reports := flag.String("reports", "", "New receipt directory")
	apply := flag.Bool("apply", false, "Apply to local DB; default is rollback preview")
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
	manifest, e := os.ReadFile(filepath.Join(*dir, "manifest.json"))
	if e != nil {
		log.Fatal(e)
	}
	var m struct{ Chunks []struct{ File string } }
	if e = json.Unmarshal(manifest, &m); e != nil || len(m.Chunks) < 1 || len(m.Chunks) > 200 {
		log.Fatal("invalid bounded manifest")
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
	for _, c := range m.Chunks {
		if c.File != filepath.Base(c.File) || !strings.HasSuffix(c.File, ".json") {
			log.Fatal("unsafe chunk path")
		}
		data, e := os.ReadFile(filepath.Join(*dir, c.File))
		if e != nil {
			log.Fatal(e)
		}
		f, e := os.OpenFile(filepath.Join(*reports, c.File), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if e != nil {
			log.Fatal(e)
		}
		result, e := ingest.ImportContinuation(ctx, pool, manifest, c.File, data, *apply)
		if e != nil {
			f.Close()
			log.Fatalf("%s rolled back: %v; previous committed chunks remain. Resume with a new receipt directory.", c.File, e)
		}
		e = json.NewEncoder(f).Encode(result)
		ce := f.Close()
		if e != nil || ce != nil {
			log.Fatalf("applied=%v receipt failure %v %v", result.Applied, e, ce)
		}
		fmt.Printf("%s applied=%v new=%d reused=%d citations=%d\n", c.File, result.Applied, result.CreatedWorks, result.ReusedWorks, result.AddedCitations)
	}
}
