package member

import (
	"context"
	"encoding/json"
	"errors"
	"sync"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type PostgresStudies struct{ DB *pgxpool.Pool }

func (p PostgresStudies) Create(ctx context.Context, owner string, s Study) error {
	tx, err := p.DB.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	// Serialize study creation for this account, including the hard bound.
	if _, err = tx.Exec(ctx, `SELECT id FROM member_accounts WHERE id=$1 FOR UPDATE`, owner); err != nil {
		return err
	}
	var n int
	if err = tx.QueryRow(ctx, `SELECT count(*) FROM member_studies WHERE member_id=$1`, owner).Scan(&n); err != nil {
		return err
	}
	if n >= studyCollectionLimit {
		return ErrStudyLimit
	}
	_, err = tx.Exec(ctx, `INSERT INTO member_studies(member_id,id,title,role,updated_at) VALUES($1,$2,$3,$4,$5)`, owner, s.ID, s.Title, s.Role, s.UpdatedAt)
	if err != nil {
		return err
	}
	return tx.Commit(ctx)
}
func readStudy(row pgx.Row) (Study, error) {
	var s Study
	var data []byte
	err := row.Scan(&s.ID, &s.Title, &s.Role, &s.UpdatedAt, &data, &s.ShareToken)
	if errors.Is(err, pgx.ErrNoRows) {
		return s, ErrStudyMissing
	}
	if err == nil {
		err = json.Unmarshal(data, &s.Records)
	}
	return s, err
}
func (p PostgresStudies) Get(ctx context.Context, owner, id string) (Study, error) {
	return readStudy(p.DB.QueryRow(ctx, `SELECT id::text,title,role,updated_at,records,coalesce(share_token::text,'') FROM member_studies WHERE member_id=$1 AND id=$2`, owner, id))
}
func (p PostgresStudies) GetShared(ctx context.Context, token string) (Study, error) {
	return readStudy(p.DB.QueryRow(ctx, `SELECT id::text,title,role,updated_at,records,coalesce(share_token::text,'') FROM member_studies WHERE share_token=$1`, token))
}
func (p PostgresStudies) Update(ctx context.Context, owner, id string, fn func(*Study) error) (Study, error) {
	tx, err := p.DB.Begin(ctx)
	if err != nil {
		return Study{}, err
	}
	defer tx.Rollback(ctx)
	s, err := readStudy(tx.QueryRow(ctx, `SELECT id::text,title,role,updated_at,records,coalesce(share_token::text,'') FROM member_studies WHERE member_id=$1 AND id=$2 FOR UPDATE`, owner, id))
	if err != nil {
		return s, err
	}
	if err = fn(&s); err != nil {
		return s, err
	}
	s.UpdatedAt = time.Now().UTC()
	raw, err := json.Marshal(s.Records)
	if err != nil {
		return s, err
	}
	_, err = tx.Exec(ctx, `UPDATE member_studies SET title=$3,role=$4,updated_at=$5,records=$6,share_token=NULLIF($7,'')::uuid WHERE member_id=$1 AND id=$2`, owner, id, s.Title, s.Role, s.UpdatedAt, raw, s.ShareToken)
	if err != nil {
		return s, err
	}
	return s, tx.Commit(ctx)
}
func (p PostgresStudies) Delete(ctx context.Context, owner, id string) error {
	result, err := p.DB.Exec(ctx, `DELETE FROM member_studies WHERE member_id=$1 AND id=$2`, owner, id)
	if err == nil && result.RowsAffected() == 0 {
		return ErrStudyMissing
	}
	return err
}

// Local previews are ephemeral and cannot write accounts, studies or catalogue data.
type LocalStudies struct {
	mu     sync.Mutex
	items  map[string]map[string]Study
	shared map[string][2]string
}

func NewLocalStudies() *LocalStudies {
	return &LocalStudies{items: map[string]map[string]Study{}, shared: map[string][2]string{}}
}
func cloneStudy(s Study) Study {
	b, _ := json.Marshal(s)
	var out Study
	_ = json.Unmarshal(b, &out)
	return out
}
func (p *LocalStudies) Create(_ context.Context, owner string, s Study) error {
	p.mu.Lock()
	defer p.mu.Unlock()
	if p.items[owner] == nil {
		p.items[owner] = map[string]Study{}
	}
	if len(p.items[owner]) >= studyCollectionLimit {
		return ErrStudyLimit
	}
	p.items[owner][s.ID] = cloneStudy(s)
	return nil
}
func (p *LocalStudies) Get(_ context.Context, owner, id string) (Study, error) {
	p.mu.Lock()
	defer p.mu.Unlock()
	s, ok := p.items[owner][id]
	if !ok {
		return Study{}, ErrStudyMissing
	}
	return cloneStudy(s), nil
}
func (p *LocalStudies) GetShared(_ context.Context, token string) (Study, error) {
	p.mu.Lock()
	defer p.mu.Unlock()
	ref, ok := p.shared[token]
	if !ok || token == "" {
		return Study{}, ErrStudyMissing
	}
	return cloneStudy(p.items[ref[0]][ref[1]]), nil
}
func (p *LocalStudies) Update(_ context.Context, owner, id string, fn func(*Study) error) (Study, error) {
	p.mu.Lock()
	defer p.mu.Unlock()
	s, ok := p.items[owner][id]
	if !ok {
		return Study{}, ErrStudyMissing
	}
	s = cloneStudy(s)
	if err := fn(&s); err != nil {
		return s, err
	}
	delete(p.shared, p.items[owner][id].ShareToken)
	if s.ShareToken != "" {
		p.shared[s.ShareToken] = [2]string{owner, id}
	}
	s.UpdatedAt = time.Now().UTC()
	p.items[owner][id] = cloneStudy(s)
	return s, nil
}
func (p *LocalStudies) Delete(_ context.Context, owner, id string) error {
	p.mu.Lock()
	defer p.mu.Unlock()
	if _, ok := p.items[owner][id]; !ok {
		return ErrStudyMissing
	}
	delete(p.shared, p.items[owner][id].ShareToken)
	delete(p.items[owner], id)
	return nil
}
