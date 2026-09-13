package ingest

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

const expandedInputSHA = "210a729ead48d12b0f228eb9e1fe0c5a6708750b196be38ddfbbb270aa1355c8"

// A plan is generated with read-only queries, then pinned and checked against
// each target's immutable CSV and official-source evidence before any writes.
type ReviewArtwork struct {
	ResearchID  string   `json:"research_id"`
	SnapshotSHA string   `json:"snapshot_sha"`
	Cells       []string `json:"cells"`
	SourceSHA   string   `json:"source_sha"`
	SourceState string   `json:"source_state"`
	ObjectKey   string   `json:"object_key"`
	ObjectURL   string   `json:"object_url"`
	Scheme      string   `json:"scheme"`
	ObjectID    string   `json:"object_id"`
	Creator     string   `json:"creator"`
	Title       string   `json:"title"`
	DateDisplay string   `json:"date_display"`
	First       *int     `json:"first"`
	Last        *int     `json:"last"`
	Precision   string   `json:"precision"`
	WorkType    string   `json:"work_type"`
	Medium      string   `json:"medium"`
	Dimensions  string   `json:"dimensions"`
	Note        string   `json:"note"`
	Excluded    bool     `json:"excluded"`
}
type ReviewChunk struct {
	File    string `json:"file"`
	SHA     string `json:"sha256"`
	Records int    `json:"records"`
}
type ReviewManifest struct {
	InputSHA string         `json:"input_sha256"`
	Chunks   []ReviewChunk  `json:"chunks"`
	Counts   map[string]int `json:"counts"`
}

func planReviewArtwork(rid, snapshot string, cells []string, f *ResolvedFact, sourceSHA, state, note string) (ReviewArtwork, error) {
	p := ReviewArtwork{ResearchID: rid, SnapshotSHA: snapshot, Cells: cells, SourceSHA: sourceSHA, SourceState: state, WorkType: "unknown"}
	if len(cells) != 6 || strings.TrimSpace(cells[0]) == "" || strings.TrimSpace(cells[1]) == "" {
		return p, errors.New("invalid retained CSV record")
	}
	p.Title, p.Creator = cells[1], cells[0]
	p.ObjectKey = "csv:" + expandedInputSHA + ":" + rid
	p.DateDisplay = cells[2]
	d := resolvedLiteral(cells[2])
	p.Note = "Supplied CSV candidate; creator authority, object identity, artwork type and museum connection require review. hasPicture is unverified; no image or display claim."
	if f != nil {
		p.ObjectKey = f.Source + ":" + f.ObjectID
		p.ObjectURL, p.ObjectID = f.ObjectURL, f.ObjectID
		p.Scheme = "european-" + f.Institution.Key + "-object"
		p.Creator, p.DateDisplay = f.Painter.Name, f.DateDisplay
		p.Medium, p.Dimensions = f.Medium, resolvedDimensions(f.Source, f.Dimensions)
		if f.WorkType != "" {
			p.WorkType = f.WorkType
		}
		d = resolvedDate(*f)
		p.Note = "Matched official source; unresolved review reason: " + note + ". Creator identity and museum holding remain unaccepted; no image or current-display claim."
		if state == "conflict" || note == "creator_attribution_review" || qualifiedCreator.MatchString(f.Painter.Name) {
			p.Excluded = true
			p.Note = "Creator attribution hold: " + note + "; retained research evidence, no new artwork."
		}
	}
	if catalog.CreationScope(d.First, d.Last, d.Precision) == "excluded" {
		p.Excluded = true
		p.Note = "Known creation date is after the 1970 cutoff; research evidence retained."
	}
	p.First, p.Last, p.Precision = d.First, d.Last, d.Precision
	if strings.TrimSpace(p.DateDisplay) == "" {
		p.DateDisplay = "Date unknown"
	} else if f == nil || d.Precision == "unknown" {
		p.DateDisplay = "Unverified date: " + p.DateDisplay
	}
	return p, validateReviewArtwork(p)
}
func validateReviewArtwork(p ReviewArtwork) error {
	if !resolvedSHA.MatchString(p.ResearchID) || !resolvedSHA.MatchString(p.SnapshotSHA) || len(p.Cells) != 6 || p.Title != p.Cells[1] || len([]rune(p.Creator)) < 1 || len([]rune(p.Creator)) > 500 {
		return errors.New("invalid review artwork identity")
	}
	if p.SourceSHA == "" {
		if p.ObjectKey != "csv:"+expandedInputSHA+":"+p.ResearchID || p.ObjectURL != "" || p.WorkType != "unknown" || p.Creator != p.Cells[0] {
			return errors.New("invented supplied-only metadata")
		}
	} else if !resolvedSHA.MatchString(p.SourceSHA) || !strings.HasPrefix(p.ObjectURL, "https://") || p.ObjectID == "" {
		return errors.New("invalid source evidence")
	}
	switch p.WorkType {
	case "unknown", "painting", "fresco", "manuscript_illumination", "drawing", "watercolor", "print":
	default:
		return errors.New("invalid artwork type")
	}
	if p.First != nil && p.Last != nil && *p.First > *p.Last {
		return errors.New("reversed creation dates")
	}
	if !p.Excluded && catalog.CreationScope(p.First, p.Last, p.Precision) == "excluded" {
		return errors.New("post-cutoff candidate")
	}
	return nil
}

