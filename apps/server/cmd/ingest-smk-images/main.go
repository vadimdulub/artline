// Selected authentic museum reproductions only. Selection and application are
// separate runs. No cloud targets, source crawling, original-size downloads,
// replacement of existing media, or publication.
package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"image/jpeg"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

const metadataSHA = "5ca7c08c06568ffeec711ec88f5ec7f525ee178913dee45918d7000df67edd53"
const approvedImagesSHA = "17a6c25903f8eeacd06f57e88c2ffdd1572e14f85358619af9ee2ca5c1207f23"
const pdm = "https://creativecommons.org/publicdomain/mark/1.0/"
const scheme = "european-smk-statens-museum-for-kunst-object"
const actor = "local-european-research"

var service = regexp.MustCompile(`^https://iip\.smk\.dk/iiif/jp2/[A-Za-z0-9_.-]+$`)

type selected struct {
	ID, Object, Title, Artist, ArtistID, Page, URL string
	Raw                                            map[string]any
}
type selection struct {
	Source      string
	Retrieved   time.Time
	MetadataSHA string
	Images      []selected
}
type imageResult struct {
	Object, Outcome, Path, Hash, Error string
	Bytes                              int
	Width, Height, Quality             int
}
type report struct {
	Applied                            bool
	Selected, Added, Preserved, Failed int
	Results                            []imageResult
}

