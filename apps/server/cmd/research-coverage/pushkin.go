package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

// Reviewed bilingual names, not positional author keys in the legacy JSON.
var pushkinPainters = map[string]string{
	"Henri Rousseau": "Q156386", "Paul Cézanne": "Q35548", "Paul Signac": "Q151573", "Toulouse-Lautrec, Henri Marie Raymond de": "Q82445", "Edouard Manet": "Q40599", "Henri Matisse": "Q5589", "Claude Monet": "Q296", "Camille Pissarro": "Q134741", "Pierre Puvis de Chavannes": "Q216873", "Pierre-Auguste Renoir": "Q39931", "Bastien-Lepage, Jules": "Q541859", "Bonnard, Pierre": "Q26408", "Paul Gauguin": "Q37693", "Edgar Degas": "Q46373", "André Derain": "Q156272", "Eugène Carrière": "Q461464", "Jean-Baptiste-Camille Corot": "Q148475", "Gustave Courbet": "Q34618", "Jean-François Millet": "Q148458", "JEAN-BAPTISTE SIMEON CHARDIN": "Q207447", "ANTOINE JEAN GROS": "Q216999", "Lorrain, Claude [Gellee, Claude]": "Q214074", "NICOLAS POUSSIN": "Q41554", "JEAN- BAPTISTE GREUZE": "Q347139", "François Boucher": "Q180932", "Watteau, Antoine": "Q183221", "Daumier, Honoré": "Q187506", "Lucas Cranach the Elder": "Q191748", "Vincent van Gogh": "Q5582", "RÉMBRÁNDT Hármenszoon Van Rijn": "Q5598", "Hendrick Barents Avercamp (De Stomme van Campen)": "Q212593", "Caspar David Friedrich": "Q104884", "Böcklin, Arnold": "Q123071", "Петер Пауль Рубенс": "Q5599", "Pablo Picasso": "Q5593", "Боттичелли": "Q5669", "Agnolo Bronzino": "Q7803", "Джованни Антонио Каналь (Каналетто)": "Q182664", "Сурбаран, Франсиско де": "Q209615", "Антонис ван Дейк": "Q150679", "Родченко Александр Михайлович": "Q312631",
}

