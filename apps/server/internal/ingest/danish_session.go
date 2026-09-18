package ingest

// Offline, checksum-pinned SMK research. Writes are bounded set operations;
// publication, image transfer and current-display claims are separate workflows.
import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

const danishSource = "danish-painters-20260913"
const danishScheme = "european-smk-statens-museum-for-kunst-object"

type DanishAuthor struct {
	ID, Name     string
	SortName     string `json:"sort_name"`
	Nationality  string
	URL          string `json:"source_url"`
	Birth, Death *int
	Start, End   int
	Painting     json.RawMessage `json:"painting_raw"`
	Person       json.RawMessage `json:"person_raw"`
}
type danishWork struct {
	europeanWork
	Raw json.RawMessage `json:"raw"`
}
type danishChunk struct {
	Source   string
	Accessed string `json:"accessed_on"`
	Authors  map[string]DanishAuthor
	Works    []danishWork
}
type danishSMK struct {
	Object     string                  `json:"object_number"`
	URL        string                  `json:"frontend_url"`
	Names      []struct{ Name string } `json:"object_names"`
	Titles     []struct{ Title string }
	Production []struct {
		ID          string `json:"creator_lref"`
		Name        string `json:"creator"`
		Nationality string `json:"creator_nationality"`
		Role        string `json:"creator_role"`
		Qualifier   string `json:"creator_qualifier"`
	}
	Dates []struct{ Start, End, Period string } `json:"production_date"`
	Notes []string                              `json:"production_dates_notes"`
}

