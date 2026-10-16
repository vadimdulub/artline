package catalog

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func TestConnectionCursorScope(t *testing.T) {
	c := connectionCursor{"00000000-0000-0000-0000-000000000001", "incoming", 0, "Person", "00000000-0000-0000-0000-000000000002"}
	b, _ := json.Marshal(c)
	raw := base64.RawURLEncoding.EncodeToString(b)
	if _, err := parseConnectionCursor(raw, c.Artist, c.Direction); err != nil {
		t.Fatal(err)
	}
	for _, tc := range []struct{ raw, artist, direction string }{{raw, "other", c.Direction}, {raw, c.Artist, "outgoing"}, {"broken", c.Artist, c.Direction}, {"", c.Artist, "both"}, {strings.Repeat("x", 4097), c.Artist, c.Direction}} {
		if _, err := parseConnectionCursor(tc.raw, tc.artist, tc.direction); err == nil {
			t.Fatal("invalid cursor accepted", tc.artist, tc.direction)
		}
	}
}

// These fixtures are VALUES expressions scoped to a SELECT in an enforced
// read-only transaction. No tables, test databases or catalogue rows are created.
const connectionsSelectFixtures = `WITH artists AS (
 SELECT ('00000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid id,
 'artist-'||n slug, 'Person '||n display_name, CASE WHEN n=5 THEN 'archived' ELSE 'review' END status
 FROM generate_series(1,8) n
), sources AS (
 SELECT n::uuid id,n::text name,true is_active,1 priority FROM (VALUES ('10000000-0000-0000-0000-000000000001')) v(n)
 UNION ALL SELECT '10000000-0000-0000-0000-000000000002'::uuid,'Inactive',false,1
), influence_claims AS (
 SELECT ('20000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid id,
 CASE WHEN src IS NULL THEN NULL ELSE ('00000000-0000-0000-0000-'||lpad(src::text,12,'0'))::uuid END source_artist_id,
 'Unresolved label'::text source_label,'00000000-0000-0000-0000-000000000001'::uuid target_artist_id,
 typ relationship_type,lev evidence_level,'Exact source note'::text evidence_note,status
 FROM (VALUES (1,2,'documented_admiration','documented','review'),(2,2,'influenced','editorial_inference','review'),
 (3,3,'teacher_of','editorial_inference','review'),(4,4,'influenced','editorial_inference','review'),
 (5,NULL,'influenced','editorial_inference','review'),(6,NULL,'teacher_of','editorial_inference','review'),
 (7,5,'influenced','documented','review'),(8,6,'influenced','documented','review'),(9,7,'influenced','documented','archived')) v(n,src,typ,lev,status)
), citations AS (
 SELECT id entity_id,'influence'::text entity_type,
 CASE WHEN id='20000000-0000-0000-0000-000000000008'::uuid THEN '10000000-0000-0000-0000-000000000002'::uuid ELSE '10000000-0000-0000-0000-000000000001'::uuid END source_id,
 'influence'::text field_name,'https://example.org/original'::text source_url,'Internal note'::text evidence_note
 FROM influence_claims
)`

type connectionsReadOnlyFixtureDB struct{ pgx.Tx }

func fixtureConnectionSQL(q string) string {
	if strings.HasPrefix(q, "WITH ") {
		return connectionsSelectFixtures + ", " + strings.TrimPrefix(q, "WITH ")
	}
	return connectionsSelectFixtures + " " + q
}
func (db connectionsReadOnlyFixtureDB) Query(ctx context.Context, q string, args ...any) (pgx.Rows, error) {
	return db.Tx.Query(ctx, fixtureConnectionSQL(q), args...)
}
func (db connectionsReadOnlyFixtureDB) QueryRow(ctx context.Context, q string, args ...any) pgx.Row {
	return db.Tx.QueryRow(ctx, fixtureConnectionSQL(q), args...)
}

func TestArtistConnectionsPagesReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("set ARTLINE_READONLY_DATABASE_URL")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	repo := &Repository{db: connectionsReadOnlyFixtureDB{tx}}
	id := "00000000-0000-0000-0000-000000000001"
	page, err := repo.artistConnectionPage(WithPublicRead(ctx), id, "incoming", "")
	if err != nil {
		t.Fatal(err)
	}
	if page.Total != 5 || len(page.Items) != 3 || page.NextCursor == "" {
		t.Fatalf("wrong initial page: %+v", page)
	}
	if len(page.Items[0].Claims) != 2 {
		t.Fatal("person's distinct claims were lost")
	}
	if len(page.Items[0].Claims[0].Citations) != 1 || page.Items[0].Claims[0].Citations[0].EvidenceNote != "" {
		t.Fatal("citation missing or internal note exposed")
	}
	second, err := repo.artistConnectionPage(ctx, id, "incoming", page.NextCursor)
	if err != nil {
		t.Fatal(err)
	}
	if second.Total != 5 || len(second.Items) != 2 || second.NextCursor != "" {
		t.Fatalf("wrong final page: %+v", second)
	}
	if second.Items[0].ID == second.Items[1].ID || second.Items[0].Slug != nil || second.Items[1].Slug != nil {
		t.Fatal("unresolved labels were merged or given an artist identity")
	}
	outgoing, err := repo.artistConnectionPage(ctx, id, "outgoing", "")
	if err != nil {
		t.Fatal(err)
	}
	if outgoing.Total != 0 || len(outgoing.Items) != 0 {
		t.Fatal("directions leaked", outgoing)
	}
	outgoing, err = repo.artistConnectionPage(ctx, "00000000-0000-0000-0000-000000000002", "outgoing", "")
	if err != nil {
		t.Fatal(err)
	}
	if outgoing.Total != 1 || len(outgoing.Items) != 1 || outgoing.Items[0].ID != id || len(outgoing.Items[0].Claims) != 2 || outgoing.Items[0].Claims[0].Direction != "outgoing" {
		t.Fatal("outgoing connections lost target identity or claims", outgoing)
	}
	_, err = repo.artistConnectionPage(ctx, id, "outgoing", page.NextCursor)
	if err != ErrConnectionsFilter {
		t.Fatal("wrong-direction cursor accepted", err)
	}
}
