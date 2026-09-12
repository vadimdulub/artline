package ingest

import (
	"bytes"
	"context"
	"image"
	"image/color"
	"image/jpeg"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func fixture() Work {
	return NormalizeMet(map[string]any{"objectID": float64(123), "title": "Fixture painting", "objectURL": "https://www.metmuseum.org/art/collection/search/123", "objectDate": "1970", "objectBeginDate": float64(1970), "objectEndDate": float64(1970), "classification": "Paintings", "isHighlight": true, "isPublicDomain": true, "primaryImageSmall": "https://images.metmuseum.org/fixture.jpg", "artistDisplayName": "Fixture Painter", "artistBeginDate": "1800"})
}
func TestImportGates(t *testing.T) {
	w := fixture()
	if w.Eligible() != "eligible" || !w.ImageAllowed() {
		t.Fatal("valid fixture rejected")
	}
	w.Highlight = false
	if w.Eligible() == "eligible" || w.ImageAllowed() {
		t.Fatal("ordinary holding accepted as masterpiece")
	}
	w = fixture()
	w.Rights = "unknown"
	if w.ImageAllowed() {
		t.Fatal("unknown rights allowed")
	}
	w = fixture()
	w.Copyright = "© Estate"
	if w.ImageAllowed() {
		t.Fatal("conflicting rights allowed")
	}
	w = fixture()
	w.Type = ""
	if w.Eligible() == "eligible" {
		t.Fatal("sculpture accepted")
	}
	w = fixture()
	w.ImageURL = "https://evil.example/image.jpg"
	if w.ImageAllowed() {
		t.Fatal("unapproved image host")
	}
	if got := workType("Photograph"); got != "" {
		t.Fatal("photograph included")
	}
	for _, raw := range []string{"http://images.metmuseum.org/a.jpg", "https://images.metmuseum.org.evil.example/a", "https://127.0.0.1/a", "https://user:pass@images.metmuseum.org/a", "https://storage.googleapis.com/unapproved/a", "https://images.metmuseum.org:8080/a"} {
		if safeURL(raw) == nil {
			t.Errorf("accepted %s", raw)
		}
	}
}
func TestMatchingDoesNotGuess(t *testing.T) {
	for _, name := range []string{"Zdzisław Beksiński", "Vilhelm Hammershøi", "張大千"} {
		for _, r := range slug(name) {
			if !(r >= 'a' && r <= 'z' || r >= '0' && r <= '9' || r == '-') {
				t.Fatalf("unsafe route slug %q", slug(name))
			}
		}
	}
	p := []Painter{{Name: "Édouard Manet", QID: "Q40599", Birth: 1832}, {Name: "Claude Monet", QID: "Q296", Birth: 1840}}
	w := fixture()
	w.ArtistName = "Edouard Manet"
	b := 1832
	w.ArtistBirth = &b
	if got := MatchPainter(w, p); got == nil || got.QID != "Q40599" {
		t.Fatal("accent normalization failed")
	}
	w.ArtistBirth = nil
	if MatchPainter(w, p) != nil {
		t.Fatal("matched name without date")
	}
	w.ArtistQID = "Q296"
	if got := MatchPainter(w, p); got == nil || got.Name != "Claude Monet" {
		t.Fatal("authority not used")
	}
	w.ArtistQID = "Q999999999"
	w.ArtistBirth = &b
	if MatchPainter(w, p) != nil {
		t.Fatal("authority conflict fell back to name")
	}
	w.ArtistQID = ""
	p = append(p, p[0])
	if MatchPainter(w, p) != nil {
		t.Fatal("ambiguous name accepted")
	}
}

type transportFunc func(*http.Request) (*http.Response, error)

func (f transportFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }
func TestImageDownloadRightsCacheAndIntegrity(t *testing.T) {
	var b bytes.Buffer
	im := image.NewRGBA(image.Rect(0, 0, 20, 10))
	im.Set(0, 0, color.White)
	if err := jpeg.Encode(&b, im, nil); err != nil {
		t.Fatal(err)
	}
	root := t.TempDir()
	c := NewClient(filepath.Join(root, "cache"))
	calls := 0
	c.HTTP.Transport = transportFunc(func(r *http.Request) (*http.Response, error) {
		calls++
		return &http.Response{StatusCode: 200, Body: io.NopCloser(bytes.NewReader(b.Bytes())), Header: http.Header{}}, nil
	})
	w := fixture()
	ctx := context.Background()
	w.SourceSnapshotAt = time.Now().UTC()
	f, err := c.DownloadImage(ctx, w, filepath.Join(root, "assets"))
	if err != nil {
		t.Fatal(err)
	}
	if f.Width != 20 || f.Height != 10 || f.Hash != checksum(b.Bytes()) {
		t.Fatalf("bad image %+v", f)
	}
	if _, err = c.DownloadImage(ctx, w, filepath.Join(root, "assets")); err != nil || calls != 1 {
		t.Fatalf("cache/idempotence failed: %v calls %d", err, calls)
	}
	w.Rights = "restricted"
	if _, err = c.DownloadImage(ctx, w, filepath.Join(root, "assets")); err == nil || calls != 1 {
		t.Fatal("restricted image reached network")
	}
	w.Rights = "cc0"
	w.SourceSnapshotAt = time.Now().Add(-25 * time.Hour)
	if _, err = c.DownloadImage(ctx, w, filepath.Join(root, "assets")); err == nil || calls != 1 {
		t.Fatal("stale source rights reached network")
	}
	path := filepath.Join(root, "unchanged")
	if err = writeNew(path, []byte("original")); err != nil {
		t.Fatal(err)
	}
	if err = writeNew(path, []byte("different")); err == nil {
		t.Fatal("overwrite permitted")
	}
	got, _ := os.ReadFile(path)
	if string(got) != "original" {
		t.Fatal("existing file changed")
	}
}

func TestClevelandPreservesSourceSemantics(t *testing.T) {
	w := NormalizeCleveland(map[string]any{"id": float64(1), "title": "Painting", "url": "https://www.clevelandart.org/art/1", "type": "Painting", "creation_date": "c. 1960–1980", "creation_date_earliest": float64(1960), "creation_date_latest": float64(1980), "is_highlight": true, "share_license_status": "CC0"})
	if w.Precision != "circa_range" || w.Eligible() != "creation_review" {
		t.Fatalf("crossing cutoff accepted: %+v", w)
	}
}
