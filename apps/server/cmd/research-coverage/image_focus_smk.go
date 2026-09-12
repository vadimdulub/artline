package main

import (
	"context"
	"path/filepath"
	"time"
)

// A reviewed missing-image subset, not an exhaustive image crawl.
var imageFocusSMKObjects = []string{"KMS359", "KMS844", "KMS1345", "KMS1662", "KMS1222", "KMS4002", "KMS3820", "KMS1691", "KMS3696", "KMS3697", "KMS1542", "KMS8010"}

func captureImageFocusSMK(ctx context.Context, out string) error {
	for n, id := range imageFocusSMKObjects {
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
	return save(filepath.Join(out, "capture.json"), map[string]any{"objects": imageFocusSMKObjects, "scope": "12 existing museum paintings; exact-object image and rights checks, no image download or DB writes"})
}
