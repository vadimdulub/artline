package exhibitions

import (
	"context"
	"encoding/json"
	"fmt"
)

// Enrich only the returned artists with indexed portrait/key-work lookups. A
// key work illustrates its creator; it does not establish exhibition attendance.
const participantImagesQuery = `SELECT a.id::text,jsonb_build_object(
 'image',image.storage_path,'imageKind',image.kind,'imageTitle',image.title,
 'imageArtworkId',image.artwork_id,'imageWidth',image.width,'imageHeight',image.height,
 'imageCredit',coalesce(image.attribution_text,image.creator_credit,image.provider_name),
 'imageLicense',image.license_label,'imageSource',image.source_page_url)
 FROM unnest($1::uuid[]) requested(artist_id)
 JOIN artists a ON a.id=requested.artist_id AND a.status<>'archived'
 LEFT JOIN artist_key_artworks k ON k.artist_id=a.id
 LEFT JOIN artworks w ON w.id=k.artwork_id AND w.status<>'archived'
   AND artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision)='eligible'
 JOIN LATERAL (
   SELECT m.*,candidate.kind,candidate.title,candidate.artwork_id
   FROM (VALUES (a.portrait_media_id,'portrait',NULL::text,NULL::uuid,0),
                (w.primary_media_id,'artwork',w.title,w.id,1))
     candidate(media_id,kind,title,artwork_id,priority)
   JOIN media_assets m ON m.id=candidate.media_id
   WHERE m.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$'
   ORDER BY candidate.priority LIMIT 1
 ) image ON true`

func participantString(person map[string]json.RawMessage, key string) string {
	var value string
	_ = json.Unmarshal(person[key], &value)
	return value
}

func applyParticipantImages(people []map[string]json.RawMessage, images map[string]map[string]json.RawMessage) {
	for _, person := range people {
		// Preserve an editorial study's existing sourced portrait and its credits.
		if participantString(person, "portrait") != "" {
			continue
		}
		for key, value := range images[participantString(person, "artist_id")] {
			person[key] = value
		}
	}
}

func (r *Repository) enrichParticipantImages(ctx context.Context, raw json.RawMessage) (json.RawMessage, error) {
	var record map[string]json.RawMessage
	if err := json.Unmarshal(raw, &record); err != nil {
		return nil, err
	}
	var people []map[string]json.RawMessage
	if err := json.Unmarshal(record["participants"], &people); err != nil {
		return nil, err
	}
	ids := []string{}
	seen := map[string]bool{}
	for _, person := range people {
		id := participantString(person, "artist_id")
		if ValidID(id) && !seen[id] && participantString(person, "portrait") == "" {
			seen[id] = true
			ids = append(ids, id)
		}
	}
	if len(ids) == 0 {
		return raw, nil
	}
	rows, err := r.db.Query(ctx, participantImagesQuery, ids)
	if err != nil {
		return nil, fmt.Errorf("query exhibition artist images: %w", err)
	}
	defer rows.Close()
	images := map[string]map[string]json.RawMessage{}
	for rows.Next() {
		var id string
		var image []byte
		var fields map[string]json.RawMessage
		if err = rows.Scan(&id, &image); err != nil {
			return nil, err
		}
		if err = json.Unmarshal(image, &fields); err != nil {
			return nil, err
		}
		images[id] = fields
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	applyParticipantImages(people, images)
	record["participants"], err = json.Marshal(people)
	if err != nil {
		return nil, err
	}
	return json.Marshal(record)
}
