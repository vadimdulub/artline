package main

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

func assembleSelectedImages(ctx context.Context, root, out string) error {
	path := filepath.Join(root, "content/imports/nga-selected-images-20260909/published_images_prefix.csv")
	if e := verify(path); e != nil {
		return e
	}
	b, e := os.ReadFile(path + ".snapshot.json")
	if e != nil {
		return e
	}
	var snap snapshot
	if e = json.Unmarshal(b, &snap); e != nil {
		return e
	}
	f, e := os.Open(path)
	if e != nil {
		return e
	}
	defer f.Close()
	r := csv.NewReader(f)
	h, e := r.Read()
	if e != nil {
		return e
	}
	pool, e := pgxpool.New(ctx, config.Load().DatabaseURL)
	if e != nil {
		return e
	}
	defer pool.Close()
	host := pool.Config().ConnConfig.Host
	if host != "localhost" && host != "127.0.0.1" && host != "::1" && !strings.HasPrefix(host, "/") {
		return errors.New("local only")
	}
	for _, fallback := range pool.Config().ConnConfig.Fallbacks {
		h := fallback.Host
		if h != "localhost" && h != "127.0.0.1" && h != "::1" && !strings.HasPrefix(h, "/") {
			return errors.New("remote fallback denied")
		}
	}
	stat, e := f.Stat()
	if e != nil {
		return e
	}
	selected := []map[string]any{}
	complete := 0
	for {
		v, e := r.Read()
		if e == io.EOF {
			break
		}
		if e != nil {
			// Only the final, deliberately truncated prefix row may be ignored.
			// A malformed interior row must stop the selection.
			if r.InputOffset() == stat.Size() && (errors.Is(e, csv.ErrQuote) || errors.Is(e, csv.ErrFieldCount)) {
				break
			}
			return e
		}
		complete++
		row := map[string]string{}
		for i, k := range h {
			row[strings.ToLower(k)] = v[i]
		}
		if row["openaccess"] != "1" || row["viewtype"] != "primary" {
			continue
		}
		var id, title, kind, credit string
		var popular bool
		e = pool.QueryRow(ctx, `SELECT a.id::text,a.title,a.work_type,coalesce(string_agg(p.display_name,', '),''),coalesce(bool_or(ds.is_popular),false) FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id LEFT JOIN artwork_artists aa ON aa.artwork_id=a.id LEFT JOIN artists p ON p.id=aa.artist_id LEFT JOIN artist_discovery_selection ds ON ds.artist_id=p.id WHERE e.entity_type='artwork' AND e.scheme='european-nga-object' AND e.external_id=$1 AND a.primary_media_id IS NULL AND a.status='review' GROUP BY a.id`, row["depictstmsobjectid"]).Scan(&id, &title, &kind, &credit, &popular)
		if e != nil {
			if strings.Contains(e.Error(), "no rows") {
				continue
			}
			return e
		}
		selected = append(selected, map[string]any{"artwork_id": id, "object_id": row["depictstmsobjectid"], "title": title, "work_type": kind, "artist": credit, "popular": popular, "image_uuid": row["uuid"], "openaccess": row["openaccess"], "url": row["iiifurl"] + "/full/!600,600/0/default.jpg", "alt_text": row["assistivetext"], "raw": row})
	}
	sort.SliceStable(selected, func(i, j int) bool {
		a, b := selected[i], selected[j]
		if (a["work_type"] == "painting") != (b["work_type"] == "painting") {
			return a["work_type"] == "painting"
		}
		return a["popular"].(bool) && !b["popular"].(bool)
	})
	eligible := len(selected)
	if len(selected) > 20 {
		selected = selected[:20]
	}
	e = save(filepath.Join(out, "images.json"), map[string]any{"source": "nga", "source_url": snap.URL, "source_snapshot_sha256": snap.SHA, "retrieved_at": snap.Retrieved, "selection": "First256KiB prefix sample; complete CSV rows only; primary openaccess=1; missing local media; prefer paintings then popular artists. Not exhaustive.", "complete_source_rows": complete, "eligible_candidates": eligible, "images": selected})
	if e != nil {
		return e
	}
	sha, n, e := hashFile(filepath.Join(out, "images.json"))
	if e != nil {
		return e
	}
	fmt.Println(sha, n, complete, eligible, len(selected))
	return nil
}
