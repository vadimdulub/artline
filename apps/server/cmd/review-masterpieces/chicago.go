package main

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"net/url"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
)

const chicagoPolicy = "https://api.artic.edu/docs/#copyright"

var chicagoPicks = []coveragePick{
	{"chicago", "16633", "Alfred Sisley", "The Seine at Port-Marly, Piles of Sand: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "37741", "Alfred Sisley", "Watering Place at Marly: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "58984", "Alfred Sisley", "Landscape along the Seine with the Institut de France and the Pont des Arts: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "73054", "Alfred Sisley", "The Loire: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "81561", "Alfred Sisley", "Street in Moret: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "96559", "Alfred Sisley", "A Turn in the Road: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "110541", "Camille Pissarro", "The Crystal Palace: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "11312", "Camille Pissarro", "Woman Mending: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "20530", "Camille Pissarro", "Rabbit Warren at Pontoise, Snow: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "45838", "Camille Pissarro", "Snow at Louveciennes: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "6005", "Camille Pissarro", "The Banks of the Marne in Winter: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "81548", "Camille Pissarro", "Young Peasant Having Her Coffee: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "81551", "Camille Pissarro", "The Place du Havre, Paris: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "81552", "Camille Pissarro", "Woman and Child at the Well: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "87000", "Camille Pissarro", "Haymaking at Éragny: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "100191", "Claude Monet", "Stack of Wheat (Thaw, Sunset): selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "103139", "Claude Monet", "Waterloo Bridge, Gray Weather: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "111318", "Claude Monet", "Stack of Wheat: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "14598", "Claude Monet", "The Beach at Sainte-Adresse: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "14620", "Claude Monet", "Cliff Walk at Pourville: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "14624", "Claude Monet", "Stacks of Wheat (End of Day, Autumn): selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "14630", "Claude Monet", "Venice, Palazzo Dario: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "14634", "Claude Monet", "Vétheuil: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "16542", "Claude Monet", "The Customs House at Varengeville: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "16544", "Claude Monet", "Charing Cross Bridge, London: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "16549", "Claude Monet", "Apples and Grapes: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "16554", "Claude Monet", "The Artist's House at Argenteuil: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "16560", "Claude Monet", "Stack of Wheat (Snow Effect, Overcast Day): selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "16564", "Claude Monet", "Branch of the Seine near Giverny (Mist): selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "16568", "Claude Monet", "Water Lilies: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "16571", "Claude Monet", "Arrival of the Normandy Train, Gare Saint-Lazare: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "16579", "Claude Monet", "Vétheuil: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "20535", "Claude Monet", "Étretat: The Beach and the Falaise d'Amont: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "20545", "Claude Monet", "Rocks at Port-Goulphar, Belle-Île: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "20701", "Claude Monet", "Waterloo Bridge, Sunlight Effect: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "4783", "Claude Monet", "Poppy Field (Giverny): selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "4887", "Claude Monet", "Irises: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "59927", "Claude Monet", "Boats on the Beach at Étretat: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "64818", "Claude Monet", "Stacks of Wheat (End of Summer): selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "81537", "Claude Monet", "Bordighera: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "81539", "Claude Monet", "On the Bank of the Seine, Bennecourt: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "81540", "Claude Monet", "The Departure of the Boats, Étretat: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "81545", "Claude Monet", "Stacks of Wheat (Sunset, Snow Effect): selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "81546", "Claude Monet", "The Petite Creuse River: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "86998", "Claude Monet", "Sandvika, Norway: selected museum-held Impressionist painting; not an inferred masterpiece."},
	{"chicago", "97933", "Claude Monet", "Water Lily Pond: selected museum-held Impressionist painting; not an inferred masterpiece."},
}

