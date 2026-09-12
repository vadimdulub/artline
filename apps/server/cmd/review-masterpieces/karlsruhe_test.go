package main

import (
	"encoding/base64"
	"encoding/json"
	"os"
	"strings"
	"testing"
)

func TestKarlsruheRawEvidenceRoundTrip(t *testing.T) {
	b := []byte("museum canonical Fran\xc3-ois")
	raw := map[string]any{"html_base64": base64.StdEncoding.EncodeToString(b)}
	encoded, err := json.Marshal(raw)
	if err != nil {
		t.Fatal(err)
	}
	var decoded map[string]any
	if err = json.Unmarshal(encoded, &decoded); err != nil {
		t.Fatal(err)
	}
	got, err := karlsruheRawHTML(decoded)
	if err != nil || hash([]byte(got)) != hash(b) {
		t.Fatal("raw evidence changed")
	}
	decoded["html"] = "different"
	if _, err = karlsruheRawHTML(decoded); err == nil {
		t.Fatal("ambiguous evidence accepted")
	}
	if _, err = karlsruheRawHTML(map[string]any{"html_base64": "%%%"}); err == nil {
		t.Fatal("invalid encoding accepted")
	}
}

func TestKarlsruheMainImageIdentity(t *testing.T) {
	for _, f := range karlsruheImageFacts {
		b, e := os.ReadFile("../../../../" + karlsruheImageCaptureDir(f) + "/" + f.File + ".html")
		if e != nil {
			t.Fatal(e)
		}
		u, e := karlsruheImage(string(b), f)
		if e != nil || u == "" {
			t.Fatalf("%s: %v", f.File, e)
		}
		// Re-pin modified fixtures to test extraction gates independently of digest gate.
		for _, bad := range []string{strings.ReplaceAll(string(b), "Public Domain", "Copyright"), strings.ReplaceAll(string(b), `data-id="`+f.Object+`"`, `data-id="wrong"`), strings.ReplaceAll(string(b), u, "https://example.org/crop.jpg")} {
			g := f
			g.SHA = hash([]byte(bad))
			if _, e = karlsruheImage(bad, g); e == nil {
				t.Fatal("changed composition/rights accepted")
			}
		}
	}
}
