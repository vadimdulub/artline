package books

import (
	"context"
	"encoding/json"
	"errors"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type Repository struct{ db *pgxpool.Pool }

func NewRepository(db *pgxpool.Pool) *Repository { return &Repository{db: db} }

const discoveryJoin = ` LEFT JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum `

// Preserve records outside the display cutoff; visibility uses recorded publication bounds.
const publicationScope = `(b.end_year <= 2000 OR b.start_year IS NULL)`

const scopePredicate = ` FROM book_records b ` + discoveryJoin + ` WHERE b.status <> 'archived' AND ($3 OR b.status='published') AND ` + publicationScope + `
 AND ($4='' OR strpos(b.search_text,lower($4))>0)
 AND (coalesce(cardinality($5::text[]),0)=0 OR b.author_label=ANY($5) OR EXISTS (
 SELECT 1 FROM book_creator_links l JOIN book_creators c ON c.id=l.creator_id WHERE l.book_id=b.id AND c.name=ANY($5)))
 AND (NOT $6 OR cardinality(d.woman_author_ids)>0)
 AND (NOT $7 OR d.top100)
 AND (coalesce(cardinality($8::text[]),0)=0 OR d.languages && $8)
 AND (coalesce(cardinality($9::text[]),0)=0 OR d.countries && $9)
 AND (coalesce(cardinality($10::text[]),0)=0 OR d.regions && $10)`

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
	args := []any{f.Start, f.End, f.Preview, strings.TrimSpace(f.Query), f.Authors, f.Women, f.Top100, f.Languages, f.Countries, f.Regions}
	if err := r.db.QueryRow(ctx, `SELECT count(*),count(*) FILTER (WHERE b.start_year IS NULL)`+predicate, args...).Scan(&result.Total, &result.UndatedTotal); err != nil {
		return result, err
	}
	if err := r.db.QueryRow(ctx, `SELECT count(*) FROM book_records b WHERE status <> 'archived' AND ($1 OR status='published') AND `+publicationScope+``, f.Preview).Scan(&result.SelectionTotal); err != nil {
		return result, err
	}
	c, _ := decodeCursor(f.After)
	rows, err := r.db.Query(ctx, `SELECT b.record,b.status`+predicate+` AND (coalesce(b.start_year,2147483647),b.id)>($11,$12) ORDER BY coalesce(b.start_year,2147483647),b.id LIMIT $13`, append(args, c.Year, c.ID, f.Limit+1)...)
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
	if err := r.attachCreators(ctx, result.Items); err != nil {
		return result, err
	}
	attachCovers(result.Items)
	if result.Total-result.UndatedTotal > 100 {
		result.Mode = "density"
		result.SuggestedFilters, err = r.suggestions(ctx, args, result.Total)
		if err != nil {
			return result, err
		}
		periods := densityPeriods(f.Range)
		starts, ends := []int{}, []int{}
		for _, period := range periods {
			starts = append(starts, period.Start)
			ends = append(ends, period.End)
		}
		rows, err := r.db.Query(ctx, `WITH matching AS MATERIALIZED (SELECT b.start_year,b.end_year`+predicate+`), periods AS (SELECT * FROM unnest($11::int[],$12::int[]) AS p(start_year,end_year))
			SELECT p.start_year,p.end_year,count(m.start_year) FROM periods p JOIN matching m ON m.start_year<=p.end_year AND m.end_year>=p.start_year GROUP BY p.start_year,p.end_year ORDER BY p.start_year`, append(args, starts, ends)...)
		if err != nil {
			return result, err
		}
		for rows.Next() {
			var period DensityPeriod
			if err := rows.Scan(&period.Start, &period.End, &period.Count); err != nil {
				rows.Close()
				return result, err
			}
			result.Density = append(result.Density, period)
		}
		err = rows.Err()
		rows.Close()
		if err != nil {
			return result, err
		}
	}
	return result, nil
}

func (r *Repository) ByID(ctx context.Context, id string, preview bool) (Book, error) {
	var book Book
	var raw []byte
	var status string
	if r.db == nil {
		return book, ErrUnavailable
	}
	err := r.db.QueryRow(ctx, `SELECT record,status FROM book_records b WHERE id=$1 AND status<>'archived' AND ($2 OR status='published') AND `+publicationScope+``, id, preview).Scan(&raw, &status)
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
		creator.Credit = credit
		items[positions[id]].Creators = append(items[positions[id]].Creators, creator)
	}
	return rows.Err()
}

func (r *Repository) Authors(ctx context.Context, query string, preview, women, top100 bool) (AuthorOptions, error) {
	result := AuthorOptions{Items: []string{}}
	if r.db == nil {
		return result, ErrUnavailable
	}
	rows, err := r.db.Query(ctx, `SELECT DISTINCT c.name FROM book_creators c WHERE strpos(lower(c.name),lower($1))>0
 AND EXISTS(SELECT 1 FROM book_creator_links l JOIN book_records b ON b.id=l.book_id `+discoveryJoin+` WHERE l.creator_id=c.id AND b.status<>'archived' AND ($2 OR b.status='published') AND `+publicationScope+` AND (NOT $3 OR cardinality(d.woman_author_ids)>0) AND (NOT $4 OR d.top100)) ORDER BY c.name LIMIT 31`, strings.TrimSpace(query), preview, women, top100)
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
func (r *Repository) Facets(ctx context.Context, preview, women, top100 bool) (Facets, error) {
	result := Facets{Languages: []FilterOption{}, Countries: []FilterOption{}, Regions: []FilterOption{}}
	if r.db == nil {
		return result, ErrUnavailable
	}
	rows, err := r.db.Query(ctx, `WITH matching AS MATERIALIZED (
 SELECT d.languages,d.countries,d.regions FROM book_records b `+discoveryJoin+`
 WHERE b.status<>'archived' AND ($1 OR b.status='published') AND `+publicationScope+`
 AND (NOT $2 OR cardinality(d.woman_author_ids)>0) AND (NOT $3 OR d.top100)
 ), keys AS (
 SELECT 'language' AS kind,unnest(languages) AS key FROM matching
 UNION SELECT 'country',unnest(countries) FROM matching
 UNION SELECT 'region',unnest(regions) FROM matching)
 SELECT t.kind,t.key,t.name FROM keys k JOIN book_discovery_terms t USING(kind,key) ORDER BY t.kind,t.name,t.key LIMIT 1000`, preview, women, top100)
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