func validateChicago(x coverageEntry) error {
	m := x.Raw
	id, ok := m["id"].(float64)
	first, fok := m["date_start"].(float64)
	last, lok := m["date_end"].(float64)
	ids, iok := m["artist_ids"].([]any)
	artistID, aok := m["artist_id"].(float64)
	imageID := str(m, "image_id")
	if !ok || strconv.Itoa(int(id)) != x.Candidate.Object || str(m, "title") != x.Candidate.Title || str(m, "main_reference_number") != x.Accession || str(m, "artist_title") != x.Candidate.Artist || !iok || len(ids) != 1 || !aok || ids[0] != artistID || !fok || !lok || first < 1100 || last > 1970 || first > last || str(m, "date_display") == "" || str(m, "artwork_type_title") != "Painting" {
		return fmt.Errorf("Chicago object/creator/date identity review")
	}
	if m["is_public_domain"] != true || str(m, "copyright_notice") != "" || !regexp.MustCompile(`^[a-f0-9-]{36}$`).MatchString(imageID) || str(m, "_iiif_base") != "https://www.artic.edu/iiif/2" || x.ImageURL != "https://www.artic.edu/iiif/2/"+imageID+"/full/843,/0/default.jpg" || x.Page != "https://www.artic.edu/artworks/"+x.Candidate.Object || x.ImagePage != x.Page || x.Policy != chicagoPolicy || x.Rights != "public_domain" || x.LicenseURL != "https://creativecommons.org/publicdomain/mark/1.0/" {
		return fmt.Errorf("Chicago primary image permission/URL review")
	}
	return nil
}

func stageChicago(ctx context.Context, p *pgxpool.Pool, out string) error {
	s := coverageSelection{Version: coverageVersion, Created: time.Now().UTC(), Entries: []coverageEntry{}, Deferred: []string{}}
	ids := []string{}
	for _, pick := range chicagoPicks {
		ids = append(ids, pick.Object)
	}
	if len(ids) == 0 || len(ids) > 50 {
		return fmt.Errorf("invalid bounded Chicago selection")
	}
	params := url.Values{"ids": {strings.Join(ids, ",")}, "limit": {"100"}, "fields": {"id,title,artist_id,artist_ids,artist_title,date_start,date_end,date_display,artwork_type_title,main_reference_number,is_public_domain,image_id,credit_line,copyright_notice"}}
	u := "https://api.artic.edu/api/v1/artworks?" + params.Encode()
	f := newFetcher()
	b, e := f.get(ctx, u, 2<<20)
	if e != nil {
		return e
	}
	at := time.Now().UTC()
	if e = save(filepath.Join(filepath.Dir(out), "chicago-selected-capture.json"), map[string]any{"url": u, "retrieved_at": at, "sha256": hash(b), "response": json.RawMessage(b)}); e != nil {
		return e
	}
	var response struct {
		Data   []map[string]any
		Config struct {
			IIIF string `json:"iiif_url"`
		}
	}
	if e = json.Unmarshal(b, &response); e != nil {
		return e
	}
	byID := map[string]map[string]any{}
	for _, m := range response.Data {
		n, ok := m["id"].(float64)
		if !ok {
			return fmt.Errorf("missing object ID")
		}
		id := strconv.Itoa(int(n))
		if byID[id] != nil {
			return fmt.Errorf("duplicate object")
		}
		m["_iiif_base"] = response.Config.IIIF
		byID[id] = m
	}
	for _, pick := range chicagoPicks {
		x, e := coverageCandidate(ctx, p, pick)
		if e != nil {
			return e
		}
		if x.Candidate.HasImage {
			continue
		}
		m := byID[pick.Object]
		if m == nil {
			s.Deferred = append(s.Deferred, pick.Object+": not returned by official API")
			continue
		}
		x.Raw = m
		x.Retrieved = at
		x.Provider = "Art Institute of Chicago"
		x.ImageURL = response.Config.IIIF + "/" + str(m, "image_id") + "/full/843,/0/default.jpg"
		x.ImagePage = x.Page
		x.Policy = chicagoPolicy
		x.Rights = "public_domain"
		x.License = "Public domain — Art Institute of Chicago"
		x.LicenseURL = "https://creativecommons.org/publicdomain/mark/1.0/"
		x.Credit = "Digital image courtesy of the Art Institute of Chicago. " + str(m, "credit_line")
		if e = validateCoverageEntry(x); e != nil {
			s.Deferred = append(s.Deferred, pick.Object+": "+e.Error())
			continue
		}
		s.Entries = append(s.Entries, x)
	}
	if e = save(out, s); e != nil {
		return e
	}
	fmt.Printf("Chicago staged %d images; %d deferred.\n", len(s.Entries), len(s.Deferred))
	return nil
}
