package main

// Bounded byte-range recovery for small static metadata feeds. Some local
// connections stall after the first16KiB of a response. This does not bypass
// authentication/access controls and is never used to crawl large archives.
import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

func fetchSmallRanges(ctx context.Context, path, rawURL string, prefix int64) error {
	if rawURL != "https://pushkinmuseum.art/json/masterpieces.json" && rawURL != "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/"+ngaRevision+"/data/published_images.csv" {
		return fmt.Errorf("unapproved ranged source")
	}
	if _, e := os.Stat(path); e == nil {
		return verify(path)
	}
	client := &http.Client{Timeout: 25 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	var output bytes.Buffer
	var total int64
	etag := ""
	lastModified := ""
	for start := int64(0); ; start += 8192 {
		if start >= 2<<20 {
			return fmt.Errorf("2MiB selected metadata budget exceeded")
		}
		end := start + 8191
		if total > 0 && end >= total {
			end = total - 1
		}
		if prefix > 0 && end >= prefix {
			end = prefix - 1
		}
		req, e := http.NewRequestWithContext(ctx, "GET", rawURL, nil)
		if e != nil {
			return e
		}
		req.Header.Set("User-Agent", agent)
		req.Header.Set("Range", fmt.Sprintf("bytes=%d-%d", start, end))
		req.Header.Set("Accept-Encoding", "identity")
		if etag != "" {
			req.Header.Set("If-Match", etag)
		}
		res, e := client.Do(req)
		if e != nil {
			return e
		}
		b, e := io.ReadAll(io.LimitReader(res.Body, 8193))
		res.Body.Close()
		if e != nil {
			return e
		}
		var a, z, n int64
		_, scanErr := fmt.Sscanf(res.Header.Get("Content-Range"), "bytes %d-%d/%d", &a, &z, &n)
		if res.StatusCode != 206 || scanErr != nil || a != start || z != end || int64(len(b)) != end-start+1 {
			return fmt.Errorf("invalid/unsupported byte range status=%d range=%s", res.StatusCode, res.Header.Get("Content-Range"))
		}
		if total == 0 {
			total = n
			etag = res.Header.Get("ETag")
			lastModified = res.Header.Get("Last-Modified")
			if etag == "" {
				return fmt.Errorf("stable ETag required")
			}
		} else if n != total || etag != res.Header.Get("ETag") || lastModified != res.Header.Get("Last-Modified") {
			return fmt.Errorf("source changed during ranges")
		}
		output.Write(b)
		if z == total-1 || prefix > 0 && z == prefix-1 {
			break
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(150 * time.Millisecond):
		}
	}
	b := output.Bytes()
	if prefix == 0 && !json.Valid(b) {
		return fmt.Errorf("incomplete/invalid complete JSON feed")
	}
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	_, e = f.Write(b)
	ce := f.Close()
	if e != nil {
		return e
	}
	if ce != nil {
		return ce
	}
	h := sha256.Sum256(b)
	return save(path+".snapshot.json", map[string]any{"url": rawURL, "sha256": hex.EncodeToString(h[:]), "bytes": len(b), "retrieved_at": time.Now().UTC(), "source_total_bytes": total, "prefix_only": prefix > 0, "range_size": 8192, "etag": etag, "last_modified": lastModified, "filename": filepath.Base(path)})
}
