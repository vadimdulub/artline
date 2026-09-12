package main

import (
	"bytes"
	"context"
	"image"
	"image/color"
	"image/jpeg"
	"io"
	"net/http"
	"strings"
	"testing"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

func TestCompressBoundedFullFrame(t *testing.T) {
	src := image.NewRGBA(image.Rect(0, 0, 1600, 1000))
	var n uint32 = 42
	for y := 0; y < 1000; y++ {
		for x := 0; x < 1600; x++ {
			n = n*1664525 + 1013904223
			src.SetRGBA(x, y, color.RGBA{uint8(n), uint8(n >> 8), uint8(n >> 16), 255})
		}
	}
	var b bytes.Buffer
	if e := jpeg.Encode(&b, src, &jpeg.Options{Quality: 95}); e != nil {
		t.Fatal(e)
	}
	out, w, h, q, e := compress(b.Bytes())
	if e != nil {
		t.Fatal(e)
	}
	if len(out) > 100000 || w > 900 || h > 900 || q < 58 || w*1000 != h*1600 {
		t.Fatalf("invalid derivative: %d bytes %dx%d q%d", len(out), w, h, q)
	}
	if _, e = jpeg.Decode(bytes.NewReader(out)); e != nil {
		t.Fatal(e)
	}
	if _, _, _, _, e = compress([]byte("not a picture")); e == nil {
		t.Fatal("accepted invalid image")
	}
}
func TestNoUpscaleAndWhiteTransparency(t *testing.T) {
	img := resize(image.NewNRGBA(image.Rect(0, 0, 20, 10)), 900)
	if img.Bounds().Dx() != 20 || img.Bounds().Dy() != 10 || img.RGBAAt(0, 0) != (color.RGBA{255, 255, 255, 255}) {
		t.Fatal("resized or mishandled transparent source")
	}
}
func fixture() selection {
	now := time.Now().UTC()
	w := ingest.NormalizeMet(map[string]any{"objectID": float64(123), "title": "Test", "objectURL": "https://www.metmuseum.org/art/collection/search/123", "classification": "Paintings", "isHighlight": true, "isPublicDomain": true, "objectBeginDate": float64(1800), "objectEndDate": float64(1800), "objectDate": "1800", "primaryImageSmall": "https://images.metmuseum.org/test.jpg"})
	w.SourceSnapshotAt = now
	return selection{Version: version, Created: now, Entries: []entry{{Candidate: candidate{ID: "work-1", Scheme: "met-object", Object: "123", SourceID: "source-1", Fingerprint: "fingerprint"}, Work: w, Retrieved: now}}}
}
func TestEvidenceValidation(t *testing.T) {
	if e := validate(fixture()); e != nil {
		t.Fatal(e)
	}
	tests := map[string]func(*selection){
		"stale":             func(s *selection) { s.Entries[0].Retrieved = time.Now().Add(-25 * time.Hour) },
		"future":            func(s *selection) { s.Created = time.Now().Add(time.Hour) },
		"duplicate":         func(s *selection) { s.Entries = append(s.Entries, s.Entries[0]) },
		"spoofed rights":    func(s *selection) { s.Entries[0].Work.Raw["isPublicDomain"] = false },
		"spoofed highlight": func(s *selection) { s.Entries[0].Work.Raw["isHighlight"] = false },
		"spoofed URL":       func(s *selection) { s.Entries[0].Work.ImageURL = "https://example.org/fake.jpg" },
		"different object":  func(s *selection) { s.Entries[0].Candidate.Object = "456" },
		"different source":  func(s *selection) { s.Entries[0].Candidate.Scheme = "cleveland-object" },
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			s := fixture()
			change(&s)
			if validate(s) == nil {
				t.Fatal("accepted unsafe selection")
			}
		})
	}
}

type transport func(*http.Request) (*http.Response, error)

func (f transport) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }
func TestSourceStopsWithoutRetry(t *testing.T) {
	for _, code := range []int{403, 429} {
		f := newFetcher()
		calls := 0
		f.client.Transport = transport(func(r *http.Request) (*http.Response, error) {
			calls++
			return &http.Response{StatusCode: code, Body: io.NopCloser(strings.NewReader("denied")), Header: make(http.Header), Request: r}, nil
		})
		for i := 0; i < 2; i++ {
			if _, e := f.get(context.Background(), "https://images.metmuseum.org/a.jpg", 100); e == nil {
				t.Fatal("accepted blocked source")
			}
		}
		if calls != 1 {
			t.Fatalf("retried blocked source: %d", calls)
		}
	}
}
func TestRejectUnknownDownloadHost(t *testing.T) {
	f := newFetcher()
	if _, e := f.get(context.Background(), "https://evil.example/a.jpg", 100); e == nil {
		t.Fatal("accepted unknown host")
	}
}
