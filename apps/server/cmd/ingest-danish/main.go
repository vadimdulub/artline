package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

func main() {
	dir := flag.String("dir", "", "Immutable reviewed manifest directory")
	pin := flag.String("manifest-sha", "", "Reviewed manifest SHA256")
	reports := flag.String("reports", "", "New receipt directory")
	target := flag.String("target", "local", "local or production (authorized Cloud SQL proxy)")
	apply := flag.Bool("apply", false, "Apply reviewed source records; default rollback preview")
	validateOnly := flag.Bool("validate-only", false, "Validate every source chunk without connecting to a database")
	flag.Parse()
	if *dir == "" || *reports == "" || len(*pin) != 64 {
		log.Fatal("dir, reports, manifest-sha required")
	}
	data, err := os.ReadFile(filepath.Join(*dir, "manifest.json"))
	if err != nil {
		log.Fatal(err)
	}
	hash := sha256.Sum256(data)
	if hex.EncodeToString(hash[:]) != *pin {
		log.Fatal("manifest pin mismatch")
	}
	var m struct {
		Chunks []struct {
			File string
			SHA  string `json:"sha256"`
		}
	}
	if json.Unmarshal(data, &m) != nil || len(m.Chunks) < 1 || len(m.Chunks) > 50 {
		log.Fatal("invalid manifest")
	}
	for _, chunk := range m.Chunks {
		if filepath.Base(chunk.File) != chunk.File {
			log.Fatal("unsafe chunk name")
		}
		b, e := os.ReadFile(filepath.Join(*dir, chunk.File))
		if e != nil {
			log.Fatal(e)
		}
		if e = ingest.ValidateDanishSession(b, chunk.SHA); e != nil {
			log.Fatalf("%s: %v", chunk.File, e)
		}
	}
	if *validateOnly {
		fmt.Printf("Validated %d pinned chunks; no database connection.\n", len(m.Chunks))
		return
	}
	cfg, err := pgxpool.ParseConfig(config.Load().DatabaseURL)
	if err != nil {
		log.Fatal("invalid database config")
	}
	c := cfg.ConnConfig
	validTarget := (*target == "local" && (c.Host == "127.0.0.1" || c.Host == "localhost") && c.Port == 5432) || (*target == "production" && c.Host == "127.0.0.1" && c.Port == 55433) || (*target == "production-cloud" && c.Host == "/cloudsql/artline-508319:europe-west1:artline-postgres")
	if c.Database != "artline" || !validTarget {
		log.Fatal("unexpected database target")
	}
	for _, f := range c.Fallbacks {
		if f.Host != c.Host || f.Port != c.Port {
			log.Fatal("unexpected database fallback")
		}
	}
	if err = os.Mkdir(*reports, 0700); err != nil {
		log.Fatal(err)
	}
	ctx := context.Background()
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		log.Fatal("database connection failed")
	}
	defer pool.Close()
	for _, chunk := range m.Chunks {
		if filepath.Base(chunk.File) != chunk.File {
			log.Fatal("unsafe chunk name")
		}
		data, err = os.ReadFile(filepath.Join(*dir, chunk.File))
		if err != nil {
			log.Fatal(err)
		}
		result, err := ingest.ImportDanishSession(ctx, pool, data, chunk.SHA, *apply)
		for attempt := 0; err != nil && attempt < 3; attempt++ {
			var pgerr *pgconn.PgError
			if !errors.As(err, &pgerr) || (pgerr.Code != "40001" && pgerr.Code != "40P01") {
				break
			}
			time.Sleep(time.Second)
			result, err = ingest.ImportDanishSession(ctx, pool, data, chunk.SHA, *apply)
		}
		if err != nil {
			log.Fatalf("%s rolled back: %v", chunk.File, err)
		}
		f, err := os.OpenFile(filepath.Join(*reports, chunk.File), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if err != nil {
			log.Fatal(err)
		}
		if err = json.NewEncoder(f).Encode(result); err != nil {
			log.Fatal(err)
		}
		if err = f.Close(); err != nil {
			log.Fatal(err)
		}
		fmt.Printf("%s target=%s applied=%v replay=%v artworks=%d artists=%d reused=%d\n", chunk.File, *target, result.Applied, result.Replayed, result.CreatedWorks, result.CreatedArtists, result.ReusedWorks)
		if *target == "production-cloud" {
			if err = json.NewEncoder(os.Stdout).Encode(result); err != nil {
				log.Fatal(err)
			}
		}
	}
}