var danishPersonID = regexp.MustCompile(`^[0-9]+_person$`)
var danishObjectID = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9./_-]{0,100}$`)
var danishUncertain = regexp.MustCompile(`(?i)(udateret|virkeår|levetid|baseret på kunstnerens årstal|tilgået museet|unknown|undated|after|before|efter|før|muligvis|tilskrevet)`)

func danishAssociation(s string) bool {
	for _, x := range strings.Split(s, ",") {
		if strings.TrimSpace(x) == "Danish" {
			return true
		}
	}
	return false
}
func danishCreator(raw json.RawMessage, pid string) (danishSMK, error) {
	var r danishSMK
	if e := json.Unmarshal(raw, &r); e != nil {
		return r, e
	}
	if len(r.Production) != 1 {
		return r, errors.New("single named creator required")
	}
	c := r.Production[0]
	if c.ID != pid || c.Name == "" || !danishAssociation(c.Nationality) || c.Qualifier != "" || (c.Role != "" && c.Role != "artist" && c.Role != "Painter") {
		return r, errors.New("unreviewed Danish creator/attribution")
	}
	return r, nil
}
func danishYear(s string) int {
	if len(s) < 5 || s[4] != '-' {
		return 0
	}
	v, _ := strconv.Atoi(s[:4])
	return v
}
func danishLife(raw json.RawMessage, kind string) *int {
	var p map[string]json.RawMessage
	if json.Unmarshal(raw, &p) != nil {
		return nil
	}
	var a, b, prec []string
	json.Unmarshal(p[kind+"_date_start"], &a)
	json.Unmarshal(p[kind+"_date_end"], &b)
	json.Unmarshal(p[kind+"_date_prec"], &prec)
	if len(a) != 1 || len(b) != 1 || len(prec) != 1 || !regexp.MustCompile(`^(?:[0-9]{1,2}-[0-9]{1,2}-)?[0-9]{4}$`).MatchString(prec[0]) {
		return nil
	}
	y := danishYear(a[0])
	if y < 1100 || y != danishYear(b[0]) {
		return nil
	}
	return &y
}
func sameYear(a, b *int) bool { return (a == nil && b == nil) || (a != nil && b != nil && *a == *b) }
func ValidateDanishSession(data []byte, sha string) error {
	_, e := validateDanish(data, sha)
	return e
}
func validateDanish(data []byte, sha string) (danishChunk, error) {
	var m danishChunk
	if !resolvedSHA.MatchString(sha) || checksum(data) != sha || len(data) > 16<<20 {
		return m, errors.New("Danish checksum/size mismatch")
	}
	if e := json.Unmarshal(data, &m); e != nil {
		return m, e
	}
	if m.Source != danishSource || len(m.Works) < 1 || len(m.Works) > 250 || len(m.Authors) < 1 || len(m.Authors) > 250 {
		return m, errors.New("invalid Danish batch shape")
	}
	checked, e := time.Parse("2006-01-02", m.Accessed)
	if e != nil || checked.After(time.Now()) {
		return m, errors.New("invalid retrieval date")
	}
	for pid, a := range m.Authors {
		if pid != a.ID || !danishPersonID.MatchString(pid) || strings.TrimSpace(a.Name) == "" || !danishAssociation(a.Nationality) || a.URL != "https://api.smk.dk/api/v1/person/?id="+pid+"&lang=en" {
			return m, fmt.Errorf("invalid painter %s", pid)
		}
		r, e := danishCreator(a.Painting, pid)
		if e != nil {
			return m, e
		}
		painting := false
		for _, n := range r.Names {
			painting = painting || n.Name == "Painting"
		}
		if !painting {
			return m, errors.New("creator lacks source painting evidence")
		}
		if !(a.Start == 0 && a.End == 0) && (a.Start < 1100 || a.End > 1970 || a.Start > a.End) {
			return m, errors.New("invalid activity interval")
		}
		if !sameYear(a.Birth, danishLife(a.Person, "birth")) || !sameYear(a.Death, danishLife(a.Person, "death")) {
			return m, errors.New("life dates disagree with literal person authority")
		}
		if a.Birth != nil && a.Death != nil && (*a.Birth > *a.Death || *a.Death-*a.Birth > 125) {
			return m, errors.New("implausible life interval")
		}
	}
	seen := map[string]bool{}
	for _, w := range m.Works {
		if m.Authors[w.Painter].ID == "" || !danishObjectID.MatchString(w.ObjectID) || strings.Contains(w.ObjectID, "..") || seen[w.ObjectID] || w.Accession != w.ObjectID || w.Institution != "smk-statens-museum-for-kunst" || w.URL != "https://open.smk.dk/artwork/image/"+w.ObjectID || w.AttributionRole != "primary" || w.Attribution != "" || w.MuseumHighlightURL != "" || w.CreationDate == nil {
			return m, fmt.Errorf("invalid Danish object %s", w.ObjectID)
		}
		d, e := europeanWorkDate(w.europeanWork)
		if e != nil {
			return m, e
		}
		r, e := danishCreator(w.Raw, w.Painter)
		if e != nil {
			return m, e
		}
		if r.Object != w.ObjectID || r.URL != w.URL {
			return m, errors.New("source object identity mismatch")
		}
		title, typ := false, false
		for _, t := range r.Titles {
			title = title || t.Title == w.Title
		}
		for _, n := range r.Names {
			typ = typ || strings.ToLower(n.Name) == w.WorkType
		}
		if !title || !typ || (w.WorkType != "painting" && w.WorkType != "drawing" && w.WorkType != "print") {
			return m, errors.New("title/type not supported by museum")
		}
		if len(r.Dates) == 1 {
			first, last := danishYear(r.Dates[0].Start), danishYear(r.Dates[0].End)
			if first > 1970 {
				return m, errors.New("explicit post-1970 source date")
			}
			if d.Precision != "unknown" && (first == 0 || last == 0 || d.First == nil || d.Last == nil || *d.First != first || *d.Last != last || danishUncertain.MatchString(strings.Join(r.Notes, " ")+" "+r.Dates[0].Period)) {
				return m, errors.New("date does not follow source or uses life/acquisition bounds")
			}
		} else if d.Precision != "unknown" {
			return m, errors.New("ambiguous source date requires review")
		}
		seen[w.ObjectID] = true
	}
	return m, nil
}

func ImportDanishSession(ctx context.Context, pool *pgxpool.Pool, data []byte, sha string, apply bool) (BulkReport, error) {
	out := BulkReport{EuropeanImportReport: EuropeanImportReport{Snapshot: sha, Warnings: []string{}, Works: []EuropeanWorkResult{}}}
	m, e := validateDanish(data, sha)
	if e != nil {
		return out, e
	}
	tx, e := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.Serializable})
	if e != nil {
		return out, e
	}
	defer tx.Rollback(ctx)
	if _, e = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(2026091315)`); e != nil {
		return out, e
	}
	if _, e = tx.Exec(ctx, `SET LOCAL statement_timeout='30s'; SET LOCAL lock_timeout='5s'`); e != nil {
		return out, e
	}
	var status string
	e = tx.QueryRow(ctx, `SELECT id::text,status FROM import_jobs WHERE idempotency_key=$1`, danishSource+"-"+sha).Scan(&out.JobID, &status)
	if e == nil {
		if status != "needs_review" {
			return out, errors.New("conflicting Danish import state")
		}
		out.Applied = apply
		out.Replayed = true
		return out, tx.Rollback(ctx)
	}
	if !errors.Is(e, pgx.ErrNoRows) {
		return out, e
	}
	if _, e = tx.Exec(ctx, `INSERT INTO editor_accounts(user_id,display_name,role) VALUES($1,'Catalogue research importer (review only)','owner') ON CONFLICT DO NOTHING`, europeanActor); e != nil {
		return out, e
	}
	if _, e = tx.Exec(ctx, `INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES($1,'SMK — selected Danish painter catalogue research','museum_api','https://api.smk.dk','https://www.smk.dk/en/article/smk-api/') ON CONFLICT DO NOTHING`, danishSource); e != nil {
		return out, e
	}
	var sid, iid string
	if e = tx.QueryRow(ctx, `SELECT id::text FROM sources WHERE slug=$1 AND is_active`, danishSource).Scan(&sid); e != nil {
		return out, e
	}
	if e = tx.QueryRow(ctx, `SELECT id::text FROM institutions WHERE slug='statens-museum-for-kunst'`).Scan(&iid); e != nil {
		return out, e
	}
	if e = tx.QueryRow(ctx, `INSERT INTO import_jobs(source_id,requested_by,adapter_version,query_json,status,idempotency_key) VALUES($1,$2,'danish-session-v1',$3,'running',$4) RETURNING id::text`, sid, europeanActor, rawJSON(map[string]string{"sha256": sha}), danishSource+"-"+sha).Scan(&out.JobID); e != nil {
		return out, e
	}
	checked, _ := time.Parse("2006-01-02", m.Accessed)
	s := europeanImport{ctx: ctx, tx: tx, checked: checked, job: out.JobID, report: &out.EuropeanImportReport}
	ids := map[string]string{}
	keys := []string{}
	for k := range m.Authors {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, pid := range keys {
		a := m.Authors[pid]
		var id string
		outcome := "skipped"
		e = tx.QueryRow(ctx, `SELECT a.id::text FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='smk-person' AND e.external_id=$1 AND a.status<>'archived' FOR UPDATE OF a`, pid).Scan(&id)
		if errors.Is(e, pgx.ErrNoRows) {
			var collision bool
			if e = tx.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artists WHERE normalized_name=ANY($1)) OR EXISTS(SELECT 1 FROM external_identifiers WHERE scheme='smk-person' AND external_id=$2)`, []string{normalize(a.Name), normalize(a.SortName)}, pid).Scan(&collision); e != nil {
				return out, e
			}
			if collision || (a.Start == 0 && (a.Birth == nil || a.Death == nil)) {
				ids[pid] = ""
				continue
			}
			start, end, basis := a.Start, a.End, "activity"
			display := fmt.Sprintf("Documented works %d–%d (not lifespan)", start, end)
			if a.Birth != nil && a.Death != nil {
				start, end, basis = *a.Birth, *a.Death, "life"
				display = fmt.Sprintf("%d–%d", start, end)
			}
			if e = tx.QueryRow(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,created_by,updated_by) VALUES($1,$2,$3,$4,$5,$6,$7,$8,'review',$9,$9) RETURNING id::text`, slug(a.Name)+"-smk-"+pid, a.Name, a.SortName, normalize(a.Name), start, end, display, basis, europeanActor).Scan(&id); e != nil {
				return out, e
			}
			if basis == "life" {
				_, e = tx.Exec(ctx, `UPDATE artists SET birth_year=$2,death_year=$3,birth_display=$4,death_display=$5,birth_precision='exact',death_precision='exact' WHERE id=$1`, id, a.Birth, a.Death, strconv.Itoa(start), strconv.Itoa(end))
			} else {
				_, e = tx.Exec(ctx, `UPDATE artists SET active_start_year=$2,active_end_year=$3,activity_display=$4 WHERE id=$1`, id, start, end, display)
			}
			if e != nil {
				return out, e
			}
			if _, e = tx.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',$1,'smk-person',$2,$3,$4,$5)`, id, pid, a.URL, sid, checked); e != nil {
				return out, e
			}
			out.CreatedArtists++
			outcome = "created"
		} else if e != nil {
			return out, e
		}
		ids[pid] = id
		if _, e = tx.Exec(ctx, `INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES($1,'DK','cultural_affiliation',false,$2) ON CONFLICT DO NOTHING`, id, "SMK source nationality: "+a.Nationality+". Multiple source associations retained; not an exclusive identity claim."); e != nil {
			return out, e
		}
		if e = s.cite("artist", id, "danish_painter_authority", sid, pid, a.URL, "Exact SMK person ID. Museum nationality: "+a.Nationality+". A named Painting record proves painter practice; full source evidence retained in the import record. Existing editorial biography and timeline retained."); e != nil {
			return out, e
		}
		if e = s.audit("artist:"+pid, a, a, outcome, "artist", id, "Source authority; new records remain in review."); e != nil {
			return out, e
		}
	}
	if _, e = tx.Exec(ctx, `CREATE TEMP TABLE danish_input(id uuid DEFAULT gen_random_uuid(),object_id text PRIMARY KEY,artist_id uuid,label text,data jsonb,raw jsonb,sha text) ON COMMIT DROP`); e != nil {
		return out, e
	}
	input := [][]any{}
	for _, w := range m.Works {
		a := m.Authors[w.Painter]
		id := ids[w.Painter]
		var artist any
		label := ""
		if id != "" {
			artist = id
		} else {
			label = a.Name
		}
		d := w.CreationDate
		normalized := map[string]any{"slug": "danish-smk-" + checksum([]byte(w.URL))[:20], "title": w.Title, "normalized_title": normalize(w.Title), "alternate_title": strings.Join(w.Aliases, "; "), "date_display": w.DateDisplay, "first": d.First, "last": d.Last, "precision": d.Precision, "work_type": w.WorkType, "medium": w.Medium, "dimensions": w.Dimensions, "url": w.URL, "notes": w.Notes, "painter": w.Painter, "nationality": a.Nationality}
		input = append(input, []any{w.ObjectID, artist, label, rawJSON(normalized), w.Raw, checksum(w.Raw)})
		if d.Precision == "unknown" {
			out.UnknownDates++
		}
	}
	if _, e = tx.CopyFrom(ctx, pgx.Identifier{"danish_input"}, []string{"object_id", "artist_id", "label", "data", "raw", "sha"}, pgx.CopyFromRows(input)); e != nil {
		return out, e
	}
	var conflicts int
	e = tx.QueryRow(ctx, `SELECT count(*) FROM danish_input i WHERE EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.scheme=$1 AND e.external_id=i.object_id) OR EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.canonical_url=i.data->>'url') OR EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.source_url=i.data->>'url') OR EXISTS(SELECT 1 FROM artworks a WHERE a.current_institution_id=$2 AND a.accession_number=i.object_id)`, danishScheme, iid).Scan(&conflicts)
	if e != nil {
		return out, e
	}
	if conflicts != 0 {
		return out, fmt.Errorf("%d exact objects already exist; re-plan without duplicates", conflicts)
	}
	queries := []struct {
		sql  string
		args []any
	}{
		{`INSERT INTO artworks(id,slug,title,normalized_title,alternate_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,description_md,creation_place_unknown_reason,current_location_text,accession_number,location_checked_at,status,unlinked_creator_label,cultural_context,created_by,updated_by)
 SELECT id,data->>'slug',data->>'title',data->>'normalized_title',nullif(data->>'alternate_title',''),data->>'date_display',(data->>'first')::int,(data->>'last')::int,data->>'precision',data->>'work_type',nullif(data->>'medium',''),nullif(data->>'dimensions',''),data->>'notes','Creation place not established by this research.','Statens Museum for Kunst, Copenhagen',object_id,$1,'review',nullif(label,''),CASE WHEN label<>'' THEN 'SMK source nationality: '||(data->>'nationality') END,$2,$2 FROM danish_input`, []any{checked, europeanActor}},
		{`INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) SELECT id,artist_id,'primary','Named creator in official SMK record; exact person ID '||(data->>'painter') FROM danish_input WHERE artist_id IS NOT NULL`, nil},
		{`INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) SELECT 'artwork',id,$1,object_id,data->>'url',$2,$3 FROM danish_input`, []any{danishScheme, sid, checked}},
		{`INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) SELECT id,'holding',$1,'collection',$2,data->>'url','Official SMK collection object record. Holding only; no current-display or ownership inference.',$3,'accepted' FROM danish_input`, []any{iid, sid, checked}},
		{`INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) SELECT 'artwork',id,'research_record',$1,object_id,data->>'url',(data->>'notes')||' Source person: '||(data->>'painter')||'. Literal date: '||(data->>'date_display')||'. Raw museum JSON and checksum retained in import audit.',$2,$3 FROM danish_input`, []any{sid, checked, europeanActor}},
		{`INSERT INTO import_records(import_job_id,source_record_id,source_checksum,outcome,matched_entity_type,matched_entity_id,raw_json,normalized_json,warnings_json) SELECT $1,object_id,sha,'created','artwork',id,raw,data,'["Review only. Museum holding is separate from current display; image rights require separate verification."]'::jsonb FROM danish_input`, []any{out.JobID}},
	}
	for _, q := range queries {
		if _, e = tx.Exec(ctx, q.sql, q.args...); e != nil {
			return out, e
		}
	}
	rows, e := tx.Query(ctx, `SELECT object_id,id::text,data->>'painter',data->>'title',data->>'url',data->>'precision' FROM danish_input ORDER BY object_id`)
	if e != nil {
		return out, e
	}
	for rows.Next() {
		var oid, id, painter, title, url, precision string
		if e = rows.Scan(&oid, &id, &painter, &title, &url, &precision); e != nil {
			rows.Close()
			return out, e
		}
		out.Works = append(out.Works, EuropeanWorkResult{painter, title, "statens-museum-for-kunst", url, id, "created", "primary", precision})
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return out, e
	}
	out.CreatedWorks = len(out.Works)
	out.AddedCitations += len(out.Works)
	out.ReusedMuseums = 1
	if _, e = tx.Exec(ctx, `UPDATE import_jobs SET status='needs_review',completed_at=now(),total_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1),accepted_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1) WHERE id=$1`, out.JobID); e != nil {
		return out, e
	}
	if !apply {
		return out, tx.Rollback(ctx)
	}
	if e = tx.Commit(ctx); e != nil {
		return out, e
	}
	out.Applied = true
	return out, nil
}
