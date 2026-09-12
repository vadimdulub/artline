// Package ingest implements an explicitly invoked, local-only, curated import.
// Browser/public requests never call these providers.
package ingest

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"image"
	_ "image/jpeg"
	_ "image/png"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

const Version = "curated-1970-v1"
const maxImageBytes = 20 << 20

var allowedHosts = map[string]bool{
	"www.uffizi.it":         true,
	"www.wikidata.org":      true,
	"commons.wikimedia.org": true, "upload.wikimedia.org": true, "thumb.wikimedia.org": true,
	"storage.googleapis.com": true, "collectionapi.metmuseum.org": true,
	"images.metmuseum.org": true, "openaccess-api.clevelandart.org": true,
	"openaccess-cdn.clevelandart.org": true, "api.artic.edu": true, "www.artic.edu": true,
}

type Client struct {
	Cache      string
	HTTP       *http.Client
	last       map[string]time.Time
	mediaBytes int64
}

func NewClient(cache string) *Client {
	return &Client{Cache: cache, last: map[string]time.Time{}, HTTP: &http.Client{
		Timeout: 45 * time.Second,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if len(via) > 3 {
				return fmt.Errorf("too many redirects")
			}
			return safeURL(req.URL.String())
		},
	}}
}

func safeURL(raw string) error {
	u, err := url.Parse(raw)
	if err != nil || u.Scheme != "https" || u.User != nil || (u.Port() != "" && u.Port() != "443") || !allowedHosts[u.Hostname()] {
		return fmt.Errorf("URL outside import allowlist")
	}
	if u.Hostname() == "storage.googleapis.com" && !strings.HasPrefix(u.Path, "/pantheon-public-data/") {
		return fmt.Errorf("unapproved data bucket")
	}
	return nil
}

func checksum(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func (c *Client) snapshotTime(raw string) time.Time {
	info, err := os.Stat(filepath.Join(c.Cache, checksum([]byte(raw))+".payload"))
	if err != nil {
		return time.Time{}
	}
	return info.ModTime().UTC()
}
func sleep(ctx context.Context, d time.Duration) error {
	if d <= 0 {
		return ctx.Err()
	}
	t := time.NewTimer(d)
	defer t.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-t.C:
		return nil
	}
}

// Cached payloads are replayable. New runs use a new cache directory to refresh;
// resuming the same run uses the original snapshot, not a moving source result.
func (c *Client) Get(ctx context.Context, raw string, limit int64) ([]byte, error) {
	if err := safeURL(raw); err != nil {
		return nil, err
	}
	path := filepath.Join(c.Cache, checksum([]byte(raw))+".payload")
	if b, err := os.ReadFile(path); err == nil {
		if int64(len(b)) > limit {
			return nil, fmt.Errorf("cached payload too large")
		}
		return b, nil
	}
	u, _ := url.Parse(raw)
	var lastErr error
	for attempt := 0; attempt < 4; attempt++ {
		interval := 250 * time.Millisecond
		if u.Hostname() == "collectionapi.metmuseum.org" {
			interval = time.Second
		}
		if err := sleep(ctx, interval-time.Since(c.last[u.Hostname()])); err != nil {
			return nil, err
		}
		c.last[u.Hostname()] = time.Now()
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, raw, nil)
		if err != nil {
			return nil, err
		}
		req.Header.Set("User-Agent", "ArtlineCuratedResearch/1.0 (local owner-requested museum highlights)")
		res, err := c.HTTP.Do(req)
		if err != nil {
			lastErr = fmt.Errorf("%s request failed: %w", u.Hostname(), err)
		} else {
			b, readErr := io.ReadAll(io.LimitReader(res.Body, limit+1))
			res.Body.Close()
			if res.StatusCode == http.StatusOK && readErr == nil {
				if int64(len(b)) > limit {
					return nil, fmt.Errorf("%s payload exceeds %d bytes", u.Hostname(), limit)
				}
				if err = writeNew(path, b); err != nil {
					return nil, err
				}
				return b, nil
			}
			lastErr = fmt.Errorf("%s HTTP %d", u.Hostname(), res.StatusCode)
			if res.StatusCode != 429 && res.StatusCode < 500 {
				return nil, lastErr
			}
			delay := time.Duration(1<<attempt) * time.Second
			if n, e := strconv.Atoi(res.Header.Get("Retry-After")); e == nil && n > 0 {
				delay = time.Duration(n) * time.Second
			}
			if when, e := http.ParseTime(res.Header.Get("Retry-After")); e == nil && time.Until(when) > delay {
				delay = time.Until(when)
			}
			// Long provider pauses end this run; resume later, don't ignore Retry-After.
			if delay > time.Minute {
				return nil, fmt.Errorf("%s requested pause; resume later", u.Hostname())
			}
			if err = sleep(ctx, delay); err != nil {
				return nil, err
			}
			continue
		}
		if err := sleep(ctx, time.Duration(1<<attempt)*time.Second); err != nil {
			return nil, err
		}
	}
	return nil, lastErr
}

