package events

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/url"
	"reflect"
	"strings"
	"unicode/utf8"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type DescriptionSource struct {
	Name         string `json:"name"`
	URL          string `json:"url"`
	Kind         string `json:"kind"`
	Language     string `json:"language,omitempty"`
	Title        string `json:"title,omitempty"`
	Revision     int64  `json:"revision,omitempty"`
	RetrievedAt  string `json:"retrievedAt,omitempty"`
	License      string `json:"license,omitempty"`
	LicenseURL   string `json:"licenseUrl,omitempty"`
	Notice       string `json:"notice"`
	EvidenceFile string `json:"evidenceFile,omitempty"`
}

type DescriptionUpdate struct {
	ID                  string             `json:"id"`
	PreviousDescription string             `json:"previousDescription"`
	PreviousSource      *DescriptionSource `json:"previousSource,omitempty"`
	Description         string             `json:"description"`
	Source              DescriptionSource  `json:"source"`
}

func ValidateDescriptions(updates []DescriptionUpdate, expected int) error {
	if expected < 1 || expected > 20000 || len(updates) != expected {
		return fmt.Errorf("expected %d description updates, got %d", expected, len(updates))
	}
	seen := map[string]bool{}
	for _, u := range updates {
		if !strings.HasPrefix(u.ID, "event-q") || !sourcePattern.MatchString("Q"+strings.TrimPrefix(u.ID, "event-q")) || seen[u.ID] {
			return fmt.Errorf("invalid or duplicate event %s", u.ID)
		}
		seen[u.ID] = true
		if strings.TrimSpace(u.Description) == "" || utf8.RuneCountInString(u.Description) > 1200 || strings.TrimSpace(u.Source.Name) == "" || u.Source.Notice == "" || !safeURL(u.Source.URL) || (u.Source.LicenseURL != "" && !safeURL(u.Source.LicenseURL)) {
			return fmt.Errorf("missing or invalid description evidence: %s", u.ID)
		}
		parsed, _ := url.Parse(u.Source.URL)
		switch u.Source.Kind {
		case "wikipedia":
			language := u.Source.Language
			if language == "" {
				language = "en"
			}
			supported := map[string]bool{"en": true, "fr": true, "de": true, "es": true, "ru": true, "it": true, "nl": true, "pl": true, "sv": true, "fi": true, "pt": true, "uk": true}
			if !supported[language] || parsed.Host != language+".wikipedia.org" || !strings.HasPrefix(parsed.Path, "/wiki/") || u.Source.Revision < 1 || u.Source.Title == "" || u.Source.RetrievedAt == "" || u.Source.License != "CC BY-SA 4.0" || u.Source.LicenseURL != "https://creativecommons.org/licenses/by-sa/4.0/" {
				return fmt.Errorf("invalid Wikipedia attribution: %s", u.ID)
			}
		case "wikidata":
			if u.Source.URL != "https://www.wikidata.org/wiki/Q"+strings.TrimPrefix(u.ID, "event-q") || u.Source.Revision < 1 || u.Source.License != "CC0" || u.Source.LicenseURL != "https://creativecommons.org/publicdomain/zero/1.0/" {
				return fmt.Errorf("invalid Wikidata attribution: %s", u.ID)
			}
		case "editorial":
			if u.Description != u.PreviousDescription {
				return fmt.Errorf("editorial text must preserve the existing researched description: %s", u.ID)
			}
		default:
			return fmt.Errorf("unknown description source: %s", u.ID)
		}
	}
	return nil
}

