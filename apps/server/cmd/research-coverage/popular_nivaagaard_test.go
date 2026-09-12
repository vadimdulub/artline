package main

import (
	"os"
	"strings"
	"testing"
)

func TestNivaagaardPrimaryFacts(t *testing.T) {
	for _, f := range nivaFacts {
		t.Run(f.Acc, func(t *testing.T) {
			b, e := os.ReadFile("../../../../content/imports/popular-resume-20260911-1852/nivaagaard/" + f.Slug + ".html")
			if e != nil {
				t.Fatal(e)
			}
			s := string(b)
			if e = verifyNivaFact(s, f); e != nil {
				t.Fatal(e)
			}
			for _, changed := range []string{strings.ReplaceAll(s, "Inventory number: "+f.Acc, "Inventory number: OTHER"), strings.ReplaceAll(s, f.MediumLine, "Oil on a different support"), strings.ReplaceAll(s, f.Heading, "Workshop of "+f.Heading), s + "<h6>Inventory number: SECOND</h6>", strings.ReplaceAll(s, f.Acquisition, "Collection connection unknown")} {
				if verifyNivaFact(changed, f) == nil {
					t.Fatal("accepted changed/ambiguous primary fields")
				}
			}
		})
	}
}
