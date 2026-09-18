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
	file := flag.String("file", "", "description evidence JSON")
	count := flag.Int("count", 10000, "required number of existing events")
	apply := flag.Bool("apply", false, "atomically update descriptions of existing review records")
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
	var updates []events.DescriptionUpdate
	if err = json.Unmarshal(raw, &updates); err != nil {
		log.Fatal(err)
	}
	if err = events.ValidateDescriptions(updates, *count); err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Validated %d attributed descriptions.\n", len(updates))
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
	changed, err := events.ApplyDescriptions(ctx, db, updates)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Updated %d review descriptions; no events inserted or published.\n", changed)
}
