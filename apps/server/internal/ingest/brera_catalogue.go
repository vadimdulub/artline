package ingest

import (
	"context"
	"encoding/json"
	"errors"

	"github.com/jackc/pgx/v5/pgxpool"
)

const BreraCataloguePath = "docs/research/russia-italy-scale/brera-v1/inventory.json"
const BreraCatalogueSHA = "04de69de3dbd22c69bc333847c7b34bd536b82ad4db2c2bc226d23f7ed3b14a1"

// Nine individually checked object pages, not an unrestricted website crawler.
func ImportBreraCatalogue(ctx context.Context, pool *pgxpool.Pool, data []byte, apply bool) (EuropeanImportReport, error) {
	if checksum(data) != BreraCatalogueSHA {
		return EuropeanImportReport{}, errors.New("unreviewed Brera snapshot")
	}
	var m struct {
		Painters    map[string]string
		Definitions map[string]europeanDefinition
	}
	if e := json.Unmarshal(data, &m); e != nil {
		return EuropeanImportReport{}, e
	}
	if len(m.Painters) != 4 || len(m.Definitions) != 1 {
		return EuropeanImportReport{}, errors.New("unexpected Brera crosswalk")
	}
	return importEuropeanBatch(ctx, pool, data, apply, europeanBatch{SHA: BreraCatalogueSHA, Version: "brera-catalogue-2026-09-09-v1", Path: BreraCataloguePath, SourceSlug: "brera-catalogue-research", SourceName: "Pinacoteca di Brera — reviewed catalogue supplement", Schema: 2, Works: 9, Museums: 1, Painters: m.Painters, Definitions: m.Definitions})
}
