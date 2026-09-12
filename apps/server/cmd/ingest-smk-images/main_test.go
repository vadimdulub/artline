package main

import (
	"bytes"
	"image"
	"image/color"
	"image/jpeg"
	"testing"
	"time"
)

func TestCompressionCeilingAndFullFrame(t *testing.T) {
	img := image.NewRGBA(image.Rect(0, 0, 700, 460))
	for y := 0; y < 460; y++ {
		for x := 0; x < 700; x++ {
			img.Set(x, y, color.RGBA{uint8(x*23 + y*11), uint8(x*5 + y*17), uint8(x + y), 255})
		}
	}
	var source bytes.Buffer
	if e := jpeg.Encode(&source, img, &jpeg.Options{Quality: 95}); e != nil {
		t.Fatal(e)
	}
	b, w, h, q, e := compress(source.Bytes())
	if e != nil {
		t.Fatal(e)
	}
	if len(b) > 100000 || w != 700 || h != 460 || q < 38 {
		t.Fatal(len(b), w, h, q)
	}
	got, e := jpeg.Decode(bytes.NewReader(b))
	if e != nil || got.Bounds() != img.Bounds() {
		t.Fatal("full frame lost", e)
	}
	if _, _, _, _, e = compress([]byte("not an image")); e == nil {
		t.Fatal("invalid bytes accepted")
	}
	var huge bytes.Buffer
	jpeg.Encode(&huge, image.NewRGBA(image.Rect(0, 0, 701, 100)), nil)
	if _, _, _, _, e = compress(huge.Bytes()); e == nil {
		t.Fatal("unexpected oversized rendition accepted")
	}
}

func TestSelectedImageGate(t *testing.T) {
	base := "https://iip.smk.dk/iiif/jp2/test_kms1.tif.jp2"
	raw := map[string]any{"object_number": "KMS1", "frontend_url": "https://open.smk.dk/artwork/image/KMS1", "image_iiif_id": base, "rights": pdm, "public_domain": true, "has_image": true}
	m := selection{Source: "smk", MetadataSHA: metadataSHA, Retrieved: time.Now(), Images: []selected{{Object: "KMS1", Page: raw["frontend_url"].(string), URL: base + "/full/!700,700/0/default.jpg", Raw: raw}}}
	if e := validate(m); e != nil {
		t.Fatal(e)
	}
	raw["public_domain"] = false
	if validate(m) == nil {
		t.Fatal("rights false accepted")
	}
	raw["public_domain"] = true
	m.Images[0].URL = "https://elsewhere.example/image.jpg"
	if validate(m) == nil {
		t.Fatal("untrusted image host accepted")
	}
	m.Images[0].URL = base + "/full/!700,700/0/default.jpg"
	m.Retrieved = time.Now().Add(-25 * time.Hour)
	if validate(m) == nil {
		t.Fatal("stale rights accepted")
	}
}
