package exhibitions

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

type Repository struct{ db *pgxpool.Pool }

func NewRepository(db *pgxpool.Pool) *Repository { return &Repository{db} }

func venueConditions(f Filter, offset int) (string, []any) {
	conditions, args := []string{}, []any{}
	add := func(clause string, value any) {
		args = append(args, value)
		conditions = append(conditions, fmt.Sprintf(clause, offset+len(args)))
	}
	if f.Institution != "" {
		add(`v.institution_id=$%d::uuid`, f.Institution)
	}
	if country := strings.TrimSpace(f.Country); country != "" {
		add(`(strpos(lower(coalesce(v.country_label,'')),lower($%[1]d))>0 OR lower(coalesce(v.country_code,''))=lower($%[1]d))`, country)
	}
	if city := strings.TrimSpace(f.City); city != "" {
		add(`strpos(lower(coalesce(v.city_label,'')),lower($%d))>0`, city)
	}
	return strings.Join(conditions, " AND "), args
}

func scope(f Filter) (string, []any) {
	where := ` FROM exhibitions e WHERE e.status<>'archived'`
	args := []any{}
	add := func(clause string, value any) { args = append(args, value); where += fmt.Sprintf(clause, len(args)) }
	if f.Theme != "" {
		add(` AND EXISTS(SELECT 1 FROM exhibition_research er WHERE er.exhibition_id=e.id AND er.concepts @> ARRAY[$%d]::text[])`, f.Theme)
	}
	if f.Person != "" {
		add(` AND EXISTS(SELECT 1 FROM exhibition_research_people p WHERE p.exhibition_id=e.id AND p.person_id=$%d::uuid)`, f.Person)
	}
	if f.Query != "" {
		add(` AND strpos(lower(e.title),lower($%d))>0`, strings.TrimSpace(f.Query))
	}
	if venueWhere, venueArgs := venueConditions(f, len(args)); len(venueArgs) > 0 {
		// All venue conditions must match the same stop of a touring exhibition.
		where += ` AND e.id IN(SELECT v.exhibition_id FROM exhibition_occurrences v WHERE ` + venueWhere + `)`
		args = append(args, venueArgs...)
	}
	if f.Artist != "" {
		add(` AND e.id IN(SELECT p.exhibition_id FROM exhibition_participants p WHERE p.artist_id=$%[1]d::uuid UNION SELECT p.exhibition_id FROM exhibition_research_people p WHERE p.artist_id=$%[1]d::uuid)`, f.Artist)
	}
	if f.Artwork != "" {
		add(` AND e.id IN(SELECT x.exhibition_id FROM exhibition_entries x WHERE x.artwork_id=$%[1]d::uuid UNION SELECT x.exhibition_id FROM exhibition_objects o JOIN exhibition_object_entries x ON x.object_id=o.id WHERE o.artwork_id=$%[1]d::uuid)`, f.Artwork)
	}
	if f.Source != "" {
		add(` AND EXISTS(SELECT 1 FROM exhibition_source_records s WHERE s.exhibition_id=e.id AND s.source_key=$%d)`, f.Source)
	}
	if f.Format != "" {
		add(` AND e.format=$%d`, f.Format)
	}
	if f.State != "" {
		add(` AND e.event_state=$%d`, f.State)
	}
	if f.Start != nil {
		add(` AND coalesce(e.end_year,e.start_year)>=$%d`, *f.Start)
	}
	if f.End != nil {
		add(` AND e.start_year<=$%d`, *f.End)
	}
	return where, args
}

const recordJSON = `jsonb_build_object('id',e.id,'title',e.title,'alternateTitles',e.alternate_titles,
 'startDate',e.start_date,'endDate',e.end_date,'startYear',e.start_year,'endYear',e.end_year,
 'dates',e.date_display,'datePrecision',e.date_precision,'state',e.event_state,'stateBasis',e.state_basis,
 'format',e.format,'checklistState',e.checklist_state)`

