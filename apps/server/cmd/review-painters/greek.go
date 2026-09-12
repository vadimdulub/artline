package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
)

const greekPin = "b91b869d01d13e8889182b77f99b2867298cc0ca22637b3b253a0966b56eadc0"
const greekPinV2 = "415a0504ab5f7fd3ca4683687943e7f75e48c7e60088c137bb853b03ddc2f900"
const greekActor = "local-european-research"
const greekBase = "https://www.nationalgallery.gr"

type GreekArtist struct {
	Key, Name, MuseumName, BirthDisplay, ExistingID, URL, SourceSHA, Biography string
	Start, End                                                                 int
	Uncertain                                                                  bool
}
type GreekWork struct {
	Artist, Key, Title, Date, Precision, Accession, Medium, Dimensions, Collection, URL, SourceSHA, Description string
	Year, LastYear                                                                                              int
}

func (w GreekWork) lastYear() int {
	if w.LastYear == 0 {
		return w.Year
	}
	return w.LastYear
}

// The content cutoff applies to works, never to the artist's lifespan.
// Literal source ranges must not become an invented single creation year.
func validGreekDate(w GreekWork) bool {
	last := w.lastYear()
	if w.Year < 1100 || last < w.Year || last > 1970 {
		return false
	}
	literal := strings.Join(strings.Fields(strings.NewReplacer("–", "-", "—", "-").Replace(w.Date)), "")
	year := strconv.Itoa(w.Year)
	switch w.Precision {
	case "exact":
		return last == w.Year && literal == year
	case "circa":
		return last == w.Year && (literal == "ca."+year || literal == "ca"+year || literal == "c."+year)
	case "range":
		return last > w.Year && literal == year+"-"+strconv.Itoa(last)
	default:
		return false
	}
}

func validGreekLifespan(a GreekArtist, now time.Time) bool {
	return a.Start >= 1100 && a.End >= a.Start && a.End <= now.Year()
}

type Evidence struct {
	URL, File, SHA string
	CheckedAt      time.Time
}
type GreekManifest struct {
	Version  string
	Created  time.Time
	Artists  []GreekArtist
	Works    []GreekWork
	Evidence []Evidence
	Policy   Evidence
}
type GreekResult struct{ Kind, Key, ID, Outcome, Source string }
type GreekReceipt struct {
	Applied bool
	SHA     string
	Results []GreekResult
}

func validateGreek(root string, b []byte, pin string) (GreekManifest, error) {
	return validateGreekAt(root, b, pin, time.Now())
}
func validateGreekAt(root string, b []byte, pin string, now time.Time) (GreekManifest, error) {
	var m GreekManifest
	version, captureDir, artistCount, workCount := "", "", 0, 0
	switch pin {
	case greekPin:
		version, captureDir, artistCount, workCount = "greek-painter-review-v1", "20260910", 10, 10
	case greekPinV2:
		version, captureDir, artistCount, workCount = "greek-painter-review-v2", "20260911", 4, 8
	default:
		return m, fmt.Errorf("unreviewed Greek snapshot")
	}
	if digest(b) != pin {
		return m, fmt.Errorf("unreviewed Greek snapshot")
	}
	if e := json.Unmarshal(b, &m); e != nil {
		return m, e
	}
	if m.Version != version || len(m.Artists) != artistCount || len(m.Works) != workCount || len(m.Evidence) != artistCount+workCount || now.Sub(m.Created) > 24*time.Hour || m.Created.Sub(now) > 5*time.Minute {
		return m, fmt.Errorf("invalid/stale bounded selection")
	}
	evidence := map[string]string{}
	for _, s := range append(m.Evidence, m.Policy) {
		if !strings.HasPrefix(s.File, "content/imports/greek-painter-review-"+captureDir+"/") || strings.Contains(s.File, "..") || now.Sub(s.CheckedAt) > 24*time.Hour || s.CheckedAt.Sub(now) > 5*time.Minute || evidence[s.URL] != "" {
			return m, fmt.Errorf("invalid source capture")
		}
		raw, e := os.ReadFile(filepath.Join(root, s.File))
		if e != nil {
			return m, e
		}
		if digest(raw) != s.SHA {
			return m, fmt.Errorf("source capture changed")
		}
		evidence[s.URL] = s.SHA
	}
	if m.Policy.URL != greekBase+"/oroi-chrisis/" {
		return m, fmt.Errorf("missing image rights decision")
	}
	seen := map[string]bool{}
	for _, a := range m.Artists {
		if !regexp.MustCompile(`^[a-z-]+$`).MatchString(a.Key) || seen[a.Key] || a.Name == "" || a.URL != greekBase+"/en/artist/"+a.Key+"/" || evidence[a.URL] != a.SourceSHA || !validGreekLifespan(a, now) {
			return m, fmt.Errorf("invalid artist identity/dates")
		}
		seen[a.Key] = true
	}
	workKeys := map[string]bool{}
	for _, w := range m.Works {
		if !seen[w.Artist] || workKeys[w.Key] || w.URL != greekBase+"/en/artwork/"+w.Key+"/" || evidence[w.URL] != w.SourceSHA || !validGreekDate(w) || w.Accession == "" || w.Title == "" {
			return m, fmt.Errorf("invalid selected work")
		}
		workKeys[w.Key] = true
	}
	return m, nil
}

