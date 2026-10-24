package events

import (
	"context"
	_ "embed"
	"encoding/json"
	"fmt"
	"net/url"
	"regexp"
	"strings"

	"github.com/jackc/pgx/v5"
)

type artworkSelection struct {
	EventID     string `json:"eventId"`
	SourceID    string `json:"sourceId"`
	ArtworkSlug string `json:"artworkSlug"`
	Label       string `json:"label,omitempty"`
	Relation    string `json:"relation,omitempty"`
	EvidenceURL string `json:"evidenceUrl,omitempty"`
}

// Slugs reconcile the same reviewed object across independently imported
// catalogues. Media paths, rights and destination IDs always come from the DB.
//
//go:embed artwork-selection.json
var artworkData []byte
var selectedArtworks = readArtworkSelection(artworkData)

func readArtworkSelection(raw []byte) map[string]artworkSelection {
	var rows []artworkSelection
	if err := json.Unmarshal(raw, &rows); err != nil {
		panic(err)
	}
	out := make(map[string]artworkSelection, len(rows))
	slug := regexp.MustCompile(`^[a-z0-9]+(?:[-_][a-z0-9]+)*$`)
	source := regexp.MustCompile(`^Q[1-9][0-9]*$`)
	for _, row := range rows {
		image, ok := selectedImages[row.EventID]
		// New catalogue illustrations do not need an independent legacy image.
		// Their event identity, relationship, caption and evidence are explicit.
		identity := source.MatchString(row.SourceID) && row.EventID == "event-"+strings.ToLower(row.SourceID)
		if ok {
			identity = row.SourceID == image.SourceID
		}
		if !identity || !slug.MatchString(row.ArtworkSlug) {
			panic("invalid event artwork selection: " + row.EventID)
		}
		if row.Label != "" {
			u, err := url.Parse(row.EvidenceURL)
			relation := row.Relation == "depiction" || row.Relation == "portrait" || row.Relation == "place" || row.Relation == "context"
			if !relation || strings.TrimSpace(row.Label) != row.Label || len(row.Label) > 500 || strings.ContainsAny(row.Label, "\r\n") || err != nil || u.Scheme != "https" || u.Host == "" || u.User != nil {
				panic("incomplete event artwork context: " + row.EventID)
			}
		} else if !ok || row.Relation != "" || row.EvidenceURL != "" {
			panic("event artwork caption required: " + row.EventID)
		}
		if _, exists := out[row.EventID]; exists {
			panic("duplicate event artwork selection: " + row.EventID)
		}
		out[row.EventID] = row
	}
	return out
}

type imageQuerier interface {
	Query(context.Context, string, ...any) (pgx.Rows, error)
}

const artworkImagesSQL = `SELECT a.slug,a.id::text,a.title,m.storage_path,
 coalesce(m.source_page_url,''),coalesce(nullif(m.creator_credit,''),m.attribution_text,''),
 coalesce(nullif(m.license_label,''),m.rights_status),coalesce(m.license_url,''),
 coalesce(to_char(m.verified_at AT TIME ZONE 'UTC','YYYY-MM-DD'),''),
 CASE WHEN creator.slug IS NOT NULL THEN '/artists/'||creator.slug||'/works/'||a.id::text
 ELSE '/all?itemType=artwork&item='||a.id::text END
 FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id
 LEFT JOIN LATERAL (
 SELECT ar.slug FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id
 WHERE aa.artwork_id=a.id AND ar.status<>'archived'
 ORDER BY (aa.attribution_role='primary') DESC,ar.slug LIMIT 1
 ) creator ON true
 WHERE a.slug=ANY($1::text[]) AND a.status<>'archived' AND a.work_type='painting'
 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)<>'excluded'
 AND m.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$'`

// ResolveImages enriches an already visible, bounded event page in one query.
// A reviewed artwork with missing/withdrawn media never falls back to the old
// independent reproduction, which could outlive a catalogue image correction.
func ResolveImages(ctx context.Context, db imageQuerier, items []Event) error {
	if len(items) > 1000 {
		return fmt.Errorf("event image page exceeds 1000 records")
	}
	slugs := []string{}
	seen := map[string]bool{}
	for i := range items {
		attachImage(&items[i])
		if selected, ok := selectedArtworks[items[i].ID]; ok && selected.SourceID == items[i].SourceID {
			items[i].Image = nil
			if !seen[selected.ArtworkSlug] {
				slugs = append(slugs, selected.ArtworkSlug)
				seen[selected.ArtworkSlug] = true
			}
		}
	}
	if len(slugs) == 0 {
		return nil
	}
	rows, err := db.Query(ctx, artworkImagesSQL, slugs)
	if err != nil {
		return err
	}
	defer rows.Close()
	images := map[string]Image{}
	for rows.Next() {
		var slug string
		image := Image{Artwork: &ArtworkLink{}}
		if err := rows.Scan(&slug, &image.Artwork.ID, &image.Artwork.Title, &image.ImageURL, &image.SourceURL, &image.Credit, &image.License, &image.LicenseURL, &image.CheckedAt, &image.Artwork.Href); err != nil {
			return err
		}
		images[slug] = image
	}
	if err := rows.Err(); err != nil {
		return err
	}
	for i := range items {
		selected, ok := selectedArtworks[items[i].ID]
		if !ok || selected.SourceID != items[i].SourceID {
			continue
		}
		if image, ok := images[selected.ArtworkSlug]; ok {
			// Keep the historical relationship (e.g. a later depiction) explicit.
			image.Label = selected.Label
			if image.Label == "" {
				image.Label = selectedImages[items[i].ID].Label
			}
			if !strings.Contains(strings.ToLower(image.Label), strings.ToLower(image.Artwork.Title)) {
				image.Label = image.Artwork.Title + " · " + image.Label
			}
			items[i].Image = &image
		}
	}
	return nil
}
