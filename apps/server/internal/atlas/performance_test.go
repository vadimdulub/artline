package atlas

import (
	"context"
	"errors"
	"net/url"
	"strings"
	"testing"

	"github.com/jackc/pgx/v5"
)

type performanceCaptureDB struct {
	atlasDB
	query string
	args  []any
}

var errPerformanceCapture = errors.New("query captured")

type performanceCaptureRow struct{}

func (performanceCaptureRow) Scan(...any) error { return errPerformanceCapture }
func (db *performanceCaptureDB) QueryRow(_ context.Context, query string, args ...any) pgx.Row {
	db.query, db.args = query, args
	return performanceCaptureRow{}
}

func TestAtlasLiteralSearchDoesNotBecomeAFormatString(t *testing.T) {
	for _, shared := range []bool{false, true} {
		db := &performanceCaptureDB{}
		f := Filter{Range: Bounds, Limit: 24, Types: []string{"artwork"}}
		term := `100%_!\`
		if shared {
			f.Query = term
		} else {
			f.Entities = map[string]url.Values{"artwork": {"q": {term}}}
		}
		_, err := (&Repository{db: db}).List(context.Background(), f)
		if !errors.Is(err, errPerformanceCapture) {
			t.Fatal(err)
		}
		if strings.Contains(db.query, "%!") || strings.Contains(db.query, term) || !strings.Contains(db.query, "ESCAPE '!'") {
			t.Fatal("search SQL was formatted or interpolated instead of bound")
		}
		found := false
		for _, arg := range db.args {
			if value, ok := arg.(string); ok && value == term {
				found = true
			}
		}
		if !found {
			t.Fatal("literal search term was altered")
		}
	}
}
