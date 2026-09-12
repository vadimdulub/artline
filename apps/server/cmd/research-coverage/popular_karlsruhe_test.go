package main

import (
	"os"
	"testing"
)

func TestKarlsruheExactFields(t *testing.T) {
	for _, f := range append(append([]karlsruheFact{}, karlsruheFacts...), karlsruheNextFacts...) {
		b, e := os.ReadFile("../../../../" + karlsruheCaptureDir(f.File) + "/" + f.File + ".html")
		if e != nil {
			t.Fatal(e)
		}
		if e = verifyKarlsruhe(string(b), f); e != nil {
			t.Fatalf("%s: %v", f.File, e)
		}
		for i := 0; i < 4; i++ {
			bad := f
			switch i {
			case 0:
				bad.Acc = "changed"
			case 1:
				bad.Date = "changed"
			case 2:
				bad.Artist = "changed"
			case 3:
				bad.Material = "changed"
			}
			if verifyKarlsruhe(string(b), bad) == nil {
				t.Fatalf("accepted changed field %d", i)
			}
		}
	}
}
func TestKarlsruheClosedRoutes(t *testing.T) {
	for _, p := range karlsruhePages {
		if !karlsruhePageAllowed(p.URL) {
			t.Fatal(p.URL)
		}
	}
	for _, u := range []string{"https://www.kunsthalle-karlsruhe.de/wp-admin/", "https://www.kunsthalle-karlsruhe.de/sammlung/alle-werke/", karlsruhePages[3].URL + "?other=1"} {
		if karlsruhePageAllowed(u) {
			t.Fatal("unreviewed route accepted")
		}
	}
}
