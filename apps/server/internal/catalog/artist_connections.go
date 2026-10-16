package catalog

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
)

const ArtistConnectionsPageSize = 3

var ErrConnectionsFilter = errors.New("invalid artist connections filter")

type ArtistConnection struct {
	ID     string      `json:"id"`
	Name   string      `json:"name"`
	Slug   *string     `json:"slug"`
	Claims []Influence `json:"claims"`
}
type ArtistConnectionsPage struct {
	Items      []ArtistConnection `json:"items"`
	Total      int                `json:"total"`
	NextCursor string             `json:"next_cursor"`
}
type ArtistConnections struct {
	Incoming ArtistConnectionsPage `json:"incoming"`
	Outgoing ArtistConnectionsPage `json:"outgoing"`
}
type connectionCursor struct {
	Artist    string `json:"a"`
	Direction string `json:"d"`
	Rank      int    `json:"r"`
	Name      string `json:"n"`
	ID        string `json:"i"`
}

func parseConnectionCursor(raw, artistID, direction string) (connectionCursor, error) {
	c := connectionCursor{Artist: artistID, Direction: direction}
	if direction != "incoming" && direction != "outgoing" || len(raw) > 4096 {
		return c, ErrConnectionsFilter
	}
	if raw == "" {
		return c, nil
	}
	b, err := base64.RawURLEncoding.DecodeString(raw)
	if err != nil || json.Unmarshal(b, &c) != nil || c.Artist != artistID || c.Direction != direction || c.Rank < 0 || c.Rank > 4 || len(c.Name) > 1000 || len(c.ID) < 36 || len(c.ID) > 42 {
		return c, ErrConnectionsFilter
	}
	return c, nil
}

// Each direction starts from an indexed artist FK. Group only resolved artist
// IDs; unresolved source labels keep their distinct claim identities. Citations
// and full claim detail are enriched only for the three returned connections.
func artistConnectionsQuery(direction string) string {
	predicate, other := "i.target_artist_id=$1", "s"
	if direction == "outgoing" {
		predicate, other = "i.source_artist_id=$1", "t"
	}
	return `WITH eligible AS MATERIALIZED (
 SELECT i.id,i.relationship_type,i.evidence_level,i.evidence_note,
 coalesce(` + other + `.id::text,'claim:'||i.id::text) AS connection_id,
 coalesce(` + other + `.display_name,i.source_label) AS name,` + other + `.slug,
 CASE i.evidence_level WHEN 'documented' THEN 0 WHEN 'scholarly_consensus' THEN 1
 WHEN 'scholarly_interpretation' THEN 2 WHEN 'editorial_inference' THEN 3 ELSE 4 END AS rank
 FROM influence_claims i LEFT JOIN artists s ON s.id=i.source_artist_id
 JOIN artists t ON t.id=i.target_artist_id
 WHERE ` + predicate + ` AND i.status<>'archived' AND t.status<>'archived'
 AND (s.id IS NULL OR s.status<>'archived')
 AND EXISTS(SELECT 1 FROM citations c JOIN sources src ON src.id=c.source_id
 WHERE c.entity_type='influence' AND c.entity_id=i.id AND src.is_active)
 ), grouped AS MATERIALIZED (
 SELECT connection_id,min(name) AS name,min(slug) AS slug,min(rank) AS rank
 FROM eligible GROUP BY connection_id
 ), page AS (
 SELECT * FROM grouped WHERE NOT $2 OR (rank,name COLLATE "C",connection_id COLLATE "C")>($3,$4 COLLATE "C",$5 COLLATE "C")
 ORDER BY rank,name COLLATE "C",connection_id COLLATE "C" LIMIT 4
 )
 SELECT (SELECT count(*) FROM grouped), coalesce(jsonb_agg(jsonb_build_object(
 'id',p.connection_id,'name',p.name,'slug',p.slug,'rank',p.rank,
 'claims',(SELECT jsonb_agg(jsonb_build_object('id',e.id,'name',p.name,'slug',p.slug,
 'direction',$6::text,'relationship_type',e.relationship_type,'evidence_level',e.evidence_level,
 'evidence_note',e.evidence_note,'citations','[]'::jsonb) ORDER BY e.rank,e.relationship_type,e.id)
 FROM eligible e WHERE e.connection_id=p.connection_id)
 ) ORDER BY p.rank,p.name COLLATE "C",p.connection_id COLLATE "C"),'[]'::jsonb) FROM page p`
}

func (r *Repository) ArtistConnectionPage(ctx context.Context, slug, direction, cursor string) (ArtistConnectionsPage, error) {
	if _, err := parseConnectionCursor("", "", direction); err != nil || len(cursor) > 4096 {
		return ArtistConnectionsPage{}, ErrConnectionsFilter
	}
	artist, err := r.ArtistIdentity(ctx, slug)
	if err != nil {
		return ArtistConnectionsPage{}, err
	}
	return r.artistConnectionPage(ctx, artist.ID, direction, cursor)
}
func (r *Repository) artistConnectionPage(ctx context.Context, id, direction, rawCursor string) (ArtistConnectionsPage, error) {
	out := ArtistConnectionsPage{Items: []ArtistConnection{}}
	cursor, err := parseConnectionCursor(rawCursor, id, direction)
	if err != nil {
		return out, err
	}
	var payload []byte
	err = r.db.QueryRow(ctx, artistConnectionsQuery(direction), id, rawCursor != "", cursor.Rank, cursor.Name, cursor.ID, direction).Scan(&out.Total, &payload)
	if err != nil {
		return out, fmt.Errorf("artist connections: %w", err)
	}
	var rows []struct {
		ArtistConnection
		Rank int `json:"rank"`
	}
	if err = json.Unmarshal(payload, &rows); err != nil {
		return out, err
	}
	if len(rows) > ArtistConnectionsPageSize {
		last := rows[ArtistConnectionsPageSize-1]
		b, _ := json.Marshal(connectionCursor{id, direction, last.Rank, last.Name, last.ID})
		out.NextCursor = base64.RawURLEncoding.EncodeToString(b)
		rows = rows[:ArtistConnectionsPageSize]
	}
	claims := []Influence{}
	for _, row := range rows {
		claims = append(claims, row.Claims...)
	}
	claims, err = r.enrichInfluenceCitations(ctx, claims)
	if err != nil {
		return out, err
	}
	offset := 0
	for _, row := range rows {
		item := row.ArtistConnection
		item.Claims = claims[offset : offset+len(item.Claims)]
		offset += len(item.Claims)
		out.Items = append(out.Items, item)
	}
	return out, nil
}
