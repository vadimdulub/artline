package ingest

// An offline, owner-requested Russian Museum selection. No crawling, image
// licensing, publication or inferred nationality takes place in this importer.
import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type RussianAuthor struct {
	QID                 string `json:"qid"`
	Name                string `json:"name"`
	Native              string `json:"native_name"`
	URL                 string `json:"url"`
	Description         string `json:"description"`
	AffiliationEvidence string `json:"affiliation_evidence"`
	Birth               *int   `json:"birth"`
	Death               *int   `json:"death"`
	Start               int    `json:"start"`
	End                 int    `json:"end"`
}
type RussianChunk struct {
	Source   string                   `json:"source"`
	Accessed string                   `json:"accessed_on"`
	Authors  map[string]RussianAuthor `json:"authors"`
	Works    []json.RawMessage        `json:"works"`
}

var russianObjectURL = regexp.MustCompile(`^https://rusmuseumvrm\.ru/data/collections/[a-zA-Z0-9_./-]+/index(?:_[0-9]+)?\.php$`)

func ValidateRussianSession(data []byte, sha string) error {
	_, err := validateRussian(data, sha)
	return err
}

func validateRussian(data []byte, sha string) (RussianChunk, error) {
	var m RussianChunk
	if !resolvedSHA.MatchString(sha) || checksum(data) != sha || len(data) > 8<<20 {
		return m, errors.New("Russian snapshot checksum/size mismatch")
	}
	if err := json.Unmarshal(data, &m); err != nil {
		return m, err
	}
	if m.Source != "russian-painters-20260913" || len(m.Works) < 1 || len(m.Works) > 250 || len(m.Authors) < 1 || len(m.Authors) > 250 {
		return m, errors.New("invalid Russian batch shape")
	}
	checked, err := time.Parse("2006-01-02", m.Accessed)
	if err != nil || checked.After(time.Now()) {
		return m, errors.New("invalid access date")
	}
	for q, a := range m.Authors {
		validActivity := a.Start >= 1100 && a.End <= 1970 && a.Start <= a.End
		unlinkedCandidate := a.Start == 0 && a.End == 0
		if q != a.QID || !bulkQID.MatchString(q) || strings.TrimSpace(a.Name) == "" || a.Native == "" || !strings.HasPrefix(a.URL, "https://rusmuseumvrm.ru/reference/classifier/author/") || !strings.HasSuffix(a.URL, "/index.php") || a.AffiliationEvidence == "" || (!validActivity && !unlinkedCandidate) {
			return m, fmt.Errorf("invalid Russian authority %s", q)
		}
		if a.Birth != nil && a.Death != nil && *a.Birth > *a.Death {
			return m, errors.New("reversed authority life dates")
		}
	}
	seen := map[string]bool{}
	for _, raw := range m.Works {
		var w europeanWork
		if err = json.Unmarshal(raw, &w); err != nil {
			return m, err
		}
		if _, err = europeanWorkDate(w); err != nil {
			return m, err
		}
		if w.CreationDate == nil {
			return m, errors.New("explicit source creation date structure required")
		}
		if m.Authors[w.Painter].Start == 0 && w.CreationDate.Precision != "unknown" {
			return m, errors.New("Unlinked candidate requires unknown dates and retained source wording")
		}
		if m.Authors[w.Painter].QID == "" || w.Institution != "russian-session-museum" || !russianObjectURL.MatchString(w.URL) || strings.Contains(w.URL, "/../") || w.ObjectID != strings.TrimPrefix(w.URL, "https://rusmuseumvrm.ru") || seen[w.URL] || w.Title == "" || w.AttributionRole != "primary" || w.Attribution != "" || w.MuseumHighlightURL != "" || w.UnlinkedCreatorLabel != "" || w.Description == "" {
			return m, fmt.Errorf("invalid Russian object %s", w.URL)
		}
		if w.WorkType != "painting" && w.WorkType != "drawing" && w.WorkType != "print" {
			return m, errors.New("unreviewed Russian work type")
		}
		seen[w.URL] = true
	}
	return m, nil
}