func (c *Client) JSON(ctx context.Context, raw string, out any) ([]byte, error) {
	b, err := c.Get(ctx, raw, 32<<20)
	if err != nil {
		return nil, err
	}
	if err = json.Unmarshal(b, out); err != nil {
		return nil, fmt.Errorf("invalid provider JSON: %w", err)
	}
	return b, nil
}

// Never overwrite an existing asset or snapshot with different bytes.
func writeNew(path string, b []byte) error {
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return err
	}
	if old, err := os.ReadFile(path); err == nil {
		if !bytes.Equal(old, b) {
			return fmt.Errorf("refuse to overwrite different content: %s", path)
		}
		return nil
	}
	f, err := os.CreateTemp(filepath.Dir(path), ".artline-import-")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if _, err = f.Write(b); err != nil {
		f.Close()
		return err
	}
	if err = f.Close(); err != nil {
		return err
	}
	// Hard-link creation is atomic and refuses to overwrite an existing target.
	return os.Link(name, path)
}

type ImageFile struct {
	Path, Hash, MIME string
	Width, Height    int
	Bytes            int64
}

func (c *Client) DownloadImage(ctx context.Context, w Work, assets string) (ImageFile, error) {
	if !w.ImageAllowed() {
		return ImageFile{}, fmt.Errorf("image rights gate denied")
	}
	if w.SourceSnapshotAt.IsZero() || time.Since(w.SourceSnapshotAt) > 24*time.Hour || time.Until(w.SourceSnapshotAt) > 5*time.Minute {
		return ImageFile{}, fmt.Errorf("source-rights snapshot is stale; create a fresh reviewed import run before downloading")
	}
	if c.mediaBytes+maxImageBytes > 512<<20 {
		return ImageFile{}, fmt.Errorf("512 MiB media budget reached; no more image downloads in this execution")
	}
	b, err := c.Get(ctx, w.ImageURL, maxImageBytes)
	if err != nil {
		return ImageFile{}, err
	}
	c.mediaBytes += int64(len(b))
	config, format, err := image.DecodeConfig(bytes.NewReader(b))
	if err != nil || (format != "jpeg" && format != "png") || config.Width < 1 || config.Height < 1 || int64(config.Width)*int64(config.Height) > 100_000_000 {
		return ImageFile{}, fmt.Errorf("invalid/oversized image")
	}
	hash := checksum(b)
	ext := "jpg"
	if format == "png" {
		ext = "png"
	}
	name := w.Source + "-" + w.ID + "-" + hash[:16] + "." + ext
	if err = writeNew(filepath.Join(assets, name), b); err != nil {
		return ImageFile{}, err
	}
	return ImageFile{"/assets/artworks/imported/" + name, hash, "image/" + format, config.Width, config.Height, int64(len(b))}, nil
}
