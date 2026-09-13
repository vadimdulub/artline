package ingest

// This is a bounded, offline import of reviewed official-source evidence, not a
// crawler. Changing the source snapshot requires a deliberate new review/version.
import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

const EuropeanSnapshotSHA = "4b2997fdc8403a9a65ad80e3fb77b14aea607d5dbe53f732fe8d70f5cc88da69"
const europeanVersion = "european-research-2026-09-09-v1"
const europeanActor = "local-european-research"
const pissarroBiography = "https://www.nationalgallery.org.uk/artists/camille-pissarro"

type europeanInstitution struct {
	ID, Name, City, Country, Rights string
	DataURL                         string `json:"data_url"`
	DataRoute                       string `json:"data_route"`
	RightsURL                       string `json:"rights_url"`
}
type europeanWork struct {
	Painter, Title, Institution, Accession, URL, Attribution, Notes, Owner, Custody, Collection, Access string
	DateDisplay                                                                                         string        `json:"date_display"`
	ObjectID                                                                                            string        `json:"source_object_id"`
	Publisher                                                                                           string        `json:"source_publisher"`
	UpdatedOn                                                                                           string        `json:"source_updated_on"`
	ConflictingSource                                                                                   string        `json:"conflicting_source"`
	Aliases                                                                                             []string      `json:"aliases"`
	CreationDate                                                                                        *europeanDate `json:"creation_date"`
	AttributionRole                                                                                     string        `json:"attribution_role"`
	Medium                                                                                              string        `json:"medium"`
	Dimensions                                                                                          string        `json:"dimensions"`
	CreationPlaceText                                                                                   string        `json:"creation_place_text"`
	MuseumHighlightURL                                                                                  string        `json:"museum_highlight_url"`
	WorkType                                                                                            string        `json:"work_type,omitempty"`
	Description                                                                                         string        `json:"description_md,omitempty"`
	UnlinkedCreatorLabel                                                                                string        `json:"unlinked_creator_label,omitempty"`
	CulturalContext                                                                                     string        `json:"cultural_context,omitempty"`
	ObjectForm                                                                                          string        `json:"object_form,omitempty"`
}
type europeanManifest struct {
	Schema       int               `json:"schema_version"`
	AccessedOn   string            `json:"accessed_on"`
	Institutions []json.RawMessage `json:"institutions"`
	Works        []json.RawMessage `json:"works"`
}
type europeanDefinition struct{ Slug, Source, Website, Host string }

var europeanInstitutions = map[string]europeanDefinition{
	"ng":             {"national-gallery-london", "national-gallery-london", "https://www.nationalgallery.org.uk", "www.nationalgallery.org.uk"},
	"mnaa":           {"museu-nacional-de-arte-antiga", "museu-nacional-de-arte-antiga", "https://www.museudearteantiga.pt", "www.museudearteantiga.pt"},
	"msk":            {"museum-of-fine-arts-ghent", "museum-of-fine-arts-ghent", "https://www.mskgent.be", "www.mskgent.be"},
	"berlin":         {"gemaldegalerie-berlin", "gemaldegalerie-berlin", "https://www.smb.museum/en/museums-institutions/gemaeldegalerie/home/", "id.smb.museum"},
	"louvre":         {"musee-du-louvre", "louvre", "https://www.louvre.fr", "collections.louvre.fr"},
	"greco":          {"museo-del-greco", "museo-del-greco", "https://www.cultura.gob.es/mgreco/", "www.cultura.gob.es"},
	"boijmans":       {"museum-boijmans-van-beuningen", "museum-boijmans-van-beuningen", "https://www.boijmans.nl", "www.boijmans.nl"},
	"thyssen":        {"museo-thyssen-bornemisza", "museo-thyssen-bornemisza", "https://www.museothyssen.org", "www.museothyssen.org"},
	"scotland":       {"scottish-national-gallery", "scottish-national-gallery", "https://www.nationalgalleries.org", "www.nationalgalleries.org"},
	"lazaro":         {"museo-lazaro-galdiano", "museo-lazaro-galdiano", "https://www.museolazarogaldiano.es", "www.museolazarogaldiano.es"},
	"prado":          {"museo-del-prado", "museo-del-prado", "https://www.museodelprado.es", "www.museodelprado.es"},
	"khm":            {"kunsthistorisches-museum", "kunsthistorisches-museum", "https://www.khm.at", "www.khm.at"},
	"academy":        {"academy-fine-arts-vienna-paintings-gallery", "academy-fine-arts-vienna-paintings-gallery", "https://www.kunstsammlungenakademie.at/en/paintings-gallery/about/", "www.kunstsammlungenakademie.at"},
	"estense":        {"galleria-estense", "italian-national-catalogue-estense", "https://gallerie-estensi.beniculturali.it/en/", "catalogo.beniculturali.it"},
	"orsay":          {"musee-orsay", "musee-orsay", "https://www.musee-orsay.fr", "www.musee-orsay.fr"},
	"orangerie":      {"musee-orangerie", "musee-orangerie", "https://www.musee-orangerie.fr", "www.musee-orangerie.fr"},
	"marmottan":      {"musee-marmottan-monet", "musee-marmottan-monet", "https://www.marmottan.fr", "www.marmottan.fr"},
	"rouen":          {"musee-beaux-arts-rouen", "musee-beaux-arts-rouen", "https://mbarouen.fr", "mbarouen.fr"},
	"cardiff":        {"national-museum-cardiff", "national-museum-cardiff", "https://museum.wales/cardiff/", "museum.wales"},
	"staedel":        {"staedel-museum", "staedel-museum", "https://www.staedelmuseum.de", "sammlung.staedelmuseum.de"},
	"rijks":          {"rijksmuseum", "rijksmuseum", "https://www.rijksmuseum.nl", "www.rijksmuseum.nl"},
	"beyeler":        {"fondation-beyeler", "fondation-beyeler", "https://www.fondationbeyeler.ch", "www.fondationbeyeler.ch"},
	"muma":           {"muma-le-havre", "muma-le-havre", "https://www.muma-lehavre.fr", "www.muma-lehavre.fr"},
	"ordrupgaard":    {"ordrupgaard", "ordrupgaard", "https://museumordrupgaard.dk", "museumordrupgaard.dk"},
	"nationalmuseum": {"nationalmuseum-stockholm", "nationalmuseum-stockholm", "https://www.nationalmuseum.se", "collection.nationalmuseum.se"},
	"belvedere":      {"belvedere", "belvedere", "https://www.belvedere.at", "sammlung.belvedere.at"},
}
var europeanPainters = map[string]string{"Bosch": "Q130531", "El Greco": "Q301", "Monet": "Q296", "Pissarro": "Q134741"}

