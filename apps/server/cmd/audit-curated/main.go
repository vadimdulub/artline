// Read-only verification of imported assets against their PostgreSQL evidence.
package main

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	_ "image/jpeg"
	_ "image/png"
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/database"
)

func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}
func run() error {
	root := flag.String("root", "../..", "Artline project root")
	flag.Parse()
	public, err := filepath.Abs(filepath.Join(*root, "apps", "web", "public"))
	if err != nil {
		return err
	}
	ctx := context.Background()
	pool, err := database.Open(ctx, config.Load().DatabaseURL)
	if err != nil {
		return err
	}
	defer pool.Close()
	rows, err := pool.Query(ctx, `SELECT ma.storage_path,trim(ma.checksum_sha256),ma.byte_size,ma.width,ma.height,ma.rights_status,
 e.policy_url,e.source_image_url FROM media_rights_evidence e JOIN media_assets ma ON ma.id=e.media_id ORDER BY ma.storage_path`)
	if err != nil {
		return err
	}
	defer rows.Close()
	count := 0
	var total int64
	for rows.Next() {
		var path, expected, rights, policy, source string
		var size int64
		var width, height int
		if err = rows.Scan(&path, &expected, &size, &width, &height, &rights, &policy, &source); err != nil {
			return err
		}
		if (rights != "cc0" && rights != "public_domain") || !strings.HasPrefix(policy, "https://") || !strings.HasPrefix(source, "https://") {
			return fmt.Errorf("invalid rights evidence for %s", path)
		}
		local, err := filepath.EvalSymlinks(filepath.Join(public, strings.TrimPrefix(path, "/")))
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(public, local)
		if err != nil || strings.HasPrefix(rel, "..") {
			return fmt.Errorf("asset outside public directory")
		}
		f, err := os.Open(local)
		if err != nil {
			return err
		}
		h := sha256.New()
		n, e := io.Copy(h, io.LimitReader(f, 20<<20+1))
		if e != nil {
			f.Close()
			return e
		}
		if n != size || fmt.Sprintf("%x", h.Sum(nil)) != expected {
			f.Close()
			return fmt.Errorf("checksum/size mismatch: %s", path)
		}
		if _, err = f.Seek(0, io.SeekStart); err != nil {
			f.Close()
			return err
		}
		c, _, err := image.DecodeConfig(f)
		f.Close()
		if err != nil || c.Width != width || c.Height != height {
			return fmt.Errorf("dimension mismatch: %s", path)
		}
		count++
		total += n
	}
	if err = rows.Err(); err != nil {
		return err
	}
	var stats []byte
	err = pool.QueryRow(ctx, `SELECT jsonb_build_object(
 'active_painters',(SELECT count(*) FROM artists WHERE status<>'archived'),
 'cohort_painters',(SELECT count(DISTINCT artist_id) FROM painter_import_cohort),
 'popular_painters',(SELECT count(*) FROM artist_discovery_selection ds JOIN artists a ON a.id=ds.artist_id WHERE ds.is_popular AND a.status<>'archived'),
 'popular_without_artworks',(SELECT count(*) FROM artist_discovery_selection ds JOIN artists a ON a.id=ds.artist_id WHERE ds.is_popular AND a.status<>'archived' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa JOIN artworks aw ON aw.id=aa.artwork_id WHERE aa.artist_id=a.id AND aw.status<>'archived')),
 'popular_without_images',(SELECT count(*) FROM artist_discovery_selection ds JOIN artists a ON a.id=ds.artist_id WHERE ds.is_popular AND a.status<>'archived' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa JOIN artworks aw ON aw.id=aa.artwork_id WHERE aa.artist_id=a.id AND aw.status<>'archived' AND aw.primary_media_id IS NOT NULL)),
 'total_artworks',(SELECT count(*) FROM artworks),
 'artworks_with_images',(SELECT count(*) FROM artworks WHERE primary_media_id IS NOT NULL),
 'museum_collections',(SELECT count(*) FROM institutions WHERE status<>'archived'),
 'imported_artworks',(SELECT count(*) FROM artworks WHERE created_by='local-curated-import'),
 'cohort_with_imported_artworks',(SELECT count(DISTINCT c.artist_id) FROM painter_import_cohort c JOIN artwork_artists aa ON aa.artist_id=c.artist_id JOIN artworks aw ON aw.id=aa.artwork_id WHERE aw.created_by='local-curated-import'),
 'cohort_with_images',(SELECT count(DISTINCT c.artist_id) FROM painter_import_cohort c JOIN artwork_artists aa ON aa.artist_id=c.artist_id JOIN artworks aw ON aw.id=aa.artwork_id WHERE aw.primary_media_id IS NOT NULL),
 'scope_violations',(SELECT count(*) FROM artworks WHERE created_by='local-curated-import' AND (artline_creation_scope(creation_year_start,creation_year_end,date_precision)<>'eligible' OR NOT artline_has_selection_evidence(id))),
 'published_painters',(SELECT count(*) FROM artists WHERE status='published'),
 'display_assertions',(SELECT count(*) FROM artwork_location_assertions WHERE claim_type='display'),
 'source_conflicts',(SELECT count(*) FROM import_records WHERE outcome='conflict')
 )`).Scan(&stats)
	if err != nil {
		return err
	}
	var report map[string]any
	if err = json.Unmarshal(stats, &report); err != nil {
		return err
	}
	report["verified_imported_images"] = count
	report["verified_image_bytes"] = total
	if report["scope_violations"].(float64) != 0 {
		return fmt.Errorf("import content policy violations found")
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(report)
}
