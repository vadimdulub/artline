package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"image"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type imageFocusState struct {
	At             time.Time
	Rows           map[string]map[string]string
	VerifiedImages int
}

// Full offline preservation audit. No fixtures, DB writes, or remote image requests.
func auditImageFocus(ctx context.Context, p *pgxpool.Pool, root, out, baseline, receiptPath string) error {
	tx, err := p.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	s := imageFocusState{At: time.Now().UTC(), Rows: map[string]map[string]string{}}
	queries := map[string]string{
		"artworks":     "SELECT id::text,md5((to_jsonb(t)-ARRAY['primary_media_id','revision','updated_at','updated_by'])::text) FROM artworks t ORDER BY id",
		"media_assets": "SELECT id::text,md5(to_jsonb(t)::text) FROM media_assets t ORDER BY id",
		"artists":      "SELECT id::text,md5(to_jsonb(t)::text) FROM artists t ORDER BY id",
		"institutions": "SELECT id::text,md5(to_jsonb(t)::text) FROM institutions t ORDER BY id",
		"attributions": "SELECT artwork_id::text||artist_id::text||attribution_role,md5(to_jsonb(t)::text) FROM artwork_artists t ORDER BY 1",
		"popular":      "SELECT artist_id::text,md5(to_jsonb(t)::text) FROM artist_discovery_selection t ORDER BY 1",
		"selections":   "SELECT collection_id::text||artwork_id::text,md5(to_jsonb(t)::text) FROM curated_collection_items t ORDER BY 1",
	}
	for name, q := range queries {
		rows, e := tx.Query(ctx, q)
		if e != nil {
			return e
		}
		values := map[string]string{}
		for rows.Next() {
			var id, h string
			if e = rows.Scan(&id, &h); e != nil {
				rows.Close()
				return e
			}
			values[id] = h
		}
		if e = rows.Err(); e != nil {
			return e
		}
		rows.Close()
		s.Rows[name] = values
	}
	if baseline != "" {
		b, e := os.ReadFile(baseline)
		if e != nil {
			return e
		}
		var old imageFocusState
		if e = json.Unmarshal(b, &old); e != nil {
			return e
		}
		for table, rows := range old.Rows {
			if table != "media_assets" && len(rows) != len(s.Rows[table]) {
				return fmt.Errorf("%s row count changed", table)
			}
			for id, h := range rows {
				if s.Rows[table][id] != h {
					return fmt.Errorf("%s editorial row changed: %s", table, id)
				}
			}
		}
		b, e = os.ReadFile(receiptPath)
		if e != nil {
			return e
		}
		var r receipt
		if e = json.Unmarshal(b, &r); e != nil {
			return e
		}
		if !r.Applied {
			return fmt.Errorf("receipt is not applied")
		}
		client := &http.Client{Timeout: 15 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return fmt.Errorf("unexpected local redirect") }}
		for _, v := range r.Results {
			if v.ImageOutcome != "attached" {
				continue
			}
			var path, digest, rights, source string
			var size int
			e = tx.QueryRow(ctx, `SELECT m.storage_path,trim(m.checksum_sha256),m.byte_size,m.rights_status,e.source_image_url
 FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=m.id
 WHERE a.id=$1 AND a.status='review' AND e.evidence_json->>'selection_sha256'=$2`, v.ArtworkID, r.SelectionSHA).Scan(&path, &digest, &size, &rights, &source)
			if e != nil {
				return e
			}
			if path != v.Path || digest != v.Hash || size != v.Bytes || size > 100000 || rights != "public_domain" || source == "" {
				return fmt.Errorf("image association/evidence mismatch")
			}
			data, e := os.ReadFile(filepath.Join(root, "apps/web/public", path))
			if e != nil {
				return e
			}
			im, _, e := image.Decode(bytes.NewReader(data))
			if e != nil {
				return e
			}
			if hash(data) != digest || len(data) != size || im.Bounds().Dx() != v.Width || im.Bounds().Dy() != v.Height {
				return fmt.Errorf("image disk mismatch")
			}
			res, e := client.Get("http://127.0.0.1:3000" + path)
			if e != nil {
				return e
			}
			served, e := io.ReadAll(io.LimitReader(res.Body, 100001))
			res.Body.Close()
			if e != nil {
				return e
			}
			if res.StatusCode != 200 || hash(served) != digest {
				return fmt.Errorf("image HTTP delivery mismatch")
			}
			s.VerifiedImages++
		}
		if len(s.Rows["media_assets"])-len(old.Rows["media_assets"]) != s.VerifiedImages {
			return fmt.Errorf("unexpected media count change")
		}
	}
	if err = tx.Commit(ctx); err != nil {
		return err
	}
	if err = save(out, s); err != nil {
		return err
	}
	fmt.Printf("Preservation snapshot: %d artworks, %d media; %d new image associations/files/HTTP responses verified.\n", len(s.Rows["artworks"]), len(s.Rows["media_assets"]), s.VerifiedImages)
	return nil
}
