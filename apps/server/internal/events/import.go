package events

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"net/url"
	"regexp"
	"strings"
)

var sourcePattern = regexp.MustCompile(`^Q[1-9][0-9]*$`)

func safeURL(raw string) bool {
	u, err := url.Parse(raw)
	return err == nil && u.Scheme == "https" && u.Hostname() != "" && u.User == nil
}
func ValidateImport(items []Event, expected int) error {
	if expected < 1 || expected > 20000 || len(items) != expected {
		return fmt.Errorf("expected %d events; received %d", expected, len(items))
	}
	seen := map[string]bool{}
	top := 0
	for _, e := range items {
		if !sourcePattern.MatchString(e.SourceID) || e.ID != "event-"+strings.ToLower(e.SourceID) || seen[e.SourceID] {
			return fmt.Errorf("invalid or duplicate event identity %s", e.ID)
		}
		seen[e.SourceID] = true
		if e.Status != "review" || e.SourceURL != "https://www.wikidata.org/wiki/"+e.SourceID || e.SourceRevision < 1 || strings.TrimSpace(e.Title) == "" || e.SelectionBasis == "" || e.DateBasis == "" || e.Years == "" {
			return fmt.Errorf("missing review evidence: %s", e.ID)
		}
		if e.Kind != "Event" && e.Kind != "Period" && e.Kind != "Movement" {
			return fmt.Errorf("invalid kind: %s", e.ID)
		}
		if len(e.Topics) == 0 {
			return fmt.Errorf("missing topic: %s", e.ID)
		}
		for _, terms := range [][]string{e.Topics, e.Countries, e.Regions} {
			unique := map[string]bool{}
			if len(terms) > 32 {
				return fmt.Errorf("too many terms: %s", e.ID)
			}
			for _, term := range terms {
				if strings.TrimSpace(term) == "" || len(term) > 250 || unique[term] {
					return fmt.Errorf("invalid term: %s", e.ID)
				}
				unique[term] = true
			}
		}
		if (e.StartYear == nil) != (e.EndYear == nil) {
			return fmt.Errorf("partial timeline envelope: %s", e.ID)
		}
		if e.StartYear != nil && (*e.StartYear == 0 || *e.EndYear == 0 || *e.StartYear > *e.EndYear || *e.StartYear < Bounds.Start || *e.EndYear > Bounds.End) {
			return fmt.Errorf("date outside historical scope: %s", e.ID)
		}
		for _, links := range [][]Link{e.Sources, e.People, e.Locations} {
			if len(links) > 32 {
				return fmt.Errorf("too many detail links: %s", e.ID)
			}
			for _, l := range links {
				if l.Name == "" || !safeURL(l.URL) {
					return fmt.Errorf("invalid source link: %s", e.ID)
				}
			}
		}
		if e.Top100 {
			top++
			if e.Significance == "" {
				return fmt.Errorf("Top 100 requires editorial context: %s", e.ID)
			}
		}
	}
	if top > 100 {
		return fmt.Errorf("Top 100 contains %d records", top)
	}
	return nil
}

// Atomic, insert-only review import; changed or partial imports require explicit
// reconciliation and never overwrite editorial work or publish a record.
func Import(ctx context.Context, db *pgxpool.Pool, items []Event) (bool, error) {
	if err := ValidateImport(items, len(items)); err != nil {
		return false, err
	}
	tx, err := db.Begin(ctx)
	if err != nil {
		return false, err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(202609170022)`); err != nil {
		return false, err
	}
	records := [][]any{}
	ids := []string{}
	hashes := map[string]string{}
	for _, e := range items {
		raw, err := json.Marshal(e)
		if err != nil {
			return false, err
		}
		sum := sha256.Sum256(raw)
		hash := hex.EncodeToString(sum[:])
		ids = append(ids, e.ID)
		hashes[e.ID] = hash
		records = append(records, []any{e.ID, e.SourceID, "review", raw, hash, e.Topics, e.Countries, e.Regions})
	}
	rows, err := tx.Query(ctx, `SELECT id,source_checksum FROM event_records WHERE id=ANY($1::text[])`, ids)
	if err != nil {
		return false, err
	}
	existing := 0
	for rows.Next() {
		var id, hash string
		if err = rows.Scan(&id, &hash); err != nil {
			rows.Close()
			return false, err
		}
		if hash != hashes[id] {
			rows.Close()
			return false, fmt.Errorf("existing event %s differs; reconciliation required", id)
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
		return false, fmt.Errorf("partial import: %d records already exist", existing)
	}
	if _, err = tx.CopyFrom(ctx, pgx.Identifier{"event_records"}, []string{"id", "source_id", "status", "record", "source_checksum", "topics", "countries", "regions"}, pgx.CopyFromRows(records)); err != nil {
		return false, err
	}
	return true, tx.Commit(ctx)
}
