package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type Artist struct {
	ID, Name, Slug, Status, Fingerprint              string
	Countries                                        []string
	Works, Pictures, VerifiedImages, CompletedRounds int
	RoundDone                                        [10]bool
}
type Credit struct{ ID, Role string }
type Work struct {
	ID, Title, Date, Scope, Institution, Accession, Source, Fingerprint string
	Credits                                                             []Credit
	Image, Checksum, Rights, License                                    string
	Bytes                                                               int64
	Evidence                                                            bool
	ImageCheck                                                          string
	UnlinkedCreator, Culture, Form                                      string
}
type Decision struct {
	Kind, ID, Fingerprint, Status, ImageOutcome, Note string
	Round                                             int
	CheckedAt                                         time.Time
	Sources                                           []string
}
type Decisions map[string]Decision

func decisionKey(kind, id string, round int) string { return fmt.Sprintf("%s:%s:%d", kind, id, round) }
func readDecisions(path string) (Decisions, error) {
	out := Decisions{}
	if path == "" {
		return out, nil
	}
	b, e := os.ReadFile(path)
	if e != nil {
		return nil, e
	}
	var list []Decision
	if e = json.Unmarshal(b, &list); e != nil {
		return nil, e
	}
	for _, d := range list {
		if (d.Kind != "artist" && d.Kind != "artwork") || d.ID == "" || d.Fingerprint == "" || d.Round < 1 || d.Round > 10 || d.Note == "" || d.CheckedAt.IsZero() || d.CheckedAt.After(time.Now().Add(5*time.Minute)) || len(d.Sources) == 0 {
			return nil, fmt.Errorf("invalid explicit review decision")
		}
		if d.Status != "done" && d.Status != "blocked" && d.Status != "in_progress" {
			return nil, fmt.Errorf("invalid review status")
		}
		if d.Kind == "artwork" && d.Status == "done" && d.ImageOutcome != "verified" && d.ImageOutcome != "unavailable" {
			return nil, fmt.Errorf("completed artwork review needs a documented image outcome")
		}
		for _, s := range d.Sources {
			u, e := url.Parse(s)
			if e != nil || u.Scheme != "https" || u.Host == "" || u.User != nil {
				return nil, fmt.Errorf("invalid evidence URL")
			}
		}
		k := decisionKey(d.Kind, d.ID, d.Round)
		if _, exists := out[k]; exists {
			return nil, fmt.Errorf("duplicate review decision")
		}
		out[k] = d
	}
	return out, nil
}
func state(ds Decisions, kind, id, fp string, round int) string {
	d, ok := ds[decisionKey(kind, id, round)]
	if !ok {
		return "pending"
	}
	if d.Fingerprint != fp {
		return "stale — changed record"
	}
	return d.Status
}
func md(s string) string {
	return strings.NewReplacer("&", "&amp;", "<", "&lt;", ">", "&gt;", "|", "&#124;", "[", "&#91;", "]", "&#93;", "\r", " ", "\n", " ", "`", "&#96;").Replace(s)
}
func link(label, target string) string {
	u, e := url.Parse(target)
	if e != nil || u.Scheme != "https" || u.Host == "" || u.User != nil {
		return "No verified source link"
	}
	return "[" + md(label) + "](<" + strings.ReplaceAll(target, ">", "%3E") + ">)"
}
func imageCheck(root string, w Work) string {
	if w.Image == "" {
		return "missing"
	}
	if !strings.HasPrefix(w.Image, "/assets/artworks/") || strings.Contains(w.Image, "..") {
		return "present — nonlocal or unsafe path"
	}
	path := filepath.Join(root, "apps/web/public", w.Image)
	info, e := os.Lstat(path)
	if e != nil || !info.Mode().IsRegular() {
		return "present — file unavailable"
	}
	if info.Size() > 100000 {
		return "present — exceeds 100 KB"
	}
	b, e := os.ReadFile(path)
	if e != nil || int64(len(b)) != w.Bytes || digest(b) != w.Checksum {
		return "present — checksum/size mismatch"
	}
	if !w.Evidence || w.License == "" || w.Rights == "restricted" || w.Rights == "unknown" {
		return "present — rights evidence needs review"
	}
	return "file verified; identity review tracked separately"
}

