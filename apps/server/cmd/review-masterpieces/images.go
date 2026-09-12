package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"image"
	"image/color"
	"image/jpeg"
	_ "image/png"
	"math"
	"os"
	"path/filepath"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

type result struct {
	Object, ArtworkID, Title, Artist, ImageOutcome, Path, Hash, Error string
	HighlightAdded                                                    bool
	Bytes, Width, Height, Quality                                     int
}
type receipt struct {
	Version, SelectionSHA string
	Applied               bool
	Results               []result
}

// Full-frame, aspect-preserving bilinear reduction. Do not upscale small
// originals, crop, or manufacture painted detail. Flatten transparency on white.
func resize(src image.Image, max int) *image.RGBA {
	b := src.Bounds()
	w, h := b.Dx(), b.Dy()
	scale := math.Min(1, float64(max)/float64(maximum(w, h)))
	nw, nh := maximum(1, int(math.Round(float64(w)*scale))), maximum(1, int(math.Round(float64(h)*scale)))
	dst := image.NewRGBA(image.Rect(0, 0, nw, nh))
	sample := func(x, y int) [3]float64 {
		r, g, bv, a := src.At(b.Min.X+x, b.Min.Y+y).RGBA()
		white := uint32(65535) - a
		return [3]float64{float64(r+white) / 257, float64(g+white) / 257, float64(bv+white) / 257}
	}
	for y := 0; y < nh; y++ {
		sy := math.Max(0, (float64(y)+.5)*float64(h)/float64(nh)-.5)
		y0 := int(sy)
		y1 := minimum(h-1, y0+1)
		dy := sy - float64(y0)
		for x := 0; x < nw; x++ {
			sx := math.Max(0, (float64(x)+.5)*float64(w)/float64(nw)-.5)
			x0 := int(sx)
			x1 := minimum(w-1, x0+1)
			dx := sx - float64(x0)
			a, b, c, d := sample(x0, y0), sample(x1, y0), sample(x0, y1), sample(x1, y1)
			v := [3]uint8{}
			for k := range v {
				v[k] = uint8(math.Round((a[k]*(1-dx)+b[k]*dx)*(1-dy) + (c[k]*(1-dx)+d[k]*dx)*dy))
			}
			dst.SetRGBA(x, y, color.RGBA{v[0], v[1], v[2], 255})
		}
	}
	return dst
}
func maximum(a, b int) int {
	if a > b {
		return a
	}
	return b
}
func minimum(a, b int) int {
	if a < b {
		return a
	}
	return b
}
func compress(raw []byte) ([]byte, int, int, int, error) {
	cfg, format, e := image.DecodeConfig(bytes.NewReader(raw))
	if e != nil {
		return nil, 0, 0, 0, e
	}
	if (format != "jpeg" && format != "png") || cfg.Width < 1 || cfg.Height < 1 || cfg.Width > 10000 || cfg.Height > 10000 || int64(cfg.Width)*int64(cfg.Height) > 25_000_000 {
		return nil, 0, 0, 0, errors.New("unsupported or oversized source image")
	}
	src, _, e := image.Decode(bytes.NewReader(raw))
	if e != nil {
		return nil, 0, 0, 0, e
	}
	for _, edge := range []int{900, 750, 600, 480} {
		img := resize(src, edge)
		for q := 88; q >= 58; q -= 5 {
			var buf bytes.Buffer
			if e = jpeg.Encode(&buf, img, &jpeg.Options{Quality: q}); e != nil {
				return nil, 0, 0, 0, e
			}
			if buf.Len() <= 100000 {
				return buf.Bytes(), img.Bounds().Dx(), img.Bounds().Dy(), q, nil
			}
		}
	}
	return nil, 0, 0, 0, errors.New("cannot meet 100000-byte ceiling at approved quality")
}
func validate(s selection) error {
	now := time.Now()
	if s.Version != version || len(s.Entries) > 700 || len(s.Entries) == 0 || now.Sub(s.Created) > 24*time.Hour || s.Created.After(now.Add(5*time.Minute)) {
		return errors.New("invalid or stale selection")
	}
	seen := map[string]bool{}
	for _, x := range s.Entries {
		c, w := x.Candidate, x.Work
		if seen[c.ID] || c.ID == "" || c.Fingerprint == "" || c.SourceID == "" || c.Object != w.ID || now.Sub(x.Retrieved) > 24*time.Hour || x.Retrieved.After(now.Add(5*time.Minute)) || !w.SourceSnapshotAt.Equal(x.Retrieved) {
			return errors.New("duplicate, stale, or incomplete entry")
		}
		seen[c.ID] = true
		var expected ingest.Work
		switch w.Source {
		case "met":
			expected = ingest.NormalizeMet(w.Raw)
			if c.Scheme != "met-object" && c.Scheme != "european-met-the-met-object" {
				return errors.New("source scheme mismatch")
			}
		case "cleveland":
			expected = ingest.NormalizeCleveland(w.Raw)
			if c.Scheme != "cleveland-object" && c.Scheme != "european-cleveland-cleveland-museum-of-art-object" {
				return errors.New("source scheme mismatch")
			}
		default:
			return errors.New("unapproved provider")
		}
		expected.SourceSnapshotAt = x.Retrieved
		if !bytes.Equal(jsonBytes(expected), jsonBytes(w)) || w.Eligible() != "eligible" {
			return errors.New("raw evidence/normalized selection mismatch")
		}
	}
	return nil
}

