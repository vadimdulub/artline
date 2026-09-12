package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"image"
	_ "image/jpeg"
	_ "image/png"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type auditMedia struct {
	ID            string `json:"id"`
	Kind          string `json:"kind"`
	Path          string `json:"path"`
	ExpectedBytes *int64 `json:"expected_bytes"`
	ExpectedHash  string `json:"expected_sha256"`
	Width, Height *int
	Rights        string   `json:"rights"`
	Evidence      bool     `json:"rights_evidence_row"`
	Source        string   `json:"source_page"`
	License       string   `json:"license_url"`
	ActualBytes   int64    `json:"actual_bytes"`
	ActualHash    string   `json:"actual_sha256"`
	Decoded       bool     `json:"fully_decoded"`
	FileValid     bool     `json:"file_valid"`
	Issues        []string `json:"issues"`
}

func checkAuditMedia(public string, m *auditMedia) {
	m.Issues = []string{}
	if m.Kind != "local" {
		m.Issues = append(m.Issues, "not_local")
		return
	}
	if !strings.HasPrefix(m.Path, "/assets/") || strings.Contains(m.Path, "\\") {
		m.Issues = append(m.Issues, "unsafe_path")
		return
	}
	file := filepath.Join(public, filepath.FromSlash(strings.TrimPrefix(m.Path, "/")))
	resolved, e := filepath.EvalSymlinks(file)
	if e != nil {
		m.Issues = append(m.Issues, "missing_or_unresolvable_file")
		return
	}
	rel, e := filepath.Rel(public, resolved)
	if e != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		m.Issues = append(m.Issues, "path_outside_public")
		return
	}
	st, e := os.Stat(resolved)
	if e != nil || !st.Mode().IsRegular() {
		m.Issues = append(m.Issues, "not_regular_file")
		return
	}
	m.ActualBytes = st.Size()
	if st.Size() > 32<<20 {
		m.Issues = append(m.Issues, "over_32mib_audit_decode_limit")
		return
	}
	f, e := os.Open(resolved)
	if e != nil {
		m.Issues = append(m.Issues, "read_error")
		return
	}
	b, e := io.ReadAll(io.LimitReader(f, (32<<20)+1))
	f.Close()
	if e != nil || len(b) > 32<<20 {
		m.Issues = append(m.Issues, "read_limit_error")
		return
	}
	m.ActualHash = digest(b)
	if m.ExpectedBytes == nil {
		m.Issues = append(m.Issues, "byte_size_not_recorded")
	} else if *m.ExpectedBytes != int64(len(b)) {
		m.Issues = append(m.Issues, "byte_size_mismatch")
	}
	if m.ExpectedHash == "" {
		m.Issues = append(m.Issues, "checksum_not_recorded")
	} else if m.ExpectedHash != m.ActualHash {
		m.Issues = append(m.Issues, "checksum_mismatch")
	}
	cfg, _, e := image.DecodeConfig(bytes.NewReader(b))
	if e != nil || cfg.Width < 1 || cfg.Height < 1 || int64(cfg.Width)*int64(cfg.Height) > 100_000_000 {
		m.Issues = append(m.Issues, "invalid_or_oversize_dimensions")
		return
	}
	img, _, e := image.Decode(bytes.NewReader(b))
	if e != nil {
		m.Issues = append(m.Issues, "full_decode_failed")
		return
	}
	m.Decoded = true
	if m.Width != nil && *m.Width != img.Bounds().Dx() || m.Height != nil && *m.Height != img.Bounds().Dy() {
		m.Issues = append(m.Issues, "dimensions_mismatch")
	}
	m.FileValid = len(m.Issues) == 0
	if len(b) > 100000 {
		m.Issues = append(m.Issues, "legacy_over_100000_bytes")
	}
	if !m.Evidence {
		m.Issues = append(m.Issues, "rights_evidence_row_missing")
	}
	if m.Source == "" {
		m.Issues = append(m.Issues, "source_page_missing")
	}
	if m.License == "" {
		m.Issues = append(m.Issues, "license_url_missing")
	}
	if m.Rights == "unknown" || m.Rights == "restricted" {
		m.Issues = append(m.Issues, "rights_review_needed")
	}
}

