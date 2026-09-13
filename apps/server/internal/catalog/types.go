package catalog

import "time"

type TimelineFilter struct {
	StartYear   int
	EndYear     int
	Query       string
	Country     string
	Movement    string
	Status      string
	Regions     []string
	WorkType    string
	PopularOnly bool
	Countries   []string
	Movements   []string
	Painters    []string
	WorkTypes   []string
}

type MovementSummary struct {
	Slug  string `json:"slug"`
	Name  string `json:"name"`
	Color string `json:"color"`
}

type TimelineArtist struct {
	ID           string          `json:"id"`
	Slug         string          `json:"slug"`
	Name         string          `json:"name"`
	StartYear    int             `json:"start_year"`
	EndYear      int             `json:"end_year"`
	DateDisplay  string          `json:"date_display"`
	Movement     MovementSummary `json:"movement"`
	Countries    []string        `json:"countries"`
	ArtworkCount int             `json:"artwork_count"`
	Status       string          `json:"status"`
}

type TimelineBin struct {
	StartYear int    `json:"start_year"`
	EndYear   int    `json:"end_year"`
	Movement  string `json:"movement"`
	Color     string `json:"color"`
	Count     int    `json:"count"`
}

type TimelineResponse struct {
	Range struct {
		Start int `json:"start"`
		End   int `json:"end"`
	} `json:"range"`
	Mode             string                    `json:"mode"`
	Items            []TimelineArtist          `json:"items"`
	Bins             []TimelineBin             `json:"bins"`
	Total            int                       `json:"total"`
	Periods          []TimelinePeriod          `json:"periods"`
	PopularOnly      bool                      `json:"popular_only"`
	SuggestedFilters []TimelineSuggestedFilter `json:"suggested_filters"`
}

type TimelineSuggestedFilter struct {
	Key   string `json:"key"`
	Value string `json:"value"`
	Name  string `json:"name"`
	Count int    `json:"count"`
}

type TimelinePeriod struct {
	StartYear int `json:"start_year"`
	EndYear   int `json:"end_year"`
	Count     int `json:"count"`
}

type Artwork struct {
	ID                         string           `json:"id"`
	Slug                       string           `json:"slug"`
	Title                      string           `json:"title"`
	AlternateTitle             *string          `json:"alternate_title"`
	DateDisplay                string           `json:"date_display"`
	CreationYearStart          *int             `json:"creation_year_start"`
	CreationYearEnd            *int             `json:"creation_year_end"`
	DatePrecision              string           `json:"date_precision"`
	WorkType                   string           `json:"work_type"`
	UnlinkedCreatorLabel       *string          `json:"unlinked_creator_label"`
	CulturalContext            *string          `json:"cultural_context"`
	ObjectForm                 *string          `json:"object_form"`
	DescriptionMD              *string          `json:"description_md,omitempty"`
	MediumText                 *string          `json:"medium_text"`
	DimensionsText             *string          `json:"dimensions_text"`
	AccessionNumber            *string          `json:"accession_number"`
	CreationPlaceUnknownReason *string          `json:"creation_place_unknown_reason"`
	CreationPlaceDisplay       *string          `json:"creation_place_display"`
	CurrentLocationText        *string          `json:"current_location_text"`
	MediaURL                   *string          `json:"media_url"`
	AltText                    *string          `json:"alt_text"`
	RightsStatus               *string          `json:"rights_status"`
	AttributionText            *string          `json:"attribution_text"`
	RepresentativeOrder        *int             `json:"representative_order"`
	Status                     string           `json:"status"`
	Revision                   int              `json:"revision"`
	AttributionRole            string           `json:"attribution_role"`
	SourcePageURL              *string          `json:"source_page_url"`
	LicenseLabel               *string          `json:"license_label"`
	LicenseURL                 *string          `json:"license_url"`
	LocationCheckedAt          *time.Time       `json:"location_checked_at"`
	Citations                  []Citation       `json:"citations"`
	Holding                    *MuseumRef       `json:"holding"`
	Display                    *DisplayEvidence `json:"display"`
}

