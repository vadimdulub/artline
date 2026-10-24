package atlas

import (
	"context"
	"encoding/json"
	"fmt"
	"slices"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/timeline"
)

type atlasDB interface {
	Query(context.Context, string, ...any) (pgx.Rows, error)
	QueryRow(context.Context, string, ...any) pgx.Row
}
type Repository struct {
	db         atlasDB
	pool       *pgxpool.Pool
	aggregates *aggregateCache
}

func NewRepository(db *pgxpool.Pool) *Repository {
	if db == nil {
		return &Repository{}
	}
	return &Repository{db: db, pool: db, aggregates: newAggregateCache()}
}

// Both selections remain distinguishable in their native detail records.
const selectedArt = `SELECT ci.artwork_id FROM curated_collection_items ci JOIN curated_collections cc ON cc.id=ci.collection_id
 WHERE cc.status<>'archived'
 AND (cc.curator_kind='owner' OR (ci.source_url IS NOT NULL AND EXISTS(SELECT 1 FROM sources s WHERE s.id=ci.source_id AND s.is_active)))`
const acceptedArtHolding = `EXISTS(SELECT 1 FROM artwork_location_assertions h JOIN sources s ON s.id=h.source_id AND s.is_active JOIN institutions i ON i.id=h.institution_id AND i.status<>'archived'  WHERE h.artwork_id=a.id AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL)`
const artScope = ` FROM artworks a WHERE a.status<>'archived' AND a.work_type='painting'
 AND a.date_precision IN ('exact','circa','range','circa_range','decade','century')
 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
 AND coalesce(a.creation_year_start,a.creation_year_end)<>0 AND coalesce(a.creation_year_end,a.creation_year_start)<>0
 AND coalesce(a.creation_year_start,a.creation_year_end)<=$2 AND coalesce(a.creation_year_end,a.creation_year_start)>=$1
` + artDiscoveryScope
const artDiscoveryScope = ` AND (a.id IN (` + selectedArt + `) OR (NOT $4 AND ` + acceptedArtHolding + `))
 AND ` + artworkCreatorVisibility + artSharedSearchScope + `
 AND ($5='' OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id JOIN artist_countries ac ON ac.artist_id=ar.id JOIN countries c ON c.code=ac.country_code WHERE aa.artwork_id=a.id AND ar.status<>'archived'  AND c.region_code=$5)
 OR EXISTS(SELECT 1 FROM artwork_places ap JOIN places pl ON pl.id=ap.place_id JOIN countries c ON c.code=pl.country_code WHERE ap.artwork_id=a.id AND c.region_code=$5))`
const artSharedSearchScope = `
 AND ($3='' OR strpos(lower(a.title),lower($3))>0 OR strpos(lower(coalesce(a.unlinked_creator_label,'')),lower($3))>0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id AND ar.status<>'archived'  AND strpos(lower(ar.display_name),lower($3))>0))`
const bookScope = ` FROM book_records b LEFT JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum
 WHERE b.status<>'archived'  AND b.start_year<=$2 AND b.end_year>=$1 AND b.end_year<=2000
 AND ($3='' OR strpos(b.search_text,lower($3))>0) AND (NOT $4 OR d.top100) AND ($5='' OR $5=ANY(d.regions))`
const eventScope = ` FROM event_records e WHERE e.status<>'archived'  AND e.start_year<=$2 AND e.end_year>=$1
 AND ($3='' OR strpos(e.search_text,lower($3))>0) AND (NOT $4 OR e.top100)
 AND ($5='' OR EXISTS(SELECT 1 FROM unnest(e.regions) region WHERE replace(lower(region),' ','-')=$5))`

type provider struct{ keys, details string }

// Within the same creation year, retain the existing painted/other/graphic
// preference. Creation chronology always takes precedence over medium.
const artworkGalleryPriority = `CASE
 WHEN a.work_type IN ('painting','fresco','watercolor','manuscript_illumination') THEN 0
 WHEN a.work_type IN ('drawing','print','calligraphy') THEN 2
 ELSE 1 END`

const artworkKeys = `SELECT a.id::text AS id,coalesce(a.creation_year_start,a.creation_year_end) AS start_year,coalesce(a.creation_year_end,a.creation_year_start) AS end_year,` + artworkGalleryPriority + ` AS gallery_priority`

