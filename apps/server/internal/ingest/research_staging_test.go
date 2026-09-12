package ingest

import (
	"context"
	"encoding/json"
	"testing"
)

func TestResearchStageValidation(t *testing.T) {
	row := ResearchRecord{Source: "wikidata", Kind: "museum_candidate", RecordID: "Q1", Country: "US", Name: "Test Museum", URL: "https://www.wikidata.org/wiki/Q1", Decision: "discovery_candidate", Raw: json.RawMessage(`{"verified":false}`)}
	if e := validateResearch([]ResearchRecord{row}); e != nil {
		t.Fatal(e)
	}
	if e := validateResearch([]ResearchRecord{row, row}); e == nil {
		t.Fatal("duplicate accepted")
	}
	row.URL = "https://user:secret@example.com/x"
	if e := validateResearch([]ResearchRecord{row}); e == nil {
		t.Fatal("credentials accepted")
	}
	if _, e := StageResearch(context.Background(), nil, []byte("[]"), "bad", "test", false); e == nil {
		t.Fatal("bad SHA accepted")
	}
}
func TestResearchStageRollbackAndReplay(t *testing.T) {
	pool := europeanDB(t)
	ctx := context.Background()
	rows := []ResearchRecord{{Source: "nga", Kind: "catalogue_object", RecordID: "1", Country: "US", Name: "Test painting", URL: "https://www.nga.gov/collection/art-object-page.1.html", Decision: "date_literal_requires_review", Raw: json.RawMessage(`{"displaydate":""}`)}}
	data, _ := json.Marshal(rows)
	before := europeanCounts(t, pool)
	r, e := StageResearch(ctx, pool, data, checksum(data), "test", false)
	if e != nil || r.Applied {
		t.Fatal(r, e)
	}
	var n int
	if e = pool.QueryRow(ctx, `SELECT count(*) FROM research_records`).Scan(&n); e != nil || n != 0 {
		t.Fatal("preview wrote", n, e)
	}
	r, e = StageResearch(ctx, pool, data, checksum(data), "test", true)
	if e != nil || !r.Applied || r.Replayed {
		t.Fatal(r, e)
	}
	r, e = StageResearch(ctx, pool, data, checksum(data), "test", true)
	if e != nil || !r.Replayed {
		t.Fatal(r, e)
	}
	if europeanCounts(t, pool) != before {
		t.Fatal("staging changed public catalogue")
	}
}