type Influence struct {
	ID               string     `json:"id"`
	Name             string     `json:"name"`
	Slug             *string    `json:"slug"`
	Direction        string     `json:"direction"`
	RelationshipType string     `json:"relationship_type"`
	EvidenceLevel    string     `json:"evidence_level"`
	EvidenceNote     string     `json:"evidence_note"`
	Citations        []Citation `json:"citations"`
}

type Citation struct {
	FieldName    string `json:"field_name"`
	SourceName   string `json:"source_name"`
	SourceURL    string `json:"source_url"`
	EvidenceNote string `json:"evidence_note,omitempty"`
}

type ArtistDetail struct {
	ID              string          `json:"id"`
	Slug            string          `json:"slug"`
	DisplayName     string          `json:"display_name"`
	SortName        string          `json:"sort_name"`
	TimelineStart   int             `json:"timeline_start_year"`
	TimelineEnd     int             `json:"timeline_end_year"`
	TimelineDisplay string          `json:"timeline_display"`
	TimelineBasis   string          `json:"timeline_basis"`
	BiographyMD     *string         `json:"biography_md"`
	Status          string          `json:"status"`
	Revision        int             `json:"revision"`
	EntityType      string          `json:"entity_type"`
	Aliases         []string        `json:"aliases"`
	Influences      []Influence     `json:"influences"`
	Movement        MovementSummary `json:"movement"`
	Countries       []string        `json:"countries"`
	Artworks        []Artwork       `json:"artworks"`
	Citations       []Citation      `json:"citations"`
}

type CatalogueArtist struct {
	ID              string    `json:"id"`
	Slug            string    `json:"slug"`
	DisplayName     string    `json:"display_name"`
	TimelineStart   int       `json:"timeline_start_year"`
	TimelineEnd     int       `json:"timeline_end_year"`
	TimelineDisplay string    `json:"timeline_display"`
	Status          string    `json:"status"`
	Revision        int       `json:"revision"`
	UpdatedAt       time.Time `json:"updated_at"`
}

type ArtistInput struct {
	Slug              string  `json:"slug"`
	DisplayName       string  `json:"display_name"`
	SortName          string  `json:"sort_name"`
	EntityType        string  `json:"entity_type"`
	TimelineStartYear int     `json:"timeline_start_year"`
	TimelineEndYear   int     `json:"timeline_end_year"`
	TimelineDisplay   string  `json:"timeline_display"`
	TimelineBasis     string  `json:"timeline_basis"`
	BiographyMD       *string `json:"biography_md"`
	Status            string  `json:"status"`
	ExpectedRevision  int     `json:"expected_revision"`
}

type CoverageSummary struct {
	ByStatus      map[string]int `json:"by_status"`
	NordicArtists int            `json:"nordic_artists"`
	AsianArtists  int            `json:"asian_artists"`
	MissingWorks  int            `json:"missing_representative_works"`
	MissingBio    int            `json:"missing_biography"`
	TotalArtists  int            `json:"total_artists"`
}

type FacetOption struct {
	Slug  string `json:"slug"`
	Name  string `json:"name"`
	Color string `json:"color,omitempty"`
	Count int    `json:"count"`
}

type TimelineFacets struct {
	Movements []FacetOption `json:"movements"`
	Countries []FacetOption `json:"countries"`
	Regions   []FacetOption `json:"regions"`
}

type ValidationIssue struct {
	Path    string `json:"path"`
	Code    string `json:"code"`
	Message string `json:"message"`
}

type PublicationValidation struct {
	ArtistID string            `json:"artist_id"`
	Ready    bool              `json:"ready"`
	Revision int               `json:"revision"`
	Issues   []ValidationIssue `json:"issues"`
}