func PlanReviewArtworks(ctx context.Context, pool *pgxpool.Pool, dir string) (ReviewManifest, error) {
	m := ReviewManifest{InputSHA: expandedInputSHA, Counts: map[string]int{}}
	if err := os.Mkdir(dir, 0755); err != nil {
		return m, err
	}
	after := ""
	for {
		rows, err := pool.Query(ctx, `WITH selected AS MATERIALIZED (
   SELECT r.*,s.sha256 FROM research_records r JOIN research_snapshots s ON s.id=r.snapshot_id
   WHERE r.source_key='supplied-registry' AND r.record_kind='catalogue_object'
   AND r.source_record_id>$1 AND r.source_url=$2 ORDER BY r.source_record_id LIMIT 1000
  ) SELECT r.source_record_id,r.sha256,r.raw_json->'csv'->'cells',r.raw_json->>'input_sha256',
   coalesce(x.facts_json,'null'::jsonb),coalesce(x.facts_sha256,''),coalesce(x.state,''),coalesce(x.note,'')
  FROM selected r LEFT JOIN LATERAL (SELECT facts_json,facts_sha256,state,note FROM research_resolutions
   WHERE research_record_id=r.source_record_id OFFSET 0) x ON true ORDER BY r.source_record_id`, after, expandedCSVURL)
		if err != nil {
			return m, err
		}
		batch := []ReviewArtwork{}
		n := 0
		for rows.Next() {
			var rid, snapshot, inputSHA, sourceSHA, state, note string
			var cells []string
			var raw json.RawMessage
			if err = rows.Scan(&rid, &snapshot, &cells, &inputSHA, &raw, &sourceSHA, &state, &note); err != nil {
				rows.Close()
				return m, err
			}
			if inputSHA != expandedInputSHA || rid == after {
				rows.Close()
				return m, errors.New("unexpected/ambiguous staged identity")
			}
			after = rid
			n++
			m.Counts["staged_entries"]++
			if state == "catalogued" {
				m.Counts["already_catalogued"]++
				continue
			}
			var f *ResolvedFact
			if err = json.Unmarshal(raw, &f); err != nil {
				rows.Close()
				return m, err
			}
			p, err := planReviewArtwork(rid, snapshot, cells, f, sourceSHA, state, note)
			if err != nil {
				rows.Close()
				return m, fmt.Errorf("%s: %w", rid, err)
			}
			batch = append(batch, p)
			if p.Excluded {
				m.Counts["excluded"]++
			} else {
				m.Counts["artwork_candidates"]++
				m.Counts["type_"+p.WorkType]++
				m.Counts["date_"+catalog.CreationScope(p.First, p.Last, p.Precision)]++
			}
		}
		err = rows.Err()
		rows.Close()
		if err != nil {
			return m, err
		}
		if n == 0 {
			break
		}
		if len(batch) > 0 {
			b, err := json.Marshal(batch)
			if err != nil {
				return m, err
			}
			c := ReviewChunk{File: fmt.Sprintf("chunk-%03d.json", len(m.Chunks)+1), SHA: checksum(b), Records: len(batch)}
			if err = os.WriteFile(filepath.Join(dir, c.File), b, 0644); err != nil {
				return m, err
			}
			m.Chunks = append(m.Chunks, c)
		}
	}
	if m.Counts["staged_entries"] != 104934 {
		return m, errors.New("unexpected staged population")
	}
	b, _ := json.MarshalIndent(m, "", "  ")
	return m, os.WriteFile(filepath.Join(dir, "manifest.json"), b, 0644)
}