// This is one offline catalogue traversal, never a public endpoint. PostgreSQL
// streams rows grouped by artist. Memory retains at most one painter's works,
// artist headers and the distinct UUID set, not 105k detailed records in a browser.
const ledgerWorksSQL = `WITH credits AS (
 SELECT artwork_id,jsonb_agg(jsonb_build_object('ID',artist_id,'Role',attribution_role) ORDER BY artist_id) AS people,
 md5(string_agg(to_jsonb(aa)::text,'' ORDER BY artist_id)) AS fp FROM artwork_artists aa GROUP BY artwork_id
), ids AS (
 SELECT entity_id,min(canonical_url) AS url,md5(string_agg(to_jsonb(e)::text,'' ORDER BY scheme,external_id)) AS fp
 FROM external_identifiers e WHERE entity_type='artwork' GROUP BY entity_id
), rights AS (SELECT media_id,count(*)>0 AS documented FROM media_rights_evidence GROUP BY media_id)
SELECT coalesce(aa.artist_id::text,''),jsonb_build_object(
 'ID',a.id,'Title',a.title,'Date',a.date_display,'Scope',artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision),
 'Institution',coalesce(i.name,a.current_location_text,''),'Accession',coalesce(a.accession_number,''),'Source',coalesce(ids.url,''),
 'Credits',coalesce(c.people,'[]'),'Fingerprint',md5(to_jsonb(a)::text||coalesce(to_jsonb(m)::text,'')||coalesce(c.fp,'')||coalesce(ids.fp,'')),
 'Image',coalesce(m.storage_path,''),'Checksum',coalesce(m.checksum_sha256,''),'Rights',coalesce(m.rights_status,''),'License',coalesce(m.license_label,''),
 'Bytes',coalesce(m.byte_size,0),'Evidence',coalesce(r.documented,false),'UnlinkedCreator',coalesce(a.unlinked_creator_label,''),'Culture',coalesce(a.cultural_context,''),'Form',coalesce(a.object_form,''))
FROM artworks a LEFT JOIN artwork_artists aa ON aa.artwork_id=a.id LEFT JOIN credits c ON c.artwork_id=a.id LEFT JOIN ids ON ids.entity_id=a.id
LEFT JOIN institutions i ON i.id=a.current_institution_id LEFT JOIN media_assets m ON m.id=a.primary_media_id LEFT JOIN rights r ON r.media_id=m.id
ORDER BY coalesce(aa.artist_id::text,''),a.id`

