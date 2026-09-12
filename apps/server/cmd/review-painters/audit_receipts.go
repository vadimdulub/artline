package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Reconcile recognized successful artwork application receipts, not raw leads.
// Other receipt formats are explicitly listed, never silently called verified.
func auditReceipts(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	if e := newSnapshot(out); e != nil {
		return e
	}
	tx, e := p.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly, IsoLevel: pgx.RepeatableRead})
	if e != nil {
		return e
	}
	defer tx.Rollback(ctx)
	if _, e = tx.Exec(ctx, `SET LOCAL statement_timeout='30s'`); e != nil {
		return e
	}
	type work struct {
		ID      string `json:"artwork_id"`
		Source  string `json:"source_url"`
		Outcome string `json:"outcome"`
	}
	type receipt struct {
		Applied bool
		Works   []work
		Results []json.RawMessage
	}
	stats := map[string]int{}
	seen := map[string]bool{}
	var files, unsupported, failures []map[string]any
	uuid := regexp.MustCompile(`^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$`)
	e = filepath.WalkDir(filepath.Join(root, "output"), func(file string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		if d.Type()&os.ModeSymlink != 0 {
			return nil
		}
		lower := strings.ToLower(file)
		if !strings.HasSuffix(lower, ".json") || (!strings.Contains(lower, "apply") && !strings.Contains(lower, "applied")) {
			return nil
		}
		st, err := d.Info()
		if err != nil {
			return err
		}
		if st.Size() == 0 || st.Size() > 32<<20 {
			unsupported = append(unsupported, map[string]any{"file": file, "reason": "empty or over32MiB scan ceiling", "bytes": st.Size()})
			return nil
		}
		b, err := os.ReadFile(file)
		if err != nil {
			return err
		}
		var r receipt
		if json.Unmarshal(b, &r) != nil || !r.Applied {
			return nil
		}
		stats["successful_receipts_found"]++
		if len(r.Works) == 0 {
			unsupported = append(unsupported, map[string]any{"file": file, "reason": "not an artwork metadata receipt; image/museum/creator formats checked separately", "results": len(r.Results)})
			return nil
		}
		stats["metadata_receipts_checked"]++
		bad := 0
		for start := 0; start < len(r.Works); start += 250 {
			end := min(start+250, len(r.Works))
			ids, urls := []string{}, []string{}
			for _, w := range r.Works[start:end] {
				if !uuid.MatchString(w.ID) || w.Source == "" {
					failures = append(failures, map[string]any{"file": file, "id": w.ID, "reason": "missing or malformed receipt identity"})
					bad++
					continue
				}
				ids = append(ids, w.ID)
				urls = append(urls, w.Source)
				seen[w.ID] = true
			}
			if len(ids) == 0 {
				continue
			}
			rows, err := tx.Query(ctx, `SELECT x.id,a.id IS NOT NULL,EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.canonical_url=x.url) OR EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.source_url=x.url)
 FROM unnest($1::text[],$2::text[]) x(id,url) LEFT JOIN artworks a ON a.id=x.id::uuid`, ids, urls)
			if err != nil {
				return err
			}
			for rows.Next() {
				var id string
				var exists, evidence bool
				if err = rows.Scan(&id, &exists, &evidence); err != nil {
					rows.Close()
					return err
				}
				stats["receipt_work_assertions_checked"]++
				if !exists || !evidence {
					failures = append(failures, map[string]any{"file": file, "id": id, "exists": exists, "source_evidence": evidence})
					bad++
				}
			}
			err = rows.Err()
			rows.Close()
			if err != nil {
				return err
			}
		}
		files = append(files, map[string]any{"file": file, "sha256": digest(b), "works": len(r.Works), "issues": bad})
		if stats["metadata_receipts_checked"]%25 == 0 {
			fmt.Printf("Reconciled %d metadata receipts\n", stats["metadata_receipts_checked"])
		}
		return nil
	})
	if e != nil {
		return e
	}
	stats["distinct_artworks_referenced"] = len(seen)
	stats["failed_assertions"] = len(failures)
	var uncovered []string
	rows, e := tx.Query(ctx, `SELECT id::text FROM artworks ORDER BY id`)
	if e != nil {
		return e
	}
	for rows.Next() {
		var id string
		if e = rows.Scan(&id); e != nil {
			rows.Close()
			return e
		}
		if !seen[id] {
			uncovered = append(uncovered, id)
		}
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	stats["artworks_outside_recognized_receipts"] = len(uncovered)
	uf, e := os.OpenFile(filepath.Join(out, "artworks-outside-recognized-receipts.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	defer uf.Close()
	ue := json.NewEncoder(uf)
	for start := 0; start < len(uncovered); start += 250 {
		end := min(start+250, len(uncovered))
		rows, e = tx.Query(ctx, `SELECT jsonb_build_object('id',a.id,'title',a.title,'created_at',a.created_at,'museum_slug',i.slug,'primary_media_id',a.primary_media_id,'sources',coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'external_id',e.external_id,'url',e.canonical_url)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]'::jsonb),'citation_count',(SELECT count(*) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id)) FROM artworks a LEFT JOIN institutions i ON i.id=a.current_institution_id WHERE a.id=ANY($1::uuid[]) ORDER BY a.id`, uncovered[start:end])
		if e != nil {
			return e
		}
		for rows.Next() {
			var raw json.RawMessage
			if e = rows.Scan(&raw); e != nil {
				rows.Close()
				return e
			}
			if e = ue.Encode(raw); e != nil {
				rows.Close()
				return e
			}
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return e
		}
	}
	if e = tx.Commit(ctx); e != nil {
		return e
	}
	r := map[string]any{"at": time.Now().UTC(), "database_read_only": true, "stats": stats, "checked": files, "failures": failures, "other_or_unread_receipts": unsupported, "limitations": []string{"Only recognized successful artwork-metadata receipt identities and source evidence checked. Existing editorial fields are not overwritten or required to equal old imported titles.", "Raw catalogue captures, deferred candidates and unrecognized receipt formats are not claimed imported.", "Independent library audit verifies every current media file; this report does not re-review image identity or permissions."}}
	if e = save(filepath.Join(out, "reconciliation.json"), encode(r)); e != nil {
		return e
	}
	fmt.Println(string(encode(stats)))
	return nil
}
