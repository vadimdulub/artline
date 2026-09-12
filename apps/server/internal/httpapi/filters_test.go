package httpapi

import (
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"
)

func TestMultipleChoices(t *testing.T) {
	got, err := parseChoices([]string{" Monet, Pissarro ", "monet"}, museumSlugPattern.MatchString, false)
	if err != nil || !reflect.DeepEqual(got, []string{"monet", "pissarro"}) {
		t.Fatalf("%v %v", got, err)
	}
	for _, raw := range []string{"monet'--", strings.Repeat("monet,", 33), strings.Repeat("a", 101)} {
		if _, err = parseChoices([]string{raw}, museumSlugPattern.MatchString, false); err == nil {
			t.Fatalf("accepted %q", raw)
		}
	}
	f, err := museumFilter(httptest.NewRequest("GET", "/api/v1/museums/x/works?artist=monet&artist=pissarro&movement=impressionism,baroque&work_type=painting&work_type=fresco", nil))
	if err != nil || len(f.Artists) != 2 || len(f.Movements) != 2 || len(f.WorkTypes) != 2 {
		t.Fatalf("lost repeated values: %+v %v", f, err)
	}
}

func TestParseRegions(t *testing.T) {
	for _, tc := range []struct {
		name        string
		input, want []string
	}{
		{"empty", nil, []string{}},
		{"legacy", []string{"northern-europe"}, []string{"northern-europe"}},
		{"multiple", []string{"northern-europe", "eastern-asia"}, []string{"eastern-asia", "northern-europe"}},
		{"normalize", []string{" Northern-Europe,eastern-asia ", "northern-europe", ""}, []string{"eastern-asia", "northern-europe"}},
		{"future region", []string{"western-africa"}, []string{"western-africa"}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got, err := parseRegions(tc.input)
			if err != nil || !reflect.DeepEqual(got, tc.want) {
				t.Fatalf("got %v, %v; want %v", got, err, tc.want)
			}
		})
	}
	for _, raw := range []string{"europe' OR 1=1", "northern_europe", strings.Repeat("a", 65), strings.Repeat("europe,", 33)} {
		if _, err := parseRegions([]string{raw}); err == nil {
			t.Errorf("accepted malformed/oversized selection %q", raw)
		}
	}
}

func TestParsePopular(t *testing.T) {
	for _, tc := range []struct {
		raw   []string
		want  bool
		valid bool
	}{
		{nil, true, true}, {[]string{"true"}, true, true}, {[]string{"false"}, false, true},
		{[]string{""}, false, false}, {[]string{"yes"}, false, false}, {[]string{"true", "false"}, false, false},
	} {
		got, err := parsePopular(tc.raw)
		if (err == nil) != tc.valid || (tc.valid && got != tc.want) {
			t.Fatalf("%v: got %v, %v", tc.raw, got, err)
		}
	}
}
