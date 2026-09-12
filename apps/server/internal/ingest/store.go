package ingest

import (
	"context"
	"errors"
	"fmt"
	"net/url"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type Store struct{ Pool *pgxpool.Pool }
type source struct{ Key, Slug, Name, Base, Docs, Policy, Institution, City, Visit, Country string }

var sources = map[string]source{
	"uffizi":    {Key: "uffizi", Slug: "uffizi", Name: "Uffizi Galleries", Base: "https://www.uffizi.it", Docs: "https://www.uffizi.it/en/the-uffizi", Policy: "https://www.uffizi.it/en/professional-services/publications", Institution: "uffizi", City: "Florence", Country: "IT", Visit: "https://www.uffizi.it/en/the-uffizi"},
	"mam":       {Key: "mam", Slug: "museo-de-arte-moderno-mexico", Name: "Museo de Arte Moderno", Base: "https://mam.inba.gob.mx", Docs: "https://mam.inba.gob.mx/destacadas.html", Policy: "https://mam.inba.gob.mx", Institution: "museo-de-arte-moderno-mexico", City: "Mexico City", Country: "MX", Visit: "https://mam.inba.gob.mx"},
	"prado":     {Key: "prado", Slug: "museo-del-prado", Name: "Museo Nacional del Prado", Base: "https://www.museodelprado.es", Docs: "https://www.museodelprado.es/en/the-collection", Policy: "https://www.museodelprado.es/en/legal-notice", Institution: "museo-del-prado", City: "Madrid", Country: "ES", Visit: "https://www.museodelprado.es/en/visit-the-museum"},
	"wikidata":  {Key: "wikidata", Slug: "wikidata", Name: "Wikidata (CC0)", Base: "https://www.wikidata.org", Docs: "https://www.wikidata.org/wiki/Wikidata:Data_access", Policy: "https://www.wikidata.org/wiki/Wikidata:Licensing"},
	"pantheon":  {Key: "pantheon", Slug: "pantheon-2025", Name: "Pantheon 2025 — Datawheel (CC BY-SA 4.0)", Base: "https://pantheon.world", Docs: "https://pantheon.world/data/datasets", Policy: "https://pantheon.world/data/permissions"},
	"met":       {Key: "met", Slug: "met-museum", Name: "The Metropolitan Museum of Art", Base: "https://www.metmuseum.org", Docs: "https://metmuseum.github.io/", Policy: "https://www.metmuseum.org/hubs/open-access", Institution: "the-met", City: "New York", Visit: "https://www.metmuseum.org/plan-your-visit"},
	"cleveland": {Key: "cleveland", Slug: "cleveland-museum-of-art", Name: "The Cleveland Museum of Art", Base: "https://www.clevelandart.org", Docs: "https://openaccess-api.clevelandart.org/", Policy: "https://www.clevelandart.org/open-access", Institution: "cleveland-museum-of-art", City: "Cleveland", Visit: "https://www.clevelandart.org/plan-your-visit"},
	"aic":       {Key: "aic", Slug: "art-institute-of-chicago", Name: "Art Institute of Chicago", Base: "https://www.artic.edu", Docs: "https://api.artic.edu/docs/", Policy: "https://www.artic.edu/open-access/open-access-images", Institution: "art-institute-of-chicago", City: "Chicago", Visit: "https://www.artic.edu/visit"},
}

func (s Store) Source(ctx context.Context, key string) (string, error) {
	def, ok := sources[key]
	if !ok {
		return "", fmt.Errorf("unapproved source")
	}
	kind := "museum_api"
	if _, reviewed := reviewedMuseums[key]; key == "prado" || reviewed {
		kind = "collection_page"
	}
	if key == "pantheon" || key == "wikidata" {
		kind = "authority_data"
	}
	_, err := s.Pool.Exec(ctx, `INSERT INTO sources(slug,name,source_type,base_url,api_docs_url,terms_url,adapter_key)
 VALUES($1,$2,$3,$4,$5,$6,$7) ON CONFLICT(slug) DO NOTHING`, def.Slug, def.Name, kind, def.Base, def.Docs, def.Policy, Version)
	if err != nil {
		return "", err
	}
	var id string
	err = s.Pool.QueryRow(ctx, `SELECT id::text FROM sources WHERE slug=$1 AND is_active`, def.Slug).Scan(&id)
	return id, err
}

func (s Store) Job(ctx context.Context, sourceID, key string, query any) (string, error) {
	_, err := s.Pool.Exec(ctx, `INSERT INTO editor_accounts(user_id,display_name,role) VALUES('local-curated-import','Local curated import (automated; review required)','owner') ON CONFLICT(user_id) DO NOTHING`)
	if err != nil {
		return "", err
	}
	var id string
	err = s.Pool.QueryRow(ctx, `INSERT INTO import_jobs(source_id,requested_by,adapter_version,query_json,status,idempotency_key)
 VALUES($1,'local-curated-import',$2,$3,'running',$4) ON CONFLICT(idempotency_key)
 DO UPDATE SET status='running',updated_at=now(),completed_at=NULL,error_summary=NULL RETURNING id::text`, sourceID, Version, rawJSON(query), key).Scan(&id)
	return id, err
}

func (s Store) Finish(ctx context.Context, job, status string, runErr error) error {
	msg := ""
	if runErr != nil {
		msg = runErr.Error()
	}
	_, err := s.Pool.Exec(ctx, `UPDATE import_jobs SET status=$2,error_summary=NULLIF($3,''),updated_at=now(),completed_at=now(),
 total_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1),
 accepted_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1 AND outcome IN ('created','updated','skipped')),
 rejected_records=(SELECT count(*) FROM import_records WHERE import_job_id=$1 AND outcome IN ('rejected','conflict','failed')) WHERE id=$1`, job, status, msg)
	return err
}

func record(ctx context.Context, tx pgx.Tx, job, id string, raw, normalized any, outcome, kind, entity, note string) error {
	b := rawJSON(raw)
	tag, err := tx.Exec(ctx, `INSERT INTO import_records(import_job_id,source_record_id,source_checksum,raw_json,normalized_json,outcome,matched_entity_type,matched_entity_id,warnings_json)
 VALUES($1,$2,$3,$4,$5,$6,NULLIF($7,''),NULLIF($8,'')::uuid,$9)
 ON CONFLICT(import_job_id,source_record_id) DO UPDATE SET
 updated_at=now(),warnings_json=EXCLUDED.warnings_json,
 raw_json=EXCLUDED.raw_json,normalized_json=EXCLUDED.normalized_json,source_checksum=EXCLUDED.source_checksum,
 outcome=CASE WHEN import_records.outcome IN ('created','updated') AND EXCLUDED.outcome IN ('skipped','rejected') THEN import_records.outcome ELSE EXCLUDED.outcome END,
 matched_entity_type=coalesce(EXCLUDED.matched_entity_type,import_records.matched_entity_type),
 matched_entity_id=coalesce(EXCLUDED.matched_entity_id,import_records.matched_entity_id)
 WHERE import_records.source_checksum=EXCLUDED.source_checksum OR import_records.outcome='failed'`, job, id, checksum(b), b, rawJSON(normalized), outcome, kind, entity, rawJSON([]string{note}))
	if err == nil && tag.RowsAffected() == 0 {
		return fmt.Errorf("source snapshot changed for %s; review required", id)
	}
	return err
}

var seedAliases = map[string]string{
	"giotto": "giotto", "giotto di bondone": "giotto", "rembrandt": "rembrandt",
	"hokusai": "katsushika-hokusai", "katsushika hokusai": "katsushika-hokusai",
	"peder severin kroyer": "p-s-kroyer", "p s kroyer": "p-s-kroyer",
	"peder severin krøyer": "p-s-kroyer", "p s krøyer": "p-s-kroyer",
}

func (s Store) Painter(ctx context.Context, job, sourceID string, p *Painter) error {
	tx, err := s.Pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	var id string
	outcome := "skipped"
	err = tx.QueryRow(ctx, `SELECT entity_id::text FROM external_identifiers WHERE scheme='wikidata' AND external_id=$1 AND entity_type='artist'`, p.QID).Scan(&id)
	if errors.Is(err, pgx.ErrNoRows) {
		// Existing seed names are preserved. Only exact names, or this small reviewed
		// seed alias crosswalk, are reconciled; ambiguous names require a human.
		rows, e := tx.Query(ctx, `SELECT id::text FROM artists WHERE normalized_name=$1 OR slug=$2`, normalize(p.Name), seedAliases[normalize(p.Name)])
		if e != nil {
			return e
		}
		var matches []string
		for rows.Next() {
			var x string
			if e = rows.Scan(&x); e != nil {
				rows.Close()
				return e
			}
			matches = append(matches, x)
		}
		rows.Close()
		if rows.Err() != nil {
			return rows.Err()
		}
		if len(matches) > 1 {
			return fmt.Errorf("ambiguous existing painter %s", p.Name)
		}
		if len(matches) == 1 {
			id = matches[0]
		} else {
			end := 2025
			display := fmt.Sprintf("born %d (living in 2025 source)", p.Birth)
			basis := "estimated"
			if p.Death != nil {
				end = *p.Death
				display = fmt.Sprintf("%d–%d", p.Birth, end)
				basis = "life"
			}
			err = tx.QueryRow(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,birth_year,death_year,birth_display,death_display,
 timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,created_by,updated_by)
 VALUES($1,$2,$2,$3,$4::int,$5::int,($4::int)::text,($5::int)::text,$4::int,$6,$7,$8,'review','local-curated-import','local-curated-import') RETURNING id::text`, slug(p.Name)+"-"+strings.ToLower(p.QID), p.Name, normalize(p.Name), p.Birth, p.Death, end, display, basis).Scan(&id)
			if err != nil {
				return err
			}
			outcome = "created"
		}
	} else if err != nil {
		return err
	}
	var conflict bool
	if err = tx.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=$1 AND scheme='wikidata' AND external_id<>$2)`, id, p.QID).Scan(&conflict); err != nil {
		return err
	}
	if conflict {
		return fmt.Errorf("authority conflict for painter %s", p.Name)
	}
	_, err = tx.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
 VALUES('artist',$1,'wikidata',$2,$3,$4,now()) ON CONFLICT(scheme,external_id) DO NOTHING`, id, p.QID, "https://www.wikidata.org/wiki/"+p.QID, sourceID)
	if err != nil {
		return err
	}
	_, err = tx.Exec(ctx, `INSERT INTO painter_import_cohort(import_job_id,artist_id,authority_id,rank,popularity_score,selection_note)
 VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT(import_job_id,artist_id) DO NOTHING`, job, id, p.QID, p.Rank, p.Score, PantheonAttribution)
	if err != nil {
		return err
	}
	// Also works on a fresh database where the discovery migration precedes the
	// import. Never overwrite a later editorial inclusion/exclusion on a rerun.
	if p.Rank <= 100 {
		popular, basis, sourceURL := true, "Pantheon 2025 imported painter cohort: top 100 by HPI. A popularity proxy, not an artistic-quality ranking.", "https://pantheon.world/data/datasets"
		if p.QID == "Q37562" {
			popular = false
			basis = "Editorial exclusion from the popular painting selection: primarily a sculptor. Original source record retained."
			sourceURL = "https://www.vam.ac.uk/articles/donatello-a-master-at-work"
		}
		_, err = tx.Exec(ctx, `INSERT INTO artist_discovery_selection(artist_id,is_popular,popularity_rank,basis,source_url) VALUES($1,$2,$3,$4,$5) ON CONFLICT(artist_id) DO NOTHING`, id, popular, p.Rank, basis, sourceURL)
		if err != nil {
			return err
		}
	}
	for _, field := range []string{"identity", "timeline_dates", "ranking"} {
		_, err = tx.Exec(ctx, `INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
 SELECT 'artist',$1,$2,$3,$4,$5,$6,now(),'local-curated-import' WHERE NOT EXISTS(SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=$1 AND field_name=$2 AND source_id=$3)`, id, field, sourceID, p.QID, "https://pantheon.world/profile/person/"+url.PathEscape(p.SourceSlug), PantheonAttribution+" Source dates are not independently reviewed; existing editorial dates are preserved.")
		if err != nil {
			return err
		}
	}
	if err = addBirthCountry(ctx, tx, id, p.Country); err != nil {
		return err
	}
	p.ID = id
	if err = record(ctx, tx, job, p.QID, p.Raw, p, outcome, "artist", id, "Imported as review; existing biography/classifications/dates preserved."); err != nil {
		return err
	}
	return tx.Commit(ctx)
}

func (s Store) Institution(ctx context.Context, key, sourceID string) (string, error) {
	def := sources[key]
	tx, err := s.Pool.Begin(ctx)
	if err != nil {
		return "", err
	}
	defer tx.Rollback(ctx)
	_, err = tx.Exec(ctx, `INSERT INTO institutions(slug,name,normalized_name,website_url,description)
 VALUES($1,$2,$3,$4,'Selected museum holdings; museum highlights and personal selections are labelled separately. Holding does not imply current display.') ON CONFLICT(slug) DO NOTHING`, def.Institution, def.Name, normalize(def.Name), def.Base)
	if err != nil {
		return "", err
	}
	var id string
	if err = tx.QueryRow(ctx, `SELECT id::text FROM institutions WHERE slug=$1 AND status<>'archived'`, def.Institution).Scan(&id); err != nil {
		return "", err
	}
	_, err = tx.Exec(ctx, `INSERT INTO source_institutions(source_id,institution_id) VALUES($1,$2) ON CONFLICT DO NOTHING`, sourceID, id)
	if err != nil {
		return "", err
	}
	_, err = tx.Exec(ctx, `INSERT INTO source_connector_config(source_id) VALUES($1) ON CONFLICT DO NOTHING`, sourceID)
	if err != nil {
		return "", err
	}
	_, err = tx.Exec(ctx, `INSERT INTO curated_collections(institution_id,curator_kind,title) VALUES($1,'museum','Museum highlights'),($1,'owner','My must-see works') ON CONFLICT(institution_id,curator_kind) DO NOTHING`, id)
	if err != nil {
		return "", err
	}
	// Existing venues are not touched; new institutions get a sourced visit link.
	country := def.Country
	if country == "" {
		country = "US"
	}
	geography, ok := map[string][2]string{"US": {"United States", "northern-america"}, "ES": {"Spain", "southern-europe"}, "IT": {"Italy", "southern-europe"}, "MX": {"Mexico", "central-america"}}[country]
	if !ok {
		return "", fmt.Errorf("museum country needs a reviewed geographic mapping: %s", country)
	}
	if _, err = tx.Exec(ctx, `INSERT INTO countries(code,name,region_code) VALUES($1,$2,$3) ON CONFLICT(code) DO NOTHING`, country, geography[0], geography[1]); err != nil {
		return "", err
	}
	_, err = tx.Exec(ctx, `INSERT INTO places(id,name,normalized_name,country_code)
 SELECT md5('artline-import-city-'||$3||'-'||$1)::uuid,$1,lower($1),$3 WHERE NOT EXISTS(SELECT 1 FROM institution_venues WHERE institution_id=$2)
 ON CONFLICT(id) DO NOTHING`, def.City, id, country)
	if err != nil {
		return "", err
	}
	_, err = tx.Exec(ctx, `INSERT INTO institution_venues(institution_id,slug,name,place_id,visit_url,source_url,checked_at)
 SELECT $1,$2,$3,md5('artline-import-city-'||$6||'-'||$4)::uuid,$5,$5,now()
 WHERE NOT EXISTS(SELECT 1 FROM institution_venues WHERE institution_id=$1) ON CONFLICT(slug) DO NOTHING`, id, def.Institution+"-main", def.Name, def.City, def.Visit, country)
	if err != nil {
		return "", err
	}
	return id, tx.Commit(ctx)
}

// Work imports are insert-only. An existing source identity or official object
// citation is reused, but edited catalogue fields are never overwritten.
func (s Store) Work(ctx context.Context, job, sourceID, institutionID string, p Painter, w Work, img *ImageFile, imageErr string) (bool, error) {
	if w.Eligible() != "eligible" {
		return false, fmt.Errorf("content policy denied work")
	}
	tx, err := s.Pool.Begin(ctx)
	if err != nil {
		return false, err
	}
	defer tx.Rollback(ctx)
	var id string
	created := false
	err = tx.QueryRow(ctx, `SELECT entity_id::text FROM external_identifiers WHERE scheme=$1 AND external_id=$2 AND entity_type='artwork'`, w.Source+"-object", w.ID).Scan(&id)
	if errors.Is(err, pgx.ErrNoRows) {
		identityURL := w.URL
		if w.Source == "mam" {
			// The highlights page describes several works. Its URL is evidence,
			// not an object identifier; use the explicit authority ID instead.
			identityURL = ""
		}
		rows, e := tx.Query(ctx, `SELECT DISTINCT aw.id::text FROM artworks aw LEFT JOIN citations c ON c.entity_type='artwork' AND c.entity_id=aw.id
 WHERE ($1<>'' AND c.source_url=$1) OR (aw.current_institution_id=$2 AND aw.accession_number=$3 AND $3<>'')`, identityURL, institutionID, w.Accession)
		if e != nil {
			return false, e
		}
		var ids []string
		for rows.Next() {
			var x string
			if e = rows.Scan(&x); e != nil {
				rows.Close()
				return false, e
			}
			ids = append(ids, x)
		}
		rows.Close()
		if rows.Err() != nil {
			return false, rows.Err()
		}
		if len(ids) > 1 {
			return false, fmt.Errorf("ambiguous artwork identity %s:%s", w.Source, w.ID)
		}
		if len(ids) == 1 {
			id = ids[0]
		} else {
			err = tx.QueryRow(ctx, `INSERT INTO artworks(slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,
 creation_place_unknown_reason,current_location_text,location_checked_at,accession_number,status,created_by,updated_by)
 VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'Not documented in this source; not inferred from the museum location.',$11,now(),$12,'review','local-curated-import','local-curated-import') RETURNING id::text`, w.Source+"-"+w.ID+"-"+slug(w.Title), w.Title, normalize(w.Title), w.Date, w.First, w.Last, w.Precision, w.Type, w.Medium, w.Dimensions, sources[w.Source].Name, w.Accession).Scan(&id)
			if err != nil {
				return false, err
			}
			created = true
		}
	} else if err != nil {
		return false, err
	}
	if !created {
		var matches bool
		if err = tx.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artwork_artists aa JOIN artworks aw ON aw.id=aa.artwork_id WHERE aa.artwork_id=$1 AND aa.artist_id=$2 AND aa.attribution_role='primary' AND aw.status<>'archived')`, id, p.ID).Scan(&matches); err != nil {
			return false, err
		}
		if !matches {
			return false, fmt.Errorf("existing artwork artist/archive conflict %s:%s", w.Source, w.ID)
		}
	}
	_, err = tx.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
 VALUES('artwork',$1,$2,$3,$4,$5,now()) ON CONFLICT(scheme,external_id) DO NOTHING`, id, w.Source+"-object", w.ID, w.URL, sourceID)
	if err != nil {
		return false, err
	}
	if created {
		_, err = tx.Exec(ctx, `INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,representative_order,attribution_note)
 VALUES($1,$2,'primary',(SELECT min(n) FROM generate_series(1,10) n WHERE NOT EXISTS(SELECT 1 FROM artwork_artists WHERE artist_id=$2 AND representative_order=n)),'Matched source authority or unambiguous name and birth year; review required.')`, id, p.ID)
		if err != nil {
			return false, err
		}
		_, err = tx.Exec(ctx, `INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
 VALUES($1,'holding',$2,'collection',$3,$4,'Official museum object record identifies this work as a collection holding. No current-display claim is imported.',now(),'accepted')`, id, institutionID, sourceID, w.URL)
		if err != nil {
			return false, err
		}
	}
	_, err = tx.Exec(ctx, `INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
 SELECT 'artwork',$1,'date_and_location',$2,$3,$4,$5,now(),'local-curated-import' WHERE NOT EXISTS(SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=$1 AND source_id=$2 AND source_record_id=$3)`, id, sourceID, w.ID, w.URL, "Official object metadata. "+w.SelectionReason)
	if err != nil {
		return false, err
	}
	if note, ok := w.Raw["image_deferral"].(string); ok && note != "" {
		_, err = tx.Exec(ctx, `INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
 SELECT 'artwork',$1,'image_permissions',$2,$3,$4,$5,now(),'local-curated-import'
 WHERE NOT EXISTS(SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=$1 AND source_id=$2 AND source_record_id=$3)`, id, sourceID, w.ID+":image-permissions", sources[w.Source].Policy, note)
		if err != nil {
			return false, err
		}
	}
	selectionKind := w.SelectionKind
	if selectionKind == "" {
		selectionKind = "museum"
	}
	// Do not reinstate an owner's removed selection when replaying an import.
	if selectionKind != "owner" || created {
		// Share the owner's collection lock/revision protocol, including for imports.
		var collectionID string
		if err = tx.QueryRow(ctx, `SELECT id::text FROM curated_collections WHERE institution_id=$1 AND curator_kind=$2 AND status<>'archived' FOR UPDATE`, institutionID, selectionKind).Scan(&collectionID); err != nil {
			return false, err
		}
		selected, err := tx.Exec(ctx, `INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
 VALUES($1,$2,coalesce((SELECT max(position) FROM curated_collection_items WHERE collection_id=$1),0)+1,$3,$4,$5,now())
 ON CONFLICT(collection_id,artwork_id) DO NOTHING`, collectionID, id, w.SelectionReason, sourceID, w.SelectionURL)
		if err != nil {
			return false, err
		}
		if selected.RowsAffected() > 0 {
			if _, err = tx.Exec(ctx, `UPDATE curated_collections SET revision=revision+1,updated_at=now(),status='review' WHERE id=$1`, collectionID); err != nil {
				return false, err
			}
		}
	}
	if img != nil {
		if !w.ImageAllowed() {
			return false, fmt.Errorf("rights gate denied image attachment")
		}
		var mediaID string
		imagePage, provider, policy, basis := w.URL, sources[w.Source].Name, sources[w.Source].Policy, "Exact record allows CC0; no conflicting copyright notice"
		licenseLabel, licenseURL, credit := "CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/", w.Credit+". "+provider+". CC0."
		if w.Source == "prado" {
			imagePage, provider, policy = w.ImageSourceURL, w.ImageProvider, w.ImagePolicyURL
			basis = "Commons file explicitly marked public domain and PD-Art/PD-old-100; exact P18 image linked to the artwork authority. Museum image-bank terms are not treated as CC0."
			licenseLabel, licenseURL, credit = "Public domain (Commons PD-Art)", policy, w.Credit
		}
		err = tx.QueryRow(ctx, `INSERT INTO media_assets(storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
 VALUES('local',$1,$2,$3,$4,$5,$6,$7,$8,$9,$12,$13,$14,$10,$11,now(),now(),'local-curated-import')
 ON CONFLICT(storage_path) DO UPDATE SET storage_path=EXCLUDED.storage_path RETURNING id::text`, img.Path, imagePage, provider, img.MIME, img.Width, img.Height, img.Bytes, img.Hash, w.Title+" — "+p.Name, p.Name, credit, w.Rights, licenseLabel, licenseURL).Scan(&mediaID)
		if err != nil {
			return false, err
		}
		_, err = tx.Exec(ctx, `INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
 VALUES($1,$2,$3,$4,$5,$6,$9,$7,now(),$8) ON CONFLICT(media_id) DO NOTHING`, mediaID, sourceID, w.ID, checksum(rawJSON(w.Raw)), w.ImageURL, policy, Version, rawJSON(map[string]any{"rights": w.Rights, "copyright": w.Copyright, "highlight": w.Highlight, "source_record": w.APIURL, "image_source_page": imagePage, "provider": provider, "commons": w.Raw["commons"], "image_sha256": img.Hash}), basis)
		if err != nil {
			return false, err
		}
		_, err = tx.Exec(ctx, `UPDATE artworks SET primary_media_id=$2,revision=revision+1,updated_at=now() WHERE id=$1 AND primary_media_id IS NULL AND status IN ('draft','review')`, id, mediaID)
		if err != nil {
			return false, err
		}
	}
	outcome := "skipped"
	if created {
		outcome = "created"
	}
	if err = record(ctx, tx, job, w.ID, w.Raw, w, outcome, "artwork", id, imageErr); err != nil {
		return false, err
	}
	return created, tx.Commit(ctx)
}

func (s Store) Outcome(ctx context.Context, job string, w Work, reason string) error {
	tx, err := s.Pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	outcome := "rejected"
	if reason == "creation_review" {
		outcome = "pending"
	}
	if w.FetchError != "" {
		outcome = "failed"
	}
	if err = record(ctx, tx, job, w.ID, w.Raw, w, outcome, "", "", reason); err != nil {
		return err
	}
	return tx.Commit(ctx)
}

func (s Store) ExistingMedia(ctx context.Context, w Work) (bool, error) {
	var exists bool
	err := s.Pool.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artworks aw WHERE aw.primary_media_id IS NOT NULL AND
 (EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=aw.id AND e.scheme=$1 AND e.external_id=$2)
 OR EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=aw.id AND c.source_url=$3)))`, w.Source+"-object", w.ID, w.URL).Scan(&exists)
	return exists, err
}

func (s Store) Checkpoint(ctx context.Context, job string, w Work) error {
	_, err := s.Pool.Exec(ctx, `UPDATE import_jobs SET checkpoint_json=$2,updated_at=now() WHERE id=$1`, job, rawJSON(map[string]any{"last_source_record": w.ID, "at": time.Now().UTC()}))
	return err
}
