package main

import (
	"errors"
	"net/url"
	"regexp"
	"strings"
	"time"
)

// This separate, opt-in adapter reuses the bounded full-frame image pipeline.
// No existing Dutch/German host or permission rules are broadened.
func imagePrefix(e map[string]any) string {
	if text(e, "provider") == "denmark-switzerland-followup" {
		return "denmark-switzerland-followup"
	}
	if text(e, "provider") == "denmark-switzerland-selected" {
		return "denmark-switzerland"
	}
	return "dutch-german"
}

func imageSourceFolder(e map[string]any) string {
	if text(e, "provider") == "denmark-switzerland-followup" {
		return "denmark-switzerland-more-images-20260918"
	}
	return imagePrefix(e) + "-museums-20260917"
}

func validateDKCH(e map[string]any, seen map[string]bool) error {
	id := text(e, "artwork_id")
	u, err := url.Parse(text(e, "source_image_url"))
	if err != nil || u.Scheme != "https" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || !regexp.MustCompile(`^[a-f0-9-]{36}$`).MatchString(id) || seen[id] {
		return errors.New("invalid DK/CH image identity or URL")
	}
	basel := u.Host == "sammlung.kunstmuseumbasel.ch" && regexp.MustCompile(`^/multimedia/\d+/multimedia-\d+\.large\.jpg$`).MatchString(u.Path)
	commons := (u.Host == "thumb.wikimedia.org" || u.Host == "upload.wikimedia.org") && strings.HasPrefix(u.Path, "/wikipedia/commons/") && strings.HasSuffix(strings.ToLower(u.Path), ".jpg")
	if !basel && !commons {
		return errors.New("unapproved DK/CH image host/path")
	}
	rights, policy := text(e, "rights_status"), text(e, "policy_url")
	allowed := basel && rights == "public_domain" && policy == "https://download.kunstmuseumbasel.ch/app/snippets/infoClaim.html"
	allowed = allowed || (commons && ((rights == "public_domain" && policy == "https://creativecommons.org/publicdomain/mark/1.0/") || (rights == "cc0" && policy == "https://creativecommons.org/publicdomain/zero/1.0/") || (rights == "cc_by" && policy == "https://creativecommons.org/licenses/by/3.0/")))
	if text(e, "provider") == "denmark-switzerland-followup" {
		// Follow-up uses independently public Commons files only. The denied
		// museum image server is not an allowed route for this batch.
		allowed = commons && ((rights == "public_domain" && policy == "https://creativecommons.org/publicdomain/mark/1.0/") || (rights == "cc_by_sa" && policy == "https://creativecommons.org/licenses/by-sa/4.0/"))
	}
	if !allowed || text(e, "identity_basis") == "" || text(e, "creator_credit") == "" || !regexp.MustCompile(`^[a-f0-9]{64}$`).MatchString(text(e, "source_evidence_sha256")) {
		return errors.New("missing DK/CH exact-source rights or identity evidence")
	}
	checked, err := time.Parse(time.RFC3339, text(e, "checked_at"))
	if err != nil || time.Since(checked) > 24*time.Hour || checked.After(time.Now().Add(5*time.Minute)) {
		return errors.New("stale DK/CH rights review")
	}
	seen[id] = true
	return nil
}
