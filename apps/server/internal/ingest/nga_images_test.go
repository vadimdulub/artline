package ingest

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"os"
	"testing"
)

func TestNGAImageResponseBounds(t *testing.T) {
	for _, tc := range []struct {
		status, size int
		start        int64
		valid        bool
	}{
		{200, 16000, 0, true}, {200, 2 << 20, 0, true}, {200, (2 << 20) + 1, 0, false},
		{206, 8192, 0, true}, {206, 8193, 0, false}, {200, 20, 8192, false},
	} {
		b, e := readNGAImageResponse(&http.Response{StatusCode: tc.status, Body: io.NopCloser(bytes.NewReader(make([]byte, tc.size)))}, tc.start)
		if (e == nil) != tc.valid || tc.valid && len(b) != tc.size {
			t.Fatalf("%+v: %d %v", tc, len(b), e)
		}
	}
}

func TestNGASelectedImageEvidence(t *testing.T) {
	b, e := os.ReadFile("../../../../" + NGAImagesPath)
	if e != nil || checksum(b) != NGAImagesSHA {
		t.Fatal("snapshot", e)
	}
	var m struct{ Images []ngaSelectedImage }
	if e = json.Unmarshal(b, &m); e != nil {
		t.Fatal(e)
	}
	if len(m.Images) != 20 {
		t.Fatal("selection changed")
	}
	seen := map[string]bool{}
	for _, x := range m.Images {
		if seen[x.ObjectID] || x.Raw["openaccess"] != "1" || x.Raw["viewtype"] != "primary" || x.Raw["depictstmsobjectid"] != x.ObjectID || x.Raw["uuid"] != x.UUID || !ngaImageURL.MatchString(x.URL) {
			t.Fatal("identity/rights", x.ObjectID)
		}
		seen[x.ObjectID] = true
	}
	if _, e = ImportNGAImages(context.Background(), nil, append(b, ' '), t.TempDir(), false); e == nil {
		t.Fatal("changed snapshot")
	}
	if _, e = downloadNGARanges(context.Background(), ngaSelectedImage{URL: "http://localhost/unsafe"}, t.TempDir()); e == nil {
		t.Fatal("unapproved host")
	}
}
