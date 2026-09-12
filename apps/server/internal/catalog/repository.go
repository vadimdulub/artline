package catalog

import (
	"context"
	"errors"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

var ErrNotFound = errors.New("record not found")
var ErrRevisionConflict = errors.New("revision conflict")

type PublicationError struct{ Report PublicationValidation }

func (e *PublicationError) Error() string { return "publication validation failed" }

type Repository struct {
	db interface {
		Query(context.Context, string, ...any) (pgx.Rows, error)
		QueryRow(context.Context, string, ...any) pgx.Row
		Begin(context.Context) (pgx.Tx, error)
	}
}

func NewRepository(db *pgxpool.Pool) *Repository {
	return &Repository{db: db}
}

func (r *Repository) ArtistBySlug(ctx context.Context, slug string, preview bool) (ArtistDetail, error) {
	var artist ArtistDetail
	const query = `
		SELECT a.id::text, a.slug, a.display_name, a.sort_name, a.timeline_start_year,
		       a.timeline_end_year, a.timeline_display, a.timeline_basis, a.biography_md,
		       a.status, a.revision, a.entity_type,
		       COALESCE(m.slug, 'unclassified'), COALESCE(m.name, 'Unclassified'), COALESCE(m.color_hex, '#717776'),
		       ARRAY(SELECT DISTINCT trim(ac.country_code::text) FROM artist_countries ac WHERE ac.artist_id = a.id ORDER BY 1),
               ARRAY(SELECT alias FROM artist_aliases WHERE artist_id=a.id ORDER BY alias)
		FROM artists a
		LEFT JOIN artist_movements am ON am.artist_id = a.id AND am.role = 'primary'
		LEFT JOIN movements m ON m.id = am.movement_id AND m.status <> 'archived'
		WHERE (a.slug = $1 OR a.id=(SELECT entity_id FROM slug_redirects WHERE entity_type='artist' AND old_slug=$1)) AND a.status <> 'archived' AND ($2 OR a.status='published')`
	err := r.db.QueryRow(ctx, query, slug, preview).Scan(
		&artist.ID, &artist.Slug, &artist.DisplayName, &artist.SortName,
		&artist.TimelineStart, &artist.TimelineEnd, &artist.TimelineDisplay,
		&artist.TimelineBasis, &artist.BiographyMD, &artist.Status, &artist.Revision, &artist.EntityType,
		&artist.Movement.Slug, &artist.Movement.Name, &artist.Movement.Color, &artist.Countries, &artist.Aliases,
	)
	if errors.Is(err, pgx.ErrNoRows) {
		return artist, ErrNotFound
	}
	if err != nil {
		return artist, fmt.Errorf("query artist: %w", err)
	}
	artworks, err := r.artistArtworks(ctx, artist.ID, preview)
	if err != nil {
		return artist, err
	}
	artist.Artworks = artworks
	citations, err := r.artistCitations(ctx, artist.ID)
	if err != nil {
		return artist, err
	}
	artist.Citations = citations
	artist.Influences, err = r.artistInfluences(ctx, artist.ID)
	if err != nil {
		return artist, err
	}
	return artist, nil
}

func (r *Repository) artistArtworks(ctx context.Context, artistID string, preview bool) ([]Artwork, error) {
	const query = `
		SELECT aw.id::text, aw.slug, aw.title, aw.alternate_title, aw.date_display,
		       aw.creation_year_start, aw.creation_year_end, aw.date_precision, aw.work_type,
		       aw.medium_text, aw.dimensions_text, aw.creation_place_display,
		       aw.current_location_text,
               CASE WHEN ma.verified_at IS NOT NULL AND ma.rights_status IN ('public_domain','cc0','cc_by','cc_by_sa','licensed') AND nullif(trim(ma.alt_text),'') IS NOT NULL THEN ma.storage_path END, ma.alt_text,
		       ma.rights_status, ma.attribution_text, aa.representative_order, aw.status,
               aw.revision,aa.attribution_role,ma.source_page_url,ma.license_label,ma.license_url,aw.location_checked_at,aw.accession_number,aw.creation_place_unknown_reason
		FROM artwork_artists aa
		JOIN artworks aw ON aw.id = aa.artwork_id
		LEFT JOIN media_assets ma ON ma.id = aw.primary_media_id
		WHERE aa.artist_id = $1 AND aw.status <> 'archived' AND ($2 OR aw.status='published') AND aa.representative_order IS NOT NULL
		ORDER BY aa.representative_order NULLS LAST, aw.creation_year_start NULLS LAST, aw.title LIMIT 10`
	rows, err := r.db.Query(ctx, query, artistID, preview)
	if err != nil {
		return nil, fmt.Errorf("query artist artworks: %w", err)
	}
	defer rows.Close()
	artworks := []Artwork{}
	for rows.Next() {
		var artwork Artwork
		if err := rows.Scan(&artwork.ID, &artwork.Slug, &artwork.Title, &artwork.AlternateTitle,
			&artwork.DateDisplay, &artwork.CreationYearStart, &artwork.CreationYearEnd,
			&artwork.DatePrecision, &artwork.WorkType, &artwork.MediumText, &artwork.DimensionsText,
			&artwork.CreationPlaceDisplay, &artwork.CurrentLocationText, &artwork.MediaURL,
			&artwork.AltText, &artwork.RightsStatus, &artwork.AttributionText,
			&artwork.RepresentativeOrder, &artwork.Status, &artwork.Revision, &artwork.AttributionRole, &artwork.SourcePageURL, &artwork.LicenseLabel, &artwork.LicenseURL, &artwork.LocationCheckedAt, &artwork.AccessionNumber, &artwork.CreationPlaceUnknownReason); err != nil {
			return nil, fmt.Errorf("scan artist artwork: %w", err)
		}
		artworks = append(artworks, artwork)
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return artworks, r.enrichArtworks(ctx, artworks, preview)
}

func (r *Repository) artistCitations(ctx context.Context, artistID string) ([]Citation, error) {
	return r.entityCitations(ctx, "artist", artistID)
}

func (r *Repository) entityCitations(ctx context.Context, entityType, id string) ([]Citation, error) {
	const query = `SELECT c.field_name, s.name, c.source_url, COALESCE(c.evidence_note, '')
		FROM citations c JOIN sources s ON s.id = c.source_id
		WHERE c.entity_type = $2 AND c.entity_id = $1 AND s.is_active ORDER BY c.field_name, s.priority LIMIT 100`
	rows, err := r.db.Query(ctx, query, id, entityType)
	if err != nil {
		return nil, fmt.Errorf("query artist citations: %w", err)
	}
	defer rows.Close()
	citations := []Citation{}
	for rows.Next() {
		var citation Citation
		if err := rows.Scan(&citation.FieldName, &citation.SourceName, &citation.SourceURL, &citation.EvidenceNote); err != nil {
			return nil, fmt.Errorf("scan artist citation: %w", err)
		}
		citations = append(citations, citation)
	}
	return citations, rows.Err()
}

func (r *Repository) Catalogue(ctx context.Context, status, query string, limit, offset int, sort string) ([]CatalogueArtist, error) {
	const statement = `
		SELECT id::text, slug, display_name, timeline_start_year, timeline_end_year,
		       timeline_display, status, revision, updated_at
		FROM artists
		WHERE ($1 = '' OR status = $1)
		  AND ($2 = '' OR normalized_name ILIKE '%' || lower($2) || '%')
		ORDER BY CASE WHEN $5='updated' THEN updated_at END DESC,
          CASE WHEN $5='date' THEN timeline_start_year END,
          sort_name,id
		LIMIT $3 OFFSET $4`
	rows, err := r.db.Query(ctx, statement, status, query, limit, offset, sort)
	if err != nil {
		return nil, fmt.Errorf("query catalogue: %w", err)
	}
	defer rows.Close()
	artists := []CatalogueArtist{}
	for rows.Next() {
		var artist CatalogueArtist
		if err := rows.Scan(&artist.ID, &artist.Slug, &artist.DisplayName, &artist.TimelineStart,
			&artist.TimelineEnd, &artist.TimelineDisplay, &artist.Status, &artist.Revision,
			&artist.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan catalogue artist: %w", err)
		}
		artists = append(artists, artist)
	}
	return artists, rows.Err()
}

func (r *Repository) CreateArtist(ctx context.Context, input ArtistInput) (CatalogueArtist, error) {
	var artist CatalogueArtist
	const statement = `
		INSERT INTO artists (
			slug, display_name, sort_name, normalized_name, entity_type,
			timeline_start_year, timeline_end_year, timeline_display, timeline_basis,
			biography_md, status
		) VALUES ($1, $2, $3, lower($2), $4, $5, $6, $7, $8, $9, $10)
		RETURNING id::text, slug, display_name, timeline_start_year, timeline_end_year,
		          timeline_display, status, revision, updated_at`
	err := r.db.QueryRow(ctx, statement, input.Slug, input.DisplayName, input.SortName,
		input.EntityType, input.TimelineStartYear, input.TimelineEndYear,
		input.TimelineDisplay, input.TimelineBasis, input.BiographyMD, input.Status).Scan(
		&artist.ID, &artist.Slug, &artist.DisplayName, &artist.TimelineStart,
		&artist.TimelineEnd, &artist.TimelineDisplay, &artist.Status, &artist.Revision,
		&artist.UpdatedAt,
	)
	if err != nil {
		return artist, fmt.Errorf("create artist: %w", err)
	}
	return artist, nil
}

func (r *Repository) UpdateArtist(ctx context.Context, id string, input ArtistInput) (CatalogueArtist, error) {
	var artist CatalogueArtist
	const statement = `
		UPDATE artists
		SET slug = $2, display_name = $3, sort_name = $4, normalized_name = lower($3),
		    entity_type = $5, timeline_start_year = $6, timeline_end_year = $7,
		    timeline_display = $8, timeline_basis = $9, biography_md = $10,
		    status = $11, published_at=NULL, revision = revision + 1, updated_at = now()
		WHERE id = $1 AND revision = $12 AND status <> 'archived'
		RETURNING id::text, slug, display_name, timeline_start_year, timeline_end_year,
		          timeline_display, status, revision, updated_at`
	err := r.db.QueryRow(ctx, statement, id, input.Slug, input.DisplayName, input.SortName,
		input.EntityType, input.TimelineStartYear, input.TimelineEndYear,
		input.TimelineDisplay, input.TimelineBasis, input.BiographyMD, input.Status,
		input.ExpectedRevision).Scan(
		&artist.ID, &artist.Slug, &artist.DisplayName, &artist.TimelineStart,
		&artist.TimelineEnd, &artist.TimelineDisplay, &artist.Status, &artist.Revision,
		&artist.UpdatedAt,
	)
	if errors.Is(err, pgx.ErrNoRows) {
		var exists bool
		if checkErr := r.db.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artists WHERE id = $1)`, id).Scan(&exists); checkErr != nil {
			return artist, fmt.Errorf("check artist after update: %w", checkErr)
		}
		if exists {
			return artist, ErrRevisionConflict
		}
		return artist, ErrNotFound
	}
	if err != nil {
		return artist, fmt.Errorf("update artist: %w", err)
	}
	return artist, nil
}

func (r *Repository) SetArchived(ctx context.Context, id string, archived bool, expectedRevision int) (CatalogueArtist, error) {
	status := "draft"
	if archived {
		status = "archived"
	}
	var artist CatalogueArtist
	const statement = `
		UPDATE artists SET status = $2, published_at=NULL, revision = revision + 1, updated_at = now()
		WHERE id = $1 AND revision=$3 AND (($2='archived' AND status<>'archived') OR ($2='draft' AND status='archived'))
		RETURNING id::text, slug, display_name, timeline_start_year, timeline_end_year,
		          timeline_display, status, revision, updated_at`
	err := r.db.QueryRow(ctx, statement, id, status, expectedRevision).Scan(
		&artist.ID, &artist.Slug, &artist.DisplayName, &artist.TimelineStart,
		&artist.TimelineEnd, &artist.TimelineDisplay, &artist.Status, &artist.Revision,
		&artist.UpdatedAt,
	)
	if errors.Is(err, pgx.ErrNoRows) {
		var exists bool
		if err := r.db.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM artists WHERE id=$1)", id).Scan(&exists); err != nil {
			return artist, err
		}
		if exists {
			return artist, ErrRevisionConflict
		}
		return artist, ErrNotFound
	}
	if err != nil {
		return artist, fmt.Errorf("set artist archive state: %w", err)
	}
	return artist, nil
}

func (r *Repository) Coverage(ctx context.Context) (CoverageSummary, error) {
	summary := CoverageSummary{ByStatus: map[string]int{}}
	rows, err := r.db.Query(ctx, `SELECT status, count(*) FROM artists GROUP BY status`)
	if err != nil {
		return summary, fmt.Errorf("query coverage by status: %w", err)
	}
	for rows.Next() {
		var status string
		var count int
		if err := rows.Scan(&status, &count); err != nil {
			rows.Close()
			return summary, fmt.Errorf("scan coverage status: %w", err)
		}
		summary.ByStatus[status] = count
		summary.TotalArtists += count
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		return summary, err
	}
	const qualityQuery = `
		SELECT
		  count(DISTINCT a.id) FILTER (WHERE trim(c.code::text) IN ('DK', 'SE', 'NO', 'FI', 'IS')),
		  count(DISTINCT a.id) FILTER (WHERE c.region_code LIKE '%asia'),
		  count(DISTINCT a.id) FILTER (WHERE (SELECT count(*) FROM artwork_artists aa JOIN artworks aw ON aw.id = aa.artwork_id WHERE aa.artist_id = a.id AND aw.status = 'published' AND aa.representative_order IS NOT NULL) < 5),
		  count(DISTINCT a.id) FILTER (WHERE a.biography_md IS NULL OR length(trim(a.biography_md)) = 0)
		FROM artists a
		LEFT JOIN artist_countries ac ON ac.artist_id = a.id
		LEFT JOIN countries c ON c.code = ac.country_code
		WHERE a.status <> 'archived'`
	if err := r.db.QueryRow(ctx, qualityQuery).Scan(&summary.NordicArtists, &summary.AsianArtists, &summary.MissingWorks, &summary.MissingBio); err != nil {
		return summary, fmt.Errorf("query coverage quality: %w", err)
	}
	return summary, nil
}

func (r *Repository) Facets(ctx context.Context, preview bool) (TimelineFacets, error) {
	return r.DiscoveryFacets(ctx, preview, false)
}

func (r *Repository) DiscoveryFacets(ctx context.Context, preview, popular bool) (TimelineFacets, error) {
	facets := TimelineFacets{Movements: []FacetOption{}, Countries: []FacetOption{}, Regions: []FacetOption{}}
	movementRows, err := r.db.Query(ctx, `
		SELECT m.slug, m.name, m.color_hex, count(DISTINCT a.id)
		FROM movements m
		JOIN artist_movements am ON am.movement_id = m.id
		JOIN artists a ON a.id = am.artist_id AND a.status <> 'archived'
        WHERE ($1 OR (a.status='published' AND m.status='published')) AND m.status<>'archived'
        AND (NOT $2 OR EXISTS(SELECT 1 FROM artist_discovery_selection ds WHERE ds.artist_id=a.id AND ds.is_popular))
		GROUP BY m.slug, m.name, m.color_hex, m.start_year
		ORDER BY m.start_year NULLS LAST, m.name`, preview, popular)
	if err != nil {
		return facets, fmt.Errorf("query movement facets: %w", err)
	}
	for movementRows.Next() {
		var option FacetOption
		if err := movementRows.Scan(&option.Slug, &option.Name, &option.Color, &option.Count); err != nil {
			movementRows.Close()
			return facets, fmt.Errorf("scan movement facet: %w", err)
		}
		facets.Movements = append(facets.Movements, option)
	}
	movementRows.Close()
	if err := movementRows.Err(); err != nil {
		return facets, err
	}

	countryRows, err := r.db.Query(ctx, `
		SELECT trim(c.code::text), c.name, count(DISTINCT a.id)
		FROM countries c
		JOIN artist_countries ac ON ac.country_code = c.code
		JOIN artists a ON a.id = ac.artist_id AND a.status <> 'archived'
        WHERE ($1 OR a.status='published')
        AND (NOT $2 OR EXISTS(SELECT 1 FROM artist_discovery_selection ds WHERE ds.artist_id=a.id AND ds.is_popular))
		GROUP BY c.code, c.name
		ORDER BY c.name`, preview, popular)
	if err != nil {
		return facets, fmt.Errorf("query country facets: %w", err)
	}
	for countryRows.Next() {
		var option FacetOption
		if err := countryRows.Scan(&option.Slug, &option.Name, &option.Count); err != nil {
			countryRows.Close()
			return facets, fmt.Errorf("scan country facet: %w", err)
		}
		facets.Countries = append(facets.Countries, option)
	}
	countryRows.Close()
	if err := countryRows.Err(); err != nil {
		return facets, err
	}
	regionRows, err := r.db.Query(ctx, `
		SELECT c.region_code, initcap(replace(c.region_code,'-',' ')), count(DISTINCT a.id)
		FROM countries c JOIN artist_countries ac ON ac.country_code=c.code
		JOIN artists a ON a.id=ac.artist_id AND a.status<>'archived'
		WHERE ($1 OR a.status='published')
		AND (NOT $2 OR EXISTS(SELECT 1 FROM artist_discovery_selection ds WHERE ds.artist_id=a.id AND ds.is_popular))
		GROUP BY c.region_code ORDER BY c.region_code`, preview, popular)
	if err != nil {
		return facets, fmt.Errorf("query region facets: %w", err)
	}
	defer regionRows.Close()
	for regionRows.Next() {
		var option FacetOption
		if err := regionRows.Scan(&option.Slug, &option.Name, &option.Count); err != nil {
			return facets, fmt.Errorf("scan region facet: %w", err)
		}
		facets.Regions = append(facets.Regions, option)
	}
	return facets, regionRows.Err()
}

func (r *Repository) ValidateArtistForPublication(ctx context.Context, id string) (PublicationValidation, error) {
	report := PublicationValidation{ArtistID: id, Issues: []ValidationIssue{}}
	var biography *string
	var influenceState, movementState, geographyState string
	const artistQuery = `
		SELECT biography_md, influence_review_state, movement_review_state,
		       geography_review_state, revision
		FROM artists WHERE id = $1 AND status <> 'archived'`
	if err := r.db.QueryRow(ctx, artistQuery, id).Scan(&biography, &influenceState, &movementState, &geographyState, &report.Revision); err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return report, ErrNotFound
		}
		return report, fmt.Errorf("query artist for publication validation: %w", err)
	}

	if biography == nil || len(strings.Fields(*biography)) < 80 {
		report.Issues = append(report.Issues, ValidationIssue{Path: "biography_md", Code: "BIOGRAPHY_TOO_SHORT", Message: "Add a sourced biography of at least 80 words."})
	} else if len(strings.Fields(*biography)) > 300 {
		report.Issues = append(report.Issues, ValidationIssue{Path: "biography_md", Code: "BIOGRAPHY_TOO_LONG", Message: "Keep the public biography at 300 words or fewer."})
	}
	if influenceState == "not_reviewed" {
		report.Issues = append(report.Issues, ValidationIssue{Path: "influences", Code: "INFLUENCE_REVIEW_REQUIRED", Message: "Review documented influences or record that none were found."})
	}

	var countryCount, primaryMovementCount, coreCitationCount int
	if err := r.db.QueryRow(ctx, `
		SELECT
		  (SELECT count(*) FROM artist_countries WHERE artist_id = $1),
		  (SELECT count(*) FROM artist_movements WHERE artist_id = $1 AND role = 'primary'),
		  (SELECT count(DISTINCT field_name) FROM citations WHERE entity_type = 'artist' AND entity_id = $1 AND field_name IN ('timeline_dates', 'biography', 'geography'))`, id).Scan(&countryCount, &primaryMovementCount, &coreCitationCount); err != nil {
		return report, fmt.Errorf("query artist publication associations: %w", err)
	}
	if geographyState == "not_reviewed" || (countryCount == 0 && geographyState != "unknown") {
		report.Issues = append(report.Issues, ValidationIssue{Path: "countries", Code: "GEOGRAPHY_REVIEW_REQUIRED", Message: "Add a sourced geographic affiliation or mark geography as reviewed and unknown."})
	}
	if movementState == "not_reviewed" || (primaryMovementCount == 0 && movementState != "unclassified") {
		report.Issues = append(report.Issues, ValidationIssue{Path: "movements", Code: "MOVEMENT_REVIEW_REQUIRED", Message: "Choose a primary movement or mark the painter as reviewed and unclassified."})
	}
	if coreCitationCount < 3 {
		report.Issues = append(report.Issues, ValidationIssue{Path: "citations", Code: "CORE_CITATIONS_MISSING", Message: "Attach citations for timeline dates, biography, and geography."})
	}

	var representativeCount, distinctOrderCount, incompleteArtworkCount int
	if err := r.db.QueryRow(ctx, `
		SELECT
		  count(*) FILTER (WHERE aw.status = 'published' AND aa.representative_order IS NOT NULL),
		  count(DISTINCT aa.representative_order) FILTER (WHERE aw.status = 'published' AND aa.representative_order IS NOT NULL),
		  count(*) FILTER (
		    WHERE aw.status = 'published' AND aa.representative_order IS NOT NULL
		      AND ((aw.creation_place_display IS NULL AND aw.creation_place_unknown_reason IS NULL)
		        OR (aw.current_location_text IS NULL AND aw.current_location_unknown_reason IS NULL)
		        OR NOT EXISTS (SELECT 1 FROM citations c WHERE c.entity_type = 'artwork' AND c.entity_id = aw.id))
		  )
		FROM artwork_artists aa
		JOIN artworks aw ON aw.id = aa.artwork_id
		WHERE aa.artist_id = $1`, id).Scan(&representativeCount, &distinctOrderCount, &incompleteArtworkCount); err != nil {
		return report, fmt.Errorf("query representative work validation: %w", err)
	}
	if representativeCount < 5 || representativeCount > 10 {
		report.Issues = append(report.Issues, ValidationIssue{Path: "artworks", Code: "REPRESENTATIVE_WORK_COUNT", Message: fmt.Sprintf("Select 5–10 published representative works; %d currently qualify.", representativeCount)})
	}
	if representativeCount != distinctOrderCount {
		report.Issues = append(report.Issues, ValidationIssue{Path: "artworks", Code: "REPRESENTATIVE_ORDER_CONFLICT", Message: "Representative work order values must be unique."})
	}
	if incompleteArtworkCount > 0 {
		report.Issues = append(report.Issues, ValidationIssue{Path: "artworks", Code: "ARTWORK_REVIEW_INCOMPLETE", Message: fmt.Sprintf("%d representative works are missing a reviewed place, location, or source citation.", incompleteArtworkCount)})
	}
	var badWorks, missingIdentity, missingInfluenceEvidence, badCoreSources int
	err := r.db.QueryRow(ctx, `
    SELECT
    (SELECT count(*) FROM artwork_artists aa JOIN artworks aw ON aw.id=aa.artwork_id LEFT JOIN media_assets ma ON ma.id=aw.primary_media_id
     WHERE aa.artist_id=$1 AND aa.representative_order IS NOT NULL AND aw.status='published'
     AND (aw.creation_year_start IS NULL OR aw.creation_year_end IS NULL OR aw.location_checked_at IS NULL
       OR nullif(trim(aw.title),'') IS NULL OR nullif(trim(aw.date_display),'') IS NULL
       OR aw.primary_media_id IS NULL OR ma.verified_at IS NULL
       OR (ma.storage_kind='local' AND (ma.rights_status NOT IN ('public_domain','cc0','cc_by','cc_by_sa','licensed')
          OR ma.source_page_url !~ '^https?://' OR ma.source_page_url IS NULL OR nullif(trim(ma.alt_text),'') IS NULL OR ma.license_label IS NULL))
       OR NOT EXISTS(SELECT 1 FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=aw.id AND s.is_active AND c.source_url ~ '^https?://'))),
    CASE WHEN EXISTS(SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=$1)
      OR EXISTS(SELECT 1 FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artist' AND c.entity_id=$1 AND s.is_active AND c.field_name='identity' AND c.source_url ~ '^https?://') THEN 0 ELSE 1 END,
    CASE WHEN EXISTS(SELECT 1 FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artist' AND c.entity_id=$1 AND c.field_name='influences' AND s.is_active AND c.source_url ~ '^https?://')
      OR EXISTS(SELECT 1 FROM influence_claims i JOIN citations c ON c.entity_type='influence' AND c.entity_id=i.id JOIN sources s ON s.id=c.source_id WHERE (i.source_artist_id=$1 OR i.target_artist_id=$1) AND i.status='published' AND s.is_active AND c.source_url ~ '^https?://') THEN 0 ELSE 1 END,
    3-(SELECT count(DISTINCT c.field_name) FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artist' AND c.entity_id=$1 AND c.field_name IN ('timeline_dates','biography','geography') AND s.is_active AND c.source_url ~ '^https?://')
    `, id).Scan(&badWorks, &missingIdentity, &missingInfluenceEvidence, &badCoreSources)
	if err != nil {
		return report, fmt.Errorf("validate source and rights evidence: %w", err)
	}
	if badWorks > 0 {
		report.Issues = append(report.Issues, ValidationIssue{"artworks", "ARTWORK_EVIDENCE_INCOMPLETE", fmt.Sprintf("%d works need date, location-check, source, or media-rights review. A reviewed placeholder is valid when no image can be used.", badWorks)})
	}
	if missingIdentity > 0 {
		report.Issues = append(report.Issues, ValidationIssue{"identity", "AUTHORITY_REQUIRED", "Add an external identity or a reviewed authority citation."})
	}
	if missingInfluenceEvidence > 0 {
		report.Issues = append(report.Issues, ValidationIssue{"influences", "INFLUENCE_CITATION_REQUIRED", "Cite a reviewed influence claim or the reviewed absence of documented influences."})
	}
	if badCoreSources > 0 && coreCitationCount == 3 {
		report.Issues = append(report.Issues, ValidationIssue{"citations", "INVALID_CORE_SOURCE", "Core citations must use active sources and HTTP(S) links."})
	}

	// Check every public work, including works outside the representative ten.
	var outOfScope int
	if err := r.db.QueryRow(ctx, `SELECT count(DISTINCT aw.id)
      FROM artwork_artists aa JOIN artworks aw ON aw.id=aa.artwork_id
      WHERE aa.artist_id=$1 AND aw.status='published' AND
      (artline_creation_scope(aw.creation_year_start,aw.creation_year_end,aw.date_precision)<>'eligible'
       OR NOT artline_has_selection_evidence(aw.id))`, id).Scan(&outOfScope); err != nil {
		return report, fmt.Errorf("validate creation cutoff and selection: %w", err)
	}
	if outOfScope > 0 {
		report.Issues = append(report.Issues, ValidationIssue{"artworks", "ARTWORK_CONTENT_SCOPE", fmt.Sprintf("%d published works need review: creation must be through 1970 and supported by a curated selection or documented museum holding.", outOfScope)})
	}
	report.Ready = len(report.Issues) == 0
	return report, nil
}

func (r *Repository) SetPublished(ctx context.Context, id string, expectedRevision int, published bool) (CatalogueArtist, error) {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return CatalogueArtist{}, err
	}
	defer tx.Rollback(ctx)
	// Publication is infrequent. Lock the small catalogue while validating dependencies
	// so a concurrent archive/edit cannot invalidate the gate before commit.
	if _, err = tx.Exec(ctx, "LOCK TABLE artists,artworks,artwork_artists,artist_countries,artist_movements,citations,influence_claims,media_assets,sources,external_identifiers,artwork_location_assertions,institutions,curated_collections,curated_collection_items IN SHARE ROW EXCLUSIVE MODE"); err != nil {
		return CatalogueArtist{}, err
	}
	if published {
		report, err := (&Repository{db: tx}).ValidateArtistForPublication(ctx, id)
		if err != nil {
			return CatalogueArtist{}, err
		}
		if report.Revision != expectedRevision {
			return CatalogueArtist{}, ErrRevisionConflict
		}
		if !report.Ready {
			return CatalogueArtist{}, &PublicationError{Report: report}
		}
	}
	status := "review"
	if published {
		status = "published"
	}
	var artist CatalogueArtist
	const statement = `
		UPDATE artists
		SET status = $2,
		    published_at = CASE WHEN $2 = 'published' THEN now() ELSE NULL END,
		    revision = revision + 1,
		    updated_at = now()
		WHERE id = $1 AND revision = $3 AND status <> 'archived'
		RETURNING id::text, slug, display_name, timeline_start_year, timeline_end_year,
		          timeline_display, status, revision, updated_at`
	err = tx.QueryRow(ctx, statement, id, status, expectedRevision).Scan(
		&artist.ID, &artist.Slug, &artist.DisplayName, &artist.TimelineStart,
		&artist.TimelineEnd, &artist.TimelineDisplay, &artist.Status, &artist.Revision,
		&artist.UpdatedAt,
	)
	if errors.Is(err, pgx.ErrNoRows) {
		var exists bool
		if checkErr := tx.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artists WHERE id = $1 AND status<>'archived')`, id).Scan(&exists); checkErr != nil {
			return artist, fmt.Errorf("check artist after publication update: %w", checkErr)
		}
		if exists {
			return artist, ErrRevisionConflict
		}
		return artist, ErrNotFound
	}
	if err != nil {
		return artist, fmt.Errorf("set artist publication status: %w", err)
	}
	if err := tx.Commit(ctx); err != nil {
		return artist, err
	}
	return artist, nil
}

func NormalizeSlug(value string) string {
	return strings.Trim(strings.ToLower(strings.TrimSpace(value)), "-")
}