func localized(v any) string {
	m, _ := v.(map[string]any)
	en, _ := m["en"].(string)
	if en != "" {
		return strings.TrimSpace(en)
	}
	ru, _ := m["ru"].(string)
	return strings.TrimSpace(ru)
}
func pushkinDate(id, display string) (creationDate, bool) {
	s := strings.TrimSpace(display)
	s = strings.NewReplacer("Около ", "circa ", "Circa ", "circa ", "–", "-").Replace(s)
	// Source precision explicitly reviewed, including month-level dates and full
	// decade envelopes. Ambiguous later reworking / open-ended dates stay out.
	switch id {
	case "4291":
		return creationDate{1890, 1899, "decade"}, true
	case "4350":
		return creationDate{1850, 1859, "decade"}, true
	case "5913":
		return creationDate{1810, 1819, "decade"}, true
	case "5297":
		return creationDate{1890, 1890, "exact"}, true
	case "5347":
		return creationDate{1888, 1888, "exact"}, true
	case "7151":
		return creationDate{1638, 1639, "range"}, true
	case "6632":
		return creationDate{1540, 1549, "decade"}, true // English early1540s vs Russian circa1540: conservative envelope.
	}
	m := literalDate.FindStringSubmatch(s)
	if m == nil {
		return creationDate{}, false
	}
	a, _ := strconv.Atoi(m[2])
	z := a
	p := "exact"
	if m[3] != "" {
		z, _ = strconv.Atoi(m[3])
		if len(m[3]) == 2 {
			z += a / 100 * 100
		}
		p = "range"
	}
	if m[1] != "" {
		if p == "range" {
			p = "circa_range"
		} else {
			p = "circa"
		}
	}
	return creationDate{a, z, p}, a >= 1100 && z >= a && z <= 1970 && !(z == 1970 && strings.HasPrefix(p, "circa"))
}
func assemblePushkin(root, out string) error {
	path := filepath.Join(root, "content/imports/pushkin-20260909/masterpieces.json")
	if e := verify(path); e != nil {
		return e
	}
	b, e := os.ReadFile(path)
	if e != nil {
		return e
	}
	var data map[string]map[string]any
	if e = json.Unmarshal(b, &data); e != nil {
		return e
	}
	ids := []string{}
	for id := range data {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	works := []any{}
	deferred := []any{}
	painters := map[string]string{}
	for _, id := range ids {
		r := data[id]
		if localized(r["type"]) != "Painting" {
			continue
		}
		authors, ok := r["authors"].(map[string]any)
		if !ok || len(authors) != 1 {
			deferred = append(deferred, map[string]any{"id": id, "reason": "creator_count"})
			continue
		}
		name := ""
		for _, a := range authors {
			name = localized(a)
		}
		q := pushkinPainters[name]
		period, _ := r["period"].(map[string]any)
		display := localized(period["text"])
		d, valid := pushkinDate(id, display)
		if q == "" || !valid {
			deferred = append(deferred, map[string]any{"id": id, "title": localized(r["name"]), "creator": name, "date": display, "reason": "identity_or_creation_date_review"})
			continue
		}
		title := localized(r["name"])
		path, _ := r["path"].(string)
		if !regexp.MustCompile(`^data/fonds/[a-zA-Z0-9_/-]+/index\.php$`).MatchString(path) {
			return fmt.Errorf("unexpected Pushkin source path")
		}
		url := "https://pushkinmuseum.art/" + path
		acc, _ := r["inv_num"].(string)
		medium := localized(r["material"])
		dimensions := localized(r["size"])
		// Deliberately omit copyrighted narrative, annotation and image binaries.
		fact := map[string]any{"id": id, "path": path, "title": r["name"], "creator_names": authors, "period": period, "year_search_value": r["year"], "accession": acc, "medium": r["material"], "dimensions": r["size"], "masterpiece": r["masterpiece"], "source": "https://pushkinmuseum.art/json/masterpieces.json"}
		painters[q] = q
		works = append(works, map[string]any{"painter": q, "title": title, "institution": "pushkin", "accession": acc, "url": url, "source_object_id": id, "source_publisher": "Pushkin State Museum of Fine Arts", "date_display": display, "creation_date": d, "attribution_role": "primary", "work_type": "painting", "medium": medium, "dimensions": dimensions, "museum_highlight_url": "https://pushkinmuseum.art/json/masterpieces.json", "description_md": fmt.Sprintf("%s — %s. %s.\n\nMedium: %s. Dimensions: %s.\n\nPushkin State Museum of Fine Arts, Moscow. Inventory %s. Included in the museum's highlights feed; current display is unverified.\n\nSource: [Pushkin Museum](%s), factual collection metadata retrieved 9 September 2026. Museum narrative and photographs are not reproduced.", title, name, display, medium, dimensions, acc, url), "notes": "Museum-authored highlights feed. Literal creation date takes precedence over numeric search year. Authored text and photographs omitted. Positional author keys are not authority IDs.", "source_raw": fact})
	}
	manifest := map[string]any{"schema_version": 2, "accessed_on": "2026-09-09", "painters": painters, "definitions": map[string]any{"pushkin": map[string]string{"Slug": "pushkin-state-museum-fine-arts", "Source": "pushkin-open-highlights", "Website": "https://pushkinmuseum.art", "Host": "pushkinmuseum.art"}}, "institutions": []any{map[string]string{"id": "pushkin", "name": "Pushkin State Museum of Fine Arts", "city": "Moscow", "country": "RU", "data_url": "https://pushkinmuseum.art/open_data/index.php?lang=ru", "data_route": "Documented legacy highlights JSON; stable source object IDs, not full KAMIS catalogue", "rights": "Open factual metadata. Authored narrative and images subject to separate museum terms; no reuse permission inferred.", "rights_url": "https://pushkinmuseum.art/usage_policy/index.php?lang=ru"}}, "works": works}
	if e = save(filepath.Join(out, "inventory.json"), manifest); e != nil {
		return e
	}
	if e = save(filepath.Join(out, "deferred.json"), deferred); e != nil {
		return e
	}
	sha, n, e := hashFile(filepath.Join(out, "inventory.json"))
	if e != nil {
		return e
	}
	return save(filepath.Join(out, "summary.json"), map[string]any{"source_objects": len(data), "source_paintings": 55, "selected": len(works), "painters": len(painters), "deferred": len(deferred), "sha256": sha, "bytes": n})
}
