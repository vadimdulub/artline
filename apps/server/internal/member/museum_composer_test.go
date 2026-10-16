package member

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"hash/crc32"
	"image"
	"image/color"
	"image/jpeg"
	"image/png"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

const composerCatalogueID = "11111111-1111-4111-8111-111111111111"

type composerCatalogue struct {
	calls int
	ids   []string
}

func (c *composerCatalogue) Search(context.Context, string, string, string, string, bool) (MuseumArtworkPage, error) {
	return MuseumArtworkPage{}, nil
}
func (c *composerCatalogue) Lookup(_ context.Context, ids []string) ([]MuseumArtworkChoice, error) {
	c.calls++
	c.ids = ids
	out := []MuseumArtworkChoice{}
	for _, id := range ids {
		if id == composerCatalogueID {
			out = append(out, MuseumArtworkChoice{MuseumArtworkRef: MuseumArtworkRef{Kind: "catalogue", ID: id}, Title: "Historical collection work", Available: true, Published: true, Href: "/artworks/" + id})
		}
	}
	return out, nil
}
func composerFixture() (*LocalMuseumStudio, *http.ServeMux, *http.ServeMux, *composerCatalogue) {
	h, s, _ := studioFixture()
	cat := &composerCatalogue{}
	blobs := NewMemoryMuseumBlobs()
	private, public := http.NewServeMux(), http.NewServeMux()
	opt := MuseumStudioOptions{Catalogue: cat, Blobs: blobs}
	h.RegisterMuseumStudio(private, s, opt)
	New(Config{Origin: "http://localhost:3000"}, nil).RegisterMuseumStudio(public, s, opt)
	studioCall(private, "POST", "/api/v1/member/museum-studio/museum-a/claim", nil)
	return s, private, public, cat
}
func composerWrite(t *testing.T, mux http.Handler, slug, id string, in PublicationWrite, status int) MuseumPublication {
	t.Helper()
	path, method := "/api/v1/member/museum-studio/"+slug+"/content", "POST"
	if id != "" {
		path += "/" + id
		method = "PUT"
	}
	w := studioCall(mux, method, path, in)
	if w.Code != status {
		t.Fatalf("%s %s: %d %s", method, path, w.Code, w.Body.String())
	}
	var item MuseumPublication
	if status == 200 {
		if err := json.Unmarshal(w.Body.Bytes(), &item); err != nil {
			t.Fatal(err)
		}
	}
	return item
}
func TestMuseumComposerPublishingReferences(t *testing.T) {
	_, mux, public, cat := composerFixture()
	art := PublicationWrite{Kind: "artwork", Action: "save", Document: MuseumDocument{Title: "New museum artwork", DateLabel: "2024–2026"}}
	child := composerWrite(t, mux, "museum-a", "", art, 200)
	guide := PublicationWrite{Kind: "guide", Action: "save", Document: MuseumDocument{Title: "A guided visit", Body: "## Introduction", BodyFormat: "markdown", Artworks: []MuseumArtworkRef{{Kind: "museum", ID: child.ID, Note: "First stop"}, {Kind: "catalogue", ID: composerCatalogueID, Note: "Second stop"}}}}
	parent := composerWrite(t, mux, "museum-a", "", guide, 200)
	guide.Action = "publish"
	guide.Version = parent.Version
	composerWrite(t, mux, "museum-a", parent.ID, guide, 400)
	art.Action = "publish"
	art.Version = child.Version
	child = composerWrite(t, mux, "museum-a", child.ID, art, 200)
	parent = composerWrite(t, mux, "museum-a", parent.ID, guide, 200)
	art.Action = "save"
	art.Version = child.Version
	art.Document.Title = "Private changed title"
	child = composerWrite(t, mux, "museum-a", child.ID, art, 200)
	path := "/api/v1/museum-publications/museum-a/" + parent.ID
	w := studioCall(public, "GET", path, nil)
	if w.Code != 200 || strings.Contains(w.Body.String(), "Private changed title") {
		t.Fatal("draft child leaked", w.Code, w.Body.String())
	}
	var published MuseumPublication
	json.Unmarshal(w.Body.Bytes(), &published)
	if len(published.Artworks) != 2 || published.Artworks[0].Title != "New museum artwork" || published.Artworks[0].Note != "First stop" || published.Artworks[1].ID != composerCatalogueID {
		t.Fatal("ordered references not resolved", w.Body.String())
	}
	if len(cat.ids) != 1 {
		t.Fatal("catalogue lookup not scoped", cat.ids)
	}
	// A draft edit to the parent cannot change the notes or order seen publicly.
	guide.Action = "save"
	guide.Version = parent.Version
	guide.Document.Artworks[0].Note = "Private parent note"
	parent = composerWrite(t, mux, "museum-a", parent.ID, guide, 200)
	if w = studioCall(public, "GET", path, nil); strings.Contains(w.Body.String(), "Private parent note") {
		t.Fatal("parent draft leaked")
	}
	art.Action = "unpublish"
	art.Version = child.Version
	composerWrite(t, mux, "museum-a", child.ID, art, 200)
	w = studioCall(public, "GET", path, nil)
	json.Unmarshal(w.Body.Bytes(), &published)
	if w.Code != 200 || published.Artworks[0].Available || published.Artworks[0].ImageURL != "" || published.Artworks[0].Title != "Artwork unavailable" {
		t.Fatal("unpublished artwork exposed", w.Body.String())
	}
	guide.Action = "unpublish"
	guide.Version = parent.Version
	composerWrite(t, mux, "museum-a", parent.ID, guide, 200)
	if w = studioCall(public, "GET", path, nil); w.Code != 404 {
		t.Fatal("parent could not unpublish after child removed")
	}
	// Even another managed museum cannot attach this museum's artwork.
	studioCall(mux, "POST", "/api/v1/member/museum-studio/museum-b/claim", nil)
	guide.Action = "save"
	guide.Version = 0
	composerWrite(t, mux, "museum-b", "", guide, 400)
}
func TestMuseumComposerValidationAndClone(t *testing.T) {
	ref := MuseumArtworkRef{Kind: "catalogue", ID: composerCatalogueID}
	for _, refs := range [][]MuseumArtworkRef{{ref, ref}, {{Kind: "unknown", ID: composerCatalogueID}}, {{Kind: "museum", ID: "bad"}}, {{Kind: "catalogue", ID: composerCatalogueID, Note: strings.Repeat("a", 1001)}}, make([]MuseumArtworkRef, 49)} {
		if validateMuseumArtworks("guide", refs) == "" {
			t.Fatal("invalid references accepted", refs)
		}
	}
	if validateMuseumArtworks("artwork", []MuseumArtworkRef{ref}) == "" {
		t.Fatal("artwork nesting accepted")
	}
	s, _, _, _ := composerFixture()
	year := 2024
	doc := MuseumDocument{Title: "Guide", Artworks: []MuseumArtworkRef{ref}, YearStart: &year}
	p, err := s.Write(context.Background(), User{ID: "local-debug"}, "museum-a", "", PublicationWrite{Kind: "guide", Action: "publish", Document: doc})
	if err != nil {
		t.Fatal(err)
	}
	doc.Artworks[0].Note = "input mutation"
	*doc.YearStart = 1999
	p.Document.Artworks[0].Note = "output mutation"
	got, _ := s.Get(context.Background(), "museum-a", p.ID, true)
	if got.Document.Artworks[0].Note != "" || *got.Document.YearStart != 2024 {
		t.Fatal("published document shares mutable data")
	}
}
func composerPNG(t *testing.T) []byte {
	t.Helper()
	im := image.NewNRGBA(image.Rect(0, 0, 3, 2))
	im.Set(0, 0, color.NRGBA{255, 20, 10, 255})
	var buf bytes.Buffer
	if err := png.Encode(&buf, im); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}
