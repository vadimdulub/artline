package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
)

func objectMap(v any) map[string]any          { m, _ := v.(map[string]any); return m }
func field(m map[string]any, k string) string { s, _ := m[k].(string); return strings.TrimSpace(s) }

var russianCentury = regexp.MustCompile(`^(?:(первая половина|вторая половина|начало|конец|середина) )?(XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX) (?:века|век|в\.)$`)

func kamisDate(r map[string]any) (creationDate, bool) {
	s := field(r, "create_date4")
	s = strings.TrimSpace(strings.TrimSuffix(s, " г."))
	s = strings.NewReplacer("Около ", "circa ", "около ", "circa ", "–", "-").Replace(s)
	if m := literalDate.FindStringSubmatch(s); m != nil {
		a, _ := strconv.Atoi(m[2])
		b := a
		if m[3] != "" {
			b, _ = strconv.Atoi(m[3])
			if len(m[3]) == 2 {
				b += a / 100 * 100
			}
		}
		d := creationDate{a, b, "exact"}
		if a != b {
			d.Precision = "range"
		}
		if m[1] != "" {
			d.Precision = "circa"
			if a != b {
				d.Precision = "circa_range"
			}
		}
		n1, e1 := strconv.Atoi(field(r, "create_date1"))
		n2, e2 := strconv.Atoi(field(r, "create_date2"))
		return d, dateEligible(d) && e1 == nil && e2 == nil && a == n1 && b == n2
	}
	if m := russianCentury.FindStringSubmatch(s); m != nil {
		c := map[string]int{"XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20}[m[2]]
		d := creationDate{(c - 1) * 100, c * 100, "century"}
		if m[1] == "первая половина" {
			d.Last = d.First + 50
			d.Precision = "range"
		}
		if m[1] == "вторая половина" {
			d.First += 50
			d.Precision = "range"
		}
		n1, e1 := strconv.Atoi(field(r, "create_date1"))
		n2, e2 := strconv.Atoi(field(r, "create_date2"))
		return d, dateEligible(d) && e1 == nil && e2 == nil && n1 >= d.First && n2 <= d.Last && n2 >= n1
	}
	return creationDate{}, false
}
func assembleKamis(ctx context.Context, root, out string) error {
	input := filepath.Join(root, "content/imports/pushkin-kamis-20260910")
	b, e := os.ReadFile(filepath.Join(input, "manifest.json"))
	if e != nil {
		return e
	}
	var manifest struct {
		Complete       bool
		Pages, Objects int
	}
	if e = json.Unmarshal(b, &manifest); e != nil || !manifest.Complete || manifest.Pages != 35 || manifest.Objects != 1729 {
		return fmt.Errorf("unreviewed/incomplete KAMIS capture")
	}
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	s := newSelection("pushkin-kamis")
	const key = "pushkin-kamis"
	s.Museums[key] = map[string]string{"id": key, "name": "Pushkin State Museum of Fine Arts", "city": "Moscow", "country": "RU", "data_url": "https://collection.pushkinmuseum.art/about", "data_route": "Museum frontend-backed search JSON; fund13; exact accession reconciliation with legacy highlights", "rights": "Factual metadata for local research; no blanket open licence asserted for KAMIS. Protected narrative and images omitted.", "rights_url": "https://pushkinmuseum.art/usage_policy/index.php?lang=ru"}
	s.Definitions[key] = map[string]string{"Slug": "pushkin-state-museum-fine-arts", "Source": "pushkin-kamis-catalogue", "Website": "https://pushkinmuseum.art", "Host": "collection.pushkinmuseum.art"}
	for p := 0; p < manifest.Pages; p++ {
		path := filepath.Join(input, fmt.Sprintf("page-%03d.json", p))
		if e = verify(path); e != nil {
			return e
		}
		b, e = os.ReadFile(path)
		if e != nil {
			return e
		}
		var page struct{ Data []map[string]any }
		if e = json.Unmarshal(b, &page); e != nil {
			return e
		}
		for _, obj := range page.Data {
			s.Decisions["candidates"]++
			raw := objectMap(obj["rawData"])
			ru, en := objectMap(raw["ru"]), objectMap(raw["en"])
			d, ok := kamisDate(ru)
			if !ok {
				s.Decisions["creation_date_review"]++
				continue
			}
			if obj["deleted"] == true {
				s.Decisions["deleted"]++
				continue
			}
			author := objectMap(objectMap(ru["author"])["entity"])
			authorEN := objectMap(objectMap(en["author"])["entity"])
			if field(author, "code") == "" {
				s.Decisions["multiple_or_missing_creator"]++
				continue
			}
			rn := strings.TrimSpace(strings.TrimSuffix(field(author, "name"), "(автор)"))
			if strings.ContainsAny(rn, "()?") {
				s.Decisions["qualified_creator"]++
				continue
			}
			name := field(authorEN, "name")
			a, ok := matchAuthor(index, name, "")
			if !ok {
				a, ok = matchAuthor(index, rn, "")
			}
			if !ok {
				s.Decisions["authority_review"]++
				continue
			}
			if creatorDateConflict(a, d, "painting") {
				s.Decisions["creator_creation_conflict"]++
				continue
			}
			id := field(obj, "id")
			acc := field(ru, "record_id")
			if acc == "" {
				s.Decisions["accession_review"]++
				continue
			}
			title := field(en, "object_title")
			if title == "" {
				title = field(ru, "name_original")
			}
			if title == "" {
				title = field(ru, "object_title")
			}
			title = strings.TrimSpace(strings.TrimPrefix(title, "Картина."))
			if title == "" {
				s.Decisions["title_review"]++
				continue
			}
			medium := field(en, "material_techniq")
			if medium == "" {
				medium = strings.TrimSpace(field(ru, "material") + "; " + field(ru, "techniq"))
			}
			display := field(ru, "create_date4")
			url := "https://collection.pushkinmuseum.art/entity/OBJECT/" + id
			facts := map[string]any{"id": id, "accession": acc, "inventory": field(ru, "invnom"), "registration": field(ru, "nomkp"), "author": author, "author_en": authorEN, "title": title, "literal_date": display, "numeric_first": field(ru, "create_date1"), "numeric_last": field(ru, "create_date2"), "medium": medium, "dimensions": field(ru, "dimensions"), "fund": ru["fund"]}
			desc := fmt.Sprintf("%s — %s. %s.\n\nMedium: %s. Dimensions: %s.\n\nPushkin State Museum of Fine Arts, Moscow. Inventory %s. Collection holding; current display unverified.\n\nSource: [Pushkin electronic catalogue](%s), factual metadata retrieved 10 September 2026. Authored narrative and photographs are not reproduced.", title, a.Name, display, medium, field(ru, "dimensions"), acc, url)
			s.addAuthor(name+" / "+rn, "", a)
			s.Works = append(s.Works, map[string]any{"painter": a.QID, "title": title, "institution": key, "accession": acc, "url": url, "source_object_id": id, "source_publisher": "Pushkin State Museum of Fine Arts", "date_display": display, "creation_date": d, "attribution_role": "primary", "work_type": "painting", "medium": medium, "dimensions": field(ru, "dimensions"), "description_md": desc, "notes": "Literal creation evidence, not acquisition or creator lifespan. Century-qualified dates use a conservative displayed-period envelope; narrower source search years are retained separately. Historical exhibition entries do not establish present display.", "source_raw": facts})
		}
	}
	return s.write(out)
}