type EuropeanWorkResult struct {
	Painter   string `json:"painter"`
	Title     string `json:"title"`
	Museum    string `json:"museum"`
	URL       string `json:"source_url"`
	ID        string `json:"artwork_id"`
	Outcome   string `json:"outcome"`
	Role      string `json:"attribution_role"`
	Precision string `json:"date_precision"`
}
type EuropeanImportReport struct {
	Applied               bool                 `json:"applied"`
	Snapshot              string               `json:"snapshot_sha256"`
	JobID                 string               `json:"job_id"`
	CreatedWorks          int                  `json:"created_artworks"`
	ReusedWorks           int                  `json:"reused_artworks"`
	EnrichedWorks         int                  `json:"enriched_existing_artworks"`
	AddedHighlights       int                  `json:"added_museum_highlights"`
	CreatedMuseums        int                  `json:"created_museums"`
	ReusedMuseums         int                  `json:"reused_museums"`
	AddedCitations        int                  `json:"added_citations"`
	ClassificationChanges int                  `json:"pissarro_classification_changes"`
	QualifiedWorks        int                  `json:"qualified_artworks"`
	UnknownDates          int                  `json:"unknown_creation_dates"`
	Warnings              []string             `json:"warnings"`
	Works                 []EuropeanWorkResult `json:"works"`
}
type europeanDate struct {
	First     *int   `json:"first"`
	Last      *int   `json:"last"`
	Precision string `json:"precision"`
}

var europeanDateRE = regexp.MustCompile(`^(about |c\. |ca\. |circa |um )?(\d{4})(?:\s*[-/]\s*(?:circa )?(\d{2}|\d{4}))?$`)
var europeanFrenchDateRE = regexp.MustCompile(`^entre (\d{4}) et (\d{4})$`)

