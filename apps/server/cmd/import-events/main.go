package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/database"
	"github.com/vadimdulub/artline/apps/server/internal/events"
)

func main() {
	file := flag.String("file", "", "reviewed research JSON to import")
	expected := flag.Int("count", 10000, "required number of distinct events")
	apply := flag.Bool("apply", false, "insert new review records into DATABASE_URL; default validates files only")
	flag.Parse()
	if *file == "" {
		log.Fatal("-file is required")
	}
	f, err := os.Open(*file)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()
	raw, err := io.ReadAll(io.LimitReader(f, 64<<20))
	if err != nil {
		log.Fatal(err)
	}
	var items []events.Event
	if err = json.Unmarshal(raw, &items); err != nil {
		log.Fatal(err)
	}
	if err = events.ValidateImport(items, *expected); err != nil {
		log.Fatal(err)
	}
	top := 0
	for _, event := range items {
		if event.Top100 {
			top++
		}
	}
	if top != 100 {
		log.Fatalf("Expected 100 editorial events, received %d", top)
	}
	fmt.Printf("Validated %d distinct source-linked review records.\n", len(items))
	if !*apply {
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	db, err := database.Open(ctx, config.Load().DatabaseURL)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	inserted, err := events.Import(ctx, db, items)
	if err != nil {
		log.Fatal(err)
	}
	if inserted {
		fmt.Printf("Inserted %d events in review. No records published.\n", len(items))
	} else {
		fmt.Println("Identical event records already present; no changes.")
	}
}
