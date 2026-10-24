package exhibitions

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
)

func (r *Repository) enrichDetail(ctx context.Context, id string, raw []byte) (json.RawMessage, error) {
	var extra []byte
	err := r.db.QueryRow(ctx, `SELECT detail FROM exhibition_research WHERE exhibition_id=$1::uuid`, id).Scan(&extra)
	if errors.Is(err, pgx.ErrNoRows) {
		return raw, nil
	}
	if err != nil {
		return nil, err
	}
	base := map[string]json.RawMessage{}
	overlay := map[string]json.RawMessage{}
	if err = json.Unmarshal(raw, &base); err != nil {
		return nil, err
	}
	if err = json.Unmarshal(extra, &overlay); err != nil {
		return nil, err
	}
	for k, v := range overlay {
		base[k] = v
	}
	// Bounded related exhibitions use exact canonical/source artist identities.
	rows, err := r.db.Query(ctx, `WITH identities AS MATERIALIZED(SELECT person_id,artist_id FROM exhibition_research_people WHERE exhibition_id=$1::uuid), related AS MATERIALIZED(
 SELECT p.exhibition_id FROM identities a JOIN exhibition_research_people p ON p.person_id=a.person_id
 UNION SELECT p.exhibition_id FROM identities a JOIN exhibition_research_people p ON p.artist_id=a.artist_id WHERE a.artist_id IS NOT NULL)
 SELECT jsonb_build_object('id',e.id,'title',e.title,'startYear',e.start_year) FROM related r JOIN exhibitions e ON e.id=r.exhibition_id WHERE e.id<>$1::uuid AND e.status<>'archived' ORDER BY e.start_year DESC,e.id DESC LIMIT 6`, id)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	related := []json.RawMessage{}
	for rows.Next() {
		var v []byte
		if err = rows.Scan(&v); err != nil {
			return nil, err
		}
		related = append(related, json.RawMessage(v))
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	base["related"], err = json.Marshal(related)
	if err != nil {
		return nil, err
	}
	return json.Marshal(base)
}

func (r *Repository) Artwork(ctx context.Context, id string) (json.RawMessage, error) {
	if !ValidID(id) {
		return nil, ErrNotFound
	}
	if r.db == nil {
		return nil, ErrUnavailable
	}
	var raw []byte
	err := r.db.QueryRow(ctx, `SELECT o.detail || jsonb_build_object('appearanceCount',(SELECT count(*) FROM exhibition_object_entries x JOIN exhibitions e ON e.id=x.exhibition_id WHERE x.object_id=o.id AND e.status<>'archived')) FROM exhibition_objects o WHERE o.id=$1::uuid AND EXISTS(SELECT 1 FROM exhibition_object_entries x JOIN exhibitions e ON e.id=x.exhibition_id WHERE x.object_id=o.id AND e.status<>'archived')`, id).Scan(&raw)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, ErrNotFound
	}
	return json.RawMessage(raw), err
}

func (r *Repository) ArtworkAppearances(ctx context.Context, id, after string, limit int) (EntriesResponse, error) {
	return r.objectEntries(ctx, id, after, limit, "", true)
}

func (r *Repository) objectEntries(ctx context.Context, id, after string, limit int, participation string, reverse bool) (EntriesResponse, error) {
	out := EntriesResponse{Items: []json.RawMessage{}}
	if !ValidID(id) {
		return out, ErrNotFound
	}
	if limit < 1 || limit > 100 || (after != "" && !ValidID(after)) {
		return out, fmt.Errorf("invalid exhibition object page")
	}
	if r.db == nil {
		return out, ErrUnavailable
	}
	if reverse {
		if _, err := r.Artwork(ctx, id); err != nil {
			return out, err
		}
	}
	column, payload := "exhibition_id", "detail"
	if reverse {
		column, payload = "object_id", "appearance"
	}
	where := ` FROM exhibition_object_entries x JOIN exhibitions e ON e.id=x.exhibition_id WHERE x.` + column + `=$1::uuid AND e.status<>'archived' AND ($2='' OR x.participation=$2)`
	if err := r.db.QueryRow(ctx, `SELECT count(*)`+where, id, participation).Scan(&out.Total); err != nil {
		return out, err
	}
	if after == "" {
		after = "00000000-0000-0000-0000-000000000000"
	}
	rows, err := r.db.Query(ctx, `SELECT x.`+payload+where+` AND x.id>$3::uuid ORDER BY x.id LIMIT $4`, id, participation, after, limit+1)
	if err != nil {
		return out, err
	}
	defer rows.Close()
	for rows.Next() {
		var raw []byte
		if err = rows.Scan(&raw); err != nil {
			return out, err
		}
		out.Items = append(out.Items, json.RawMessage(raw))
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	if len(out.Items) > limit {
		out.HasMore = true
		out.Items = out.Items[:limit]
		var last struct {
			ID string `json:"id"`
		}
		if err = json.Unmarshal(out.Items[limit-1], &last); err != nil {
			return out, err
		}
		out.NextCursor = last.ID
	}
	return out, nil
}
