package ingest

// Explicit, offline, bounded catalogue ingestion. Source batches are immutable;
// each <=1,000-object chunk is atomic and replayable. It is not a public API.
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
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

const ngaBulkRevision = "f088836026d09d0d25001814fba0f84d757ebe62"

type bulkAuthor struct {
	ID, Name, QID string
	SortName      string          `json:"sort_name"`
	DateDisplay   string          `json:"date_display"`
	SourceBegin   string          `json:"source_begin"`
	SourceEnd     string          `json:"source_end"`
	ActivityStart int             `json:"activity_start"`
	ActivityEnd   int             `json:"activity_end"`
	URL           string          `json:"source_url"`
	Raw           json.RawMessage `json:"raw"`
}
type bulkManifest struct {
	Schema           int    `json:"schema_version"`
	Accessed         string `json:"accessed_on"`
	Source, Revision string
	Authors          map[string]bulkAuthor
	Institutions     []json.RawMessage
	Works            []json.RawMessage
}
type BulkReport struct {
	EuropeanImportReport
	CreatedArtists int  `json:"created_artists"`
	Replayed       bool `json:"replayed"`
}

var bulkID = regexp.MustCompile(`^[0-9]{1,12}$`)
var bulkQID = regexp.MustCompile(`^Q[1-9][0-9]*$`)

// NormalizeAuthorityName shares exact normalization between offline preflight
// and the transactional identity check. It is not a fuzzy matching operation.
func NormalizeAuthorityName(name string) string { return normalize(name) }

func validateBulk(data []byte, sha string) (bulkManifest, error) {
	var m bulkManifest
	if len(data) > 32<<20 || len(sha) != 64 || checksum(data) != sha {
		return m, errors.New("bulk snapshot checksum/size mismatch")
	}
	if e := json.Unmarshal(data, &m); e != nil {
		return m, e
	}
	if m.Schema != 3 || m.Source != "nga" || m.Revision != ngaBulkRevision || len(m.Works) < 1 || len(m.Works) > 1000 || len(m.Institutions) != 1 || len(m.Authors) < 1 || len(m.Authors) > 1000 {
		return m, errors.New("unapproved bulk source or batch shape")
	}
	checked, e := time.Parse("2006-01-02", m.Accessed)
	if e != nil || checked.After(time.Now()) {
		return m, errors.New("invalid access date")
	}
	for k, a := range m.Authors {
		if k != a.ID || !bulkID.MatchString(a.ID) || strings.TrimSpace(a.Name) == "" || len(a.Name) > 500 || a.ActivityStart < 1100 || a.ActivityEnd > 1970 || a.ActivityStart > a.ActivityEnd || a.QID != "" && !bulkQID.MatchString(a.QID) || a.URL != "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/"+m.Revision+"/data/constituents.csv" {
			return m, fmt.Errorf("invalid source creator %s", k)
		}
	}
	seen := map[string]bool{}
	for _, r := range m.Works {
		var w europeanWork
		if e = json.Unmarshal(r, &w); e != nil {
			return m, e
		}
		d, e := europeanWorkDate(w)
		if e != nil || catalog.CreationScope(d.First, d.Last, d.Precision) != "eligible" {
			return m, fmt.Errorf("ineligible source date %s", w.ObjectID)
		}
		if !bulkID.MatchString(w.ObjectID) || seen[w.ObjectID] || w.Institution != "nga" || m.Authors[w.Painter].ID == "" || w.URL != "https://www.nga.gov/collection/art-object-page."+w.ObjectID+".html" || w.Accession == "" || strings.TrimSpace(w.Title) == "" || len(w.Description) > 40000 || w.MuseumHighlightURL != "" || w.AttributionRole != "primary" || (w.WorkType != "painting" && w.WorkType != "drawing" && w.WorkType != "print") {
			return m, fmt.Errorf("invalid source object %s", w.ObjectID)
		}
		seen[w.ObjectID] = true
	}
	return m, nil
}

