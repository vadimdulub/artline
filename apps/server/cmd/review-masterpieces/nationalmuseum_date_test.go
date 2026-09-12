package main

import (
	"os"
	"testing"
)

func TestNationalmuseumMonetCreationEvidence(t *testing.T) {
	b, err := os.ReadFile("../../../../content/imports/popular-nationalmuseum-20260911/19182.html")
	if err != nil {
		t.Fatal(err)
	}
	if hash(b) != nationalmuseumMonetCapture {
		t.Fatal("capture changed")
	}
	fixture := func() map[string]any {
		r, e := nationalmuseumItem(b)
		if e != nil {
			t.Fatal(e)
		}
		return r
	}
	if err = validateNationalmuseumMonet(fixture()); err != nil {
		t.Fatal(err)
	}
	for _, mutate := range []func(map[string]any){
		func(r map[string]any) { r["ObjDescriptionTxt_sv"] = "Signed 1882" },
		func(r map[string]any) { r["ObjInventoryNumberTxt"] = "NM 2513" },
		func(r map[string]any) { r["ObjToYearTxt"] = "1971" },
		func(r map[string]any) { r["ObjTitleMainTxt"] = "Another Monet" },
		func(r map[string]any) {
			obj(obj(r["ObjPersonRef"])["Items"].([]any)[0])["ReferencedId"] = "another_artist"
		},
		func(r map[string]any) {
			obj(obj(obj(r["ObjPersonRef"])["Items"].([]any)[0])["RoleVoc"])["LabelTxt"] = "Copy after"
		},
	} {
		r := fixture()
		mutate(r)
		if validateNationalmuseumMonet(r) == nil {
			t.Fatal("accepted conflicting evidence")
		}
	}
	if _, err = nationalmuseumItem(append(b, b...)); err == nil {
		t.Fatal("accepted ambiguous payload")
	}
}
