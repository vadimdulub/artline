package ingest

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"image"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

const NGAImagesPath = "docs/research/russia-italy-scale/selected-images-v1/images.json"
const NGAImagesSHA = "98824943ecf566471e165c087da80b046b735eb7a6fd778a2de287afb51a6a95"

type ngaSelectedImage struct {
	ArtworkID     string `json:"artwork_id"`
	ObjectID      string `json:"object_id"`
	UUID          string `json:"image_uuid"`
	URL           string `json:"url"`
	OpenAccess    string `json:"openaccess"`
	Title, Artist string
	Alt           string `json:"alt_text"`
	Raw           map[string]string
}
type NGAImageResult struct {
	ObjectID             string `json:"object_id"`
	Outcome, Path, Error string
}
type NGAImagesReport struct {
	Applied                         bool
	Snapshot                        string
	Selected, Added, Reused, Failed int
	Results                         []NGAImageResult
}

var ngaImageURL = regexp.MustCompile(`^https://api\.nga\.gov/iiif/[a-f0-9-]{36}/full/!600,600/0/default\.jpg$`)

// Only a checksum-pinned, explicitly selected openaccess=1 museum image set is
// accepted. Metadata CC0 is not used as a blanket image licence.
func ImportNGAImages(ctx context.Context, pool *pgxpool.Pool, data []byte, assets string, apply bool) (NGAImagesReport, error) {
	out := NGAImagesReport{Applied: apply, Snapshot: checksum(data), Results: []NGAImageResult{}}
	if out.Snapshot != NGAImagesSHA {
		return out, errors.New("unreviewed image selection")
	}
	var m struct {
		Source    string
		Retrieved time.Time `json:"retrieved_at"`
		Images    []ngaSelectedImage
	}
	if e := json.Unmarshal(data, &m); e != nil {
		return out, e
	}
	if m.Source != "nga" || len(m.Images) > 20 || time.Since(m.Retrieved) > 24*time.Hour || time.Until(m.Retrieved) > 5*time.Minute {
		return out, errors.New("stale/invalid image rights evidence")
	}
	for _, x := range m.Images {
		if !bulkID.MatchString(x.ObjectID) || x.OpenAccess != "1" || x.Raw["openaccess"] != "1" || x.Raw["viewtype"] != "primary" || x.Raw["uuid"] != x.UUID || x.Raw["depictstmsobjectid"] != x.ObjectID || x.URL != x.Raw["iiifurl"]+"/full/!600,600/0/default.jpg" || !ngaImageURL.MatchString(x.URL) {
			return out, errors.New("invalid image identity/rights")
		}
	}
	out.Selected = len(m.Images)
	var sid string
	if e := pool.QueryRow(ctx, `SELECT id::text FROM sources WHERE slug='nga-open-data' AND is_active`).Scan(&sid); e != nil {
		return out, e
	}
	for _, x := range m.Images {
		var id, status string
		var existing *string
		e := pool.QueryRow(ctx, `SELECT a.id::text,a.status,a.primary_media_id::text FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme='european-nga-object' AND e.external_id=$1`, x.ObjectID).Scan(&id, &status, &existing)
		if e != nil || id != x.ArtworkID || status != "review" {
			return out, fmt.Errorf("image artwork identity/state changed: %s", x.ObjectID)
		}
		if existing != nil {
			out.Reused++
			out.Results = append(out.Results, NGAImageResult{ObjectID: x.ObjectID, Outcome: "existing_media_preserved"})
			continue
		}
		if !apply {
			out.Results = append(out.Results, NGAImageResult{ObjectID: x.ObjectID, Outcome: "eligible_preview_no_download"})
			continue
		}
		// Recoverable content-addressed local file, before a short DB-only transaction.
		img, e := downloadNGARanges(ctx, x, assets)
		if e != nil {
			out.Failed++
			out.Results = append(out.Results, NGAImageResult{ObjectID: x.ObjectID, Outcome: "download_failed", Error: e.Error()})
			if out.Failed >= 3 {
				break
			}
			continue
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
				out.Reused++
				return
			}
			var mediaID string
			alt := x.Alt
			if alt == "" {
				alt = x.Title + " — " + x.Artist
			}
			page := "https://www.nga.gov/collection/art-object-page." + x.ObjectID + ".html"
			policy := "https://www.nga.gov/artworks/free-images-and-open-access"
			e = tx.QueryRow(ctx, `INSERT INTO media_assets(storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
 VALUES('local',$1,$2,'National Gallery of Art',$3,$4,$5,$6,$7,$8,'licensed','NGA Open Access — unrestricted reuse',$9,$10,$11,$12,$12,$13) ON CONFLICT(storage_path) DO UPDATE SET storage_path=EXCLUDED.storage_path RETURNING id::text`, img.Path, page, img.MIME, img.Width, img.Height, img.Bytes, img.Hash, alt, policy, x.Artist, x.Artist+". "+x.Title+". National Gallery of Art, Washington. Open Access.", m.Retrieved, europeanActor).Scan(&mediaID)
			if e != nil {
				return
			}
			_, e = tx.Exec(ctx, `INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES($1,$2,$3,$4,$5,$6,'NGA published_images exact object/UUID, primary view, openaccess=1; individual image gate, not metadata licence','nga-selected-images-v1',$7,$8) ON CONFLICT(media_id) DO NOTHING`, mediaID, sid, x.ObjectID, checksum(rawJSON(x.Raw)), x.URL, policy, m.Retrieved, rawJSON(x.Raw))
			if e != nil {
				return
			}
			_, e = tx.Exec(ctx, `UPDATE artworks SET primary_media_id=$2,revision=revision+1,updated_at=now(),updated_by=$3 WHERE id=$1 AND primary_media_id IS NULL`, id, mediaID, europeanActor)
			if e != nil {
				return
			}
			e = tx.Commit(ctx)
			if e == nil {
				out.Added++
				out.Results = append(out.Results, NGAImageResult{ObjectID: x.ObjectID, Outcome: "attached", Path: img.Path})
			}
		}()
		if e != nil {
			return out, e
		}
	}
	return out, nil
}

