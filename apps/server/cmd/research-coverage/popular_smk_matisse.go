package main

import (
	"context"
	"path/filepath"
	"time"
)

// Individually reviewed gaps, not a new collection-wide crawl. Existing 41-object
// SMK research is retained and sources with unavailable images are not retried.
var smkMatisseObjects = []string{"KMSr171", "KMSr73", "KMSr75"}

func captureSMKMatisse(ctx context.Context, out string) error {
	for n, id := range smkMatisseObjects {
		if n > 0 {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(2 * time.Second):
			}
		}
		if err := fetch(ctx, filepath.Join(out, "smk-"+id+".json"), "https://api.smk.dk/api/v1/art/?object_number="+id+"&lang=en", 1<<20); err != nil {
			return err
		}
	}
	return save(filepath.Join(out, "capture.json"), map[string]any{"source": "SMK official exact-object API", "objects": smkMatisseObjects, "policy": "https://www.smk.dk/en/article/smk-api/", "scope": "Selected factual catalogue and per-object rights checks; no image binaries, generated enrichment or database writes"})
}
