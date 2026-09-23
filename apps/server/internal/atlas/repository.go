package atlas

import (
	"context"
	"encoding/json"
	"fmt"
	"slices"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type atlasDB interface {
	Query(context.Context, string, ...any) (pgx.Rows, error)
	QueryRow(context.Context, string, ...any) pgx.Row
}
type Repository struct{ db atlasDB }

func NewRepository(db *pgxpool.Pool) *Repository {
	if db == nil {
		return &Repository{}
	}
	return &Repository{db}
}

// Both selections remain distinguishable in their native detail records.
const selectedArt = `SELECT ci.artwork_id FROM curated_collection_items ci JOIN curated_collections cc ON cc.id=ci.collection_id
 WHERE cc.status<>'archived' AND ($3 OR cc.status='published')
 AND (cc.curator_kind='owner' OR (ci.source_url IS NOT NULL AND EXISTS(SELECT 1 FROM sources s WHERE s.id=ci.source_id AND s.is_active)))`
const artScope = ` FROM artworks a WHERE a.status<>'archived' AND ($3 OR a.status='published')
 AND a.date_precision IN ('exact','circa','range','circa_range','decade','century')
 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
 AND coalesce(a.creation_year_start,a.creation_year_end)<>0 AND coalesce(a.creation_year_end,a.creation_year_start)<>0
 AND coalesce(a.creation_year_start,a.creation_year_end)<=$2 AND coalesce(a.creation_year_end,a.creation_year_start)>=$1
 AND (a.id IN (` + selectedArt + `) OR (NOT $5 AND EXISTS(SELECT 1 FROM artwork_location_assertions h JOIN sources s ON s.id=h.source_id AND s.is_active JOIN institutions i ON i.id=h.institution_id AND i.status<>'archived' AND ($3 OR i.status='published') WHERE h.artwork_id=a.id AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL)))
 AND (NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id) OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id AND ar.status<>'archived' AND ($3 OR ar.status='published')))
 AND ($4='' OR strpos(lower(a.title),lower($4))>0 OR strpos(lower(coalesce(a.unlinked_creator_label,'')),lower($4))>0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id AND ar.status<>'archived' AND ($3 OR ar.status='published') AND strpos(lower(ar.display_name),lower($4))>0))
 AND ($6='' OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id JOIN artist_countries ac ON ac.artist_id=ar.id JOIN countries c ON c.code=ac.country_code WHERE aa.artwork_id=a.id AND ar.status<>'archived' AND ($3 OR ar.status='published') AND c.region_code=$6)
 OR EXISTS(SELECT 1 FROM artwork_places ap JOIN places pl ON pl.id=ap.place_id JOIN countries c ON c.code=pl.country_code WHERE ap.artwork_id=a.id AND c.region_code=$6))`
const bookScope = ` FROM book_records b LEFT JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum
 WHERE b.status<>'archived' AND ($3 OR b.status='published') AND b.start_year<=$2 AND b.end_year>=$1 AND b.end_year<=2000
 AND ($4='' OR strpos(b.search_text,lower($4))>0) AND (NOT $5 OR d.top100) AND ($6='' OR $6=ANY(d.regions))`
const eventScope = ` FROM event_records e WHERE e.status<>'archived' AND ($3 OR e.status='published') AND e.start_year<=$2 AND e.end_year>=$1
 AND ($4='' OR strpos(e.search_text,lower($4))>0) AND (NOT $5 OR e.top100)
 AND ($6='' OR EXISTS(SELECT 1 FROM unnest(e.regions) region WHERE replace(lower(region),' ','-')=$6))`

type provider struct{ keys, details string }

// Native predicates are applied before any creator, image or source enrichment.
// Only page keys reach the detail projection; aggregates use IDs/dates only.
var providers = map[string]provider{
	"artwork": {`SELECT a.id::text AS id,coalesce(a.creation_year_start,a.creation_year_end) AS start_year,coalesce(a.creation_year_end,a.creation_year_start) AS end_year` + artScope,
		`SELECT p.id,p.start_year,p.end_year,a.title,
 coalesce((SELECT string_agg(names.name,', ' ORDER BY names.name) FROM (SELECT DISTINCT ar.display_name AS name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id AND ar.status<>'archived' AND ($3 OR ar.status='published')) names),a.unlinked_creator_label,'Creator not recorded'),a.date_display,a.date_precision<>'exact'
 FROM page p JOIN artworks a ON a.id=p.id::uuid`},
	"book":  {`SELECT b.id,b.start_year,b.end_year` + bookScope, `SELECT p.id,p.start_year,p.end_year,b.title,b.author_label,b.record->>'years',coalesce((b.record->>'approximate')::boolean,false) FROM page p JOIN book_records b ON b.id=p.id`},
	"event": {`SELECT e.id,e.start_year,e.end_year` + eventScope, `SELECT p.id,p.start_year,p.end_year,e.title,e.kind,e.record->>'years',coalesce((e.record->>'approximate')::boolean,false) FROM page p JOIN event_records e ON e.id=p.id`},
}

func (r *Repository) List(ctx context.Context, f Filter) (Response, error) {
	out := Response{Range: f.Range, Bounds: Bounds, Lanes: []Lane{}, Ticks: Ticks(f.Range)}
	if err := f.Validate(); err != nil {
		return out, err
	}
	focus := presetFocus(f.PresetID)
	if f.Selection && len(f.Types) == 0 && len(f.Picks) == 0 {
		return out, nil
	}
	if r.db == nil {
		return out, fmt.Errorf("atlas unavailable")
	}
	args := []any{pgx.QueryExecModeCacheDescribe, f.Start, f.End, f.Preview, strings.TrimSpace(f.Query), f.Highlights, f.Region}
	for _, definition := range Definitions {
		if (f.Selection && !slices.Contains(f.Types, definition.Key) && len(f.Picks[definition.Key]) == 0) || (!f.Selection && len(f.Types) > 0 && !slices.Contains(f.Types, definition.Key)) {
			continue
		}
		lane := Lane{Definition: definition, Mode: "individual", Items: []Item{}, Density: []Period{}}
		p := providers[definition.Key]
		var picked []string
		if f.Selection && !slices.Contains(f.Types, definition.Key) {
			picked = f.Picks[definition.Key]
		}
		args := append(slices.Clone(args), picked)
		entity := f.Entities[definition.Key]
		if picked != nil {
			entity = nil
		}
		// Book/event editorial selections can override the shared default.
		// A popular painter filter is independent of artwork highlight membership.
		if entity.Has("top100") {
			args[5] = false
		}
		clause := entityPredicate(definition.Key, entity, &args)
		highlight := "a.id IN (" + selectedArt + ")"
		if definition.Key == "book" || definition.Key == "event" {
			column := "d.top100"
			if definition.Key == "event" {
				column = "e.top100"
			}
			highlight = presetHighlightPredicate(definition.Key, focus, &args)
			p.keys = strings.ReplaceAll(p.keys, column, highlight)
			clause = strings.ReplaceAll(clause, column, highlight)
		}
		var selection string
		key := "b.id=ANY($7::text[])"
		if definition.Key == "event" {
			key = "e.id=ANY($7::text[])"
		}
		if definition.Key == "artwork" {
			key = "a.id=ANY($7::text[]::uuid[])"
		}
		if picked != nil {
			// An explicitly chosen ID is not subject to the layer's discovery filters.
			args[5] = false
			selection = key
		} else {
			if ids := f.Picks[definition.Key]; f.Selection && len(ids) > 0 {
				args[7] = ids
				if args[5] == true {
					clause = "(" + clause + ") AND (" + highlight + ")"
					args[5] = false
				}
				selection = "(" + clause + ") OR " + key
			} else {
				// Keep the creator predicate conjunctive so PostgreSQL can start
				// with the selected painter's indexed artwork links.
				selection = "$7::text[] IS NULL AND (" + clause + ")"
			}
		}
		scope := "(" + selection + ") AND (" + creatorPredicate(definition.Key, f.Creators, &args) + ") AND (" + geographyPredicate(definition.Key, f, &args) + ") AND (" + focusPredicate(definition.Key, focus, &args) + ")"
		// All is an illustrated discovery view, including legacy explicit picks.
		if definition.Key == "artwork" {
			scope += ` AND EXISTS(SELECT 1 FROM media_assets image WHERE image.id=a.primary_media_id AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$')`
		}
		prefix := ""
		if definition.Key == "artwork" && (len(f.Creators) > 0 || focus != nil && !focus.Global || len(f.Countries) > 0 || len(f.Continents) > 0 || len(entity["country"]) > 0 || len(entity["region"]) > 0) {
			// With several countries the planner can otherwise check holdings and
			// visibility across the whole catalogue before applying geography.
			// Materialize only the filtered native columns; enrich page IDs below.
			prefix = `artwork_scope AS MATERIALIZED (
 SELECT a.id,a.status,a.date_precision,a.creation_year_start,a.creation_year_end,a.title,a.unlinked_creator_label
 FROM artworks a WHERE ` + scope + `),`
			p.keys = strings.Replace(p.keys, " FROM artworks a WHERE", " FROM artwork_scope a WHERE", 1)
		} else {
			p.keys += " AND " + scope
		}
		next := len(args)
		starts, ends := []int{}, []int{}
		for _, period := range Periods(f.Range) {
			starts = append(starts, period.Start)
			ends = append(ends, period.End)
		}
		c, _ := decodeCursor(f.After[definition.Key], f, definition.Key)
		pageWhere := fmt.Sprintf("(start_year,id)>($%d,$%d)", next+2, next+3)
		pageOrder := "start_year,id"
		if f.NeighborOf != "" {
			// Seek within the same eligible/filter-scoped relation. An anchor
			// outside this view yields no neighbours and never leaks a record.
			op := " > "
			if f.Direction == "previous" {
				op = " < "
				pageOrder = "start_year DESC,id DESC"
			}
			pageWhere = fmt.Sprintf("$%d::int IS NOT NULL AND (start_year,id)"+op+"(SELECT start_year,id FROM matching WHERE id=$%d)", next+2, next+3)
			c.ID = f.NeighborOf
			starts, ends = []int{}, []int{}
		}
		// Eligibility and geography can be costly for a broad filter. Evaluate the
		// scoped ID/date relation once for totals, density and the bounded page.
		// Only returned page IDs reach creator/title enrichment.
		query := fmt.Sprintf(`WITH `+prefix+`matching AS MATERIALIZED (`+p.keys+`),
 totals AS (SELECT count(*) AS total FROM matching),
 periods AS (SELECT * FROM unnest($%d::int[],$%d::int[]) p(start_year,end_year)),
 page AS MATERIALIZED (SELECT * FROM matching WHERE `+pageWhere+` ORDER BY `+pageOrder+` LIMIT $%d)
 SELECT total,
 coalesce((SELECT jsonb_agg(bins ORDER BY start_year) FROM (
  SELECT p.start_year,p.end_year,count(*) AS count FROM periods p
  JOIN matching m ON m.start_year<=p.end_year AND m.end_year>=p.start_year
  WHERE totals.total>60 GROUP BY p.start_year,p.end_year
 ) bins),'[]'::jsonb),
 coalesce((SELECT jsonb_agg(details ORDER BY "startYear",id) FROM (`+p.details+`)
 details(id,"startYear","endYear",title,context,years,approximate)),'[]'::jsonb)
 FROM totals`, next, next+1, next+4)
		var density, items []byte
		pageLimit := f.Limit + 1
		if f.NeighborOf != "" {
			pageLimit = 1
		}
		if err := r.db.QueryRow(ctx, query, append(slices.Clone(args), starts, ends, c.Year, c.ID, pageLimit)...).Scan(&lane.Total, &density, &items); err != nil {
			return out, err
		}
		if err := json.Unmarshal(density, &lane.Density); err != nil {
			return out, err
		}
		if err := json.Unmarshal(items, &lane.Items); err != nil {
			return out, err
		}
		for i := range lane.Items {
			lane.Items[i].Type = definition.Key
			if focus != nil && slices.Contains(focus.Context[definition.Key], lane.Items[i].ID) {
				lane.Items[i].Relation = "context"
			}
		}
		out.Total += lane.Total
		if lane.Total > 60 {
			lane.Mode = "density"
		}
		if len(lane.Items) > f.Limit {
			lane.Items = lane.Items[:f.Limit]
			lane.NextCursor = encodeCursor(lane.Items[len(lane.Items)-1], f, definition.Key)
		}
		if definition.Key == "artwork" {
			if err := r.attachImages(ctx, lane.Items); err != nil {
				return out, err
			}
		}
		out.Lanes = append(out.Lanes, lane)
	}
	return out, nil
}
func (r *Repository) ArtworkVisible(ctx context.Context, id string, preview bool) (bool, error) {
	var exists bool
	err := r.db.QueryRow(ctx, `SELECT EXISTS(SELECT 1`+artScope+` AND a.id=$7::uuid)`, pgx.QueryExecModeCacheDescribe, Bounds.Start, Bounds.End, preview, "", false, "", id).Scan(&exists)
	return exists, err
}