func europeanCreationDate(display string) (europeanDate, error) {
	d := europeanDate{Precision: "unknown"}
	// Signature dates are not automatically creation dates. Preserve the literal.
	if display == "Signed 1882" {
		return d, nil
	}
	if display == "Fines del s. XV" {
		a, b := 1401, 1500
		return europeanDate{&a, &b, "century"}, nil
	}
	if display == "late 1570s" {
		a, b := 1570, 1579
		return europeanDate{&a, &b, "decade"}, nil
	}
	s := europeanFrenchDateRE.ReplaceAllString(display, "$1-$2")
	m := europeanDateRE.FindStringSubmatch(s)
	if m == nil {
		return d, fmt.Errorf("unreviewed creation date %q", display)
	}
	a, _ := strconv.Atoi(m[2])
	b := a
	d.Precision = "exact"
	if m[3] != "" {
		b, _ = strconv.Atoi(m[3])
		if len(m[3]) == 2 {
			b += (a / 100) * 100
		}
		d.Precision = "range"
	}
	if m[1] != "" {
		if d.Precision == "range" {
			d.Precision = "circa_range"
		} else {
			d.Precision = "circa"
		}
	}
	if a < 1100 || b < a || b > 1970 {
		return d, fmt.Errorf("date outside approved batch scope: %q", display)
	}
	d.First, d.Last = &a, &b
	return d, nil
}
func europeanRole(w europeanWork) (string, error) {
	if w.AttributionRole != "" {
		switch w.AttributionRole {
		case "primary", "attributed_to", "workshop", "circle_of", "follower_of", "formerly_attributed_to":
			if w.AttributionRole != "primary" && w.Attribution == "" {
				return "", errors.New("qualified role needs literal attribution evidence")
			}
			return w.AttributionRole, nil
		default:
			return "", errors.New("unsupported attribution role")
		}
	}
	switch w.Attribution {
	case "":
		return "primary", nil
	case "disputed; museum-listed Bosch", "possibly by El Greco", "attributed to El Greco (attribuito)":
		return "attributed_to", nil
	default:
		return "", fmt.Errorf("unreviewed attribution %q", w.Attribution)
	}
}
func europeanURL(key, raw string) bool {
	return europeanAllowedURL(europeanInstitutions, key, raw)
}
func europeanAllowedURL(defs map[string]europeanDefinition, key, raw string) bool {
	d, ok := defs[key]
	if !ok {
		return false
	}
	u, err := url.Parse(raw)
	return err == nil && u.Scheme == "https" && strings.Contains("|"+d.Host+"|", "|"+u.Host+"|") && u.User == nil && u.Fragment == "" && u.Path != ""
}
func europeanIdentity(w europeanWork) (string, string) {
	id := w.ObjectID
	if id == "" {
		id = w.Accession
	}
	if id == "" {
		id = w.URL
	}
	return "european-" + w.Institution + "-object", id
}

// ImportEuropean performs the exact same transaction for preview and apply.
// Preview rolls EVERYTHING back, including audit rows, sources and import jobs.
// PostgreSQL sequences may advance; returned preview UUIDs are provisional.
func ImportEuropean(ctx context.Context, pool *pgxpool.Pool, data []byte, apply bool) (EuropeanImportReport, error) {
	return importEuropeanBatch(ctx, pool, data, apply, europeanBatch{SHA: EuropeanSnapshotSHA, Version: europeanVersion, Path: "docs/research/european-paintings/inventory.json", Schema: 1, Works: 59, Museums: 26, Painters: europeanPainters, Definitions: europeanInstitutions, ClassifyPissarro: true})
}

type europeanBatch struct {
	SHA, Version, Path     string
	SourceSlug, SourceName string
	Schema, Works, Museums int
	Painters               map[string]string
	Definitions            map[string]europeanDefinition
	ClassifyPissarro       bool
	AllowUnlinkedCreators  bool
}

