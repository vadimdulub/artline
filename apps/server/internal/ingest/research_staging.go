package ingest

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"regexp"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type ResearchRecord struct {
	Source   string          `json:"source"`
	Kind     string          `json:"kind"`
	RecordID string          `json:"record_id"`
	Country  string          `json:"country"`
	Name     string          `json:"name"`
	URL      string          `json:"source_url"`
	Decision string          `json:"decision"`
	Raw      json.RawMessage `json:"raw"`
}
type ResearchStageReport struct {
	Applied    bool           `json:"applied"`
	Replayed   bool           `json:"replayed"`
	SnapshotID string         `json:"snapshot_id"`
	SHA        string         `json:"sha256"`
	Records    int            `json:"records"`
	Counts     map[string]int `json:"counts"`
}

func validateResearch(rows []ResearchRecord) error {
	if len(rows) == 0 || len(rows) > 100000 {
		return errors.New("research batch needs 1..100000 records")
	}
	seen := map[string]bool{}
	for _, r := range rows {
		if r.Source != "nga" && r.Source != "wikidata" && r.Source != "museofile" && r.Source != "supplied-registry" {
			return errors.New("unreviewed research source")
		}
		kinds := map[string]bool{"museum_candidate": true, "museum_directory": true, "catalogue_source": true, "catalogue_object": true}
		if !kinds[r.Kind] || r.RecordID == "" || len(r.RecordID) > 200 || strings.TrimSpace(r.Name) == "" || len(r.Name) > 4096 || r.Decision == "" || len(r.Decision) > 120 {
			return errors.New("invalid research row")
		}
		u, e := url.Parse(r.URL)
		if e != nil || u.Scheme != "https" || u.Host == "" || u.User != nil || u.Fragment != "" {
			return errors.New("invalid research source URL")
		}
		if len(r.Raw) > 4<<20 || !json.Valid(r.Raw) {
			return errors.New("invalid/oversize evidence JSON")
		}
		key := r.Source + ":" + r.Kind + ":" + r.RecordID
		if seen[key] {
			return fmt.Errorf("duplicate research source ID %s", key)
		}
		seen[key] = true
	}
	return nil
}

// StageResearch stores discovery/source evidence without changing any public
// catalogue entity. The caller must supply the SHA reviewed before execution.
// CopyFrom uses one transaction; a rollback preview exercises the same inserts.
func StageResearch(ctx context.Context, pool *pgxpool.Pool, data []byte, sha, name string, apply bool) (ResearchStageReport, error) {
	out := ResearchStageReport{SHA: checksum(data), Counts: map[string]int{}}
	if !regexp.MustCompile(`^[a-f0-9]{64}$`).MatchString(sha) || out.SHA != sha {
		return out, errors.New("unreviewed research snapshot checksum")
	}
	if len(data) > 128<<20 || len(name) == 0 || len(name) > 160 {
		return out, errors.New("research snapshot exceeds budget/invalid name")
	}
	var rows []ResearchRecord
	if e := json.Unmarshal(data, &rows); e != nil {
		return out, e
	}
	if e := validateResearch(rows); e != nil {
		return out, e
	}
	out.Records = len(rows)
	for _, r := range rows {
		out.Counts[r.Source+"/"+r.Kind+"/"+r.Decision]++
	}
	tx, e := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.Serializable})
	if e != nil {
		return out, e
	}
	defer tx.Rollback(ctx)
	if _, e = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(2026090911)`); e != nil {
		return out, e
	}
	if _, e = tx.Exec(ctx, `SET LOCAL statement_timeout='30s'`); e != nil {
		return out, e
	}
	var oldCount int
	e = tx.QueryRow(ctx, `SELECT id::text,record_count FROM research_snapshots WHERE sha256=$1`, sha).Scan(&out.SnapshotID, &oldCount)
	if e == nil {
		if oldCount != len(rows) {
			return out, errors.New("snapshot record count conflict")
		}
		out.Replayed = true
	} else if errors.Is(e, pgx.ErrNoRows) {
		e = tx.QueryRow(ctx, `INSERT INTO research_snapshots(sha256,snapshot_name,record_count) VALUES($1,$2,$3) RETURNING id::text`, sha, name, len(rows)).Scan(&out.SnapshotID)
		if e != nil {
			return out, e
		}
		_, e = tx.CopyFrom(ctx, pgx.Identifier{"research_records"}, []string{"snapshot_id", "source_key", "record_kind", "source_record_id", "country_code", "display_name", "source_url", "decision", "raw_json"}, pgx.CopyFromSlice(len(rows), func(i int) ([]any, error) {
			r := rows[i]
			return []any{out.SnapshotID, r.Source, r.Kind, r.RecordID, r.Country, r.Name, r.URL, r.Decision, r.Raw}, nil
		}))
		if e != nil {
			return out, e
		}
	} else {
		return out, e
	}
	if !apply {
		return out, tx.Rollback(ctx)
	}
	if e = tx.Commit(ctx); e != nil {
		return out, e
	}
	out.Applied = true
	return out, nil
}
