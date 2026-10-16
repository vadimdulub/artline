// Read-only repository verification. Run from a temporary directory inside apps/server.
package main

import (
	"context"
	"encoding/json"
	"os"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(os.Getenv("RUSIMP_VERIFY_DSN"))
	if err != nil { panic("invalid connection configuration") }
	cfg.MaxConns = 2
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "60000"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil { panic("connection unavailable") }
	defer db.Close()
	var readonly string
	if err = db.QueryRow(ctx, "SHOW default_transaction_read_only").Scan(&readonly); err != nil || readonly != "on" { panic("read-only required") }
	repo := catalog.NewRepository(db)
	slug := "museum-of-russian-impressionism"
	museum, err := repo.Museum(ctx, slug)
	if err != nil { panic(err) }
	if museum.WorkCount != 68 || museum.HoldingCount != 68 || museum.OnViewCount != 0 { panic("museum count mismatch") }
	pages := []catalog.MuseumWorksPage{}
	works := []catalog.MuseumArtwork{}
	seen := map[string]bool{}
	f := catalog.MuseumFilter{Limit:24,Sort:"title"}
	for {
		page, err := repo.MuseumWorks(ctx, slug, f)
		if err != nil { panic(err) }
		if page.Total != 68 || page.ImageCount != 68 { panic("page count mismatch") }
		pages = append(pages, page)
		for _, w := range page.Items {
			if seen[w.ID] || w.MediaURL == nil || len(w.Artists) == 0 { panic("missing image/artist or duplicate") }
			seen[w.ID] = true
			work, err := repo.MuseumArtwork(ctx, slug, w.ID)
			if err != nil { panic(err) }
			works = append(works, work)
		}
		if page.NextCursor == "" { break }
		f.Cursor = page.NextCursor
	}
	if len(seen) != 68 { panic("incomplete paging") }
	out, err := os.OpenFile(os.Getenv("RUSIMP_VERIFY_OUTPUT"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil { panic(err) }
	defer out.Close()
	err = json.NewEncoder(out).Encode(map[string]any{"at":time.Now().UTC(),"readOnly":true,"method":"Current repository queries against production, not an authenticated HTTP or browser check","museum":museum,"pages":pages,"works":works})
	if err != nil { panic(err) }
}
