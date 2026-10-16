package member

import (
	"context"
	"errors"
	"github.com/jackc/pgx/v5"
)

func (s PostgresMuseumStudio) Artworks(ctx context.Context, slug string, ids []string, public bool) ([]MuseumPublication, error) {
	out := []MuseumPublication{}
	if len(ids) == 0 {
		return out, nil
	}
	if len(ids) > maxMuseumArtworks {
		return nil, ErrMuseumArtwork
	}
	rows, err := s.DB.Query(ctx, `SELECT `+publicationColumns+` FROM museum_publications p JOIN institutions i ON i.id=p.institution_id WHERE i.slug=$1 AND i.status<>'archived' AND (NOT $2 OR p.published IS NOT NULL) AND p.kind='artwork' AND p.id=ANY($3::uuid[])`, slug, public, ids)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	for rows.Next() {
		p, err := scanPublication(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, p)
	}
	return out, rows.Err()
}
func (s PostgresMuseumStudio) SaveUpload(ctx context.Context, u User, slug string, info MuseumUpload) error {
	tx, err := s.DB.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	id, err := studioAccess(ctx, tx, u, slug, true)
	if err != nil {
		return err
	}
	_, err = tx.Exec(ctx, `INSERT INTO museum_uploads(id,institution_id,storage_key,content_type,width,height,byte_size,uploaded_by) VALUES($1,$2,$3,$4,$5,$6,$7,$8)`, info.ID, id, info.Key, info.ContentType, info.Width, info.Height, info.Size, u.ID)
	if err != nil {
		return err
	}
	return tx.Commit(ctx)
}
func (s PostgresMuseumStudio) Upload(ctx context.Context, slug, id string) (MuseumUpload, error) {
	var p MuseumUpload
	err := s.DB.QueryRow(ctx, `SELECT u.id::text,u.storage_key,u.content_type,u.width,u.height,u.byte_size FROM museum_uploads u JOIN institutions i ON i.id=u.institution_id WHERE i.slug=$1 AND i.status<>'archived' AND u.id=$2`, slug, id).Scan(&p.ID, &p.Key, &p.ContentType, &p.Width, &p.Height, &p.Size)
	if errors.Is(err, pgx.ErrNoRows) {
		err = ErrPublicationMissing
	}
	p.URL = museumImageURL(slug, id)
	return p, err
}
func (s PostgresMuseumStudio) ImagePublished(ctx context.Context, slug, id string) (bool, error) {
	var public bool
	err := s.DB.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM museum_publications p JOIN institutions i ON i.id=p.institution_id WHERE i.slug=$1 AND i.status<>'archived' AND p.published IS NOT NULL AND p.published->>'image_id'=$2)`, slug, id).Scan(&public)
	return public, err
}
func (s *LocalMuseumStudio) Artworks(_ context.Context, slug string, ids []string, public bool) ([]MuseumPublication, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := []MuseumPublication{}
	for _, id := range ids {
		p, ok := s.items[id]
		if ok && p.slug == slug && p.item.Kind == "artwork" && (!public || p.published != nil) {
			out = append(out, localPublicationView(p, public))
		}
	}
	return out, nil
}

type localMuseumUpload struct {
	slug string
	info MuseumUpload
}

func (s *LocalMuseumStudio) SaveUpload(_ context.Context, u User, slug string, info MuseumUpload) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if u.ID != "local-debug" || !s.staff[slug] {
		return ErrMuseumAccess
	}
	if s.uploads == nil {
		s.uploads = map[string]localMuseumUpload{}
	}
	s.uploads[info.ID] = localMuseumUpload{slug, info}
	return nil
}
func (s *LocalMuseumStudio) Upload(_ context.Context, slug, id string) (MuseumUpload, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	p, ok := s.uploads[id]
	if !ok || p.slug != slug {
		return MuseumUpload{}, ErrPublicationMissing
	}
	return p.info, nil
}
func (s *LocalMuseumStudio) ImagePublished(_ context.Context, slug, id string) (bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, p := range s.items {
		if p.slug == slug && p.published != nil && p.published.ImageID == id {
			return true, nil
		}
	}
	return false, nil
}
func cloneMuseumDocument(d MuseumDocument) MuseumDocument {
	d.Artworks = append([]MuseumArtworkRef(nil), d.Artworks...)
	if d.YearStart != nil {
		v := *d.YearStart
		d.YearStart = &v
	}
	if d.YearEnd != nil {
		v := *d.YearEnd
		d.YearEnd = &v
	}
	return d
}
