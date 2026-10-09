package books

import (
	"context"
	"encoding/json"
	"errors"
	"github.com/vadimdulub/artline/apps/server/internal/timeline"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type Repository struct{ db *pgxpool.Pool }

func NewRepository(db *pgxpool.Pool) *Repository { return &Repository{db: db} }

const discoveryJoin = ` LEFT JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum `

// Preserve records outside the display cutoff; visibility uses recorded publication bounds.
const publicationScope = `(b.end_year <= 2000 OR b.start_year IS NULL)`

const scopePredicate = ` FROM book_records b ` + discoveryJoin + ` WHERE b.status <> 'archived'  AND ` + publicationScope + `
 AND ($3='' OR strpos(b.search_text,lower($3))>0)
 AND (coalesce(cardinality($4::text[]),0)=0 OR b.author_label=ANY($4) OR EXISTS (
 SELECT 1 FROM book_creator_links l JOIN book_creators c ON c.id=l.creator_id WHERE l.book_id=b.id AND c.name=ANY($4)))
 AND (NOT $5 OR cardinality(d.woman_author_ids)>0)
 AND (NOT $6 OR d.top100)
 AND (coalesce(cardinality($7::text[]),0)=0 OR d.languages && $7)
 AND (coalesce(cardinality($8::text[]),0)=0 OR d.countries && $8)
 AND (coalesce(cardinality($9::text[]),0)=0 OR d.regions && $9)`

const predicate = scopePredicate + ` AND ((b.start_year <= $2 AND b.end_year >= $1) OR (b.start_year IS NULL AND $1=-5000 AND $2=2000))`

func (r *Repository) List(ctx context.Context, f Filter) (Response, error) {
	result := metadata(f.Range)
	if err := f.Validate(); err != nil {
		return result, err
	}
	if r.db == nil {
		return result, ErrUnavailable
	}
	if f.View == "authors" {
		return r.authorTimeline(ctx, f)
	}
	args := []any{f.Start, f.End, strings.TrimSpace(f.Query), f.Authors, f.Women, f.Top100, f.Languages, f.Countries, f.Regions}
	var firstYear, lastYear *int
	if err := r.db.QueryRow(ctx, `SELECT count(*),count(*) FILTER (WHERE b.start_year IS NULL),min(b.start_year),max(b.end_year)`+predicate, args...).Scan(&result.Total, &result.UndatedTotal, &firstYear, &lastYear); err != nil {
		return result, err
	}
	result.MatchedRange = timeline.FitExtent(firstYear, lastYear, f.Start, f.End)
	individualLimit := timeline.IndividualLimit
	if f.Top100 {
		individualLimit = HighlightsLimit
	}
	if result.Total > individualLimit || (result.Total > 0 && result.UndatedTotal == result.Total) {
		result.Mode = "density"
	}
	if err := r.db.QueryRow(ctx, `SELECT count(*) FROM book_records b WHERE status <> 'archived'  AND `+publicationScope+``).Scan(&result.SelectionTotal); err != nil {
		return result, err
	}
	c, _ := decodeCursor(f.After)
	record := "b.record"
	if f.Summary {
		record = `jsonb_build_object('id',b.record->'id','sourceId',b.record->'sourceId',
 'title',b.record->'title','author',b.record->'author','years',b.record->'years',
 'startYear',b.record->'startYear','endYear',b.record->'endYear','approximate',b.record->'approximate')`
	}
	rows, err := r.db.Query(ctx, `SELECT `+record+`,b.status`+predicate+` AND (coalesce(b.start_year,2147483647),b.id)>($10,$11) ORDER BY coalesce(b.start_year,2147483647),b.id LIMIT $12`, append(args, c.Year, c.ID, f.Limit+1)...)
	if err != nil {
		return result, err
	}
	for rows.Next() {
		var raw []byte
		var status string
		var book Book
		if err := rows.Scan(&raw, &status); err != nil {
			rows.Close()
			return result, err
		}
		if err := json.Unmarshal(raw, &book); err != nil {
			rows.Close()
			return result, err
		}
		book.Status = status
		book.Summary = f.Summary
		book.Creators = []Creator{}
		result.Items = append(result.Items, book)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return result, err
	}
	if len(result.Items) > f.Limit {
		result.HasMore = true
		result.Items = result.Items[:f.Limit]
		result.NextCursor = encodeCursor(result.Items[len(result.Items)-1])
	}
	if !f.Summary {
		if err := r.attachCreators(ctx, result.Items); err != nil {
			return result, err
		}
	}
	attachCovers(result.Items)
	// Dense selections retain bounded keyset pages for the cover gallery.
	return result, nil
}

func (r *Repository) ByID(ctx context.Context, id string) (Book, error) {
	var book Book
	var raw []byte
	var status string
	if r.db == nil {
		return book, ErrUnavailable
	}
	err := r.db.QueryRow(ctx, `SELECT record,status FROM book_records b WHERE id=$1 AND status<>'archived'  AND `+publicationScope+``, id).Scan(&raw, &status)
	if errors.Is(err, pgx.ErrNoRows) {
		return book, ErrNotFound
	}
	if err != nil {
		return book, err
	}
	if err = json.Unmarshal(raw, &book); err != nil {
		return book, err
	}
	book.Status = status
	book.Creators = []Creator{}
	items := []Book{book}
	err = r.attachCreators(ctx, items)
	attachCovers(items)
	return items[0], err
}

// Enrich only the bounded IDs already returned, in one indexed batch.
func (r *Repository) attachCreators(ctx context.Context, items []Book) error {
	if len(items) == 0 {
		return nil
	}
	ids := make([]string, 0, len(items))
	positions := map[string]int{}
	for i, b := range items {
		ids = append(ids, b.ID)
		positions[b.ID] = i
	}
	rows, err := r.db.Query(ctx, `SELECT l.book_id,c.record,l.credit FROM book_creator_links l JOIN book_creators c ON c.id=l.creator_id WHERE l.book_id=ANY($1::text[]) ORDER BY l.book_id,l.position,c.id`, ids)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var id string
		var raw []byte
		var creator Creator
		var credit string
		if err := rows.Scan(&id, &raw, &credit); err != nil {
			return err
		}
		if err := json.Unmarshal(raw, &creator); err != nil {
			return err
		}
		attachPortrait(&creator)
		creator.Credit = credit
		items[positions[id]].Creators = append(items[positions[id]].Creators, creator)
	}
	return rows.Err()
}

