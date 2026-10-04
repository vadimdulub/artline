package timeline

import "testing"

func TestFitExtent(t *testing.T) {
	for _, test := range []struct{ start, end, low, high, wantStart, wantEnd int }{
		{1800, 1900, 1100, 2000, 1800, 1900}, {1790, 1910, 1800, 1900, 1800, 1900},
		{1800, 1800, 1100, 2000, 1800, 1801}, {-1, -1, -5000, 2000, -1, 1}, {1, 1, -5000, 1, -1, 1},
	} {
		got := FitExtent(&test.start, &test.end, test.low, test.high)
		if got == nil || got.Start != test.wantStart || got.End != test.wantEnd {
			t.Fatalf("%+v: %+v", test, got)
		}
	}
	if FitExtent(nil, nil, 1100, 2000) != nil {
		t.Fatal("unknown dates invented")
	}
	got := MergeExtents(&DateExtent{1700, 1800}, &DateExtent{1850, 1900})
	if got.Start != 1700 || got.End != 1900 {
		t.Fatal(got)
	}
}
