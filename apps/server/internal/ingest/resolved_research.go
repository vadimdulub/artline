package ingest

// Source resolution preserves the original CSV snapshot. Museum facts live in
// a separate, checksummed record; only eligible, reconciled objects are promoted.
import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

const expandedCSVURL = "https://storage.googleapis.com/artline-508319-images/research/expanded-20260912/210a729ead48d12b0f228eb9e1fe0c5a6708750b196be38ddfbbb270aa1355c8.csv"

type ResolvedPainter struct {
	SourceID    string `json:"source_id"`
	Name        string `json:"name"`
	SortName    string `json:"sort_name"`
	Birth       *int   `json:"birth"`
	Death       *int   `json:"death"`
	DateDisplay string `json:"date_display"`
	Role        string `json:"role"`
	URL         string `json:"url"`
}
type ResolvedFact struct {
	ResearchID    string                                             `json:"research_record_id"`
	Source        string                                             `json:"source"`
	ObjectID      string                                             `json:"object_id"`
	ObjectURL     string                                             `json:"object_url"`
	Title         string                                             `json:"title"`
	Accession     string                                             `json:"accession"`
	DateDisplay   string                                             `json:"date_display"`
	DateFields    map[string]json.RawMessage                         `json:"date_fields"`
	WorkType      string                                             `json:"work_type"`
	TypeBasis     string                                             `json:"type_basis"`
	Medium        string                                             `json:"medium"`
	Dimensions    string                                             `json:"dimensions"`
	ObjectContext map[string]string                                  `json:"object_context"`
	Painter       ResolvedPainter                                    `json:"painter"`
	Institution   struct{ Key, Name, City, Country, Website string } `json:"institution"`
	Evidence      []struct {
		URL       string `json:"url"`
		SHA       string `json:"sha256"`
		Retrieved string `json:"retrieved_at"`
		Path      string `json:"local_path"`
	} `json:"evidence"`
	SourceNote string   `json:"source_note"`
	CSVCells   []string `json:"csv_cells"`
}
type ResolutionReport struct {
	SHA            string                     `json:"sha256"`
	Applied        bool                       `json:"applied"`
	Records        int                        `json:"records"`
	Inserted       int64                      `json:"inserted_resolutions"`
	CreatedArtists int                        `json:"created_artists"`
	CreatedWorks   int                        `json:"created_artworks"`
	ReusedWorks    int                        `json:"reused_artworks"`
	Counts         map[string]int             `json:"counts"`
	LookupPlans    map[string]json.RawMessage `json:"lookup_plans,omitempty"`
}

var resolvedSHA = regexp.MustCompile(`^[a-f0-9]{64}$`)
var resolvedObjectID = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9 ._/-]{0,99}$`)
var resolvedYear = regexp.MustCompile(`^(?:(c\.?|ca\.?|circa|about|vers)\s*)?(\d{4})(?:\s*[-–/]\s*(\d{1,4}))?(?:\s*(vers|en))?$`)
var resolvedFrenchPeriod = regexp.MustCompile(`^(?:(1er|1ère|2e|3e|4e) (quart|moitié) (?:du )?)?(\d{2})e siècle$`)
var uncertainSMK = regexp.MustCompile(`(?i)udateret|virkeår|levetid|baseret på kunstnerens årstal|tilgået museet|unknown|undated|after|before|efter|før|muligvis|tilskrevet`)
var qualifiedCreator = regexp.MustCompile(`(?i)unknown|anonym|an[oó]nim|inconnu|not recorded|unident|ubekendt|ukendt|tiedossa|ignoto|workshop|atelier|bottega|school|scuola|d'après|attribu|tilskrevet|circle of|follower|master of|ma[iî]tre|\b(skole|skola|schule|école|ecole|mesteren fra|mesteren af|mester af|meister von|maestro di)\b|;`)

