package events

import (
	"context"
	"encoding/json"
	"errors"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"strings"
)

type Repository struct{ db *pgxpool.Pool }

func NewRepository(db *pgxpool.Pool) *Repository { return &Repository{db} }

const predicate = ` FROM event_records e WHERE e.status<>'archived' AND ($3 OR e.status='published')
 AND ($4='' OR strpos(e.search_text,lower($4))>0)
 AND (NOT $5 OR e.top100)
 AND (coalesce(cardinality($6::text[]),0)=0 OR e.topics && $6)
 AND (coalesce(cardinality($7::text[]),0)=0 OR e.countries && $7)
 AND (coalesce(cardinality($8::text[]),0)=0 OR e.regions && $8)
 AND (coalesce(cardinality($9::text[]),0)=0 OR e.kind=ANY($9))
 AND ((e.start_year<=$2 AND e.end_year>=$1) OR (e.start_year IS NULL AND $1=-12000 AND $2=2000))`

func (r *Repository) List(ctx context.Context, f Filter) (Response, error) {
	out := metadata(f.Range)
	if err := f.Validate(); err != nil {
		return out, err
	}
	if r.db == nil {
		return out, ErrUnavailable
	}
	args := []any{f.Start, f.End, f.Preview, strings.TrimSpace(f.Query), f.Top100, f.Topics, f.Countries, f.Regions, f.Kinds}
	if err := r.db.QueryRow(ctx, `SELECT count(*),count(*) FILTER(WHERE e.start_year IS NULL)`+predicate, args...).Scan(&out.Total, &out.UndatedTotal); err != nil {
		return out, err
	}
	if err := r.db.QueryRow(ctx, `SELECT count(*) FROM event_records WHERE status<>'archived' AND ($1 OR status='published')`, f.Preview).Scan(&out.SelectionTotal); err != nil {
		return out, err
	}
	c, _ := decodeCursor(f.After)
	rows, err := r.db.Query(ctx, `SELECT e.record,e.status`+predicate+` AND (coalesce(e.start_year,2147483647),e.id)>($10,$11) ORDER BY coalesce(e.start_year,2147483647),e.id LIMIT $12`, append(args, c.Year, c.ID, f.Limit+1)...)
	if err != nil {
		return out, err
	}
	for rows.Next() {
		var raw []byte
		var status string
		var e Event
		if err = rows.Scan(&raw, &status); err != nil {
			rows.Close()
			return out, err
		}
		if err = json.Unmarshal(raw, &e); err != nil {
			rows.Close()
			return out, err
		}
		e.Status = status
		out.Items = append(out.Items, e)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return out, err
	}
	if len(out.Items) > f.Limit {
		out.HasMore = true
		out.Items = out.Items[:f.Limit]
		out.NextCursor = encodeCursor(out.Items[len(out.Items)-1])
	}
	if out.Total-out.UndatedTotal > 100 {
		out.Mode = "density"
		starts, ends := []int{}, []int{}
		for _, p := range densityPeriods(f.Range) {
			starts = append(starts, p.Start)
			ends = append(ends, p.End)
		}
		rows, err = r.db.Query(ctx, `WITH matching AS MATERIALIZED(SELECT e.start_year,e.end_year`+predicate+`), periods AS(SELECT * FROM unnest($10::int[],$11::int[]) AS p(start_year,end_year)) SELECT p.start_year,p.end_year,count(m.start_year) FROM periods p JOIN matching m ON m.start_year<=p.end_year AND m.end_year>=p.start_year GROUP BY p.start_year,p.end_year ORDER BY p.start_year`, append(args, starts, ends)...)
		if err != nil {
			return out, err
		}
		for rows.Next() {
			var p DensityPeriod
			if err = rows.Scan(&p.Start, &p.End, &p.Count); err != nil {
				rows.Close()
				return out, err
			}
			out.Density = append(out.Density, p)
		}
		err = rows.Err()
		rows.Close()
		if err != nil {
			return out, err
		}
		// Only unused dimensions can narrow the existing AND/OR selection.
		for _, d := range []struct {
			key, column string
			used        bool
			array       bool
		}{{"topic", "topics", len(f.Topics) > 0, true}, {"country", "countries", len(f.Countries) > 0, true}, {"region", "regions", len(f.Regions) > 0, true}, {"kind", "kind", len(f.Kinds) > 0, false}} {
			if d.used {
				continue
			}
			expr := "unnest(e." + d.column + ")"
			if !d.array {
				expr = "e." + d.column
			}
			var s Suggestion
			s.Key = d.key
			err = r.db.QueryRow(ctx, `SELECT choice,count(*) FROM(SELECT DISTINCT e.id,`+expr+` AS choice`+predicate+`) choices GROUP BY choice HAVING count(*)<$10 ORDER BY (count(*)<=100) DESC,count(*) DESC,choice LIMIT 1`, append(args, out.Total)...).Scan(&s.Value, &s.Count)
			if errors.Is(err, pgx.ErrNoRows) {
				continue
			}
			if err != nil {
				return out, err
			}
			s.Name = s.Value
			out.Suggestions = append(out.Suggestions, s)
			if len(out.Suggestions) == 3 {
				break
			}
		}
	}
	return out, nil
}
func (r *Repository) ByID(ctx context.Context, id string, preview bool) (Event, error) {
	var e Event
	var raw []byte
	var status string
	if r.db == nil {
		return e, ErrUnavailable
	}
	err := r.db.QueryRow(ctx, `SELECT record,status FROM event_records WHERE id=$1 AND status<>'archived' AND ($2 OR status='published')`, id, preview).Scan(&raw, &status)
	if errors.Is(err, pgx.ErrNoRows) {
		return e, ErrNotFound
	}
	if err != nil {
		return e, err
	}
	err = json.Unmarshal(raw, &e)
	e.Status = status
	return e, err
}
func (r *Repository) Facets(ctx context.Context, preview, top100 bool) (Facets, error) {
	out := Facets{Topics: []Option{}, Countries: []Option{}, Regions: []Option{}, Kinds: []Option{}}
	if r.db == nil {
		return out, ErrUnavailable
	}
	for _, d := range []struct {
		column string
		dest   *[]Option
		array  bool
	}{{"topics", &out.Topics, true}, {"countries", &out.Countries, true}, {"regions", &out.Regions, true}, {"kind", &out.Kinds, false}} {
		expr := "unnest(" + d.column + ")"
		if !d.array {
			expr = d.column
		}
		rows, err := r.db.Query(ctx, `SELECT DISTINCT `+expr+` AS choice FROM event_records WHERE status<>'archived' AND ($1 OR status='published') AND (NOT $2 OR top100) ORDER BY choice LIMIT 1000`, preview, top100)
		if err != nil {
			return out, err
		}
		for rows.Next() {
			var name string
			if err = rows.Scan(&name); err != nil {
				rows.Close()
				return out, err
			}
			*d.dest = append(*d.dest, Option{name, name})
		}
		err = rows.Err()
		rows.Close()
		if err != nil {
			return out, err
		}
	}
	return out, nil
}