func (r *Repository) List(ctx context.Context, f Filter) (Response, error) {
	out := Response{Items: []json.RawMessage{}}
	if err := f.Validate(); err != nil {
		return out, err
	}
	if r.db == nil {
		return out, ErrUnavailable
	}
	where, args := scope(f)
	if err := r.db.QueryRow(ctx, `SELECT count(*),count(*) FILTER(WHERE e.event_state='held')`+where, args...).Scan(&out.Total, &out.HeldTotal); err != nil {
		return out, err
	}
	if f.After != "" {
		cursor, _ := DecodeCursor(f.After)
		args = append(args, cursor.Year, cursor.ID)
		where += fmt.Sprintf(` AND (coalesce(e.start_year,-2147483648),e.id)<($%d,$%d::uuid)`, len(args)-1, len(args))
	}
	args = append(args, f.Limit+1)
	limitArg := len(args)
	venueOrder, summary := `v.id`, `coalesce(er.summary,'{}'::jsonb)`
	if venueWhere, venueArgs := venueConditions(f, len(args)); len(venueArgs) > 0 {
		args = append(args, venueArgs...)
		venueOrder = `(` + venueWhere + `) DESC NULLS LAST,v.id`
		// Prefer live matching venues to a study's older stored venue summary.
		summary = `coalesce(er.summary-'venues','{}'::jsonb)`
	}
	// Scope to the bounded page before any child counts or venue enrichment.
	prefix := `WITH `
	page := `SELECT e.*` + where + fmt.Sprintf(` ORDER BY coalesce(e.start_year,-2147483648) DESC,e.id DESC LIMIT $%d`, limitArg)
	if f.Source != "" || f.Institution != "" || f.Country != "" || f.City != "" || f.Artist != "" || f.Artwork != "" || f.Theme != "" || f.Person != "" {
		// A selective historical source must not walk the global chronology and
		// probe a relationship index for every newer exhibition. Materialize only
		// matching IDs/years, sort those, then fetch the bounded full records.
		prefix += `candidates AS MATERIALIZED(SELECT e.id,e.start_year` + where + `), selected AS MATERIALIZED(SELECT id FROM candidates ORDER BY coalesce(start_year,-2147483648) DESC,id DESC ` + fmt.Sprintf(`LIMIT $%d), `, limitArg)
		page = `SELECT e.* FROM exhibitions e JOIN selected chosen ON chosen.id=e.id`
	}
	query := prefix + `page AS MATERIALIZED(` + page + `),
 entry_counts AS(SELECT x.exhibition_id,count(*) n,count(x.artwork_id) linked FROM exhibition_entries x JOIN page p ON p.id=x.exhibition_id GROUP BY x.exhibition_id)
 SELECT ` + recordJSON + ` || jsonb_build_object('entryCount',coalesce(c.n,0),'linkedArtworkCount',coalesce(c.linked,0),
 'venues',coalesce((SELECT jsonb_agg(v) FROM(SELECT v.venue_label name,v.city_label city,v.country_label country,` + catalog.MuseumLinkSlugSQL + ` museum_slug FROM exhibition_occurrences v LEFT JOIN institutions i ON i.id=v.institution_id WHERE v.exhibition_id=e.id ORDER BY ` + venueOrder + ` LIMIT 3)v),'[]'::jsonb)) || ` + summary + `
 FROM page e LEFT JOIN entry_counts c ON c.exhibition_id=e.id LEFT JOIN exhibition_research er ON er.exhibition_id=e.id ORDER BY coalesce(e.start_year,-2147483648) DESC,e.id DESC`
	rows, err := r.db.Query(ctx, query, args...)
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
	if len(out.Items) > f.Limit {
		out.HasMore = true
		out.Items = out.Items[:f.Limit]
		var last struct {
			ID   string `json:"id"`
			Year *int   `json:"startYear"`
		}
		if err = json.Unmarshal(out.Items[len(out.Items)-1], &last); err != nil {
			return out, err
		}
		year := -2147483648
		if last.Year != nil {
			year = *last.Year
		}
		b, _ := json.Marshal(Cursor{year, last.ID})
		out.NextCursor = base64.RawURLEncoding.EncodeToString(b)
	}
	return out, nil
}

func (r *Repository) ByID(ctx context.Context, id string) (json.RawMessage, error) {
	if !ValidID(id) {
		return nil, ErrNotFound
	}
	if r.db == nil {
		return nil, ErrUnavailable
	}
	resolved, err := r.CanonicalID(ctx, id)
	if err != nil {
		return nil, err
	}
	id = resolved
	var raw []byte
	err = r.db.QueryRow(ctx, `SELECT `+recordJSON+` || jsonb_build_object(
 'entryCount',(SELECT count(*) FROM exhibition_entries x WHERE x.exhibition_id=e.id),
 'participationCounts',coalesce((SELECT jsonb_object_agg(p.participation,p.n) FROM (SELECT participation,count(*) n FROM exhibition_entries WHERE exhibition_id=e.id GROUP BY participation)p),'{}'::jsonb),
 'participantCount',(SELECT count(*) FROM exhibition_participants p WHERE p.exhibition_id=e.id),
 'venueCount',(SELECT count(*) FROM exhibition_occurrences v WHERE v.exhibition_id=e.id),
 'venues',coalesce((SELECT jsonb_agg(v) FROM(SELECT v.id,v.venue_label name,v.city_label city,v.country_label country,v.start_date,v.end_date,v.institution_id,`+catalog.MuseumLinkSlugSQL+` museum_slug FROM exhibition_occurrences v LEFT JOIN institutions i ON i.id=v.institution_id WHERE v.exhibition_id=e.id ORDER BY v.start_date NULLS LAST,v.id LIMIT 50)v),'[]'::jsonb),
 'participants',coalesce((SELECT jsonb_agg(p) FROM(SELECT p.id,p.name_label name,p.role,p.artist_id,a.slug artist_slug FROM exhibition_participants p LEFT JOIN artists a ON a.id=p.artist_id AND a.status<>'archived' WHERE p.exhibition_id=e.id ORDER BY p.name_label,p.id LIMIT 100)p),'[]'::jsonb),
 'sources',coalesce((SELECT jsonb_agg(s) FROM(SELECT s.source_key provider,s.source_record_id,s.source_url url,s.retrieved_at,s.interpretation FROM exhibition_source_records s WHERE s.exhibition_id=e.id ORDER BY s.source_key,s.source_record_id LIMIT 50)s),'[]'::jsonb),
 'publications',coalesce((SELECT jsonb_agg(p) FROM(SELECT p.publication_type kind,p.title_label title,p.author_label author,p.url,p.source_identifier FROM exhibition_publications p WHERE p.exhibition_id=e.id ORDER BY p.id LIMIT 50)p),'[]'::jsonb))
 FROM exhibitions e WHERE e.id=$1::uuid AND e.status<>'archived'`, id).Scan(&raw)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	detail, err := r.enrichDetail(ctx, id, raw)
	if err != nil {
		return nil, err
	}
	return r.enrichParticipantImages(ctx, detail)
}

