package books

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

var sourceIDPattern = regexp.MustCompile(`^Q[1-9][0-9]*$`)
var idPattern = regexp.MustCompile(`^[a-z0-9]+(-[a-z0-9]+)*$`)

func ValidateImport(items []Book, expected int) error {
	if len(items) != expected || expected < 1 || expected > 20000 {
		return fmt.Errorf("expected %d books, received %d", expected, len(items))
	}
	ids, sources := map[string]bool{}, map[string]bool{}
	for _, b := range items {
		if !idPattern.MatchString(b.ID) || len(b.ID) > 100 || !sourceIDPattern.MatchString(b.SourceID) || ids[b.ID] || sources[b.SourceID] {
			return fmt.Errorf("duplicate or invalid book identity %q", b.ID)
		}
		ids[b.ID] = true
		sources[b.SourceID] = true
		if b.Status != "review" || b.SourceURL != "https://www.wikidata.org/wiki/"+b.SourceID || strings.TrimSpace(b.Title) == "" || b.Author == "" || b.SelectionBasis == "" || b.DateBasis == "" {
			return fmt.Errorf("missing review provenance for %q", b.ID)
		}
		if (b.StartYear == nil) != (b.EndYear == nil) {
			return fmt.Errorf("partial date interval for %q", b.ID)
		}
		// Review-source validation retains the original research envelope. The
		// separate display cutoff must not invalidate preserved source records.
		if b.StartYear != nil && (*b.StartYear == 0 || *b.EndYear == 0 || *b.StartYear > *b.EndYear || *b.StartYear < Bounds.Start || *b.StartYear > 2026 || *b.EndYear > 5000) {
			return fmt.Errorf("invalid date interval for %q", b.ID)
		}
		seen := map[string]bool{}
		for _, a := range b.Creators {
			if !sourceIDPattern.MatchString(a.ID) || a.SourceURL != "https://www.wikidata.org/wiki/"+a.ID || a.Name == "" || seen[a.ID] {
				return fmt.Errorf("invalid or duplicate creator on %q", b.ID)
			}
			seen[a.ID] = true
		}
	}
	return nil
}

func checksum(raw []byte) string { sum := sha256.Sum256(raw); return hex.EncodeToString(sum[:]) }

// Import inserts only new review records. Repeating the exact same import is
// harmless; any partial/changed collection aborts instead of overwriting edits.
// It never runs migrations or publishes a record.
func Import(ctx context.Context, db *pgxpool.Pool, items []Book) (bool, error) {
	if err := ValidateImport(items, len(items)); err != nil {
		return false, err
	}
	tx, err := db.Begin(ctx)
	if err != nil {
		return false, err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(202609160020)`); err != nil {
		return false, err
	}
	records, links, creatorRows := [][]any{}, [][]any{}, [][]any{}
	creators := map[string]string{}
	hashes := map[string]string{}
	ids := []string{}
	for _, book := range items {
		source, err := json.Marshal(book)
		if err != nil {
			return false, err
		}
		for position, creator := range book.Creators {
			credit := creator.Credit
			creator.Credit = ""
			raw, err := json.Marshal(creator)
			if err != nil {
				return false, err
			}
			hash := checksum(raw)
			if prior, ok := creators[creator.ID]; ok && prior != hash {
				return false, fmt.Errorf("conflicting source details for creator %s", creator.ID)
			} else if !ok {
				creators[creator.ID] = hash
				creatorRows = append(creatorRows, []any{creator.ID, creator.Name, raw, hash})
			}
			links = append(links, []any{book.ID, creator.ID, position, credit})
		}
		book.Creators = []Creator{}
		raw, err := json.Marshal(book)
		if err != nil {
			return false, err
		}
		hash := checksum(source)
		hashes[book.ID] = hash
		ids = append(ids, book.ID)
		records = append(records, []any{book.ID, book.SourceID, "review", raw, hash})
	}
	rows, err := tx.Query(ctx, `SELECT id,source_checksum FROM book_records WHERE id=ANY($1::text[])`, ids)
	if err != nil {
		return false, err
	}
	existing := 0
	for rows.Next() {
		var id, hash string
		if err := rows.Scan(&id, &hash); err != nil {
			rows.Close()
			return false, err
		}
		if hash != hashes[id] {
			rows.Close()
			return false, fmt.Errorf("existing book %s differs; manual reconciliation required", id)
		}
		existing++
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return false, err
	}
	if existing == len(items) {
		return false, nil
	}
	if existing != 0 {
		return false, fmt.Errorf("partial existing import: %d records; manual reconciliation required", existing)
	}
	// Shared creators may already have been researched by a separate book batch.
	for _, row := range creatorRows {
		tag, err := tx.Exec(ctx, `INSERT INTO book_creators(id,name,record,source_checksum) VALUES($1,$2,$3,$4) ON CONFLICT(id) DO UPDATE SET name=book_creators.name WHERE book_creators.source_checksum=excluded.source_checksum`, row...)
		if err != nil {
			return false, err
		}
		if tag.RowsAffected() != 1 {
			return false, fmt.Errorf("existing creator %s differs; manual reconciliation required", row[0])
		}
	}
	if _, err = tx.CopyFrom(ctx, pgx.Identifier{"book_records"}, []string{"id", "source_id", "status", "record", "source_checksum"}, pgx.CopyFromRows(records)); err != nil {
		return false, err
	}
	if _, err = tx.CopyFrom(ctx, pgx.Identifier{"book_creator_links"}, []string{"book_id", "creator_id", "position", "credit"}, pgx.CopyFromRows(links)); err != nil {
		return false, err
	}
	return true, tx.Commit(ctx)
}