func importEuropeanBatch(ctx context.Context, pool *pgxpool.Pool, data []byte, apply bool, batch europeanBatch) (EuropeanImportReport, error) {
	out := EuropeanImportReport{Snapshot: checksum(data), Warnings: []string{}, Works: []EuropeanWorkResult{}}
	if out.Snapshot != batch.SHA {
		return out, errors.New("unreviewed European snapshot: checksum does not match approved inventory")
	}
	var manifest europeanManifest
	if err := json.Unmarshal(data, &manifest); err != nil {
		return out, err
	}
	if manifest.Schema != batch.Schema || len(manifest.Works) != batch.Works || len(manifest.Institutions) != batch.Museums {
		return out, errors.New("unexpected batch structure")
	}
	checked, err := time.Parse("2006-01-02", manifest.AccessedOn)
	if err != nil || checked.After(time.Now()) {
		return out, errors.New("invalid/future evidence access date")
	}
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.Serializable})
	if err != nil {
		return out, err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(2026090959)`); err != nil {
		return out, err
	}
	if _, err = tx.Exec(ctx, `SET LOCAL statement_timeout='30s'`); err != nil {
		return out, err
	}
	// Resolve every approved pre-existing authority first. Never create a painter or
	// use approximate name matching as a fallback for a missing authority.
	artists := map[string]string{}
	for name, qid := range batch.Painters {
		var id string
		err = tx.QueryRow(ctx, `SELECT a.id::text FROM external_identifiers e JOIN artists a ON a.id=e.entity_id
 WHERE e.entity_type='artist' AND e.scheme='wikidata' AND e.external_id=$1 AND a.status<>'archived' FOR UPDATE OF a`, qid).Scan(&id)
		if err != nil {
			return out, fmt.Errorf("painter authority %s (%s): %w", name, qid, err)
		}
		artists[name] = id
	}
	if _, err = tx.Exec(ctx, `INSERT INTO editor_accounts(user_id,display_name,role) VALUES($1,'European museum research importer (review only)','owner') ON CONFLICT DO NOTHING`, europeanActor); err != nil {
		return out, err
	}
	var batchSource string
	batchSlug, batchName := batch.SourceSlug, batch.SourceName
	if batchSlug == "" {
		batchSlug, batchName = "european-museum-research", "European museum research — reviewed evidence inventory"
	}
	if _, err = tx.Exec(ctx, `INSERT INTO sources(slug,name,source_type,adapter_key) VALUES($1,$2,'manual',$3) ON CONFLICT(slug) DO NOTHING`, batchSlug, batchName, batch.Version); err != nil {
		return out, err
	}
	if err = tx.QueryRow(ctx, `SELECT id::text FROM sources WHERE slug=$1 AND is_active`, batchSlug).Scan(&batchSource); err != nil {
		return out, err
	}
	if _, err = tx.Exec(ctx, `INSERT INTO import_jobs(source_id,requested_by,adapter_version,query_json,status,idempotency_key,raw_manifest_path)
 VALUES($1,$2,$3,$4,'running',$3,$5) ON CONFLICT(idempotency_key) DO NOTHING`, batchSource, europeanActor, batch.Version, rawJSON(map[string]string{"sha256": out.Snapshot}), batch.Path); err != nil {
		return out, err
	}
	var previousSHA string
	if err = tx.QueryRow(ctx, `SELECT id::text,query_json->>'sha256' FROM import_jobs WHERE idempotency_key=$1 FOR UPDATE`, batch.Version).Scan(&out.JobID, &previousSHA); err != nil {
		return out, err
	}
	if previousSHA != out.Snapshot {
		return out, errors.New("import job snapshot changed; review required")
	}
	state := europeanImport{ctx: ctx, tx: tx, checked: checked, job: out.JobID, report: &out, batch: batch}
	instIDs, sourceIDs, instDefs := map[string]string{}, map[string]string{}, map[string]europeanInstitution{}
	for _, raw := range manifest.Institutions {
		var inst europeanInstitution
		if err = json.Unmarshal(raw, &inst); err != nil {
			return out, err
		}
		id, sid, e := state.institution(inst, raw)
		if e != nil {
			return out, fmt.Errorf("institution %s: %w", inst.ID, e)
		}
		instIDs[inst.ID], sourceIDs[inst.ID], instDefs[inst.ID] = id, sid, inst
	}
	seen := map[string]bool{}
	for _, raw := range manifest.Works {
		var w europeanWork
		if err = json.Unmarshal(raw, &w); err != nil {
			return out, err
		}
		unlinked := batch.AllowUnlinkedCreators && w.Painter == "" && strings.TrimSpace(w.UnlinkedCreatorLabel) != ""
		if (!unlinked && artists[w.Painter] == "") || (!unlinked && w.UnlinkedCreatorLabel != "") || instIDs[w.Institution] == "" || !europeanAllowedURL(batch.Definitions, w.Institution, w.URL) || seen[w.URL] {
			return out, fmt.Errorf("invalid/duplicate source identity: %s", w.Title)
		}
		seen[w.URL] = true
		if err = state.work(w, raw, artists[w.Painter], instIDs[w.Institution], sourceIDs[w.Institution], instDefs[w.Institution]); err != nil {
			return out, fmt.Errorf("%s / %s: %w", w.Painter, w.Title, err)
		}
	}
	if batch.ClassifyPissarro {
		if err = state.pissarro(artists["Pissarro"], sourceIDs["ng"]); err != nil {
			return out, err
		}
	}
	if _, err = tx.Exec(ctx, `UPDATE import_jobs SET status='needs_review',completed_at=coalesce(completed_at,now()),
 total_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1),
 accepted_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1 AND outcome IN ('created','updated','skipped'))
 WHERE id=$1 AND status<>'needs_review'`, out.JobID); err != nil {
		return out, err
	}
	if !apply {
		out.Warnings = append(out.Warnings, "Dry run: transaction rolled back; UUIDs for planned new records are provisional.")
		return out, tx.Rollback(ctx)
	}
	if err = tx.Commit(ctx); err != nil {
		return out, err
	}
	out.Applied = true
	return out, nil
}

type europeanImport struct {
	ctx     context.Context
	tx      pgx.Tx
	checked time.Time
	job     string
	report  *EuropeanImportReport
	batch   europeanBatch
}

func (s europeanImport) cite(kind, id, field, sid, recordID, sourceURL, note string) error {
	tag, err := s.tx.Exec(s.ctx, `INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
 SELECT $1,$2::uuid,$3,$4::uuid,$5,$6,$7,$8,$9 WHERE NOT EXISTS(
 SELECT 1 FROM citations WHERE entity_type=$1 AND entity_id=$2 AND field_name=$3 AND source_id=$4 AND source_record_id=$5 AND source_url=$6)`, kind, id, field, sid, recordID, sourceURL, note, s.checked, europeanActor)
	s.report.AddedCitations += int(tag.RowsAffected())
	return err
}
func (s europeanImport) audit(recordID string, raw, normalized any, outcome, kind, id, note string) error {
	// True no-op replay: don't churn import timestamps or audit history.
	var priorSHA, priorID string
	err := s.tx.QueryRow(s.ctx, `SELECT source_checksum,coalesce(matched_entity_id::text,'') FROM import_records WHERE import_job_id=$1 AND source_record_id=$2`, s.job, recordID).Scan(&priorSHA, &priorID)
	if err == nil {
		if priorSHA != checksum(rawJSON(raw)) || priorID != id {
			return fmt.Errorf("import identity/snapshot conflict for %s", recordID)
		}
		return nil
	}
	if !errors.Is(err, pgx.ErrNoRows) {
		return err
	}
	return record(s.ctx, s.tx, s.job, recordID, raw, normalized, outcome, kind, id, note)
}

func (s europeanImport) institution(inst europeanInstitution, raw json.RawMessage) (string, string, error) {
	d, ok := s.batch.Definitions[inst.ID]
	if !ok {
		return "", "", errors.New("unapproved institution")
	}
	var name, region string
	for country, v := range birthCountries {
		parts := strings.Fields(v)
		if parts[0] == inst.Country {
			name, region = country, parts[1]
			break
		}
	}
	if name == "" {
		return "", "", errors.New("unknown country")
	}
	if _, err := s.tx.Exec(s.ctx, `INSERT INTO countries(code,name,region_code) VALUES($1,$2,$3) ON CONFLICT DO NOTHING`, inst.Country, name, region); err != nil {
		return "", "", err
	}
	var sid string
	publisher := inst.Name
	if inst.ID == "estense" {
		publisher = "Italian Ministry of Culture — Galleria Estense catalogue"
	}
	if _, err := s.tx.Exec(s.ctx, `INSERT INTO sources(slug,name,source_type,base_url,api_docs_url,terms_url,adapter_key)
 VALUES($1,$2,'collection_page',$3,NULLIF($4,''),NULLIF($5,''),$6) ON CONFLICT(slug) DO NOTHING`, d.Source, publisher, "https://"+strings.Split(d.Host, "|")[0], inst.DataURL, inst.RightsURL, s.batch.Version); err != nil {
		return "", "", err
	}
	if err := s.tx.QueryRow(s.ctx, `SELECT id::text FROM sources WHERE slug=$1 AND is_active`, d.Source).Scan(&sid); err != nil {
		return "", "", err
	}
	var id, place, status string
	err := s.tx.QueryRow(s.ctx, `SELECT id::text,coalesce(place_id::text,''),status FROM institutions WHERE slug=$1 FOR UPDATE`, d.Slug).Scan(&id, &place, &status)
	created := errors.Is(err, pgx.ErrNoRows)
	if err != nil && !created {
		return "", "", err
	}
	if status == "archived" {
		return "", "", errors.New("institution archived; not reactivating")
	}
	if created {
		var duplicate bool
		if err = s.tx.QueryRow(s.ctx, `SELECT EXISTS(SELECT 1 FROM institutions WHERE normalized_name=$1)`, normalize(inst.Name)).Scan(&duplicate); err != nil {
			return "", "", err
		}
		if duplicate {
			return "", "", errors.New("institution name already exists under another slug; review crosswalk")
		}
		rows, e := s.tx.Query(s.ctx, `SELECT id::text FROM places WHERE normalized_name=$1 AND country_code=$2 LIMIT 2`, normalize(inst.City), inst.Country)
		if e != nil {
			return "", "", e
		}
		places, e := pgx.CollectRows(rows, pgx.RowTo[string])
		if e != nil {
			return "", "", e
		}
		if len(places) > 1 {
			return "", "", errors.New("ambiguous city identity")
		}
		if len(places) == 1 {
			place = places[0]
		} else if e = s.tx.QueryRow(s.ctx, `INSERT INTO places(name,normalized_name,country_code) VALUES($1,$2,$3) RETURNING id::text`, inst.City, normalize(inst.City), inst.Country).Scan(&place); e != nil {
			return "", "", e
		}
		kind := "museum"
		if inst.ID == "beyeler" {
			kind = "foundation"
		}
		e = s.tx.QueryRow(s.ctx, `INSERT INTO institutions(slug,name,normalized_name,place_id,website_url,kind,status,description)
 VALUES($1,$2,$3,$4,$5,$6,'review','Selected museum collection records with official-source citations. Holdings do not establish current display or ownership.') RETURNING id::text`, d.Slug, inst.Name, normalize(inst.Name), place, d.Website, kind).Scan(&id)
		if e != nil {
			return "", "", e
		}
		s.report.CreatedMuseums++
		// A city-level museum venue enables geography facets. This is not a
		// gallery/room assignment, ticketing promise or current display claim.
		if _, e = s.tx.Exec(s.ctx, `INSERT INTO institution_venues(institution_id,slug,name,place_id,visit_url,source_url,checked_at,status)
 VALUES($1,$2,$3,$4,$5,$5,$6,'review')`, id, d.Slug+"-main", inst.Name, place, d.Website, s.checked); e != nil {
			return "", "", e
		}
	} else {
		s.report.ReusedMuseums++
	}
	if _, err = s.tx.Exec(s.ctx, `INSERT INTO source_institutions(source_id,institution_id) VALUES($1,$2) ON CONFLICT DO NOTHING`, sid, id); err != nil {
		return "", "", err
	}
	if _, err = s.tx.Exec(s.ctx, `INSERT INTO source_connector_config(source_id,metadata_policy,image_policy) VALUES($1,'reviewed_offline_evidence','manual_review') ON CONFLICT DO NOTHING`, sid); err != nil {
		return "", "", err
	}
	for _, kind := range []string{"owner", "museum"} {
		if _, err = s.tx.Exec(s.ctx, `INSERT INTO curated_collections(institution_id,curator_kind,title,status) VALUES($1,$2,$3,'review') ON CONFLICT DO NOTHING`, id, kind, map[string]string{"owner": "My must-see works", "museum": "Museum-designated highlights"}[kind]); err != nil {
			return "", "", err
		}
	}
	policyURL := inst.RightsURL
	if policyURL == "" {
		policyURL = d.Website
	}
	if err = s.cite("institution", id, "research_image_policy", sid, inst.ID, policyURL, inst.Rights+" No images downloaded or licensed by this import. Metadata access: "+inst.DataRoute); err != nil {
		return "", "", err
	}
	outcome := "skipped"
	if created {
		outcome = "created"
	}
	err = s.audit("institution:"+inst.ID, raw, d, outcome, "institution", id, "Reviewed institution geography; no display claim; connectors disabled.")
	return id, sid, err
}

// Each branch uses an exact identity index. Never merge solely by artwork title:
// two Annunciations, multiple Water Lilies, aliases and panels are not equivalent.
const europeanMatchSQL = `SELECT id::text FROM artworks WHERE id IN (
 SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=$1 AND external_id=$2
 UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=$3
 UNION SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=$3
 UNION SELECT id FROM artworks WHERE current_institution_id=$4 AND accession_number=$5 AND $5<>''
) LIMIT 3`

func (s europeanImport) work(w europeanWork, raw json.RawMessage, artist, inst, sid string, idef europeanInstitution) error {
	workType := w.WorkType
	if workType == "" {
		workType = "painting"
	}
	switch workType {
	case "painting", "drawing", "watercolor", "print", "fresco", "manuscript_illumination":
	default:
		return errors.New("unsupported artwork type")
	}
	date, err := europeanWorkDate(w)
	if err != nil {
		return err
	}
	role, err := europeanRole(w)
	if err != nil {
		return err
	}
	if role != "primary" || w.Attribution != "" {
		s.report.QualifiedWorks++
	}
	if date.Precision == "unknown" {
		s.report.UnknownDates++
	}
	scheme, objectID := europeanIdentity(w)
	rows, err := s.tx.Query(s.ctx, europeanMatchSQL, scheme, objectID, w.URL, inst, w.Accession)
	if err != nil {
		return err
	}
	matches, err := pgx.CollectRows(rows, pgx.RowTo[string])
	if err != nil {
		return err
	}
	if len(matches) > 1 {
		return errors.New("ambiguous exact object identity; manual reconciliation required")
	}
	var id string
	outcome := "skipped"
	note := "Official collection metadata; attribution follows named catalogue, not an independent authenticity determination. Holdings are not ownership or current display."
	creatorNote := "Attribution: " + role
	if artist == "" {
		creatorNote = "Source-level creator: " + w.UnlinkedCreatorLabel + ". No artist authority has been linked."
	}
	for _, part := range []string{w.Notes, creatorNote, w.Attribution} {
		if part != "" {
			note += " " + part
		}
	}
	if w.Owner != "" {
		note += " Recorded owner: " + w.Owner + "."
	}
	if w.Custody != "" {
		note += " Custody: " + w.Custody + "."
	}
	if w.Collection != "" {
		note += " Collection credit: " + w.Collection + "."
	}
	if date.Precision == "unknown" {
		note += " Creation interval intentionally unknown, pending review."
	}
	if date.Precision == "decade" || date.Precision == "century" {
		note += " Full source decade/century used as a conservative envelope; late qualifier retained in date display."
	}
	if len(matches) == 0 {
		description := note
		if w.Description != "" {
			description = w.Description
		}
		idSlug := "europe-" + w.Institution + "-" + checksum([]byte(w.URL))[:12] + "-" + slug(w.Title)
		locationText := idef.Name
		if idef.City != "" && !strings.HasSuffix(normalize(idef.Name), " "+normalize(idef.City)) {
			locationText += ", " + idef.City
		}
		err = s.tx.QueryRow(s.ctx, `INSERT INTO artworks(slug,title,alternate_title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,
 work_type,description_md,creation_place_unknown_reason,current_location_text,accession_number,location_checked_at,status,created_by,updated_by)
 VALUES($1,$2,NULLIF($3,''),$4,$5,$6,$7,$8,$14,$9,'Creation place not established by this research.',$10,NULLIF($11,''),$12,'review',$13,$13) RETURNING id::text`,
			idSlug, w.Title, strings.Join(w.Aliases, "; "), normalize(w.Title), w.DateDisplay, date.First, date.Last, date.Precision, description, locationText, w.Accession, s.checked, europeanActor, workType).Scan(&id)
		if err != nil {
			return err
		}
		if artist != "" {
			if _, err = s.tx.Exec(s.ctx, `INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES($1,$2,$3,NULLIF($4,''))`, id, artist, role, w.Attribution); err != nil {
				return err
			}
		}
		if s.batch.AllowUnlinkedCreators {
			if _, err = s.tx.Exec(s.ctx, `UPDATE artworks SET unlinked_creator_label=NULLIF($2,''),cultural_context=NULLIF($3,''),object_form=NULLIF($4,'') WHERE id=$1`, id, w.UnlinkedCreatorLabel, w.CulturalContext, w.ObjectForm); err != nil {
				return err
			}
		}
		s.report.CreatedWorks++
		outcome = "created"
	} else {
		id = matches[0]
		var valid bool
		if artist == "" {
			err = s.tx.QueryRow(s.ctx, `SELECT a.status<>'archived' AND (a.current_institution_id IS NULL OR a.current_institution_id=$2)
 AND a.unlinked_creator_label=$3 AND a.cultural_context IS NOT DISTINCT FROM NULLIF($4,'') AND a.object_form=$5
 AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id)
 FROM artworks a WHERE a.id=$1 FOR UPDATE`, id, inst, w.UnlinkedCreatorLabel, w.CulturalContext, w.ObjectForm).Scan(&valid)
		} else {
			err = s.tx.QueryRow(s.ctx, `SELECT a.status<>'archived' AND (a.current_institution_id IS NULL OR a.current_institution_id=$2)
 AND EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id AND aa.artist_id=$3 AND aa.attribution_role=$4)
 AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id AND (aa.artist_id<>$3 OR aa.attribution_role<>$4))
 FROM artworks a WHERE a.id=$1 FOR UPDATE`, id, inst, artist, role).Scan(&valid)
		}
		if err != nil {
			return err
		}
		if !valid {
			return errors.New("existing artist/attribution/holding/status conflicts; existing record untouched")
		}
		s.report.ReusedWorks++
	}
	if _, err = s.tx.Exec(s.ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
 VALUES('artwork',$1,$2,$3,$4,$5,$6) ON CONFLICT(scheme,external_id) DO NOTHING`, id, scheme, objectID, w.URL, sid, s.checked); err != nil {
		return err
	}
	var heldAt *string
	err = s.tx.QueryRow(s.ctx, `SELECT institution_id::text FROM artwork_location_assertions WHERE artwork_id=$1 AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL`, id).Scan(&heldAt)
	if errors.Is(err, pgx.ErrNoRows) {
		context := "collection"
		if w.Custody != "" {
			context = "loan"
		}
		var updated *time.Time
		if w.UpdatedOn != "" {
			v, e := time.Parse("2006-01-02", w.UpdatedOn)
			if e != nil || v.After(s.checked) {
				return errors.New("invalid source update date")
			}
			updated = &v
		}
		_, err = s.tx.Exec(s.ctx, `INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,source_updated_at,review_state)
 VALUES($1,'holding',$2,$3,$4,$5,$6,$7,$8,'accepted')`, id, inst, context, sid, w.URL, note, s.checked, updated)
	} else if err == nil && *heldAt != inst {
		return errors.New("conflicting accepted holding; no automatic replacement")
	}
	if err != nil {
		return err
	}
	access := w.Access
	if access == "" {
		access = "Official object record from reviewed inventory"
	}
	recordID := scheme + ":" + objectID
	updatedOn := w.UpdatedOn
	if updatedOn == "" {
		updatedOn = "unknown (not substituted with retrieval date)"
	}
	if err = s.cite("artwork", id, "research_record", sid, recordID, w.URL, note+" Source date: "+w.DateDisplay+". Access: "+access+". Source update: "+updatedOn); err != nil {
		return err
	}
	if w.ConflictingSource != "" {
		if !europeanAllowedURL(s.batch.Definitions, w.Institution, w.ConflictingSource) {
			return errors.New("unapproved conflicting source URL")
		}
		if err = s.cite("artwork", id, "display_conflict", sid, recordID, w.ConflictingSource, w.Notes+" No display assertion imported."); err != nil {
			return err
		}
	}
	if s.batch.Schema == 2 {
		changed, e := s.details(w, id, inst, sid, recordID, note)
		if e != nil {
			return e
		}
		if changed && outcome != "created" {
			outcome = "updated"
			s.report.EnrichedWorks++
		}
	}
	if err = s.audit(recordID, raw, map[string]any{"date": date, "role": role, "institution_id": inst, "artist_id": artist, "image_downloaded": false}, outcome, "artwork", id, note); err != nil {
		return err
	}
	s.report.Works = append(s.report.Works, EuropeanWorkResult{w.Painter, w.Title, s.batch.Definitions[w.Institution].Slug, w.URL, id, outcome, role, date.Precision})
	return nil
}

