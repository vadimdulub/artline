// export-research exports the real catalogue without changing database or media.
package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	_ "image/jpeg"
	_ "image/png"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/jackc/pgx/v5"
)

var header = []string{"Painter", "artwork", "year", "museum", "country", "hasPicture"}

// Aggregate relationships separately so multiple creators, venues, and media
// never multiply artwork rows. This full-catalogue export is not an API query.
const exportQuery = `DECLARE research_export NO SCROLL CURSOR FOR
WITH creators AS (
 SELECT aa.artwork_id,string_agg(a.display_name || CASE aa.attribution_role
 WHEN 'primary' THEN '' WHEN 'attributed_to' THEN ' (attributed to)'
 WHEN 'workshop' THEN ' (workshop)' WHEN 'circle_of' THEN ' (circle of)'
 WHEN 'follower_of' THEN ' (follower of)'
 WHEN 'formerly_attributed_to' THEN ' (formerly attributed to)' END,
 ' ; ' ORDER BY a.display_name,aa.attribution_role) AS names
 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id GROUP BY aa.artwork_id
), institution_countries AS (
 SELECT ic.institution_id,string_agg(DISTINCT c.name,' ; ' ORDER BY c.name) AS names
 FROM (
 SELECT id AS institution_id,place_id FROM institutions WHERE place_id IS NOT NULL
 UNION SELECT institution_id,place_id FROM institution_venues WHERE status <> 'archived'
 ) ic JOIN places p ON p.id=ic.place_id JOIN countries c ON c.code=p.country_code
 GROUP BY ic.institution_id
), pictures AS (
 SELECT artwork_id,array_agg(DISTINCT media_id::text) AS ids FROM (
 SELECT id AS artwork_id,primary_media_id AS media_id FROM artworks WHERE primary_media_id IS NOT NULL
 UNION ALL SELECT artwork_id,media_id FROM artwork_media
 ) links GROUP BY artwork_id
)
SELECT coalesce(nullif(cr.names,''),nullif(w.unlinked_creator_label,''),'Unknown artist'),
 w.title,w.date_display,coalesce(i.name,''),coalesce(ic.names,''),coalesce(pic.ids,ARRAY[]::text[])
FROM artworks w LEFT JOIN creators cr ON cr.artwork_id=w.id
LEFT JOIN institutions i ON i.id=w.current_institution_id
LEFT JOIN institution_countries ic ON ic.institution_id=i.id
LEFT JOIN pictures pic ON pic.artwork_id=w.id
ORDER BY 1,w.title,w.date_display,w.id`