func composerUpload(t *testing.T, mux http.Handler, slug string, raw []byte, status int) MuseumUpload {
	t.Helper()
	r := httptest.NewRequest("POST", "/api/v1/member/museum-studio/"+slug+"/images", bytes.NewReader(raw))
	r.RemoteAddr = "127.0.0.1:9988"
	r.Header.Set("Origin", "http://localhost:3000")
	r.Header.Set("Content-Type", "image/png")
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, r)
	if w.Code != status {
		t.Fatalf("upload: %d %s", w.Code, w.Body.String())
	}
	var info MuseumUpload
	if status == 200 {
		json.Unmarshal(w.Body.Bytes(), &info)
	}
	return info
}
func TestMuseumUploadPrivacyAndOwnership(t *testing.T) {
	_, mux, public, _ := composerFixture()
	raw := composerPNG(t)
	composerUpload(t, public, "museum-a", raw, 401)
	composerUpload(t, mux, "museum-b", raw, 403)
	upload := composerUpload(t, mux, "museum-a", append(raw, []byte("untrusted appended content")...), 200)
	path := "/api/v1/museum-media/museum-a/" + upload.ID
	if w := studioCall(public, "GET", path, nil); w.Code != 401 {
		t.Fatal("anonymous draft image read", w.Code)
	}
	if w := studioCall(mux, "GET", path, nil); w.Code != 200 || w.Header().Get("Content-Type") != "image/png" || bytes.Contains(w.Body.Bytes(), []byte("untrusted")) {
		t.Fatal("owner image read or normalization failed", w.Code)
	}
	if w := studioCall(mux, "GET", "/api/v1/museum-media/museum-b/"+upload.ID, nil); w.Code != 404 {
		t.Fatal("cross-museum image access")
	}
	doc := MuseumDocument{Title: "Uploaded work", DateLabel: "2026", ImageID: upload.ID, ImageAlt: "Red detail", ImageCredit: "Museum, test fixture"}
	studioCall(mux, "POST", "/api/v1/member/museum-studio/museum-b/claim", nil)
	composerWrite(t, mux, "museum-b", "", PublicationWrite{Kind: "artwork", Document: doc, Action: "save"}, 400)
	p := composerWrite(t, mux, "museum-a", "", PublicationWrite{Kind: "artwork", Document: doc, Action: "publish"}, 200)
	if w := studioCall(public, "GET", path, nil); w.Code != 200 || !strings.Contains(w.Header().Get("Cache-Control"), "no-store") {
		t.Fatal("published image not public or cached", w.Code)
	}
	next := composerUpload(t, mux, "museum-a", raw, 200)
	doc.ImageID = next.ID
	p = composerWrite(t, mux, "museum-a", p.ID, PublicationWrite{Kind: "artwork", Document: doc, Action: "save", Version: p.Version}, 200)
	if w := studioCall(public, "GET", "/api/v1/museum-media/museum-a/"+next.ID, nil); w.Code != 401 {
		t.Fatal("new draft image leaked")
	}
	if w := studioCall(public, "GET", path, nil); w.Code != 200 {
		t.Fatal("published image lost after draft update")
	}
	composerWrite(t, mux, "museum-a", p.ID, PublicationWrite{Kind: "artwork", Document: doc, Action: "unpublish", Version: p.Version}, 200)
	if w := studioCall(public, "GET", path, nil); w.Code != 401 {
		t.Fatal("image remained public after unpublishing")
	}
	composerUpload(t, mux, "museum-a", []byte(`<svg onload="alert(1)"/>`), 400)
	composerUpload(t, mux, "museum-a", make([]byte, museumUploadLimit+1), 413)
	r := httptest.NewRequest("POST", "/api/v1/member/museum-studio/museum-a/images", bytes.NewReader(raw))
	r.RemoteAddr = "127.0.0.1:9988"
	r.Header.Set("Origin", "https://foreign.example")
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, r)
	if w.Code != 403 {
		t.Fatal("cross-origin upload accepted", w.Code)
	}
}
func TestMuseumImageBoundsAndEXIF(t *testing.T) {
	raw := composerPNG(t)
	binary.BigEndian.PutUint32(raw[16:20], 100000)
	binary.BigEndian.PutUint32(raw[20:24], 100000)
	binary.BigEndian.PutUint32(raw[29:33], crc32.ChecksumIEEE(raw[12:29]))
	if _, _, err := prepareMuseumImage(raw); err == nil || !strings.Contains(err.Error(), "20 million") {
		t.Fatal("pixel bomb accepted", err)
	}
	im := image.NewNRGBA(image.Rect(0, 0, 3, 2))
	im.Set(0, 0, color.NRGBA{255, 0, 0, 255})
	var buf bytes.Buffer
	jpeg.Encode(&buf, im, nil)
	// Little-endian EXIF orientation 6 rotates a 3x2 image to 2x3.
	exif := []byte{'E', 'x', 'i', 'f', 0, 0, 'I', 'I', 42, 0, 8, 0, 0, 0, 1, 0, 0x12, 1, 3, 0, 1, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0}
	oriented := append([]byte{0xff, 0xd8, 0xff, 0xe1, 0, byte(len(exif) + 2)}, exif...)
	oriented = append(oriented, buf.Bytes()[2:]...)
	out, info, err := prepareMuseumImage(oriented)
	if err != nil || info.Width != 2 || info.Height != 3 || bytes.Contains(out, []byte("Exif")) {
		t.Fatal("orientation or metadata stripping failed", info, err)
	}
	for _, tc := range []struct{ o, x, y int }{{2, 2, 0}, {3, 2, 1}, {4, 0, 1}, {5, 0, 0}, {6, 1, 0}, {7, 1, 2}, {8, 0, 2}} {
		r, _, _, _ := orientMuseumImage(im, tc.o).At(tc.x, tc.y).RGBA()
		if r != 65535 {
			t.Fatal("orientation", tc.o)
		}
	}
}