// Native predicates are applied before any creator, image or source enrichment.
// Only page keys reach the detail projection; aggregates use IDs/dates only.
var providers = map[string]provider{
	"artwork": {artworkKeys + artScope,
		`SELECT p.id,p.start_year,p.end_year,a.title,
 coalesce((SELECT string_agg(names.name,', ' ORDER BY names.name) FROM (SELECT DISTINCT ar.display_name AS name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id AND ar.status<>'archived' ) names),a.unlinked_creator_label,'Creator not recorded'),a.date_display,a.date_precision<>'exact',p.gallery_priority
 FROM page p JOIN artworks a ON a.id=p.id::uuid`},
	"book":  {`SELECT b.id,b.start_year,b.end_year,0 AS gallery_priority` + bookScope, `SELECT p.id,p.start_year,p.end_year,b.title,b.author_label,b.record->>'years',coalesce((b.record->>'approximate')::boolean,false),p.gallery_priority FROM page p JOIN book_records b ON b.id=p.id`},
	"event": {`SELECT e.id,e.start_year,e.end_year,0 AS gallery_priority` + eventScope, `SELECT p.id,p.start_year,p.end_year,e.title,e.kind,e.record->>'years',coalesce((e.record->>'approximate')::boolean,false),p.gallery_priority FROM page p JOIN event_records e ON e.id=p.id`},
}

func (r *Repository) List(ctx context.Context, f Filter) (Response, error) {
	if r.pool == nil || f.Validate() != nil || (f.Selection && len(f.Types) == 0 && len(f.Picks) == 0) {
		return r.list(ctx, f, "")
	}
	// Aggregates, dirty overlays and page details must describe one catalogue
	// snapshot, even if an import commits between the separate SQL statements.
	tx, err := r.pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		return Response{}, err
	}
	defer tx.Rollback(ctx)
	var revision string
	if err = tx.QueryRow(ctx, "SELECT sum(revision)::text FROM catalogue_cache_revisions HAVING count(*)=64").Scan(&revision); err != nil {
		return Response{}, err
	}
	reader := &Repository{db: tx, aggregates: r.aggregates}
	return reader.list(ctx, f, revision)
}

