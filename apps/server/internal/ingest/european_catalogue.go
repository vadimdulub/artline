package ingest

import (
	"context"
	"encoding/json"
	"errors"
	"regexp"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Pinned after offline review; earlier inventories remain unchanged.
const EuropeanCatalogueSnapshotSHA = "5f3fba58d4b3e736b8491252c55aa7244017e5109001d6e0b229e17580f83320"
const EuropeanCataloguePath = "docs/research/european-catalogue-expansion/inventory.json"
const EuropeanCatalogueWorks = 115
const europeanCataloguePainters = 24

func catalogueEuropeanBatch(data []byte) (europeanBatch, error) {
	b := europeanBatch{SHA: EuropeanCatalogueSnapshotSHA, Version: "european-catalogue-research-2026-09-09-v3", Path: EuropeanCataloguePath, Schema: 2, Works: EuropeanCatalogueWorks, Museums: 3}
	if checksum(data) != b.SHA {
		return b, errors.New("unreviewed European catalogue snapshot: checksum mismatch")
	}
	var m struct {
		Definitions map[string]europeanDefinition
		Painters    map[string]string
	}
	if err := json.Unmarshal(data, &m); err != nil {
		return b, err
	}
	if len(m.Definitions) != b.Museums || len(m.Painters) != europeanCataloguePainters {
		return b, errors.New("invalid catalogue authority crosswalk")
	}
	qid := regexp.MustCompile(`^Q[1-9][0-9]*$`)
	for k, v := range m.Painters {
		if k != v || !qid.MatchString(v) {
			return b, errors.New("invalid painter authority")
		}
	}
	b.Definitions, b.Painters = m.Definitions, m.Painters
	return b, nil
}

// ImportEuropeanCatalogue imports only the approved local metadata supplement.
// No remote retrieval, images, publication or inferred current-display claims.
func ImportEuropeanCatalogue(ctx context.Context, pool *pgxpool.Pool, data []byte, apply bool) (EuropeanImportReport, error) {
	b, err := catalogueEuropeanBatch(data)
	if err != nil {
		return EuropeanImportReport{}, err
	}
	return importEuropeanBatch(ctx, pool, data, apply, b)
}