// Audit only: no schema, fixture, mutation, network or implicit image download.
// Keyset pages are bounded at250 media/500 works; the full queue is streamed.
func auditLibrary(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	if e := newSnapshot(out); e != nil {
		return e
	}
	public, e := filepath.Abs(filepath.Join(root, "apps/web/public"))
	if e != nil {
		return e
	}
	public, e = filepath.EvalSymlinks(public)
	if e != nil {
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
	stats := map[string]int64{}
	for key, q := range map[string]string{
		"artworks":                       "SELECT count(*) FROM artworks",
		"artists":                        "SELECT count(*) FROM artists",
		"media":                          "SELECT count(*) FROM media_assets",
		"artworks_with_primary_media":    "SELECT count(*) FROM artworks WHERE primary_media_id IS NOT NULL",
		"artworks_without_primary_media": "SELECT count(*) FROM artworks WHERE primary_media_id IS NULL",
		"eligible_without_primary_media": "SELECT count(*) FROM artworks WHERE primary_media_id IS NULL AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible'",
		"primary_media_missing_artwork_media_link": "SELECT count(*) FROM artworks a WHERE primary_media_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM artwork_media am WHERE am.artwork_id=a.id AND am.media_id=a.primary_media_id)",
		"monet_artworks":           "SELECT count(*) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE ar.slug='claude-monet'",
		"monet_with_primary_media": "SELECT count(*) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id JOIN artworks a ON a.id=aa.artwork_id WHERE ar.slug='claude-monet' AND a.primary_media_id IS NOT NULL",
	} {
		var n int64
		if e = tx.QueryRow(ctx, q).Scan(&n); e != nil {
			return fmt.Errorf("%s: %w", key, e)
		}
		stats[key] = n
	}
	mediaFile, e := os.OpenFile(filepath.Join(out, "media-audit.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	defer mediaFile.Close()
	enc := json.NewEncoder(mediaFile)
	issues := map[string]int64{}
	known := map[string]bool{}
	cursor := "00000000-0000-0000-0000-000000000000"
	for {
		rows, e := tx.Query(ctx, `SELECT id::text,storage_kind,coalesce(storage_path,''),byte_size,coalesce(checksum_sha256,''),width,height,rights_status,EXISTS(SELECT 1 FROM media_rights_evidence e WHERE e.media_id=m.id),coalesce(source_page_url,''),coalesce(license_url,'') FROM media_assets m WHERE id>$1::uuid ORDER BY id LIMIT 250`, cursor)
		if e != nil {
			return e
		}
		batch := []auditMedia{}
		for rows.Next() {
			var m auditMedia
			if e = rows.Scan(&m.ID, &m.Kind, &m.Path, &m.ExpectedBytes, &m.ExpectedHash, &m.Width, &m.Height, &m.Rights, &m.Evidence, &m.Source, &m.License); e != nil {
				rows.Close()
				return e
			}
			batch = append(batch, m)
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return e
		}
		if len(batch) == 0 {
			break
		}
		for _, m := range batch {
			checkAuditMedia(public, &m)
			known[m.Path] = true
			stats["media_checked"]++
			if m.Decoded {
				stats["media_fully_decoded"]++
			}
			if m.FileValid {
				stats["media_file_valid"]++
			}
			if len(m.Issues) == 0 {
				stats["media_all_automated_checks_passed"]++
			}
			for _, s := range m.Issues {
				issues[s]++
			}
			if e = enc.Encode(m); e != nil {
				return e
			}
			cursor = m.ID
		}
		fmt.Printf("Audited %d media files\n", stats["media_checked"])
	}
	// List unexplained local raster files, never delete them automatically.
	var unlinked []string
	e = filepath.WalkDir(filepath.Join(public, "assets/artworks"), func(file string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		ext := strings.ToLower(filepath.Ext(file))
		if ext != ".jpg" && ext != ".jpeg" && ext != ".png" && ext != ".webp" {
			return nil
		}
		rel, e := filepath.Rel(public, file)
		if e != nil {
			return e
		}
		asset := "/" + filepath.ToSlash(rel)
		stats["disk_raster_files"]++
		if !known[asset] {
			unlinked = append(unlinked, asset)
		}
		return nil
	})
	if e != nil {
		return e
	}
	if e = save(filepath.Join(out, "disk-files-without-media-row.json"), encode(unlinked)); e != nil {
		return e
	}
	stats["disk_files_without_media_row"] = int64(len(unlinked))
	queue, e := os.OpenFile(filepath.Join(out, "eligible-missing-image-queue.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	defer queue.Close()
	qenc := json.NewEncoder(queue)
	cursor = "00000000-0000-0000-0000-000000000000"
	for {
		rows, e := tx.Query(ctx, `WITH page AS MATERIALIZED (SELECT * FROM artworks WHERE id>$1::uuid ORDER BY id LIMIT 500)
 SELECT a.id::text,CASE WHEN a.primary_media_id IS NULL AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' THEN jsonb_build_object('artwork_id',a.id,'title',a.title,'date_display',a.date_display,'creation_year_start',a.creation_year_start,'creation_year_end',a.creation_year_end,'date_precision',a.date_precision,'work_type',a.work_type,'status',a.status,'accession',a.accession_number,'museum_slug',i.slug,'museum_name',i.name,'country',pl.country_code,'unlinked_creator',a.unlinked_creator_label,'cultural_context',a.cultural_context,
 'creators',coalesce((SELECT jsonb_agg(jsonb_build_object('id',ar.id,'name',ar.display_name,'slug',ar.slug,'role',aa.attribution_role)) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]'::jsonb),
 'sources',coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'external_id',e.external_id,'url',e.canonical_url)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]'::jsonb),'research_state','not_yet_reconciled_with_prior_checklists') ELSE NULL END FROM page a LEFT JOIN institutions i ON i.id=a.current_institution_id LEFT JOIN places pl ON pl.id=i.place_id ORDER BY a.id`, cursor)
		if e != nil {
			return e
		}
		n := 0
		for rows.Next() {
			var raw json.RawMessage
			if e = rows.Scan(&cursor, &raw); e != nil {
				rows.Close()
				return e
			}
			n++
			if len(raw) == 0 {
				continue
			}
			if e = qenc.Encode(raw); e != nil {
				rows.Close()
				return e
			}
			stats["queued_missing_images"]++
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return e
		}
		if n == 0 {
			break
		}
	}
	if stats["queued_missing_images"] != stats["eligible_without_primary_media"] || stats["media_checked"] != stats["media"] {
		return fmt.Errorf("audit coverage mismatch")
	}
	if e = tx.Commit(ctx); e != nil {
		return e
	}
	report := map[string]any{"at": time.Now().UTC(), "database": "local/artline", "database_read_only": true, "stats": stats, "issues": issues, "queue_cursor": cursor, "limitations": []string{"Automatic file/provenance-field checks are not source-backed identity or licence re-review.", "No HTTP/browser visibility assertions from this offline audit.", "Missing-primary-media queue includes non-paintings already in scope; prior deferred states must be reconciled before fetching.", "No data or image deletion/replacement; unrelated disk files are only listed."}}
	if e = save(filepath.Join(out, "summary.json"), encode(report)); e != nil {
		return e
	}
	md := fmt.Sprintf("# Real database and disk audit\n\nChecked %s, read-only PostgreSQL snapshot.\n\n- Artworks: %d; with primary media: %d; without: %d.\n- Eligible missing-primary-image queue: %d records, streamed in500-record keyset pages.\n- Media rows/files checked: %d; fully decoded: %d; matching recorded file integrity: %d.\n- All automated file/evidence-field checks passed: %d. This is not manual identity/rights completion.\n- Raster files without a media row: %d, listed without deletion.\n- Monet: %d artworks /%d primary images. Browser visibility remains unverified.\n\nSee summary.json, media-audit.jsonl, eligible-missing-image-queue.jsonl and disk-files-without-media-row.json. No database or artwork-file mutations.\n", time.Now().UTC().Format(time.RFC3339), stats["artworks"], stats["artworks_with_primary_media"], stats["artworks_without_primary_media"], stats["queued_missing_images"], stats["media_checked"], stats["media_fully_decoded"], stats["media_file_valid"], stats["media_all_automated_checks_passed"], stats["disk_files_without_media_row"], stats["monet_artworks"], stats["monet_with_primary_media"])
	if e = save(filepath.Join(out, "AUDIT.md"), []byte(md)); e != nil {
		return e
	}
	fmt.Println(string(encode(report)))
	return nil
}