func ApplyReviewArtworks(ctx context.Context, pool *pgxpool.Pool, data []byte, sha string) (map[string]int64, error) {
	out := map[string]int64{}
	if checksum(data) != sha || len(data) > 8<<20 {
		return out, errors.New("review plan checksum/size mismatch")
	}
	var entries []ReviewArtwork
	if err := json.Unmarshal(data, &entries); err != nil {
		return out, err
	}
	if len(entries) == 0 || len(entries) > 1000 {
		return out, errors.New("review batch requires 1..1000 entries")
	}
	for _, p := range entries {
		if err := validateReviewArtwork(p); err != nil {
			return out, err
		}
	}
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.Serializable})
	if err != nil {
		return out, err
	}
	defer tx.Rollback(ctx)
	// These small temporary batches benefit from ordinary indexed execution.
	// Missing temp-table statistics can inflate the final joins enough to invoke
	// JIT compilation, which is expensive on the shared-core production instance.
	if _, err = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(2026090959); SET LOCAL statement_timeout='300s'; SET LOCAL jit=off;
 CREATE TEMP TABLE review_incoming(rid text PRIMARY KEY,snapshot_sha text,cells jsonb,source_sha text,source_state text,
 object_key text,object_url text,scheme text,oid text,slug text,creator text,title text,normalized_title text,date_display text,
 first_year int,last_year int,precision text,work_type text,medium text,dimensions text,note text,excluded boolean,entry_sha text) ON COMMIT DROP`); err != nil {
		return out, err
	}
	_, err = tx.CopyFrom(ctx, pgx.Identifier{"review_incoming"}, []string{"rid", "snapshot_sha", "cells", "source_sha", "source_state", "object_key", "object_url", "scheme", "oid", "slug", "creator", "title", "normalized_title", "date_display", "first_year", "last_year", "precision", "work_type", "medium", "dimensions", "note", "excluded", "entry_sha"}, pgx.CopyFromSlice(len(entries), func(i int) ([]any, error) {
		p := entries[i]
		return []any{p.ResearchID, p.SnapshotSHA, rawJSON(p.Cells), p.SourceSHA, p.SourceState, p.ObjectKey, p.ObjectURL, p.Scheme, p.ObjectID, "research-candidate-" + checksum([]byte(p.ObjectKey)), p.Creator, p.Title, normalize(p.Title), p.DateDisplay, p.First, p.Last, p.Precision, p.WorkType, p.Medium, p.Dimensions, p.Note, p.Excluded, checksum(rawJSON(p))}, nil
	}))
	if err != nil {
		return out, err
	}
	if _, err = tx.Exec(ctx, `ANALYZE review_incoming;
 CREATE TEMP TABLE review_selected ON COMMIT DROP AS SELECT i.*,r.snapshot_id FROM review_incoming i
 JOIN LATERAL (SELECT snapshot_id,raw_json FROM research_records WHERE source_record_id=i.rid
 AND source_key='supplied-registry' AND record_kind='catalogue_object' AND source_url=$1 OFFSET 0) r
 ON r.raw_json->'csv'->'cells'=i.cells AND r.raw_json->>'input_sha256'=$2
 JOIN research_snapshots s ON s.id=r.snapshot_id AND s.sha256=i.snapshot_sha
 LEFT JOIN LATERAL (SELECT facts_sha256,state FROM research_resolutions WHERE research_record_id=i.rid OFFSET 0) x ON true
 WHERE coalesce(x.facts_sha256,'')=i.source_sha AND coalesce(x.state,'')=i.source_state`, pgx.QueryExecModeSimpleProtocol, expandedCSVURL, expandedInputSHA); err != nil {
		return out, err
	}
	var n int
	if err = tx.QueryRow(ctx, `SELECT count(*) FROM review_selected`).Scan(&n); err != nil {
		return out, err
	}
	if n != len(entries) {
		return out, errors.New("target CSV/source evidence differs from plan")
	}
	if err = tx.QueryRow(ctx, `SELECT count(*) FROM review_selected i JOIN research_artwork_links l ON l.source_key='supplied-registry' AND l.record_kind='catalogue_object' AND l.research_record_id=i.rid WHERE l.entry_sha256<>i.entry_sha`).Scan(&n); err != nil {
		return out, err
	}
	if n != 0 {
		return out, errors.New("changed review plan requires explicit reconciliation")
	}
	if _, err = tx.Exec(ctx, `DELETE FROM review_selected i USING research_artwork_links l WHERE l.source_key='supplied-registry' AND l.record_kind='catalogue_object' AND l.research_record_id=i.rid;
 ANALYZE review_selected;
 CREATE TEMP TABLE review_objects ON COMMIT DROP AS SELECT DISTINCT ON (object_key) i.* FROM review_selected i WHERE NOT excluded ORDER BY object_key,rid;
 ALTER TABLE review_objects ADD COLUMN existing_ids uuid[] NOT NULL DEFAULT '{}';
 UPDATE review_objects i SET existing_ids=ARRAY(SELECT id FROM artworks WHERE id IN (
 SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=i.scheme AND external_id=i.oid AND i.oid<>''
 UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=i.object_url AND i.object_url<>''
 UNION SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=i.object_url AND i.object_url<>''
 UNION SELECT artwork_id FROM research_artwork_links WHERE object_key=i.object_key AND artwork_id IS NOT NULL
 UNION SELECT id FROM artworks WHERE slug=i.slug) ORDER BY id);
 ANALYZE review_objects;
 CREATE TEMP TABLE review_created(id uuid,object_key text) ON COMMIT DROP;
 WITH inserted AS (INSERT INTO artworks(slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,
 medium_text,dimensions_text,unlinked_creator_label,description_md,current_location_unknown_reason,status,research_candidate)
 SELECT slug,title,normalized_title,date_display,first_year,last_year,precision,work_type,nullif(medium,''),nullif(dimensions,''),creator,
 note||E'\n\nSupplied museum label (unverified): '||(cells->>3)||E'\nSupplied country label (unverified): '||(cells->>4),
 'Museum connection and current location require source review','review',true FROM review_objects WHERE cardinality(existing_ids)=0 RETURNING id,slug)
 INSERT INTO review_created SELECT a.id,i.object_key FROM inserted a JOIN review_objects i ON i.slug=a.slug;
 ANALYZE review_created`); err != nil {
		return out, err
	}
	if err = tx.QueryRow(ctx, `SELECT count(*) FROM review_created`).Scan(&n); err != nil {
		return out, err
	}
	out["created_artworks"] = int64(n)
	if _, err = tx.Exec(ctx, `INSERT INTO sources(slug,name,source_type,base_url) VALUES('expanded-csv-review-artworks','Supplied expanded CSV — unverified artwork candidates','manual',$1) ON CONFLICT DO NOTHING;
 INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at)
 SELECT 'artwork',c.id,'supplied_research',s.id,i.rid,$1,i.note||' CSV SHA256: '||$2,now()
 FROM review_created c JOIN review_objects i ON i.object_key=c.object_key CROSS JOIN sources s WHERE s.slug='expanded-csv-review-artworks';
 INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at)
 SELECT 'artwork',c.id,'unresolved_source_match',s.id,i.oid,i.object_url,i.note||' Matched-fact SHA256: '||i.source_sha,now()
 FROM review_created c JOIN review_objects i ON i.object_key=c.object_key CROSS JOIN sources s
 WHERE s.slug='expanded-csv-review-artworks' AND i.object_url<>'';
 INSERT INTO research_artwork_links(snapshot_id,research_record_id,artwork_id,object_key,disposition,possible_artwork_ids,review_note,plan_sha256,entry_sha256)
 SELECT i.snapshot_id,i.rid,CASE WHEN i.excluded THEN NULL WHEN cardinality(o.existing_ids)=1 THEN o.existing_ids[1] ELSE c.id END,
 i.object_key,CASE WHEN i.excluded THEN 'excluded' WHEN cardinality(o.existing_ids)>1 THEN 'existing_conflict'
 WHEN c.id IS NOT NULL THEN 'created' ELSE 'existing' END,coalesce(o.existing_ids,'{}'),i.note,$3,i.entry_sha
 FROM review_selected i LEFT JOIN review_objects o ON o.object_key=i.object_key LEFT JOIN review_created c ON c.object_key=i.object_key`, pgx.QueryExecModeSimpleProtocol, expandedCSVURL, expandedInputSHA, sha); err != nil {
		return out, err
	}
	rows, err := tx.Query(ctx, `SELECT disposition,count(*) FROM research_artwork_links WHERE plan_sha256=$1 GROUP BY disposition`, sha)
	if err != nil {
		return out, err
	}
	for rows.Next() {
		var k string
		var v int64
		if err = rows.Scan(&k, &v); err != nil {
			rows.Close()
			return out, err
		}
		out["entries_"+k] = v
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return out, err
	}
	return out, tx.Commit(ctx)
}
