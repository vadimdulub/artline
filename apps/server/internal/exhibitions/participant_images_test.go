package exhibitions

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func TestParticipantImagesPreserveSourceIdentity(t *testing.T) {
	var people []map[string]json.RawMessage
	err := json.Unmarshal([]byte(`[
 {"id":"source-1","artist_id":"artist-1","name":"Historical label","role":"artist"},
 {"id":"source-2","artist_id":"artist-1","name":"Historical label","role":"represented_artist"},
 {"id":"source-3","artist_id":"artist-1","portrait":"/assets/artists/source.jpg","imageCredit":"Source portrait credit"},
 {"id":"unresolved","artist_id":null,"name":"Unresolved artist"}
 ]`), &people)
	if err != nil {
		t.Fatal(err)
	}
	var image map[string]json.RawMessage
	if err = json.Unmarshal([]byte(`{"image":"/assets/artworks/key.jpg","imageKind":"artwork","imageCredit":"Artwork credit"}`), &image); err != nil {
		t.Fatal(err)
	}
	applyParticipantImages(people, map[string]map[string]json.RawMessage{"artist-1": image})
	for i, role := range []string{"artist", "represented_artist"} {
		if participantString(people[i], "image") != "/assets/artworks/key.jpg" || participantString(people[i], "role") != role || participantString(people[i], "name") != "Historical label" {
			t.Fatal("artist image missing or source identity/role changed")
		}
	}
	if participantString(people[2], "image") != "" || participantString(people[2], "imageCredit") != "Source portrait credit" {
		t.Fatal("existing source portrait or credit overwritten")
	}
	if participantString(people[3], "image") != "" {
		t.Fatal("unresolved artist received another artist's image")
	}
}

// Reads the existing catalogue only; no exhibition tables, migrations or stored
// fixtures are needed to verify the screenshot's two saved artist selections.
func TestParticipantImagesReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal("invalid read-only DSN")
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	ids := []string{"ed8ab094-58e2-4b73-8fc6-e261cf8b0899", "8b89f8d7-fe8f-44f2-9eb8-620497347c8d"}
	people := []map[string]any{}
	for _, id := range ids {
		for _, role := range []string{"artist", "represented_artist"} {
			people = append(people, map[string]any{"artist_id": id, "role": role})
		}
	}
	raw, _ := json.Marshal(map[string]any{"participants": people})
	result, err := NewRepository(pool).enrichParticipantImages(ctx, raw)
	if err != nil {
		t.Fatal(err)
	}
	var detail struct {
		Participants []struct {
			Image, ImageKind, ImageTitle, ImageCredit, Role string
			ImageWidth, ImageHeight                         int
		}
	}
	if err = json.Unmarshal(result, &detail); err != nil || len(detail.Participants) != 4 {
		t.Fatal("participant records lost", err)
	}
	for _, person := range detail.Participants {
		if !strings.HasPrefix(person.Image, "/assets/artworks/") || person.ImageKind != "artwork" || person.ImageTitle == "" || person.ImageCredit == "" || person.ImageWidth <= 0 || person.ImageHeight <= 0 {
			t.Fatalf("saved key artwork/image metadata missing: %+v", person)
		}
	}
	var portraitID, portraitPath string
	if err = pool.QueryRow(ctx, `SELECT a.id::text,m.storage_path FROM artists a
 JOIN media_assets m ON m.id=a.portrait_media_id
 WHERE a.status<>'archived' AND m.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$'
 ORDER BY a.id LIMIT 1`).Scan(&portraitID, &portraitPath); err != nil {
		t.Fatal(err)
	}
	rows, err := pool.Query(ctx, participantImagesQuery, []string{portraitID})
	if err != nil {
		t.Fatal(err)
	}
	if !rows.Next() {
		rows.Close()
		t.Fatal("existing artist portrait missing")
	}
	var selectedID string
	var selectedImage []byte
	if err = rows.Scan(&selectedID, &selectedImage); err != nil {
		rows.Close()
		t.Fatal(err)
	}
	rows.Close()
	var portrait struct{ Image, ImageKind string }
	if err = json.Unmarshal(selectedImage, &portrait); err != nil || portrait.Image != portraitPath || portrait.ImageKind != "portrait" {
		t.Fatalf("portrait must precede the key artwork: %s, %v", selectedImage, err)
	}
	// Also check the complete 100-person page size against the populated
	// catalogue. This is a query-plan check, not a 10-million-row load test.
	var pageIDs []string
	if err = pool.QueryRow(ctx, `SELECT array_agg(artist_id::text) FROM (SELECT artist_id FROM artist_key_artworks ORDER BY artist_id LIMIT 100) page`).Scan(&pageIDs); err != nil {
		t.Fatal(err)
	}
	for _, requested := range [][]string{ids, pageIDs} {
		var plan []byte
		if err = pool.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+participantImagesQuery, requested).Scan(&plan); err != nil {
			t.Fatal(err)
		}
		var decoded []struct {
			Plan          map[string]any
			ExecutionTime float64 `json:"Execution Time"`
		}
		if err = json.Unmarshal(plan, &decoded); err != nil {
			t.Fatal(err)
		}
		var inspect func(map[string]any)
		inspect = func(node map[string]any) {
			if node["Node Type"] == "Seq Scan" {
				t.Fatalf("artist image lookup scans a full table: %s", plan)
			}
			if children, ok := node["Plans"].([]any); ok {
				for _, child := range children {
					inspect(child.(map[string]any))
				}
			}
		}
		inspect(decoded[0].Plan)
		t.Logf("%d artist IDs: %.3f ms, indexed image lookups", len(requested), decoded[0].ExecutionTime)
	}
}