func (r *Repository) Authors(ctx context.Context, query string, women, top100 bool) (AuthorOptions, error) {
	result := AuthorOptions{Items: []string{}}
	if r.db == nil {
		return result, ErrUnavailable
	}
	rows, err := r.db.Query(ctx, `SELECT DISTINCT c.name FROM book_creators c WHERE strpos(lower(c.name),lower($1))>0
 AND EXISTS(SELECT 1 FROM book_creator_links l JOIN book_records b ON b.id=l.book_id `+discoveryJoin+` WHERE l.creator_id=c.id AND b.status<>'archived'  AND `+publicationScope+` AND (NOT $2 OR cardinality(d.woman_author_ids)>0) AND (NOT $3 OR d.top100)) ORDER BY c.name LIMIT 31`, strings.TrimSpace(query), women, top100)
	if err != nil {
		return result, err
	}
	defer rows.Close()
	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			return result, err
		}
		result.Items = append(result.Items, name)
	}
	if len(result.Items) > 30 {
		result.HasMore = true
		result.Items = result.Items[:30]
	}
	return result, rows.Err()
}

// Small controlled vocabularies, scoped by visibility and the two discovery
// selections, just like ArtWorks facets. No collection records are sent here.
func (r *Repository) Facets(ctx context.Context, women, top100 bool) (Facets, error) {
	result := Facets{Languages: []FilterOption{}, Countries: []FilterOption{}, Regions: []FilterOption{}}
	if r.db == nil {
		return result, ErrUnavailable
	}
	rows, err := r.db.Query(ctx, `WITH matching AS MATERIALIZED (
 SELECT d.languages,d.countries,d.regions FROM book_records b `+discoveryJoin+`
 WHERE b.status<>'archived'  AND `+publicationScope+`
 AND (NOT $1 OR cardinality(d.woman_author_ids)>0) AND (NOT $2 OR d.top100)
 ), keys AS (
 SELECT 'language' AS kind,unnest(languages) AS key FROM matching
 UNION SELECT 'country',unnest(countries) FROM matching
 UNION SELECT 'region',unnest(regions) FROM matching)
 SELECT t.kind,t.key,t.name FROM keys k JOIN book_discovery_terms t USING(kind,key) ORDER BY t.kind,t.name,t.key LIMIT 1000`, women, top100)
	if err != nil {
		return result, err
	}
	defer rows.Close()
	for rows.Next() {
		var kind string
		var option FilterOption
		if err := rows.Scan(&kind, &option.Slug, &option.Name); err != nil {
			return result, err
		}
		switch kind {
		case "language":
			result.Languages = append(result.Languages, option)
		case "country":
			result.Countries = append(result.Countries, option)
		case "region":
			result.Regions = append(result.Regions, option)
		}
	}
	return result, rows.Err()
}
