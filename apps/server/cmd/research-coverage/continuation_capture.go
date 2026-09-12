package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

// Public frontend-backed search, not a promised public API. Bounded to the
// painting fund and 40 pages; no image downloads or per-artwork request loop.
func capturePushkinKamis(ctx context.Context, out string) error {
	const endpoint = "https://collection.pushkinmuseum.art/api/search-entities/OBJECT?raw=true"
	client := &http.Client{Timeout: 30 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	seen := map[string]bool{}
	total := 0
	for page := 0; page < 40; page++ {
		path := filepath.Join(out, fmt.Sprintf("page-%03d.json", page))
		request := map[string]any{"query": nil, "start": page * 50, "count": 50, "filters": map[string][]string{"fund": {"13"}}, "sort": "90", "rawDataFilters": map[string]any{}}
		body, _ := json.Marshal(request)
		var data []byte
		if _, e := os.Stat(path); e == nil {
			if e = verify(path); e != nil {
				return e
			}
			data, e = os.ReadFile(path)
			if e != nil {
				return e
			}
		} else {
			req, e := http.NewRequestWithContext(ctx, "POST", endpoint, bytes.NewReader(body))
			if e != nil {
				return e
			}
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("User-Agent", agent)
			resp, e := client.Do(req)
			if e != nil {
				return e
			}
			data, e = io.ReadAll(io.LimitReader(resp.Body, (8<<20)+1))
			resp.Body.Close()
			if e != nil {
				return e
			}
			if resp.StatusCode != 200 || len(data) > 8<<20 || !json.Valid(data) {
				return fmt.Errorf("Pushkin page%d status%d invalid/oversize response", page, resp.StatusCode)
			}
			var v any
			json.Unmarshal(data, &v)
			if e = save(path, v); e != nil {
				return e
			}
			sha, n, e := hashFile(path)
			if e != nil {
				return e
			}
			if e = save(path+".snapshot.json", map[string]any{"url": endpoint, "request": request, "sha256": sha, "bytes": n, "retrieved_at": time.Now().UTC()}); e != nil {
				return e
			}
		}
		var parsed struct {
			Data  []struct{ ID string }
			Total int `json:"totalCount"`
		}
		if e := json.Unmarshal(data, &parsed); e != nil {
			return e
		}
		if page == 0 {
			total = parsed.Total
		}
		if total < 1 || total > 2000 || parsed.Total != total || len(parsed.Data) != min(50, total-page*50) {
			return fmt.Errorf("changing/unexpected Pushkin pagination")
		}
		for _, r := range parsed.Data {
			if r.ID == "" || seen[r.ID] {
				return fmt.Errorf("duplicate/missing source identity")
			}
			seen[r.ID] = true
		}
		fmt.Printf("Pushkin page%d %d/%d\n", page, len(seen), total)
		if len(seen) == total {
			return save(filepath.Join(out, "manifest.json"), map[string]any{"source": endpoint, "scope": "fund13 paintings, all dates", "pages": page + 1, "objects": total, "complete": true, "rights": "Factual local research only; no open license asserted for KAMIS images or narrative."})
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(300 * time.Millisecond):
		}
	}
	return fmt.Errorf("Pushkin page cap reached")
}