func ImportRussianSession(ctx context.Context, pool *pgxpool.Pool, data []byte, sha string, apply bool) (BulkReport, error) {
	out := BulkReport{EuropeanImportReport: EuropeanImportReport{Snapshot: sha, Warnings: []string{}, Works: []EuropeanWorkResult{}}}
	m, err := validateRussian(data, sha)
	if err != nil {
		return out, err
	}
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.Serializable})
	if err != nil {
		return out, err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(2026091313)`); err != nil {
		return out, err
	}
	if _, err = tx.Exec(ctx, `SET LOCAL statement_timeout='30s'; SET LOCAL lock_timeout='5s'`); err != nil {
		return out, err
	}
	key := m.Source + "-" + sha
	var status string
	err = tx.QueryRow(ctx, `SELECT id::text,status FROM import_jobs WHERE idempotency_key=$1`, key).Scan(&out.JobID, &status)
	if err == nil {
		if status != "needs_review" {
			return out, errors.New("conflicting Russian import job")
		}
		out.Applied = apply
		out.Replayed = true
		return out, tx.Rollback(ctx)
	}
	if !errors.Is(err, pgx.ErrNoRows) {
		return out, err
	}
	if _, err = tx.Exec(ctx, `INSERT INTO editor_accounts(user_id,display_name,role) VALUES($1,'Local catalogue research importer (review only)','owner') ON CONFLICT DO NOTHING`, europeanActor); err != nil {
		return out, err
	}
	if _, err = tx.Exec(ctx, `INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES('russian-painters-20260913','Russian Museum — selected Russian painter catalogue facts','collection_page','https://rusmuseumvrm.ru','https://rusmuseumvrm.ru/terms/index.php?lang=en') ON CONFLICT DO NOTHING`); err != nil {
		return out, err
	}
	var source string
	if err = tx.QueryRow(ctx, `SELECT id::text FROM sources WHERE slug='russian-painters-20260913' AND is_active`).Scan(&source); err != nil {
		return out, err
	}
	if err = tx.QueryRow(ctx, `INSERT INTO import_jobs(source_id,requested_by,adapter_version,query_json,status,idempotency_key) VALUES($1,$2,'russian-session-v1',$3,'running',$4) RETURNING id::text`, source, europeanActor, rawJSON(map[string]string{"sha256": sha}), key).Scan(&out.JobID); err != nil {
		return out, err
	}
	checked, _ := time.Parse("2006-01-02", m.Accessed)
	batch := europeanBatch{Schema: 2, Version: "russian-session-v1", Definitions: map[string]europeanDefinition{"russian-session-museum": {"state-russian-museum", "russian-painters-20260913", "https://rusmuseum.ru/", "rusmuseumvrm.ru"}}}
	s := europeanImport{ctx: ctx, tx: tx, checked: checked, job: out.JobID, report: &out.EuropeanImportReport, batch: batch}
	inst := europeanInstitution{ID: "russian-session-museum", Name: "State Russian Museum", City: "Saint Petersburg", Country: "RU", DataURL: "https://rusmuseumvrm.ru/collections/index.php", DataRoute: "Bounded collection-specific listing facts and exact named-creator authority crosswalk; metadata only.", Rights: "Museum photographs require written permission. No image licence is inferred from metadata.", RightsURL: "https://rusmuseumvrm.ru/terms/index.php?lang=en"}
	iid, sid, err := s.institution(inst, rawJSON(inst))
	if err != nil {
		return out, err
	}
	ids := map[string]string{}
	for q, a := range m.Authors {
		var id string
		authorOutcome := "skipped"
		err = tx.QueryRow(ctx, `SELECT a.id::text FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='wikidata' AND e.external_id=$1 AND a.status<>'archived' FOR UPDATE OF a`, q).Scan(&id)
		// Reviewed exact authority IDs: MoMA P2174 and Tate P2741. Kliun's
		// conflicting birth dates remain separately cited; no lifespan is changed.
		crosswalks := map[string][3]string{"Q270460": {"moma-person", "5066", "olga rozanova"}, "Q1343751": {"tate-person", "2181", "konstantin yuon"}, "Q1988310": {"moma-person", "13470", "ivan kliun"}}
		if cross, ok := crosswalks[q]; errors.Is(err, pgx.ErrNoRows) && ok {
			err = tx.QueryRow(ctx, `SELECT a.id::text FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme=$1 AND e.external_id=$2 WHERE a.normalized_name=$3 AND a.status<>'archived' AND NOT EXISTS(SELECT 1 FROM external_identifiers x WHERE x.entity_type='artist' AND x.entity_id=a.id AND x.scheme='wikidata') FOR UPDATE OF a`, cross[0], cross[1], cross[2]).Scan(&id)
			if err == nil {
				_, err = tx.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',$1,'wikidata',$2,$3,$4,$5)`, id, q, "https://www.wikidata.org/wiki/"+q, source, checked)
			}
		}
		if errors.Is(err, pgx.ErrNoRows) {
			if a.Start == 0 {
				// Preserve real named-creator objects without inventing an artist
				// lifespan or activity interval merely to satisfy timeline columns.
				ids[q] = ""
				s.batch.AllowUnlinkedCreators = true
				continue
			}
			var collision bool
			if err = tx.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artists WHERE normalized_name=ANY($1)) OR EXISTS(SELECT 1 FROM external_identifiers WHERE scheme='wikidata' AND external_id=$2)`, []string{normalize(a.Name), normalize(a.Native)}, q).Scan(&collision); err != nil {
				return out, err
			}
			if collision {
				// Distinct full-name authorities: Vasily Petrovich (1835–1909)
				// and the existing Vasily Vasilyevich (1842–1904) Vereshchagin.
				// Keep the source-backed homonyms separate, with QID-qualified slugs.
				vereshchagin := q == "Q4107761" && a.Native == "Василий Петрович Верещагин" && a.Birth != nil && a.Death != nil && *a.Birth == 1835 && *a.Death == 1909
				sokolov := q == "Q3388979" && a.Native == "Пётр Петрович Соколов" && a.Birth != nil && a.Death != nil && *a.Birth == 1821 && *a.Death == 1899
				if !vereshchagin && !sokolov {
					return out, fmt.Errorf("creator authority collision %s (%s)", a.Name, q)
				}
				var distinct bool
				if vereshchagin {
					err = tx.QueryRow(ctx, `SELECT count(*)=1 AND bool_and(birth_year=1842 AND death_year=1904) FROM artists WHERE normalized_name=$1`, normalize(a.Name)).Scan(&distinct)
				}
				if sokolov {
					err = tx.QueryRow(ctx, `SELECT count(*)=1 AND bool_and(EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' AND e.external_id='Q1994515')) FROM artists a WHERE normalized_name=$1`, normalize(a.Name)).Scan(&distinct)
				}
				if err != nil || !distinct {
					return out, errors.New("unreviewed source-authority homonym")
				}
			}
			display := fmt.Sprintf("Documented works %d–%d (not lifespan)", a.Start, a.End)
			if err = tx.QueryRow(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,active_start_year,active_end_year,activity_display,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,created_by,updated_by) VALUES($1,$2,$2,$3,$4,$5,$6,$4,$5,$6,'activity','review',$7,$7) RETURNING id::text`, slug(a.Name)+"-"+strings.ToLower(q), a.Name, normalize(a.Name), a.Start, a.End, display, europeanActor).Scan(&id); err != nil {
				return out, err
			}
			if a.Birth != nil && a.Death != nil {
				if _, err = tx.Exec(ctx, `UPDATE artists SET birth_year=$2::integer,death_year=$3::integer,birth_display=($2::integer)::text,death_display=($3::integer)::text,birth_precision='exact',death_precision='exact',timeline_start_year=$2::integer,timeline_end_year=$3::integer,timeline_display=($2::integer)::text||'–'||($3::integer)::text,timeline_basis='life' WHERE id=$1`, id, *a.Birth, *a.Death); err != nil {
					return out, err
				}
			}
			if _, err = tx.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',$1,'wikidata',$2,$3,$4,$5)`, id, q, "https://www.wikidata.org/wiki/"+q, source, checked); err != nil {
				return out, err
			}
			out.CreatedArtists++
			authorOutcome = "created"
		} else if err != nil {
			return out, err
		}
		ids[q] = id
		if q == "Q1988310" {
			if err = s.cite("artist", id, "life_date_conflict", sid, q, "https://www.wikidata.org/wiki/"+q, "Exact MoMA artist ID 13470 reconciles the identity. Wikidata records birth 1873; the existing MoMA-derived profile records 1878. Existing lifespan retained pending editorial review."); err != nil {
				return out, err
			}
		}
		if _, err = tx.Exec(ctx, `INSERT INTO artist_aliases(artist_id,alias,normalized_alias,language_code,alias_type) VALUES($1,$2,$3,'ru','native_name') ON CONFLICT DO NOTHING`, id, a.Native, normalize(a.Native)); err != nil {
			return out, err
		}
		if _, err = tx.Exec(ctx, `INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES($1,'RU','cultural_affiliation',false,$2) ON CONFLICT DO NOTHING`, id, a.AffiliationEvidence+". This is a documented Russian association, not an exclusive nationality or birthplace claim."); err != nil {
			return out, err
		}
		if err = s.cite("artist", id, "russian_session_creator_authority", sid, q, a.URL, "Exact full museum name matched to "+q+". "+a.AffiliationEvidence+". Authority description: "+a.Description+". No exclusive nationality or complete biography inferred."); err != nil {
			return out, err
		}
		if err = s.cite("artist", id, "russian_session_wikidata_evidence", sid, q, "https://www.wikidata.org/wiki/"+q, "CC0 authority facts; native name: "+a.Native+". "+a.AffiliationEvidence); err != nil {
			return out, err
		}
		if err = s.audit("artist:"+q, rawJSON(a), a, authorOutcome, "artist", id, "Exact source authority recorded; newly created profiles remain in review and existing profiles retain their editorial fields."); err != nil {
			return out, err
		}
	}
	for _, raw := range m.Works {
		var w europeanWork
		json.Unmarshal(raw, &w)
		artistID := ids[w.Painter]
		if artistID == "" {
			a := m.Authors[w.Painter]
			w.UnlinkedCreatorLabel = a.Native
			w.CulturalContext = a.AffiliationEvidence
			w.Notes += " Named creator retained without a timeline profile. Authority candidate: https://www.wikidata.org/wiki/" + w.Painter + "; museum creator: " + a.URL
			w.Painter = ""
		}
		if err = s.work(w, raw, artistID, iid, sid, inst); err != nil {
			return out, fmt.Errorf("Russian object %s: %w", w.URL, err)
		}
	}
	if _, err = tx.Exec(ctx, `UPDATE import_jobs SET status='needs_review',completed_at=now(),total_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1),accepted_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1) WHERE id=$1`, out.JobID); err != nil {
		return out, err
	}
	if !apply {
		return out, tx.Rollback(ctx)
	}
	if err = tx.Commit(ctx); err != nil {
		return out, err
	}
	out.Applied = true
	return out, nil
}