func (r *Repository) Entries(ctx context.Context, id, after string, limit int, participation ...string) (EntriesResponse, error) {
	out := EntriesResponse{Items: []json.RawMessage{}}
	if !ValidID(id) {
		return out, ErrNotFound
	}
	if limit < 1 || limit > 100 || (after != "" && !ValidID(after)) {
		return out, fmt.Errorf("invalid artwork-entry page")
	}
	if r.db == nil {
		return out, ErrUnavailable
	}
	resolved, err := r.CanonicalID(ctx, id)
	if err != nil {
		return out, err
	}
	id = resolved
	filter := ""
	if len(participation) > 0 {
		filter = participation[0]
	}
	if filter != "" && filter != "exhibited" {
		return out, fmt.Errorf("invalid participation")
	}
	var expanded bool
	if err := r.db.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM exhibition_research er JOIN exhibitions e ON e.id=er.exhibition_id WHERE e.id=$1::uuid AND e.status<>'archived')`, id).Scan(&expanded); err != nil {
		return out, err
	}
	if expanded {
		return r.objectEntries(ctx, id, after, limit, filter, false)
	}
	var exists bool
	if err := r.db.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM exhibitions WHERE id=$1::uuid AND status<>'archived')`, id).Scan(&exists); err != nil {
		return out, err
	}
	if !exists {
		return out, ErrNotFound
	}
	if err := r.db.QueryRow(ctx, `SELECT count(*) FROM exhibition_entries WHERE exhibition_id=$1::uuid AND ($2='' OR participation=$2)`, id, filter).Scan(&out.Total); err != nil {
		return out, err
	}
	if after == "" {
		after = "00000000-0000-0000-0000-000000000000"
	}
	// Rank only this exhibition's indexed entries, then enrich the bounded page.
	// Illustrated exhibited works lead, followed by other illustrated entries.
	// Resolve the UUID cursor's rank in the same exhibition to preserve keyset
	// paging across the illustrated/unillustrated boundary.
	rows, err := r.db.Query(ctx, `WITH ranked AS MATERIALIZED(
 SELECT x.id,(CASE WHEN m.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$' THEN 0 ELSE 2 END + CASE WHEN x.participation='exhibited' THEN 0 ELSE 1 END) position
 FROM exhibition_entries x LEFT JOIN artworks a ON a.id=x.artwork_id AND a.status<>'archived' LEFT JOIN media_assets m ON m.id=a.primary_media_id
 WHERE x.exhibition_id=$1::uuid AND ($4='' OR x.participation=$4)),
 page AS MATERIALIZED(SELECT * FROM ranked WHERE $2::uuid='00000000-0000-0000-0000-000000000000'::uuid OR (position,id)>(SELECT position,id FROM ranked WHERE id=$2::uuid) ORDER BY position,id LIMIT $3)
 SELECT jsonb_build_object('id',x.id,'artworkId',a.id,'title',coalesce(x.title_label,a.title),'creator',x.creator_label,'date',x.date_label,'catalogueNumber',x.catalogue_number,
 'medium',coalesce(x.medium_label,a.medium_text),'imageWidth',m.width,'imageHeight',m.height,
 'participation',x.participation,'sourcePage',x.source_page,'evidence',x.evidence,'sourceCaption',x.evidence->>'tombstone','sourceURL',s.source_url,'provider',s.source_key,
 'imageCredit',coalesce(m.attribution_text,m.creator_credit,m.provider_name),'imageLicense',m.license_label,'imageSource',m.source_page_url,
 'image',CASE WHEN m.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$' THEN m.storage_path ELSE NULL END)
 FROM page p JOIN exhibition_entries x ON x.id=p.id JOIN exhibition_source_records s ON s.id=x.source_record_id
 LEFT JOIN artworks a ON a.id=x.artwork_id AND a.status<>'archived' LEFT JOIN media_assets m ON m.id=a.primary_media_id ORDER BY p.position,x.id`, id, after, limit+1, filter)
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
		if err = json.Unmarshal(out.Items[len(out.Items)-1], &last); err != nil {
			return out, err
		}
		out.NextCursor = last.ID
	}
	return out, nil
}
