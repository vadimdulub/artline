package main

import (
	"os"
	"strings"
	"testing"
)

func TestEntombmentExactNotice(t *testing.T) {
	b, e := os.ReadFile("../../../../content/imports/popular-resume-20260911-1852/athens-entombment/entombment.html")
	if e != nil {
		t.Fatal(e)
	}
	if e = verifyEntombment(b); e != nil {
		t.Fatal(e)
	}
	for _, v := range []string{"Π.9979", "1568-1570", "Theotokopoulos"} {
		if verifyEntombment([]byte(strings.ReplaceAll(string(b), v, "changed"))) == nil {
			t.Fatal("changed source accepted")
		}
	}
}
