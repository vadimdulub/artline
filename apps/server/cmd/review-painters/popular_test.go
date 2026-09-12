package main

import "testing"

func TestPopularCreditRolePreservesQualification(t *testing.T) {
	w := Work{Credits: []Credit{{ID: "artist-a", Role: "after"}, {ID: "artist-b", Role: "primary"}}}
	if got := popularCreditRole(w, "artist-a"); got != "after" {
		t.Fatal(got)
	}
	if got := popularCreditRole(w, "artist-b"); got != "primary" {
		t.Fatal(got)
	}
	if got := popularCreditRole(w, "other"); got != "unresolved attribution" {
		t.Fatal(got)
	}
}
