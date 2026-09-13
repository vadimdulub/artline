package ingest

import "testing"

func TestIncompleteReviewArtwork(t *testing.T) {
	cells := []string{"Jane Painter", "Unfinished landscape", "", "Museum supplied by user", "Country", "true"}
	p, err := planReviewArtwork(expandedInputSHA, expandedInputSHA, cells, nil, "", "", "")
	if err != nil {
		t.Fatal(err)
	}
	if p.Excluded || p.WorkType != "unknown" || p.First != nil || p.Last != nil || p.Precision != "unknown" || p.Creator != cells[0] || p.ObjectURL != "" {
		t.Fatalf("invented metadata: %+v", p)
	}
	p.WorkType = "painting"
	if validateReviewArtwork(p) == nil {
		t.Fatal("accepted fabricated supplied-only artwork type")
	}
}
func TestReviewArtworkCutoff(t *testing.T) {
	for _, tt := range []struct {
		date      string
		excluded  bool
		precision string
	}{{"1971", true, "exact"}, {"1960-1980", false, "range"}, {"c. 1970", false, "circa"}, {"date not recorded", false, "unknown"}, {"1870", false, "exact"}} {
		cells := []string{"Jane Painter", "Landscape", tt.date, "Museum", "Country", "false"}
		p, err := planReviewArtwork(expandedInputSHA, expandedInputSHA, cells, nil, "", "", "")
		if err != nil || p.Excluded != tt.excluded || p.Precision != tt.precision {
			t.Fatalf("%s: %+v %v", tt.date, p, err)
		}
	}
}
func TestReviewArtworkAttributionHold(t *testing.T) {
	cells := []string{"Named painter", "Landscape", "1800", "Museum", "Country", "false"}
	f := &ResolvedFact{Source: "smk", ObjectID: "KMS1", ObjectURL: "https://open.smk.dk/artwork/image/KMS1", Painter: ResolvedPainter{Name: "Named painter"}, CSVCells: cells}
	p, err := planReviewArtwork(expandedInputSHA, expandedInputSHA, cells, f, expandedInputSHA, "conflict", "creator_attribution_review")
	if err != nil || !p.Excluded {
		t.Fatalf("attribution hold lost: %+v %v", p, err)
	}
}