func (s europeanImport) pissarro(id, sid string) error {
	// Source supports working in France and Impressionism, not citizenship.
	// Fill unreviewed missing primary classifications only; preserve subsequent
	// editorial decisions and other associated movements.
	var previouslyReviewed bool
	if err := s.tx.QueryRow(s.ctx, `SELECT EXISTS(SELECT 1 FROM import_records WHERE import_job_id=$1 AND source_record_id='artist:pissarro-classification')`, s.job).Scan(&previouslyReviewed); err != nil {
		return err
	}
	if previouslyReviewed {
		// Even an intentionally cleared classification is an editorial decision.
		// Do not repopulate it on replay of this already reviewed snapshot.
		return nil
	}
	var status string
	if err := s.tx.QueryRow(s.ctx, `SELECT status FROM artists WHERE id=$1`, id).Scan(&status); err != nil {
		return err
	}
	note := "National Gallery, Camille Pissarro biography (n.d.), accessed 2026-09-09: Impressionist; lived/worked mainly in the Paris area. France is an active-in relationship, not nationality or birthplace."
	changes := int64(0)
	if status == "review" || status == "draft" {
		tag, err := s.tx.Exec(s.ctx, `INSERT INTO artist_movements(artist_id,movement_id,role)
 SELECT $1,id,'primary' FROM movements WHERE slug='impressionism' AND status<>'archived'
 AND (SELECT movement_review_state FROM artists WHERE id=$1)='not_reviewed'
 AND NOT EXISTS(SELECT 1 FROM artist_movements WHERE artist_id=$1 AND role='primary')
 ON CONFLICT(artist_id,movement_id) DO UPDATE SET role='primary' WHERE artist_movements.role='associated'`, id)
		if err != nil {
			return err
		}
		changes += tag.RowsAffected()
		tag, err = s.tx.Exec(s.ctx, `INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note)
 SELECT $1,'FR','active',true,$2 WHERE NOT EXISTS(SELECT 1 FROM artist_countries WHERE artist_id=$1)
 AND (SELECT geography_review_state FROM artists WHERE id=$1)='not_reviewed'`, id, note)
		if err != nil {
			return err
		}
		changes += tag.RowsAffected()
		if changes > 0 {
			_, err = s.tx.Exec(s.ctx, `UPDATE artists SET movement_review_state=CASE WHEN EXISTS(SELECT 1 FROM artist_movements WHERE artist_id=$1 AND role='primary') THEN 'classified' ELSE movement_review_state END,
 geography_review_state=CASE WHEN EXISTS(SELECT 1 FROM artist_countries WHERE artist_id=$1) THEN 'classified' ELSE geography_review_state END,
 revision=revision+1,updated_at=now(),updated_by=$2 WHERE id=$1`, id, europeanActor)
			if err != nil {
				return err
			}
		}
	} else {
		s.report.Warnings = append(s.report.Warnings, "Pissarro classifications not changed: painter is not in draft/review.")
	}
	s.report.ClassificationChanges = int(changes)
	if err := s.cite("artist", id, "research_classification", sid, "pissarro-biography-2026-09-09", pissarroBiography, note); err != nil {
		return err
	}
	outcome := "skipped"
	if changes > 0 {
		outcome = "updated"
	}
	return s.audit("artist:pissarro-classification", map[string]string{"url": pissarroBiography, "note": note}, map[string]string{"movement": "impressionism", "country_relationship": "active:FR"}, outcome, "artist", id, note)
}