func (r *Repository) list(ctx context.Context, f Filter, revision string) (Response, error) {
	out := Response{Range: f.Range, Bounds: Bounds, Lanes: []Lane{}, Ticks: Ticks(f.Range)}
	if err := f.Validate(); err != nil {
		return out, err
	}
	if f.Selection && len(f.Types) == 0 && len(f.Picks) == 0 {
		return out, nil
	}
	if r.db == nil {
		return out, fmt.Errorf("atlas unavailable")
	}
	focus := presetFocus(f.PresetID)
	if focus != nil && len(focus.ArtworkIdentities) > 0 {
		var err error
		focus, err = r.resolveArtworkIdentities(ctx, focus)
		if err != nil {
			return out, err
		}
	}
	args := []any{pgx.QueryExecModeCacheDescribe, f.Start, f.End, strings.TrimSpace(f.Query), f.Highlights, f.Region}
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
			args[4] = false
		}
		clause := entityPredicate(definition.Key, entity, &args)
		highlight := "a.is_highlight"
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
		key := "b.id=ANY($6::text[])"
		if definition.Key == "event" {
			key = "e.id=ANY($6::text[])"
		}
		if definition.Key == "artwork" {
			key = "a.id=ANY($6::text[]::uuid[])"
		}
		if picked != nil {
			// An explicitly chosen ID is not subject to the layer's discovery filters.
			args[4] = false
			selection = key
		} else {
			if ids := f.Picks[definition.Key]; f.Selection && len(ids) > 0 {
				args[6] = ids
				if args[4] == true {
					clause = "(" + clause + ") AND (" + highlight + ")"
					args[4] = false
				}
				selection = "(" + clause + ") OR " + key
			} else {
				// Keep the creator predicate conjunctive so PostgreSQL can start
				// with the selected painter's indexed artwork links.
				selection = "$6::text[] IS NULL AND (" + clause + ")"
			}
		}
		creatorScope := creatorPredicate(definition.Key, f.Creators, &args)
		broadGeography := definition.Key == "artwork" && broadArtworkGeography(f)
		needsGeography := false
		pageGeography := []string{}
		matchGeography := func(condition string) string {
			if broadGeography {
				return artworkGeographyMatch(condition)
			}
			needsGeography = true
			scoped := scopedArtworkGeographyMatch(condition)
			pageGeography = append(pageGeography, scoped, pageArtworkGeographyMatch(condition))
			return scoped
		}
		geography := geographyPredicateWithArtwork(definition.Key, f, &args, matchGeography)
		focusScope := focusPredicateWithArtwork(definition.Key, focus, &args, matchGeography)
		prefix := ""
		if definition.Key == "artwork" {
			if strings.TrimSpace(f.Query) != "" {
				selection = "(" + selection + ") AND " + sharedArtworkSearchPredicate("$3")
			}
			prefix = browseArtworkScope(selection, creatorScope)
			if needsGeography {
				// Geography references these IDs several times. Resolve a selected
				// creator/filter scope once instead of repeating the browse view.
				prefix = strings.Replace(prefix, "AS NOT MATERIALIZED", "AS MATERIALIZED", 1)
				prefix += artworkGeographyScope
			}
			p.keys = `SELECT a.id::text AS id,a.start_year,a.end_year,a.gallery_priority
 FROM artwork_native_scope a WHERE (NOT $4 OR a.is_highlight) AND (` + geography + `) AND (` + focusScope + `)
 AND ($5='' OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id
 JOIN artist_countries ac ON ac.artist_id=ar.id JOIN countries c ON c.code=ac.country_code
 WHERE aa.artwork_id=a.id AND ar.status<>'archived' AND c.region_code=$5)
 OR EXISTS(SELECT 1 FROM artwork_places ap JOIN places pl ON pl.id=ap.place_id
 JOIN countries c ON c.code=pl.country_code WHERE ap.artwork_id=a.id AND c.region_code=$5))`
		} else {
			p.keys += " AND (" + selection + ") AND (" + creatorScope + ") AND (" + geography + ") AND (" + focusScope + ")"
		}
		next := len(args)
		starts, ends := []int{}, []int{}
		for _, period := range Periods(f.Range) {
			starts = append(starts, period.Start)
			ends = append(ends, period.End)
		}
		// Count distinct date groups once. This avoids materializing hundreds of
		// thousands of IDs just to count them and compute their density.
		groupPrefix := prefix
		groupQuery := "SELECT start_year,end_year,count(*) AS weight FROM (" + p.keys + ") scope GROUP BY start_year,end_year"
		// Text searches can be expensive even when they match no IDs (for
		// example literal punctuation). Resolve that search once per query.
		splitBrowse := definition.Key == "artwork" && strings.TrimSpace(f.Query) == "" && strings.TrimSpace(entity.Get("q")) == ""
		if splitBrowse {
			clean, pending := browseBranches(prefix)
			groupQuery = "SELECT start_year,end_year,sum(weight) AS weight FROM ((WITH " + clean + "grouped AS (" + groupQuery + ") SELECT * FROM grouped) UNION ALL (WITH " + pending + "grouped AS (" + groupQuery + ") SELECT * FROM grouped)) branches GROUP BY start_year,end_year"
			groupPrefix = ""
		}
		aggregateSQL := fmt.Sprintf(`WITH %sdate_groups AS MATERIALIZED (
 %s
), totals AS (SELECT coalesce(sum(weight),0)::bigint AS total,min(start_year) AS first_year,max(end_year) AS last_year FROM date_groups),
 periods AS (SELECT start_year,end_year,ordinality-1 AS bucket FROM unnest($%d::int[],$%d::int[]) WITH ORDINALITY p(start_year,end_year,ordinality)),
 density_changes AS (
 SELECT change.bucket,sum(change.amount) AS amount FROM date_groups m
 CROSS JOIN LATERAL (VALUES
  (width_bucket(m.start_year::bigint-1,$%d::bigint[]),m.weight),
  (width_bucket(m.end_year,$%d::int[]),-m.weight)
 ) change(bucket,amount) WHERE (SELECT total FROM totals)>%d GROUP BY change.bucket
 ) SELECT total,first_year,last_year,
 coalesce((SELECT jsonb_agg(bins ORDER BY start_year) FROM (
 SELECT * FROM (SELECT p.start_year,p.end_year,
 sum(coalesce(d.amount,0)) OVER(ORDER BY p.bucket)::bigint AS count
 FROM periods p LEFT JOIN density_changes d USING(bucket)) counts WHERE count>0
 ) bins),'[]'::jsonb) FROM totals`, groupPrefix, groupQuery, next, next+1, next+1, next, timeline.IndividualLimit)
		aggregateArgs := append(slices.Clone(args), starts, ends)
		aggregate, err := r.aggregates.load(ctx, revision, aggregateSQL, aggregateArgs[1:], func() (laneAggregate, error) {
			var v laneAggregate
			var raw []byte
			if err := r.db.QueryRow(ctx, aggregateSQL, aggregateArgs...).Scan(&v.Total, &v.FirstYear, &v.LastYear, &raw); err != nil {
				return v, err
			}
			return v, json.Unmarshal(raw, &v.Density)
		})
		if err != nil {
			return out, err
		}
		lane.Total, lane.Density = aggregate.Total, aggregate.Density
		if lane.Total == 0 {
			out.Lanes = append(out.Lanes, lane)
			continue
		}
		firstYear, lastYear := aggregate.FirstYear, aggregate.LastYear
		c, _ := decodeCursor(f.After[definition.Key], f, definition.Key)
		pageWhere := fmt.Sprintf("(start_year,gallery_priority,id)>($%d,$%d,$%d)", next, next+3, next+1)
		pageOrder := "start_year,gallery_priority,id"
		pageLimit := f.Limit + 1
		if f.NeighborOf != "" {
			op := ">"
			if f.Direction == "previous" {
				op = "<"
				pageOrder = "start_year DESC,gallery_priority DESC,id DESC"
			}
			pageWhere = fmt.Sprintf("$%d::int IS NOT NULL AND $%d::int IS NOT NULL AND (start_year,gallery_priority,id) %s (SELECT start_year,gallery_priority,id FROM matching WHERE id=$%d)", next, next+3, op, next+1)
			c.ID = f.NeighborOf
			pageLimit = 1
			lane.Density = []Period{}
		}
		// NOT MATERIALIZED lets the cursor/order/limit reach the browse index.
		// Only the bounded page reaches titles, creator labels and image details.
		pageSQL := fmt.Sprintf(`WITH %smatching AS NOT MATERIALIZED (%s),
 page AS MATERIALIZED(SELECT * FROM matching WHERE %s ORDER BY %s LIMIT $%d)
 SELECT coalesce(jsonb_agg(details ORDER BY "startYear",gallery_priority,id),'[]'::jsonb)
 FROM (%s) details(id,"startYear","endYear",title,context,years,approximate,gallery_priority)`, prefix, p.keys, pageWhere, pageOrder, next+2, p.details)
		if splitBrowse && f.NeighborOf == "" {
			pagePrefix, pageKeys := prefix, p.keys
			if needsGeography && f.End-f.Start <= 600 && lane.Total > timeline.IndividualLimit {
				// Counts retain the set-based geographic plan. Bounded period pages
				// seek the same memberships per candidate and stop at their LIMIT.
				// Keep wide windows and sparse selections on their measured paths.
				pagePrefix = browseArtworkScope(selection, creatorScope)
				pageKeys = strings.NewReplacer(pageGeography...).Replace(p.keys)
			}
			clean, pending := browseBranches(pagePrefix)
			branch := func(scope string) string {
				return fmt.Sprintf("(WITH %smatching AS NOT MATERIALIZED (%s) SELECT * FROM matching WHERE %s ORDER BY %s LIMIT $%d)", scope, pageKeys, pageWhere, pageOrder, next+2)
			}
			pageSQL = fmt.Sprintf(`WITH page AS MATERIALIZED (
 SELECT * FROM (%s UNION ALL %s) candidates ORDER BY %s LIMIT $%d)
 SELECT coalesce(jsonb_agg(details ORDER BY "startYear",gallery_priority,id),'[]'::jsonb)
 FROM (%s) details(id,"startYear","endYear",title,context,years,approximate,gallery_priority)`, branch(clean), branch(pending), pageOrder, next+2, p.details)
		}
		var items []byte
		if err = r.db.QueryRow(ctx, pageSQL, append(slices.Clone(args), c.Year, c.ID, pageLimit, c.Priority)...).Scan(&items); err != nil {
			return out, err
		}
		// The rank travels with each page key/cursor but is not public metadata.
		var rankedItems []struct {
			Item
			Priority int `json:"gallery_priority"`
		}
		if err := json.Unmarshal(items, &rankedItems); err != nil {
			return out, err
		}
		for _, ranked := range rankedItems {
			ranked.Item.galleryPriority = ranked.Priority
			lane.Items = append(lane.Items, ranked.Item)
		}
		for i := range lane.Items {
			lane.Items[i].Type = definition.Key
			if focus != nil && slices.Contains(focus.Context[definition.Key], lane.Items[i].ID) {
				lane.Items[i].Relation = "context"
			}
		}
		out.MatchedRange = timeline.MergeExtents(out.MatchedRange, timeline.FitExtent(firstYear, lastYear, f.Start, f.End))
		out.Total += lane.Total
		if lane.Total > timeline.IndividualLimit {
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
		if definition.Key == "book" && lane.Mode == "density" {
			if err := r.attachBookCovers(ctx, lane.Items); err != nil {
				return out, err
			}
		}
		out.Lanes = append(out.Lanes, lane)
	}
	return out, nil
}
func (r *Repository) ArtworkVisible(ctx context.Context, id string) (bool, error) {
	var exists bool
	// Direct inspection also serves exhibition links with uncertain dates or
	// explicitly approved dates outside the timeline. Keep discovery bounds on
	// lists, while retaining source-backed selection and archive checks here.
	err := r.db.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artworks a
 WHERE a.id=$1::uuid AND a.status<>'archived'
 AND (EXISTS(`+selectedArt+` AND ci.artwork_id=a.id) OR `+acceptedArtHolding+`)
 AND `+artworkCreatorVisibility+`)`, pgx.QueryExecModeCacheDescribe, id).Scan(&exists)
	return exists, err
}