func main() {
	dsn := flag.String("database-url", "postgres://localhost/artline?sslmode=disable", "Database (read-only transaction)")
	public := flag.String("public", "../web/public", "Local public asset root")
	out := flag.String("out", "", "New CSV path; existing files are never overwritten")
	flag.Parse()
	if err := run(*dsn, *public, *out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(dsn, public, out string) error {
	if out == "" {
		return fmt.Errorf("-out is required")
	}
	root, err := filepath.Abs(public)
	if err != nil {
		return err
	}
	root, err = filepath.EvalSymlinks(root)
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	conn, err := pgx.Connect(ctx, dsn)
	if err != nil {
		return err
	}
	defer conn.Close(context.Background())
	tx, err := conn.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		return err
	}
	defer tx.Rollback(context.Background())
	if _, err = tx.Exec(ctx, "SET LOCAL statement_timeout='120s'"); err != nil {
		return err
	}
	var total int
	var snapshot time.Time
	if err = tx.QueryRow(ctx, "SELECT count(*),transaction_timestamp() FROM artworks").Scan(&total, &snapshot); err != nil {
		return err
	}
	validMedia := map[string]bool{}
	mediaIssues := map[string]string{}
	media, err := tx.Query(ctx, "SELECT id::text,storage_kind,coalesce(storage_path,'') FROM media_assets ORDER BY id")
	if err != nil {
		return err
	}
	for media.Next() {
		var id, kind, path string
		if err = media.Scan(&id, &kind, &path); err != nil {
			media.Close()
			return err
		}
		if kind != "local" {
			mediaIssues[id] = "Not a local image"
			continue
		}
		if err = checkImage(root, path); err != nil {
			mediaIssues[id] = err.Error()
		} else {
			validMedia[id] = true
		}
	}
	if err = media.Err(); err != nil {
		return err
	}
	media.Close()
	if _, err = tx.Exec(ctx, exportQuery); err != nil {
		return err
	}
	if err = os.MkdirAll(filepath.Dir(out), 0755); err != nil {
		return err
	}
	f, err := os.OpenFile(out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		return err
	}
	defer f.Close()
	w := csv.NewWriter(f)
	if err = w.Write(header); err != nil {
		return err
	}
	count, pictures, escaped, missingCountry := 0, 0, 0, 0
	for {
		rows, err := tx.Query(ctx, "FETCH FORWARD 1000 FROM research_export")
		if err != nil {
			return err
		}
		n := 0
		for rows.Next() {
			r := make([]string, 6)
			var ids []string
			if err = rows.Scan(&r[0], &r[1], &r[2], &r[3], &r[4], &ids); err != nil {
				rows.Close()
				return err
			}
			has := false
			for _, id := range ids {
				has = has || validMedia[id]
			}
			r[5] = strconv.FormatBool(has)
			if has {
				pictures++
			}
			if r[4] == "" {
				missingCountry++
			}
			for i := 0; i < 5; i++ {
				s := safeCell(r[i])
				if s != r[i] {
					escaped++
				}
				r[i] = s
			}
			if err = w.Write(r); err != nil {
				rows.Close()
				return err
			}
			count++
			n++
		}
		if err = rows.Err(); err != nil {
			return err
		}
		rows.Close()
		if n == 0 {
			break
		}
	}
	w.Flush()
	if err = w.Error(); err != nil {
		return err
	}
	if err = f.Close(); err != nil {
		return err
	}
	if count != total {
		return fmt.Errorf("row mismatch: exported %d, database %d", count, total)
	}
	if err = tx.Commit(ctx); err != nil {
		return err
	}
	if err = verifyCSV(out, count, pictures); err != nil {
		return err
	}
	file, err := os.Open(out)
	if err != nil {
		return err
	}
	hash := sha256.New()
	_, err = io.Copy(hash, file)
	file.Close()
	if err != nil {
		return err
	}
	return json.NewEncoder(os.Stdout).Encode(map[string]any{
		"file": out, "snapshot_utc": snapshot.UTC(), "artwork_rows": count, "hasPicture_true": pictures,
		"hasPicture_false": count - pictures, "valid_local_images": len(validMedia), "media_issues": mediaIssues,
		"blank_country_rows": missingCountry, "formula_escaped_cells": escaped, "csv_roundtrip_verified": true,
		"sha256": fmt.Sprintf("%x", hash.Sum(nil)), "database_read_only": true,
	})
}

func safeCell(s string) string {
	t := strings.TrimSpace(s)
	if t != "" && strings.ContainsRune("=+-@", rune(t[0])) {
		return "'" + s
	}
	return s
}

func checkImage(root, asset string) error {
	if !strings.HasPrefix(asset, "/assets/") || strings.Contains(asset, "\\") {
		return fmt.Errorf("Unsafe asset path")
	}
	path, err := filepath.EvalSymlinks(filepath.Join(root, filepath.FromSlash(strings.TrimPrefix(asset, "/"))))
	if err != nil {
		return err
	}
	rel, err := filepath.Rel(root, path)
	if err != nil || !filepath.IsLocal(rel) {
		return fmt.Errorf("Asset outside public root")
	}
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	st, err := f.Stat()
	if err != nil {
		return err
	}
	if !st.Mode().IsRegular() || st.Size() <= 0 || st.Size() > 32<<20 {
		return fmt.Errorf("Invalid image file size/type")
	}
	b, err := io.ReadAll(io.LimitReader(f, 32<<20+1))
	if err != nil {
		return err
	}
	cfg, _, err := image.DecodeConfig(bytes.NewReader(b))
	if err != nil {
		return err
	}
	if cfg.Width <= 0 || cfg.Height <= 0 || int64(cfg.Width)*int64(cfg.Height) > 40_000_000 {
		return fmt.Errorf("Invalid/oversize image dimensions")
	}
	_, _, err = image.Decode(bytes.NewReader(b))
	return err
}

func verifyCSV(path string, expected, pictures int) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	r := csv.NewReader(f)
	r.FieldsPerRecord = 6
	h, err := r.Read()
	if err != nil {
		return err
	}
	if !reflect.DeepEqual(h, header) {
		return fmt.Errorf("CSV header mismatch")
	}
	count, yes := 0, 0
	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}
		for _, cell := range row {
			if !utf8.ValidString(cell) {
				return fmt.Errorf("Invalid UTF-8")
			}
		}
		if row[5] != "true" && row[5] != "false" {
			return fmt.Errorf("Invalid hasPicture value")
		}
		if row[5] == "true" {
			yes++
		}
		count++
	}
	if count != expected || yes != pictures {
		return fmt.Errorf("CSV roundtrip count mismatch")
	}
	return nil
}
