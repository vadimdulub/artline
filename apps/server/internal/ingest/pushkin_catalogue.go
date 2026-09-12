package ingest

import (
	"context"
	"encoding/json"
	"errors"
	"github.com/jackc/pgx/v5/pgxpool"
)

const PushkinCataloguePath = "docs/research/russia-italy-scale/pushkin-v1/inventory.json"
const PushkinCatalogueSHA = "bfabd703446edafbbe86abf63b6aad1b40098631558e950945c45f6cae3eeb45"

func ImportPushkinCatalogue(ctx context.Context, pool *pgxpool.Pool, data []byte, apply bool) (EuropeanImportReport, error) {
	if checksum(data) != PushkinCatalogueSHA {
		return EuropeanImportReport{}, errors.New("unreviewed Pushkin snapshot")
	}
	var m struct {
		Painters    map[string]string
		Definitions map[string]europeanDefinition
	}
	if e := json.Unmarshal(data, &m); e != nil {
		return EuropeanImportReport{}, e
	}
	if len(m.Painters) != 41 || len(m.Definitions) != 1 {
		return EuropeanImportReport{}, errors.New("unexpected Pushkin crosswalk")
	}
	return importEuropeanBatch(ctx, pool, data, apply, europeanBatch{SHA: PushkinCatalogueSHA, Version: "pushkin-highlights-2026-09-09-v1", Path: PushkinCataloguePath, SourceSlug: "pushkin-catalogue-research", SourceName: "Pushkin Museum — reviewed open highlights", Schema: 2, Works: 49, Museums: 1, Painters: m.Painters, Definitions: m.Definitions})
}
