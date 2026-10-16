package member

import (
	"context"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"net/url"
	"sort"
	"strings"
	"time"
)

const studyCollectionLimit = 1000
const studyCollectionPageSize = 24

type StudyListFilter struct {
	Query, Sort, Cursor string
}

type StudyListPage struct {
	Items      []StudySummary `json:"items"`
	Total      int            `json:"total"`
	Matched    int            `json:"matched"`
	NextCursor string         `json:"next_cursor"`
}

type studyListCursor struct {
	ID, Title, Scope string
	UpdatedAt        time.Time
}

func studyListFilter(q url.Values) (StudyListFilter, error) {
	f := StudyListFilter{Query: strings.TrimSpace(q.Get("q")), Sort: q.Get("sort"), Cursor: q.Get("cursor")}
	if f.Sort == "" {
		f.Sort = "recent"
	}
	if len(f.Query) > 800 || len(f.Cursor) > 4096 || (f.Sort != "recent" && f.Sort != "title") {
		return f, studyInputError("Check your study search and sort order.")
	}
	return f, nil
}

func (f StudyListFilter) scope(owner string) string {
	raw, _ := json.Marshal([]string{owner, f.Query, f.Sort})
	hash := sha256.Sum256(raw)
	return hex.EncodeToString(hash[:])
}

func (f StudyListFilter) decode(owner string) (studyListCursor, error) {
	var c studyListCursor
	if f.Cursor == "" {
		return c, nil
	}
	raw, err := base64.RawURLEncoding.DecodeString(f.Cursor)
	if err != nil || json.Unmarshal(raw, &c) != nil || !bookmarkID.MatchString(c.ID) || c.Scope != f.scope(owner) || c.UpdatedAt.IsZero() || len(c.Title) > 800 {
		return c, studyInputError("This page no longer matches your search. Return to the first page.")
	}
	return c, nil
}

func (f StudyListFilter) finish(owner string, page StudyListPage) StudyListPage {
	if len(page.Items) > studyCollectionPageSize {
		page.Items = page.Items[:studyCollectionPageSize]
		last := page.Items[len(page.Items)-1]
		raw, _ := json.Marshal(studyListCursor{last.ID, strings.ToLower(last.Title), f.scope(owner), last.UpdatedAt})
		page.NextCursor = base64.RawURLEncoding.EncodeToString(raw)
	}
	return page
}

func (p PostgresStudies) List(ctx context.Context, owner string, f StudyListFilter) (StudyListPage, error) {
	page := StudyListPage{Items: []StudySummary{}}
	c, err := f.decode(owner)
	if err != nil {
		return page, err
	}
	// All scans are scoped to one account (at most 1,000 studies). Counts never
	// decode record documents; only the returned page reads record counts.
	pattern := "%" + strings.NewReplacer(`\`, `\\`, `%`, `\%`, `_`, `\_`).Replace(strings.ToLower(f.Query)) + "%"
	if err := p.DB.QueryRow(ctx, `SELECT count(*), count(*) FILTER (WHERE lower(title) LIKE $2) FROM member_studies WHERE member_id=$1`, owner, pattern).Scan(&page.Total, &page.Matched); err != nil {
		return page, err
	}
	args := []any{owner, pattern}
	where := "member_id=$1 AND lower(title) LIKE $2"
	order := "updated_at DESC,id"
	if f.Sort == "title" {
		order = `lower(title) COLLATE "C",id`
	}
	if c.ID != "" {
		if f.Sort == "title" {
			where += ` AND (lower(title) COLLATE "C",id) > ($3::text COLLATE "C",$4::uuid)`
			args = append(args, c.Title, c.ID)
		} else {
			where += " AND (updated_at < $3 OR (updated_at=$3 AND id>$4))"
			args = append(args, c.UpdatedAt, c.ID)
		}
	}
	rows, err := p.DB.Query(ctx, `SELECT id::text,title,role,updated_at,jsonb_array_length(records),share_token IS NOT NULL FROM member_studies WHERE `+where+` ORDER BY `+order+` LIMIT 25`, args...)
	if err != nil {
		return page, err
	}
	defer rows.Close()
	for rows.Next() {
		var s StudySummary
		if err := rows.Scan(&s.ID, &s.Title, &s.Role, &s.UpdatedAt, &s.Count, &s.Public); err != nil {
			return page, err
		}
		page.Items = append(page.Items, s)
	}
	return f.finish(owner, page), rows.Err()
}

func (p *LocalStudies) List(_ context.Context, owner string, f StudyListFilter) (StudyListPage, error) {
	c, err := f.decode(owner)
	if err != nil {
		return StudyListPage{}, err
	}
	p.mu.Lock()
	defer p.mu.Unlock()
	page := StudyListPage{Items: []StudySummary{}, Total: len(p.items[owner])}
	for _, s := range p.items[owner] {
		title := strings.ToLower(s.Title)
		if !strings.Contains(title, strings.ToLower(f.Query)) {
			continue
		}
		page.Matched++
		if c.ID != "" {
			if f.Sort == "title" {
				if title < c.Title || (title == c.Title && s.ID <= c.ID) {
					continue
				}
			} else if s.UpdatedAt.After(c.UpdatedAt) || (s.UpdatedAt.Equal(c.UpdatedAt) && s.ID <= c.ID) {
				continue
			}
		}
		page.Items = append(page.Items, studySummary(s))
	}
	sort.Slice(page.Items, func(i, j int) bool {
		a, b := page.Items[i], page.Items[j]
		if f.Sort == "title" {
			if strings.ToLower(a.Title) != strings.ToLower(b.Title) {
				return strings.ToLower(a.Title) < strings.ToLower(b.Title)
			}
		} else if !a.UpdatedAt.Equal(b.UpdatedAt) {
			return a.UpdatedAt.After(b.UpdatedAt)
		}
		return a.ID < b.ID
	})
	return f.finish(owner, page), nil
}