func factString(f ResolvedFact, key string) string {
	var s string
	_ = json.Unmarshal(f.DateFields[key], &s)
	return s
}
func unknownResolvedDate() europeanDate { return europeanDate{Precision: "unknown"} }
func closedResolvedDate(a, b int, p string) europeanDate {
	return europeanDate{First: &a, Last: &b, Precision: p}
}
func resolvedPeriod(s string) europeanDate {
	a, b, precision := 9999, 0, "century"
	for _, part := range strings.Split(s, ";") {
		m := resolvedFrenchPeriod.FindStringSubmatch(strings.TrimSpace(part))
		if m == nil {
			return unknownResolvedDate()
		}
		c, _ := strconv.Atoi(m[3])
		lo, hi := (c-1)*100, c*100
		if m[1] != "" {
			n, _ := strconv.Atoi(m[1][:1])
			width := 25
			if m[2] == "moitié" {
				width = 50
			}
			if n*width > 100 {
				return unknownResolvedDate()
			}
			lo += (n - 1) * width
			hi = lo + width
			precision = "range"
		}
		a = min(a, lo)
		b = max(b, hi)
	}
	return closedResolvedDate(a, b, precision)
}
func resolvedLiteral(s string) europeanDate {
	m := resolvedYear.FindStringSubmatch(strings.TrimSpace(s))
	if m == nil {
		return unknownResolvedDate()
	}
	a, _ := strconv.Atoi(m[2])
	b, p := a, "exact"
	if m[3] != "" {
		b, _ = strconv.Atoi(m[3])
		if len(m[3]) < 4 {
			div := 1
			for range len(m[3]) {
				div *= 10
			}
			b += (a / div) * div
		}
		p = "range"
	}
	if b < a {
		return unknownResolvedDate()
	}
	if a == b {
		p = "exact"
	}
	if m[1] != "" || m[4] == "vers" {
		p = "circa"
		if a != b {
			p = "circa_range"
		}
	}
	return closedResolvedDate(a, b, p)
}
func resolvedDate(f ResolvedFact) europeanDate {
	d := resolvedLiteral(f.DateDisplay)
	switch f.Source {
	case "joconde":
		period := resolvedPeriod(factString(f, "periode_de_creation"))
		if factString(f, "millesime_de_creation") == "" {
			d = period
		} else if d.First != nil && period.First != nil && (*d.First < *period.First || *d.Last > *period.Last) {
			return unknownResolvedDate()
		}
	case "smk":
		var notes []string
		_ = json.Unmarshal(f.DateFields["notes"], &notes)
		for _, note := range notes {
			if uncertainSMK.MatchString(note) {
				return unknownResolvedDate()
			}
			if strings.Contains(strings.ToLower(note), "ca.") && d.First != nil {
				d.Precision = "circa"
				if *d.First != *d.Last {
					d.Precision = "circa_range"
				}
			}
		}
		start, end := factString(f, "start"), factString(f, "end")
		if len(start) < 4 || len(end) < 4 || d.First == nil {
			return unknownResolvedDate()
		}
		a, e1 := strconv.Atoi(start[:4])
		b, e2 := strconv.Atoi(end[:4])
		if e1 != nil || e2 != nil || a != *d.First || b != *d.Last {
			return unknownResolvedDate()
		}
		if f.Painter.Birth != nil && f.Painter.Death != nil && a == *f.Painter.Birth && b == *f.Painter.Death && b-a > 20 {
			return unknownResolvedDate()
		}
	}
	if d.First != nil && *d.First < 1100 {
		return unknownResolvedDate()
	}
	return d
}
func resolvedIssue(f ResolvedFact, d europeanDate) string {
	if catalog.CreationScope(d.First, d.Last, d.Precision) != "eligible" {
		return "creation_date_review"
	}
	if f.WorkType == "" {
		return "work_type_review"
	}
	if f.Source == "smk" && (f.ObjectContext["creator_qualifier"] != "" || strings.Contains(strings.ToLower(f.ObjectContext["creator_notes"]), "kopi efter")) {
		return "creator_attribution_review"
	}
	if strings.Contains(strings.ToLower(f.ObjectID), "verso") || strings.Contains(strings.ToLower(f.ObjectID), "recto") {
		return "physical_object_review"
	}
	if qualifiedCreator.MatchString(f.Painter.Name) {
		return "creator_attribution_review"
	}
	switch strings.ToLower(f.Painter.Role) {
	case "artist", "painter", "kunstner", "maler", "":
	default:
		return "creator_role_review"
	}
	if f.Painter.Birth != nil && *d.Last < *f.Painter.Birth || f.Painter.Death != nil && f.WorkType == "painting" && *d.First > *f.Painter.Death {
		return "creator_date_conflict"
	}
	if f.Source == "joconde" {
		if f.CSVCells[4] != "France" {
			return "institution_geography_review"
		}
		c := f.ObjectContext
		if c["missing"] != "" || c["missing_note"] != "" || c["deposit"] != "" {
			return "holding_or_deposit_review"
		}
		switch c["denomination"] {
		case "tableau", "peinture", "dessin", "estampe", "estampe originale":
		default:
			return "physical_object_review"
		}
		for _, word := range []string{"album", "carnet", "verso", "recto", "ensemble"} {
			if strings.Contains(strings.ToLower(f.Title+" "+f.Accession), word) {
				return "physical_object_review"
			}
		}
		if resolutionNameKey(strings.Split(c["localisation"], ";")[0]) != resolutionNameKey(f.Institution.City) {
			return "institution_localisation_review"
		}
	}
	return ""
}
func validateResolved(f ResolvedFact) error {
	if !resolvedSHA.MatchString(f.ResearchID) || !resolvedObjectID.MatchString(f.ObjectID) || len(f.CSVCells) != 6 || strings.TrimSpace(f.Title) == "" || f.Title != f.CSVCells[1] && normalize(f.Title) != normalize(f.CSVCells[1]) || len(f.Evidence) == 0 {
		return errors.New("invalid source resolution identity")
	}
	u, e := url.Parse(f.ObjectURL)
	if e != nil || u.Scheme != "https" || u.User != nil || u.Fragment != "" {
		return errors.New("invalid museum object URL")
	}
	switch f.Source {
	case "smk":
		if f.Painter.SourceID != "" && !regexp.MustCompile(`^[0-9]+_person$`).MatchString(f.Painter.SourceID) {
			return errors.New("invalid SMK creator authority")
		}
		if u.Host != "open.smk.dk" || u.Path != "/artwork/image/"+f.ObjectID || f.Institution.Key != "smk-statens-museum-for-kunst" {
			return errors.New("invalid SMK identity")
		}
	case "tate":
		if !regexp.MustCompile(`^[0-9]+$`).MatchString(f.Painter.SourceID) {
			return errors.New("invalid Tate creator authority")
		}
		if u.Host != "www.tate.org.uk" || !strings.HasPrefix(u.Path, "/art/artworks/") || f.Institution.Key != "tate" {
			return errors.New("invalid Tate identity")
		}
	case "joconde":
		if f.Painter.SourceID != "" {
			return errors.New("Joconde notice does not supply a creator authority ID")
		}
		if u.Host != "www.pop.culture.gouv.fr" || u.Path != "/notice/joconde/"+f.ObjectID || !regexp.MustCompile(`^joconde-m[0-9]{4}$`).MatchString(f.Institution.Key) {
			return errors.New("invalid Joconde identity")
		}
	default:
		return errors.New("unsupported museum source")
	}
	for _, e := range f.Evidence {
		if !resolvedSHA.MatchString(e.SHA) || !strings.HasPrefix(e.URL, "https://") || len(e.Retrieved) < 10 {
			return errors.New("missing pinned source evidence")
		}
	}
	if f.WorkType != "" {
		switch f.WorkType {
		case "painting", "drawing", "watercolor", "print", "fresco", "manuscript_illumination":
		default:
			return errors.New("invalid work type")
		}
	}
	return nil
}

