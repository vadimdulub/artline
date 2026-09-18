package events

import (
	"encoding/json"
	"strings"
	"testing"
)

func sampleDescription() DescriptionUpdate {
	return DescriptionUpdate{ID: "event-q361", PreviousDescription: "Old description", Description: "A short source-backed description.", Source: DescriptionSource{Name: "Wikipedia", URL: "https://en.wikipedia.org/wiki/World_War_I", Kind: "wikipedia", Title: "World War I", Revision: 123, RetrievedAt: "2026-09-18T00:00:00+00:00", License: "CC BY-SA 4.0", LicenseURL: "https://creativecommons.org/licenses/by-sa/4.0/", Notice: "Shortened excerpt."}}
}

func TestDescriptionEvidenceValidation(t *testing.T) {
	u := sampleDescription()
	if err := ValidateDescriptions([]DescriptionUpdate{u}, 1); err != nil {
		t.Fatal(err)
	}
	for _, change := range []func(*DescriptionUpdate){
		func(v *DescriptionUpdate) { v.Description = "" },
		func(v *DescriptionUpdate) { v.Description = strings.Repeat("a", 1201) },
		func(v *DescriptionUpdate) { v.Source.URL = "https://en.wikipedia.org.evil.example/wiki/World_War_I" },
		func(v *DescriptionUpdate) { v.Source.LicenseURL = "javascript:alert(1)" },
		func(v *DescriptionUpdate) { v.Source.Revision = 0 },
		func(v *DescriptionUpdate) { v.Source.Kind = "editorial" },
		func(v *DescriptionUpdate) { v.Source.Kind = "guessed" },
	} {
		invalid := u
		change(&invalid)
		if ValidateDescriptions([]DescriptionUpdate{invalid}, 1) == nil {
			t.Fatalf("accepted invalid evidence: %+v", invalid)
		}
	}
	if ValidateDescriptions([]DescriptionUpdate{u, u}, 2) == nil {
		t.Fatal("duplicate accepted")
	}
	if ValidateDescriptions([]DescriptionUpdate{u}, 10000) == nil {
		t.Fatal("partial batch accepted")
	}
}

func TestDescriptionPatchPreservesMetadataAndRefusesConflicts(t *testing.T) {
	raw := []byte(`{"id":"event-q361","description":"Old description","startYear":1914,"status":"review","futureMetadata":{"keep":[1,"unknown"]}}`)
	u := sampleDescription()
	result, changed, err := describeRecord(raw, u)
	if err != nil || !changed {
		t.Fatal(changed, err)
	}
	var before, after map[string]json.RawMessage
	json.Unmarshal(raw, &before)
	json.Unmarshal(result, &after)
	for _, key := range []string{"id", "startYear", "status", "futureMetadata"} {
		if string(before[key]) != string(after[key]) {
			t.Fatalf("changed unrelated %s", key)
		}
	}
	if _, changed, err = describeRecord(result, u); err != nil || changed {
		t.Fatal("replay was not idempotent", err)
	}
	other := u
	other.Description = "New conflicting description."
	if _, _, err = describeRecord(result, other); err == nil {
		t.Fatal("overwrote prior enrichment")
	}
	other = u
	other.PreviousDescription = "Someone edited it"
	if _, _, err = describeRecord(raw, other); err == nil {
		t.Fatal("overwrote different editorial description")
	}
}

func TestTranslatedDescriptionReconciliation(t *testing.T) {
	old := sampleDescription()
	raw, _, err := describeRecord([]byte(`{"description":"Old description","unknown":{"retain":true}}`), old)
	if err != nil {
		t.Fatal(err)
	}
	next := old
	next.PreviousDescription = old.Description
	next.PreviousSource = &old.Source
	next.Description = "An English summary translated from a French article."
	next.Source.Language = "fr"
	next.Source.URL = "https://fr.wikipedia.org/wiki/Premi%C3%A8re_Guerre_mondiale"
	if err := ValidateDescriptions([]DescriptionUpdate{next}, 1); err != nil {
		t.Fatal(err)
	}
	result, changed, err := describeRecord(raw, next)
	if err != nil || !changed || !strings.Contains(string(result), `"unknown":{"retain":true}`) {
		t.Fatal(changed, err, string(result))
	}
	if _, changed, err := describeRecord(result, next); err != nil || changed {
		t.Fatal("replay", changed, err)
	}
	wrong := next
	wrong.Source.Language = "ru"
	if ValidateDescriptions([]DescriptionUpdate{wrong}, 1) == nil {
		t.Fatal("accepted mismatched language host")
	}
	wrong = next
	changedSource := old.Source
	changedSource.Revision++
	wrong.PreviousSource = &changedSource
	if _, _, err := describeRecord(raw, wrong); err == nil {
		t.Fatal("overwrote changed source")
	}
	wrong = next
	wrong.PreviousDescription = "Stale expected text"
	if _, _, err := describeRecord(raw, wrong); err == nil {
		t.Fatal("overwrote changed text")
	}
	if _, _, err := describeRecord([]byte(`{"description":"Old description"}`), next); err == nil {
		t.Fatal("accepted missing expected source")
	}
	var record map[string]any
	json.Unmarshal(raw, &record)
	record["descriptionSource"].(map[string]any)["futureEvidence"] = "preserve"
	unknownSource, _ := json.Marshal(record)
	if _, _, err := describeRecord(unknownSource, next); err == nil {
		t.Fatal("overwrote unknown source metadata")
	}
}
