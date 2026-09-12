package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

type marmottanFact struct {
	URL          string   `json:"url"`
	Title        string   `json:"title"`
	Lines        []string `json:"lines"`
	ImageURL     string   `json:"image_url"`
	Canonical    string   `json:"canonical"`
	SnapshotFile string   `json:"snapshot_file"`
	Snapshot     snapshot `json:"snapshot"`
}

var marmottanBetween = regexp.MustCompile(`^(\d{4}) entre\s*;\s*(\d{4}) et$`)
var marmottanCirca = regexp.MustCompile(`^(\d{4}) vers$`)
var marmottanFrenchRange = regexp.MustCompile(`^entre (\d{4}) et (\d{4})$`)
var marmottanYears = regexp.MustCompile(`\b\d{4}\b`)

func marmottanDate(literal string) (creationDate, string, bool) {
	display := strings.TrimSpace(literal)
	if m := marmottanFrenchRange.FindStringSubmatch(display); m != nil {
		display = m[1] + "–" + m[2]
	}
	if m := marmottanBetween.FindStringSubmatch(display); m != nil {
		display = m[1] + "–" + m[2]
	}
	if m := marmottanCirca.FindStringSubmatch(display); m != nil {
		display = "vers " + m[1]
	}
	d, ok := normandyDate(display)
	return d, display, ok
}

func marmottanFields(f marmottanFact) (name, life, literal, medium, dimensions, accession, kind, reason string) {
	if len(f.Lines) < 5 || f.Title == "" || f.Lines[1] != f.Title {
		reason = "caption_layout_review"
		return
	}
	name = f.Lines[0]
	if i := strings.Index(name, " ("); i >= 0 {
		years := marmottanYears.FindAllString(name[i:], -1)
		if len(years) != 2 {
			reason = "creator_qualification_review"
			return
		}
		life = years[0] + "-" + years[1]
		name = name[:i]
	}
	if strings.ContainsAny(name, ";()") || normandyQualified.MatchString(name) {
		reason = "qualified_creator_review"
		return
	}
	literal = f.Lines[2]
	if !marmottanYears.MatchString(literal) {
		reason = "creation_date_missing"
		return
	}
	md := f.Lines[3]
	// Preserve source dimensions, including frame qualifiers; do not mix a
	// framed height with an unframed width or invent missing measurements.
	medium = md
	if i := strings.Index(md, " H."); i >= 0 {
		medium = strings.TrimSpace(md[:i])
		dimensions = strings.TrimSpace(md[i:])
	}
	if dimensions == "" {
		re := regexp.MustCompile(`\s+(\d+(?:[.,]\d+)?\s*[×x]\s*\d+(?:[.,]\d+)?\s*cm.*)$`)
		if m := re.FindStringSubmatchIndex(md); m != nil {
			medium = strings.TrimSpace(md[:m[0]])
			dimensions = strings.TrimSpace(md[m[0]:])
		}
	}
	m := strings.ToLower(medium)
	switch {
	case strings.Contains(m, "huile"):
		kind = "painting"
	case strings.Contains(m, "pastel"), strings.Contains(m, "aquarelle"), strings.Contains(m, "crayon"), strings.Contains(m, "fusain"), strings.Contains(m, "gouache"), strings.Contains(m, "mine de plomb"), strings.Contains(m, "sanguine"), strings.Contains(m, "encre"), strings.Contains(m, "lavis"), strings.Contains(m, "pierre noire"):
		kind = "drawing"
	case strings.Contains(m, "eau-forte"), strings.Contains(m, "lithograph"), strings.Contains(m, "monotype"), strings.Contains(m, "pointe sèche"):
		kind = "print"
	default:
		reason = "medium_review"
		return
	}
	accession = strings.TrimSuffix(strings.TrimPrefix(f.URL, "https://www.marmottan.fr/notice/"), "/")
	if !regexp.MustCompile(`^[A-Za-z0-9._-]+$`).MatchString(accession) {
		reason = "inventory_review"
		return
	}
	found := false
	for _, l := range f.Lines[4:] {
		if l == "inv. "+accession || strings.HasPrefix(l, "inv. "+accession+" ") {
			found = true
		}
		// This exact source notice joins its inventory and depositor label.
		if accession == "D.11-1993" && l == "inv. D.11-1993Fondation Ephrussi de Rothschild (déposant)" {
			found = true
		}
	}
	if !found {
		reason = "inventory_caption_mismatch"
	}
	if strings.Contains(strings.ToLower(f.Title), "carnet") {
		reason = "bound_volume_physical_unit_review"
	}
	return
}

func assemblePopularMarmottan(ctx context.Context, root, out string) error {
	return assemblePopularMarmottanPass(ctx, root, out, false)
}