func apply(ctx context.Context, p *pgxpool.Pool, root, input, pin, out string, do bool) (err error) {
	b, e := os.ReadFile(input)
	if e != nil {
		return e
	}
	if len(pin) != 64 || hash(b) != pin {
		return errors.New("selection checksum does not match reviewed pin")
	}
	var s selection
	if e = json.Unmarshal(b, &s); e != nil {
		return e
	}
	if e = validate(s); e != nil {
		return e
	}
	// Reserve the immutable receipt before any possible external or DB write.
	if e = os.MkdirAll(filepath.Dir(out), 0755); e != nil {
		return e
	}
	f, e := os.OpenFile(out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return e
	}
	defer f.Close()
	r := receipt{Version: version, SelectionSHA: pin, Applied: do, Results: []result{}}
	defer func() {
		if e := json.NewEncoder(f).Encode(r); err == nil {
			err = e
		}
	}()
	fetch := newFetcher()
	for _, x := range s.Entries {
		c, w := x.Candidate, x.Work
		res := result{Object: w.Source + ":" + w.ID, ArtworkID: c.ID, Title: c.Title, Artist: c.Artist, ImageOutcome: "rights_or_image_unavailable"}
		var fingerprint string
		var current *string
		e = p.QueryRow(ctx, `SELECT `+fingerprintSQL+`,a.primary_media_id::text FROM artworks a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artwork' JOIN sources s ON s.id=e.source_id AND s.is_active WHERE a.id=$1 AND e.scheme=$2 AND e.external_id=$3 AND e.source_id=$4 AND a.current_institution_id=$5 AND a.status='review' AND (a.accession_number IS NULL OR a.accession_number=$6)`, c.ID, c.Scheme, c.Object, c.SourceID, c.Institution, w.Accession).Scan(&fingerprint, &current)
		if e != nil || fingerprint != c.Fingerprint {
			return fmt.Errorf("target changed or identity/holding conflict: %s (%v)", res.Object, e)
		}
		if !do {
			if current != nil {
				res.ImageOutcome = "existing_media_preserved"
			} else if w.ImageAllowed() {
				res.ImageOutcome = "ready"
			}
			r.Results = append(r.Results, res)
			continue
		}
		var original, data []byte
		if current != nil {
			res.ImageOutcome = "existing_media_preserved"
		} else if w.ImageAllowed() {
			original, e = fetch.get(ctx, w.ImageURL, 4<<20)
			if e == nil {
				data, res.Width, res.Height, res.Quality, e = compress(original)
			}
			if e != nil {
				res.ImageOutcome = "download_deferred"
				res.Error = e.Error()
				data = nil
			} else {
				res.Hash = hash(data)
				res.Bytes = len(data)
				res.Path = "/assets/artworks/imported/" + w.Source + "-study-" + res.Hash + ".jpg"
				path := filepath.Join(root, "apps/web/public", res.Path)
				if old, e := os.ReadFile(path); e == nil {
					if hash(old) != res.Hash {
						return errors.New("existing content-addressed file mismatch")
					}
				} else if errors.Is(e, os.ErrNotExist) {
					if e = writeNew(path, data); e != nil {
						return e
					}
				} else {
					return e
				}
			}
		}
		tx, e := p.Begin(ctx)
		if e != nil {
			return e
		}
		e = func() error {
			defer tx.Rollback(ctx)
			var fp string
			var media *string
			if e := tx.QueryRow(ctx, `SELECT `+fingerprintSQL+`,a.primary_media_id::text FROM artworks a WHERE id=$1 AND status='review' FOR UPDATE`, c.ID).Scan(&fp, &media); e != nil {
				return e
			}
			if fp != c.Fingerprint {
				return errors.New("concurrent target edit; left derivative on disk unattached")
			}
			// Only append a source-backed museum designation; leave personal lists alone.
			var collection string
			if e := tx.QueryRow(ctx, `SELECT id::text FROM curated_collections WHERE institution_id=$1 AND curator_kind='museum' AND status='review' FOR UPDATE`, c.Institution).Scan(&collection); e != nil {
				return e
			}
			tag, e := tx.Exec(ctx, `INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at) VALUES($1,$2,coalesce((SELECT max(position) FROM curated_collection_items WHERE collection_id=$1),0)+1,$3,$4,$5,$6) ON CONFLICT(collection_id,artwork_id) DO NOTHING`, collection, c.ID, w.SelectionReason, c.SourceID, w.SelectionURL, x.Retrieved)
			if e != nil {
				return e
			}
			res.HighlightAdded = tag.RowsAffected() > 0
			if res.HighlightAdded {
				if _, e = tx.Exec(ctx, `UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=$1`, collection); e != nil {
					return e
				}
			}
			if len(data) > 0 && media == nil {
				policy, provider := "https://www.metmuseum.org/hubs/open-access", "The Metropolitan Museum of Art"
				if w.Source == "cleveland" {
					policy, provider = "https://www.clevelandart.org/open-access", "Cleveland Museum of Art"
				}
				evidence := jsonBytes(map[string]any{"object": w.Raw, "source_snapshot_at": x.Retrieved, "selection_sha256": pin, "downloaded_at": time.Now().UTC(), "source_sha256": hash(original), "source_bytes": len(original), "derivative_sha256": res.Hash, "derivative_bytes": res.Bytes, "width": res.Width, "height": res.Height, "jpeg_quality": res.Quality, "transform": "Full-frame aspect-preserving downsample and JPEG recompression; no crop, no generated content."})
				var mid string
				if e = tx.QueryRow(ctx, `INSERT INTO media_assets(storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
 VALUES('local',$1,$2,$3,'image/jpeg',$4,$5,$6,$7,$8,'cc0','CC0 1.0','https://creativecommons.org/publicdomain/zero/1.0/',$9,$10,now(),$11,$12) RETURNING id::text`, res.Path, w.URL, provider, res.Width, res.Height, res.Bytes, res.Hash, c.Title+" — "+c.Artist, c.Artist, w.Credit+". "+provider+". CC0; compressed study reproduction.", x.Retrieved, actor).Scan(&mid); e != nil {
					return e
				}
				if _, e = tx.Exec(ctx, `INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES($1,$2,$3,$4,$5,$6,'Exact museum-highlight object with explicit per-image CC0/public-domain flag and no conflicting copyright notice',$7,$8,$9)`, mid, c.SourceID, w.ID, hash(jsonBytes(w.Raw)), w.ImageURL, policy, version, x.Retrieved, evidence); e != nil {
					return e
				}
				if _, e = tx.Exec(ctx, `UPDATE artworks SET primary_media_id=$2,revision=revision+1,updated_at=now(),updated_by=$3 WHERE id=$1 AND primary_media_id IS NULL`, c.ID, mid, actor); e != nil {
					return e
				}
				res.ImageOutcome = "attached"
			} else if media != nil {
				res.ImageOutcome = "existing_media_preserved"
			}
			return tx.Commit(ctx)
		}()
		if e != nil {
			res.Error = e.Error()
			r.Results = append(r.Results, res)
			return e
		}
		r.Results = append(r.Results, res)
		fmt.Printf("%s: %s; new highlight=%t (%d bytes)\n", res.Object, res.ImageOutcome, res.HighlightAdded, res.Bytes)
	}
	return nil
}