func importGreek(ctx context.Context, p *pgxpool.Pool, root, input, pin, out string, apply bool) (err error) {
	b, e := os.ReadFile(input)
	if e != nil {
		return e
	}
	m, e := validateGreek(root, b, pin)
	if e != nil {
		return e
	}
	f, e := os.OpenFile(out, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	defer f.Close()
	report := GreekReceipt{SHA: pin, Results: []GreekResult{}}
	defer func() {
		e := json.NewEncoder(f).Encode(report)
		if err == nil {
			err = e
		}
	}()
	tx, e := p.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.Serializable})
	if e != nil {
		return e
	}
	defer tx.Rollback(ctx)
	if _, e = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(2026091010); SET LOCAL statement_timeout='30s'`); e != nil {
		return e
	}
	var sid, institution, place string
	if _, e = tx.Exec(ctx, `INSERT INTO sources(slug,name,source_type,base_url,terms_url,adapter_key) VALUES('national-gallery-greece','National Gallery of Greece — selected catalogue facts','collection_page',$1,$2,'greek-painter-review-v1') ON CONFLICT(slug) DO NOTHING`, greekBase, m.Policy.URL); e != nil {
		return e
	}
	if e = tx.QueryRow(ctx, `SELECT id::text FROM sources WHERE slug='national-gallery-greece' AND is_active AND base_url=$1`, greekBase).Scan(&sid); e != nil {
		return e
	}
	if e = tx.QueryRow(ctx, `SELECT id::text FROM places WHERE id='549e8cc8-f15e-461c-b847-c0542d9f3e47' AND normalized_name='athens' AND country_code='GR'`).Scan(&place); e != nil {
		return e
	}
	e = tx.QueryRow(ctx, `SELECT id::text FROM institutions WHERE slug='national-gallery-greece' AND status<>'archived' AND website_url=$1 FOR UPDATE`, greekBase).Scan(&institution)
	if errors.Is(e, pgx.ErrNoRows) {
		var duplicate bool
		if e = tx.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM institutions WHERE website_url LIKE 'https://www.nationalgallery.gr%' OR slug='national-gallery-greece')`).Scan(&duplicate); e != nil {
			return e
		}
		if duplicate {
			return fmt.Errorf("museum identity needs reconciliation")
		}
		e = tx.QueryRow(ctx, `INSERT INTO institutions(slug,name,normalized_name,place_id,website_url,kind,status,description) VALUES('national-gallery-greece','National Gallery – Alexandros Soutsos Museum','national gallery alexandros soutsos museum',$1,$2,'museum','review','Selected official catalogue records. Collection credit is retained; museum connection does not imply ownership or current display.') RETURNING id::text`, place, greekBase).Scan(&institution)
		if e != nil {
			return e
		}
		if _, e = tx.Exec(ctx, `INSERT INTO institution_venues(institution_id,slug,name,place_id,visit_url,source_url,checked_at,status) VALUES($1,'national-gallery-greece-athens','National Gallery, Athens',$2,$3,$3,$4,'review')`, institution, place, greekBase, m.Created); e != nil {
			return e
		}
	} else if e != nil {
		return e
	}
	cite := func(kind, id, field, key, url, note string) error {
		_, e := tx.Exec(ctx, `INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) SELECT $1,$2::uuid,$3,$4::uuid,$5,$6,$7,$8,$9 WHERE NOT EXISTS(SELECT 1 FROM citations WHERE entity_type=$1 AND entity_id=$2 AND field_name=$3 AND source_id=$4 AND source_record_id=$5 AND source_url=$6)`, kind, id, field, sid, key, url, note, m.Created, greekActor)
		return e
	}
	ids := map[string]string{}
	for _, a := range m.Artists {
		var id string
		outcome := "existing_preserved"
		e = tx.QueryRow(ctx, `SELECT a.id::text FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='nationalgallery-gr-artist' AND e.external_id=$1 AND e.canonical_url=$2 AND a.status<>'archived' FOR UPDATE OF a`, a.Key, a.URL).Scan(&id)
		if errors.Is(e, pgx.ErrNoRows) {
			if a.ExistingID != "" {
				e = tx.QueryRow(ctx, `SELECT id::text FROM artists WHERE id=$1 AND display_name=$2 AND birth_year=$3 AND death_year=$4 AND status<>'archived' FOR UPDATE`, a.ExistingID, a.Name, a.Start, a.End).Scan(&id)
				if e != nil {
					return e
				}
			} else {
				var duplicate bool
				if e = tx.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artists WHERE normalized_name=lower($1) OR slug=$2)`, a.Name, "greek-"+a.Key).Scan(&duplicate); e != nil {
					return e
				}
				if duplicate {
					return fmt.Errorf("artist identity needs review: %s", a.Name)
				}
				var birth any = a.Start
				basis, precision := "life", "exact"
				if a.Uncertain {
					birth = nil
					basis, precision = "estimated", "unknown"
				}
				e = tx.QueryRow(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,birth_year,death_year,birth_display,death_display,birth_precision,death_precision,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,biography_md,status,created_by,updated_by) VALUES($1,$2,$2,lower($2),$3::int,$4::int,$5,($4::int)::text,$6,'exact',$7::int,$4::int,$8,$9,$10,'review',$11,$11) RETURNING id::text`, "greek-"+a.Key, a.Name, birth, a.End, a.BirthDisplay, precision, a.Start, a.BirthDisplay+"–"+fmt.Sprint(a.End), basis, a.Biography, greekActor).Scan(&id)
				if e != nil {
					return e
				}
				outcome = "created"
				if _, e = tx.Exec(ctx, `INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES($1,'GR','cultural_affiliation',true,'Greek art catalogue context; not a birthplace or citizenship inference.')`, id); e != nil {
					return e
				}
			}
			if _, e = tx.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',$1,'nationalgallery-gr-artist',$2,$3,$4,$5)`, id, a.Key, a.URL, sid, m.Created); e != nil {
				return e
			}
		} else if e != nil {
			return e
		}
		ids[a.Key] = id
		if e = cite("artist", id, "identity_dates", a.Key, a.URL, "Exact named museum artist record; no fuzzy authority merge. Source capture SHA256 "+a.SourceSHA+". Existing artist fields preserved. "+a.BirthDisplay); e != nil {
			return e
		}
		report.Results = append(report.Results, GreekResult{"artist", a.Key, id, outcome, a.URL})
	}
	for _, w := range m.Works {
		var id string
		outcome := "existing_preserved"
		e = tx.QueryRow(ctx, `SELECT a.id::text FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE e.entity_type='artwork' AND e.scheme='nationalgallery-gr-work' AND e.external_id=$1 AND e.canonical_url=$2 AND a.current_institution_id=$3 AND a.accession_number=$4 AND aa.artist_id=$5 AND aa.attribution_role='primary' AND a.status<>'archived' FOR UPDATE OF a`, w.Key, w.URL, institution, w.Accession, ids[w.Artist]).Scan(&id)
		if errors.Is(e, pgx.ErrNoRows) {
			var duplicate bool
			if e = tx.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=$1 UNION ALL SELECT 1 FROM artworks WHERE current_institution_id=$2 AND accession_number=$3)`, w.URL, institution, w.Accession).Scan(&duplicate); e != nil {
				return e
			}
			if duplicate {
				return fmt.Errorf("artwork identity needs reconciliation: %s", w.Title)
			}
			kind := "painting"
			if w.Medium == "Pastel" {
				kind = "drawing"
			}
			e = tx.QueryRow(ctx, `INSERT INTO artworks(slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,description_md,creation_place_unknown_reason,current_institution_id,current_location_text,location_checked_at,accession_number,status,created_by,updated_by) VALUES($1,$2,lower($2),$3,$4,$14,$5,$6,$7,$8,$9,'Not established by this source review.',$10,'National Gallery of Greece catalogue; see collection credit.',$11,$12,'review',$13,$13) RETURNING id::text`, "greek-"+w.Key, w.Title, w.Date, w.Year, w.Precision, kind, w.Medium, w.Dimensions, w.Description, institution, m.Created, w.Accession, greekActor, w.lastYear()).Scan(&id)
			if e != nil {
				return e
			}
			if _, e = tx.Exec(ctx, `INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES($1,$2,'primary','Exact artist link on official object page; source attribution preserved.')`, id, ids[w.Artist]); e != nil {
				return e
			}
			if _, e = tx.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',$1,'nationalgallery-gr-work',$2,$3,$4,$5)`, id, w.Key, w.URL, sid, m.Created); e != nil {
				return e
			}
			if _, e = tx.Exec(ctx, `INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES($1,'holding',$2,'collection',$3,$4,$5,$6,'accepted')`, id, institution, sid, w.URL, "Official museum catalogue connection; "+w.Collection+". Not an ownership or current-display claim.", m.Created); e != nil {
				return e
			}
			outcome = "created"
		} else if e != nil {
			return e
		}
		if e = cite("artwork", id, "catalogue_metadata", w.Key, w.URL, "Title, literal date, medium, dimensions and accession individually checked. Source SHA256 "+w.SourceSHA+". Collection credit: "+w.Collection); e != nil {
			return e
		}
		if e = cite("artwork", id, "image_rights_review", w.Key, m.Policy.URL, "Image attempt reviewed: no unrestricted reuse grant established. Museum photograph not downloaded; permission or a separately licensed exact reproduction required. Policy SHA256 "+m.Policy.SHA); e != nil {
			return e
		}
		report.Results = append(report.Results, GreekResult{"artwork", w.Key, id, outcome, w.URL})
	}
	if apply {
		if e = tx.Commit(ctx); e != nil {
			return e
		}
		report.Applied = true
	} else {
		if e = tx.Rollback(ctx); e != nil {
			return e
		}
	}
	fmt.Printf("Applied=%v; %d reviewed artist/artwork decisions.\n", report.Applied, len(report.Results))
	return nil
}