func assemblePopularMarmottanPass(ctx context.Context, root, out string, deposits bool) error {
	index, err := localAuthors(ctx)
	if err != nil {
		return err
	} // validates local-only DB
	p, err := pgxpool.New(ctx, config.Load().DatabaseURL)
	if err != nil {
		return err
	}
	defer p.Close()
	rows, err := p.Query(ctx, `SELECT e.external_id FROM artist_discovery_selection d JOIN artists a ON a.id=d.artist_id JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artist' AND e.scheme='wikidata' WHERE d.is_popular AND a.status<>'archived'`)
	if err != nil {
		return err
	}
	popular := map[string]bool{}
	for rows.Next() {
		var q string
		if err = rows.Scan(&q); err != nil {
			return err
		}
		popular[q] = true
	}
	rows.Close()
	if err = rows.Err(); err != nil {
		return err
	}
	dir := filepath.Join(root, "content/imports/popular-marmottan-20260911")
	b, err := os.ReadFile(filepath.Join(dir, "popular-facts.json"))
	if err != nil {
		return err
	}
	var input struct{ Works []marmottanFact }
	if err = json.Unmarshal(b, &input); err != nil {
		return err
	}
	// The featured collection page exposes one Monet deposit omitted by the
	// public artist search. Keep its individually captured notice as evidence.
	b, err = os.ReadFile(filepath.Join(dir, "facts.json"))
	if err != nil {
		return err
	}
	var supplement struct{ Works []marmottanFact }
	if err = json.Unmarshal(b, &supplement); err != nil {
		return err
	}
	for _, f := range supplement.Works {
		if f.URL == "https://www.marmottan.fr/notice/D.11-1993/" {
			input.Works = append(input.Works, f)
		}
	}
	if len(input.Works) < 1 || len(input.Works) > 500 {
		return fmt.Errorf("invalid bounded facts")
	}
	source := "popular-marmottan"
	if deposits {
		source = "popular-marmottan-deposits"
	}
	s := newSelection(source)
	s.AccessedOn = "2026-09-11"
	key := source + "-museum"
	s.Museums[key] = map[string]string{"id": key, "name": "Musée Marmottan Monet", "city": "Paris", "country": "FR", "data_url": "https://www.marmottan.fr/collection-en-ligne/", "data_route": "Public artist search and individual museum notices; local factual review only", "rights": "No open image or authored-text license asserted. Factual catalogue labels and source links only.", "rights_url": "https://www.marmottan.fr/mentions-legales/"}
	s.Definitions[key] = map[string]string{"Slug": "musee-marmottan-monet", "Source": "popular-marmottan", "Website": "https://www.marmottan.fr", "Host": "www.marmottan.fr"}
	deferred := []map[string]any{}
	seen := map[string]bool{}
	for _, f := range input.Works {
		if deposits && f.URL != "https://www.marmottan.fr/notice/D.2018.1.12/" && f.URL != "https://www.marmottan.fr/notice/D.2018.1.14/" {
			continue
		}
		s.Decisions["examined"]++
		// Non-featured notices publish a generic /notice/ canonical. Their
		// requested inventory URL and independently printed inv. caption must
		// agree; never use that generic canonical to merge different objects.
		if seen[f.URL] || (f.Canonical != f.URL && f.Canonical != "https://www.marmottan.fr/notice/") || f.Snapshot.URL != f.URL || filepath.Base(f.SnapshotFile) != f.SnapshotFile || f.Snapshot.Retrieved.Format("2006-01-02") != "2026-09-11" {
			return fmt.Errorf("source identity mismatch: %s", f.URL)
		}
		seen[f.URL] = true
		path := filepath.Join(dir, f.SnapshotFile)
		if err = verify(path); err != nil {
			return err
		}
		h, n, err := hashFile(path)
		if err != nil || h != f.Snapshot.SHA || n != f.Snapshot.Bytes {
			return fmt.Errorf("capture mismatch")
		}
		name, life, literal, medium, dimensions, accession, kind, reason := marmottanFields(f)
		// These exact notices omit the separator between inventory and depositor.
		if deposits && reason == "inventory_caption_mismatch" {
			for _, line := range f.Lines {
				if line == "inv. "+accession+"Fondation Ephrussi de Rothschild (déposant)" {
					reason = ""
				}
			}
		}
		a, matched := matchAuthor(index, name, life)
		d, display, dated := marmottanDate(literal)
		if reason == "" && (!matched || !popular[a.QID]) {
			reason = "popular_authority_or_lifespan_review"
		}
		if reason == "" && (!dated || creatorDateConflict(a, d, kind)) {
			reason = "creation_date_review"
		}
		// Inscription dates are a contradiction flag, not replacement dating.
		if accession == "5390" {
			reason = "caption_1956_inscription_1956_7_review"
		}
		if reason != "" {
			s.Decisions[reason]++
			imageState := "image URL in notice; reuse permission not established; not downloaded"
			if f.ImageURL == "" || strings.Contains(f.ImageURL, "no-picture.png") {
				imageState = "no artwork image supplied by notice"
			}
			deferred = append(deferred, map[string]any{"url": f.URL, "title": f.Title, "reason": reason, "source_lines": f.Lines, "image_url": f.ImageURL, "image_state": imageState})
			continue
		}
		s.addAuthor(name, life, a)
		desc := fmt.Sprintf("%s — %s. %s.\n\nMedium: %s. Dimensions: %s.\n\nMuseum collection record: Musée Marmottan Monet, Paris; inventory %s. Holding connection according to the museum notice, not an ownership or current-display assertion.\n\nSource: [museum object notice](%s), accessed 11 September 2026. Factual labels only; photograph and authored commentary reuse require separate permission.", f.Title, a.Name, display, medium, dimensions, accession, f.URL)
		if strings.Contains(strings.Join(f.Lines, " "), "déposant") {
			desc += "\n\nThe notice identifies a depositor; museum holding must not be read as ownership."
		}
		s.Works = append(s.Works, map[string]any{"painter": a.QID, "title": f.Title, "institution": key, "accession": accession, "url": f.URL, "source_object_id": accession, "source_publisher": "Musée Marmottan Monet", "date_display": display, "creation_date": d, "attribution_role": "primary", "work_type": kind, "medium": medium, "dimensions": dimensions, "description_md": desc, "notes": "Source date literal: " + literal + ". Selected from popular-artist museum searches, not an inferred masterpiece.", "source_raw": f})
	}
	if err = save(filepath.Join(out, "deferred.json"), deferred); err != nil {
		return err
	}
	return s.write(out)
}
