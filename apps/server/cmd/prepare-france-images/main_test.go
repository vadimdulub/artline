package main

import (
	"bytes"
	"image"
	"image/color"
	"image/png"
	"testing"
	"time"
)

func TestFullFrameCompression(t *testing.T) {
	im := image.NewRGBA(image.Rect(0, 0, 1600, 1000))
	for y := 0; y < 1000; y++ {
		for x := 0; x < 1600; x++ {
			im.Set(x, y, color.RGBA{uint8(x % 251), uint8(y % 251), 50, 255})
		}
	}
	var raw bytes.Buffer
	if err := png.Encode(&raw, im); err != nil {
		t.Fatal(err)
	}
	data, w, h, q, err := compress(raw.Bytes())
	if err != nil {
		t.Fatal(err)
	}
	if len(data) > 100000 || w*1000 != h*1600 || q < 58 {
		t.Fatalf("unexpected image %d %d %d %d", len(data), w, h, q)
	}
	if _, _, err = image.Decode(bytes.NewReader(data)); err != nil {
		t.Fatal(err)
	}
}
func TestInvalidImageRejected(t *testing.T) {
	if _, _, _, _, err := compress([]byte("not an image")); err == nil {
		t.Fatal("invalid bytes accepted")
	}
}
func TestBoundedEvidenceAndURL(t *testing.T) {
	e := map[string]any{"artwork_id": "bde58d01-8a1e-5a9b-9ad8-9175ff377b99", "source_image_url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Example.jpg", "identity_basis": "reviewed exact source identifier", "creator_credit": "Example photographer", "source_evidence_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "provider": "france-commons", "rights_status": "public_domain", "policy_url": "https://creativecommons.org/publicdomain/mark/1.0/", "checked_at": time.Now().UTC().Format(time.RFC3339)}
	if err := validate([]map[string]any{e}); err != nil {
		t.Fatal(err)
	}
	if err := validate([]map[string]any{e, e}); err == nil {
		t.Fatal("duplicate accepted")
	}
	e["source_image_url"] = "http://localhost:8080/private"
	if err := validate([]map[string]any{e}); err == nil {
		t.Fatal("unapproved URL accepted")
	}
	e["source_image_url"] = "https://upload.wikimedia.org/wikipedia/commons/a/ab/Example.jpg"
	e["checked_at"] = time.Now().Add(-48 * time.Hour).UTC().Format(time.RFC3339)
	if err := validate([]map[string]any{e}); err == nil {
		t.Fatal("stale evidence accepted")
	}
}
