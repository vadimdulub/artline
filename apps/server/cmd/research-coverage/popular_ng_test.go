package main

import (
	"net/url"
	"testing"
)

func ngFixture() ngObject {
	return ngObject{"_id": "TEST-0001", "_source": ngObject{
		"summary": ngObject{"title": "Painting"}, "identifier": []any{ngObject{"type": "object number", "value": "NG999"}},
		"category":       []any{ngObject{"type": "department", "value": "Main Collection"}},
		"classification": []any{ngObject{"type": "classification", "value": "Picture"}},
		"legal":          ngObject{"status": "Accessioned object", "credit": "Gift"},
		"material":       []any{ngObject{"value": "oil on canvas"}},
		"creation": []any{ngObject{
			"maker":       []any{ngObject{"summary": ngObject{"title": "Piero della Francesca"}, "@link": ngObject{"historical": false, "role": ngObject{"value": "Artist"}}}},
			"attribution": []any{ngObject{"type": "attribution", "value": "Piero della Francesca"}},
			"date":        []any{ngObject{"from": "1480", "to": "1483", "value": "early 1480s"}},
		}},
	}}
}
func TestPopularNGSourceGates(t *testing.T) {
	a := popularNGArtist{QID: "Q5822", Name: "Piero della Francesca"}
	index := map[string][]knownAuthor{authorityKey(a.Name): {{QID: a.QID, Name: a.Name}}}
	w, state := popularNGWork(ngFixture(), a, index)
	if state != "eligible" {
		t.Fatal(state)
	}
	if d := w["creation_date"].(creationDate); d.First != 1480 || d.Last != 1483 || d.Precision != "range" {
		t.Fatal(d)
	}
	for _, mutate := range []func(ngObject){
		func(s ngObject) { s["legal"] = ngObject{"status": "Loan"} },
		func(s ngObject) {
			c := ngMap(ngArray(s["creation"])[0])
			c["date"] = []any{ngObject{"from": "1960", "to": "1980", "value": "1960-1980"}}
		},
		func(s ngObject) {
			c := ngMap(ngArray(s["creation"])[0])
			c["date"] = []any{ngObject{"from": "1480", "to": "1483", "value": ""}}
		},
		func(s ngObject) {
			c := ngMap(ngArray(s["creation"])[0])
			c["attribution"] = []any{ngObject{"type": "attribution", "value": "Workshop of Piero della Francesca"}}
		},
		func(s ngObject) { s["summary"] = ngObject{"title": "Fragments from an altarpiece"} },
	} {
		h := ngFixture()
		mutate(ngMap(h["_source"]))
		if _, state = popularNGWork(h, a, index); state == "eligible" {
			t.Fatal("unsafe candidate accepted")
		}
	}
}
func TestPopularNGQueryIsBounded(t *testing.T) {
	u, err := url.Parse(popularNGQuery(popularNGArtist{QID: "Q5822", Name: "Piero della Francesca"}))
	if err != nil || u.Host != "data.ng.ac.uk" || u.Query().Get("size") != "100" {
		t.Fatal(u, err)
	}
}