func exportLedger(ctx context.Context, p *pgxpool.Pool, root, out, decisionFile string) error {
	ds, e := readDecisions(decisionFile)
	if e != nil {
		return e
	}
	if e = newSnapshot(out); e != nil {
		return e
	}
	if e = os.Mkdir(filepath.Join(out, "painters"), 0755); e != nil {
		return e
	}
	tx, e := p.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if e != nil {
		return e
	}
	defer tx.Rollback(ctx)
	rows, e := tx.Query(ctx, `SELECT jsonb_build_object('ID',a.id,'Name',a.display_name,'Slug',a.slug,'Status',a.status,'Fingerprint',md5(to_jsonb(a)::text||coalesce((SELECT string_agg(to_jsonb(ac)::text,'' ORDER BY ac.country_code,ac.relationship_type) FROM artist_countries ac WHERE ac.artist_id=a.id),'')),'Countries',coalesce((SELECT jsonb_agg(DISTINCT country_code) FROM artist_countries WHERE artist_id=a.id),'[]')) FROM artists a ORDER BY a.display_name,a.id`)
	if e != nil {
		return e
	}
	artists := []*Artist{}
	byID := map[string]*Artist{}
	for rows.Next() {
		var b []byte
		if e = rows.Scan(&b); e != nil {
			return e
		}
		var a Artist
		if e = json.Unmarshal(b, &a); e != nil {
			return e
		}
		artists = append(artists, &a)
		byID[a.ID] = &a
	}
	rows.Close()
	if e = rows.Err(); e != nil {
		return e
	}
	inventory, e := os.OpenFile(filepath.Join(out, "artworks.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	defer inventory.Close()
	enc := json.NewEncoder(inventory)
	seen := map[string]bool{}
	imageResults := map[string]string{}
	counts := map[string]int{"artists": len(artists)}
	var workReviews [10]int
	seenArtist := map[string]bool{}
	flush := func(id string, works []Work) error {
		if id == "" {
			if len(works) == 0 {
				return nil
			}
			return save(filepath.Join(out, "UNLINKED_ARTWORKS.md"), []byte(renderWorks("Unlinked and anonymous creators", works, ds)))
		}
		a := byID[id]
		if a == nil {
			return fmt.Errorf("missing linked artist %s", id)
		}
		seenArtist[id] = true
		a.Works = len(works)
		parts := a.Fingerprint
		for _, w := range works {
			parts += w.ID + ":" + w.Fingerprint
			if w.Image != "" {
				a.Pictures++
			}
			if strings.HasPrefix(w.ImageCheck, "file verified") {
				a.VerifiedImages++
			}
		}
		a.Fingerprint = digest([]byte(parts))
		var b strings.Builder
		fmt.Fprintf(&b, "# %s\n\nArtist ID: `%s` · Catalogue status: %s · Country links: %s\n\n%d artworks; %d images present; %d file/rights-evidence checks passed.\n\nReview fingerprint: `%s`\n\n## Ten research rounds\n\n", md(a.Name), a.ID, a.Status, md(strings.Join(a.Countries, ", ")), a.Works, a.Pictures, a.VerifiedImages, a.Fingerprint)
		for round := 1; round <= 10; round++ {
			s := state(ds, "artist", a.ID, a.Fingerprint, round)
			if s == "done" {
				for _, w := range works {
					if state(ds, "artwork", w.ID, w.Fingerprint, round) != "done" {
						s = "in_progress — artwork reviews remain"
						break
					}
				}
			}
			check := " "
			if s == "done" {
				check = "x"
				a.CompletedRounds++
				a.RoundDone[round-1] = true
			}
			fmt.Fprintf(&b, "- [%s] Round %02d: %s\n", check, round, s)
			if d, ok := ds[decisionKey("artist", a.ID, round)]; ok {
				fmt.Fprintf(&b, "  - %s Checked %s.\n", md(d.Note), d.CheckedAt.Format(time.RFC3339))
				for _, src := range d.Sources {
					fmt.Fprintf(&b, "  - %s\n", link("Evidence", src))
				}
			}
		}
		b.WriteString("\n" + renderWorks("Artwork checklist", works, ds))
		return save(filepath.Join(out, "painters", a.ID+".md"), []byte(b.String()))
	}
	rows, e = tx.Query(ctx, ledgerWorksSQL)
	if e != nil {
		return e
	}
	id := ""
	group := []Work{}
	for rows.Next() {
		var next string
		var b []byte
		if e = rows.Scan(&next, &b); e != nil {
			return e
		}
		var w Work
		if e = json.Unmarshal(b, &w); e != nil {
			return e
		}
		if next != id {
			if e = flush(id, group); e != nil {
				return e
			}
			id = next
			group = nil
		}
		if !seen[w.ID] {
			w.ImageCheck = imageCheck(root, w)
			imageResults[w.ID] = w.ImageCheck
			seen[w.ID] = true
			counts["artworks"]++
			for round := 1; round <= 10; round++ {
				if state(ds, "artwork", w.ID, w.Fingerprint, round) == "done" {
					workReviews[round-1]++
				}
			}
			if w.Image != "" {
				counts["images_present"]++
			}
			if strings.HasPrefix(w.ImageCheck, "file verified") {
				counts["images_file_verified"]++
			}
			if len(w.Credits) == 0 {
				counts["unlinked_artworks"]++
			}
			if e = enc.Encode(w); e != nil {
				return e
			}
		} else {
			w.ImageCheck = imageResults[w.ID]
		}
		group = append(group, w)
	}
	rows.Close()
	if e = rows.Err(); e != nil {
		return e
	}
	if e = flush(id, group); e != nil {
		return e
	}
	for _, a := range artists {
		if !seenArtist[a.ID] {
			if e = flush(a.ID, nil); e != nil {
				return e
			}
			counts["artists_without_artworks"]++
		}
	}
	var expectedWorks, expectedArtists int
	if e = tx.QueryRow(ctx, `SELECT (SELECT count(*) FROM artworks),(SELECT count(*) FROM artists)`).Scan(&expectedWorks, &expectedArtists); e != nil {
		return e
	}
	if counts["artworks"] != expectedWorks || counts["artists"] != expectedArtists {
		return fmt.Errorf("incomplete inventory")
	}
	if e = tx.Commit(ctx); e != nil {
		return e
	}
	if e = inventory.Close(); e != nil {
		return e
	}
	var index strings.Builder
	fmt.Fprintf(&index, "# Painter and artwork review index\n\nSnapshot: %s. **%d painters; %d distinct artworks.**\n\nTen full research rounds requested. Automated inventory and file checks do not count as painter/artwork research. Checkmarks are explicit, evidence-backed decisions for the exact record fingerprint; edits reopen reviews. An unavailable image can have a completed research decision but is never marked downloaded. Catalogue publication is independent.\n\n[Unlinked/anonymous artworks](UNLINKED_ARTWORKS.md) · [Machine-readable artwork inventory](artworks.jsonl)\n\n## Full-catalogue rounds\n\n", time.Now().UTC().Format(time.RFC3339), expectedArtists, expectedWorks)
	for round := 1; round <= 10; round++ {
		done := 0
		for _, a := range artists {
			if a.RoundDone[round-1] {
				done++
			}
		}
		check, completion := " ", "full round not complete"
		if done == expectedArtists && workReviews[round-1] == expectedWorks {
			check, completion = "x", "complete for this snapshot"
		}
		fmt.Fprintf(&index, "- [%s] Round %02d: %d/%d painters; %d/%d artworks reviewed; %s.\n", check, round, done, expectedArtists, workReviews[round-1], expectedWorks, completion)
	}
	index.WriteString("\n## Every painter\n\n| Painter | Countries | Artworks | Images | Research rounds done |\n|---|---|---:|---:|---:|\n")
	for _, a := range artists {
		fmt.Fprintf(&index, "| [%s](painters/%s.md) | %s | %d | %d | %d/10 |\n", md(a.Name), a.ID, md(strings.Join(a.Countries, ", ")), a.Works, a.Pictures, a.CompletedRounds)
	}
	if e = save(filepath.Join(out, "PAINTERS.md"), []byte(index.String())); e != nil {
		return e
	}
	if counts["unlinked_artworks"] == 0 {
		if e = save(filepath.Join(out, "UNLINKED_ARTWORKS.md"), []byte("# Unlinked artworks\n\nNone in this snapshot.\n")); e != nil {
			return e
		}
	}
	if e = save(filepath.Join(out, "artists.json"), append(encode(artists), '\n')); e != nil {
		return e
	}
	if e = save(filepath.Join(out, "summary.json"), append(encode(map[string]any{"created_at": time.Now().UTC(), "counts": counts, "requested_rounds": 10, "decision_file": decisionFile, "database_writes": false}), '\n')); e != nil {
		return e
	}
	fmt.Println(string(encode(counts)))
	return nil
}

func renderWorks(title string, works []Work, ds Decisions) string {
	var b strings.Builder
	fmt.Fprintf(&b, "## %s\n\n", title)
	if len(works) == 0 {
		return b.String() + "No artworks recorded. Research is still pending; an empty list is not a finished painter.\n"
	}
	sort.Slice(works, func(i, j int) bool { return works[i].ID < works[j].ID })
	for _, w := range works {
		fmt.Fprintf(&b, "### %s\n\n- Artwork ID: `%s`\n- Date: %s; cutoff: %s\n- Holding record: %s; accession: %s. Not a current-display claim.\n- %s\n- Attribution: ", md(w.Title), w.ID, md(w.Date), w.Scope, md(w.Institution), md(w.Accession), link("Catalogue source", w.Source))
		for _, c := range w.Credits {
			fmt.Fprintf(&b, "`%s` (%s) ", c.ID, md(c.Role))
		}
		if w.UnlinkedCreator != "" {
			b.WriteString(md(w.UnlinkedCreator))
		}
		b.WriteString("\n")
		if w.Culture != "" || w.Form != "" {
			fmt.Fprintf(&b, "- Cultural context/form: %s / %s\n", md(w.Culture), md(w.Form))
		}
		check := " "
		if strings.HasPrefix(w.ImageCheck, "file verified") {
			check = "x"
		}
		fmt.Fprintf(&b, "- [%s] Image file: %s", check, md(w.ImageCheck))
		if w.Image != "" {
			fmt.Fprintf(&b, "; `%s`; %d bytes; %s", md(w.Image), w.Bytes, md(w.License))
		}
		b.WriteString("\n")
		fmt.Fprintf(&b, "- Review fingerprint: `%s`\n", w.Fingerprint)
		for round := 1; round <= 10; round++ {
			s := state(ds, "artwork", w.ID, w.Fingerprint, round)
			check = " "
			if s == "done" {
				check = "x"
			}
			fmt.Fprintf(&b, "- [%s] Research %02d: %s", check, round, s)
			if d, ok := ds[decisionKey("artwork", w.ID, round)]; ok {
				fmt.Fprintf(&b, " — %s; image outcome: %s; checked %s", md(d.Note), md(d.ImageOutcome), d.CheckedAt.Format(time.RFC3339))
			}
			b.WriteString("\n")
			if d, ok := ds[decisionKey("artwork", w.ID, round)]; ok {
				for _, src := range d.Sources {
					fmt.Fprintf(&b, "  - %s\n", link("Review evidence", src))
				}
			}
		}
		b.WriteString("\n")
	}
	return b.String()
}
