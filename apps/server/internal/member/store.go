package member

import (
	"context"
	"errors"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

var ErrNoSession = errors.New("no active session")

type User struct {
	ID    string `json:"id"`
	Email string `json:"email"`
	Name  string `json:"name"`
}

type Identity struct{ Subject, Email, Name string }

type Store interface {
	Login(context.Context, Identity, string, string, time.Time) error
	Session(context.Context, string) (User, error)
	Logout(context.Context, string) error
}

type PostgresStore struct{ DB *pgxpool.Pool }

func (s PostgresStore) Login(ctx context.Context, identity Identity, hash, previous string, expires time.Time) error {
	tx, err := s.DB.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	var id string
	// Google sub is the identity key. Never merge accounts by email.
	err = tx.QueryRow(ctx, `INSERT INTO member_accounts(google_subject,email,display_name)
 VALUES($1,$2,$3) ON CONFLICT(google_subject) DO UPDATE
 SET email=EXCLUDED.email, display_name=EXCLUDED.display_name, updated_at=now()
 RETURNING id::text`, identity.Subject, identity.Email, identity.Name).Scan(&id)
	if err != nil {
		return err
	}
	if _, err = tx.Exec(ctx, `DELETE FROM member_sessions WHERE token_hash=$1 OR (member_id=$2 AND expires_at<=now())`, previous, id); err != nil {
		return err
	}
	if _, err = tx.Exec(ctx, `INSERT INTO member_sessions(token_hash,member_id,expires_at) VALUES($1,$2,$3)`, hash, id, expires); err != nil {
		return err
	}
	return tx.Commit(ctx)
}

func (s PostgresStore) Session(ctx context.Context, hash string) (User, error) {
	var u User
	err := s.DB.QueryRow(ctx, `SELECT m.id::text,m.email,m.display_name FROM member_sessions s
 JOIN member_accounts m ON m.id=s.member_id WHERE s.token_hash=$1 AND s.expires_at>now()`, hash).Scan(&u.ID, &u.Email, &u.Name)
	if errors.Is(err, pgx.ErrNoRows) {
		err = ErrNoSession
	}
	return u, err
}

func (s PostgresStore) Logout(ctx context.Context, hash string) error {
	_, err := s.DB.Exec(ctx, `DELETE FROM member_sessions WHERE token_hash=$1`, hash)
	return err
}
