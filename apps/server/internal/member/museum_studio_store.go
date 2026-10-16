package member

import (
	"context"
	"encoding/json"
	"errors"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type PostgresMuseumStudio struct{ DB *pgxpool.Pool }

func (s PostgresMuseumStudio) Museum(ctx context.Context, slug string) (StudioMuseum, error) {
	var m StudioMuseum
	err := s.DB.QueryRow(ctx, `SELECT id::text,slug,name,coalesce(website_url,'') FROM institutions WHERE slug=$1 AND status<>'archived'`, slug).Scan(&m.ID, &m.Slug, &m.Name, &m.Website)
	if errors.Is(err, pgx.ErrNoRows) {
		err = ErrPublicationMissing
	}
	return m, err
}
func (s PostgresMuseumStudio) Museums(ctx context.Context, u User, q string) ([]StudioMuseum, error) {
	rows, err := s.DB.Query(ctx, `SELECT i.id::text,i.slug,i.name,coalesce(i.website_url,''),
 coalesce(m.revoked_at IS NULL AND m.member_id IS NOT NULL,false),
 EXISTS(SELECT 1 FROM museum_staff_domains d WHERE d.institution_id=i.id AND d.domain=$2 AND d.revoked_at IS NULL) AND (m.member_id IS NULL OR m.revoked_at IS NULL)
 FROM institutions i LEFT JOIN museum_staff_members m ON m.institution_id=i.id AND m.member_id=$1::uuid
 WHERE i.status<>'archived' AND ($3='' AND m.member_id IS NOT NULL OR $3<>'' AND (strpos(lower(i.name),lower($3))>0 OR i.slug=$3))
 ORDER BY i.name,i.id LIMIT 25`, u.ID, museumDomain(u), q)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := []StudioMuseum{}
	for rows.Next() {
		var m StudioMuseum
		if err = rows.Scan(&m.ID, &m.Slug, &m.Name, &m.Website, &m.Managed, &m.Eligible); err != nil {
			return nil, err
		}
		m.Managed = m.Managed && m.Eligible
		items = append(items, m)
	}
	return items, rows.Err()
}
func (s PostgresMuseumStudio) Claim(ctx context.Context, u User, slug string) error {
	if museumDomain(u) == "" {
		return ErrMuseumAccess
	}
	tx, err := s.DB.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	var id string
	err = tx.QueryRow(ctx, `SELECT i.id::text FROM institutions i JOIN museum_staff_domains d ON d.institution_id=i.id
 WHERE i.slug=$1 AND i.status<>'archived' AND d.domain=$2 AND d.revoked_at IS NULL FOR SHARE OF d,i`, slug, museumDomain(u)).Scan(&id)
	if errors.Is(err, pgx.ErrNoRows) {
		return ErrMuseumAccess
	}
	if err != nil {
		return err
	}
	_, err = tx.Exec(ctx, `INSERT INTO museum_staff_members(institution_id,member_id,verified_email) VALUES($1,$2,$3)
 ON CONFLICT(institution_id,member_id) DO NOTHING`, id, u.ID, u.Email)
	if err != nil {
		return err
	}
	var revoked bool
	err = tx.QueryRow(ctx, `SELECT revoked_at IS NOT NULL FROM museum_staff_members WHERE institution_id=$1 AND member_id=$2 FOR SHARE`, id, u.ID).Scan(&revoked)
	if err != nil {
		return err
	}
	if revoked {
		return ErrMuseumAccess
	}
	return tx.Commit(ctx)
}

type studioQuerier interface {
	QueryRow(context.Context, string, ...any) pgx.Row
}

func studioAccess(ctx context.Context, db studioQuerier, u User, slug string, lock bool) (string, error) {
	if museumDomain(u) == "" {
		return "", ErrMuseumAccess
	}
	query := `SELECT i.id::text FROM institutions i JOIN museum_staff_members m ON m.institution_id=i.id
 JOIN museum_staff_domains d ON d.institution_id=i.id
 WHERE i.slug=$1 AND i.status<>'archived' AND m.member_id=$2 AND m.revoked_at IS NULL AND d.domain=$3 AND d.revoked_at IS NULL`
	if lock {
		query += " FOR SHARE OF m,d,i"
	}
	var id string
	err := db.QueryRow(ctx, query, slug, u.ID, museumDomain(u)).Scan(&id)
	if errors.Is(err, pgx.ErrNoRows) {
		err = ErrMuseumAccess
	}
	return id, err
}
func (s PostgresMuseumStudio) Access(ctx context.Context, u User, slug string) error {
	_, err := studioAccess(ctx, s.DB, u, slug, false)
	return err
}
func scanPublication(row pgx.Row) (MuseumPublication, error) {
	var p MuseumPublication
	var raw []byte
	err := row.Scan(&p.ID, &p.Kind, &raw, &p.Version, &p.Published, &p.HasChanges, &p.UpdatedAt)
	if errors.Is(err, pgx.ErrNoRows) {
		return p, ErrPublicationMissing
	}
	if err != nil {
		return p, err
	}
	err = json.Unmarshal(raw, &p.Document)
	return p, err
}

const publicationColumns = `p.id::text,p.kind,CASE WHEN $2 THEN p.published ELSE p.draft END,CASE WHEN $2 THEN 0 ELSE p.version END,p.published IS NOT NULL,CASE WHEN $2 THEN false ELSE p.published IS DISTINCT FROM p.draft END,CASE WHEN $2 THEN p.published_at ELSE p.updated_at END`

func (s PostgresMuseumStudio) List(ctx context.Context, slug string, public bool, kind, q, cursor string) ([]MuseumPublication, error) {
	rows, err := s.DB.Query(ctx, `SELECT `+publicationColumns+` FROM museum_publications p JOIN institutions i ON i.id=p.institution_id
 WHERE i.slug=$1 AND i.status<>'archived' AND (NOT $2 OR p.published IS NOT NULL) AND p.kind=$3
 AND ($4='' OR strpos(lower((CASE WHEN $2 THEN p.published ELSE p.draft END)->>'title'),lower($4))>0)
 AND ($5='' OR p.id>NULLIF($5,'')::uuid) ORDER BY p.id LIMIT 25`, slug, public, kind, q, cursor)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := []MuseumPublication{}
	for rows.Next() {
		p, err := scanPublication(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, p)
	}
	return items, rows.Err()
}
func (s PostgresMuseumStudio) Get(ctx context.Context, slug, id string, public bool) (MuseumPublication, error) {
	return scanPublication(s.DB.QueryRow(ctx, `SELECT `+publicationColumns+` FROM museum_publications p JOIN institutions i ON i.id=p.institution_id
 WHERE i.slug=$1 AND i.status<>'archived' AND (NOT $2 OR p.published IS NOT NULL) AND p.id=$3`, slug, public, id))
}
func (s PostgresMuseumStudio) Write(ctx context.Context, u User, slug, id string, input PublicationWrite) (MuseumPublication, error) {
	tx, err := s.DB.Begin(ctx)
	if err != nil {
		return MuseumPublication{}, err
	}
	defer tx.Rollback(ctx)
	institution, err := studioAccess(ctx, tx, u, slug, true)
	if err != nil {
		return MuseumPublication{}, err
	}
	if input.Document.ImageID != "" {
		var exists bool
		err = tx.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM museum_uploads WHERE id=$1 AND institution_id=$2)`, input.Document.ImageID, institution).Scan(&exists)
		if err != nil {
			return MuseumPublication{}, err
		}
		if !exists {
			return MuseumPublication{}, ErrPublicationMissing
		}
	}
	if input.Action == "publish" {
		ids := []string{}
		for _, ref := range input.Document.Artworks {
			if ref.Kind == "museum" {
				ids = append(ids, ref.ID)
			}
		}
		if len(ids) > 0 {
			rows, err := tx.Query(ctx, `SELECT id FROM museum_publications WHERE institution_id=$1 AND id=ANY($2::uuid[]) AND kind='artwork' AND published IS NOT NULL FOR SHARE`, institution, ids)
			if err != nil {
				return MuseumPublication{}, err
			}
			count := 0
			for rows.Next() {
				count++
			}
			err = rows.Err()
			rows.Close()
			if err != nil {
				return MuseumPublication{}, err
			}
			if count != len(ids) {
				return MuseumPublication{}, ErrMuseumArtwork
			}
		}
	}
	raw, err := json.Marshal(input.Document)
	if err != nil {
		return MuseumPublication{}, err
	}
	if id == "" {
		id = studyID()
		tag, err := tx.Exec(ctx, `INSERT INTO museum_publications(id,institution_id,kind,draft,updated_by) VALUES($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING`, id, institution, input.Kind, raw, u.ID)
		if err != nil {
			return MuseumPublication{}, err
		}
		if tag.RowsAffected() != 1 {
			return MuseumPublication{}, ErrPublicationConflict
		}
	} else {
		tag, err := tx.Exec(ctx, `UPDATE museum_publications SET draft=$1,version=version+1,updated_at=now(),updated_by=$2
 WHERE id=$3 AND institution_id=$4 AND kind=$5 AND version=$6`, raw, u.ID, id, institution, input.Kind, input.Version)
		if err != nil {
			return MuseumPublication{}, err
		}
		if tag.RowsAffected() != 1 {
			return MuseumPublication{}, ErrPublicationConflict
		}
	}
	if input.Action == "publish" {
		_, err = tx.Exec(ctx, `UPDATE museum_publications SET published=draft,published_at=now() WHERE id=$1`, id)
	}
	if input.Action == "unpublish" {
		_, err = tx.Exec(ctx, `UPDATE museum_publications SET published=NULL,published_at=NULL WHERE id=$1`, id)
	}
	if err != nil {
		return MuseumPublication{}, err
	}
	_, err = tx.Exec(ctx, `INSERT INTO museum_publication_history(publication_id,member_id,action,version,document) SELECT id,$2,$3,version,draft FROM museum_publications WHERE id=$1`, id, u.ID, input.Action)
	if err != nil {
		return MuseumPublication{}, err
	}
	p, err := scanPublication(tx.QueryRow(ctx, `SELECT `+publicationColumns+` FROM museum_publications p WHERE p.id=$1`, id, false))
	if err != nil {
		return p, err
	}
	return p, tx.Commit(ctx)
}

// The development store only reads institution identities; all staff and publishing data stays in memory.
type localPublication struct {
	slug        string
	item        MuseumPublication
	published   *MuseumDocument
	publishedAt time.Time
}
type LocalMuseumStudio struct {
	uploads map[string]localMuseumUpload
	mu      sync.Mutex
	lookup  func(context.Context, string) (StudioMuseum, error)
	search  func(context.Context, string) ([]StudioMuseum, error)
	staff   map[string]bool
	items   map[string]localPublication
}

func NewLocalMuseumStudio(db PostgresMuseumStudio) *LocalMuseumStudio {
	return &LocalMuseumStudio{lookup: db.Museum, search: func(ctx context.Context, q string) ([]StudioMuseum, error) {
		rows, err := db.DB.Query(ctx, `SELECT id::text,slug,name,coalesce(website_url,'') FROM institutions WHERE status<>'archived' AND $1<>'' AND (strpos(lower(name),lower($1))>0 OR slug=$1) ORDER BY name,id LIMIT 25`, q)
		if err != nil {
			return nil, err
		}
		defer rows.Close()
		items := []StudioMuseum{}
		for rows.Next() {
			var m StudioMuseum
			if err = rows.Scan(&m.ID, &m.Slug, &m.Name, &m.Website); err != nil {
				return nil, err
			}
			items = append(items, m)
		}
		return items, rows.Err()
	}, staff: map[string]bool{}, items: map[string]localPublication{}}
}
func (s *LocalMuseumStudio) Museum(ctx context.Context, slug string) (StudioMuseum, error) {
	return s.lookup(ctx, slug)
}
func (s *LocalMuseumStudio) Museums(ctx context.Context, u User, q string) ([]StudioMuseum, error) {
	if u.ID != "local-debug" {
		return nil, ErrMuseumAccess
	}
	items := []StudioMuseum{}
	if q != "" {
		var err error
		items, err = s.search(ctx, q)
		if err != nil {
			return nil, err
		}
	} else {
		s.mu.Lock()
		slugs := []string{}
		for slug := range s.staff {
			slugs = append(slugs, slug)
		}
		s.mu.Unlock()
		sort.Strings(slugs)
		for _, slug := range slugs {
			m, err := s.lookup(ctx, slug)
			if err != nil {
				return nil, err
			}
			items = append(items, m)
			if len(items) == 25 {
				break
			}
		}
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	for i := range items {
		items[i].Eligible = true
		items[i].Managed = s.staff[items[i].Slug]
	}
	return items, nil
}
func (s *LocalMuseumStudio) Claim(ctx context.Context, u User, slug string) error {
	if u.ID != "local-debug" {
		return ErrMuseumAccess
	}
	if _, err := s.lookup(ctx, slug); err != nil {
		return err
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.staff[slug] = true
	return nil
}
func (s *LocalMuseumStudio) Access(_ context.Context, u User, slug string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if u.ID != "local-debug" || !s.staff[slug] {
		return ErrMuseumAccess
	}
	return nil
}
func localPublicationView(p localPublication, public bool) MuseumPublication {
	item := p.item
	item.Document = cloneMuseumDocument(item.Document)
	item.Published = p.published != nil
	item.HasChanges = p.published == nil || !equalMuseumDocument(item.Document, *p.published)
	if public {
		item.Document = cloneMuseumDocument(*p.published)
		item.Version = 0
		item.HasChanges = false
		item.UpdatedAt = p.publishedAt
	}
	return item
}
func equalMuseumDocument(a, b MuseumDocument) bool {
	ra, _ := json.Marshal(a)
	rb, _ := json.Marshal(b)
	return string(ra) == string(rb)
}
func (s *LocalMuseumStudio) List(_ context.Context, slug string, public bool, kind, q, cursor string) ([]MuseumPublication, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	items := []MuseumPublication{}
	for _, p := range s.items {
		if p.slug != slug || p.item.Kind != kind || p.item.ID <= cursor || (public && p.published == nil) {
			continue
		}
		item := localPublicationView(p, public)
		if strings.Contains(strings.ToLower(item.Document.Title), strings.ToLower(q)) {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].ID < items[j].ID })
	if len(items) > 25 {
		items = items[:25]
	}
	return items, nil
}
func (s *LocalMuseumStudio) Get(_ context.Context, slug, id string, public bool) (MuseumPublication, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	p, ok := s.items[id]
	if !ok || p.slug != slug || (public && p.published == nil) {
		return MuseumPublication{}, ErrPublicationMissing
	}
	return localPublicationView(p, public), nil
}
func (s *LocalMuseumStudio) Write(_ context.Context, u User, slug, id string, in PublicationWrite) (MuseumPublication, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if u.ID != "local-debug" || !s.staff[slug] {
		return MuseumPublication{}, ErrMuseumAccess
	}
	if in.Document.ImageID != "" {
		image, ok := s.uploads[in.Document.ImageID]
		if !ok || image.slug != slug {
			return MuseumPublication{}, ErrPublicationMissing
		}
	}
	if in.Action == "publish" {
		for _, ref := range in.Document.Artworks {
			if ref.Kind == "museum" {
				p, ok := s.items[ref.ID]
				if !ok || p.slug != slug || p.item.Kind != "artwork" || p.published == nil {
					return MuseumPublication{}, ErrMuseumArtwork
				}
			}
		}
	}
	p := localPublication{slug: slug, item: MuseumPublication{ID: id, Kind: in.Kind}}
	if id == "" {
		if in.Kind == "profile" {
			for _, old := range s.items {
				if old.slug == slug && old.item.Kind == "profile" {
					return MuseumPublication{}, ErrPublicationConflict
				}
			}
		}
		p.item.ID = studyID()
	} else {
		var ok bool
		p, ok = s.items[id]
		if !ok || p.slug != slug || p.item.Kind != in.Kind || p.item.Version != in.Version {
			return MuseumPublication{}, ErrPublicationConflict
		}
	}
	p.item.Version++
	p.item.Document = cloneMuseumDocument(in.Document)
	p.item.UpdatedAt = time.Now().UTC()
	if in.Action == "publish" {
		d := cloneMuseumDocument(in.Document)
		p.published = &d
		p.publishedAt = p.item.UpdatedAt
	}
	if in.Action == "unpublish" {
		p.published = nil
	}
	s.items[p.item.ID] = p
	return localPublicationView(p, false), nil
}