type resolvedAuthor struct {
	ID, Name, SortName string
	Birth, Death       *int
	Status             string
}
type ResolutionImporter struct {
	Pool    *pgxpool.Pool
	Explain bool
	authors map[string][]resolvedAuthor
}

func resolutionNameKey(s string) string {
	v := strings.Fields(normalize(s))
	sort.Strings(v)
	return strings.Join(v, " ")
}
func (r *ResolutionImporter) loadAuthors(ctx context.Context) error {
	if r.authors != nil {
		return nil
	}
	r.authors = map[string][]resolvedAuthor{}
	rows, e := r.Pool.Query(ctx, `SELECT a.id::text,a.display_name,a.sort_name,a.birth_year,a.death_year,a.status,n.name FROM artists a CROSS JOIN LATERAL (SELECT a.display_name name UNION SELECT a.sort_name UNION SELECT alias FROM artist_aliases WHERE artist_id=a.id) n`)
	if e != nil {
		return e
	}
	defer rows.Close()
	for rows.Next() {
		var a resolvedAuthor
		var name string
		if e = rows.Scan(&a.ID, &a.Name, &a.SortName, &a.Birth, &a.Death, &a.Status, &name); e != nil {
			return e
		}
		r.rememberAuthor(name, a)
	}
	return rows.Err()
}
func (r *ResolutionImporter) rememberAuthor(name string, a resolvedAuthor) {
	k := resolutionNameKey(name)
	for _, v := range r.authors[k] {
		if v.ID == a.ID {
			return
		}
	}
	r.authors[k] = append(r.authors[k], a)
}