func hash(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func writeNew(p string, v any) error {
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return e
	}
	return writeBytes(p, append(b, '\n'))
}
func writeBytes(p string, b []byte) error {
	f, e := os.OpenFile(p, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	_, e = f.Write(b)
	ce := f.Close()
	if e != nil {
		return e
	}
	return ce
}
func rawString(r map[string]any, k string) string { s, _ := r[k].(string); return s }

func selectImages(ctx context.Context, pool *pgxpool.Pool, root string) (selection, error) {
	out := selection{Source: "smk", MetadataSHA: metadataSHA, Images: []selected{}}
	dir := filepath.Join(root, "docs/research/europe-ui-20260910/smk-v1")
	b, e := os.ReadFile(filepath.Join(dir, "manifest.json"))
	if e != nil {
		return out, e
	}
	if hash(b) != metadataSHA {
		return out, errors.New("unreviewed metadata")
	}
	var m struct {
		Chunks []struct {
			File string
			SHA  string `json:"sha256"`
		}
	}
	if e = json.Unmarshal(b, &m); e != nil {
		return out, e
	}
	candidates := map[string]map[string]any{}
	ids := []string{}
	for _, c := range m.Chunks {
		if c.File != filepath.Base(c.File) {
			return out, errors.New("unsafe chunk")
		}
		b, e = os.ReadFile(filepath.Join(dir, c.File))
		if e != nil || hash(b) != c.SHA {
			return out, errors.New("changed chunk")
		}
		var chunk struct {
			Works []struct {
				Raw map[string]any `json:"source_raw"`
			}
		}
		if e = json.Unmarshal(b, &chunk); e != nil {
			return out, e
		}
		for _, w := range chunk.Works {
			r := w.Raw
			id := rawString(r, "object_number")
			if r["has_image"] == true && r["public_domain"] == true && rawString(r, "rights") == pdm && service.MatchString(rawString(r, "image_iiif_id")) {
				candidates[id] = r
				ids = append(ids, id)
			}
		}
	}
	b, e = os.ReadFile(filepath.Join(root, "content/imports/europe-smk-20260910/page-001.json.snapshot.json"))
	if e != nil {
		return out, e
	}
	var snap struct {
		Retrieved time.Time `json:"retrieved_at"`
	}
	if e = json.Unmarshal(b, &snap); e != nil {
		return out, e
	}
	out.Retrieved = snap.Retrieved
	// One bounded source set, at most three images per artist. Popularity is only
	// a presentation priority; it never becomes a museum-highlight assertion.
	rows, e := pool.Query(ctx, `WITH ranked AS (
 SELECT a.id::text,e.external_id,a.title,p.display_name,p.id::text AS artist_id,e.canonical_url,
 coalesce(s.is_popular,false) AS popular,
 row_number() OVER(PARTITION BY p.id ORDER BY a.creation_year_start,e.external_id) AS n
 FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
 JOIN artwork_artists aa ON aa.artwork_id=a.id AND aa.attribution_role='primary'
 JOIN artists p ON p.id=aa.artist_id LEFT JOIN artist_discovery_selection s ON s.artist_id=p.id
 WHERE e.entity_type='artwork' AND e.scheme=$1 AND e.external_id=ANY($2::text[])
 AND a.primary_media_id IS NULL AND a.status='review'
 ) SELECT id,external_id,title,display_name,artist_id,canonical_url FROM ranked WHERE n<=3
 ORDER BY n,popular DESC,display_name,external_id LIMIT 80`, scheme, ids)
	if e != nil {
		return out, e
	}
	defer rows.Close()
	for rows.Next() {
		var x selected
		if e = rows.Scan(&x.ID, &x.Object, &x.Title, &x.Artist, &x.ArtistID, &x.Page); e != nil {
			return out, e
		}
		x.Raw = candidates[x.Object]
		x.URL = rawString(x.Raw, "image_iiif_id") + "/full/!700,700/0/default.jpg"
		out.Images = append(out.Images, x)
	}
	return out, rows.Err()
}

func validate(m selection) error {
	if m.Source != "smk" || m.MetadataSHA != metadataSHA || len(m.Images) < 1 || len(m.Images) > 80 || time.Since(m.Retrieved) > 24*time.Hour || time.Until(m.Retrieved) > 5*time.Minute {
		return errors.New("stale or invalid selection")
	}
	seen := map[string]bool{}
	for _, x := range m.Images {
		r := x.Raw
		s := rawString(r, "image_iiif_id")
		if seen[x.Object] || !service.MatchString(s) || r["public_domain"] != true || r["has_image"] != true || rawString(r, "rights") != pdm || rawString(r, "object_number") != x.Object || rawString(r, "frontend_url") != x.Page || x.Page != "https://open.smk.dk/artwork/image/"+x.Object || x.URL != s+"/full/!700,700/0/default.jpg" {
			return errors.New("image identity/rights mismatch")
		}
		seen[x.Object] = true
	}
	return nil
}

func compress(b []byte) ([]byte, int, int, int, error) {
	cfg, e := jpeg.DecodeConfig(bytes.NewReader(b))
	if e != nil {
		return nil, 0, 0, 0, e
	}
	if cfg.Width < 1 || cfg.Height < 1 || cfg.Width > 700 || cfg.Height > 700 {
		return nil, 0, 0, 0, errors.New("unexpected rendition dimensions")
	}
	img, e := jpeg.Decode(bytes.NewReader(b))
	if e != nil {
		return nil, 0, 0, 0, e
	}
	for q := 88; q >= 38; q -= 5 {
		var out bytes.Buffer
		if e = jpeg.Encode(&out, img, &jpeg.Options{Quality: q}); e != nil {
			return nil, 0, 0, 0, e
		}
		if out.Len() <= 100000 {
			return out.Bytes(), cfg.Width, cfg.Height, q, nil
		}
	}
	return nil, 0, 0, 0, errors.New("cannot meet 100000-byte ceiling at acceptable quality")
}

func applyImages(ctx context.Context, pool *pgxpool.Pool, m selection, assets string) (report, error) {
	out := report{Applied: true, Selected: len(m.Images), Results: []imageResult{}}
	if e := validate(m); e != nil {
		return out, e
	}
	if e := os.MkdirAll(assets, 0755); e != nil {
		return out, e
	}
	client := &http.Client{Timeout: 35 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	for _, x := range m.Images {
		var existing *string
		var id string
		e := pool.QueryRow(ctx, `SELECT a.id::text,a.primary_media_id::text FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.scheme=$1 AND e.external_id=$2 AND e.canonical_url=$3 AND a.status='review' AND EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id AND aa.artist_id=$4 AND aa.attribution_role='primary')`, scheme, x.Object, x.Page, x.ArtistID).Scan(&id, &existing)
		if e != nil || id != x.ID {
			return out, fmt.Errorf("artwork identity/state changed: %s", x.Object)
		}
		if existing != nil {
			out.Preserved++
			out.Results = append(out.Results, imageResult{Object: x.Object, Outcome: "existing_media_preserved"})
			continue
		}
		req, e := http.NewRequestWithContext(ctx, "GET", x.URL, nil)
		if e != nil {
			return out, e
		}
		req.Header.Set("User-Agent", "Artline/1.0 (selected public-domain SMK reproductions; 700px local study images)")
		res, e := client.Do(req)
		var original []byte
		status := 0
		if e == nil {
			status = res.StatusCode
			if status != 200 {
				e = fmt.Errorf("HTTP %d", status)
			} else {
				original, e = io.ReadAll(io.LimitReader(res.Body, 2<<20+1))
				if len(original) > 2<<20 {
					e = errors.New("image exceeds 2 MiB transfer ceiling")
				}
			}
			res.Body.Close()
		}
		result := imageResult{Object: x.Object}
		var data []byte
		if e == nil {
			data, result.Width, result.Height, result.Quality, e = compress(original)
		}
		if e != nil {
			out.Failed++
			result.Outcome = "image_deferred"
			result.Error = e.Error()
			out.Results = append(out.Results, result)
			if status == 403 || status == 429 || out.Failed >= 3 {
				return out, fmt.Errorf("source access/failure stop: %w", e)
			}
			continue
		}
		result.Hash = hash(data)
		result.Bytes = len(data)
		name := "smk-" + result.Hash + ".jpg"
		result.Path = "/assets/artworks/imported/" + name
		path := filepath.Join(assets, name)
		if old, e := os.ReadFile(path); e == nil {
			if hash(old) != result.Hash {
				return out, errors.New("existing file mismatch")
			}
		} else if errors.Is(e, os.ErrNotExist) {
			if e = writeBytes(path, data); e != nil {
				return out, e
			}
		} else {
			return out, e
		}
		evidence := map[string]any{"object": x.Raw, "source_url": x.URL, "metadata_retrieved_at": m.Retrieved, "downloaded_at": time.Now().UTC(), "download_sha256": hash(original), "download_bytes": len(original), "derivative_sha256": result.Hash, "derivative_bytes": result.Bytes, "jpeg_quality": result.Quality, "width": result.Width, "height": result.Height, "transform": "museum 700px full-frame IIIF rendition; JPEG recompression only, no crop, no generated content"}
		evidenceBytes, e := json.Marshal(evidence)
		if e != nil {
			return out, e
		}
		tx, e := pool.Begin(ctx)
		if e != nil {
			return out, e
		}
		func() {
			defer tx.Rollback(ctx)
			var current *string
			e = tx.QueryRow(ctx, `SELECT primary_media_id::text FROM artworks WHERE id=$1 AND status='review' FOR UPDATE`, id).Scan(&current)
			if e != nil {
				return
			}
			if current != nil {
				out.Preserved++
				result.Outcome = "concurrent_media_preserved"
				return
			}
			var sid, mediaID string
			e = tx.QueryRow(ctx, `SELECT source_id::text FROM external_identifiers WHERE scheme=$1 AND external_id=$2 AND entity_id=$3`, scheme, x.Object, id).Scan(&sid)
			if e != nil {
				return
			}
			e = tx.QueryRow(ctx, `INSERT INTO media_assets(storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
   VALUES('local',$1,$2,'Statens Museum for Kunst','image/jpeg',$3,$4,$5,$6,$7,'public_domain','Public Domain Mark 1.0',$8,$9,$10,now(),$11,$12) RETURNING id::text`, result.Path, x.Page, result.Width, result.Height, result.Bytes, result.Hash, x.Title+" — "+x.Artist, pdm, x.Artist, x.Artist+". "+x.Title+". Statens Museum for Kunst, Copenhagen. Public domain; compressed study reproduction.", m.Retrieved, actor).Scan(&mediaID)
			if e != nil {
				return
			}
			_, e = tx.Exec(ctx, `INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES($1,$2,$3,$4,$5,$6,'Exact source object, public_domain=true and per-object Public Domain Mark; primary IIIF full-frame rendition','smk-selected-100kb-v1',$7,$8)`, mediaID, sid, x.Object, hash(mustJSON(x.Raw)), x.URL, pdm, m.Retrieved, evidenceBytes)
			if e != nil {
				return
			}
			_, e = tx.Exec(ctx, `UPDATE artworks SET primary_media_id=$2,revision=revision+1,updated_at=now(),updated_by=$3 WHERE id=$1 AND primary_media_id IS NULL`, id, mediaID, actor)
			if e != nil {
				return
			}
			e = tx.Commit(ctx)
			if e == nil {
				out.Added++
				result.Outcome = "attached"
			}
		}()
		out.Results = append(out.Results, result)
		if e != nil {
			return out, e
		}
		fmt.Printf("%s: %s (%d bytes)\n", x.Object, result.Outcome, result.Bytes)
		select {
		case <-ctx.Done():
			return out, ctx.Err()
		case <-time.After(time.Second):
		}
	}
	return out, nil
}
func mustJSON(v any) []byte { b, _ := json.Marshal(v); return b }

func main() {
	root := flag.String("root", "../..", "Project root")
	sel := flag.String("selection", "", "New selection file, or approved input with -apply")
	receipt := flag.String("report", "", "New receipt for apply")
	apply := flag.Bool("apply", false, "Explicit selected download and local DB attach")
	flag.Parse()
	if *sel == "" {
		log.Fatal("-selection required")
	}
	cfg, e := pgxpool.ParseConfig(config.Load().DatabaseURL)
	if e != nil {
		log.Fatal(e)
	}
	local := func(h string) bool {
		return h == "localhost" || h == "127.0.0.1" || h == "::1" || strings.HasPrefix(h, "/")
	}
	if !local(cfg.ConnConfig.Host) {
		log.Fatal("local DB only")
	}
	for _, f := range cfg.ConnConfig.Fallbacks {
		if !local(f.Host) {
			log.Fatal("remote fallback denied")
		}
	}
	ctx := context.Background()
	pool, e := pgxpool.NewWithConfig(ctx, cfg)
	if e != nil {
		log.Fatal(e)
	}
	defer pool.Close()
	if !*apply {
		m, e := selectImages(ctx, pool, *root)
		if e != nil {
			log.Fatal(e)
		}
		if e = validate(m); e != nil {
			log.Fatal(e)
		}
		if e = writeNew(*sel, m); e != nil {
			log.Fatal(e)
		}
		fmt.Printf("Selected %d; no downloads or DB writes. Review and pin file before -apply.\n", len(m.Images))
		return
	}
	if *receipt == "" {
		log.Fatal("-report required")
	}
	f, e := os.OpenFile(*receipt, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		log.Fatal(e)
	}
	defer f.Close()
	b, e := os.ReadFile(*sel)
	if e != nil {
		log.Fatal(e)
	}
	if hash(b) != approvedImagesSHA {
		log.Fatal("unreviewed image selection")
	}
	var m selection
	if e = json.Unmarshal(b, &m); e != nil {
		log.Fatal(e)
	}
	r, runErr := applyImages(ctx, pool, m, filepath.Join(*root, "apps/web/public/assets/artworks/imported"))
	if e = json.NewEncoder(f).Encode(r); e != nil {
		log.Fatal(e)
	}
	if runErr != nil {
		log.Fatal(runErr)
	}
	fmt.Printf("Added %d, preserved %d, failed %d\n", r.Added, r.Preserved, r.Failed)
}