func ImportBulkCatalogue(ctx context.Context, pool *pgxpool.Pool, data []byte, sha string, apply bool) (BulkReport, error) {
	out := BulkReport{EuropeanImportReport: EuropeanImportReport{Snapshot: checksum(data), Warnings: []string{}, Works: []EuropeanWorkResult{}}}
	m, e := validateBulk(data, sha)
	if e != nil {
		return out, e
	}
	checked, _ := time.Parse("2006-01-02", m.Accessed)
	tx, e := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.Serializable})
	if e != nil {
		return out, e
	}
	defer tx.Rollback(ctx)
	if _, e = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(2026090959)`); e != nil {
		return out, e
	}
	if _, e = tx.Exec(ctx, `SET LOCAL statement_timeout='30s'`); e != nil {
		return out, e
	}
	key := "bulk-nga-" + sha
	var status string
	e = tx.QueryRow(ctx, `SELECT id::text,status FROM import_jobs WHERE idempotency_key=$1`, key).Scan(&out.JobID, &status)
	if e == nil {
		if status != "needs_review" {
			return out, errors.New("unexpected existing bulk job state")
		}
		out.Applied = apply
		out.Replayed = true
		return out, tx.Rollback(ctx)
	}
	if !errors.Is(e, pgx.ErrNoRows) {
		return out, e
	}
	if _, e = tx.Exec(ctx, `INSERT INTO editor_accounts(user_id,display_name,role) VALUES($1,'Local catalogue research importer (review only)','owner') ON CONFLICT DO NOTHING`, europeanActor); e != nil {
		return out, e
	}
	if _, e = tx.Exec(ctx, `INSERT INTO sources(slug,name,source_type,base_url,terms_url,adapter_key) VALUES('nga-bulk-catalogue','National Gallery of Art — bounded CC0 catalogue','museum_api','https://www.nga.gov','https://github.com/NationalGalleryOfArt/opendata/blob/main/LICENSE','nga-bulk-v1') ON CONFLICT DO NOTHING`); e != nil {
		return out, e
	}
	var source string
	if e = tx.QueryRow(ctx, `SELECT id::text FROM sources WHERE slug='nga-bulk-catalogue' AND is_active`).Scan(&source); e != nil {
		return out, e
	}
	if e = tx.QueryRow(ctx, `INSERT INTO import_jobs(source_id,requested_by,adapter_version,query_json,status,idempotency_key) VALUES($1,$2,'nga-bulk-v1',$3,'running',$4) RETURNING id::text`, source, europeanActor, rawJSON(map[string]string{"sha256": sha, "revision": m.Revision}), key).Scan(&out.JobID); e != nil {
		return out, e
	}
	batch := europeanBatch{Schema: 2, Version: "nga-bulk-v1", Definitions: map[string]europeanDefinition{"nga": {"national-gallery-of-art", "nga-open-data", "https://www.nga.gov", "www.nga.gov"}}}
	s := europeanImport{ctx: ctx, tx: tx, checked: checked, job: out.JobID, report: &out.EuropeanImportReport, batch: batch}
	var inst europeanInstitution
	if e = json.Unmarshal(m.Institutions[0], &inst); e != nil {
		return out, e
	}
	if inst.ID != "nga" || inst.Country != "US" || inst.City != "Washington, DC" || inst.Name != "National Gallery of Art" {
		return out, errors.New("unexpected NGA institution identity")
	}
	instID, sid, e := s.institution(inst, m.Institutions[0])
	if e != nil {
		return out, e
	}
	authorIDs := map[string]string{}
	authorKeys := make([]string, 0, len(m.Authors))
	for k := range m.Authors {
		authorKeys = append(authorKeys, k)
	}
	sort.Strings(authorKeys)
	for _, k := range authorKeys {
		id, created, e := s.bulkAuthor(m.Authors[k], sid)
		if e != nil {
			return out, e
		}
		authorIDs[k] = id
		if created {
			out.CreatedArtists++
		}
	}
	for _, raw := range m.Works {
		var w europeanWork
		json.Unmarshal(raw, &w)
		if e = s.work(w, raw, authorIDs[w.Painter], instID, sid, inst); e != nil {
			return out, fmt.Errorf("NGA object %s: %w", w.ObjectID, e)
		}
		// Existing owner-authored descriptions remain intact. New objects already
		// received the museum description. Supplement only missing fields on review.
		if w.Description != "" {
			id := out.Works[len(out.Works)-1].ID
			if _, e = tx.Exec(ctx, `UPDATE artworks SET description_md=$2,revision=revision+1,updated_at=now() WHERE id=$1 AND status IN ('draft','review') AND (description_md IS NULL OR description_md='')`, id, w.Description); e != nil {
				return out, e
			}
			if e = s.cite("artwork", id, "catalogue_description", sid, w.ObjectID, w.URL, "Source: National Gallery of Art CC0 bulk metadata; source revision "+m.Revision+". Descriptive museum fields preserved; no current-display or masterpiece inference."); e != nil {
				return out, e
			}
		}
	}
	if _, e = tx.Exec(ctx, `UPDATE import_jobs SET status='needs_review',completed_at=now(),total_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1),accepted_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1) WHERE id=$1`, out.JobID); e != nil {
		return out, e
	}
	if !apply {
		out.Warnings = append(out.Warnings, "Preview rolled back all changes; UUIDs are provisional.")
		return out, tx.Rollback(ctx)
	}
	if e = tx.Commit(ctx); e != nil {
		return out, e
	}
	out.Applied = true
	return out, nil
}

func (s europeanImport) bulkAuthor(a bulkAuthor, sid string) (string, bool, error) {
	rows, e := s.tx.Query(s.ctx, `SELECT a.id::text FROM artists a WHERE a.id IN (SELECT entity_id FROM external_identifiers WHERE entity_type='artist' AND ((scheme='nga-constituent' AND external_id=$1) OR (scheme='wikidata' AND external_id=$2 AND $2<>''))) FOR UPDATE`, a.ID, a.QID)
	if e != nil {
		return "", false, e
	}
	ids, e := pgx.CollectRows(rows, pgx.RowTo[string])
	if e != nil {
		return "", false, e
	}
	if len(ids) > 1 {
		return "", false, fmt.Errorf("conflicting NGA/QID creator identity %s", a.ID)
	}
	created := false
	id := ""
	if len(ids) == 1 {
		id = ids[0]
		var conflict bool
		if e = s.tx.QueryRow(s.ctx, `SELECT status='archived' OR EXISTS(SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=$1 AND scheme='wikidata' AND external_id<>$2 AND $2<>'') FROM artists WHERE id=$1`, id, a.QID).Scan(&conflict); e != nil {
			return "", false, e
		}
		if conflict {
			return "", false, fmt.Errorf("archived/conflicting authority %s", a.ID)
		}
	} else {
		var collision bool
		if e = s.tx.QueryRow(s.ctx, `SELECT EXISTS(SELECT 1 FROM artists WHERE normalized_name=$1)`, normalize(a.Name)).Scan(&collision); e != nil {
			return "", false, e
		}
		if collision {
			// Reviewed NGA homonyms: 4866 is active c.1616, 37703 active
			// c.1530–1550. Separate source UUIDs and periods: do not merge.
			if a.ID == "37703" && a.Name == "Master CR" && a.SourceBegin == "1530" && a.SourceEnd == "1550" {
				var onlyReviewedHomonym bool
				if e = s.tx.QueryRow(s.ctx, `SELECT count(*)=1 AND bool_and(EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='nga-constituent' AND e.external_id='4866')) FROM artists a WHERE normalized_name=$1`, normalize(a.Name)).Scan(&onlyReviewedHomonym); e != nil {
					return "", false, e
				}
				collision = !onlyReviewedHomonym
			}
		}
		if collision {
			return "", false, fmt.Errorf("creator name requires explicit authority crosswalk: %s (%s)", a.Name, a.ID)
		}
		// Do not turn NGA search bounds or a missing death into a fabricated lifespan.
		// Activity is documented by this selected set of dated museum works.
		display := fmt.Sprintf("Documented works %d–%d (not lifespan)", a.ActivityStart, a.ActivityEnd)
		e = s.tx.QueryRow(s.ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,active_start_year,active_end_year,activity_display,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,created_by,updated_by)
 VALUES($1,$2,$3,$4,$5,$6,$7,$5,$6,$7,'activity','review',$8,$8) RETURNING id::text`, slug(a.Name)+"-nga-"+a.ID, a.Name, a.SortName, normalize(a.Name), a.ActivityStart, a.ActivityEnd, display, europeanActor).Scan(&id)
		if e != nil {
			return "", false, e
		}
		created = true
		// Only an unqualified closed numeric literal whose endpoints agree with the
		// source's person bounds is treated as life; all other wording stays cited.
		literal := regexp.MustCompile(`^(?:[^0-9,]+, )?(\d{4})\s*[-–]\s*(\d{4})$`).FindStringSubmatch(a.DateDisplay)
		if literal != nil && literal[1] == a.SourceBegin && literal[2] == a.SourceEnd {
			b, _ := strconv.Atoi(literal[1])
			d, _ := strconv.Atoi(literal[2])
			if b > 0 && d >= b && d-b <= 125 {
				if _, e = s.tx.Exec(s.ctx, `UPDATE artists SET birth_year=$2::int,death_year=$3::int,birth_display=($2::int)::text,death_display=($3::int)::text,timeline_start_year=$2::int,timeline_end_year=$3::int,timeline_display=$4,timeline_basis='life' WHERE id=$1`, id, b, d, a.DateDisplay); e != nil {
					return "", false, e
				}
			}
		}
	}
	for scheme, x := range map[string]string{"nga-constituent": a.ID, "wikidata": a.QID} {
		if x == "" {
			continue
		}
		if _, e = s.tx.Exec(s.ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,source_id,retrieved_at) VALUES('artist',$1,$2,$3,$4,$5) ON CONFLICT(scheme,external_id) DO NOTHING`, id, scheme, x, sid, s.checked); e != nil {
			return "", false, e
		}
	}
	if e = s.cite("artist", id, "catalogue_authority", sid, a.ID, a.URL, "NGA stable constituent ID "+a.ID+"; source display: "+a.DateDisplay+". Existing editorial identity and biography retained; new activity interval uses dated selected works, not invented life dates."); e != nil {
		return "", false, e
	}
	outcome := "skipped"
	if created {
		outcome = "created"
	}
	e = s.audit("artist:nga:"+a.ID, a, a, outcome, "artist", id, "Source authority; not a popularity designation.")
	return id, created, e
}
