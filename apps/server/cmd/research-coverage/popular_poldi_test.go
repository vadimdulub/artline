package main

import (
	"os"
	"strings"
	"testing"
)

func TestPoldiExactFields(t *testing.T) {
	for _, f := range poldiFacts {
		b, e := os.ReadFile("../../../../content/imports/popular-resume-20260911-1852/poldi/" + f.File + ".html")
		if e != nil {
			t.Fatal(e)
		}
		if e = verifyPoldi(string(b), f); e != nil {
			t.Fatal(e)
		}
		for _, field := range []string{f.Acc, f.Medium, f.Date, f.Heading} {
			if verifyPoldi(strings.ReplaceAll(string(b), field, "changed"), f) == nil {
				t.Fatal("changed Poldi facts accepted")
			}
		}
	}
}