func (r *ResolutionImporter) Import(ctx context.Context, data []byte, sha string, apply, promote bool) (ResolutionReport, error) {
	out := ResolutionReport{SHA: checksum(data), Counts: map[string]int{}}
	if out.SHA != sha || len(data) > 16<<20 {
		return out, errors.New("unreviewed/oversize resolution chunk")
	}
	var facts []ResolvedFact
	if e := json.Unmarshal(data, &facts); e != nil {
		return out, e
	}
	if len(facts) < 1 || len(facts) > 500 {
		return out, errors.New("resolution chunk requires 1..500 entries")
	}
	out.Records = len(facts)
	seen := map[string]bool{}
	for _, f := range facts {
		if e := validateResolved(f); e != nil {
			return out, fmt.Errorf("%s: %w", f.ResearchID, e)
		}
		if seen[f.ResearchID] {
			return out, errors.New("duplicate CSV identity")
		}
		seen[f.ResearchID] = true
		issue := resolvedIssue(f, resolvedDate(f))
		if issue == "" {
			issue = "source_ready"
		}
		out.Counts[issue]++
	}
	if !apply {
		return out, nil
	}
	if promote {
		if e := r.loadAuthors(ctx); e != nil {
			return out, e
		}
	}
	tx, e := r.Pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.Serializable})
	if e != nil {
		return out, e
	}
	defer tx.Rollback(ctx)
	if _, e = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(2026090959); SET LOCAL statement_timeout='120s'`); e != nil {
		return out, e
	}
	if _, e = tx.Exec(ctx, `CREATE TEMP TABLE incoming_resolution(rid text,source_kind text,oid text,url text,sha text,facts jsonb,scope text,state text,note text,cells jsonb) ON COMMIT DROP`); e != nil {
		return out, e
	}
	_, e = tx.CopyFrom(ctx, pgx.Identifier{"incoming_resolution"}, []string{"rid", "source_kind", "oid", "url", "sha", "facts", "scope", "state", "note", "cells"}, pgx.CopyFromSlice(len(facts), func(i int) ([]any, error) {
		f := facts[i]
		b := rawJSON(f)
		d := resolvedDate(f)
		issue := resolvedIssue(f, d)
		state := "ready"
		if issue != "" {
			state = "needs_review"
		}
		return []any{f.ResearchID, f.Source, f.ObjectID, f.ObjectURL, checksum(b), b, catalog.CreationScope(d.First, d.Last, d.Precision), state, issue, rawJSON(f.CSVCells)}, nil
	}))
	if e != nil {
		return out, e
	}
	const matchSQL = `SELECT count(*) FROM incoming_resolution i JOIN LATERAL (
 SELECT raw_json FROM research_records WHERE source_record_id=i.rid AND source_key='supplied-registry' AND record_kind='catalogue_object' AND source_url=$1 OFFSET 0
 ) r ON r.raw_json->'csv'->'cells'=i.cells`
	if r.Explain {
		out.LookupPlans = map[string]json.RawMessage{}
		var plan json.RawMessage
		if e = tx.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) `+matchSQL, expandedCSVURL).Scan(&plan); e != nil {
			return out, e
		}
		out.LookupPlans["before_batch_statistics"] = plan
	}
	// Temporary tables have no autovacuum statistics. Facts JSON makes default
	// row estimates much larger than the bounded 500-row batch. The lateral
	// lookup also keeps source enrichment scoped to those IDs even near the end
	// of the fingerprint range, where a merge join would scan earlier records.
	if _, e = tx.Exec(ctx, `ANALYZE incoming_resolution`); e != nil {
		return out, e
	}
	if r.Explain {
		var plan json.RawMessage
		if e = tx.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) `+matchSQL, expandedCSVURL).Scan(&plan); e != nil {
			return out, e
		}
		out.LookupPlans["after_batch_statistics"] = plan
	}
	var matched int
	if e = tx.QueryRow(ctx, matchSQL, expandedCSVURL).Scan(&matched); e != nil {
		return out, e
	}
	if matched != len(facts) {
		return out, errors.New("CSV identity/content mismatch against target database")
	}
	tag, e := tx.Exec(ctx, `INSERT INTO research_resolutions(snapshot_id,research_record_id,source_kind,source_object_id,object_url,facts_sha256,facts_json,date_scope,state,note)
 SELECT r.snapshot_id,i.rid,i.source_kind,i.oid,i.url,i.sha,i.facts,i.scope,i.state,i.note FROM incoming_resolution i JOIN LATERAL (
 SELECT snapshot_id FROM research_records WHERE source_record_id=i.rid AND source_key='supplied-registry' AND record_kind='catalogue_object' AND source_url=$1 OFFSET 0
 ) r ON true ON CONFLICT DO NOTHING`, expandedCSVURL)
	if e != nil {
		return out, e
	}
	out.Inserted = tag.RowsAffected()
	if e = tx.QueryRow(ctx, `SELECT count(*) FROM incoming_resolution i JOIN LATERAL (
 SELECT facts_sha256 FROM research_resolutions WHERE research_record_id=i.rid AND source_kind=i.source_kind AND source_object_id=i.oid OFFSET 0
 ) r ON r.facts_sha256=i.sha`).Scan(&matched); e != nil {
		return out, e
	}
	if matched != len(facts) {
		return out, errors.New("existing resolution has different facts; explicit reconciliation required")
	}
	if promote {
		if _, e = tx.Exec(ctx, `INSERT INTO editor_accounts(user_id,display_name,role) VALUES($1,'Museum source reconciliation (review only)','owner') ON CONFLICT DO NOTHING`, europeanActor); e != nil {
			return out, e
		}
		if _, e = tx.Exec(ctx, `INSERT INTO sources(slug,name,source_type) VALUES('expanded-csv-source-resolution','Official museum sources resolving supplied CSV candidates','manual') ON CONFLICT DO NOTHING`); e != nil {
			return out, e
		}
		var job string
		e = tx.QueryRow(ctx, `INSERT INTO import_jobs(source_id,requested_by,adapter_version,query_json,status,idempotency_key) SELECT id,$1,'expanded-resolution-v1',$2,'running',$3 FROM sources WHERE slug='expanded-csv-source-resolution' ON CONFLICT(idempotency_key) DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING id::text`, europeanActor, rawJSON(map[string]string{"sha256": sha}), "expanded-resolution-"+sha).Scan(&job)
		if e != nil {
			return out, e
		}
		for _, f := range facts {
			if resolvedIssue(f, resolvedDate(f)) != "" {
				continue
			}
			var state string
			if e = tx.QueryRow(ctx, `SELECT state FROM research_resolutions WHERE research_record_id=$1 AND source_kind=$2 AND source_object_id=$3`, f.ResearchID, f.Source, f.ObjectID).Scan(&state); e != nil {
				return out, e
			}
			if state == "catalogued" {
				out.Counts["already_catalogued"]++
				continue
			}
			if state == "conflict" {
				out.Counts["source_review_hold"]++
				continue
			}
			sub, e := tx.Begin(ctx)
			if e != nil {
				return out, e
			}
			a, created, work, err := r.promote(ctx, sub, f, job)
			if err != nil {
				_ = sub.Rollback(ctx)
				var sqlError *pgconn.PgError
				if errors.As(err, &sqlError) {
					if sqlError.Code == "23505" && sqlError.ConstraintName == "external_identifiers_entity_type_entity_id_scheme_key" {
						err = errors.New("source identity conflicts with an existing object or creator identifier")
					} else {
						return out, fmt.Errorf("database failure promoting %s: %w", f.ResearchID, err)
					}
				}
				out.Counts["promotion_needs_review"]++
				if _, e = tx.Exec(ctx, `UPDATE research_resolutions SET state='needs_review',note=$4 WHERE research_record_id=$1 AND source_kind=$2 AND source_object_id=$3`, f.ResearchID, f.Source, f.ObjectID, err.Error()); e != nil {
					return out, e
				}
				continue
			}
			if e = sub.Commit(ctx); e != nil {
				return out, e
			}
			if created {
				out.CreatedArtists++
				r.rememberAuthor(a.Name, a)
				r.rememberAuthor(a.SortName, a)
			}
			if work.Outcome == "created" {
				out.CreatedWorks++
			} else {
				out.ReusedWorks++
			}
			if _, e = tx.Exec(ctx, `UPDATE research_resolutions SET state='catalogued',artist_id=$4,artwork_id=$5,note='Matched official source identity; catalogue record remains in review unless already published' WHERE research_record_id=$1 AND source_kind=$2 AND source_object_id=$3`, f.ResearchID, f.Source, f.ObjectID, a.ID, work.ID); e != nil {
				return out, e
			}
		}
		if _, e = tx.Exec(ctx, `UPDATE import_jobs SET status='needs_review',completed_at=now(),total_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1),accepted_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1) WHERE id=$1`, job); e != nil {
			return out, e
		}
	}
	if e = tx.Commit(ctx); e != nil {
		r.authors = nil
		return out, e
	}
	out.Applied = true
	return out, nil
}

func (r *ResolutionImporter) promote(ctx context.Context, tx pgx.Tx, f ResolvedFact, job string) (resolvedAuthor, bool, EuropeanWorkResult, error) {
	var empty resolvedAuthor
	var result EuropeanWorkResult
	d := resolvedDate(f)
	checked, e := time.Parse("2006-01-02", f.Evidence[0].Retrieved[:10])
	if e != nil {
		return empty, false, result, e
	}
	u, _ := url.Parse(f.ObjectURL)
	def := europeanDefinition{Slug: f.Institution.Key, Source: f.Institution.Key, Website: f.Institution.Website, Host: u.Host}
	if f.Source == "smk" {
		def.Slug = "statens-museum-for-kunst"
	}
	var mapped string
	var iid, sid string
	e = tx.QueryRow(ctx, `SELECT i.slug,i.id::text,s.id::text FROM sources s JOIN source_institutions x ON x.source_id=s.id JOIN institutions i ON i.id=x.institution_id WHERE s.slug=$1 AND s.is_active AND i.status<>'archived'`, f.Institution.Key).Scan(&mapped, &iid, &sid)
	if e == nil {
		def.Slug = mapped
	} else if !errors.Is(e, pgx.ErrNoRows) {
		return empty, false, result, e
	}
	batch := europeanBatch{Schema: 2, Version: "expanded-resolution-v1", Definitions: map[string]europeanDefinition{f.Institution.Key: def}}
	report := EuropeanImportReport{}
	s := europeanImport{ctx: ctx, tx: tx, checked: checked, job: job, report: &report, batch: batch}
	inst := europeanInstitution{ID: f.Institution.Key, Name: f.Institution.Name, City: f.Institution.City, Country: f.Institution.Country, DataURL: f.Evidence[0].URL, Rights: "Metadata only; image reuse not established.", DataRoute: "Pinned official museum source resolving a supplied CSV row"}
	if f.Source == "tate" {
		inst.City = ""
		iid, sid, e = resolvedTateInstitution(ctx, tx)
	} else if iid == "" {
		iid, sid, e = s.institution(inst, rawJSON(f.Institution))
	}
	if e != nil {
		return empty, false, result, e
	}
	a, created, e := r.resolvePainter(ctx, tx, f, sid, d)
	if e != nil {
		return empty, false, result, e
	}
	w := europeanWork{Painter: f.Painter.Name, Title: f.Title, Institution: f.Institution.Key, Accession: f.Accession, URL: f.ObjectURL, DateDisplay: f.DateDisplay, ObjectID: f.ObjectID, Publisher: f.Institution.Name, CreationDate: &d, AttributionRole: "primary", Medium: f.Medium, Dimensions: f.Dimensions, WorkType: f.WorkType, Notes: f.SourceNote + " Type evidence: " + f.TypeBasis, Access: "Source snapshot " + f.Evidence[0].SHA + "; CSV links retained in research_resolutions"}
	w.Accession = resolvedAccession(f.Accession)
	w.Dimensions = resolvedDimensions(f.Source, f.Dimensions)
	if e = s.work(w, rawJSON(w), a.ID, iid, sid, inst); e != nil {
		return empty, false, result, e
	}
	return a, created, report.Works[0], nil
}

func resolvedTateInstitution(ctx context.Context, tx pgx.Tx) (string, string, error) {
	// Tate's aggregate dataset does not identify a physical Tate venue. Keep the
	// institution without a fabricated London gallery, room or on-view record.
	_, e := tx.Exec(ctx, `INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES('tate','Tate Collection metadata (October 2014 snapshot)','museum_api','https://www.tate.org.uk','https://github.com/tategallery/collection/blob/master/LICENCE') ON CONFLICT DO NOTHING;
 INSERT INTO institutions(slug,name,normalized_name,website_url,status,description) VALUES('tate','Tate','tate','https://www.tate.org.uk','review','Aggregate Tate collection. Source snapshot dates to October 2014; a physical venue and current display are not established.') ON CONFLICT(slug) DO NOTHING`)
	if e != nil {
		return "", "", e
	}
	var iid, sid string
	e = tx.QueryRow(ctx, `SELECT i.id::text,s.id::text FROM institutions i CROSS JOIN sources s WHERE i.slug='tate' AND i.status<>'archived' AND s.slug='tate' AND s.is_active`).Scan(&iid, &sid)
	if e != nil {
		return "", "", e
	}
	_, e = tx.Exec(ctx, `INSERT INTO source_institutions(source_id,institution_id) VALUES($1,$2) ON CONFLICT DO NOTHING`, sid, iid)
	return iid, sid, e
}

func (r *ResolutionImporter) resolvePainter(ctx context.Context, tx pgx.Tx, f ResolvedFact, sid string, d europeanDate) (resolvedAuthor, bool, error) {
	p := f.Painter
	var a resolvedAuthor
	scheme := ""
	if p.SourceID != "" {
		scheme = f.Source + "-person"
	}
	if scheme != "" {
		e := tx.QueryRow(ctx, `SELECT a.id::text,a.display_name,a.sort_name,a.birth_year,a.death_year,a.status FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme=$1 AND e.external_id=$2`, scheme, p.SourceID).Scan(&a.ID, &a.Name, &a.SortName, &a.Birth, &a.Death, &a.Status)
		if e != nil && !errors.Is(e, pgx.ErrNoRows) {
			return a, false, e
		}
	}
	if a.ID == "" {
		candidates := map[string]resolvedAuthor{}
		for _, name := range []string{p.Name, p.SortName} {
			for _, v := range r.authors[resolutionNameKey(name)] {
				candidates[v.ID] = v
			}
		}
		matches := []resolvedAuthor{}
		for _, v := range candidates {
			positive := p.Birth != nil && v.Birth != nil && *p.Birth == *v.Birth || p.Death != nil && v.Death != nil && *p.Death == *v.Death
			conflict := p.Birth != nil && v.Birth != nil && *p.Birth != *v.Birth || p.Death != nil && v.Death != nil && *p.Death != *v.Death
			if positive && !conflict && v.Status != "archived" {
				matches = append(matches, v)
			}
		}
		if len(matches) == 1 {
			a = matches[0]
		} else if len(candidates) > 0 {
			return a, false, errors.New("creator name requires authority/biography reconciliation")
		}
	}
	created := a.ID == ""
	if created {
		// A shortened name with matching dates may already be in the catalogue.
		// Defer that collision instead of inventing a second identity or merging it.
		for _, entries := range r.authors {
			for _, candidate := range entries {
				if possibleResolvedAlias(p, candidate) {
					return a, false, errors.New("possible existing creator alias requires reconciliation")
				}
			}
		}
		if p.SourceID == "" && (p.Birth == nil || p.Death == nil) {
			return a, false, errors.New("creator lacks a source authority ID or a documented closed biography")
		}
		if strings.TrimSpace(p.Name) == "" || qualifiedCreator.MatchString(p.Name) {
			return a, false, errors.New("creator is not a resolved named person")
		}
		first, last, basis, display := *d.First, *d.Last, "activity", fmt.Sprintf("Documented works %d–%d (not lifespan)", *d.First, *d.Last)
		if p.Birth != nil && p.Death != nil {
			if *p.Birth > *p.Death || *p.Death-*p.Birth > 125 {
				return a, false, errors.New("source biography requires review")
			}
			first, last, basis, display = *p.Birth, *p.Death, "life", fmt.Sprintf("%d–%d", *p.Birth, *p.Death)
		}
		key := f.Source + ":" + p.SourceID
		if p.SourceID == "" {
			key = resolutionNameKey(p.Name) + ":" + display
		}
		nameSlug := slug(p.Name) + "-research-" + checksum([]byte(key))[:12]
		e := tx.QueryRow(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,birth_year,death_year,birth_display,death_display,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,created_by,updated_by)
 VALUES($1,$2,$3,$4,$5,$6,CASE WHEN $5::int IS NULL THEN NULL ELSE ($5::int)::text END,CASE WHEN $6::int IS NULL THEN NULL ELSE ($6::int)::text END,$7,$8,$9,$10,'review',$11,$11) RETURNING id::text`, nameSlug, p.Name, p.SortName, normalize(p.Name), p.Birth, p.Death, first, last, display, basis, europeanActor).Scan(&a.ID)
		if e != nil {
			return a, false, e
		}
		a.Name, a.SortName, a.Birth, a.Death, a.Status = p.Name, p.SortName, p.Birth, p.Death, "review"
	}
	if !created {
		if e := tx.QueryRow(ctx, `SELECT display_name,sort_name,birth_year,death_year,status FROM artists WHERE id=$1 FOR UPDATE`, a.ID).Scan(&a.Name, &a.SortName, &a.Birth, &a.Death, &a.Status); e != nil {
			return a, false, e
		}
	}
	if a.Status == "archived" || p.Birth != nil && a.Birth != nil && *p.Birth != *a.Birth || p.Death != nil && a.Death != nil && *p.Death != *a.Death {
		return a, false, errors.New("creator authority conflicts with existing biography or status")
	}
	if scheme != "" {
		if _, e := tx.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,source_id,canonical_url,retrieved_at) VALUES('artist',$1,$2,$3,$4,$5,now()) ON CONFLICT(scheme,external_id) DO NOTHING`, a.ID, scheme, p.SourceID, sid, p.URL); e != nil {
			return a, false, e
		}
	}
	// Expand only activity intervals owned by this importer. Preserve curated
	// lifespans and editor-managed existing artist intervals.
	if _, e := tx.Exec(ctx, `UPDATE artists SET timeline_start_year=LEAST(timeline_start_year,$2),timeline_end_year=GREATEST(timeline_end_year,$3),timeline_display='Documented works ' || LEAST(timeline_start_year,$2)::text || '–' || GREATEST(timeline_end_year,$3)::text || ' (not lifespan)' WHERE id=$1 AND slug LIKE '%-research-%' AND timeline_basis='activity' AND status='review' AND created_by=$4 AND updated_by=$4`, a.ID, *d.First, *d.Last, europeanActor); e != nil {
		return a, false, e
	}
	if _, e := tx.Exec(ctx, `INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) SELECT 'artist',$1,'museum_creator_record',$2,$3,$4,$5,now(),$6 WHERE NOT EXISTS(SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=$1 AND field_name='museum_creator_record' AND source_id=$2 AND source_record_id=$3)`, a.ID, sid, f.Source+":"+p.SourceID+":"+checksum([]byte(p.Name + p.DateDisplay))[:12], p.URL, "Museum creator metadata: "+p.Name+"; source biography: "+p.DateDisplay+". Source authority ID: "+p.SourceID+". No nationality, popularity or current display inferred.", europeanActor); e != nil {
		return a, false, e
	}
	return a, created, nil
}

func possibleResolvedAlias(p ResolvedPainter, a resolvedAuthor) bool {
	if !(p.Birth != nil && a.Birth != nil && *p.Birth == *a.Birth || p.Death != nil && a.Death != nil && *p.Death == *a.Death) {
		return false
	}
	words := strings.Fields(normalize(p.Name))
	for _, existing := range strings.Fields(normalize(a.Name)) {
		for _, word := range words {
			if len(word) > 3 && word == existing {
				return true
			}
		}
	}
	return false
}

func resolvedAccession(s string) string {
	// These source literals explicitly mean no inventory number. They cannot
	// be used as shared object identities; the original remains in the evidence.
	switch normalize(s) {
	case "sn", "s n", "sans numero", "sans numero inventaire", "sans numero d inventaire", "non inventorie", "neant", "0":
		return ""
	}
	return s
}

func resolvedDimensions(source, raw string) string {
	if source != "smk" {
		return raw
	}
	var rows []struct{ Part, Type, Value, Unit, Notes string }
	if json.Unmarshal([]byte(raw), &rows) != nil {
		return raw
	}
	parts := []string{}
	for _, row := range rows {
		label := strings.TrimSpace(row.Part + " " + row.Type)
		value := strings.TrimSpace(row.Value + " " + row.Unit)
		if row.Notes != "" {
			value += " (" + row.Notes + ")"
		}
		value = strings.TrimSpace(value)
		if value == "" {
			continue
		}
		if label != "" {
			value = label + ": " + value
		}
		parts = append(parts, value)
	}
	return strings.Join(parts, "; ")
}
