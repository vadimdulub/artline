package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

// One bounded recovery after the normal Chicago download timed out. Each range
// is independently checkpointed, and the same strong ETag is required throughout.
// No archive members are extracted; source data remains offline metadata only.
func captureChicagoRanges(ctx context.Context, out string) error {
	const total int64 = 119891546
	const width int64 = 1 << 20
	const etag = "\"2a4a6375ca842dc45f171d91fec44f1e-23\""
	const modified = "Sun, 16 Feb 2025 08:32:05 GMT"
	final := filepath.Join(out, "metadata.tar.bz2")
	if _, e := os.Stat(final); e == nil {
		return verify(final)
	}
	client := &http.Client{Timeout: 45 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	parts := []string{}
	for start := int64(0); start < total; start += width {
		end := min(start+width, total) - 1
		file := filepath.Join(out, fmt.Sprintf("range-%03d.bin", start/width))
		parts = append(parts, file)
		if _, e := os.Stat(file); e == nil {
			if e = verify(file); e != nil {
				return e
			}
			b, e := os.ReadFile(file + ".snapshot.json")
			if e != nil {
				return e
			}
			var s struct {
				URL, ETag, Range string
				Bytes            int64
			}
			if json.Unmarshal(b, &s) != nil || s.URL != chicagoExport || s.ETag != etag || s.Range != fmt.Sprintf("bytes=%d-%d", start, end) || s.Bytes != end-start+1 {
				return fmt.Errorf("cached range identity mismatch")
			}
			continue
		}
		req, e := http.NewRequestWithContext(ctx, "GET", chicagoExport, nil)
		if e != nil {
			return e
		}
		req.Header.Set("User-Agent", agent)
		req.Header.Set("Range", fmt.Sprintf("bytes=%d-%d", start, end))
		req.Header.Set("If-Match", etag)
		req.Header.Set("Accept-Encoding", "identity")
		resp, e := client.Do(req)
		if e != nil {
			return e
		}
		b, e := io.ReadAll(io.LimitReader(resp.Body, width+1))
		resp.Body.Close()
		if e != nil {
			return e
		}
		if resp.StatusCode != 206 || resp.Header.Get("Content-Range") != fmt.Sprintf("bytes %d-%d/%d", start, end, total) || resp.Header.Get("ETag") != etag || resp.Header.Get("Last-Modified") != modified || int64(len(b)) != end-start+1 {
			return fmt.Errorf("Chicago changed/invalid range status%d", resp.StatusCode)
		}
		f, e := os.OpenFile(file, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
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
		sha, n, e := hashFile(file)
		if e != nil {
			return e
		}
		if e = save(file+".snapshot.json", map[string]any{"url": chicagoExport, "sha256": sha, "bytes": n, "retrieved_at": time.Now().UTC(), "etag": etag, "range": req.Header.Get("Range"), "last_modified": modified}); e != nil {
			return e
		}
		if start/width%10 == 0 {
			fmt.Printf("Chicago %d/%d bytes checkpointed\n", end+1, total)
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(time.Second):
		}
	}
	f, e := os.CreateTemp(out, ".archive-*")
	if e != nil {
		return e
	}
	temp := f.Name()
	defer os.Remove(temp)
	for _, p := range parts {
		part, e := os.Open(p)
		if e != nil {
			f.Close()
			return e
		}
		_, e = io.Copy(f, part)
		part.Close()
		if e != nil {
			f.Close()
			return e
		}
	}
	if e = f.Close(); e != nil {
		return e
	}
	sha, n, e := hashFile(temp)
	if e != nil {
		return e
	}
	if n != total {
		return fmt.Errorf("archive length mismatch")
	}
	if e = os.Link(temp, final); e != nil {
		return e
	}
	if e = save(final+".snapshot.json", map[string]any{"url": chicagoExport, "sha256": sha, "bytes": n, "retrieved_at": time.Now().UTC(), "etag": etag, "last_modified": modified, "range_count": len(parts)}); e != nil {
		return e
	}
	fmt.Printf("Chicago complete archive %d bytes\n", n)
	return nil
}