func downloadNGARanges(ctx context.Context, x ngaSelectedImage, assets string) (ImageFile, error) {
	if !ngaImageURL.MatchString(x.URL) {
		return ImageFile{}, errors.New("unapproved image URL")
	}
	cache := filepath.Join(assets, "nga-selected-"+x.ObjectID+"-"+x.UUID+".jpg")
	var b []byte
	if old, e := os.ReadFile(cache); e == nil {
		var evidence struct{ URL, SHA string }
		raw, err := os.ReadFile(cache + ".source.json")
		if err != nil || json.Unmarshal(raw, &evidence) != nil || evidence.URL != x.URL || evidence.SHA != checksum(old) {
			return ImageFile{}, errors.New("unverified cached image; original file preserved")
		}
		b = old
	} else if !errors.Is(e, os.ErrNotExist) {
		return ImageFile{}, e
	} else {
		client := &http.Client{Timeout: 25 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
		var output bytes.Buffer
		var total int64
		etag := ""
		for start := int64(0); ; start += 8192 {
			if start >= 2<<20 {
				return ImageFile{}, errors.New("selected image exceeds2MiB")
			}
			end := start + 8191
			if total > 0 && end >= total {
				end = total - 1
			}
			req, e := http.NewRequestWithContext(ctx, "GET", x.URL, nil)
			if e != nil {
				return ImageFile{}, e
			}
			req.Header.Set("User-Agent", "Artline/1.0 (selected NGA open-access images)")
			req.Header.Set("Range", fmt.Sprintf("bytes=%d-%d", start, end))
			req.Header.Set("Accept-Encoding", "identity")
			if etag != "" {
				req.Header.Set("If-Match", etag)
			}
			res, e := client.Do(req)
			if e != nil {
				return ImageFile{}, e
			}
			// IIIF may legitimately ignore Range. Accept a bounded full response
			// only for the initial request; never concatenate HTTP 200 responses.
			part, e := readNGAImageResponse(res, start)
			res.Body.Close()
			if e != nil {
				return ImageFile{}, e
			}
			if res.StatusCode == http.StatusOK && start == 0 {
				if len(part) > 2<<20 {
					return ImageFile{}, errors.New("selected image exceeds 2 MiB")
				}
				output.Write(part)
				break
			}
			var a, z, n int64
			_, e = fmt.Sscanf(res.Header.Get("Content-Range"), "bytes %d-%d/%d", &a, &z, &n)
			if res.StatusCode != 206 || e != nil || a != start || z != min(end, n-1) || int64(len(part)) != z-a+1 || n > 2<<20 {
				return ImageFile{}, fmt.Errorf("image range unavailable: HTTP%d", res.StatusCode)
			}
			if total == 0 {
				total = n
				etag = res.Header.Get("ETag")
				if etag == "" {
					return ImageFile{}, errors.New("missing image ETag")
				}
			} else if n != total || etag != res.Header.Get("ETag") {
				return ImageFile{}, errors.New("image changed during download")
			}
			output.Write(part)
			if z == total-1 {
				break
			}
			if e = sleep(ctx, 150*time.Millisecond); e != nil {
				return ImageFile{}, e
			}
		}
		b = output.Bytes()
	}
	cfg, format, e := image.DecodeConfig(bytes.NewReader(b))
	if e != nil || format != "jpeg" || cfg.Width < 1 || cfg.Height < 1 || cfg.Width > 600 || cfg.Height > 600 {
		return ImageFile{}, errors.New("invalid selected600pxJPEG")
	}
	if e = writeNew(cache, b); e != nil {
		return ImageFile{}, e
	}
	if e = writeNew(cache+".source.json", rawJSON(map[string]string{"URL": x.URL, "SHA": checksum(b)})); e != nil {
		return ImageFile{}, e
	}
	return ImageFile{Path: "/assets/artworks/imported/" + filepath.Base(cache), Hash: checksum(b), MIME: "image/jpeg", Width: cfg.Width, Height: cfg.Height, Bytes: int64(len(b))}, nil
}

func readNGAImageResponse(res *http.Response, start int64) ([]byte, error) {
	limit := int64(8192)
	if res.StatusCode == http.StatusOK {
		if start != 0 {
			return nil, errors.New("full image response after initial range")
		}
		limit = 2 << 20
	}
	part, err := io.ReadAll(io.LimitReader(res.Body, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(part)) > limit {
		return nil, errors.New("image response exceeds byte budget")
	}
	return part, nil
}