// Only these two JSON fields can change. Unknown fields and all existing
// historical metadata survive enrichment, including concurrent editorial work.
func describeRecord(raw []byte, update DescriptionUpdate) ([]byte, bool, error) {
	var record map[string]json.RawMessage
	if err := json.Unmarshal(raw, &record); err != nil {
		return nil, false, err
	}
	var previous string
	if err := json.Unmarshal(record["description"], &previous); err != nil {
		return nil, false, err
	}
	source, err := json.Marshal(update.Source)
	if err != nil {
		return nil, false, err
	}
	if stored, ok := record["descriptionSource"]; ok {
		var decoded DescriptionSource
		if json.Unmarshal(stored, &decoded) == nil {
			encoded, _ := json.Marshal(decoded)
			if previous == update.Description && bytes.Equal(encoded, source) {
				return raw, false, nil
			}
		}
		var actual, expected any
		prior, _ := json.Marshal(update.PreviousSource)
		if update.PreviousSource == nil || json.Unmarshal(stored, &actual) != nil || json.Unmarshal(prior, &expected) != nil || !reflect.DeepEqual(actual, expected) {
			return nil, false, fmt.Errorf("description provenance changed or reconciliation missing for %s", update.ID)
		}
	} else if update.PreviousSource != nil {
		return nil, false, fmt.Errorf("expected description provenance missing for %s", update.ID)
	}
	if previous != update.PreviousDescription {
		return nil, false, fmt.Errorf("description changed for %s; refusing to overwrite it", update.ID)
	}
	record["description"], _ = json.Marshal(update.Description)
	record["descriptionSource"] = source
	result, err := json.Marshal(record)
	return result, true, err
}

// ApplyDescriptions atomically enriches actual review records; it never inserts
// events, changes visibility, or rewrites unrelated metadata.
func ApplyDescriptions(ctx context.Context, db *pgxpool.Pool, updates []DescriptionUpdate) (int, error) {
	if err := ValidateDescriptions(updates, len(updates)); err != nil {
		return 0, err
	}
	tx, err := db.Begin(ctx)
	if err != nil {
		return 0, err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(202609170022)`); err != nil {
		return 0, err
	}
	byID := map[string]DescriptionUpdate{}
	ids := []string{}
	for _, u := range updates {
		byID[u.ID] = u
		ids = append(ids, u.ID)
	}
	rows, err := tx.Query(ctx, `SELECT id,record,status FROM event_records WHERE id=ANY($1::text[]) ORDER BY id FOR UPDATE`, ids)
	if err != nil {
		return 0, err
	}
	prepared := [][]any{}
	found := 0
	for rows.Next() {
		var id, status string
		var raw []byte
		if err = rows.Scan(&id, &raw, &status); err != nil {
			rows.Close()
			return 0, err
		}
		if status != "review" {
			rows.Close()
			return 0, fmt.Errorf("event %s is not in review", id)
		}
		next, changed, prepareErr := describeRecord(raw, byID[id])
		if prepareErr != nil {
			rows.Close()
			return 0, prepareErr
		}
		found++
		if changed {
			sum := sha256.Sum256(next)
			prepared = append(prepared, []any{id, next, hex.EncodeToString(sum[:])})
		}
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return 0, err
	}
	if found != len(updates) {
		return 0, fmt.Errorf("found %d of %d existing review events", found, len(updates))
	}
	if len(prepared) == 0 {
		return 0, nil
	}
	if _, err = tx.Exec(ctx, `CREATE TEMP TABLE artline_event_description_updates(id text PRIMARY KEY, record jsonb NOT NULL, checksum text NOT NULL) ON COMMIT DROP`); err != nil {
		return 0, err
	}
	if _, err = tx.CopyFrom(ctx, pgx.Identifier{"artline_event_description_updates"}, []string{"id", "record", "checksum"}, pgx.CopyFromRows(prepared)); err != nil {
		return 0, err
	}
	tag, err := tx.Exec(ctx, `UPDATE event_records e SET record=u.record,source_checksum=u.checksum FROM artline_event_description_updates u WHERE e.id=u.id AND e.status='review'`)
	if err != nil {
		return 0, err
	}
	if tag.RowsAffected() != int64(len(prepared)) {
		return 0, fmt.Errorf("unexpected update count")
	}
	return len(prepared), tx.Commit(ctx)
}
