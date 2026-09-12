package main

import "testing"

func TestCatalogueMakerExactCrosswalk(t *testing.T) {
	for _, c := range [][3]string{{"Q42207", "Caravaggio", "Michelangelo Merisi da Caravaggio"}, {"Q46373", "Edgar Degas", "Hilaire-Germain-Edgar Degas"}, {"Q296", "Claude Monet", "Claude Monet"}} {
		if got := catalogueMaker(c[0], c[1]); got != c[2] {
			t.Fatalf("%s: %q", c[0], got)
		}
	}
	if catalogueMaker("Q42207", "Caravaggio") == "Polidoro da Caravaggio" {
		t.Fatal("unrelated namesake")
	}
}

func TestOverallDimensionsSkipsEmptyAndFrame(t *testing.T) {
	measurements := []any{obj{"type": "Overall"}, obj{"type": "Frame", "display": "130 x 150 cm"}, obj{"type": "Overall", "display": "96 x 121.2 cm"}}
	if got := overallDimensions(measurements); got != "96 x 121.2 cm" {
		t.Fatal(got)
	}
	if got := overallDimensions([]any{obj{"type": "Overall", "display": " "}}); got != "" {
		t.Fatal(got)
	}
}
