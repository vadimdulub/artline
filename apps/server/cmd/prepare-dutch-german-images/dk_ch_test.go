package main

import (
	"strings"
	"testing"
	"time"
)

func TestDKCHExactRights(t *testing.T) {
	e := map[string]any{"artwork_id": "bde58d01-8a1e-5a9b-9ad8-9175ff377b99", "source_image_url": "https://sammlung.kunstmuseumbasel.ch/multimedia/5/multimedia-123785.large.jpg", "identity_basis": "Exact image in public-domain object", "creator_credit": "Kunstmuseum Basel", "source_evidence_sha256": strings.Repeat("a", 64), "provider": "denmark-switzerland-selected", "rights_status": "public_domain", "policy_url": "https://download.kunstmuseumbasel.ch/app/snippets/infoClaim.html", "checked_at": time.Now().UTC().Format(time.RFC3339)}
	if err := validate([]map[string]any{e}); err != nil {
		t.Fatal(err)
	}
	if imagePrefix(e) != "denmark-switzerland" {
		t.Fatal("wrong asset namespace")
	}
	if err := validate([]map[string]any{e, e}); err == nil {
		t.Fatal("duplicate accepted")
	}
	e["rights_status"] = "cc0"
	if err := validate([]map[string]any{e}); err == nil {
		t.Fatal("invented Basel CC0 accepted")
	}
	e["source_image_url"] = "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8a/Example.jpg/960px-Example.jpg"
	e["rights_status"] = "cc_by"
	e["policy_url"] = "https://creativecommons.org/licenses/by/3.0/"
	if err := validate([]map[string]any{e}); err != nil {
		t.Fatal(err)
	}
	e["policy_url"] = "https://creativecommons.org/licenses/by-nc/3.0/"
	if err := validate([]map[string]any{e}); err == nil {
		t.Fatal("noncommercial accepted")
	}
	e["policy_url"] = "https://creativecommons.org/licenses/by/3.0/"
	e["source_image_url"] = "https://thumb.wikimedia.org.attacker.invalid/wikipedia/commons/example.jpg"
	if err := validate([]map[string]any{e}); err == nil {
		t.Fatal("unapproved host accepted")
	}
}

func TestDKCHFollowupOnlyCommons(t *testing.T) {
	e := map[string]any{"artwork_id": "bde58d01-8a1e-5a9b-9ad8-9175ff377b99", "source_image_url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Example.jpg/960px-Example.jpg", "identity_basis": "Exact inventory", "creator_credit": "Photographer", "source_evidence_sha256": strings.Repeat("a", 64), "provider": "denmark-switzerland-followup", "rights_status": "cc_by_sa", "policy_url": "https://creativecommons.org/licenses/by-sa/4.0/", "checked_at": time.Now().UTC().Format(time.RFC3339)}
	if err := validate([]map[string]any{e}); err != nil {
		t.Fatal(err)
	}
	if imageSourceFolder(e) != "denmark-switzerland-more-images-20260918" {
		t.Fatal("wrong source folder")
	}
	e["source_image_url"] = "https://sammlung.kunstmuseumbasel.ch/multimedia/5/multimedia-123785.large.jpg"
	e["rights_status"] = "public_domain"
	e["policy_url"] = "https://download.kunstmuseumbasel.ch/app/snippets/infoClaim.html"
	if err := validate([]map[string]any{e}); err == nil {
		t.Fatal("previously denied museum route accepted in follow-up")
	}
}
