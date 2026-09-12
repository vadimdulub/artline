package ingest

import (
	"context"
	"encoding/json"
	"errors"
	"github.com/jackc/pgx/v5/pgxpool"
)

const NGACataloguePath = "docs/research/nga-catalogue-expansion/reviewed/inventory.json"
const NGACatalogueSHA = "1bb0735af4f17696c341b7e8324b39c4afc1668548abce4714d60d26e22d148f"
const NGACatalogueWorks = 1510

func ngaCatalogueBatch(data []byte) (europeanBatch, error) {
	b := europeanBatch{SHA: NGACatalogueSHA, Version: "nga-open-catalogue-2026-09-09-v1", Path: NGACataloguePath, Schema: 2, Works: NGACatalogueWorks, Museums: 1, SourceSlug: "nga-catalogue-research", SourceName: "National Gallery of Art — pinned CC0 catalogue research"}
	if checksum(data) != b.SHA {
		return b, errors.New("NGA snapshot requires review: checksum mismatch")
	}
	var m struct {
		Definitions map[string]europeanDefinition
		Painters    map[string]string
	}
	if e := json.Unmarshal(data, &m); e != nil {
		return b, e
	}
	if len(m.Painters) != 356 || len(m.Definitions) != 1 {
		return b, errors.New("invalid NGA authority manifest")
	}
	b.Painters, b.Definitions = m.Painters, m.Definitions
	return b, nil
}

// No per-painter cap: all eligible records in this immutable source batch.
// Missing authorities, attribution/date conflicts and physical duplicate parts
// remain in research_records; they are not silently guessed into the atlas.
func ImportNGACatalogue(ctx context.Context, pool *pgxpool.Pool, data []byte, apply bool) (EuropeanImportReport, error) {
	b, e := ngaCatalogueBatch(data)
	if e != nil {
		return EuropeanImportReport{}, e
	}
	return importEuropeanBatch(ctx, pool, data, apply, b)
}
